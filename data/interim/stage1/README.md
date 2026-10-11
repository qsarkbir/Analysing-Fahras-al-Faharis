# Stage 1 report: item table and boundary review

- **Codebook:** v0.1 (`docs/codebook.md`, §5, §6, §15)
- **Script:** `scripts/stage1_build_items.py` (standard library only)
- **Run:** `python -I -X utf8 scripts/stage1_build_items.py` (from the repository root; deterministic)
- **Raw file SHA-256:** `f1ead509…729bfd4` (see `data/raw/README.md`)

## Outputs

| File | Rows | Content |
|---|---|---|
| `data/processed/items.csv` | 1,225 | Items (§6.1). Segment word counts are left empty until Stage 2. |
| `data/processed/references.csv` | 176 | Cross-reference headings (§6.2), with automatic target resolution. |
| `boundary_issues.csv` | 52 | Boundary decisions and review candidates (39 need review). |
| `numbering_issues.csv` | 12 | Duplicates, gaps, misprints, and per-series summaries. |
| `date_expression_counts.csv` | 18 | Frequency of the §10.1 date expressions and known artefacts. |
| `stage1_summary.json` | — | Counts from the last run. |

## Items

| `item_kind` | `printed_series` | `section` | n |
|---|---|---|---|
| hafiz_list | none | introduction | 5 |
| entry | book | introduction | 15 (*awāʾil* 1–12, *arbaʿūn* 13–15) |
| entry | person | dictionary | 655 |
| entry | book | dictionary | 550 |

- Word count per entry: median 74, 90th percentile 490, maximum 4,538 (237,384 words in all items).
- 30 items have `boundary_status = corrected`.
- 11 headings have no colon within the first 120 characters; the first 8 words are used instead (see `notes`).
- `heading_translit` is left empty for Stage 2.

### Sections (open issue 4)

The `section` codes follow the codebook (`introduction`, `dictionary`, `other`). The text actually has these divisions; the finer division is visible in `heading_group_ar`:

| Lines | Division | Items |
|---|---|---|
| 39–232 | Preface: al-Kattānī's reply to Muḥammad Ḥabīb Allāh al-Shinqīṭī | — |
| 233–439 | List of 167 of al-Kattānī's own teachers («تسمية بعض من رويت عنه»), alphabetical | — |
| 440–806 | Four *muqaddimāt* (the 2nd contains the 5 ḥāfiẓ lists) | 5 hafiz_list |
| 807–1415 | *Musalsal bi-l-awwaliyya*, *kutub al-awāʾil*, *al-arbaʿūn* | 15 |
| 1417–23942 | Dictionary | 1,205 |
| 23943– | *Khātima* | — |

**Proposal:** split `introduction` into `preface`, `teacher_list`, `muqaddimat`, `opening`, and rename `other` to `khatima`. The teacher list is a ready-made source for `person_kattani_relation = direct_teacher` (§8.4).

## Boundary rules applied (§5.2)

| Issue | n | Treatment |
|---|---|---|
| `mis_tagged_continuation` | 12 | `$$$` directly after an **empty** numbered heading → continuation of that item (e.g. person #283 al-Kūrānī). Applied without review. |
| `split_midline` | 16 | `$$$` that is not reference-like → continuation of the preceding item. Review. |
| `false_heading_year` | 3 | A "numbered heading" whose previous line ends in «سنة» or «عام» is a year broken across a page marker (person «733», person «253», book «392»). Treated as continuation, and the number is kept as text. |
| `tag_variant` | 1 | `### $$ 494 -` read as person #494. |
| `possible_untagged_item` | 4 | `$$$` text after a reference, not reference-like; left outside any item. Review. |
| `unassigned_text` | 10 | Paragraphs after a reference, outside any item (often untagged references or entries). Review. |
| `reference_with_content` | 1 | A reference containing «نرويها»; may be an untagged entry. Review. |
| `possible_untagged_heading` | 5 | «NAME (n) :» or «N - NAME :» inside an item, e.g. «… الخاتمة 65 - الباجي (1) :» (line 3501), «8. - البناني المكي» (line 3860), «299ب - مشيخة الجزري» (line 12634). Review. |

A `$$$` is treated as a **reference** when its text (with `~~` continuation lines) is at most 300 characters, contains انظر / سبق / تقدم, and starts either with «NAME :» or with «NAME (انظر …».

Two further rules are not in the codebook but were needed:

- **Milestones inside headings.** Headings such as `### $DIC_BIB$ ms425 219 -` and `### $ 196 ms259 -` occur.
- **Page markers.** A character belongs to the first `PageV..P...` at or after it (OpenITI end-of-page convention). **To verify against the printed edition.**

## Numbering (§6.1 `number_issue`)

- **Person series:** 655 items; numbers 1–662; 7 gaps.
  - **Located (2):** #65 is inline at line 3501, and #80 is at line 3860 (written «8.»).
  - **Not located (5):** #184, #433, #471, #481, #566. Check the printed edition.
- **Book series:** 565 items; numbers 1–563.
  - Duplicates: #15 (*arbaʿūn* and dictionary) and #233 (a sub-entry «ب معجم السبكي»).
  - #598 is read as **538** (`printed_number_corrected`), between 537 and 539.
- The earlier counts in `docs/handoff_codebook.md` were affected by the false headings «733», «253», «392» and by the missed `ms` headings.

## References

| Status | n |
|---|---|
| resolved | 92 |
| ambiguous | 20 |
| unresolved | 64 |

Resolution is **automatic and unverified**. It matches either the name in the hint («انظر الأمم») or, for hints like «انظر حرف الحاء», the tail of the name within that letter. `resolution_note` records the method and the candidates. `name_form_type` and `target_person_id` are left for Stage 2.

## Date expressions (§10.1)

Counts are over items (occurrences / items):

| ID | Expression | Count |
|---|---|---|
| E01 | Digit year | 1,229 / 522 |
| E14 | Death cue + year | 624 / 450 |
| E15 | Birth cue + year | 205 / 186 |
| E04 | Year in words | 58 / 41 |
| E02 | Abbreviated year (1–2 digits) | 24 / 22 |
| E03 | Dot inside the digits | 9 / 8 |
| E03b | Digits + trailing dot | 77 / 73 |
| E05 | Digits attached to a word | 20 / 18 |
| E12 | Early / mid / late century | 31 / 26 |
| E06 | نيف after a year cue | 9 / 9 |
| E10 | Circa + year | 6 / 6 |
| E11 | Floruit | 1 / 1 |
| E16 | Variant («وقيل») | 1 / 1 |
| E08, E09 | After / before + year | 0 |
| E17 | Arabic-Indic digits | 0 |

Implications for Stage 2:

- **'.' for Arabic zero (٠).** `1.87` = 1087, `11.1` = 1101, `132.` = 1320. This needs its own rule beside abbreviated years; E03b mixes it with full stops.
- **نيف is mostly about age** («عن نيف وسبعين سنة»), not a date.
- `after` / `before` qualifiers do not occur. Open issue 2 therefore has no practical effect.

## Proposed codebook changes (for decision)

1. `section` codes, as above.
2. Add `line_start` and `line_end` to `items.csv` (added already, for reviewing against the raw file).
3. Add `resolution_note` and `line_no` to `references.csv` (added already).
4. Add boundary issue codes: `false_heading_year`, `tag_variant`, `possible_untagged_item`, `unassigned_text`, `reference_with_content`, `possible_untagged_heading`.
5. Add a date rule for '.' standing for Arabic zero.
6. §5.2 rule 2 says "without «انظر»". In fact the decisive condition is an **empty** numbered heading (#283 itself contains «انظر الأمم»).

## How to review

Record decisions in `data/interim/corrections/*.csv` (codebook §4), never in the processed tables. The script does not yet read correction files. That step will be added once the first corrections exist.
