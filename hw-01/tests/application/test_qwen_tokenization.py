"""Qwen counters retain byte coverage, specials and normalization bounds."""

from typing import Any

import pytest
from tokenizers import pre_tokenizers

from extraction_service.application.qwen_tokenization import QwenTokenizer


def qwen_info() -> dict[str, Any]:
    tokens = sorted(pre_tokenizers.ByteLevel.alphabet()) + ["ab", "<|im_start|>"]
    return {
        "general.architecture": "qwen35",
        "tokenizer.ggml.model": "gpt2",
        "tokenizer.ggml.pre": "qwen35",
        "tokenizer.ggml.tokens": tokens,
        "tokenizer.ggml.token_type": [1] * (len(tokens) - 1) + [3],
        "tokenizer.ggml.merges": ["a b"],
        "tokenizer.ggml.add_bos_token": False,
    }


def test_qwen_counts_bytes_digits_specials_and_normalization_bound() -> None:
    tokenizer = QwenTokenizer(qwen_info())

    assert tokenizer.count("ab") == 1
    assert tokenizer.count("ab 123") == 5
    assert tokenizer.count("<|im_start|>ab\n") == 3
    assert tokenizer.count("🙂") == 4
    assert tokenizer.count("é") == 2
    assert tokenizer.count("e\u0301") == 3


@pytest.mark.parametrize(
    "field,value,expected",
    [
        ("general.architecture", "qwen2", "Unsupported Qwen tokenizer model"),
        ("tokenizer.ggml.pre", "qwen2", "Unsupported Qwen tokenizer model"),
        ("tokenizer.ggml.add_bos_token", True, "boundary behavior"),
        ("tokenizer.ggml.token_type", [], "token types"),
        ("tokenizer.ggml.merges", ["a missing"], "missing vocabulary"),
    ],
)
def test_qwen_rejects_specific_unsupported_metadata(field: str, value: Any, expected: str) -> None:
    info = qwen_info()
    info[field] = value

    with pytest.raises(ValueError, match=expected):
        QwenTokenizer(info)


def test_qwen_rejects_missing_byte_without_another_metadata_defect() -> None:
    info = qwen_info()
    info["tokenizer.ggml.tokens"].remove("z")
    info["tokenizer.ggml.token_type"].pop(0)

    with pytest.raises(ValueError, match="Incomplete Qwen byte alphabet"):
        QwenTokenizer(info)
