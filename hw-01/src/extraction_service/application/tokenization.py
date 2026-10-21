"""Pinned Gemma4 tokenizer reconstructed from installed GGUF metadata."""

import hashlib
import json
from typing import Any

from tokenizers import AddedToken, Regex, Tokenizer, models, normalizers, pre_tokenizers


class GemmaTokenizer:
    """Match the installed SPM-style BPE: space escaping and newline splitting.

    No model weights, generated probes or external tokenizer downloads are used.
    Only the reviewed Gemma4 metadata shape is supported; other models fail closed.
    """

    def __init__(self, info: dict[str, Any]) -> None:
        if info.get("tokenizer.ggml.model") != "gemma4":
            raise ValueError("Unsupported local tokenizer model")

        tokens = info.get("tokenizer.ggml.tokens")
        kinds = info.get("tokenizer.ggml.token_type")
        raw_merges = info.get("tokenizer.ggml.merges")

        if not isinstance(tokens, list) or not all(isinstance(item, str) for item in tokens):
            raise ValueError("Missing tokenizer vocabulary")

        if (
            not isinstance(kinds, list)
            or len(kinds) != len(tokens)
            or any(type(kind) is not int for kind in kinds)
            or len(set(tokens)) != len(tokens)
        ):
            raise ValueError("Missing tokenizer token types")

        if not isinstance(raw_merges, list) or not raw_merges:
            raise ValueError("Missing tokenizer merges")

        if info.get("tokenizer.ggml.add_space_prefix") is not False:
            raise ValueError("Unsupported tokenizer prefix behavior")

        if info.get("tokenizer.ggml.add_eos_token", False) is not False:
            raise ValueError("Unsupported tokenizer EOS behavior")

        merges = []

        for merge in raw_merges:
            if not isinstance(merge, str) or " " not in merge:
                raise ValueError("Malformed tokenizer merge")

            left, right = merge.split(" ", 1)
            merges.append((left, right))

        vocabulary = {token: index for index, token in enumerate(tokens)}

        if "<unk>" not in vocabulary or any(
            f"<0x{byte:02X}>" not in vocabulary for byte in range(256)
        ):
            raise ValueError("Incomplete byte fallback vocabulary")

        self._tokenizer = Tokenizer(
            models.BPE(vocab=vocabulary, merges=merges, unk_token="<unk>", byte_fallback=True)
        )
        self._tokenizer.normalizer = normalizers.Replace(" ", "▁")
        self._tokenizer.pre_tokenizer = pre_tokenizers.Split(
            Regex(r"[^\n]+|[\n]+"), behavior="isolated"
        )
        special = []

        for token, kind in zip(tokens, kinds, strict=True):
            if kind in (3, 4):
                special.append(AddedToken(token, special=True, normalized=False))

        self._tokenizer.add_special_tokens(special)
        serialized = json.dumps(info, sort_keys=True, ensure_ascii=False).encode()
        self.sha256 = hashlib.sha256(serialized).hexdigest()

    def count(self, rendered: str) -> int:
        """Count the server-rendered prompt without adding another BOS/EOS."""

        return len(self._tokenizer.encode(rendered, add_special_tokens=False).ids)
