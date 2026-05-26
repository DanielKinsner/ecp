---
name: ecp
description: >-
  E-commerce Psychology toolkit for ecommerce pages. Evidence-backed citations
  with credibility tiers (Gold/Silver/Bronze) across pricing, trust, SEO, mobile,
  visual design, content, and checkout domains. Annotated screenshot reports with
  bidirectional scroll-sync, screenshot-only input mode, component-library-enforced
  structural consistency, ethics compliance in every report. Use when the user
  mentions ecommerce optimization, conversion, CRO, or page improvements without
  specifying audit, build, scan, or compare.
disable-model-invocation: false
---

<objective>
Present the E-commerce Psychology engine commands and direct the user to the right one.
For automated callers: skip this router and invoke specific commands directly.
Never invoke another skill from this router. Only present options.
</objective>

<quick_start>
Available commands:

/ecp:audit [url-or-path]           Full audit with plan, review, and build phases
/ecp:build [description]           Build a new ecommerce page from scratch
/ecp:quick-scan [url-or-desc]      Quick scan — one focus area, 3-5 quick wins
/ecp:compare [url] [competitor]    1:1 competitor comparison with gap analysis
/ecp:resume [--engagement-id <id>] List & resume in-progress engagements

Output flags: --visual (generate annotated screenshot report), --no-visual (skip visual report prompt)
Device flags: --device mobile|laptop|desktop or comma pair (e.g., --device mobile,desktop) for two-device mode
Focus flags: --focus cro|seo|pricing|trust|visual|mobile|content|checkout (comma-separated for multiple, default is full cross-domain audit)
Common flags: --auto, --force, --min-priority, --platform
</quick_start>

<instructions>
If $ARGUMENTS contains a URL or file path, suggest: "It looks like you want to audit a page. Run `/ecp:audit $ARGUMENTS` to start."

If $ARGUMENTS contains a description of something to build, suggest: "It sounds like you want to build something new. Run `/ecp:build $ARGUMENTS` to start."

Otherwise, present the command table above and ask: "What would you like to do?"
</instructions>
