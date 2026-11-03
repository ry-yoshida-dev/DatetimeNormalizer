import pytest

from datetime_normalizer.text import KanjiNumeralConverter


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("〇", "0"),
        ("二〇二四", "2024"),
        ("二零二四", "2024"),
        ("十", "10"),
        ("十二", "12"),
        ("二十", "20"),
        ("三十一", "31"),
        ("百", "100"),
        ("千", "1000"),
        ("二千二十四", "2024"),
        ("千九百八十九", "1989"),
        ("平成三十年", "平成30年"),
        ("十十", "十十"),
        ("二千千", "二千千"),
    ],
)
def test_convert(text: str, expected: str) -> None:
    assert KanjiNumeralConverter.convert(text) == expected
