# DatetimeNormalizer Reference

Supported notations and readings of shared time zone abbreviations.

## Supported notations

Full-width characters, kanji numerals, spacing around units, and letter case are folded first.

| Kind | Examples |
| --- | --- |
| Numeric date | `2024-01-05`, `2024/1/5`, `2024.1.5`, `2024:01:05`, `20240105` |
| Partial date | `2024`, `2024-01`, `2024年`, `2024年1月`, `January 2024` |
| Japanese date | `2024年1月5日`, `二〇二四年一月五日`, `二千二十四年十二月三十一日` |
| Era | `令和6年1月5日`, `令和元年5月1日`, `R6.1.5`, `H31/4/30`, `令6.1.5`, `㋿6年1月5日` |
| English date | `January 5, 2024`, `5 Jan 2024`, `05-Sept-2024` |
| Year-last date | `1/2/2024`, with `date_order` set |
| Date without a year | `1月5日`, `1月`, `January 5`, `5 Jan`, with `default_year` set; `1/5`, with `date_order` also set |
| Weekday | `(金)`, `（金曜日）`, `金曜`, `Friday,`, `(Fri)`; verified against the date, then dropped |
| Time | `13`, `13:05`, `13:05:09.5`, `130509`, `13時5分9秒`, `1時半`, `正午` |
| 12-hour clock | `午後1時`, `午前9:30`, `1:30 PM`, `1 p.m.` |
| Offset | `Z`, `+09:00`, `+0900`, `+9`, `UTC+9`, `GMT-05:00`, `+09:18:59` |
| IANA time zone | `Asia/Tokyo`, `america/new_york`, `Etc/GMT+9`, `Japan` |
| Abbreviation | `UTC`, `GMT`, `JST`, `KST`, `HKT`, `SGT`, `EST`, `EDT`, `PDT`, `CET`, `CEST`, `AEST`, `NZST`, and others in [time_zone.py](../src/datetime_normalizer/readers/time_zone.py); `ET`, `CT`, `MT`, `PT` |
| Japanese time zone | `日本時間`, `日本標準時`, `協定世界時`, `世界標準時`, `世界時`, `世界時間`, `グリニッジ標準時`, `東部標準時`, `米国東部時間`, `ロンドン時間`, `シンガポール時間` |
| Zone before the time | `日本時間午後1時`, `(日本時間)13:05`, `UTC 13:05` |
| Unix time | `1704427200`, `1704427200.5`, `1704427200000` (milliseconds); always UTC |
| Zone as a note | `+09:00[Asia/Tokyo]`, `+0900 (JST)`, `GMT+0900 (日本標準時)`, `13時(日本時間)` |
| Zone after a date | `2024-01-05 JST`, `2024-01-05+09:00`, `2024-01-05Z`, `2024年1月5日(日本時間)` |

A time or a zone needs a full date. An hour from 24 to 47 belongs to the next day (`24:00`, `25時`).
Relative text such as `昨日` is not supported.

## Time zones

- Abbreviations are fixed offsets: `EST` is -05:00 even in July. Region names (`America/New_York`, `ET`, `米国東部時間`) follow daylight saving time.
- IANA and region names need the system time zone database, or [`tzdata`](https://pypi.org/project/tzdata/) where there is none (Windows, slim containers).

Shared abbreviations are read as the most common zone; override with `zone_abbreviations`.

| Name | Read as | Also used for |
| --- | --- | --- |
| `CST`, `CDT` | United States Central, -06:00, -05:00 | China, Cuba |
| `PST` | United States Pacific, -08:00 | Philippines |
| `MST` | United States Mountain, -07:00 | Malaysia |
| `AST`, `ADT` | Atlantic, -04:00, -03:00 | Arabia |
| `IST` | India, +05:30 | Israel, Ireland |
| `BST` | British Summer Time, +01:00 | Bangladesh |
| `GST` | Gulf, +04:00 | South Georgia |
| `AMT` | Amazon, -04:00 | Armenia |
| `BDT` | Bangladesh, +06:00 | Brunei |
| `ECT` | Ecuador, -05:00 | Eastern Caribbean |
| `SST` | Samoa, -11:00 | Singapore |
| `WST` | West Samoa, +13:00 | Western Australia |

