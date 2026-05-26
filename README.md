# E-Commerce Psychology (ECP)

![v1.4.1](https://img.shields.io/badge/version-1.4.1-blue) ![Claude Code](https://img.shields.io/badge/Claude_Code-plugin-7c3aed) ![Codex](https://img.shields.io/badge/Codex-skill-10b981) ![Platforms](https://img.shields.io/badge/platforms-Shopify_%7C_Next.js_%7C_OpenCart_%7C_WooCommerce_%7C_any-green)

**One audit. Every insight. Research-backed.**

Point it at any e-commerce page — a URL, your local codebase, a screenshot, or just a description of what you want to build. ECP runs a multi-phase analysis grounded in **945 classified findings across 72 reference files** from Baymard Institute, Nielsen Norman Group, peer-reviewed journals, FTC enforcement actions, and more. Every recommendation cites its source. Every citation is rated by evidence quality. Every phase is checked against an ethics gate built from actual compliance law.

**Not vibes. Not best practices. Actual studies, actual evidence tiers, actual legal compliance.**

---

## Install

### Cursor

Recommended install (mirrors the full runtime + knowledge base into your local Cursor plugins directory):

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\sync-to-cursor.ps1
```

Default target: `C:\Users\%USERNAME%\.cursor\plugins\local\ecp-cursor`

Then restart Cursor.

**Slash commands** (after install): **`/ecp-cursor`**, **`/ecp-cursor-quick-scan`**, **`/ecp-cursor-audit`**, … — see `commands/ecp-cursor*.md`. (Claude Code uses **`/ecp:`** commands such as `/ecp:audit`; Cursor uses the **`ecp-cursor-`** prefix so they stay distinct.) **Subagent roles** (Claude “Agent Teams” replacement): `agents/ecp-orchestrator.md` + `ecp-cluster-auditor.md` (≤4 refs per cluster run) + synthesizer + reviewer. **Annotated HTML reports:** `ecp_run_visual_reports.py` after fenced `FINDING` blocks in `quick-scan.md` or `audit.md`.

Runtime helpers for Cursor mode live in `.cursor-plugin/scripts/`:

- `validate_meta.py`
- `infer_engagement_state.py`
- `run_visual_report.py`

URL bootstrapping for live pages:

- `scripts/cursor_bootstrap_url.py` (requires `agent-browser`; see the `agent-browser` section below)

### Claude Code

ECP uses Claude Code's experimental Agent Teams feature for the `audit`, `build`, `compare`, and `resume` pipelines. You **must** enable it in `~/.claude/settings.json` before running any ECP command other than `/ecp:quick-scan`:

```json
{
  "env": {
    "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"
  }
}
```

Then install the plugin:

```bash
claude plugin marketplace add Dannytownkins/ecommerce-conversion-psychology
claude plugin install ecp@ecommerce-conversion-psychology
```

Restart Claude Code. The `/ecp` commands become available immediately. ECP fails fast with a clear error if the env var is missing — quick-scan is the one command that runs without teams.

### Recommended: install `agent-browser` for full URL support

```bash
npm install -g agent-browser
agent-browser install
```

Without `agent-browser`, ECP still works — when you give it a URL, it falls back to WebFetch mode and gives you a CODE-only audit from raw page source. You'll see a prompt explaining the degraded mode before it proceeds.

**With `agent-browser`, you get:** full screenshot capture at real viewports, rendered DOM extraction (post-hydration for SPAs), element coordinate mapping for precise visual-report hotspot placement, **dual-device capture** (e.g. laptop + mobile in one engagement via `--both` in the Cursor bootstrap, or parallel named sessions in the full `acquire.md` flow), and click-to-spotlight finding hotspots (select a finding from the left rail → its hotspot appears on the screenshot with a callout card). Highly recommended for anyone auditing live URLs.

**Cursor quick-start:** `python scripts/cursor_bootstrap_url.py --url "https://…"` (default **desktop** 1920×1080; `--device laptop` for 1440×900) materializes a first-pass `docs/ecp/<id>/` folder from a live URL, including a report-oriented baton (desktop/laptop: `baton.json` + `dom.html`; mobile: `baton-mobile.json` + `dom-mobile.html`), **unique descriptive section names** in `sections[]` / `screenshots[]` (headings + landmark-based scenes, deduped per acquire-style labeling), and multi-screenshot evidence. Use `--both` for **desktop + mobile** in the same folder. Add `--hybrid` for fast-first capture with one automatic stricter rerun when quality gates fail. The full Claude `workflows/acquire.md` run remains the most thorough, but this gets Cursor workflows unblocked with compatible artifacts.

**File path inputs, pasted code, screenshots, and description inputs don't need `agent-browser`** — those modes skip the browser entirely.

### Codex

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\sync-to-codex.ps1
```

Default target: `C:\Users\%USERNAME%\.codex\skills\ecp-codex`. Use the Codex skill as `$ecp-codex`.

If you still have an older install at `C:\Users\%USERNAME%\.codex\skills\ecommerce-conversion-psychology`, remove it after syncing so Codex does not show two ECP skills.

---

## Commands

Every command works with URLs, file paths, screenshots, or descriptions. You pick the action — the engine brings the right knowledge.

| Command | What it does |
|---------|-------------|
| `/ecp:audit [target]` | Full audit → plan → review → build relay. Scope selector lets you choose breadth: focused (1 cluster), standard (3-4), all clusters, or custom. |
| `/ecp:quick-scan [target]` | 3–5 high-impact wins. Fast, focused, actionable. |
| `/ecp:build [source]` | Build or rewrite from your codebase or a description. Changes go into your actual files. |
| `/ecp:compare [a] [b]` | Head-to-head competitor analysis with gap scoring. |
| `/ecp:resume [id]` | Pick up any previous engagement from where you left off. |

### Input modes — works for every type of user

| You have... | What happens | Works with |
|-------------|-------------|------------|
| **A URL** | Screenshots, DOM extraction, element coordinate mapping — full visual + code analysis | `audit`, `build`, `compare`, `quick-scan`, `resume` |
| **A codebase / file path** | Source code analysis → findings → code changes written directly into your files | `audit`, `build`, `compare`, `quick-scan` |
| **A screenshot** | Drop a PNG/JPEG/WebP — visual-only analysis, no code needed | `audit`, `quick-scan` |
| **A description** | Plans and builds a conversion-optimized page from scratch | `build`, `quick-scan` |
| **A past engagement** | Resume with `/ecp:resume --engagement-id {id}` — full progress memory across v4, v5, and v1.x engagements | `resume` |

**Compare mode is URL + file path only.** Screenshot and description inputs aren't supported by `/ecp:compare` — the comparison requires real page data from both sides. For screenshot-only or description-based work, use `/ecp:audit` or `/ecp:quick-scan`.

### Useful flags

| Flag | What it does |
|------|-------------|
| `--device mobile,desktop` | Single device or comma-pair (e.g., `mobile,laptop`). Viewports: mobile 390×844 3x DPR, laptop 1440×900, desktop 1920×1080. |
| `--auto` | Run all phases without stopping at checkpoints |
| `--visual` / `--no-visual` | Force-enable or force-skip the annotated visual report |
| `--focus pricing,trust` | Target specific clusters — skips the scope selector entirely. Accepts cluster slugs or domains (`cro`, `seo`, `pricing`, `trust`, `visual`, `mobile`, `content`, `checkout`, `all`) |
| `--deep` | Route cluster auditors + builder to **opus** instead of the default **sonnet**. Use for complex pages or client-facing runs where quality matters more than cost. |
| `--min-priority high` | Only show HIGH and CRITICAL findings |
| `--platform shopify` | Skip platform detection (`shopify`, `nextjs`, `opencart`, `woocommerce`, `generic`) |
| `--ab-scaffold` | Generate A/B test hypotheses + variant code after planning |
| `--engagement-id {id}` | Target or resume a specific past engagement |

---

## What makes this different

### Evidence tiers — not all research is equal

Every finding is classified by the quality of its source:

| Tier | What qualifies | Examples |
|------|---------------|----------|
| 🥇 **Gold** | Peer-reviewed research, RCTs, meta-analyses | Baymard Institute, NN/g, PMC/NIH, ACM CHI, USENIX |
| 🥈 **Silver** | Enterprise research, documented methodology, large-N A/B tests | CXL Institute, Stripe, Forrester, Google Developers |
| 🥉 **Bronze** | Industry commentary, vendor blogs, expert consensus | HubSpot, VWO, Optimizely, Neil Patel |

When findings from different domains conflict — like pricing psychology suggesting one thing and CTA research suggesting another — the tier system tells you which evidence to trust. Gold outranks Silver outranks Bronze. Every citation includes a clickable URL resolved at render time from `citations/sources.md`, so you can verify the source yourself.

### Ethics gate — three states, not a binary

Non-negotiable rules checked at every phase. Not a suggestion layer — a hard gate backed by 27 regulations with canonical source URLs so you can read the actual law yourself. Based on:

- **EU Digital Services Act (Art 25)** — up to 6% global turnover
- **EU AI Act (Feb 2025)** — up to 7% global turnover
- **FTC Fake Reviews Rule (Oct 2024)** — up to $53K per violation
- **FTC v. Amazon ($2.5B, Sep 2025)** — largest dark patterns settlement in history
- **CA SB-478** (honest pricing), **SB-1001** (bot disclosure), **SB-243** (AI chatbot disclosure)
- **GDPR Art 22, CCPA/CPRA ADMT** (Jan 2026)
- **COPPA** (children's privacy), **ADA Title III + EAA** (web accessibility), **Lanham Act § 43(a)** (false advertising in metadata), **CA ARL / AB-2863** (subscription cancel parity, Jul 2025), **EU ePrivacy Art 5(3)** (cookie consent timing), **EU–US Data Privacy Framework** (cross-border transfer)

Three output states ensure findings match their actual legal weight:

| State | Severity | Meaning |
|-------|----------|---------|
| **BLOCK** | CRITICAL | Currently violating a specific regulation. Cite the exact clause + source URL. |
| **ADJACENT** | MEDIUM | Not currently illegal, but one change away from a violation. Strongly recommended. |
| **CLEAR** | — | No ethics concerns found. |

Every BLOCK and ADJACENT finding links to the official regulation text. Before firing CRITICAL, auditors must pass a 3-question applicability self-check: does this regulation actually prohibit what I'm seeing? Would the penalty be enforceable? Can I cite the specific clause? If any answer is uncertain → ADJACENT, not BLOCK. A false legal accusation is worse than a missed finding.

### Multi-phase team relay — not a single-pass linter

```
/ecp:audit       Audit → Checkpoint → Plan → Checkpoint → Review → Checkpoint → Build
/ecp:build       Intake → Plan → Checkpoint → Review → Checkpoint → Build
/ecp:quick-scan  Audit → Results
/ecp:compare     Audit Both → Compare → Results
```

ECP now uses a **hybrid runtime**. Cluster specialists still run where coordination helps; mechanical or one-shot roles such as acquisition, synthesis, planning, review, and build can run as scoped subagents depending on the host runtime. A baton file passes structured findings between phases so nothing gets lost to compaction. The reviewer actively challenges vague recommendations before any code gets written. Checkpoints let you stop, go back, export reports, or scaffold A/B tests at any pause.

**Cost control is explicit.** Cluster auditors and the builder run on **sonnet** by default (mechanical coverage work); the lead, planner, and reviewer stay on **opus** (synthesis + quality gate). Pass `--deep` to route everything to opus when you need the extra depth.

### Priority Path — the action plan, not the checklist

Every audit report **opens on the Priority Path tab**: 3–5 action stories that consolidate the highest-leverage findings across clusters. Each story names the fix, the underlying findings it resolves, the expected leverage, and the reference URLs. Tackle these first; everything else can wait. Priority Path is the primary user-facing artifact — By Cluster and Ethics tabs are reference material for when you want to drill down.

### Visual reports (v1.0 app-shell redesign)

Self-contained single-file dark-mode HTML reports with a three-panel app shell:

| Panel | What lives there |
|---|---|
| **Left rail** | Three tabs — **Priority Path** (opens here by default), **By Cluster** (collapsible cards with per-cluster `VC-01`, `TC-03`-style IDs), **Ethics** (always-visible tab with BLOCK / ADJACENT count badge). |
| **Center stage** | Empty by default. On selection, shows the screenshot at real viewport aspect + a single severity-colored hotspot zone outlining the finding's element, with an animated dark-mode callout card pointing at it from the side. |
| **Right rail** | Selected finding's full detail — element selector, observation, recommendation, research source with tier badge and clickable URL, ethics banner when applicable, Skip / Add-to-brief actions. |

**Work the report, don't scroll it.** Click findings to see them spotlighted; check the boxes on the ones you want to act on; hit **Export Brief** to copy them out as a bulleted list or as a verbatim markdown mirror of the underlying audit.md. The brief persists in `localStorage` so refreshing doesn't lose your selections.

**Key visual contracts:**

- **Cluster chips** show the **worst** severity present, not the plurality — a cluster with 3 HIGH + 4 MEDIUM displays `3 HIGH` (not `4 MEDIUM` hiding the HIGHs).
- **Header ethics pill** is always visible and state-colored: `ETHICS: PASS` (green ✓), `ETHICS: ADVISORY (N)` (amber ⚠), `ETHICS: BLOCK` (red ✗ with outer glow). Clicking it jumps to the Ethics tab.
- **Hotspot zones** use real `getBoundingClientRect()` coordinates from the acquired DOM — pixel-accurate to the rendered page.
- **Cluster-scoped IDs** (`VC-01`, `TC-03`, `PR-05`) make every finding uniquely addressable across the report, across reruns, and inside Slack/PR discussions.
- **Safe JSON embedding.** The inline runtime escapes every `</` in JSON payloads as `<\/` so findings that cite HTML fragments (Speculation Rules, `<script>` markup) can't close the script tag and silently truncate the runtime. Regression-tested.
- **CSP-safe:** `default-src 'none'`, `script-src 'unsafe-inline'`, `style-src 'unsafe-inline'`, `img-src data:`, `font-src data:`. No external deps.

Rendered by `scripts/generate-report.py` — the single canonical render path for every ECP skill.

### Platform-aware implementations

| Platform | What you get |
|----------|-------------|
| **Shopify** | First-class: Liquid patterns, OS 2.0 section schemas, Shop Pay, Checkout Extensions |
| **Next.js** | First-class: App Router, RSC boundaries, Server Actions, middleware A/B testing |
| **WooCommerce** | First-class: classic-hooks vs `render_block` split, HPOS-aware, Cart/Checkout Blocks |
| **OpenCart** | Auto-detected via `catalog/view/`, URL patterns, meta generator. Uses generic e-commerce psychology principles. |
| **Any platform** | Universal conversion psychology — works with anything |

---

## What it knows

ECP ships 72 reference files with 945 classified findings, organized into **10 domain clusters** that route automatically based on page type:

1. **Visual & CTA** — CTA design, color, eye tracking, hero sections, headlines, page length
2. **Trust & Credibility** — trust signals, social proof, E-E-A-T, reviews, UGC, accessibility
3. **Pricing** — charm pricing, anchoring, bundles, discount framing, BNPL, scarcity, competitive positioning
4. **Checkout & Flows** — checkout optimization, biometric/express checkout, abandoned cart, cookie consent
5. **Performance & UX** — page performance (Core Web Vitals, media delivery), cognitive load, plus mobile-specific UX (touch targets, thumb zones, sticky bars)
6. **Product Media** — gallery UX, image quantity, thumbnails, video, AR/3D, color accuracy
7. **Category & Navigation** — search/filter, grid layout, merchandising, pagination, sorting, zero-results
8. **Content & SEO** — canonical, schema markup, image SEO, URL structure, content freshness, AI search
9. **Post-Purchase** — order confirmation, buyer's remorse, loyalty programs, referral programs
10. **Audience** — personalization, cross-cultural considerations, social commerce

Each cluster groups a focused set of reference files. The scope selector defaults to **standard** mode (3-4 highest-impact clusters per page type); choose **all clusters** for full coverage or **focused** for a single cluster deep-dive. `--focus` overrides the selector entirely. See [ARCHITECTURE.md](ARCHITECTURE.md#cluster-routing) for the full page-type routing table and domain value mapping.

---

## Roadmap

The reference library is expanding. Future rounds add deeper coverage on landing page psychology, post-purchase retention, advanced personalization, and AI search optimization. The commands don't change — the engine just gets smarter.

*The product grows by adding knowledge, not features.*

---

## Deep dive

Want to understand how the team relay protocol, baton schema, engagement directory, forensic assertion canary, render pipeline, and security guarantees work under the hood? See **[ARCHITECTURE.md](ARCHITECTURE.md)**.

---

## Author

Built by [Daniel Kinsner](https://github.com/Dannytownkins).

## License

[MIT](LICENSE)
