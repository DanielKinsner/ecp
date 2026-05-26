"""Shared constants and small utility functions."""


# --- Constants (canonical design tokens — this script is the single source
#     of truth for every ECP visual report as of Round 10.5) ---

SEVERITY_COLORS = {
    "critical": "#dc2626",
    "high": "#ef4444",
    "medium": "#eab308",
    "low": "#22c55e",
    "pass": "#6b7280",
}

SEVERITY_LABELS = {
    "critical": "Critical",
    "high": "High",
    "medium": "Medium",
    "low": "Low",
}


# --- Cluster metadata (10-cluster v5.0 system + legacy v4.x aliases) ---

CLUSTER_LABELS = {
    # Client-facing labels — describe outcomes/experiences, not engineering taxonomy.
    # Internal slugs (kept in cluster files, meta.json, --focus flag) stay as-is;
    # only the rendered display label is humanized.
    "visual-cta": "Headlines & Buttons",
    "trust-credibility": "Trust & Credibility",
    "pricing": "Price & Offers",
    "checkout-flows": "Checkout Experience",
    "performance-ux": "Performance & UX",
    "product-media": "Product Photos & Video",
    "category-navigation": "Browse & Search",
    "content-seo": "Search Findability",
    "post-purchase": "After Purchase",
    "audience": "Audience Fit",
    # Legacy v4.x names — accepted for old engagements (mapped to v5.0 equivalents)
    "trust-conversion": "Trust & Credibility",
    "context-platform": "Performance & UX",
    "audience-journey": "Audience Fit",
    # Legacy v5.0/v1.0 name — renamed to performance-ux in v1.1 because the cluster
    # contains 4 device-agnostic reference files (core-web-vitals, cognitive-load-
    # management, page-performance-psychology, media-performance-optimization) plus
    # mobile-conversion. Old name led users to think it only ran on mobile.
    "mobile-performance": "Performance & UX",
}

CLUSTER_COLORS = {
    "visual-cta": "#f59e0b",
    "trust-credibility": "#22c55e",
    "pricing": "#ef4444",
    "checkout-flows": "#06b6d4",
    "performance-ux": "#8b5cf6",
    "product-media": "#ec4899",
    "category-navigation": "#14b8a6",
    "content-seo": "#84cc16",
    "post-purchase": "#f97316",
    "audience": "#3b82f6",
    # Legacy v4.x colors — match the new equivalents
    "trust-conversion": "#22c55e",
    "context-platform": "#8b5cf6",
    "audience-journey": "#3b82f6",
    # Legacy v5.0/v1.0 slug — same color family, renamed in v1.1
    "mobile-performance": "#8b5cf6",
}

CLUSTER_TAB_ORDER = [
    "visual-cta",
    "trust-credibility",
    "pricing",
    "checkout-flows",
    "performance-ux",
    "product-media",
    "category-navigation",
    "content-seo",
    "post-purchase",
    "audience",
    # Legacy fallbacks
    "mobile-performance",
    "trust-conversion",
    "context-platform",
    "audience-journey",
]


# --- SVG Icons ---

SVG_LIGHTBULB = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"/></svg>'

SVG_INFO = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4M12 8h.01"/></svg>'

SVG_TREND_UP = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M23 6l-9.5 9.5-5-5L1 18"/><path d="M17 6h6v6"/></svg>'

SVG_CHECK = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 11-5.93-9.14"/><path d="M22 4L12 14.01l-3-3"/></svg>'

SVG_X = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M15 9l-6 6M9 9l6 6"/></svg>'

SVG_SQUARE = '<svg viewBox="0 0 24 24" fill="currentColor"><rect x="7" y="7" width="10" height="10" rx="2"/></svg>'

SVG_CHEVRON_LEFT = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M15 18l-6-6 6-6"/></svg>'

SVG_CHEVRON_RIGHT = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 18l6-6-6-6"/></svg>'


# --- Utility Functions ---

def escape_html(text):
    """HTML-escape text content."""
    if not text:
        return ""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
    )


def slug_to_title(slug):
    """Convert a canonical slug to a display title."""
    return slug.replace("-", " ").title()


def aspect_ratio_value(width, height, fallback="16 / 9"):
    """Return a CSS aspect-ratio string from numeric dimensions."""
    try:
        width = int(width or 0)
        height = int(height or 0)
    except (TypeError, ValueError):
        return fallback

    if width > 0 and height > 0:
        return f"{width} / {height}"

    return fallback


def get_severity_class(priority):
    """Map priority string to severity class name."""
    return (priority or "medium").lower()


def get_device_frame_css(device):
    """Return CSS for the device frame.

    Subtle frame: thin border, rounded corners, uppercase corner label. No
    monitor stands, no phone notches, no window-control dots — those chromed
    the screenshot visually but stole vertical space from the actual content
    (Dan's 2026-04-14 feedback). Label in the top-right reads
    "DESKTOP" / "MOBILE" / "LAPTOP" so the user still has instant
    disambiguation on which device they're looking at.

    The ``.device-base``, ``.device-stand``, and ``.device-stand-base`` class
    hooks emitted by ``html_structure.py`` are kept in the DOM but collapsed
    to ``display: none`` so the HTML contract stays stable.
    """
    label = {
        "mobile": "MOBILE",
        "laptop": "LAPTOP",
    }.get(device, "DESKTOP")
    max_width_rule = "max-width: 430px; margin: 0 auto;" if device == "mobile" else ""
    outer_radius = "1rem" if device == "mobile" else "0.625rem"
    return f"""
/* Device frame — subtle, v1.1 2026-04-14 */
.device-frame {{
  position: relative;
  padding: 1.75rem 0.375rem 0.375rem 0.375rem;
  background: transparent;
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: {outer_radius};
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.02);
  {max_width_rule}
}}
.device-frame::after {{
  content: "{label}";
  position: absolute;
  top: 0.5rem;
  right: 0.75rem;
  font: 600 10px/1 ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  letter-spacing: 0.12em;
  color: rgba(255, 255, 255, 0.32);
  pointer-events: none;
}}
.device-frame::before {{
  content: "";
  position: absolute;
  top: 0.625rem;
  left: 0.75rem;
  width: 0.375rem;
  height: 0.375rem;
  background: rgba(255, 255, 255, 0.14);
  border-radius: 50%;
}}
.device-base,
.device-stand,
.device-stand-base {{
  display: none;
}}
"""
