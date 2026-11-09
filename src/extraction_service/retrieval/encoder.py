"""Pinned local ONNX sentence encoding; no automatic downloads or truncation."""

import importlib
import time
from pathlib import Path
from typing import Any

from tokenizers import Tokenizer

from extraction_service.retrieval.core import digest, read_confined
from extraction_service.retrieval.vector_store import checked_vector


class SentenceEncoder:
    """Encode whole texts with masked mean pooling and L2 normalization.

    Tokenizer and ONNX bytes must match the frozen artifact manifest. Runtime
    imports are lazy so offline tests never initialize a model. Native execution
    is not used; the CPU provider and one thread are explicit.
    """

    def __init__(
        self,
        directory: Path,
        hashes: dict[str, str],
        *,
        max_inputs: int = 104,
        deadline_seconds: float = 300,
    ) -> None:
        required = {"model.onnx", "tokenizer.json", "config.json"}
        if set(hashes) != required:
            raise ValueError("Encoder artifact manifest mismatch")
        for name, expected in hashes.items():
            raw = read_confined(directory, name, 128 * 1024 * 1024)
            if digest(raw) != expected:
                raise ValueError("Encoder artifact hash mismatch")
        self.tokenizer = Tokenizer.from_file(str(directory / "tokenizer.json"))
        self.tokenizer.no_truncation()
        self.tokenizer.no_padding()
        runtime = importlib.import_module("onnxruntime")
        self.numpy: Any = importlib.import_module("numpy")
        options = runtime.SessionOptions()
        options.intra_op_num_threads = 1
        options.inter_op_num_threads = 1
        self.session: Any = runtime.InferenceSession(
            str(directory / "model.onnx"), sess_options=options, providers=["CPUExecutionProvider"]
        )
        self.max_inputs = max_inputs
        self.calls = 0
        self.deadline = time.monotonic() + deadline_seconds

    def encode(self, text: str) -> list[float]:
        """Encode one complete input, rejecting capacity overruns before inference."""

        if self.calls >= self.max_inputs or time.monotonic() >= self.deadline:
            raise ValueError("Encoder invocation limit exceeded")
        if not text or len(text.encode()) > 65536:
            raise ValueError("Invalid encoder input size")
        encoded = self.tokenizer.encode(text)
        if len(encoded.ids) > 256:
            raise ValueError("Encoder token capacity exceeded; no truncation allowed")
        self.calls += 1
        feeds = {
            "input_ids": self.numpy.array([encoded.ids], dtype="int64"),
            "attention_mask": self.numpy.array([encoded.attention_mask], dtype="int64"),
            "token_type_ids": self.numpy.array([encoded.type_ids], dtype="int64"),
        }
        names = {item.name for item in self.session.get_inputs()}
        output = self.session.run(
            None, {key: value for key, value in feeds.items() if key in names}
        )
        embeddings = output[0]
        if embeddings.shape != (1, len(encoded.ids), 384):
            raise ValueError("Encoder output shape mismatch")
        mask = feeds["attention_mask"][..., None]
        pooled = (embeddings * mask).sum(axis=1) / mask.sum(axis=1)
        length = self.numpy.linalg.norm(pooled, axis=1, keepdims=True)
        vector: object = (pooled / length)[0].tolist()
        if time.monotonic() >= self.deadline:
            raise ValueError("Encoder deadline exceeded")
        return checked_vector(vector)
