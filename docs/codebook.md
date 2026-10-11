# Codebook: *Fahras al-fahāris* Fahrasa Distribution Project

- **Version:** 0.1 (draft)
- **Date:** 2026-10-11
- **Status:** Draft for review. Items marked **[proposed]** await confirmation; see §13 Open issues.
- **Location in repository:** `docs/codebook.md`

---

## 0. About this document

This codebook defines the units, identifiers, variables, controlled vocabularies, file layout, and coding rules for building a dataset from al-Kattānī's *Fahras al-fahāris*. It governs all scripted and LLM-assisted processing in this repository.

**Language conventions**

- Field names, codes, category labels, and notes are in **English**.
- Arabic as written in the source is kept in fields ending in `_ar`.
- Transliteration follows **IJMES** and is kept in fields ending in `_translit`.
- Years are **AH (hijrī)** unless a field name says `_ce`. CE values are always derived, never entered by hand.

**Change control.** Every change to definitions, codes, or rules is recorded in §12 Decision log with a date. Datasets record the codebook version they were built against.

---

## 1. Source and premises

### 1.1 Source

- **Work:** ʿAbd al-Ḥayy al-Kattānī (d. 1382/1962), *Fahras al-fahāris wa-l-athbāt wa-muʿjam al-maʿājim wa-l-mashyakhāt wa-l-musalsalāt* (فهرس الفهارس والأثبات ومعجم المعاجم والمشيخات والمسلسلات).
- **Edition:** ed. Iḥsān ʿAbbās, 2nd ed. (Beirut: Dār al-Gharb al-Islāmī, 1982).
- **Digital text:** OpenITI, `1400AH`, `1382Kattani.FahrasFaharis.Shamela0001037-ara1` (Shamela-derived, OpenITI mARkdown).
- The editor's footnotes are **not** present in the digital text; only their markers (e.g. `(1)`) survive.

The SHA-256 checksum of the raw file used is recorded in `data/raw/README.md`. All character offsets in this dataset refer to that exact file.

### 1.2 Research premise

The dataset is a record of transmitted works **as collected and presented from al-Kattānī's vantage point**, not a sample of Islamic knowledge transmission at large. Al-Kattānī's selection, emphasis, and judgement are treated as **objects of analysis**, not as error to be corrected. The coding scheme therefore records:

- what al-Kattānī says, separately from what we infer or import from external authorities; and
- the attributes of al-Kattānī's own relation to each person and work (access, proximity, routes, evaluations).

### 1.3 Research questions the data must support

1. How are fahrasa-type works and their authors distributed over time (AH century) and space (city → region)?
2. How do author attributes (titles, legal school, Sufi affiliation), work content (ḥadīth only vs. other fields), and work extent relate to that distribution?
3. How does al-Kattānī's proximity, access, and attention shape what is recorded?

---

## 2. General principles

| ID | Principle |
|---|---|
| P1 | **Code broadly and granularly; filter and aggregate at analysis time.** Inclusion/exclusion decisions are analysis-time filters, not coding-time deletions. |
| P2 | **Preserve the original wording.** Every coded value keeps the Arabic expression it was coded from. |
| P3 | **Separate stated, inferred, and imported values.** Every value carries a provenance code (§9). |
| P4 | **Anchor every extracted value.** LLM-extracted values carry verbatim evidence and character offsets into the raw file. |
| P5 | **Derive, don't hand-enter, aggregate values.** Primary region, century, CE dates, and category mappings are computed by documented rules (§11); the rule ID is stored with the result. |
| P6 | **Store multi-valued attributes in long format.** One row per value; never `title1, title2, …` columns. |
| P7 | **Never renumber.** Identifiers, once frozen, are never reassigned or reused. |

---

## 3. Units of analysis

| Unit | Definition | ID |
|---|---|---|
| **Item** | A descriptive unit carrying its own heading in the printed edition (numbered headings in the person series or the book series), plus the ḥāfiẓ lists. | `I0001` |
| **Transmission object** | Anything al-Kattānī presents as transmitted or transmittable: a standalone work, a part of a work, or the whole of a person's transmitted corpus (*marwiyyāt*). **Works** are the subset with `object_type = standalone_work`. | `O0001` |
| **Person** | Any compiler, subject, or heading person of an item or object. Persons appearing only inside transmission routes are out of scope for v0.1 (see §8.4). | `P0001` |
| **Reference** | A heading-only cross-reference (`### $$$` with *unẓur*), e.g. «أحمد بن علي ابن حجر: هو الحافظ (انظر حرف الحاء)». Not an item. | `R0001` |

```
Item ──describes / mentions──▶ Transmission object (0..n) ──agent (role)──▶ Person
  └──────────────── heading person ─────────────────────────────────────────▶ Person
Reference ──points to──▶ Item
```

### 3.1 Typical mismatches between units

| Pattern | Example | Items | Objects | Persons |
|---|---|---|---|---|
| One-to-one | Person #1 Aḥmad al-Azdī | 1 | 1 (untitled) | 1 |
| One item, several works | Person #283 Ibrāhīm al-Kūrānī: *al-Amam li-īqāẓ al-himam*, *Janāḥ al-najāḥ*, the middle and large *thabat*s | 1 | 4 | 1 |
| One person, several items | al-Kūrānī: Person #283, Book #16 *al-Amam*, the *Janāḥ al-najāḥ* item | 3 | 4 | 1 |
| Heading person ≠ compiler | Person #18 Ibrāhīm al-ʿAlawī; transmissions compiled by his grandson Abū al-Qāsim | 1 | 1 | 2 |
| Whole corpus, no book | #18 «أروي ماله من مروي» | 1 | 1 (`whole_corpus`) | 1 |

What each count measures:

- **Items** → al-Kattānī's arrangement and attention.
- **Objects / works** → the fahrasa literature known to al-Kattānī.
- **Persons** → the distribution and attributes of fahrasa subjects and compilers.

---

## 4. Files and layers

```
data/
  raw/         OpenITI mARkdown file (never modified) + README.md (checksum, provenance)
  interim/     extraction output: JSONL, one record per item; run logs
  processed/   long-format CSV (and/or Parquet) tables; DuckDB database built from them
scripts/
docs/
  codebook.md
  crosswalks/  title_category_crosswalk.csv, place_region_crosswalk.csv, region_codes.csv
```

| Layer | Format | Role |
|---|---|---|
| Text | OpenITI mARkdown | Source of truth for wording and offsets |
| Extraction | JSONL (nested) | LLM output with evidence, offsets, provenance, run metadata |
| Analysis | Long-format CSV/Parquet + DuckDB | Joining and aggregation; generated **only** by script from the extraction layer and manual-correction files |

Manual corrections are never typed into processed tables. They are recorded in `data/interim/corrections/*.csv` (target table, ID, field, old value, new value, reason, date, coder) and applied by script.

### 4.1 Processed tables (overview)

| Table | Grain (one row per…) | Section |
|---|---|---|
| `items.csv` | item | §6.1 |
| `item_segments.csv` | internal segment of an item | §5.3 |
| `references.csv` | cross-reference heading | §6.2 |
| `objects.csv` | transmission object | §7.1 |
| `item_object.csv` | item–object link | §7.2 |
| `object_genre_terms.csv` | genre term occurrence | §7.3 |
| `object_agents.csv` | object–person role | §7.4 |
| `object_contents.csv` | content domain of an object | §7.5 |
| `object_kattani_access.csv` | al-Kattānī's access statement | §8.1 |
| `routes.csv` | transmission route | §8.2 |
| `route_modes.csv` | mode term on a route | §8.2 |
| `item_sources.csv` | source cited by al-Kattānī | §8.3 |
| `assessments.csv` | evaluative statement | §8.5 |
| `persons.csv` | person | §7.6 |
| `item_persons.csv` | item–person link | §7.7 |
| `person_names.csv` | name component | §7.6 |
| `person_nisbas.csv` | nisba | §7.8 |
| `person_titles.csv` | title / epithet | §7.9 |
| `person_affiliations.csv` | madhhab or ṭarīqa | §7.10 |
| `person_places.csv` | person–place relation | §7.11 |
| `person_kattani_relation.csv` | relation to al-Kattānī | §8.4 |
| `dates.csv` | dated event | §10 |
| `external_ids.csv` | external identifier | §6.3 |
| `derived_*.csv` | derived values (§11) | §11 |

---

## 5. Text structure and segmentation

### 5.1 Heading types in the raw text

| Tag | Meaning | Count (observed) | Treatment |
|---|---|---|---|
| `### $` | Person series, numbered 1–662 («من اسمه أحمد» … «الكنى») | — | Item, `printed_series = person` |
| `### $DIC_BIB$` | Book series, numbered 1–563, continuous through the whole text (includes the introduction) | — | Item, `printed_series = book` |
| `### $$$` | Cross-reference heading (with *unẓur*) | 208 | Reference (§6.2) |
| `### $$$` without «انظر» | Probable mis-tag | 18 | Boundary issue; review |
| `### $$$$` | Ḥāfiẓ lists by century | 5 | Item, `item_kind = hafiz_list` |

Total numbered headings: 1,222.

### 5.2 Item boundaries (Stage 1)

1. An item begins at a numbered heading and ends immediately before the next heading of any type, except as provided in rules 2–3.
2. A `### $$$` immediately following a numbered heading **without** «انظر» (12 known cases, e.g. person #283 al-Kūrānī) is treated as continuation text of the preceding item. Record it in `boundary_issues.csv` with `issue = mis_tagged_continuation`.
3. A `$$$` tag inserted mid-line that splits an item (e.g. the al-Suyūṭī item) is likewise treated as continuation. Record it with `issue = split_midline`.
4. All boundary decisions other than rule 1 are listed in `boundary_issues.csv` and set `boundary_status = corrected` on the item.

### 5.3 Internal segments (`item_segments.csv`)

Most items run: ① biography of the author → ② assessment/content of the work(s) → ③ transmission route(s) to al-Kattānī. Segmentation is coded explicitly as the first step of extraction, because it:

- confines person-attribute extraction to the biography segment (nisbas in routes otherwise contaminate author attributes, e.g. «الزبيدي» mostly refers to Murtaḍā al-Zabīdī in routes); and
- allows length to be measured by segment.

| Field | Type | Values / notes |
|---|---|---|
| `segment_id` | string | `S000001` |
| `item_id` | string | |
| `seq` | int | Order within the item; segments may repeat (bio → assessment → route → assessment → route …) |
| `segment_type` | code | `bio`, `assessment`, `route`, `other` |
| `obj_id` | string, nullable | For `assessment` / `route` segments tied to a particular object |
| `char_start`, `char_end` | int | Offsets into the raw file (§5.4) |
| `order_exception` | bool | True if the item departs from the bio → assessment → route order |
| `method` | code | `rule`, `llm`, `manual` |

Cue expressions for `route` (non-exhaustive, for rules and prompts): أرويه، نرويه، أروي، نروي، أخبرنا، حدثنا، عن، ح (taḥwīl).

### 5.4 Offsets and word counts

- **Offsets** are 0-based Unicode code-point offsets into the raw file (UTF-8 decoded), end-exclusive.
- **Normalization** (tatweel removal, alif/yāʾ unification, diacritic stripping) is used **only for matching** and never alters the stored text.
- **Word count:** whitespace-delimited tokens after removing mARkdown markup — heading tags, page markers `PageV..P...`, milestones, line-continuation markers — and footnote markers such as `(1)`. Clitics are not split.

---

## 6. Items, references, identifiers

### 6.1 `items.csv`

| Field | Type | Values / notes |
|---|---|---|
| `item_id` | string | `I0001`… in document order; frozen after Stage 1. Items added later get new IDs appended at the end (P7). |
| `item_kind` | code | `entry`, `hafiz_list` |
| `section` | code | `introduction`, `dictionary`, `other` **[proposed; confirm in Stage 1]** |
| `heading_group_ar` | string | The running sub-section heading, e.g. «من اسمه أحمد», «الكنى» |
| `printed_series` | code | `person`, `book`, `none` |
| `printed_number_raw` | int | As in the digital text |
| `printed_number_corrected` | int, nullable | Filled only when corrected |
| `number_issue` | code | `none`, `duplicate`, `misprint`, `gap_before`, `other`. Known cases: book 15 / 233 / 392 duplicated; person 253 duplicated; person 140 misprinted as 733; person 65, 80, 184, … missing. |
| `heading_ar` | string | Heading text as written |
| `heading_translit` | string | |
| `vol_start`, `page_start`, `vol_end`, `page_end` | int | From `PageV..P...` markers (ʿAbbās edition) |
| `char_start`, `char_end` | int | |
| `word_count_total` | int | §5.4 |
| `word_count_bio`, `word_count_assessment`, `word_count_route`, `word_count_other` | int | Sums over segments |
| `boundary_status` | code | `auto`, `verified`, `corrected` |
| `notes` | string | |

The book-series entries in the introduction (*awāʾil* works, book 1–12; *arbaʿūn* works, book 13–15) are ordinary items with `section = introduction`. Whether to include them in an analysis is a filter (P1).

### 6.2 `references.csv`

| Field | Type | Values / notes |
|---|---|---|
| `ref_id` | string | `R0001`… |
| `heading_ar` | string | e.g. «أحمد بن علي ابن حجر» |
| `full_text_ar` | string | e.g. «هو الحافظ (انظر حرف الحاء)» |
| `after_item_id` | string | The item immediately preceding the reference |
| `vol`, `page`, `char_start`, `char_end` | | |
| `target_hint_ar` | string | e.g. «انظر حرف الحاء» |
| `target_item_id` | string, nullable | Resolved target |
| `target_person_id` | string, nullable | Resolved person |
| `resolution_status` | code | `resolved`, `ambiguous`, `unresolved` |
| `name_form_type` | code | Form under which the reference is filed: `ism`, `kunya`, `laqab`, `shuhra`, `nisba`, `other` |

Uses: alias lists for entity resolution; data on al-Kattānī's filing choices; detection of mis-tagged `$$$`.

### 6.3 Identifiers and `external_ids.csv`

- **Internal IDs:** `I` item, `R` reference, `O` object, `P` person, `S` segment, `D` date, `T` route, `A` assessment. Zero-padded; never reused.
- **Places:** al-Thurayya gazetteer URIs.

`external_ids.csv`

| Field | Type | Values / notes |
|---|---|---|
| `entity_type` | code | `person`, `object` |
| `entity_id` | string | |
| `scheme` | code | `openiti_author_uri`, `openiti_text_uri`, `wikidata_qid`, `alam_ref` (al-Ziriklī, *al-Aʿlām*, vol:page); reserved: `ainet_id`, `ibn_ghazi_kg_id` |
| `value` | string | |
| `match_confidence` | code | `exact`, `probable`, `possible` |
| `matched_by` | code | `manual`, `script`, `llm` |
| `note` | string | |

---

## 7. Objects and persons

### 7.1 `objects.csv`

| Field | Type | Values / notes |
|---|---|---|
| `obj_id` | string | |
| `title_ar` | string, nullable | As written; null if untitled |
| `title_translit` | string, nullable | |
| `object_type` | code | `standalone_work`, `part_of_work`, `whole_corpus` (e.g. «ما له من مروي»), `unknown` |
| `attestation` | code | `headed` (has its own item or is the main object of an item), `mention_only` |
| `form_as_stated` | code | `printed`, `manuscript`, `unknown` — as stated by al-Kattānī, i.e. status in his time |
| `extent_as_written_ar` | string, nullable | e.g. «في كراريس», «في مجلد» |
| `extent_unit` | code | `kurrasa`, `mujallad`, `juz`, `waraqa`, `other`, `none_stated` |
| `extent_quantity` | number, nullable | Only when stated |
| `includes_musalsalat` | code | `yes`, `no_mention` |
| `includes_awail` | code | `yes`, `no_mention` |
| `notes` | string | |

Default analytic sets:
- **works** = `object_type = standalone_work`
- **main set** = works with `attestation = headed`
- `mention_only` objects are used for sensitivity analysis.

### 7.2 `item_object.csv`

| Field | Values |
|---|---|
| `item_id`, `obj_id` | |
| `relation` | `describes` (main object), `mentions` |
| `seq` | order of first appearance in the item |

### 7.3 `object_genre_terms.csv`

| Field | Values / notes |
|---|---|
| `obj_id`, `item_id` | |
| `term` | `fahrasa`, `thabat`, `barnamaj`, `mashyakha`, `mujam`, `ijaza`, `musalsalat`, `awail`, `arbaun`, `other` |
| `term_ar` | As written (فهرسة، ثبت، برنامج، مشيخة، معجم، إجازة، مسلسلات، أوائل، أربعون …) |
| `locus` | `title` (part of the title), `kattani_label` (al-Kattānī calls it so), `author_self_label`, `quoted_source` |
| `evidence_ar`, `char_start`, `char_end`, `provenance` | §9 |

### 7.4 `object_agents.csv`

| Field | Values / notes |
|---|---|
| `obj_id`, `person_id` | |
| `role` | `subject` (person whose teachers/transmissions are recorded), `compiler`, `abridger`, `continuator` (*dhayl*, *istidrāk*), `versifier`, `commentator`, `other` |
| `evidence_ar`, `char_start`, `char_end`, `provenance` | |

Both `subject` and `compiler` are recorded wherever identifiable, so either can serve as the analytic axis (D4). When the subject compiled his own fahrasa, the same person gets both roles.

### 7.5 `object_contents.csv`

| Field | Values / notes |
|---|---|
| `obj_id` | |
| `domain` | `hadith`, `fiqh`, `usul`, `kalam`, `tasawwuf`, `qiraat`, `tafsir`, `arabic_language`, `adab`, `history_biography`, `other` |
| `evidence_ar`, `char_start`, `char_end`, `provenance` | |

`hadith_only` is derived (§11.6).

### 7.6 `persons.csv` and `person_names.csv`

`persons.csv`

| Field | Type | Values / notes |
|---|---|---|
| `person_id` | string | |
| `display_name_translit` | string | Short IJMES form, e.g. *Ibrāhīm al-Kūrānī* |
| `display_name_ar` | string | |
| `gender` | code | `male`, `female`, `unknown` |
| `is_kattani` | bool | True only for al-Kattānī himself |
| `notes` | string | |

`person_names.csv`

| Field | Values / notes |
|---|---|
| `person_id` | |
| `name_type` | `ism`, `nasab`, `kunya`, `laqab`, `shuhra`, `other` |
| `value_ar`, `value_translit` | |
| `seq` | |
| `item_id`, `evidence_ar`, `char_start`, `char_end`, `provenance` | |

Nisbas are coded separately (§7.8).

### 7.7 `item_persons.csv`

| Field | Values |
|---|---|
| `item_id`, `person_id` | |
| `role` | `heading_person`, `mentioned_bio` (named in the biography segment as a relative, teacher, etc.) |

### 7.8 `person_nisbas.csv`

| Field | Values / notes |
|---|---|
| `person_id`, `seq` | |
| `nisba_ar`, `nisba_translit` | e.g. الفاسي |
| `nisba_type` | `geographic`, `genealogical`, `madhhab`, `tariqa`, `occupational`, `other`, `unknown` |
| `item_id`, `evidence_ar`, `char_start`, `char_end`, `provenance` | |

Rules:
- Extract nisbas **only from `bio` segments and headings**.
- A geographic nisba also generates a row in `person_places.csv` with `relation = nisba`.

### 7.9 `person_titles.csv`

| Field | Values / notes |
|---|---|
| `person_id`, `seq` | `seq` is the order in the text |
| `title_ar`, `title_translit` | As written: الحافظ، المحدث، المسند، العارف، الفقيه، … |
| `item_id` | Item in which the title is given |
| `attributed_by` | `kattani`, `quoted_source` |
| `source_ref` | If `quoted_source`: `item_sources` row or free text |
| `evidence_ar`, `char_start`, `char_end`, `provenance` | |

Category mapping is done only through `docs/crosswalks/title_category_crosswalk.csv` (§11.5). It is many-to-many, versioned, and never written into this table.

### 7.10 `person_affiliations.csv`

| Field | Values / notes |
|---|---|
| `person_id` | |
| `aff_type` | `madhhab`, `tariqa`, `other` |
| `value` | madhhab: `maliki`, `hanafi`, `shafii`, `hanbali`, `zahiri`, `other`; ṭarīqa: transliterated name, e.g. `shadhiliyya`, `naqshbandiyya` |
| `value_ar` | |
| `evidence_ar`, `char_start`, `char_end`, `provenance` | |

**No default inference:** a madhhab is not inferred from region (e.g. Mālikī for Maghribīs). If an inference is ever recorded, it must have `provenance = inferred` and a basis note, and it is excluded from default analyses.

### 7.11 `person_places.csv`

| Field | Values / notes |
|---|---|
| `person_id`, `seq` | `seq` follows the life sequence where the text implies it (e.g. «الفاسي ثم المدني» → Fes 1, Medina 2) |
| `place_ar`, `place_translit` | |
| `thurayya_uri` | Nullable until resolved |
| `relation` | `nisba`, `origin`, `birth`, `residence`, `sojourn` (temporary stay, study travel, pilgrimage), `death`, `burial` |
| `cue_ar` | The expression grounding the relation: نزيل، دفين، ثم، ولد ب، توفي ب … |
| `item_id`, `evidence_ar`, `char_start`, `char_end`, `provenance` | |

Notes:
- **نزيل** (*nazīl*) → `residence`; **دفين** (*dafīn*) → `burial`.
- A nisba is evidence of origin or affiliation, **not of residence**; keep it as `nisba` unless the text states more.

---

## 8. Al-Kattānī's vantage point

### 8.1 `object_kattani_access.csv`

| Field | Values / notes |
|---|---|
| `obj_id`, `item_id` | |
| `access` | `transmits` (أرويه/نرويه), `seen` (وقفت عليه), `owns` (عندي), `autograph_seen` (بخطه), `not_seen` (لم أقف عليه), `known_by_report`, `other` |
| `expression_ar`, `evidence_ar`, `char_start`, `char_end`, `provenance` | |

Multiple rows per object are allowed.

### 8.2 `routes.csv` and `route_modes.csv`

A **route** is one complete chain from al-Kattānī to the target person (the object's subject or compiler). Each *taḥwīl* (ح) that yields a distinct path produces a separate route.

`routes.csv`

| Field | Type | Values / notes |
|---|---|---|
| `route_id` | string | `T00001` |
| `item_id`, `obj_id` | | `obj_id` nullable if the route covers the whole item |
| `target_person_id` | string, nullable | |
| `seq` | int | Order within the item |
| `char_start`, `char_end` | int | |
| `n_links` | int, nullable | Number of intermediaries **strictly between** al-Kattānī and the target. Al-Kattānī → A → B → target gives `n_links = 2`. |
| `reconstruction_status` | code | `clear`, `ambiguous` (e.g. unclear ح junctions), `not_reconstructable` |
| `uluww_claim` | bool | Al-Kattānī explicitly claims a high (short) route (عالٍ، علو …) |
| `uluww_evidence_ar` | string, nullable | |
| `provenance` | code | |

`route_modes.csv`

| Field | Values |
|---|---|
| `route_id`, `seq` | |
| `mode` | `sama`, `qiraa`, `ijaza`, `ijaza_amma`, `mukataba`, `munawala`, `unknown` — aligned with the AINet-DB transmission-type vocabulary |
| `expression_ar`, `evidence_ar`, `char_start`, `char_end` | |

Derived per item / object (§11.7): `n_routes`, `min_links`.

**Out of scope for v0.1:** persons along routes. Table `route_links.csv` (route_id, position, person_id, mode) is reserved for a later layer.

### 8.3 `item_sources.csv`

| Field | Values / notes |
|---|---|
| `item_id`, `seq` | |
| `source_type` | `written`, `oral`, `unspecified` |
| `source_title_ar` | e.g. البدور الضاوية |
| `source_obj_id`, `source_person_id` | Nullable; link when the cited source is itself in the dataset |
| `citation_formula_ar` | e.g. قال في … ، نقل … ، أخبرني … |
| `evidence_ar`, `char_start`, `char_end`, `provenance` | |

### 8.4 `person_kattani_relation.csv`

| Field | Values / notes |
|---|---|
| `person_id` | |
| `relation` | `self`, `kattani_family`, `direct_teacher` (شيخنا …), `teacher_of_teacher`, `student`, `correspondent`, `contemporary_met`, `contemporary_not_met`, `no_contact`, `unknown` |
| `evidence_ar`, `char_start`, `char_end`, `provenance` | |

Multiple rows are allowed (e.g. `kattani_family` + `direct_teacher`). Al-Kattānī's own works (e.g. book #12) are linked to the person with `is_kattani = true` via `object_agents`, and that person carries `relation = self`.

### 8.5 `assessments.csv`

| Field | Values / notes |
|---|---|
| `assessment_id` | `A00001` |
| `item_id` | |
| `target_type` | `person`, `object`, `route`, `other` |
| `target_id` | |
| `assessment_type` | `praise`, `criticism`, `rarity_claim`, `authenticity_doubt`, `usefulness`, `other` |
| `polarity` | `positive`, `negative`, `mixed`, `neutral` |
| `attributed_by` | `kattani`, `quoted_source` |
| `expression_ar`, `evidence_ar`, `char_start`, `char_end`, `provenance` | |

Titles (§7.9) and access statements (§8.1) are not duplicated here.

---

## 9. Provenance, evidence, missing values

Every row in the long tables carries:

| Field | Values / notes |
|---|---|
| `provenance` | `stated` (explicit in al-Kattānī's text, including his quotations), `inferred` (our reasoning from the text; requires `note`), `external` (from an external authority; requires `source_ref`), `unknown`, `not_applicable` |
| `evidence_ar` | Verbatim Arabic from the raw file. Required for `stated` and `inferred`. |
| `char_start`, `char_end` | Required whenever `evidence_ar` is given |
| `run_id` | Extraction run that produced the value, or `manual` |
| `source_ref` | For `external`: e.g. `alam:1:123`, `wikidata:Q…` |
| `note` | |

**Missing values**
- An empty cell means *not coded*.
- `unknown` and `not_applicable` are explicit codes, used only in categorical fields.
- "The text does not mention X" is expressed by the **absence of a row** in a long table. If a coder has positively checked a variable for an item and found nothing, record it in `coverage.csv` (item_id, variable, checked = true).

**Conflicts between text and external authorities.** Keep both values as separate rows with different provenance. Derived variables use the precedence in §11.

---

## 10. Dates (`dates.csv`)

| Field | Type | Values / notes |
|---|---|---|
| `date_id` | string | `D00001` |
| `entity_type`, `entity_id` | | `person` or `object` |
| `event` | code | `birth`, `death`, `floruit` (كان حيا سنة …), `composition`, `completion`, `ijaza_granted`, `other` |
| `calendar` | code | `ah` |
| `year_min`, `year_max` | int, nullable | Interval in AH; equal for point dates |
| `qualifier` | code | See table below |
| `as_written_ar` | string | Verbatim expression |
| `reconstructed` | bool | True when the year was completed or corrected (abbreviated year, typo) |
| `reconstruction_note` | string | |
| `variant_group` | string, nullable | Shared by alternative reports of the same event (وقيل …) |
| `preferred_in_text` | bool | The variant al-Kattānī adopts, if any |
| `provenance`, `source_ref`, `evidence_ar`, `char_start`, `char_end` | | |

### 10.1 Qualifier rules

| Expression | `qualifier` | `year_min` | `year_max` |
|---|---|---|---|
| سنة 1052 | `exact` | 1052 | 1052 |
| نيف وأربعين وتسعمائة | `nayyif` | 941 | 949 |
| بعد سنة 1100 | `after` | 1100 | null |
| قبل سنة 1100 | `before` | null | 1100 |
| في حدود / نحو / قرابة سنة 1100 | `circa` | 1100 | 1100 |
| كان حيا سنة 1100 | `exact`, with `event = floruit` | 1100 | 1100 |
| أوائل / أواسط / أواخر القرن العاشر | `century_early` / `century_mid` / `century_late` | 901 | 1000 |
| في القرن العاشر | `century` | 901 | 1000 |

Rules:
- **نيف** (*nayyif*): general sense, units 1–9 above the stated decade (D7).
- **circa:** no interval is invented; the stated year is recorded as a point and the qualifier marks the uncertainty (D8).
- **Within-century qualifiers** (early, mid, late) do not narrow the interval; the qualifier carries the information.
- **Abbreviated years** (e.g. «ولد سنة 96» in Person #5 Ibn al-Qāḍī): complete them from context (the century of the person's other dates, teachers, or the surrounding entries), set `reconstructed = true`, and state the basis in `reconstruction_note`.
- **Typos** (e.g. «عام1.32» in Person #4 Aḥmad Bābā → 1032): keep `as_written_ar` unchanged, put the corrected year in `year_min`/`year_max`, and set `reconstructed = true`.
- `floruit` is never coded as `death`.

CE values (`ce_min`, `ce_max`) are derived (§11.2).

---

## 11. Derived variables and rules

Each derived table stores `rule_id` and the codebook version it was built against.

### 11.1 Anchor date per person — `R-DATE-1` **[proposed]**

1. Preferred `death` date, stated in the text.
2. Otherwise, a `death` date from an external authority.
3. Otherwise, `floruit` (flagged `anchor_is_floruit = true`).
4. Otherwise, null.

Where a variant group exists, use `preferred_in_text`; otherwise use the earliest-recorded variant and flag it.

### 11.2 CE conversion — `R-CE-1`

Convert `year_min` → `ce_min` using the first day of that AH year, and `year_max` → `ce_max` using the last day of that AH year (tabular calendar).

### 11.3 Century allocation — `R-CENT-1`

- AH century *c* covers years 100(*c*−1)+1 to 100*c* (the 10th century = 901–1000).
- For a closed interval [*a*, *b*], each century receives the weight (number of years of [*a*, *b*] falling in that century) / (*b* − *a* + 1). Point dates receive weight 1 (**proportional allocation**, D9).
- Open intervals (`after`, `before`) are **not allocated** in default analyses (weight recorded as null). **[proposed]**
- The convention must be checked against al-Kattānī's own ḥāfiẓ lists (§13).

Output: `derived_person_century.csv` (person_id, century, weight, rule_id).

### 11.4 Primary place and region — `R-PLACE-1`

Primary place is the first available of:
1. the last `residence` (highest `seq`);
2. `death`;
3. `burial`;
4. `birth` / `origin`;
5. a geographic `nisba`.

Within each rule, use stated values before external ones.

Region is assigned via `docs/crosswalks/place_region_crosswalk.csv` (thurayya_uri → region code). City-level values are always retained, so sub-regional analysis (e.g. within the Maghrib: Fes, Marrakesh, Sūs, Tetouan, Ifrīqiya) remains possible.

Output: `derived_person_place.csv` (person_id, place, region, rule_step, rule_id).

**Region codes [proposed]:** `maghrib_aqsa`, `maghrib_central`, `ifriqiya`, `andalus`, `egypt`, `hijaz`, `yemen`, `sham`, `iraq`, `iran_central_asia`, `india`, `rum`, `bilad_al_sudan`, `other`. To be finalized after the place data from Stage 2 have been observed.

### 11.5 Title categories — `R-TITLE-1`

`title_category_crosswalk.csv` has the fields `title_ar`, `category`, `crosswalk_version`, `note`. It is many-to-many, and a title may map to several categories.

**Categories [proposed]:** `hadith`, `law`, `theology`, `sufism`, `quranic_sciences`, `language_literature`, `office_rank`, `general_honorific`. To be finalized from the observed title inventory.

### 11.6 Content — `R-CONTENT-1`

`hadith_only = true` if the object's only `domain` rows are `hadith`; `false` if any other domain is present; `null` if there are no domain rows.

### 11.7 Routes and attention — `R-ROUTE-1`, `R-ATTN-1`

- Per object and per item: `n_routes`, and `min_links` (minimum `n_links` over routes with `reconstruction_status = clear`).
- Attention metrics are the segment word counts from `items.csv`. They are reported per segment type, not only in total.

### 11.8 Analytic axis — `R-AXIS-1`

`derived_object_axis.csv` lists, for each object, both the `subject` and the `compiler` person_id, so analyses can be run on either axis (D4).

---

## 12. Decision log

| ID | Date | Decision |
|---|---|---|
| D1 | 2026-10-11 | Introductory *awāʾil* (book 1–12) and *arbaʿūn* (book 13–15) items are coded as ordinary items (`section = introduction`); inclusion is an analysis-time filter. The book series (`$DIC_BIB$`) is a single continuous sequence 1–563 across the whole text. |
| D2 | 2026-10-11 | Untitled whole-corpus transmissions («ما له من مروي») are coded as transmission objects with `object_type = whole_corpus`; "works" are the `standalone_work` subset. |
| D3 | 2026-10-11 | Mention-only works are included with `attestation = mention_only` and used mainly for sensitivity analysis. |
| D4 | 2026-10-11 | Both subject and compiler are recorded; either can serve as the analytic axis. |
| D5 | 2026-10-11 | Titles are recorded verbatim in long format; categories only via a separate, versioned many-to-many crosswalk. |
| D6 | 2026-10-11 | Places are recorded at city level with relation types in long format; regions via a crosswalk; primary place by `R-PLACE-1`. |
| D7 | 2026-10-11 | نيف = units 1–9 (general sense). |
| D8 | 2026-10-11 | No interval is invented for circa expressions. |
| D9 | 2026-10-11 | Cross-century intervals are allocated proportionally. |
| D10 | 2026-10-11 | Data, field names, codes, and this codebook are in English; Arabic is preserved in `_ar` fields; transliteration is IJMES. |
| D11 | 2026-10-11 | Internal person IDs are project-local; reserved external schemes `ainet_id` and `ibn_ghazi_kg_id`; OpenITI URIs and Wikidata QIDs are recorded now. |
| D12 | 2026-10-11 | Cross-reference headings are recorded in `references.csv` and resolved to target items and persons. |
| D13 | 2026-10-11 | Persons along transmission routes are deferred to a later layer (`route_links.csv` reserved). |

---

## 13. Open issues

1. **Century convention:** Check al-Kattānī's assignment of boundary years (e.g. d. 1000 vs. 1001) in his ḥāfiẓ lists; record any divergence from `R-CENT-1`.
2. **Open intervals** (`after`, `before`) in century allocation: currently not allocated **[proposed]**.
3. **Anchor date fallback** `R-DATE-1` **[proposed]**.
4. **`section` codes:** confirm the actual structural divisions of the text in Stage 1.
5. **Printed numbering:** determine whether the item numbers are the editor's (ʿAbbās) or al-Kattānī's.
6. **Region and title-category codes:** finalize after the observed inventories from Stage 2.
7. **ḥāfiẓ lists (`$$$$`):** decide whether they are coded as a separate person list (al-Kattānī's own canon of *ḥuffāẓ*) or only kept as items.
8. **Ambiguous ح junctions:** develop reconstruction guidance after piloting on a sample.
9. **`kattani_family`:** define its scope (agnatic Kattānī lineage only, or including in-laws).

---

## 14. Extraction and validation (interim layer)

### 14.1 JSONL record (one per item; abbreviated)

```json
{
  "schema_version": "0.1",
  "run_id": "run_2026xxxx_01",
  "item_id": "I0283",
  "segments": [
    {"seq": 1, "segment_type": "bio", "char_start": 0, "char_end": 0}
  ],
  "persons": [
    {
      "local_ref": "p1",
      "role_in_item": "heading_person",
      "titles": [
        {"title_ar": "…", "seq": 1, "attributed_by": "kattani",
         "evidence_ar": "…", "char_start": 0, "char_end": 0, "provenance": "stated"}
      ],
      "places": [],
      "dates": []
    }
  ],
  "objects": [],
  "routes": [],
  "assessments": [],
  "sources": []
}
```

Persons and objects carry item-local references (`local_ref`). Global IDs (`P…`, `O…`) are assigned at the entity-resolution step, never by the LLM.

### 14.2 Run log (`data/interim/runs.csv`)

`run_id`, `date`, `model`, `model_version`, `prompt_id`, `prompt_sha256`, `schema_version`, `codebook_version`, `item_ids`, `notes`.

### 14.3 Validation

**Hard errors** (reject and retry):
- schema violation;
- `evidence_ar` not found verbatim (after normalization, §5.4) within the item;
- offsets outside the item;
- a person attribute whose evidence lies in a `route` segment.

**Soft flags** (keep and review):
- birth > death;
- lifespan > 100 years (long-lived *muʿammarūn* are historically meaningful; flag, do not reject);
- a reconstructed year;
- `n_links` implausible for the time gap;
- `mention_only` objects with very long descriptions.

### 14.4 Human verification

- Draw a stratified random sample by `section` × `printed_series` × length decile × anchor century.
- Long items are over-sampled.
- An acceptance threshold is set **per variable** before review.
- Verification results go to `data/interim/verification.csv` (item_id, variable, value_id, verdict, corrected_value, coder, date).

---

## 15. Stage 1 deliverables (item table and boundary review)

1. `items.csv`, with all fields except the segment word counts.
2. `references.csv`, with `target_item_id` resolved where possible.
3. `boundary_issues.csv`: issue type, location, proposed action.
4. `numbering_issues.csv`: duplicates, gaps, misprints in both series.
5. `date_expression_counts.csv`: frequency of the date expressions in §10.1 across the text. This shows which date rules materially affect results.
6. `data/raw/README.md`: source citation, OpenITI URI, retrieval date, SHA-256 checksum.
