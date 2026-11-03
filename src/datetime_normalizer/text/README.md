# text

## Overview

Removal of character-level differences, so that readers only deal with one spelling.

## Components

| Component | Responsibility |
| --- | --- |
| [canonicalizer.py](canonicalizer.py) | `TextCanonicalizer`: width, case, dashes, spacing, and numerals |
| [kanji_numeral_converter.py](kanji_numeral_converter.py) | `KanjiNumeralConverter`: positional and unit-based kanji numerals to digits |
