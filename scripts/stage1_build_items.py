#!/usr/bin/env python3
"""Stage 1: item table, references, and boundary / numbering review lists.

Implements codebook v0.1, sections 5, 6 and 15. Standard library only.

Usage (from the repository root):
    python -I -X utf8 scripts/stage1_build_items.py

Outputs:
    data/processed/items.csv
    data/processed/references.csv
    data/interim/stage1/boundary_issues.csv
    data/interim/stage1/numbering_issues.csv
    data/interim/stage1/date_expression_counts.csv
    data/interim/stage1/stage1_summary.json
"""
import csv
import hashlib
import json
import re
from bisect import bisect_left
from pathlib import Path

CODEBOOK_VERSION = "0.1"
ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data/raw/1382Kattani.FahrasFaharis.Shamela0001037-ara1.completed.mARkdown"
OUT_PROCESSED = ROOT / "data/processed"
OUT_STAGE1 = ROOT / "data/interim/stage1"

# --- heading patterns (codebook §5.1) ---------------------------------------
RE_SECTION = re.compile(r"^### (\|+) ?(.*)$")
RE_NUMBERED = re.compile(r"^### (\$DIC_BIB\$|\$\$?)\s+(?:ms\d+\s+)?(\d+)\s*(?:ms\d+\s*)?-\s*(.*)$")
RE_HAFIZ = re.compile(r"^### \$\$\$\$\s*(.*)$")
RE_REF = re.compile(r"^### \$\$\$(?!\$)\s*(.*)$")

# --- markup removal (codebook §5.4) -----------------------------------------
RE_PAGE = re.compile(r"PageV(\d+)P(\d+)")
RE_MILESTONE = re.compile(r"(?<![A-Za-z])ms\d+")
RE_FOOTNOTE = re.compile(r"\(\d+\)")
RE_TAG_NUMBERED = re.compile(r"^### (\$DIC_BIB\$|\$+)\s*(?:ms\d+\s+)?(?:\d+\s*(?:ms\d+\s*)?-)?")
RE_TAG_ONLY = re.compile(r"^### (\$DIC_BIB\$|\$+|\|+)")
RE_WORDCHAR = re.compile(r"\w")

YEAR_CUE_END = re.compile(r"(سنة|عام)\s*$")
REF_HEAD = re.compile(r"^\s*[^:،.()]{1,80}?\s*(\(\d+\))?\s*:")
REF_CUE = re.compile(r"انظر|سبق|تقدم")
REF_NAME_HINT = re.compile(r"^\s*[^.،:()\"]{2,80}?\s*\(\s*(?:و?انظر|سبق|تقدم)")
ROUTE_CUE = re.compile(r"أرويه|نرويه|أرويها|نرويها|أروي|نروي")
UNTAGGED_HEAD = re.compile(r"^# ([^:()\n]{2,60}?)\s*\(\d+\)\s*:")

AR_DIACRITICS = re.compile(r"[ً-ْٰـ]")


def norm(s):
    """Normalization for matching only (codebook §5.4); never stored."""
    s = AR_DIACRITICS.sub("", s)
    s = re.sub("[أإآٱ]", "ا", s)
    s = s.replace("ى", "ي").replace("ة", "ه")
    return re.sub(r"\s+", " ", s).strip()


def strip_markup(line, keep_number=False):
    """Remove mARkdown markup from one line, for display text and word counts."""
    if keep_number:
        line = RE_TAG_ONLY.sub("", line)
    else:
        line = RE_TAG_NUMBERED.sub("", line)
        line = RE_TAG_ONLY.sub("", line)
    line = RE_PAGE.sub(" ", line)
    line = RE_MILESTONE.sub(" ", line)
    line = re.sub(r"^(~~|# )", "", line)
    return line


def display(text):
    return re.sub(r"\s+", " ", RE_FOOTNOTE.sub(" ", text)).strip()


def word_count(text):
    return sum(1 for t in RE_FOOTNOTE.sub(" ", text).split() if RE_WORDCHAR.search(t))


def main():
    raw_bytes = RAW.read_bytes()
    text = raw_bytes.decode("utf-8")
    assert "\r" not in text, "CR characters found; offsets assume LF line endings"
    lines = text.split("\n")
    line_off = []
    pos = 0
    for ln in lines:
        line_off.append(pos)
        pos += len(ln) + 1

    # Page markers: OpenITI places PageV..P... at the END of the page it closes,
    # so a character belongs to the first marker at or after it.
    markers = [(m.start(), int(m.group(1)), int(m.group(2))) for m in RE_PAGE.finditer(text)]
    marker_pos = [m[0] for m in markers]

    def page_at(off):
        i = bisect_left(marker_pos, off)
        if i == len(markers):
            return markers[-1][1], markers[-1][2]
        return markers[i][1], markers[i][2]

    body_start = next(i for i, ln in enumerate(lines) if ln.startswith("#META#Header#End#")) + 1

    # ---- pass 1: classify lines ------------------------------------------------
    ev = []  # one dict per line from body_start
    for i in range(body_start, len(lines)):
        ln = lines[i]
        e = {"i": i, "line": ln, "kind": "text"}
        if not ln.strip():
            e["kind"] = "blank"
        elif m := RE_SECTION.match(ln):
            e.update(kind="section", level=len(m.group(1)), text=m.group(2).strip())
        elif m := RE_HAFIZ.match(ln):
            e.update(kind="hafiz", text=m.group(1))
        elif m := RE_REF.match(ln):
            e.update(kind="ref", text=m.group(1))
        elif m := RE_NUMBERED.match(ln):
            series = "book" if m.group(1) == "$DIC_BIB$" else "person"
            e.update(kind="numbered", series=series, number=int(m.group(2)),
                     rest=m.group(3), tag=m.group(1))
        elif ln.startswith("###"):
            e["kind"] = "unknown_heading"
        ev.append(e)

    def prev_content(k):
        """Text of the nearest preceding non-blank line, page markers stripped."""
        for j in range(k - 1, -1, -1):
            if ev[j]["kind"] == "blank":
                continue
            content = RE_MILESTONE.sub("", RE_PAGE.sub("", ev[j]["line"]))
            content = re.sub(r"^(~~|# )", "", content).rstrip()
            if content:
                return content, ev[j]
        return "", None

    def ref_text(k):
        """A $$$ line plus its ~~ continuation lines."""
        parts = [ev[k]["text"]]
        j = k + 1
        while j < len(ev) and ev[j]["line"].startswith("~~"):
            parts.append(ev[j]["line"][2:])
            j += 1
        return " ".join(parts), j

    issues = []

    def issue(kind, k, action, needs_review=True, item_ref=None, end_line=None, extra=None):
        e = ev[k]
        start = line_off[e["i"]]
        end = line_off[end_line] - 1 if end_line is not None else start + len(e["line"])
        issues.append({
            "issue": kind, "line_no": e["i"] + 1, "char_start": start, "char_end": end,
            "item_ref": item_ref, "printed_series": e.get("series", ""),
            "printed_number": e.get("number", ""),
            "context_ar": display(" ".join(strip_markup(ev[x]["line"], keep_number=True)
                                   for x in range(k, min(k + 3, len(ev)))))[:160],
            "action_taken": action, "needs_review": needs_review, "detail": extra or "",
        })

    # ---- pass 2: decide which headings start items --------------------------------
    for k, e in enumerate(ev):
        if e["kind"] == "numbered":
            pc, _ = prev_content(k)
            if YEAR_CUE_END.search(pc):
                e["role"] = "continuation"
                e["why"] = "false_heading_year"
            else:
                e["role"] = "item_start"
        elif e["kind"] == "hafiz":
            e["role"] = "item_start"
        elif e["kind"] == "ref":
            _, pe = prev_content(k)
            t, _ = ref_text(k)
            if pe is not None and pe["kind"] == "numbered" and pe.get("role") == "item_start" \
                    and not display(strip_markup(pe["line"])):
                e["role"] = "continuation"
                e["why"] = "mis_tagged_continuation"
            elif len(display(t)) <= 300 and REF_CUE.search(t) and (
                    REF_HEAD.match(t) or REF_NAME_HINT.match(t)):
                e["role"] = "reference"
            else:
                e["role"] = "continuation"
                e["why"] = "split_midline"
        elif e["kind"] in ("section", "unknown_heading"):
            e["role"] = "boundary"
        else:
            e["role"] = "content"

    # ---- pass 3: build items, references, and spans --------------------------
    items, refs = [], []
    l1 = l2 = l3 = ""
    dict_start = khatima_start = None
    cur = None
    cur_ref = None
    unassigned = None  # (start_k, end_k) of text outside any item, after a reference or in the dictionary

    def section_of(i):
        if dict_start is None or i < dict_start:
            return "introduction"
        if khatima_start is None or i < khatima_start:
            return "dictionary"
        return "other"

    def close_unassigned(end_k):
        nonlocal unassigned
        if unassigned:
            sk = unassigned[0]
            issue("unassigned_text", sk,
                  "left outside any item; review (new item or merge)",
                  end_line=ev[end_k]["i"] if end_k < len(ev) else len(lines),
                  item_ref=f"#{len(items)}" if items else None,
                  extra=f"lines {ev[sk]['i'] + 1}-{ev[end_k - 1]['i'] + 1}")
            unassigned = None

    def close_item(end_k):
        nonlocal cur
        if cur is None:
            return
        end_line = ev[end_k]["i"] if end_k < len(ev) else len(lines)
        cur["_end_line"] = end_line
        items.append(cur)
        cur = None

    after_ref = False
    for k, e in enumerate(ev):
        role = e.get("role")
        if e["kind"] == "section":
            close_item(k)
            close_unassigned(k)
            after_ref = False
            if e["level"] == 1:
                l1, l2, l3 = e["text"], "", ""
                if e["text"].startswith("[خاتمة]"):
                    khatima_start = e["i"]
            elif e["level"] == 2:
                l2, l3 = e["text"], ""
                if dict_start is None and re.match(r"من [اأ]سمه", e["text"]):
                    dict_start = e["i"]
            else:
                l3 = e["text"]
            continue
        if e["kind"] == "unknown_heading":
            close_item(k)
            close_unassigned(k)
            issue("unknown_heading", k, "treated as a boundary")
            continue
        if role == "item_start":
            close_item(k)
            close_unassigned(k)
            after_ref = False
            group = " > ".join(x for x in (l1, l2, l3) if x)
            cur = {
                "_k": k, "_start_line": e["i"],
                "item_kind": "hafiz_list" if e["kind"] == "hafiz" else "entry",
                "section": section_of(e["i"]),
                "heading_group_ar": group,
                "_letter": l1 if l1.startswith("حرف") else ("حرف الألف" if section_of(e["i"]) == "dictionary" else ""),
                "printed_series": e.get("series", "none"),
                "printed_number_raw": e.get("number", ""),
                "_issues": [],
            }
            if e["kind"] == "numbered" and e["tag"] == "$$":
                issue("tag_variant", k, "read as person-series heading", needs_review=False,
                      extra="tag '### $$' instead of '### $'")
                cur["_issues"].append("tag_variant")
            continue
        if role == "reference":
            close_item(k)
            close_unassigned(k)
            t, _ = ref_text(k)
            cur_ref = {"_k": k, "_text": t, "_after_item": items[-1] if items else None,
                       "_group_letter": l1 if l1.startswith("حرف") else ("حرف الألف" if section_of(e["i"]) == "dictionary" else "")}
            refs.append(cur_ref)
            if ROUTE_CUE.search(t):
                issue("reference_with_content", k,
                      "kept as reference; contains a transmission cue, may be an untagged item")
            after_ref = True
            continue
        if role == "continuation":
            if cur is not None:
                issue(e["why"], k, f"treated as continuation of the preceding item",
                      item_ref=f"#{len(items) + 1}",
                      needs_review=e["why"] != "mis_tagged_continuation")
                cur["_issues"].append(e["why"])
            else:
                issue("possible_untagged_item", k,
                      "not a reference and no open item; left outside any item",
                      extra="'### $$$' text after a reference; may be an untagged item")
            continue
        # content / blank lines
        if cur is None and e["kind"] == "text":
            in_dict = section_of(e["i"]) == "dictionary"
            continues_ref = after_ref and e["line"].startswith("~~")
            if (in_dict or after_ref) and not continues_ref and unassigned is None:
                unassigned = (k,)
            if not after_ref and not in_dict:
                pass  # narrative text in the introduction: expected, not an issue
    close_item(len(ev))
    close_unassigned(len(ev))

    # ---- item ids, offsets, pages, headings, word counts ---------------------------
    for n, it in enumerate(items, 1):
        it["item_id"] = f"I{n:04d}"
    # resolve placeholder item refs (#n) in issues
    for iss in issues:
        r = iss["item_ref"]
        if isinstance(r, str) and r.startswith("#"):
            iss["item_ref"] = items[int(r[1:]) - 1]["item_id"]

    for it in items:
        s_line, e_line = it["_start_line"], it["_end_line"]
        block = lines[s_line:e_line]
        while block and not block[-1].strip():
            block.pop()
            e_line -= 1
        it["char_start"] = line_off[s_line]
        it["char_end"] = line_off[e_line - 1] + len(lines[e_line - 1])
        it["_line_start"], it["_line_end"] = s_line + 1, e_line
        # last content char (skip trailing page marker / milestone / spaces)
        tail = text[it["char_start"]:it["char_end"]]
        stripped = re.sub(r"(\s|PageV\d+P\d+|ms\d+)+$", "", tail)
        last = it["char_start"] + max(len(stripped) - 1, 0)
        it["vol_start"], it["page_start"] = page_at(it["char_start"])
        it["vol_end"], it["page_end"] = page_at(last)

        cleaned_lines = []
        for j, ln in enumerate(block):
            k_ev = ev[it["_k"]]["i"] + j - body_start
            keep_num = ev[k_ev].get("why") == "false_heading_year" if 0 <= k_ev < len(ev) else False
            cleaned_lines.append(strip_markup(ln, keep_number=keep_num))
        body = " ".join(cleaned_lines)
        it["_clean"] = re.sub(r"\s+", " ", body).strip()
        it["word_count_total"] = word_count(body)

        head_src = display(body)[:300]
        if it["item_kind"] == "hafiz_list":
            it["heading_ar"] = it["heading_group_ar"].split(" > ")[-1]
            note = ""
        else:
            c = head_src.find(":")
            if 0 < c <= 120:
                it["heading_ar"] = head_src[:c].strip()
                note = ""
            else:
                it["heading_ar"] = " ".join(head_src.split()[:8])
                note = "heading_no_colon: first 8 words used"
        it["heading_translit"] = ""
        it["notes"] = "; ".join(x for x in [note] if x)
        corrected = {"mis_tagged_continuation", "split_midline", "false_heading_year"}
        it["boundary_status"] = "corrected" if corrected & set(it["_issues"]) else "auto"

    # ---- numbering issues per series ----------------------------------------
    num_issues = []
    for it in items:
        it["printed_number_corrected"] = ""
    for series in ("person", "book"):
        seq = [it for it in items if it["printed_series"] == series]
        seen = {}
        prev = 0
        for idx, it in enumerate(seq):
            n = it["printed_number_raw"]
            it["number_issue"] = "none"
            if n in seen:
                it["number_issue"] = "duplicate"
                num_issues.append({"series": series, "printed_number": n, "issue": "duplicate",
                                   "item_id": it["item_id"], "line_no": it["_line_start"],
                                   "detail": f"also {seen[n]}"})
            elif n > prev + 1 and idx + 1 < len(seq) and seq[idx + 1]["printed_number_raw"] == prev + 2:
                it["number_issue"] = "misprint"
                it["printed_number_corrected"] = prev + 1
                num_issues.append({"series": series, "printed_number": n, "issue": "misprint",
                                   "item_id": it["item_id"], "line_no": it["_line_start"],
                                   "detail": f"read as {prev + 1} (between {prev} and {prev + 2})"})
                seen.setdefault(prev + 1, it["item_id"])
                prev += 1
                continue
            elif n > prev + 1:
                it["number_issue"] = "gap_before"
                missing = list(range(prev + 1, n))
                lab = str(missing[0]) if len(missing) == 1 else f"{missing[0]}-{missing[-1]}"
                prev_item = seq[idx - 1]["item_id"] if idx else ""
                num_issues.append({"series": series, "printed_number": n, "issue": "gap_before",
                                   "item_id": it["item_id"], "line_no": it["_line_start"],
                                   "detail": f"missing {lab} (after {prev_item or 'start'})"})
            elif n < prev:
                it["number_issue"] = "other"
                num_issues.append({"series": series, "printed_number": n, "issue": "out_of_order",
                                   "item_id": it["item_id"], "line_no": it["_line_start"],
                                   "detail": f"follows {prev}"})
            seen.setdefault(n, it["item_id"])
            prev = max(prev, n)
        num_issues.append({"series": series, "printed_number": prev, "issue": "summary",
                           "item_id": "", "line_no": "",
                           "detail": f"{len(seq)} items; highest number {prev}; "
                                     f"{len(seen)} distinct numbers"})
    for it in items:
        it.setdefault("number_issue", "none")

    # ---- possible untagged headings inside dictionary items ----------------------
    for it in items:
        if it["section"] != "dictionary" or it["item_kind"] != "entry":
            continue
        # 0-based line indices; skip the heading line and the item's first paragraph
        for j in range(it["_line_start"] + 1, it["_line_end"]):
            ln = lines[j]
            m = UNTAGGED_HEAD.match(ln)
            if m:
                if re.match(r"(و|ف|قال|قلت|فائدة|تنبيه|تتمة|ونص)", m.group(1)) or '"' in m.group(1):
                    continue
                issues.append({
                    "issue": "possible_untagged_heading", "line_no": j + 1,
                    "char_start": line_off[j], "char_end": line_off[j] + len(ln),
                    "item_ref": it["item_id"], "printed_series": "", "printed_number": "",
                    "context_ar": display(strip_markup(ln))[:160],
                    "action_taken": "none; candidate for a missing item heading",
                    "needs_review": True, "detail": ""})

    # link gaps to candidate untagged headings in the preceding item of the same series
    cand_by_item = {}
    for iss in issues:
        if iss["issue"] == "possible_untagged_heading":
            cand_by_item.setdefault(iss["item_ref"], []).append(str(iss["line_no"]))
    item_index = {it["item_id"]: n for n, it in enumerate(items)}
    for ni in num_issues:
        if ni["issue"] != "gap_before":
            continue
        idx = item_index[ni["item_id"]]
        hits = []
        for back in range(idx - 1, -1, -1):
            hits += cand_by_item.get(items[back]["item_id"], [])
            if items[back]["printed_series"] == ni["series"]:
                break
        m = re.search(r"missing (\d+)(?:-(\d+))?", ni["detail"])
        lo, hi = int(m.group(1)), int(m.group(2) or m.group(1))
        if hi - lo < 5:
            back_items = []
            for back in range(idx - 1, -1, -1):
                back_items.append(items[back])
                if items[back]["printed_series"] == ni["series"]:
                    break
            for miss in range(lo, hi + 1):
                rx = re.compile(rf"(?<![\d.]){miss}\s*-\s+\S")
                for b in back_items:
                    for j in range(b["_line_start"], b["_line_end"]):
                        if rx.search(lines[j]):
                            hits.append(f"{j + 1}(number {miss} inline)")
        ni["candidate_lines"] = " ".join(dict.fromkeys(hits))

    # ---- references ------------------------------------------------------------
    by_letter = {}
    for it in items:
        if it["section"] == "dictionary":
            by_letter.setdefault(it["_letter"], []).append(it)
    hint_re = re.compile(r"\(([^()]*?(?:انظر|سبق|تقدم)[^()]*)\)")
    for n, r in enumerate(refs, 1):
        k = r["_k"]
        e = ev[k]
        t = display(strip_markup(r["_text"]))
        c = t.find(":")
        head, full = (t[:c].strip(), t[c + 1:].strip()) if c > 0 else (t, "")
        start = line_off[e["i"]]
        end = start + len(r["_text"])  # approximate when continuation lines exist
        _, j_end = ref_text(k)
        end = line_off[ev[j_end - 1]["i"]] + len(ev[j_end - 1]["line"])
        vol, page = page_at(start)
        hm = hint_re.search(t)
        hint = hm.group(1).strip() if hm else ""
        target, status, how = "", "unresolved", ""
        if hint:
            letter = ""
            lm = re.search(r"حرف\s+(ال\S+)", hint)
            if lm:
                letter = "حرف " + lm.group(1)
            name = re.sub(r"حرف\s+\S+|(?<!\S)ص\s*\d+", " ", hint)
            name = re.sub(r"(?<!\S)(انظر|وانظر|فانظر|ترجمته|ترجمة|سبق|تقدم|ذكره|في|من|أيضا|ايضا"
                          r"|هناك|منه|له|أولا|اولا|إثر|اثر)(?!\S)", " ", name)
            name = norm(re.sub(r"[^\w\s]", " ", name))
            pool = by_letter.get(letter, []) if letter else [it for v in by_letter.values() for it in v]
            cands = []
            if len(name) >= 3:
                cands = [it for it in pool if norm(it["heading_ar"]).startswith(name)
                         or (len(norm(it["heading_ar"])) >= 3 and name.startswith(norm(it["heading_ar"])))]
                how = "hint name vs. item heading" + (" within letter" if letter else "")
            elif letter:
                # name forms: the reference heading, then the name before the hint in its text
                before_hint = full.split("(")[0]
                before_hint = re.sub(r"^(هو|لشيخنا|للشيخ|لل|ل)\s*", "", before_hint.strip())
                for src, src_label in ((head, "heading"), (before_hint, "text")):
                    toks = [x for x in norm(re.sub(r"[^\w\s]", " ", src)).split()
                            if x not in ("بن", "بنت", "هو", "شيخنا")]
                    for width in (3, 2, 1):
                        if len(toks) < width:
                            continue
                        key = " ".join(toks[-width:])
                        if len(key) < 4 or key in ("ابن", "ابو", "ابي"):
                            continue
                        found = [it for it in pool if re.search(rf"(?<!\S){re.escape(key)}(?!\S)",
                                                                norm(it["heading_ar"]))]
                        exact = [it for it in found if norm(it["heading_ar"]).endswith(key)]
                        if len(exact) == 1:
                            found = exact
                        if found:
                            cands = found
                            how = f"{src_label} tail '{key}' within letter"
                            break
                    if len(cands) == 1:
                        break
            cands = list({id(c): c for c in cands}.values())
            if len(cands) == 1:
                target, status = cands[0]["item_id"], "resolved"
            elif len(cands) > 1:
                status = "ambiguous"
                how += f"; {len(cands)} candidates: " + " ".join(c["item_id"] for c in cands[:6])
        r.update({
            "ref_id": f"R{n:04d}", "heading_ar": head, "full_text_ar": full,
            "after_item_id": r["_after_item"]["item_id"] if r["_after_item"] else "",
            "vol": vol, "page": page, "char_start": start, "char_end": end,
            "target_hint_ar": hint, "target_item_id": target, "target_person_id": "",
            "resolution_status": status, "name_form_type": "", "resolution_note": how,
            "line_no": e["i"] + 1,
        })

    # ---- date expressions (codebook §10.1) -----------------------------------------
    YR = r"(?:سنة|عام)"
    date_patterns = [
        ("E01", "digit year", "exact", YR + r"\s*\d{3,4}(?![\d.,٫])"),
        ("E02", "abbreviated digit year (1-2 digits)", "exact; reconstructed", YR + r"\s*\d{1,2}(?![\d.,٫])"),
        ("E03", "dot inside digit year (e.g. 1.87 = 1087; '.' for Arabic zero)", "exact; reconstructed (typo)", YR + r"\s*\d+[.,٫]\d+"),
        ("E03b", "digit year + trailing dot (e.g. 132. = 1320?; ambiguous with full stop)", "check: '.' for zero or full stop", YR + r"\s*\d{2,3}\.(?!\d)"),
        ("E04", "year in words", "exact (as words)", YR + r"\s+(?:[إا]حدى|[إا]حد|اثن|ثنت|ثلاث|[أا]ربع|خمس|ست|سبع|ثمان|تسع|عشر|مائ|ألف)"),
        ("E05", "digits attached to a word (e.g. توفي752, سنة1276)", "spacing artefact", r"[ء-ي](?:\d{3,4})"),
        ("E06", "نيف after a year cue", "nayyif", YR + r"[^.،]{0,25}?(?:نيف|نيّف)"),
        ("E07", "نيف anywhere", "nayyif (incl. non-date)", r"نيف|نيّف"),
        ("E08", "after + year", "after", r"بعد\s+" + YR),
        ("E09", "before + year", "before", r"قبل\s+" + YR),
        ("E10", "circa + year", "circa", r"(?:في\s+حدود|حدود|نحو|قرابة|حوالي|حوالى)\s+" + YR),
        ("E11", "floruit (حيا سنة)", "floruit", r"(?<!\S)حيا\s+(?:" + YR + r"|في)"),
        ("E12", "early/mid/late century", "century_early/mid/late", r"(?:أوائل|أواسط|أواخر|أول|وسط|آخر|صدر|منتصف)\s+(?:القرن|المائة)"),
        ("E13", "century mention", "century", r"(?:القرن|المائة)\s+ال\S+"),
        ("E14", "death cue + year", "event = death", r"(?:المتوفى|المتوفي|توفي|توفى|مات|وفاته|وفاة)\D{0,30}?" + YR + r"\s*\S"),
        ("E15", "birth cue + year", "event = birth", r"(?:ولد|مولده)\D{0,30}?" + YR + r"\s*\S"),
        ("E16", "variant (وقيل + year)", "variant_group", r"وقيل\s+(?:\S+\s+)?" + YR),
        ("E17", "Arabic-Indic digits", "digit form", r"[٠-٩]+"),
    ]
    body_text = " ".join(strip_markup(ln, keep_number=True) for ln in lines[body_start:])
    body_text = re.sub(r"\s+", " ", body_text)
    date_rows = []
    for pid, label, qual, pat in date_patterns:
        rx = re.compile(pat)
        n_occ, n_items, examples = 0, 0, []
        for it in items:
            ms = list(rx.finditer(it["_clean"]))
            if ms:
                n_items += 1
                n_occ += len(ms)
                if len(examples) < 3:
                    m = ms[0]
                    a, b = max(0, m.start() - 25), m.end() + 15
                    examples.append(f"{it['item_id']}: …{it['_clean'][a:b]}…")
        date_rows.append({"expr_id": pid, "label": label, "codebook_mapping": qual, "regex": pat,
                          "n_occurrences_in_items": n_occ, "n_items": n_items,
                          "n_occurrences_full_text": len(rx.findall(body_text)),
                          "examples": " | ".join(examples)})

    # ---- write --------------------------------------------------------------------
    OUT_PROCESSED.mkdir(parents=True, exist_ok=True)
    OUT_STAGE1.mkdir(parents=True, exist_ok=True)

    def write(path, rows, fields):
        with open(path, "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
            w.writeheader()
            for r in rows:
                w.writerow({k: ("true" if v is True else "false" if v is False else v)
                            for k, v in r.items()})

    item_fields = ["item_id", "item_kind", "section", "heading_group_ar", "printed_series",
                   "printed_number_raw", "printed_number_corrected", "number_issue",
                   "heading_ar", "heading_translit", "vol_start", "page_start", "vol_end",
                   "page_end", "char_start", "char_end", "word_count_total",
                   "word_count_bio", "word_count_assessment", "word_count_route",
                   "word_count_other", "boundary_status", "notes", "line_start", "line_end"]
    for it in items:
        it["line_start"], it["line_end"] = it["_line_start"], it["_line_end"]
    write(OUT_PROCESSED / "items.csv", items, item_fields)

    ref_fields = ["ref_id", "heading_ar", "full_text_ar", "after_item_id", "vol", "page",
                  "char_start", "char_end", "target_hint_ar", "target_item_id",
                  "target_person_id", "resolution_status", "name_form_type",
                  "resolution_note", "line_no"]
    write(OUT_PROCESSED / "references.csv", refs, ref_fields)

    issues.sort(key=lambda r: r["line_no"])
    for n, iss in enumerate(issues, 1):
        iss["issue_id"] = f"B{n:04d}"
    write(OUT_STAGE1 / "boundary_issues.csv", issues,
          ["issue_id", "issue", "item_ref", "line_no", "char_start", "char_end",
           "printed_series", "printed_number", "context_ar", "action_taken",
           "needs_review", "detail"])
    write(OUT_STAGE1 / "numbering_issues.csv", num_issues,
          ["series", "printed_number", "issue", "item_id", "line_no", "detail", "candidate_lines"])
    write(OUT_STAGE1 / "date_expression_counts.csv", date_rows,
          ["expr_id", "label", "codebook_mapping", "n_occurrences_in_items", "n_items",
           "n_occurrences_full_text", "regex", "examples"])

    from collections import Counter
    summary = {
        "codebook_version": CODEBOOK_VERSION,
        "raw_file": RAW.name,
        "raw_sha256": hashlib.sha256(raw_bytes).hexdigest(),
        "items": len(items),
        "items_by_kind_series_section": Counter(
            f"{it['item_kind']}|{it['printed_series']}|{it['section']}" for it in items),
        "items_boundary_corrected": sum(it["boundary_status"] == "corrected" for it in items),
        "references": len(refs),
        "references_by_status": Counter(r["resolution_status"] for r in refs),
        "boundary_issues_by_type": Counter(i["issue"] for i in issues),
        "numbering_issues_by_type": Counter(f"{i['series']}|{i['issue']}" for i in num_issues),
        "dictionary_start_line": (dict_start or 0) + 1,
        "khatima_start_line": (khatima_start or 0) + 1,
        "word_count_total": sum(it["word_count_total"] for it in items),
    }
    (OUT_STAGE1 / "stage1_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, default=dict), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2, default=dict))


if __name__ == "__main__":
    main()
