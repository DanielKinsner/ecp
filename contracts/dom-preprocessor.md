# DOM preprocessor

Algorithm for reading the full DOM once per device and writing per-cluster context slices, so each auditor receives only its relevant DOM sections instead of the full page.

**Why this file exists:** The DOM preprocessing algorithm is reusable across any skill that dispatches cluster auditors against a captured DOM (audit, compare, quick-scan). Extracting it from the audit skill makes it a single canonical source for the slicing logic, cluster-context file format, empty-slice pruning rules, and token savings rationale.

**Read this file when:** you are the coordinator (lead) of any `/ecp:*` skill that needs to slice a full DOM into per-cluster context files before dispatching auditor teammates.

---

## When to run

After baton validation passes and baton normalization completes, before spawning cluster auditors. Runs once per device.

## When to skip

- File path mode (`source_mode: "file"`) — content passed directly to auditors
- Description mode (`source_mode: "description"`) — no DOM to slice
- Screenshot-only mode (`source_mode: "screenshot"`) — no DOM to slice

## Process per device

1. **Read the full DOM file** — `dom.html` (laptop/desktop) or `dom-mobile.html` (mobile). ONE Read call.
2. **Read the baton** — `baton.json` or `baton-{device}.json`. Use `sections[]` with their `clusters` arrays and `elements[]` with their absolute `y` coordinates.
3. **For each resolved cluster in `clusters_used`:**
   a. Collect baton `sections[]` where the `clusters` array includes this cluster slug.
   b. Use baton `elements[]` (which have absolute y coordinates from `getBoundingClientRect`) to identify which DOM subtrees fall within each section's `scrollY..scrollY+height` range. Match elements to DOM nodes by `selector`/`tag`/`class` from the elements array.
   c. Extract those DOM subtrees from the full DOM.
   d. Also extract page-level elements that CODE-source auditors need regardless of scroll position: `<head>` content (meta tags, schema markup, canonical links, title tag), `<meta name="viewport">`, any `<script type="application/ld+json">` blocks.
   e. Write `cluster-context-{cluster}-{device}.json` to the engagement directory.

4. **Cluster-context file format:**

```json
{
  "cluster": "pricing",
  "device": "mobile",
  "sections": [
    {
      "label": "Product title, ratings, price and add to cart CTA",
      "scrollY": 1100,
      "height": 702,
      "dom_slice": "<div class='product-price-row'>...</div>..."
    }
  ],
  "page_head": "<head>...meta, schema, canonical, title...</head>",
  "elements": [
    {"selector": "[class*=\"price\"]", "tag": "div", "text": "$999.00", "x": 45, "y": 3229, "width": 1080, "height": 230}
  ],
  "styles": {"bg": "#ffffff", "text": "#666666", "cta_bg": "#505050", "link": "#868686"}
}
```

5. **Global sections — header, footer, and announcement bar are included in EVERY cluster's context.**
   Baton sections whose `label` matches any of: `header`, `footer`, `announcement`, `nav` (case-insensitive partial match), OR whose `scrollY` is 0 (above-fold hero/header region), are treated as **global sections**. They are included in every resolved cluster's context file regardless of whether the section's `clusters` array includes that cluster.

   **Why:** Page-wide elements contain information relevant to all clusters — free-shipping thresholds (pricing), trust badges (trust-credibility), navigation structure (category-navigation), meta content (content-seo), mobile nav patterns (performance-ux). Filtering these out based on the acquirer's section-to-cluster tagging causes false findings: a pricing auditor that can't see the free-shipping banner in the announcement bar will flag "no shipping info visible" even though it's at the top of every page.

   **Implementation:** After step 3a (collect sections where `clusters` array includes this cluster slug), also collect any section matching the global-section criteria above. Deduplicate by `scrollY` so a section isn't included twice if it's both globally matched and cluster-matched.

6. **Sections tagged to multiple clusters** appear in all relevant slices. A section tagged `["visual-cta", "pricing"]` produces DOM content in both `cluster-context-visual-cta-{device}.json` and `cluster-context-pricing-{device}.json`. This duplication across slices is acceptable — it's still far less than every auditor reading the full DOM.

7. **Empty slice handling:** If no baton sections route to a cluster after scope resolution (e.g., `post-purchase` on a product page with no post-purchase content), the lead **skips dispatching that auditor entirely**. Log to `audit-trace.log`: "Skipped {cluster} — no DOM sections routed to this cluster." Decrement `expected_auditor_count` accordingly. Do NOT spawn an auditor with an empty context file.

8. **Fallback for missing section clusters:** When baton sections lack `clusters` arrays, use the keyword fallback rules from the coordinator's `<phase_audit>` "Fallback (malformed baton)" to infer cluster assignment before slicing. Log which sections used fallback: "Section '{label}' cluster assignment inferred via keyword fallback."

## Recommended implementation: Python html.parser

The lead's DOM preprocessor should use Python's built-in `html.parser` (standard library, no pip install needed) rather than regex for section extraction. Regex-based extraction with patterns like `<section[^>]*class="[^"]*shopify-section[^"]*"[^>]*>.*?</section>` fails on:
- Nested `<section>` elements (regex greedily matches the wrong closing tag)
- CSS `background-image` declarations (hero images served as backgrounds are invisible to the slice)
- Liquid `{% include %}` content injected without a `<section>` wrapper
- Self-closing tags or HTML fragments that break regex assumptions

**Recommended approach:**

```python
from html.parser import HTMLParser

class SectionExtractor(HTMLParser):
    """Extract top-level Shopify sections from rendered DOM."""
    
    def __init__(self):
        super().__init__()
        self.sections = {}        # label -> html_content
        self.current_section = None
        self.depth = 0
        self.buffer = []
        self.header_html = ""
        self.footer_html = ""
        self._in_header = False
        self._in_footer = False
        self._header_depth = 0
        self._footer_depth = 0
        self._head_content = ""
        self._in_head = False
    
    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        classes = attrs_dict.get("class", "")
        raw = self.get_starttag_text() or f"<{tag}>"
        
        # Track <head>
        if tag == "head":
            self._in_head = True
            self._head_content = raw
            return
        if self._in_head:
            self._head_content += raw
            return
        
        # Track <header> / <footer>
        if tag == "header" and not self._in_header:
            self._in_header = True
            self._header_depth = 1
            self.header_html = raw
            return
        if self._in_header:
            self._header_depth += 1
            self.header_html += raw
            return
        if tag == "footer" and not self._in_footer:
            self._in_footer = True
            self._footer_depth = 1
            self.footer_html = raw
            return
        if self._in_footer:
            self._footer_depth += 1
            self.footer_html += raw
            return
        
        # Track shopify-section elements
        if tag == "section" and "shopify-section" in classes:
            label = "unknown"
            for kw, name in [
                ("slideshow", "hero"), ("hero", "hero"), ("banner", "hero"),
                ("image-banner", "hero"), ("multicolumn", "category_nav"),
                ("featured", "featured_collection"), ("collection", "featured_collection"),
                ("newsletter", "newsletter"), ("rich-text", "richtext"),
            ]:
                if kw in classes.lower():
                    label = name
                    break
            self.current_section = label
            self.depth = 1
            self.buffer = [raw]
            return
        
        if self.current_section:
            self.depth += 1 if tag in (
                "section", "div", "article", "main", "aside", "nav",
                "header", "footer", "form", "ul", "ol", "table",
                "details", "dialog", "fieldset", "figure"
            ) else 0
            self.buffer.append(raw)
    
    def handle_endtag(self, tag):
        if self._in_head and tag == "head":
            self._in_head = False
            self._head_content += f"</{tag}>"
            return
        if self._in_head:
            self._head_content += f"</{tag}>"
            return
        if self._in_header:
            self._header_depth -= 1
            self.header_html += f"</{tag}>"
            if self._header_depth <= 0:
                self._in_header = False
            return
        if self._in_footer:
            self._footer_depth -= 1
            self.footer_html += f"</{tag}>"
            if self._footer_depth <= 0:
                self._in_footer = False
            return
        
        if self.current_section:
            self.buffer.append(f"</{tag}>")
            if tag == "section":
                self.depth -= 1
                if self.depth <= 0:
                    self.sections[self.current_section] = "".join(self.buffer)
                    self.current_section = None
                    self.buffer = []
    
    def handle_data(self, data):
        if self._in_head:
            self._head_content += data
        elif self._in_header:
            self.header_html += data
        elif self._in_footer:
            self.footer_html += data
        elif self.current_section:
            self.buffer.append(data)
```

**Usage by the lead:**

```python
extractor = SectionExtractor()
extractor.feed(dom_html)

# extractor.sections -> {"hero": "...", "category_nav": "...", ...}
# extractor.header_html -> full <header>...</header>
# extractor.footer_html -> full <footer>...</footer>
# extractor._head_content -> full <head>...</head>
```

This replaces the regex approach and correctly handles nested elements, self-closing tags, and deep Shopify theme structures.

**Fallback:** If `html.parser` produces empty results (malformed HTML), fall back to the regex approach documented in the original algorithm above.

## Token savings

A full DOM is typically 200-500K tokens. Per-cluster slices are typically 20-80K tokens each. With 6 clusters, this reduces total DOM input from ~1.2-3M tokens (6 x full DOM) to ~120-480K tokens (6 x slice) — a 60-80% reduction in per-auditor DOM input.
