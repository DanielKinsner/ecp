---
name: ecp
description: >-
  E-commerce conversion-psychology audit for a single ecommerce page from a URL.
  Evidence-tiered findings (Gold/Silver/Bronze citations) across pricing, trust,
  SEO, mobile, performance, visual design, content, and checkout, a prioritized
  Priority Path, and an annotated visual report with an editable hotspot tool.
  Ethics gate in every audit. Use when the user mentions ecommerce optimization,
  conversion, CRO, or page improvements.
disable-model-invocation: false
---

<objective>
Present the ECP audit command and direct the user to it.
For automated callers: skip this router and invoke /ecp:audit directly.
Never invoke another skill from this router. Only present the option.
</objective>

<quick_start>
ECP is an audit engine. One command:

/ecp:audit [url]    Audit an ecommerce page — cited findings + Priority Path + annotated visual report

Output flags: --visual (generate annotated visual report), --no-visual (skip the report prompt)
Device flags: --device mobile|laptop|desktop, or a comma pair (e.g., --device mobile,desktop) for two-device mode
Focus flags: --focus cro|seo|pricing|trust|visual|mobile|content|checkout (comma-separated; default is full cross-domain audit)
Common flags: --auto, --deep, --min-priority, --platform, --engagement-id

Build, compare, quick-scan, and resume are out of scope in this build — see product.md.
</quick_start>

<instructions>
If $ARGUMENTS contains a URL, suggest: "Run `/ecp:audit $ARGUMENTS` to start the audit."

Otherwise, present the command above and ask: "What page would you like to audit? Share a URL."
</instructions>
