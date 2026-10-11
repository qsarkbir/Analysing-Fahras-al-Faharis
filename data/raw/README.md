# Raw source text

Do not modify the file in this folder. All character offsets in the dataset refer to it exactly (codebook §1.1, §5.4).

## File

| | |
|---|---|
| File | `1382Kattani.FahrasFaharis.Shamela0001037-ara1.completed.mARkdown` |
| SHA-256 | `f1ead509612b7512714ade5d39277d9a30a46e0c60c7732a102dca960729bfd4` |
| Git blob SHA-1 | `dd406e89f3ddb11c5bdb46507fd66d417cbae35e` |
| Size | 2,649,601 bytes; 24,022 lines; UTF-8, LF line endings, no BOM |

## Provenance

- **Work:** ʿAbd al-Ḥayy al-Kattānī (d. 1382/1962), *Fahras al-fahāris wa-l-athbāt wa-muʿjam al-maʿājim wa-l-mashyakhāt wa-l-musalsalāt*.
- **Edition:** ed. Iḥsān ʿAbbās, 2nd ed. (Beirut: Dār al-Gharb al-Islāmī, 1982). The page markers `PageV..P...` refer to this edition.
- **Digital text:** OpenITI, version URI `1382Kattani.FahrasFaharis.Shamela0001037-ara1`, derived from al-Maktaba al-Shāmila (book 1037).
- **Repository:** <https://github.com/OpenITI/1400AH/tree/master/data/1382Kattani/1382Kattani.FahrasFaharis>
- **Upstream file name:** `1382Kattani.FahrasFaharis.Shamela0001037-ara1.completed`. The extension `.mARkdown` was added locally.
- **Upstream identity:** the git blob SHA-1 above is identical to the upstream file in `OpenITI/1400AH`. Checked on 2026-10-11; latest upstream commit touching the file: `9ecd69d142e2f165f80a52a958aa2cda09048e03` (2025-11-27).
- **Retrieval date:** on or before 2026-10-11 (date of first commit to this repository). **[confirm]**

## Known properties

- **Cleaned version.** According to the OpenITI version metadata (`…Shamela0001037-ara1.yml`), all paratextual elements were removed (introductions, footnotes, indices; "OpenITI Clean operation", 2023, HRH and MGR). Only footnote markers such as `(1)` survive. A pre-clean version with footnotes is available on the `pre-clean` branch:
  <https://raw.githubusercontent.com/OpenITI/1400AH/pre-clean/data/1382Kattani/1382Kattani.FahrasFaharis/1382Kattani.FahrasFaharis.Shamela0001037-ara1.completed>
- **Another digital version** exists in the same OpenITI folder: `1382Kattani.FahrasFaharis.JK001082-ara1` (2,991,467 bytes; base edition not recorded in its metadata). It has not been examined.
- **Page-marker convention.** OpenITI places `PageV..P...` at the **end** of the page it closes. Stage 1 assigns each character to the first page marker at or after it.
- **Digit artefacts.** The Arabic zero (٠) is often rendered as a full stop: `1.87` = 1087, `11.1` = 1101, `عام132.` = 1320 (see `data/interim/stage1/date_expression_counts.csv`, E03 and E03b).
