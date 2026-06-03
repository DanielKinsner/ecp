# ECP — Adversarial Type-Safety Review (findings)

**Date:** 2026-06-03  ·  **Base commit:** reviewed at `6e2c9be` (origin/main)  ·  **Branch:** `main`

**Method:** 13 subsystem reviewers fanned across the full Python surface + the Node↔Python boundary; each candidate finding then run past **two independent skeptics** (a *reachability* lens — can the bad type actually arrive? — and a *masking/coverage* lens — is it already guarded or tested?). A finding is **confirmed** only if neither skeptic could refute it.

**Tally:** 43 candidates → **31 confirmed**, 5 contested, 7 refuted.

> ✅ = already fixed + committed this session.  Everything else is **proposed, not yet applied** — this doc is for your review pass.

## Gate review outcome (2026-06-03 — Codex + Claude cross-check)

An independent gate review (Codex) plus Claude verification adjusted three findings:

- **[30] `serve-editor.cjs:22` — REMOVED (false positive).** Probed on Node 24: `server.listen(Number("abc"))` throws `ERR_SOCKET_BAD_PORT` synchronously — it does **not** silently bind a wrong port. No fix.
- **[16] `review_state.py:172-184` — DOWNGRADED to P3.** `jsonschema` is a hard `requirements.txt` dependency, so the real validation path is not type-blind; the lightweight fallback only runs on a broken venv. Fix = narrow the `except` to `ImportError`/`FileNotFoundError` **and** guard the fallback's own `finding.get` loops (lines 198, 208). Tightening, not a blocker.
- **[29] `v2_markers.py:185` — ANNOTATION-ONLY.** The caller assigns the whole tuple (no arity unpack), so there is no runtime crash. With no type checker in the repo this is documentation only. Optional.

**Implementable set:** 1-5, 8-15, 17-28, 31 (+ 16 as a tightening, 29 optional). **[06]/[07] already fixed** (commit `7b29180`); **[30] dropped.** Fixes land as small commits on `main`, each with a negative test.

### Implementation status — ALL LANDED on `main` (2026-06-03)

| Batch | Findings | Commit |
|-------|----------|--------|
| cross-OS UTF-8 stdio (root cause of the 2 failing e2e tests) | — | `89a9a5d` |
| synth-emission fallback | 6, 7 | `7b29180` |
| business_rules malformed-emission hardening | 1, 2, 3, 4, 8, 9 | `100be00` |
| canary_checks type guards | 5, 10, 11 | `ecb69d9` |
| review_state effect floats + validation tightening | 13, 14, 15, 16 | `12f79ff` |
| v2_markers operator-override safety + annotation | 19, 20, 21, 29 | `a07e749` |
| report builders (html_builder / v2_html_builder) | 18, 26, 27 | `0b73396` |
| dom_preprocess null/non-dict baton guards | 17, 24, 25 | `e3c1790` |
| json_parser non-object payload guard | 12 | `67cbb7e` |
| remaining P3 guards | 22, 23, 28, 31 | `91ec9aa` |

**Dropped:** [30] (false positive — Node throws `ERR_SOCKET_BAD_PORT`, no silent bind).
**Net:** 30 of 31 confirmed findings fixed (+ the cross-OS stdio bug), each with a negative regression test proven to fail pre-fix. **Full suite: 1028 passed, 12 skipped, 0 failed** (baseline was 2 failed / 987 passed).


---

## Summary (confirmed, by severity)

| # | Sev | File:Line | Category | Title | Status |
|---|-----|-----------|----------|-------|--------|
| 1 | P1-high | `scripts/assembly/business_rules.py:227, 260` | none-handling | findings: null crashes enumerate() because .get default does not apply to explicit null | proposed |
| 2 | P1-high | `scripts/assembly/business_rules.py:322, 329` | dict-vs-list | reference_citations emitted as a dict makes max() iterate keys and c.get() crash | proposed |
| 3 | P1-high | `scripts/assembly/business_rules.py:374, 439, 577, 679, 854` | dict-vs-list | finding.element as a non-empty list/string survives `or {}` and breaks .get() | proposed |
| 4 | P1-high | `scripts/assembly/business_rules.py:687-689, 717-720` | dict-vs-list | evidence_anchors entries assumed to be dicts; string/non-dict entry crashes a.get() | proposed |
| 5 | P1-high | `scripts/assembly/canary_checks.py:178-179` | str-numeric | local_id formatted with :02d crashes when JSON value is a string | proposed |
| 6 | P1-high | `scripts/build_synthesizer_emission_fallback.py:127-129` | annotation-mismatch | derive_quick_wins reads non-existent f.effort.change_type — Finding has no 'effort' attribute, so quick_wins is always empty | ✅ fixed |
| 7 | P1-high | `scripts/build_synthesizer_emission_fallback.py:147-149` | annotation-mismatch | derive_severity_manifest reads non-existent f.severity and f.evidence_tier — severity sort collapses to all-equal, manifest order is arbitrary | ✅ fixed |
| 8 | P2-medium | `scripts/assembly/business_rules.py:260-261` | dict-vs-list | findings as a single object (dict) iterates keys, then finding.get() hits AttributeError on str | proposed |
| 9 | P2-medium | `scripts/assembly/business_rules.py:957, 999-1002` | none-handling | title: null passed to _title_jaccard calls None.lower() | proposed |
| 10 | P2-medium | `scripts/assembly/canary_checks.py:661` | iteration-over-none | set(meta['clusters_used']) silently iterates a string into per-character clusters | proposed |
| 11 | P2-medium | `scripts/assembly/canary_checks.py:872-873` | iteration-over-none | clusters_used / devices_scanned iterated as lists silently expand a string into characters | proposed |
| 12 | P2-medium | `scripts/assembly/json_parser.py:195-203` | json-coercion | Candidate-id resolution runs on unvalidated payload before schema check; non-object JSON raises AttributeError instead of EmissionValidationError | proposed |
| 13 | P2-medium | `scripts/assembly/review_state.py:954-956` | str-numeric | dim effect opacity bare float() crashes on non-numeric string; opacity is not schema-type-constrained | proposed |
| 14 | P2-medium | `scripts/assembly/review_state.py:944-946` | str-numeric | blur effect feather_pct bare float() crashes on non-numeric string; feather_pct is not schema-type-constrained | proposed |
| 15 | P2-medium | `scripts/assembly/review_state.py:1000` | str-numeric | spotlight dim opacity bare float() inside max() crashes on non-numeric string | proposed |
| 16 | P2-medium | `scripts/assembly/review_state.py:172-184` | json-coercion | Schema validation silently degrades to a type-blind lightweight check, so callers treat unvalidated coordinate types as safe | proposed |
| 17 | P2-medium | `scripts/dom_preprocess.py:411-414` | isinstance-gap | baton section iterated with sec.get() before any isinstance(dict) guard | proposed |
| 18 | P2-medium | `scripts/report/html_builder.py:503-536` | unchecked-get | baton viewport used as dict when it can be JSON null | proposed |
| 19 | P2-medium | `scripts/report/v2_markers.py:904` | unchecked-get | mapping["finding_index"] KeyError on operator-override entries keyed only by f_ref | proposed |
| 20 | P2-medium | `scripts/report/v2_markers.py:911` | str-numeric | slide compared with < against int when operator JSON can supply a string slide | proposed |
| 21 | P2-medium | `scripts/report/v2_markers.py:923` | unchecked-get | fallback_pos["x_pct"]/["y_pct"] subscript assumes keys present and numeric on operator overrides | proposed |
| 22 | P3-low | `scripts/assembly/finding_stability.py:75` | str-numeric | title/text assumed string-like; a numeric title crashes on .lower() | proposed |
| 23 | P3-low | `scripts/assembly/visual_quality.py:82` | isinstance-gap | _ve(item) assumes each finding/marker is a dict; a non-dict list element raises AttributeError | proposed |
| 24 | P3-low | `scripts/dom_preprocess.py:368` | iteration-over-none | for el in elements crashes when baton has "elements": null | proposed |
| 25 | P3-low | `scripts/dom_preprocess.py:494-497` | dict-vs-list | clusters_used returned unchecked; a non-list value is iterated char-by-char | proposed |
| 26 | P3-low | `scripts/report/v2_html_builder.py:63-68` | str-numeric | int(scroll_y) on unvalidated operator override anchor crashes the whole report | proposed |
| 27 | P3-low | `scripts/report/v2_html_builder.py:64` | bytes-str | escape_html(viewport) raises AttributeError when viewport is a non-zero number | proposed |
| 28 | P3-low | `scripts/report/v2_loader.py:994-998` | json-coercion | priority_path stories assumed to be dicts from unvalidated synthesizer JSON | proposed |
| 29 | P3-low | `scripts/report/v2_markers.py:185` | unpacking | Return annotation tuple[int, float, float] \| None but function returns a 4-tuple | proposed |
| 30 | P3-low | `scripts/serve-editor.cjs:22` | str-numeric | Non-numeric --port silently coerces to NaN and is passed to server.listen | proposed |
| 31 | P3-low | `scripts/validate-cluster-files.py:271-272` | json-coercion | meta.json json.loads output assumed to be a dict; array/scalar or non-dict 'page' crashes with AttributeError | proposed |


---

## Confirmed findings — detail

### 1. [P1-high] `scripts/assembly/business_rules.py:227, 260` — findings: null crashes enumerate() because .get default does not apply to explicit null

- **Symbol:** `validate_business_rules`  ·  **Category:** none-handling  ·  **Reviewer severity:** P1-high  ·  **Confidence:** 0.85
- **Verification:** 2/2 skeptics confirmed · reachable=True · no existing test covers it
- **Trigger:** LLM emits {"schema_version": "v2", "findings": null}. emission.get("findings", []) returns None (the default only fires on a MISSING key, not a null value), so findings is None.
- **Why it breaks:** Line 227 `findings = emission.get("findings", [])` then line 260 `for i, f in enumerate(findings)`. When findings is None this raises TypeError: 'NoneType' object is not iterable. The caller (test-specialist.py ~line 925-945) runs business rules even when schema validation already flagged the emission, and the surrounding try/except only catches ValueError — a TypeError propagates and crashes the validator instead of being demoted to a clean SCHEMA/RULE message.
- **Proposed fix:** Coerce non-list to empty: `findings = emission.get("findings") or []; if not isinstance(findings, list): findings = []` (apply the same guard in _check_within_emission_unique_anchors and _check_finding_count_in_band).
- **Verifier refinement:** At line 227 coerce defensively: `findings = emission.get("findings") or []` then `if not isinstance(findings, list): findings = []`. Apply the identical guard inside _check_within_emission_unique_anchors (line 937) and _check_finding_count_in_band (line 1013), since both also call `emission.get("findings", [])` and would crash independently. This matches the isinstance-guard pattern already used throughout emission_autofix.py. (Note: `or []` alone also coerces an empty-but-valid `[]` harmlessly, but keep the isinstance check to also defend against non-list non-null junk like a dict or string slipping through before schema validation rejects it.)

### 2. [P1-high] `scripts/assembly/business_rules.py:322, 329` — reference_citations emitted as a dict makes max() iterate keys and c.get() crash

- **Symbol:** `_check_evidence_tier`  ·  **Category:** dict-vs-list  ·  **Reviewer severity:** P1-high  ·  **Confidence:** 0.8
- **Verification:** 2/2 skeptics confirmed · reachable=True · no existing test covers it
- **Trigger:** LLM emits reference_citations as a JSON object, e.g. {"reference_citations": {"0": {"tier": "Gold"}}}, or as a list of bare strings ["Gold"].
- **Why it breaks:** Line 322 `cites = finding.get("reference_citations") or []` keeps a non-empty dict (truthy), passes the `if not cites` guard, then line 329 `max(EVIDENCE_TIER_RANK.get(c.get("tier", ""), 0) for c in cites)` iterates dict keys (str) so `c.get` raises AttributeError; if it is a list of strings, same AttributeError. The function never checks each citation is a dict or that cites is a list.
- **Proposed fix:** Filter to dict items: `cites = [c for c in (finding.get("reference_citations") or []) if isinstance(c, dict)]` and bail if empty.
- **Verifier refinement:** The reviewer's fix is correct and idiomatic: `cites = [c for c in (finding.get("reference_citations") or []) if isinstance(c, dict)]`. For a dict input, `for c in dict` iterates string keys, which the isinstance filter discards (-> empty -> bails via `if not cites`); for a list of strings, the filter discards them too. This matches the existing defensive isinstance patterns elsewhere in the codebase (pa_raw, ve_raw, anchor_candidates_sidecar). Optionally also wrap the business-rules call in test-specialist.py:925-945 to catch broader exceptions (not just ValueError) so any future malformed-shape bug degrades to a reported error rather than a crash — but the per-function isinstance guard is the correct primary fix.

### 3. [P1-high] `scripts/assembly/business_rules.py:374, 439, 577, 679, 854` — finding.element as a non-empty list/string survives `or {}` and breaks .get()

- **Symbol:** `_check_baton_index_in_candidate_registry/_check_baton_index/_check_element_text_match/_check_evidence_anchor_consistency/_check_baton_precedence`  ·  **Category:** dict-vs-list  ·  **Reviewer severity:** P1-high  ·  **Confidence:** 0.8
- **Verification:** 2/2 skeptics confirmed · reachable=True · no existing test covers it
- **Trigger:** LLM emits element as something other than an object, e.g. "element": ["e15"] or "element": "e15". A truthy non-dict value passes the `or {}` fallback unchanged.
- **Why it breaks:** All five helpers do `element = finding.get("element") or {}` then `element.get("baton_index", "")` (e.g. line 374/375, 439/440, 577/578). `or {}` only replaces falsy values; a non-empty list or a string is truthy, so `.get` runs on a list/str and raises AttributeError. The schema would reject a non-object element, but business rules execute regardless of schema failure.
- **Proposed fix:** Use a type-checked coercion helper: `element = finding.get("element"); element = element if isinstance(element, dict) else {}` in each helper (or one shared accessor).
- **Verifier refinement:** Add a shared type-checked accessor and use it in all five helpers (and any other `finding.get("element")` reader), e.g. a module-level helper:

    def _element_of(finding: dict) -> dict:
        el = finding.get("element")
        return el if isinstance(el, dict) else {}

then replace `element = finding.get("element") or {}` with `element = _element_of(finding)` at lines 374, 439, 577, 679, and the inline use at 854. Note the same `or {}`/`or []` truthiness assumption appears for sibling fields (e.g. `evidence_anchors` iteration at 687, and `a.get(...)` assumes each anchor is a dict) — those are adjacent variants of the same class but the claim's five element sites are the confirmed ones. Additionally, harden the orchestrator: broaden the except at test-specialist.py:941 from `except ValueError` to also defend against malformed-finding-shape errors (or, better, gate `_run_business_rules` to skip per-finding checks when `iter_errors` already reported a type error for that finding), so a single bad finding shape degrades to a clean SCHEMA error rather than crashing the whole validate run.

### 4. [P1-high] `scripts/assembly/business_rules.py:687-689, 717-720` — evidence_anchors entries assumed to be dicts; string/non-dict entry crashes a.get()

- **Symbol:** `_check_evidence_anchor_consistency/_check_anchor_resolution`  ·  **Category:** dict-vs-list  ·  **Reviewer severity:** P1-high  ·  **Confidence:** 0.78
- **Verification:** 2/2 skeptics confirmed · reachable=True · no existing test covers it
- **Trigger:** LLM emits evidence_anchors as a list containing a string or scalar, e.g. "evidence_anchors": ["section-1.jpg"], or evidence_anchors as a dict.
- **Why it breaks:** Line 687 `for j, a in enumerate(finding.get("evidence_anchors") or [])` then line 688 `a.get("type")`; same pattern at line 717-721 with `a.get("reference", "")` and `a.get("type", "")`. If an entry is a str, `a.get` raises AttributeError; if evidence_anchors is a dict, enumeration yields str keys with the same result. No isinstance check on the entries.
- **Proposed fix:** `for j, a in enumerate(finding.get("evidence_anchors") or []): if not isinstance(a, dict): continue` in both functions.
- **Verifier refinement:** The reviewer's fix is correct. In both functions replace the loop header with a per-entry type guard:

    for j, a in enumerate(finding.get("evidence_anchors") or []):
        if not isinstance(a, dict):
            continue
        ...

This handles all three malformed shapes: list-of-string (entries are str), list-of-scalar (entries non-dict), and evidence_anchors-as-dict (enumeration yields str keys, which are non-dict and get skipped). Note that `continue` silently drops the malformed anchor; that is acceptable here because the schema validator (which runs in the same validate_emission pass and aggregates into all_errors) already reports the type violation as a graceful schema error — so the operator still sees a clear message rather than a stack trace. Apply the guard at line 687-688 (_check_evidence_anchor_consistency) and line 717-720 (_check_anchor_resolution).

### 5. [P1-high] `scripts/assembly/canary_checks.py:178-179` — local_id formatted with :02d crashes when JSON value is a string

- **Symbol:** `check_ethics_findings_have_source_urls`  ·  **Category:** str-numeric  ·  **Reviewer severity:** P1-high  ·  **Confidence:** 0.85
- **Verification:** 2/2 skeptics confirmed · reachable=True · no existing test covers it
- **Trigger:** ethics-findings.json (LLM-emitted, read raw via json.loads at line 157 with no schema validation in this path) contains a BLOCK/ADJACENT finding whose local_id is a string, e.g. {"ethics_state":"BLOCK","local_id":"3"}. The string "3" is truthy so it passes the `if local_id` guard, then hits `:02d`.
- **Why it breaks:** Line 179: `f_ref = f"ethics F-{local_id:02d}" if local_id else "ethics F-??"`. local_id comes from `f.get("local_id")` (line 178). The `if local_id` guard only filters falsy values (None, 0, ""); a non-empty string like "3" passes the truthiness check and then `"{:02d}".format("3")` raises `ValueError: Unknown format code 'd' for object of type 'str'`, aborting the entire canary run for BLOCK/ADJACENT findings. Sibling code knows this risk: determinism_gate.py:524-525 guards with `isinstance(local_id, int)` and finding_stability.py:474 wraps `int(local_id)` in try/except — only this canary does neither, despite consuming the same LLM-drift-prone field.
- **Proposed fix:** Coerce defensively: `try: f_ref = f"ethics F-{int(local_id):02d}"` / `except (TypeError, ValueError): f_ref = "ethics F-??"`, mirroring determinism_gate's isinstance/int guard.
- **Verifier refinement:** The proposed fix is correct. Mirror the sibling guards: replace line 179 with a coercion that degrades to the existing "??" sentinel: `try:\n    f_ref = f"ethics F-{int(local_id):02d}"\nexcept (TypeError, ValueError):\n    f_ref = "ethics F-??"`. This matches determinism_gate.py:414 / finding_stability.py:474 (int() in try/except) and determinism_gate.py:524-525 (isinstance gate) and keeps the canary running instead of aborting on a drifted/hand-edited local_id.

### 6. ✅ [P1-high] `scripts/build_synthesizer_emission_fallback.py:127-129` — derive_quick_wins reads non-existent f.effort.change_type — Finding has no 'effort' attribute, so quick_wins is always empty

- **Symbol:** `derive_quick_wins`  ·  **Category:** annotation-mismatch  ·  **Reviewer severity:** P1-high  ·  **Confidence:** 0.85
- **Verification:** 2/2 skeptics confirmed · reachable=True · no existing test covers it
- **Trigger:** Every call. findings come from parse_emission_file (json_parser) which returns models.Finding instances. models.Finding exposes change_type / change_scope as TOP-LEVEL fields and has no 'effort' attribute.
- **Why it breaks:** change_type = getattr(getattr(f, 'effort', None), 'change_type', None); getattr(f, 'effort', None) is always None because Finding has no 'effort' field, so change_type is always None, `None in QUICK_TYPES` is always False, and the quick_wins_manifest emitted into synthesizer-emission-v1.json is silently always []. The real attributes are f.change_type and f.change_scope (models.py:131-132).
- **Proposed fix:** Read the real fields: change_type = getattr(f, 'change_type', None); change_scope = getattr(f, 'change_scope', None).
- **Verifier refinement:** At lines 127-128 read the flattened top-level fields: change_type = getattr(f, "change_type", None); change_scope = getattr(f, "change_scope", None). This matches the field layout of models.Finding (models.py:131-132) produced by json_parser._finding_from_dict and the existing correct consumer in scripts/report/v2_loader.py:498-499.
- **Status:** ✅ Fixed in this session (commit `7b29180`), regression test in `tests/test_synth_emission_fallback.py`.

### 7. ✅ [P1-high] `scripts/build_synthesizer_emission_fallback.py:147-149` — derive_severity_manifest reads non-existent f.severity and f.evidence_tier — severity sort collapses to all-equal, manifest order is arbitrary

- **Symbol:** `derive_severity_manifest`  ·  **Category:** annotation-mismatch  ·  **Reviewer severity:** P1-high  ·  **Confidence:** 0.85
- **Verification:** 2/2 skeptics confirmed · reachable=True · no existing test covers it
- **Trigger:** Every call. findings are models.Finding from parse_emission_file. Finding has 'priority' (CRITICAL/HIGH/MEDIUM/LOW) and 'tier' (Gold/Silver/Bronze), NOT 'severity' or 'evidence_tier'.
- **Why it breaks:** sev = getattr(f, 'severity', None) or '?' is always '?', so SEVERITY_RANK.get('?', 0) is 0 for every finding; tier = getattr(f, 'evidence_tier', None) or 'Bronze' is always 'Bronze', so TIER_RANK.get('Bronze') is 1 for every finding. The subsequent rows.sort(key=lambda r: (-r[0], -r[1], -r[2])) therefore degenerates to confidence-only ordering, silently producing a severity_manifest that is NOT severity-sorted. Correct fields are f.priority and f.tier (models.py:113,121).
- **Proposed fix:** Use sev = getattr(f, 'priority', None) or '?' and tier = getattr(f, 'tier', None) or 'Bronze'.
- **Verifier refinement:** In derive_severity_manifest, read the actual Finding attributes: `sev = getattr(f, "priority", None) or "?"` and `tier = getattr(f, "tier", None) or "Bronze"` (or, since these are direct dataclass fields, simply `sev = f.priority or "?"` and `tier = f.tier or "Bronze"`). Note Finding.tier defaults to "" so the `or "Bronze"` fallback maps unknown-tier to Bronze=1; if the original intent was unknown->0, use `TIER_RANK.get(f.tier, 0)` with `tier = f.tier`. The claim's proposed fix is correct.
- **Status:** ✅ Fixed in this session (commit `7b29180`), regression test in `tests/test_synth_emission_fallback.py`.

### 8. [P2-medium] `scripts/assembly/business_rules.py:260-261` — findings as a single object (dict) iterates keys, then finding.get() hits AttributeError on str

- **Symbol:** `validate_business_rules`  ·  **Category:** dict-vs-list  ·  **Reviewer severity:** P1-high  ·  **Confidence:** 0.82
- **Verification:** 2/2 skeptics confirmed · reachable=True · no existing test covers it
- **Trigger:** LLM emits a single finding object instead of an array: {"findings": {"surface": ...}}. enumerate() over a dict yields its string keys, so each `f` is a str like "surface".
- **Why it breaks:** Line 260 `for i, f in enumerate(findings)` followed by per-finding helpers that all call `finding.get(...)` (e.g. _check_evidence_tier line 322 `finding.get("reference_citations")`). With `f` a str, `f.get(...)` raises AttributeError: 'str' object has no attribute 'get'. This is the exact 'single object where a list is expected' class. Business rules run before schema errors gate execution, and only ValueError is caught upstream.
- **Proposed fix:** Guard the loop: `if not isinstance(findings, list): findings = []`, and/or `for i, f in enumerate(findings): if not isinstance(f, dict): continue`.
- **Verifier refinement:** The claimed fix is correct and matches the codebase's own established pattern (sibling emission_autofix.py). Add a guard at the top of validate_business_rules right after computing findings (line 227): `findings = emission.get("findings", []); if not isinstance(findings, list): findings = []` AND defensively skip non-dict items in the loop: `for i, f in enumerate(findings): if not isinstance(f, dict): continue`. Apply the same `if not isinstance(f, dict): continue` guard inside _check_within_emission_unique_anchors (line 941), which also iterates findings and would raise the same AttributeError on f.get(...). Both loops read emission['findings'] independently, so guarding only line 260 leaves the emission-scoped duplicate check exposed.

### 9. [P2-medium] `scripts/assembly/business_rules.py:957, 999-1002` — title: null passed to _title_jaccard calls None.lower()

- **Symbol:** `_check_within_emission_unique_anchors/_title_jaccard`  ·  **Category:** none-handling  ·  **Reviewer severity:** P2-medium  ·  **Confidence:** 0.7
- **Verification:** 2/2 skeptics confirmed · reachable=True · no existing test covers it
- **Trigger:** Two duplicate baton_index='absent' findings where at least one has "title": null. f_a.get("title", "") returns None (default does not apply to explicit null).
- **Why it breaks:** Line 957 `_title_jaccard(f_a.get("title", ""), f_b.get("title", ""))` and line 1001 `re.findall(r"\w+", a.lower())`. A None title reaches a.lower() → AttributeError: 'NoneType' object has no attribute 'lower'. Only reached on the 'absent' duplicate path, but that path is data-reachable from LLM output.
- **Proposed fix:** Coerce in _title_jaccard: `a = a or ""; b = b or ""` (or guard the callers with `f.get("title") or ""`).
- **Verifier refinement:** Coerce inside _title_jaccard to match the codebase's existing defensive idiom and protect all current/future callers: at the top of _title_jaccard add `a = a or ""` and `b = b or ""` before the re.findall calls. This mirrors the (x.get("field") or "") pattern used at business_rules.py lines 624-625, 644-645, 890, 904. Caller-side guarding at line 957 (f_a.get("title") or "") also works but only fixes this one call site.

### 10. [P2-medium] `scripts/assembly/canary_checks.py:661` — set(meta['clusters_used']) silently iterates a string into per-character clusters

- **Symbol:** `check_clusters_represented`  ·  **Category:** iteration-over-none  ·  **Reviewer severity:** P2-medium  ·  **Confidence:** 0.7
- **Verification:** 2/2 skeptics confirmed · reachable=True · no existing test covers it
- **Trigger:** meta.json (read raw via json.loads at line 651) has clusters_used written as a string instead of a list, e.g. "clusters_used": "visual-cta". meta_validator.validate_meta_json (lines 124-129) explicitly treats a non-list clusters_used as a real runtime case (it only warns, never blocks), so this value can reach the canary.
- **Why it breaks:** Line 661: `expected = set(meta.get("clusters_used") or []) - {"ethics"}`. When clusters_used is a string, `set("visual-cta")` does not crash — it produces `{'v','i','s','u','a','l','-','c','t'}`, a set of single characters. `missing = expected - represented` (line 668) then reports bogus per-character 'missing clusters' and the canary's PASS/FAIL verdict becomes meaningless wrong-typed data with no error surfaced — exactly the silent-misleading mode this G16 canary exists to prevent.
- **Proposed fix:** Guard the type before use: `cu = meta.get("clusters_used"); expected = (set(cu) if isinstance(cu, list) else set()) - {"ethics"}`.
- **Verifier refinement:** The reviewer's fix (`set(cu) if isinstance(cu, list) else set()`) silently coerces a malformed type to an empty set, which makes expected empty so the canary PASSES — converting a misleading-FAIL into a misleading-PASS, which is worse for a trust canary whose purpose is surfacing silent corruption. Better: detect the wrong type and FAIL loudly with a clear message, e.g. at line 661: `cu = meta.get("clusters_used") or []` then `if not isinstance(cu, list): return CanaryResult(name="clusters_represented", passed=False, summary=f"clusters_represented: FAIL -- meta.json clusters_used must be a list, got {type(cu).__name__}", detail={"error": "clusters_used_wrong_type", "got_type": type(cu).__name__})`. Add a regression test (none of the G16 tests currently pass a string) and apply the same guard at line 872.

### 11. [P2-medium] `scripts/assembly/canary_checks.py:872-873` — clusters_used / devices_scanned iterated as lists silently expand a string into characters

- **Symbol:** `check_trace_counters_reconcile_with_artifacts`  ·  **Category:** iteration-over-none  ·  **Reviewer severity:** P2-medium  ·  **Confidence:** 0.66
- **Verification:** 2/2 skeptics confirmed · reachable=True · no existing test covers it
- **Trigger:** meta.json has clusters_used or devices_scanned as a string (e.g. "devices_scanned": "desktop") — the exact M2 corruption class meta_validator was built to detect and which it only warns about (lines 124-129), so the malformed value still flows into this canary that reads meta.json raw (line 843).
- **Why it breaks:** Line 872 `requested_clusters = [c for c in (meta.get("clusters_used") or []) if c != "ethics"]` and line 873 `requested_devices = list(meta.get("devices_scanned") or [])`. If the field is a string, the comprehension/`list()` iterates characters: "desktop" becomes ['d','e','s','k','t','o','p']. The nested loop (lines 875-879) then probes for files like `cluster-d-e.json`, observed_specialists stays ~0, and the reconciliation verdict is computed against garbage — a silent wrong-typed result, no crash to flag the corruption.
- **Proposed fix:** Coerce with isinstance before iterating: `cu = meta.get("clusters_used"); requested_clusters = [c for c in cu if c != "ethics"] if isinstance(cu, list) else []` and likewise for devices_scanned.
- **Verifier refinement:** Apply isinstance guards mirroring meta_validator.py:149-150's own pattern: `cu = meta.get("clusters_used"); requested_clusters = [c for c in cu if c != "ethics"] if isinstance(cu, list) else []` and `ds = meta.get("devices_scanned"); requested_devices = list(ds) if isinstance(ds, list) else []`. The reviewer's proposed fix is correct as written.

### 12. [P2-medium] `scripts/assembly/json_parser.py:195-203` — Candidate-id resolution runs on unvalidated payload before schema check; non-object JSON raises AttributeError instead of EmissionValidationError

- **Symbol:** `parse_emission_file`  ·  **Category:** json-coercion  ·  **Reviewer severity:** P2-medium  ·  **Confidence:** 0.82
- **Verification:** 2/2 skeptics confirmed · reachable=True · no existing test covers it
- **Trigger:** A malformed cluster-emission file whose top-level JSON is an array or scalar (e.g. the LLM emits `[ {...} ]` or `"skipped"` instead of an object) AND a non-None anchor_candidates_sidecar is passed. json.loads(...) at line 193 yields a list; line 199 calls resolve_candidate_ids_in_emission(payload, sidecar) BEFORE validate_emission_payload runs at line 203.
- **Why it breaks:** Line 193 `payload = json.loads(...)` is unchecked. The schema guard (validate_emission_payload) is at line 203, but the sidecar branch at lines 195-201 executes first. resolve_candidate_ids_in_emission (anchor_candidates.py:596) immediately does `for f in emission.get('findings') or []:` — `list`/`str` has no `.get`, so a top-level non-object payload raises `AttributeError: 'list' object has no attribute 'get'`. This bypasses the structured EmissionValidationError contract callers rely on. v2_loader.py wraps the call in `except Exception` so it degrades there, but build_synthesizer_emission_fallback.py:109 and trim_batons_phase5.py:33 do NOT catch it, so the AttributeError propagates uncaught.
- **Proposed fix:** Guard immediately after json.loads: `if not isinstance(payload, dict): validate_emission_payload(payload, source_path=str(path))` (which raises EmissionValidationError) — or move the `validate_emission_payload(payload, ...)` call to before the sidecar-resolution branch so non-object payloads fail with the structured error first.
- **Verifier refinement:** Move validate_emission_payload(payload, source_path=str(path)) to run immediately after payload = json.loads(...) (i.e. before the sidecar-resolution branch at line 195). This makes any non-object or otherwise schema-invalid payload fail with the structured EmissionValidationError before resolve_candidate_ids_in_emission ever touches it, and is strictly safer than a narrow isinstance guard because it also catches other malformed-but-object payloads earlier. The reviewer's alternative (an isinstance(payload, dict) guard that calls validate_emission_payload) is also acceptable but redundant once validation is simply hoisted ahead of the sidecar branch.

### 13. [P2-medium] `scripts/assembly/review_state.py:954-956` — dim effect opacity bare float() crashes on non-numeric string; opacity is not schema-type-constrained

- **Symbol:** `_render_effects`  ·  **Category:** str-numeric  ·  **Reviewer severity:** P2-medium  ·  **Confidence:** 0.78
- **Verification:** 2/2 skeptics confirmed · reachable=True · no existing test covers it
- **Trigger:** A review-state effect dict {"type":"dim","rect":{...},"opacity":"high"} (or any non-numeric string). review-state-v1.json $defs.effect has additionalProperties:true and does NOT define an 'opacity' property, so a string opacity passes jsonschema validation and reaches the renderer.
- **Why it breaks:** Line 956: `opacity = max(0.0, min(0.95, float(effect.get("opacity", 0.38) or 0.38)))`. The effect schema only constrains `radius_px` and `strength` to number; `opacity` is undefined and additionalProperties:true admits any type. `float("high")` raises ValueError, aborting render_final_report for the whole report. The operator-owned review-state file is explicitly hand-editable (module docstring), so a malformed opacity is reachable input, not a theoretical one.
- **Proposed fix:** Use the existing guarded coercion: `opacity = _bounded_float(effect.get("opacity", 0.38), 0.38, 0.0, 0.95)` (it catches TypeError/ValueError). Apply the same to the feather/blur path.
- **Verifier refinement:** Replace the bare float() with the existing guarded helper at line 956: `opacity = _bounded_float(effect.get("opacity", 0.38), 0.38, 0.0, 0.95)`. Apply the same to the blur feather path (line 946: `feather = _bounded_float(effect.get("feather_pct", 18), 18, 0.0, 45.0)`) and the spotlight opacity (line 1000). Note: passing the raw value (not `... or 0.38`) is fine because _bounded_float already falls back on TypeError/ValueError and also handles 0/None via fallback only on coercion failure; if a literal 0.0 opacity must map to fallback, keep `effect.get("opacity", 0.38) or 0.38` semantics by passing `(effect.get("opacity") or 0.38)`.

### 14. [P2-medium] `scripts/assembly/review_state.py:944-946` — blur effect feather_pct bare float() crashes on non-numeric string; feather_pct is not schema-type-constrained

- **Symbol:** `_render_effects`  ·  **Category:** str-numeric  ·  **Reviewer severity:** P2-medium  ·  **Confidence:** 0.77
- **Verification:** 2/2 skeptics confirmed · reachable=True · no existing test covers it
- **Trigger:** A review-state effect dict {"type":"blur","feather_pct":"soft"}. 'feather_pct' is not a property in review-state-v1.json $defs.effect (additionalProperties:true), so a string passes schema validation.
- **Why it breaks:** Line 946: `feather = max(0.0, min(45.0, float(effect.get("feather_pct", 18) or 18)))`. Bare float() on an unconstrained, operator-editable field. `float("soft")` -> ValueError, which propagates out of render_final_report and fails the entire report render. Contrast with _render_outside_blur (line 965-969) which correctly uses _bounded_float for the same kind of values.
- **Proposed fix:** Replace with `feather = _bounded_float(effect.get("feather_pct", 18), 18, 0.0, 45.0)`.
- **Verifier refinement:** Apply the reviewer's fix: replace line 946 with `feather = _bounded_float(effect.get("feather_pct", 18), 18, 0.0, 45.0)`. Verified it returns 18 for "soft" and "", passes 30 through, and clamps 999 to 45 — matching the existing max(0.0, min(45.0, ...)) bounds and the _bounded_float pattern already used for sibling fields at lines 965-969. Note for completeness: line 952 also embeds `effect.get("radius_px", 8)` directly into CSS without coercion; a string radius_px would not crash here (it is only string-formatted, not float()-ed), so it is out of scope for this str-numeric ValueError but worth a follow-up sanitize for consistency.

### 15. [P2-medium] `scripts/assembly/review_state.py:1000` — spotlight dim opacity bare float() inside max() crashes on non-numeric string

- **Symbol:** `_render_spotlight`  ·  **Category:** str-numeric  ·  **Reviewer severity:** P2-medium  ·  **Confidence:** 0.75
- **Verification:** 2/2 skeptics confirmed · reachable=True · no existing test covers it
- **Trigger:** A whole-slide dim effect (no rect) with a string opacity, e.g. {"type":"dim","opacity":"0.5x"}. dims is guaranteed non-empty (guarded line 998) so the generator expression runs, and opacity is not schema-typed (additionalProperties:true on effect).
- **Why it breaks:** Line 1000: `opacity = max(max(0.0, min(0.95, float(dim.get("opacity", 0.5) or 0.5))) for dim in dims)`. `float("0.5x")` raises ValueError mid-comprehension, aborting render_final_report. Same unconstrained-field problem as _render_effects.
- **Proposed fix:** Coerce safely per dim: `float_opacities = [_bounded_float(d.get("opacity", 0.5), 0.5, 0.0, 0.95) for d in dims]; opacity = max(float_opacities)`.
- **Verifier refinement:** Replace line 1000 with the existing safe helper, per dim, matching the codebase pattern: `opacity = max(_bounded_float(dim.get("opacity", 0.5), 0.5, 0.0, 0.95) for dim in dims)`. Note _bounded_float already clamps to [low, high] and falls back on TypeError/ValueError, so the outer max(0.0, min(0.95, ...)) is unnecessary. Apply the identical fix to the sibling site _render_effects line 956 (`float(effect.get("opacity", 0.38) or 0.38)` -> `_bounded_float(effect.get("opacity", 0.38), 0.38, 0.0, 0.95)`), since it has the same latent bare-float() crash on a string opacity for a rect-scoped dim.

### 16. [P2-medium] `scripts/assembly/review_state.py:172-184` — Schema validation silently degrades to a type-blind lightweight check, so callers treat unvalidated coordinate types as safe

- **Symbol:** `validate_review_state`  ·  **Category:** json-coercion  ·  **Reviewer severity:** P2-medium  ·  **Confidence:** 0.55
- **Verification:** 1/2 skeptics confirmed · reachable=True · no existing test covers it
- **Trigger:** jsonschema not importable or schema/review-state-v1.json missing/unreadable -> the broad `except Exception` swallows it and falls back to _validate_review_state_lightweight, which never checks that marker x_pct/cx_pct/w_pct or effect numeric fields are numbers. The python-cmd.cjs resolver explicitly documents that a bare system python3 lacking jsonschema is a real runtime condition.
- **Why it breaks:** Lines 181-182: `except Exception: schema_errors = _validate_review_state_lightweight(review_state)`. The lightweight validator (187-201) only checks version/keys/status enum. render_final_report (353) and build_initial_review_state (162) trust validate_review_state to reject malformed input, then do `float(marker.get("x_pct"...))`, `float(crop.get(...))`, arithmetic in _marker_center/_default_callout_position. A string coordinate that the real schema would reject now flows into float()/arithmetic and raises ValueError/TypeError at render time instead of a clean validation error.
- **Proposed fix:** Narrow the except to ImportError/FileNotFoundError, and have the lightweight fallback type-check numeric marker/effect fields (or re-raise so the missing-jsonschema condition is loud rather than silently weakening validation).
- **Verifier refinement:** Narrow the except to (ImportError, ModuleNotFoundError, OSError) so unexpected errors propagate, and either (a) re-raise/loudly flag the missing-jsonschema condition instead of silently falling back, or (b) extend _validate_review_state_lightweight (and _validate_review_state_references) to type-check numeric marker fields (cx_pct/cy_pct/x_pct/y_pct/w_pct/h_pct/rx_pct/ry_pct/stroke_width) and finding callout_position numeric fields, appending an error when a present value is not an int/float (excluding bool). Option (b) is preferable because it preserves the fallback's purpose (work without jsonschema) while closing the type-blind gap; the render-time float() sites assume validation already rejected non-numbers.

### 17. [P2-medium] `scripts/dom_preprocess.py:411-414` — baton section iterated with sec.get() before any isinstance(dict) guard

- **Symbol:** `preprocess_device`  ·  **Category:** isinstance-gap  ·  **Reviewer severity:** P1-high  ·  **Confidence:** 0.78
- **Verification:** 2/2 skeptics confirmed · reachable=True · no existing test covers it
- **Trigger:** baton.json on disk has a sections[] entry that is not an object (e.g. a string, number, or null) — `"sections": ["hero", null]` from a hand-edited or malformed baton.
- **Why it breaks:** Line 342 `baton_sections = baton.get("sections", [])` reads raw json.loads output with no element filtering. Line 411 `for sec in baton_sections:` then 412 `label = sec.get("label") or ""` calls .get() directly on `sec`. If any list entry is not a dict, `sec.get` raises AttributeError. The geometry helpers at 413-414 (`section_scroll_top`/`section_scroll_bottom`) DO guard `isinstance(section, dict)`, and lead_prep.py guards each section with `isinstance(sec, dict)` (lines 127/133) — this loop is the odd one out, crashing one line BEFORE the guarded helpers run.
- **Proposed fix:** Guard the loop body: `for sec in baton_sections:` followed by `if not isinstance(sec, dict): continue` before line 412.
- **Verifier refinement:** The proposed fix is correct. In the loop at line 411, add a guard as the first statement of the body: `for sec in baton_sections:` then `if not isinstance(sec, dict): continue`. Optionally also filter at the source for full consistency with the rest of the file: `baton_sections = [s for s in baton.get("sections", []) if isinstance(s, dict)]` at line 342, which would also protect the infer_element_coord_scale call at line 360-366 that passes baton_sections downstream.

### 18. [P2-medium] `scripts/report/html_builder.py:503-536` — baton viewport used as dict when it can be JSON null

- **Symbol:** `_process_screenshots`  ·  **Category:** unchecked-get  ·  **Reviewer severity:** P2-medium  ·  **Confidence:** 0.6
- **Verification:** 2/2 skeptics confirmed · reachable=True · no existing test covers it
- **Trigger:** A baton.json with an explicit `"viewport": null` (key present, value null).
- **Why it breaks:** `viewport = baton.get("viewport", {})` only substitutes {} when the key is ABSENT; a present-but-null value returns None. Subsequent `viewport.get("width")` / `viewport.get("height")` (lines 503, 535-536) then raise AttributeError. baton is loaded with raw json.load in _load_inputs (lines 143-144) with no jsonschema validation, so a null viewport is not caught upstream. Same pattern at _load_metadata line 653.
- **Proposed fix:** Use `viewport = baton.get("viewport") or {}` so a null value also degrades to an empty dict.
- **Verifier refinement:** Apply `viewport = baton.get("viewport") or {}` at both html_builder.py:502 (_process_screenshots) and html_builder.py:653 (_load_metadata), matching the existing defensive idiom already used at geometry_validator.py:158. The reviewer's proposed fix is correct; just apply it at both sites, not only line 503.

### 19. [P2-medium] `scripts/report/v2_markers.py:904` — mapping["finding_index"] KeyError on operator-override entries keyed only by f_ref

- **Symbol:** `compute_marker_positions_v2`  ·  **Category:** unchecked-get  ·  **Reviewer severity:** P1-high  ·  **Confidence:** 0.78
- **Verification:** 2/2 skeptics confirmed · reachable=True · no existing test covers it
- **Trigger:** An operator-overrides JSON entry that supplies f_ref + slide but omits finding_index. merge_markers keys such an entry by f_ref (line 827: `ov.get("f_ref") or ("idx", ...)`) and stores `dict(ov)` verbatim without ever setting finding_index.
- **Why it breaks:** Line 904 uses subscript `finding_idx = mapping["finding_index"]` (not .get). merge_markers (lines 835-837) builds operator-only entries via `entry = dict(ov); entry.setdefault("match_method", ...)` — it never guarantees a finding_index key. Every other field read in this loop uses .get() defensively; this one assumes the key is present. An operator who pins a finding by f_ref (the documented preferred v2 key) and provides a slide reaches line 904 (after passing the `slide is None` guard) and crashes with KeyError.
- **Proposed fix:** Use `finding_idx = mapping.get("finding_index")` and fall back to f_ref/burn_number, or have merge_markers backfill finding_index from the matched auto entry.
- **Verifier refinement:** Use `finding_idx = mapping.get("finding_index")` at line 904 and tolerate None downstream (burn_number already falls back via `mapping.get("burn_number") or finding_idx`, so guard that too). More robust: in merge_markers else branch (v2_markers.py:835), backfill finding_index when the operator entry omits it — e.g. set entry.setdefault("finding_index", None) is insufficient; instead skip/queue operator entries whose f_ref resolves to no known finding, or surface them as unplaced. Either fix prevents the KeyError. The reviewer's proposed .get() + f_ref/burn_number fallback is correct.

### 20. [P2-medium] `scripts/report/v2_markers.py:911` — slide compared with < against int when operator JSON can supply a string slide

- **Symbol:** `compute_marker_positions_v2`  ·  **Category:** str-numeric  ·  **Reviewer severity:** P2-medium  ·  **Confidence:** 0.6
- **Verification:** 2/2 skeptics confirmed · reachable=True · no existing test covers it
- **Trigger:** Operator-overrides JSON with `"slide": "2"` (string) — operator-authored, not produced by auto_map_markers_v2. merge_markers does `merged.update(ov)` (line 831), so the override's raw slide value survives into the mapping.
- **Why it breaks:** Line 898 `slide = mapping.get("slide")`; line 899 only rejects None. Lines 901 `slide not in slide_markers` / `slide_markers[slide]` work for any hashable, but line 911 `slide < len(screenshots)` requires slide to be an int. A string slide raises `TypeError: '<' not supported between instances of 'str' and 'int'`. v1 compute_marker_positions has the same shape but its slides come only from auto_map_markers (always int|None); v2's merge path admits operator strings.
- **Proposed fix:** After the None guard, coerce: `try: slide = int(slide) except (TypeError, ValueError): continue` before comparisons.
- **Verifier refinement:** The reviewer's fix is correct and idiomatic for this function. After the None guard (v2_markers.py line 899), coerce: `try:\n    slide = int(slide)\nexcept (TypeError, ValueError):\n    continue` placed BEFORE line 901's dict-keying so the same normalized int is used as the `slide_markers` key and in the `< len(screenshots)` comparison. This matches the existing defensive `int(...)`/try-except patterns already used in this function (viewport dims lines 887-894, natural dims lines 913-914) and gracefully skips a non-numeric garbage slide instead of crashing. Optionally do the same coercion at the merge boundary in `_load_operator_overrides` to normalize all operator override fields once, but the point-fix at line 899-900 is sufficient and lowest-risk.

### 21. [P2-medium] `scripts/report/v2_markers.py:923` — fallback_pos["x_pct"]/["y_pct"] subscript assumes keys present and numeric on operator overrides

- **Symbol:** `compute_marker_positions_v2`  ·  **Category:** unchecked-get  ·  **Reviewer severity:** P2-medium  ·  **Confidence:** 0.55
- **Verification:** 2/2 skeptics confirmed · reachable=True · no existing test covers it
- **Trigger:** An operator-override / hand-authored markers entry that sets fallback_position to a dict lacking x_pct/y_pct, or with a string value. merge_markers passes operator dicts through verbatim (line 831 merged.update(ov)).
- **Why it breaks:** Line 922 only checks `fallback_pos is not None`; lines 923-924 do `int(nat_w * fallback_pos["x_pct"] / 100)` and the same for y_pct. An operator `"fallback_position": {}` raises KeyError; `"x_pct": "50"` makes `nat_w * "50"` a string-repeat then `/100` raises TypeError. Auto-generated fallback_position always has both numeric keys (lines 665, 687), but the operator-merge path admits arbitrary JSON shapes that are never validated.
- **Proposed fix:** Read with coercing defaults: `fx = float(fallback_pos.get("x_pct", 50) or 50)`, `fy = float(fallback_pos.get("y_pct", 50) or 50)` before the arithmetic.
- **Verifier refinement:** Coerce both reads with numeric defaults before the arithmetic, matching the codebase's existing _review_float idiom. Replace lines 922-924 with: `if fallback_pos is not None:` then `fx = _review_float(fallback_pos.get("x_pct"), 50.0)`, `fy = _review_float(fallback_pos.get("y_pct"), 50.0)`, `cx = int(nat_w * fx / 100)`, `cy = int(nat_h * fy / 100)`, and use fx/fy for the stored "x_pct"/"y_pct" too (lines 931-932) so the emitted marker dict is also numeric. (_review_float already exists in v2_html_builder.py; either import it or inline a try/except float() coercion.) The reviewer's `float(fallback_pos.get("x_pct", 50) or 50)` also works but `.get("x_pct", 50)` returns the present-but-bad value before the `or`, so a non-numeric non-falsy string like "abc" would still raise in float(); wrapping in try/except (as _review_float does) is more robust. Apply the same fix to the v1 sibling at scripts/report/markers.py:624-625/631-632.

### 22. [P3-low] `scripts/assembly/finding_stability.py:75` — title/text assumed string-like; a numeric title crashes on .lower()

- **Symbol:** `_tokenize`  ·  **Category:** str-numeric  ·  **Reviewer severity:** P3-low  ·  **Confidence:** 0.55
- **Verification:** 2/2 skeptics confirmed · reachable=True · no existing test covers it
- **Trigger:** title_token_set_jaccard called via compare_findings_stability line 365-367 where g_title = golden.get("title") or "". A truthy non-string title (e.g. title=123) survives the `or ""` and reaches _tokenize.
- **Why it breaks:** return set(_TOKEN_RE.findall((text or "").lower())). With text=123, (123 or "") -> 123 and 123.lower() raises AttributeError: 'int' object has no attribute 'lower'. The caller's `or ""` only handles None/empty, not wrong-typed truthy values; this path is unvalidated json.loads() output.
- **Proposed fix:** Normalize to str first: `text = text if isinstance(text, str) else ""` (or `str(text or "")`) at the top of _tokenize.
- **Verifier refinement:** At the top of `_tokenize` normalize defensively: `text = text if isinstance(text, str) else ""` then `return set(_TOKEN_RE.findall(text.lower()))`. This is the single chokepoint both title and any future caller flow through. The reviewer's `str(text or "")` is also acceptable but would stringify numerics into tokens (e.g. 123 -> "123") rather than treating a wrong-typed title as empty; the isinstance form is safer since a numeric title is malformed data, not meaningful tokens. For belt-and-suspenders, the caller's `golden.get("title") or ""` could additionally be `golden.get("title") if isinstance(golden.get("title"), str) else ""`, but fixing `_tokenize` alone fully closes the crash since severity_distance/levenshtein already tolerate non-strings via their own `or ""` + the int-keyed rank map. No upstream schema/validation change needed.

### 23. [P3-low] `scripts/assembly/visual_quality.py:82` — _ve(item) assumes each finding/marker is a dict; a non-dict list element raises AttributeError

- **Symbol:** `_ve`  ·  **Category:** isinstance-gap  ·  **Reviewer severity:** P3-low  ·  **Confidence:** 0.5
- **Verification:** 2/2 skeptics confirmed · reachable=True · no existing test covers it
- **Trigger:** A findings or markers list whose element is not a dict — e.g. review-state JSON where findings contains a stray string/null, or markers is a list of scalars. run_visual_quality_gates loads these straight from json.loads (lines 399-403) with only `or []` guarding the top-level key, never the element type.
- **Why it breaks:** _ve (line 82) does `finding_or_marker.get("visual_evidence")` with no isinstance check on its argument. check_proxy_overload iterates `for f in findings` (line 208) and compute_visual_evidence_summary iterates `for f in findings` (line 331) calling `_ve(f)`; if any f is a str/int/None, `.get` raises AttributeError. The values arrive from LLM-emitted review-state JSON via json.loads with no per-element schema check at this boundary.
- **Proposed fix:** Guard at the top of _ve: `if not isinstance(finding_or_marker, dict): return None`.
- **Verifier refinement:** Guard at the top of _ve as proposed: `if not isinstance(finding_or_marker, dict): return None`. For completeness the same one-line isinstance guard should be applied in review_state.py at _validate_review_state_lightweight (line 198, the `finding.get("status")` loop) and ideally _validate_review_state_references (line 208), which share the identical gap, but those are outside this claim's scope.

### 24. [P3-low] `scripts/dom_preprocess.py:368` — for el in elements crashes when baton has "elements": null

- **Symbol:** `preprocess_device`  ·  **Category:** iteration-over-none  ·  **Reviewer severity:** P2-medium  ·  **Confidence:** 0.7
- **Verification:** 1/2 skeptics confirmed · reachable=False · no existing test covers it
- **Trigger:** baton.json contains an explicit null value: `"elements": null`. json.loads yields Python None; `baton.get("elements", [])` returns None (the [] default applies only when the KEY is absent, not when its value is null).
- **Why it breaks:** Line 343 `elements = baton.get("elements", [])` -> None for a null value. `infer_element_coord_scale` at 360 tolerates None internally (`for element in elements or []`), masking the problem, but line 368 `for el in elements:` iterates None directly -> TypeError: 'NoneType' object is not iterable.
- **Proposed fix:** Coerce at read time: `elements = baton.get("elements") or []` (and likewise for sections at line 342).
- **Verifier refinement:** Apply the codebase's existing safe idiom to both vulnerable reads: `elements = baton.get("elements") or []` (line 343) and `baton_sections = baton.get("sections") or []` (line 342). This matches lines 345 and 362 which already use `baton.get(...) or default`. Coercing at read time also protects the downstream `for el in elements` (368), `for cluster in clusters`, and any other consumers without per-loop guards.

### 25. [P3-low] `scripts/dom_preprocess.py:494-497` — clusters_used returned unchecked; a non-list value is iterated char-by-char

- **Symbol:** `_resolve_clusters`  ·  **Category:** dict-vs-list  ·  **Reviewer severity:** P3-low  ·  **Confidence:** 0.5
- **Verification:** 2/2 skeptics confirmed · reachable=True · no existing test covers it
- **Trigger:** meta.json has `"clusters_used": "visual-cta"` (a bare string instead of a list), produced by a hand-edit or a non-canonical writer.
- **Why it breaks:** Line 494 `clusters = meta.get("clusters_used") or []`; line 495-496 returns `clusters` if truthy with no isinstance(list) check. A string is truthy, so it is returned and `preprocess_device` does `for cluster in clusters` (line 407), iterating individual characters, then `f"cluster-context-{cluster}-{device}.json"` writes garbage per-character filenames — silent wrong-typed output, not a crash.
- **Proposed fix:** `clusters = meta.get("clusters_used")` then `if isinstance(clusters, list) and clusters: return clusters`.
- **Verifier refinement:** In _resolve_clusters, replace the truthy check with a type-and-content guard: clusters = meta.get("clusters_used"); if isinstance(clusters, list) and clusters: return clusters; return CLUSTERS_DEFAULT. Optionally also coerce/validate entries are str so a list containing non-strings doesn't propagate. This matches the field-shape rule already encoded in meta_validator.py (clusters_used must be a list).

### 26. [P3-low] `scripts/report/v2_html_builder.py:63-68` — int(scroll_y) on unvalidated operator override anchor crashes the whole report

- **Symbol:** `_build_evidence_anchors_html`  ·  **Category:** str-numeric  ·  **Reviewer severity:** P3-low  ·  **Confidence:** 0.5
- **Verification:** 2/2 skeptics confirmed · reachable=True · no existing test covers it
- **Trigger:** An operator review-state with status=edited/approved and an `evidence_anchors_override` entry whose scroll_y is a non-numeric string, e.g. {"type":"visual","scroll_y":"above"}.
- **Why it breaks:** _apply_review_state_to_findings (v2_html_builder.py line 463-464) assigns finding["evidence_anchors"] = review["evidence_anchors_override"] from operator JSON, and review-state is loaded with no schema validation (the review-state schema does not define evidence_anchors_override at all). This runs in Phase 2c before _build_evidence_anchors_html, where `int(scroll_y)` (lines 63,67) assumes an int. A string like "above" raises ValueError and aborts report generation. The validated specialist path types scroll_y as integer, so only the override path is exposed.
- **Proposed fix:** Coerce defensively: `try: scroll_y_int = int(scroll_y) except (TypeError, ValueError): scroll_y_int = None` and guard the format on the result.
- **Verifier refinement:** The proposed fix is correct and idiomatic. Coerce defensively at the two call sites (lines 63 and 67), e.g.: `def _fmt_scroll(v):` `    try: return f" @ y={int(v)}"` `    except (TypeError, ValueError): return ""` and use scroll_part = _fmt_scroll(scroll_y). This also transparently handles float-string and other non-int operator inputs, not just the "above" case. Optionally harden _apply_review_state_to_findings further by filtering evidence_anchors_override items to dicts, but coercing at the int() boundary is the minimal, sufficient fix since that is the only place the value is treated as numeric.

### 27. [P3-low] `scripts/report/v2_html_builder.py:64` — escape_html(viewport) raises AttributeError when viewport is a non-zero number

- **Symbol:** `_build_evidence_anchors_html`  ·  **Category:** bytes-str  ·  **Reviewer severity:** P3-low  ·  **Confidence:** 0.45
- **Verification:** 2/2 skeptics confirmed · reachable=True · no existing test covers it
- **Trigger:** An operator evidence_anchors_override entry with viewport set to a non-zero int/float, e.g. {"type":"visual","viewport":1}.
- **Why it breaks:** `viewport = ea.get("viewport") or ""` keeps a non-empty number (1 is truthy). escape_html (utils.py line 109) does `if not text: return ""` then `text.replace(...)`; for an int like 1, `not 1` is False so it calls `1.replace(...)` -> AttributeError. Reachable only via the unvalidated review-state evidence_anchors_override path (the specialist schema types viewport as a string), but no validation gate exists before render.
- **Proposed fix:** Stringify before escaping: `escape_html(str(viewport))`, or have escape_html coerce non-str inputs with str().
- **Verifier refinement:** Coerce at the escape boundary: change escape_html (scripts/report/utils.py:109) to `if not text: return ""` then operate on `str(text)`, e.g. `text = str(text)` before the .replace chain. This is more robust than only stringifying viewport at v2_html_builder.py:64, because the same unvalidated override path also feeds reference/context/atype into escape_html and could carry non-str types. If a localized fix is preferred, also apply `escape_html(str(viewport))` at line 64. Note scroll_y at lines 63/67 uses int(scroll_y) which would TypeError on a non-numeric string from the same override path — worth fixing in the same pass.

### 28. [P3-low] `scripts/report/v2_loader.py:994-998` — priority_path stories assumed to be dicts from unvalidated synthesizer JSON

- **Symbol:** `load_v2_priority_path`  ·  **Category:** json-coercion  ·  **Reviewer severity:** P3-low  ·  **Confidence:** 0.4
- **Verification:** 1/2 skeptics confirmed · reachable=True · no existing test covers it
- **Trigger:** A synthesizer-emission-v1.json whose "priority_path" is a list containing a non-object element (e.g. a bare string ref) — the file is read with raw json.loads and never schema-validated here.
- **Why it breaks:** `stories = data.get("priority_path") or []` then `for i, story in enumerate(stories, start=1)` and immediately `_priority_story_refs_for_device(story, ...)` plus `story.get(...)` (lines 1051-1061). If a story element is a string, `story.get` raises AttributeError. load_v2_priority_path does no isinstance check and does not run the synthesizer jsonschema, relying entirely on the writer having produced valid JSON.
- **Proposed fix:** Skip non-dict stories: `for i, story in enumerate(stories, start=1): if not isinstance(story, dict): continue`.
- **Verifier refinement:** Add a type guard at the top of the loop in load_v2_priority_path so the renderer is robust to a malformed emission: `for i, story in enumerate(stories, start=1): if not isinstance(story, dict): continue`. This matches the proposed fix and the loader's existing defensive style (it already tolerates missing keys via .get with defaults). Optionally also guard at line 1066 in _priority_story_refs_for_device (return [] when story is not a dict) since that is where the first AttributeError actually fires. A stricter alternative — wiring validate_synthesizer_emission_payload into the report path so a schema-invalid emission is rejected before rendering — would address the root cause (the renderer trusting an unvalidated LLM-authored file) but is a larger change than the P3 warrants.

### 29. [P3-low] `scripts/report/v2_markers.py:185` — Return annotation tuple[int, float, float] | None but function returns a 4-tuple

- **Symbol:** `_section_centroid`  ·  **Category:** unpacking  ·  **Reviewer severity:** P3-low  ·  **Confidence:** 0.85
- **Verification:** 2/2 skeptics confirmed · reachable=False · no existing test covers it
- **Trigger:** Any successful section match — the only non-None return (line 220) is `(slide_idx, x_pct, y_pct, screenshot_ref)`, a 4-tuple, whereas the signature (line 185) promises a 3-tuple.
- **Why it breaks:** Signature `-> tuple[int, float, float] | None` (line 185) disagrees with the actual `return (slide_idx, x_pct, y_pct, screenshot_ref)` (line 220). The sole caller (line 676) correctly unpacks 4 values, so no crash today, but the lying annotation is a latent unpacking hazard: a caller trusting the signature would write `a, b, c = _section_centroid(...)` and get ValueError 'too many values to unpack'. The unused viewport_h (line 217) confirms the body drifted from the contract.
- **Proposed fix:** Change the annotation to `tuple[int, float, float, str | None] | None` to match the real 4-tuple return.

### 30. [P3-low] `scripts/serve-editor.cjs:22` — Non-numeric --port silently coerces to NaN and is passed to server.listen

- **Symbol:** `port (module top-level)`  ·  **Category:** str-numeric  ·  **Reviewer severity:** P2-medium  ·  **Confidence:** 0.6
- **Verification:** 1/2 skeptics confirmed · reachable=True · no existing test covers it
- **Trigger:** User invokes `node scripts/serve-editor.cjs --engagement X --port abc`. argValue returns the string "abc"; Number("abc") yields NaN.
- **Why it breaks:** `const port = Number(argValue("--port", "8787"));` then `server.listen(port, "127.0.0.1", ...)` (line 198) and `new URL(req.url, "http://localhost:${port}")` (line 158). A non-numeric --port produces NaN, not an int. Node coerces NaN port to a random/0 port or throws ERR_SOCKET_BAD_PORT depending on value, and `http://localhost:NaN` builds a bogus base URL. The string "8787" default works because Number coerces it, masking that no numeric validation exists, so any non-numeric arg becomes NaN rather than being rejected.
- **Proposed fix:** Validate after coercion: `const port = Number(argValue("--port", "8787")); if (!Number.isInteger(port) || port < 0 || port > 65535) { console.error("--port must be an integer 0-65535"); process.exit(2); }`
- **Verifier refinement:** The proposed fix is functionally fine and worth applying as a UX/hardening improvement (clearer error than the raw RangeError): `const port = Number(argValue("--port", "8787")); if (!Number.isInteger(port) || port < 0 || port > 65535) { console.error("--port must be an integer 0-65535"); process.exit(2); }`. Note this only upgrades the error message — without it, an invalid --port already fails loudly and immediately via ERR_SOCKET_BAD_PORT (it does NOT silently start on a wrong/random port), so this is graceful-error polish, not a correctness fix.

### 31. [P3-low] `scripts/validate-cluster-files.py:271-272` — meta.json json.loads output assumed to be a dict; array/scalar or non-dict 'page' crashes with AttributeError

- **Symbol:** `_page_netloc_from_meta`  ·  **Category:** json-coercion  ·  **Reviewer severity:** P2-medium  ·  **Confidence:** 0.83
- **Verification:** 1/2 skeptics confirmed · reachable=True · no existing test covers it
- **Trigger:** A meta.json whose top-level JSON value is an array (e.g. '[...]') or scalar (e.g. '"x"'/42), OR a valid object whose "page" value is a string/list rather than an object (e.g. {"page": "https://x.com"}). The standalone --engagement lint reads a possibly hand-edited / LLM-emitted meta.json that does NOT pass through assembly/meta_validator.py.
- **Why it breaks:** Line 268 `meta = json.loads(meta_path.read_text(...))` is typed/used as a dict immediately: line 271 `page = meta.get("page") or {}` calls .get() on `meta`. Only `json.JSONDecodeError` is caught (line 269) — a successfully-parsed JSON array/scalar passes the try and then `meta.get` raises `AttributeError: 'list'/'str'/'int' object has no attribute 'get'`. Sub-case: if `meta` is a dict but `"page"` is a non-empty string/list, `page` is that truthy non-dict and line 272 `page.get("url")` raises `AttributeError`. The author already used the defensive `or {}` idiom, showing intent to guard, but the guard is incomplete because `.get` is reached before any isinstance check.
- **Proposed fix:** After parsing, guard the type: `if not isinstance(meta, dict): return None`, and at line 271 use `page = meta.get("page"); page = page if isinstance(page, dict) else {}` before calling page.get("url").
- **Verifier refinement:** The reviewer's fix is correct and matches the intent. After parsing, guard both levels: `if not isinstance(meta, dict): return None` (right after line 268's parse), and replace line 271 with `page = meta.get("page"); page = page if isinstance(page, dict) else {}` before `page.get("url")`. Note the same `meta.get("page") or {}` idiom appears unguarded in production readers (report/html_builder.py:158,661; assembly/review_state.py:1129; report/v2_loader.py:1189) — if hardening this defensively, apply consistently, though those consume code-produced meta.json where the dict shape is guaranteed.


---

## Contested (5) — one skeptic confirmed, one refuted (judgement call)

1. **[P1-high] `scripts/assembly/finding_stability.py:344-345`** — element field assumed to be a dict; `or {}` does not defend against a non-dict element
   - Fix if pursued: Guard the type, not just falsiness: `el = golden.get("element"); g_bidx = el.get("baton_index", "") if isinstance(el, dict) else ""` (and likewise for candidate).
2. **[P2-medium] `scripts/assembly/finding_stability.py:104`** — severity assumed to be a string; a numeric severity crashes on .upper()
   - Fix if pursued: Coerce defensively: `s = severity if isinstance(severity, str) else ""; return _SEVERITY_RANK.get(s.upper(), 0)` — or `str(severity).upper()` if non-string labels should still rank as unknown.
3. **[P2-medium] `scripts/report/html_builder.py:514-538`** — Screenshot metadata indexed by filtered-list position causes misaligned aspect ratios
   - Fix if pursued: Carry the metadata alongside the path: build a list of (path, meta_dict) tuples in the first loop and unpack in the second, instead of re-indexing screenshots[i].
4. **[P2-medium] `scripts/dom_preprocess.py:411`** — for sec in baton_sections crashes when baton has "sections": null
   - Fix if pursued: `baton_sections = baton.get("sections") or []` at line 342.
5. **[P3-low] `scripts/lead_prep.py:109-127`** — screenshots/sections containers assumed list; a dict survives `or []` and is indexed by int
   - Fix if pursued: After reading, normalize: `screenshots = baton.get("screenshots") if isinstance(baton.get("screenshots"), list) else []` (same for sections).


---

## Refuted (7) — flagged by a reviewer but knocked down on verification

1. `scripts/assembly/finding_stability.py:468-471` — findings list elements assumed to be dicts; isinstance check only validates the container
   - Why refuted: The Python pattern the claim describes is real but the triggering input is not reachable.

Mechanism check (accurate): `_index_by_ref` (finding_stability.py:468-471) calls `f.get("cluster")`/`f.get("local_id")` on each element, and `_load_findings` (line 453) only asserts `isinstance(findings, list)`, not per-element dict-ness. A non-dict element would raise AttributeError. True at the line level.

Reachability (decisive, all against the claim):
1. SCHEMA FORBIDS IT. schema/synthesizer-emission-v1.json has NO top-level `findings` property and is `additionalProperties:false`. A schema-valid synth emission literally cannot contain a `findings` key, let alone a list of strings/numbers. There is no jsonschema layer that validates a `findings` array because the array isn't part of the contract.
2. NO PRODUCER EMITS IT. The canonical producer (scripts/build_synthesizer_emission_fallback.py) writes priority_path/quick_wins_manifest/severity_manifest/scope_page_synchronized_refs — never a top-level `findings`. The live synthesizer per the schema emits `humanized_findings`, not `findings`. Grep for `"findings":` in scripts/ finds only unrelated dicts (dedup, review_state, html_builder, geometry_validator, v2_loader) — none target the emission file.
3. ALL 14 REAL FILES LACK IT. I parsed every synthesizer-emission-v1.json on disk (11 in docs/ecp/, 2 golden fixtures incl. fixtures/awdmods-homepage/ that diff_engagements is documented to read, 1 test fixture). Every one has NO `findings` key; top keys are audit_documents/.../humanized_findings.
4. THE ONLY PRODUCTION CALLER SHORT-CIRCUITS. scripts/test-fixture-stability.py is the sole production caller of diff_engagements. On any real dir, `_load_findings` does `data.get("findings")` → None → raises ValueError at line 453 → caught at line 122 → exit 2. Control never reaches `_index_by_ref`.
5. THE CODEBASE DOCUMENTS THIS AS DEAD. determinism_gate.py:28-30 and 721-726 explicitly call diff_engagements' `findings`-array assumption a "latent bug ... (which doesn't exist on real output)" and route Phase K production around it via `_diff_engagement_findings`/`_index_findings_by_ref` over dataclass findings from cluster files.

So feeding a non-dict element to `_index_by_ref` requires a hand-authored file that has a top-level `findings` list (no producer creates one; the schema forbids one) AND contains a string/number — a synthetic input deliberately crafted to break a code path that real output never exercises. That is not a concrete reachable trigger.

Note on the proposed fix: `if not isinstance(f, dict): continue` would mirror the existing skip-on-missing-key behavior and is harmless, but it guards an unreachable path and would silently swallow genuinely malformed input rather than surfacing it — defensible only as cheap hardening, not a P2 correctness fix.
2. `scripts/assembly/business_rules.py:329-330` — evidence_tier comparison treats tier as Bronze/Silver/Gold string but unknown/numeric tiers silently rank 0 and mis-report
   - Why refuted: The code-level mechanic the reviewer describes is real: at line 329, EVIDENCE_TIER_RANK.get(c.get("tier",""), 0) returns 0 for any tier not in {"Bronze","Silver","Gold"} (numeric, lowercase, or unknown), and at line 330 `expected` resolves to "" because no rank maps to 0 (EVIDENCE_TIER_RANK = {"Bronze":1,"Silver":2,"Gold":3}). The `if expected and declared` guard at line 331 then short-circuits, so _check_evidence_tier returns [] (no violation) for a malformed tier. That specific rule does silently no-op.

However the claimed IMPACT and REACHABILITY are false. The triggering inputs cannot reach this code in a way that matters, because schema validation gates every consumer BEFORE the value has any downstream effect:

1. Schema forbids both trigger values. finding-v1.json constrains reference_citations[].tier as {"type":"string","enum":["Gold","Silver","Bronze"]} (lines 315-319, tier is required per line 298) and evidence_tier as {"type":"string","enum":["Gold","Silver","Bronze"]} (lines 341-344). So {"tier":3} fails the string type check and {"tier":"gold"} (lowercase) fails the enum.

2. Both real callers run schema validation and reject on failure:
   - scripts/test-specialist.py validate_emission(): runs validator.iter_errors(emission) (line 917) AND business rules, then all_errors = identity_errors + schema_errors + business_errors (line 959); any non-empty list -> FAIL/exit 1 and retry-prompt. A malformed tier always yields a non-empty schema_errors, so the emission is bounced regardless of _check_evidence_tier returning empty.
   - scripts/assembly/json_parser.py parse_emission_file(): calls validate_emission_payload() at line 203 which RAISES EmissionValidationError on any schema error, BEFORE _finding_from_dict() builds any Finding (line 209). So no wrong-typed evidence_tier ever reaches the dedup/synth downstream.

The reviewer's stated harm ("a malformed tier passes the business rule ... producing wrong-typed/wrong evidence_tier downstream rather than a violation") does not occur: the schema gate produces the violation and bounces the emission first. _check_evidence_tier silently passing on bad input is masked entirely by the schema, which is precisely the kind of guarded value the brief warned about. No caller invokes validate_business_rules on un-schema-validated data. Severity therefore none; this is at most a defense-in-depth nicety (the module docstring even notes the schema already promotes evidence_tier via allOf and business rules are redundant verification).
3. `scripts/assembly/business_rules.py:148-151` — FindingBand.parse assumes both halves are int-parseable; '3' or '3-' raises ValueError
   - Why refuted: The claim is technically correct that FindingBand.parse('3', '3-', 'three-five', or '3-5-7') would raise ValueError — but the adversarial reachability lens defeats it. There is exactly ONE runtime caller (scripts/test-specialist.py:206) and it wraps the call in `try/except (ValueError, AttributeError): target_band = None`, with the comment "malformed — silently skip; lead can warn". A second usage at test-specialist.py:911 (`params.get("target_band")`) reads the ALREADY-PARSED FindingBand|None from that guarded path — it does not call parse() at all, and is additionally wrapped in `try/except (FileNotFoundError, ValueError)`. So every runtime path to parse() is double-guarded.

Beyond the guard, the triggering input cannot even arise from real data: the value comes from `target_finding_count` in contracts/specialists/*.md YAML. I enumerated all 10 cluster contracts — every value is a well-formed `<int>-<int>` band (4-7, 3-6, 2-5, 1-3, 5-8, etc.). No contract ships '3', '3-', or 'three-five'. The reviewer's own evidence concedes "The known internal caller wraps it in try/except ValueError."

The reviewer's secondary argument — "the annotation -> FindingBand lies" and "any other caller crashes" — is speculative: there are no other callers. The only unguarded callers are the unit tests (test_v2_business_rules.py:587-588), which pass hardcoded valid strings ('3-5', '1-10') and would never trigger the path. parse() being in __all__ is a public-export argument, but no production code outside the guarded path invokes it, so no concrete reachable crash exists.

This is a P3-low style/robustness nit (validating inputs to a public constructor is defensible hygiene), but it is NOT a reachable bug: schema-of-record data is well-formed and the sole runtime caller catches the exception by design.
4. `scripts/prep_synth_input.py:46-48` — KeyError on ethics findings: cluster_counters built only from clusters_used, but finalized.findings includes cluster='ethics'
   - Why refuted: The claim conflates two distinct code paths. prep_synth_input.py (scripts/prep_synth_input.py:32-37) uses the V1 pipeline: load_all_cluster_files -> parse_cluster_file -> deduplicate (dedup.py:42). It does NOT use deduplicate_v2 (dedup.py:345) or v2_loader, which is where the claim's evidence actually lives.

Tracing the producer of f.cluster in the V1 path: assembly/parser.py:124-125 constructs every Finding with cluster=<the cluster slug argument>. That argument is the loop variable in load_all_cluster_files (parser.py:271-285), which iterates ONLY over clusters = meta['clusters_used']. So in this path EVERY finding's cluster is, by construction, a member of clusters_used. cluster_counters = {c: 0 for c in clusters} (line 46) therefore always contains the key, and cluster_counters[f.cluster] += 1 (line 48) can never KeyError.

The claim's premise that 'ethics findings carry f.cluster == ethics (dedup.py:374)' is the V2 routing rule (deduplicate_v2: `if f.cluster == 'ethics' and ...`). prep_synth_input.py calls the V1 deduplicate, whose ethics split routes purely by ethics_state in ('BLOCK','ADJACENT') (dedup.py:67) and does NOT reassign or require cluster=='ethics'. A V1 ethics finding keeps the cluster slug of the .md file it came from -- which is in clusters_used. The cluster=='ethics' value only originates in v2_loader.py:208 (_finding_dict('ethics','page',f)) reading the separate ethics-findings.json, and that same V2 path EXPLICITLY appends 'ethics' to clusters_used (v2_loader.py:431-432) BEFORE FinalizedFindings.build -- so even the V2 path cannot KeyError, and the V2 path never executes the prep_synth_input loop anyway.

Corroboration: assemble-audit.py:273-276 (the canonical production assembler) builds FinalizedFindings identically -- list(result.ethics_findings)+list(result.kept) with bare `clusters` -- using the same V1 deduplicate. It runs on real engagements without a KeyError, confirming V1 ethics findings do not carry an out-of-clusters_used cluster. Real engagement files (docs/ecp/2026-06-01-749a3c3d) use V2 JSON + ethics-findings.json; the .md cluster files the V1 path requires are absent, meaning prep_synth_input.py is itself a V1-only utility whose findings come exclusively from clusters_used slugs.

Reachability conclusion: a finding with cluster NOT in clusters_used cannot be produced in this code path (parser hard-binds cluster to the clusters_used slug; meta_validator.py only checks clusters_used is a list, never that it contains 'ethics', and even if it did, that would make 'ethics' a key, not a missing one). assign_display_indices is defensively orphan-tolerant (by_cluster.get(cluster, []), pipeline.py:150) regardless. No concrete input triggers the KeyError.
5. `scripts/assemble-audit.py:130,249` — ', '.join(clusters) crashes if meta['clusters_used'] is a list of non-strings; meta_validator only warns and does not enforce element type
   - Why refuted: The claim's isolated facts are correct: validate_meta_json (meta_validator.py:124-129) only checks isinstance(data[field], list) and never validates element types; its warnings only print to stderr and never abort (assemble-audit.py:121-123); the `if not clusters` guard (line 131) passes a non-empty list of ints; and str.join over a list containing an int raises TypeError. So the validator side is genuinely unconstrained (LLM-emitted meta.json, no jsonschema anywhere on clusters_used elements).

However, the join at line 249 is NOT reachable with non-string clusters in any realistic run. Between line 130 and line 249, line 169 calls load_all_cluster_files(engagement_dir, device, clusters), which iterates the SAME cluster elements: `for cluster in clusters: filename = f"cluster-{cluster}-{device}.md"; filepath = engagement_dir / filename; if not filepath.exists(): missing.append(filename)`. For an int element like 1, the f-string yields "cluster-1-mobile.md" (no crash), but real cluster files are slug-named (confirmed by a real engagement meta.json: clusters_used = ["visual-cta", "trust-credibility", ...] → files cluster-visual-cta-mobile.md). So the int-named file does not exist, every such cluster lands in `missing`, and load_all_cluster_files raises FileNotFoundError (parser.py:292-302). main catches it at lines 170-177 and calls sys.exit(3) — terminating with a clear actionable error well BEFORE the dry-run join at line 249. The missing-files join at parser.py:298 only joins `missing`, which contains strings (filenames), so that join is safe.

The line-249 crash is only reachable if an operator/LLM simultaneously (a) emits integer/non-string clusters_used elements AND (b) creates files literally named cluster-1-mobile.md, cluster-2-mobile.md on disk — a contrived co-occurrence that contradicts the stated trigger (an LLM emitting [1,2]). In the trigger scenario the program exits cleanly at code 3, not a TypeError. The bug as described (reached at join time on a plain [1,2] meta.json) does not occur; load_all_cluster_files is the type-effective gate that fires first.
6. `scripts/report/v2_loader.py:192-193` — Cluster-emission findings iterated as list-of-dicts with no validation
   - Why refuted: The code-level mechanic the reviewer describes is real as written: `_finding_dict(cluster, device, raw)` (v2_loader.py:215) immediately does `raw.get("element")` at line 222, and `load_cluster_emission_findings` reads the file with raw `json.loads` (line 188) and iterates `data.get("findings", [])` (line 192) with NO jsonschema validation, unlike the render path (build_canonical_view -> parse_emission_file). So IF `findings` were a dict (iteration yields str keys) or contained a stray string, `_finding_dict` would raise AttributeError. That part checks out.

But the claim fails the reachability test, which is decisive here. I grepped the entire repo (scripts/, tests/, dynamic importlib/getattr sites): `load_cluster_emission_findings` has ZERO callers anywhere. It is not invoked by any production script (generate-report.py / load_v2_engagement / load_v2_findings all route through build_canonical_view, which DOES validate via parse_emission_file), and it is not invoked by any test. The reviewer's own evidence hedges "no production caller invokes it today (used by tests)" — and even that is inaccurate: tests in tests/test_anchor_candidates.py call `_finding_dict` DIRECTLY with hand-built dicts (lines 692, 741) and call `build_canonical_view`, never the public `load_cluster_emission_findings`. The buggy loop at lines 192-193 lives in fully dead code.

Therefore no runtime value — well-formed or malformed — ever flows through that loop. schema/cluster-emission-v1.json constrains conformant producers to `findings: array of finding objects`, but that schema is irrelevant to this path since this loader never applies it; the point is moot because the loop is never executed. A bug that cannot be reached by any caller is not a runtime defect; it is at most a latent hardening nit in dead code. The proposed isinstance guard is harmless and would be correct if the function were ever wired up, but the P3-low severity overstates the case: with zero callers the practical severity is none.
7. `scripts/serve-editor.cjs:22` — --port parsed with Number() yields NaN for non-numeric input and is passed to server.listen
   - Why refuted: The reviewer's central mechanism is factually false. Tested on the repo's Node (v24.15.0, no engine pin in package.json): Number("abc") is NaN (correct), but server.listen(NaN, "127.0.0.1", ...) at line 198 does NOT silently coerce to port 0 / an ephemeral port. It throws immediately: RangeError [ERR_SOCKET_BAD_PORT]: options.port should be >= 0 and < 65536. Received type number (NaN). Out-of-range (99999) and negative ports also throw ERR_SOCKET_BAD_PORT. Node's validatePort in node:net has rejected NaN/out-of-range for many major versions; the "coerces to 0" behavior only applies to literal 0 or an omitted port, never NaN. Consequence chain: the server fails to bind and the process exits non-zero at startup with a clear, specific error naming the exact constraint. The request handler never runs, so the line 158 template (localhost:NaN) is never constructed and no wrong port is ever served. The line 199 success-callback URL never prints because listen throws before the callback fires. NaN does reach line 198 (no upstream validation), so reachable=true at the syntactic level, but the CLAIMED impact ("silently producing wrong-typed behavior", "binds a port the operator didn't request", "the printed URL is wrong") is unreachable — Node intercepts it with a hard throw. This is also an operator-run CLI script, not a schema- or caller-constrained surface; the trigger requires the operator to type a non-numeric --port. The proposed fix only swaps Node's already-clear RangeError for a marginally friendlier message; it fixes no actual wrong-typed runtime behavior. The bug as described (str-numeric NaN flowing to silent misbehavior) does not occur.
