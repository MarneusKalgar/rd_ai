import copy
from typing import Any

import pytest

from extraction_service.application.tokenization import GemmaTokenizer

from .conftest import tokenizer_info


def test_bpe_specials_unicode_newlines_and_space() -> None:
    tokenizer = GemmaTokenizer(tokenizer_info())

    count = tokenizer.count("<bos>ab é\nab")

    # BOS + merged ab + space + two UTF-8 bytes + newline + merged ab.
    assert count == 7
    assert tokenizer.count("🙂") == 4
    assert tokenizer.count("ab\nab") == 3


@pytest.mark.parametrize(
    "field,value",
    [
        ("tokenizer.ggml.model", "unknown"),
        ("tokenizer.ggml.add_space_prefix", True),
        ("tokenizer.ggml.add_eos_token", True),
        ("tokenizer.ggml.token_type", []),
        ("tokenizer.ggml.tokens", ["<unk>"]),
        ("tokenizer.ggml.merges", ["broken"]),
    ],
)
def test_unsupported_tokenizers_fail_closed(field: str, value: Any) -> None:
    info = copy.deepcopy(tokenizer_info())
    info[field] = value

    with pytest.raises(ValueError):
        GemmaTokenizer(info)


@pytest.mark.parametrize("missing", ["<0xC3>", "<unk>"])
def test_incomplete_fallback_vocabulary_has_no_other_metadata_defect(missing: str) -> None:
    info = copy.deepcopy(tokenizer_info())
    index = info["tokenizer.ggml.tokens"].index(missing)
    info["tokenizer.ggml.tokens"].pop(index)
    info["tokenizer.ggml.token_type"].pop(index)

    with pytest.raises(ValueError, match="Incomplete byte fallback vocabulary"):
        GemmaTokenizer(info)
