"""Count installed Qwen3.5 byte-level BPE without downloading tokenizer assets."""

import hashlib
import json
import unicodedata
from typing import Any, Final

from tokenizers import AddedToken, Regex, Tokenizer, models, pre_tokenizers

QWEN35_SPLIT: Final[str] = (
    r"(?i:'s|'t|'re|'ve|'m|'ll|'d)|[^\r\n\p{L}\p{N}]?[\p{L}\p{M}]+|\p{N}|"
    r" ?[^\s\p{L}\p{M}\p{N}]+[\r\n]*|\s*[\r\n]+|\s+(?!\S)|\s+"
)


class QwenTokenizer:
    """Reconstruct the reviewed qwen35 pre-tokenizer from installed GGUF metadata.

    Use the upstream Qwen3.5 split expression and GPT-2 byte alphabet. Count both
    raw text and its NFC form, retaining the larger count to cover normalization
    differences between the GGUF runtime and upstream tokenizer. Admission adds
    its separate two-token boundary allowance. Unsupported metadata fails closed.
    """

    method = "qwen35-installed-bpe-raw-nfc-max-render-only-plus-two-boundary-tokens"

    def __init__(self, info: dict[str, Any]) -> None:
        if (
            info.get("general.architecture") != "qwen35"
            or info.get("tokenizer.ggml.model") != "gpt2"
            or info.get("tokenizer.ggml.pre") != "qwen35"
        ):
            raise ValueError("Unsupported Qwen tokenizer model")

        tokens = info.get("tokenizer.ggml.tokens")
        kinds = info.get("tokenizer.ggml.token_type")
        raw_merges = info.get("tokenizer.ggml.merges")

        if (
            not isinstance(tokens, list)
            or not tokens
            or not all(isinstance(token, str) for token in tokens)
            or len(set(tokens)) != len(tokens)
        ):
            raise ValueError("Missing Qwen tokenizer vocabulary")

        if (
            not isinstance(kinds, list)
            or len(kinds) != len(tokens)
            or any(type(kind) is not int or kind not in (1, 3, 4, 5) for kind in kinds)
        ):
            raise ValueError("Unsupported Qwen token types")

        if any(
            info.get(key, False) is not False
            for key in (
                "tokenizer.ggml.add_space_prefix",
                "tokenizer.ggml.add_bos_token",
                "tokenizer.ggml.add_eos_token",
            )
        ):
            raise ValueError("Unsupported Qwen boundary behavior")

        vocabulary = {token: index for index, token in enumerate(tokens)}
        if not set(pre_tokenizers.ByteLevel.alphabet()) <= set(vocabulary):
            raise ValueError("Incomplete Qwen byte alphabet")

        if not isinstance(raw_merges, list) or not raw_merges:
            raise ValueError("Missing Qwen tokenizer merges")

        merges = []
        for merge in raw_merges:
            if not isinstance(merge, str) or len(merge.split(" ")) != 2:
                raise ValueError("Malformed Qwen tokenizer merge")
            left, right = merge.split(" ")
            if left not in vocabulary or right not in vocabulary or left + right not in vocabulary:
                raise ValueError("Qwen merge references missing vocabulary")
            merges.append((left, right))

        self._tokenizer = Tokenizer(models.BPE(vocab=vocabulary, merges=merges))
        self._tokenizer.pre_tokenizer = pre_tokenizers.Sequence(
            [
                pre_tokenizers.Split(Regex(QWEN35_SPLIT), behavior="isolated"),
                pre_tokenizers.ByteLevel(add_prefix_space=False, use_regex=False),
            ]
        )
        special = [
            AddedToken(token, special=True, normalized=False)
            for token, kind in zip(tokens, kinds, strict=True)
            if kind in (3, 4)
        ]
        self._tokenizer.add_special_tokens(special)
        serialized = json.dumps(info, sort_keys=True, ensure_ascii=False).encode()
        self.sha256 = hashlib.sha256(serialized).hexdigest()

    def count(self, rendered: str) -> int:
        """Conservatively retain the larger installed-BPE raw/NFC token count."""

        raw = len(self._tokenizer.encode(rendered, add_special_tokens=False).ids)
        normalized = unicodedata.normalize("NFC", rendered)
        if normalized == rendered:
            return raw

        nfc = len(self._tokenizer.encode(normalized, add_special_tokens=False).ids)
        return max(raw, nfc)
