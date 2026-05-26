"""Anchor candidate registry (Phase 4a — 2026-05-18).

Phase 4a brings forward the Phase 2 + Phase 3 visual evidence work into the
specialist input layer. Instead of asking specialists to invent baton
``e_index`` citations from raw element data (which produces the giant
parent-container rectangles Phase 3 now catches), the lead pre-computes a
small registry of role-classified candidate elements + a stable
``candidate_id`` per element. Specialists may reference candidates by
``candidate_id`` (e.g., ``cta-1``, ``price-1``, ``trust-strip-2``) instead
of having to scan the full baton.

Phase 4a ships the registry as a SIDE-CHANNEL: specialists CAN use it but
the existing ``element.baton_index`` contract still works. Phase 4b will
make the candidate registry mandatory by updating the specialist prompt
template to require it, plus a business-rules check that rejects findings
whose baton_index doesn't appear in the candidate registry (with explicit
``intentional_outside_registry`` opt-out for the rare case the candidate
ranker missed something).

Pairs with:
- ``scripts/report/visual_evidence.py`` — visual_evidence types that
  consume candidate IDs in ``observed_anchor.candidate_id``
- ``schema/finding-v1.json`` ``visual_evidence`` field
- ``docs/ecp/2026-05-18-report-accuracy-and-hotspot-remediation-plan.md``
  Phase 4 plan section

Roles classified (12 total):

- ``primary-cta``: Add-to-cart / Buy / Configure CTAs
- ``secondary-cta``: Other action buttons (favorite, share, compare)
- ``price-block``: Price displays with currency markers
- ``product-title``: h1/h2 product name headings
- ``subheading``: Secondary h2/h3 section titles
- ``gallery-image``: Product gallery images and thumbnails
- ``variant-selector``: Color/size swatches and selectors
- ``search``: Search inputs and forms
- ``reviews-widget``: Review/rating elements
- ``trust-strip``: Trust badges, guarantees, payment icons
- ``navigation``: Top nav / hamburger / mega-menu
- ``footer-region``: Footer container and footer policy links

Output sidecar (``anchor-candidates-{device}.json``):

    {
      "engagement_id": "...",
      "device": "desktop",
      "candidates_by_role": {
        "primary-cta": [
          {"candidate_id": "primary-cta-1", "e_index": "e18",
           "tag": "button", "role": "button",
           "accessible_name_truncated": "Select Color",
           "rect": {...}, "rank_score": 0.95,
           "rank_factors": {...}}
        ],
        ...
      },
      "candidate_to_e_index": {"primary-cta-1": "e18", ...},
      "expected_overlay_templates": {...}
    }
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Callable

from .atomic_write import atomic_write_json

# ---------------------------------------------------------------------------
# Role classifiers — each returns a (role, confidence) tuple or None
# ---------------------------------------------------------------------------

_CURRENCY_PATTERN = re.compile(
    r"[$€£¥₹]\s*\d|(\d+[.,]\d{2})\s*(USD|EUR|GBP|JPY|CAD|AUD|INR)",
    re.IGNORECASE,
)
_PRIMARY_CTA_TOKENS = (
    "add to cart", "add-to-cart", "buy now", "buy", "purchase",
    "checkout", "order now", "shop now", "select color", "select size",
    "configure", "customize", "build",
)
_SECONDARY_CTA_TOKENS = (
    "wishlist", "favorite", "save for later", "share", "compare", "notify me",
)
_TRUST_TOKENS = (
    "secure", "guarantee", "warranty", "free shipping", "money back",
    "certified", "verified", "trusted", "ssl", "ssl secured",
)
_REVIEW_TOKENS = (
    "review", "rating", "stars", "verified buyer", "customers", "feedback",
)
_VARIANT_TOKENS = (
    "color", "size", "variant", "option", "swatch", "select size",
    "select color", "choose", "style",
)
_PAYMENT_TOKENS = (
    "visa", "mastercard", "paypal", "apple pay", "google pay", "amex",
    "discover", "shop pay", "klarna", "afterpay", "affirm",
)


def _text_blob(el: dict) -> str:
    """Combine accessible_name + text_content + class into one searchable
    lowercase string for token matching."""
    parts = [
        str(el.get("accessible_name") or ""),
        str(el.get("text_content") or "")[:200],
        str(el.get("class") or ""),
    ]
    return " ".join(parts).lower()


def _has_currency(text: str) -> bool:
    return bool(_CURRENCY_PATTERN.search(text))


def _has_any_token(text: str, tokens: tuple[str, ...]) -> bool:
    return any(t in text for t in tokens)


def _classify(el: dict) -> tuple[str, float] | None:
    """Return (role, confidence) for an element, or None if it doesn't fit
    any candidate role.

    Confidence in [0.0, 1.0] is the classifier's self-rating. Used by the
    ranker as one input to rank_score; higher confidence wins ties.

    Classification rules are intentionally conservative — bias toward "no
    role assignment" rather than mis-assignment. The renderer can fall
    back to the raw baton when a candidate isn't found.
    """
    tag = (el.get("tag") or "").lower()
    role = (el.get("role") or "").lower()
    text = _text_blob(el)

    # 1. Search — most specific, check first
    if role == "search" or (tag == "input" and "search" in text):
        return ("search", 0.95)

    # 2. Footer + footer-region
    if role == "contentinfo" or tag == "footer":
        return ("footer-region", 0.9)

    # 3. Navigation
    if role == "navigation" or tag == "nav":
        return ("navigation", 0.85)

    # 4. Trust strip — payment names or trust tokens (free shipping,
    #    guarantee, BNPL providers). Checked BEFORE price-block because
    #    trust copy frequently mentions a dollar amount: "Free shipping
    #    on orders over $75", "Save $20 with Klarna", "Money back within
    #    30 days on purchases of $50+". Without this ordering, the
    #    currency-pattern test below would swallow those into price-block
    #    and the page would lose its trust-strip candidates. Codex
    #    2026-05-18 review of Phase 4a flagged this regression.
    if _has_any_token(text, _PAYMENT_TOKENS) or _has_any_token(text, _TRUST_TOKENS):
        return ("trust-strip", 0.8)

    # 5. Reviews widget — review/rating tokens (also before price-block
    #    because review snippets sometimes quote dollar amounts in user
    #    text like "Great value for $200").
    if _has_any_token(text, _REVIEW_TOKENS):
        return ("reviews-widget", 0.8)

    # 6. Price block — currency in text wins, AFTER trust and review
    #    classifiers have had a chance to claim the element. This is the
    #    "default for any unclassified element that quotes a price."
    if _has_currency(text):
        return ("price-block", 0.9)

    # 7. Primary CTA — button + cart/buy/checkout/configure language.
    #    Checked BEFORE variant-selector because "select color" /
    #    "select size" on a PDP is typically the gated primary CTA copy
    #    ("Add to cart" appears only after color is chosen) — see the
    #    awdmods 2026-05-18 case where button e18 says "Select Color" and
    #    IS the purchase-intent CTA, not a swatch group.
    if (
        tag == "button" or role == "button"
    ) and _has_any_token(text, _PRIMARY_CTA_TOKENS):
        return ("primary-cta", 0.95)

    # 8. Variant selector — interactive shape + variant tokens (post-CTA
    #    so genuine swatches/dropdowns are caught without stealing the
    #    PDP primary CTA).
    if (
        tag in {"button", "select"}
        and _has_any_token(text, _VARIANT_TOKENS)
    ):
        return ("variant-selector", 0.85)

    # 9. Secondary CTA — button + wishlist/share/compare language
    if (
        tag == "button" or role == "button"
    ) and _has_any_token(text, _SECONDARY_CTA_TOKENS):
        return ("secondary-cta", 0.85)

    # 10. Gallery image — img tag (or role=image) with product context
    if tag == "img" or role == "image":
        return ("gallery-image", 0.7)

    # 11. Product title — h1, or first h2 above the fold. Treat all h1/h2
    #     as product-title candidates; ranker handles dominance via
    #     is_above_fold + rect size.
    if tag in {"h1", "h2"} or role == "heading":
        # If text looks like a section label ("Information", "Specifications"),
        # treat as subheading not product-title. Heuristic: short generic
        # labels are subheadings.
        text_lower = (el.get("accessible_name") or "").lower().strip()
        section_labels = {
            "information", "specifications", "about us", "my account",
            "details", "features", "shipping", "returns", "support",
            "menu", "categories",
        }
        if text_lower in section_labels:
            return ("subheading", 0.7)
        if tag == "h1" or (tag == "h2" and el.get("is_above_fold")):
            return ("product-title", 0.9)
        return ("subheading", 0.7)

    # No fit — let the specialist work from the raw baton for this element
    return None


# ---------------------------------------------------------------------------
# Ranker — assigns rank_score per element within its role
# ---------------------------------------------------------------------------


def _rank_score(el: dict, classification_confidence: float) -> tuple[float, dict]:
    """Score an element's strength as a candidate for its role.

    Factors (each in [0, 1], multiplied into the score):
    - classification confidence (from _classify)
    - above_fold: above-fold elements rank higher (0.6 baseline, 1.0 above)
    - has_accessible_name: named elements > anonymous (0.7 / 1.0)
    - rect_size_specificity: smaller rects = more specific element
      (1.0 if width<400 AND height<200; 0.5 if either dimension is large;
      0.2 if both are large — penalizes parent-container anchors)
    - text_richness: a short distinctive text wins over an empty element
      (0.5 if empty; 1.0 if 10-120 chars; 0.7 if very long)

    Returns (score, factors_dict) — factors_dict exposes the inputs so
    operators can debug ranking decisions.
    """
    factors = {"classification_confidence": classification_confidence}

    above_fold = bool(el.get("is_above_fold"))
    factors["above_fold"] = 1.0 if above_fold else 0.6

    accessible_name = (el.get("accessible_name") or "").strip()
    factors["has_accessible_name"] = 1.0 if accessible_name else 0.7

    rect = el.get("rect") or {}
    width = float(rect.get("width") or 0)
    height = float(rect.get("height") or 0)
    if 0 < width < 400 and 0 < height < 200:
        factors["rect_size_specificity"] = 1.0
    elif 0 < width < 400 or 0 < height < 200:
        factors["rect_size_specificity"] = 0.5
    elif width == 0 or height == 0:
        factors["rect_size_specificity"] = 0.6  # unknown size — neutral
    else:
        factors["rect_size_specificity"] = 0.2  # giant rect — penalize

    text_len = len(_text_blob(el))
    if text_len == 0:
        factors["text_richness"] = 0.5
    elif text_len <= 120:
        factors["text_richness"] = 1.0
    elif text_len <= 240:
        factors["text_richness"] = 0.85
    else:
        factors["text_richness"] = 0.7

    score = 1.0
    for v in factors.values():
        score *= float(v)
    return (round(score, 4), factors)


# ---------------------------------------------------------------------------
# Expected-overlay template registry
# ---------------------------------------------------------------------------


EXPECTED_OVERLAY_TEMPLATES: dict[str, dict[str, Any]] = {
    "sticky-cta": {
        "description": (
            "Ghost rectangle pinned at the bottom of the mobile viewport "
            "representing a missing sticky Add-to-Cart bar. Use for "
            "'no sticky CTA after scroll' findings."
        ),
        "default_placement": "viewport-bottom-sticky",
        "default_kind": "viewport",
        "default_viewport_trigger": "after_primary_cta_offscreen",
    },
    "reviews-block": {
        "description": (
            "Ghost panel representing a missing reviews section. Place "
            "below the product description or above the related-products row."
        ),
        "default_placement": "after-section",
        "default_kind": "section",
    },
    "payment-badges": {
        "description": (
            "Ghost strip of payment-method icons (Visa/MC/PayPal/Apple Pay). "
            "Place inside the purchase zone, immediately below the CTA."
        ),
        "default_placement": "after-element",
        "default_kind": "element",
    },
    "trust-strip": {
        "description": (
            "Ghost row of trust signals (guarantee, free shipping, secure "
            "checkout). Place adjacent to the price block or CTA."
        ),
        "default_placement": "after-element",
        "default_kind": "element",
    },
    "video-tile": {
        "description": (
            "Ghost tile inside the gallery thumbnail strip representing a "
            "missing product video. Place adjacent to the first gallery image."
        ),
        "default_placement": "inside-element-bottom",
        "default_kind": "element",
    },
    "msrp-anchor": {
        "description": (
            "Ghost text representing a missing MSRP strikethrough. Place "
            "immediately above the live price element."
        ),
        "default_placement": "before-element",
        "default_kind": "element",
    },
    "faq-section": {
        "description": (
            "Ghost section representing missing FAQ markup. Place after the "
            "product description."
        ),
        "default_placement": "after-section",
        "default_kind": "section",
    },
    "breadcrumb-bar": {
        "description": (
            "Ghost breadcrumb row representing missing navigation context. "
            "Place above the product title."
        ),
        "default_placement": "before-element",
        "default_kind": "element",
    },
}


# ---------------------------------------------------------------------------
# Sidecar builder
# ---------------------------------------------------------------------------


def build_candidates(baton: dict) -> dict:
    """Classify and rank candidates from a baton.

    Returns the ``candidates_by_role`` portion of the sidecar (without
    metadata wrapping). Pure function — used by tests directly.

    The candidate_id format is ``{role}-{N}`` where N is 1-based
    rank-order within the role. Same baton produces identical
    candidate_ids across runs (deterministic).
    """
    elements = baton.get("elements") or []

    # Group by role with rank score per element
    by_role: dict[str, list[dict]] = {}
    for el in elements:
        classified = _classify(el)
        if not classified:
            continue
        role, confidence = classified
        score, factors = _rank_score(el, confidence)
        by_role.setdefault(role, []).append({
            "e_index": el.get("e_index"),
            "tag": el.get("tag", ""),
            "role": el.get("role", ""),
            "accessible_name_truncated": (el.get("accessible_name") or "")[:80],
            "text_content_truncated": (el.get("text_content") or "")[:120],
            "rect": el.get("rect", {}),
            "is_above_fold": bool(el.get("is_above_fold")),
            "is_sticky": bool(el.get("is_sticky")),
            "rank_score": score,
            "rank_factors": factors,
        })

    # Sort within each role by rank_score desc, then e_index for determinism
    def _e_int(c: dict) -> int:
        e = c.get("e_index") or "e9999"
        try:
            return int(e[1:]) if e.startswith("e") and e[1:].isdigit() else 9999
        except (TypeError, ValueError):
            return 9999

    candidates_by_role: dict[str, list[dict]] = {}
    for role in sorted(by_role.keys()):
        bucket = sorted(by_role[role], key=lambda c: (-c["rank_score"], _e_int(c)))
        # Assign 1-based candidate_id within the role
        for i, c in enumerate(bucket, start=1):
            c["candidate_id"] = f"{role}-{i}"
        candidates_by_role[role] = bucket

    return candidates_by_role


def build_anchor_candidates_sidecar(
    engagement_dir: Path | str,
    device: str,
    *,
    baton_filename: str | None = None,
    out_filename: str | None = None,
) -> dict:
    """Build the anchor-candidates sidecar for one device.

    Reads the device's baton (``baton.json`` for desktop/laptop,
    ``baton-mobile.json`` for mobile), classifies + ranks candidates,
    and writes ``anchor-candidates-{device}.json`` atomically.

    Returns the full sidecar dict for in-memory callers (lead orchestration
    that wants to log counts to audit-trace.log).
    """
    engagement_dir = Path(engagement_dir)
    if baton_filename is None:
        baton_filename = (
            "baton.json" if device in {"desktop", "laptop"}
            else f"baton-{device}.json"
        )
    if out_filename is None:
        out_filename = f"anchor-candidates-{device}.json"

    baton_path = engagement_dir / baton_filename
    baton = json.loads(baton_path.read_text(encoding="utf-8"))
    candidates_by_role = build_candidates(baton)

    # Flat lookup map for renderer/specialist convenience
    candidate_to_e_index: dict[str, str] = {}
    for bucket in candidates_by_role.values():
        for c in bucket:
            cid = c.get("candidate_id")
            e_index = c.get("e_index")
            if cid and e_index:
                candidate_to_e_index[cid] = e_index

    sidecar = {
        "engagement_id": baton.get("engagement_id", ""),
        "device": baton.get("device", device),
        "candidates_by_role": candidates_by_role,
        "candidate_to_e_index": candidate_to_e_index,
        "expected_overlay_templates": EXPECTED_OVERLAY_TEMPLATES,
        "counts": {
            "total_candidates": sum(len(v) for v in candidates_by_role.values()),
            "by_role": {role: len(bucket) for role, bucket in candidates_by_role.items()},
            "baton_elements": len(baton.get("elements") or []),
        },
    }
    atomic_write_json(engagement_dir / out_filename, sidecar)
    return sidecar


class SidecarLoadError(Exception):
    """Raised when an anchor-candidates sidecar exists on disk but cannot
    be loaded as valid JSON.

    Phase 4b hardening 2 (2026-05-18): fail-loud on present-but-broken
    sidecars closes the silent-bypass class Codex caught — every sidecar
    loader (test-specialist.py, v2_loader.py, lead_prep.py,
    build_synthesizer_emission_fallback.py) used to swallow
    OSError + JSONDecodeError and treat the result as "no sidecar," which
    silently disabled the mandatory candidate-registry rule.

    Convention:
    - missing file → return None (legacy skip is correct — sidecar may
      not have been generated yet)
    - file exists but unreadable / malformed → raise this error (broken
      sidecar must NOT be silently treated as legacy mode)

    Carries enough context (path + reason) that CLI scripts can print
    a clear "anchor-candidates sidecar is not valid/readable at <path>"
    line and exit non-zero.
    """

    def __init__(self, path: "Path", reason: str):
        self.path = path
        self.reason = reason
        super().__init__(
            f"anchor-candidates sidecar at {path} exists on disk but is "
            f"not valid/readable: {reason}"
        )


def load_anchor_candidates_sidecar_strict(path: "Path") -> dict | None:
    """Load an anchor-candidates sidecar with strict present-but-broken
    semantics. Returns the parsed dict, or None when the file does not
    exist on disk. Raises ``SidecarLoadError`` when the file exists but
    cannot be parsed.

    This is the canonical sidecar loader for every consumer in the
    pipeline (test-specialist.py, v2_loader.py, lead_prep.py,
    build_synthesizer_emission_fallback.py).
    Centralizing the "missing vs broken" decision in one helper prevents
    the fail-open class Codex caught from re-emerging in a new caller.
    """
    if not path.exists():
        return None
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as e:
        raise SidecarLoadError(path, f"OSError reading file: {e}") from e
    try:
        loaded = json.loads(raw)
    except json.JSONDecodeError as e:
        raise SidecarLoadError(path, f"invalid JSON: {e}") from e
    if not isinstance(loaded, dict):
        raise SidecarLoadError(
            path, f"top-level JSON value is {type(loaded).__name__}, not object",
        )
    return loaded


class CandidateResolutionError(Exception):
    """Raised when an observed_anchor.candidate_id can't be resolved
    through the anchor-candidates sidecar's candidate_to_e_index map.

    Carries enough context for the caller (lead orchestration or the
    test harness) to either bounce the finding back to the specialist
    or fall through to a degraded-mode resolution.
    """

    def __init__(self, candidate_id: str, finding_ref: str, available: list[str]):
        self.candidate_id = candidate_id
        self.finding_ref = finding_ref
        self.available_sample = sorted(available)[:10]
        super().__init__(
            f"observed_anchor.candidate_id={candidate_id!r} "
            f"in finding {finding_ref} not found in anchor-candidates "
            f"sidecar candidate_to_e_index map. "
            f"Sample of available IDs: {self.available_sample}"
        )


def resolve_candidate_ids_in_emission(
    emission: dict,
    sidecar: dict | None,
    *,
    strict: bool = False,
) -> tuple[dict, list[dict]]:
    """Substitute candidate_id references with canonical baton_index.

    For each finding in ``emission.findings[]`` whose
    ``visual_evidence.observed_anchor.candidate_id`` is set:
      * Look up the candidate_id in
        ``sidecar.candidate_to_e_index``.
      * If found AND the finding's ``element.baton_index`` is empty or
        ``"absent"``, substitute the resolved e_index into BOTH
        ``element.baton_index`` and
        ``visual_evidence.observed_anchor.baton_index``.
      * If the finding already has a non-absent baton_index, leave it
        unchanged (the specialist's explicit baton_index wins; the
        candidate_id is treated as supplementary metadata).
      * If the candidate_id is NOT found:
          - ``strict=True``: raise ``CandidateResolutionError`` for the
            first unresolvable id.
          - ``strict=False`` (default): record a resolution log entry
            and leave the finding's baton_index unchanged. Caller can
            decide whether to bounce, fall through, or accept.

    Returns ``(new_emission, resolution_log)``:
      * ``new_emission`` is a SHALLOW-NEW dict with the substituted
        findings; original emission untouched.
      * ``resolution_log`` is a list of ``{f_ref, candidate_id, action,
        resolved_to}`` dicts. ``action`` is one of:
        ``"substituted"``, ``"already_resolved"`` (finding had explicit
        baton_index that we kept), ``"unresolved"`` (candidate_id not
        in sidecar), ``"no_candidate_id"`` (no observed_anchor.candidate_id
        present — finding skipped).

    When ``sidecar`` is None (no anchor-candidates file present for
    the device), every finding skips with ``action="no_sidecar"``. The
    function is idempotent: running it twice produces the same output.
    """
    if sidecar is None:
        log = [{"action": "no_sidecar"} for _ in emission.get("findings") or []]
        return (emission, log)

    candidate_to_e = sidecar.get("candidate_to_e_index") or {}
    new_findings: list[dict] = []
    log: list[dict] = []
    for f in emission.get("findings") or []:
        f_ref = f"{f.get('cluster', '?')} local_id={f.get('local_id', '?')}"
        ve = f.get("visual_evidence") or {}
        anchor = ve.get("observed_anchor") or {}
        cid = anchor.get("candidate_id")
        if not cid:
            log.append({"f_ref": f_ref, "candidate_id": None, "action": "no_candidate_id"})
            new_findings.append(f)
            continue

        resolved = candidate_to_e.get(cid)
        if resolved is None:
            log.append({
                "f_ref": f_ref, "candidate_id": cid,
                "action": "unresolved",
                "resolved_to": None,
            })
            if strict:
                raise CandidateResolutionError(
                    candidate_id=cid,
                    finding_ref=f_ref,
                    available=list(candidate_to_e.keys()),
                )
            new_findings.append(f)
            continue

        element = f.get("element") or {}
        current_bi = element.get("baton_index", "")
        if current_bi and current_bi != "absent":
            log.append({
                "f_ref": f_ref, "candidate_id": cid,
                "action": "already_resolved",
                "resolved_to": current_bi,
            })
            new_findings.append(f)
            continue

        # Substitute: deep-copy the element + visual_evidence subtrees
        # we mutate so the original emission stays untouched.
        new_element = dict(element)
        new_element["baton_index"] = resolved
        new_ve = dict(ve)
        new_anchor = dict(anchor)
        new_anchor["baton_index"] = resolved
        new_ve["observed_anchor"] = new_anchor
        new_f = dict(f)
        new_f["element"] = new_element
        new_f["visual_evidence"] = new_ve
        new_findings.append(new_f)
        log.append({
            "f_ref": f_ref, "candidate_id": cid,
            "action": "substituted",
            "resolved_to": resolved,
        })

    new_emission = dict(emission)
    new_emission["findings"] = new_findings
    return (new_emission, log)


__all__ = [
    "CandidateResolutionError",
    "EXPECTED_OVERLAY_TEMPLATES",
    "SidecarLoadError",
    "build_anchor_candidates_sidecar",
    "build_candidates",
    "load_anchor_candidates_sidecar_strict",
    "resolve_candidate_ids_in_emission",
]
