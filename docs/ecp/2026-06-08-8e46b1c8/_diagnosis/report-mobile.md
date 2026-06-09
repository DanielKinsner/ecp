# Engagement diagnosis - 2026-06-08-8e46b1c8 (mobile)

**Verdict: DO NOT SHIP - re-capture / review**

- above-fold captured flat/void (50% void rows) with 27 scroll-trigger / 19 lazy / 0 video elements in the DOM - hero likely UNRENDERED
- 21/24 findings have a stage-attributed defect

## Stage attribution (who is accountable)

| count | attribution | owning stage | tune |
|---|---|---|---|
| 6 | DUPLICATE | PLACEMENT | scripts/report/v2_markers.py + scripts/assembly/review_state.py (region findings -> box over the section; de-stack absence/head-meta; drop the -ai duplicate from the render set) |
| 5 | WEAK_ANCHOR | SPECIALIST | contracts/specialist-prompt-v2.md anchor rules (cite the element the claim is actually about; predicates like 'over $X' must anchor to an element that satisfies them, or to the section) |
| 4 | CAPTURE_SUSPECT | ACQUISITION | scripts/acquire_url.py reveal/settle (scroll-trigger + lazy media); re-capture and re-check the screenshot |
| 3 | OK | - | no action |
| 2 | LOW_CONF_PLACEMENT | PLACEMENT | scripts/report/v2_markers.py + scripts/assembly/review_state.py (region findings -> box over the section; de-stack absence/head-meta; drop the -ai duplicate from the render set) |
| 2 | POINT_FOR_REGION | PLACEMENT | scripts/report/v2_markers.py + scripts/assembly/review_state.py (region findings -> box over the section; de-stack absence/head-meta; drop the -ai duplicate from the render set) |
| 2 | STACKED | PLACEMENT | scripts/report/v2_markers.py + scripts/assembly/review_state.py (region findings -> box over the section; de-stack absence/head-meta; drop the -ai duplicate from the render set) |

## Acquisition / capture signals

- DOM render-risk: scroll-trigger=27 animate--=19 lazy-img=19 video=0
- Above-fold void-row fraction: 0.501  (>= 35% + render-risk => capture-suspect=True)
- Above-fold element desert: 0px (largest no-element vertical gap in the first viewport)

## Per-finding accountability  (LOOK AT THE CROP for each non-OK row)

| f_ref | sev | shape/source | anchor (element text) | attribution | reason | crop |
|---|---|---|---|---|---|---|
| category-navigation F-05 | MEDIUM | rect/e_index_lookup | e36 (Shop by Vehicle) | **DUPLICATE** | another marker shares this exact position | crops/mobile-category-navigation_F-05.png |
| category-navigation F-63 | MEDIUM | rect/e_index_lookup | e15 (Performance 


                      IntakesExhaustCoolingDr) | **LOW_CONF_PLACEMENT** | placed via proxy_element (low confidence) - confirm the crop | crops/mobile-category-navigation_F-63.png |
| content-seo F-32 | HIGH | point/proposed_anchor_element | - | **WEAK_ANCHOR** | no concrete element anchor (source=proposed_anchor_element, ve=generated_expected_zone) | crops/mobile-content-seo_F-32.png |
| content-seo F-62 | HIGH | point/proposed_anchor_element | - | **WEAK_ANCHOR** | no concrete element anchor (source=proposed_anchor_element, ve=proxy_element) | crops/mobile-content-seo_F-62.png |
| content-seo F-75 | MEDIUM | point/proposed_anchor_element | - | **WEAK_ANCHOR** | no concrete element anchor (source=proposed_anchor_element, ve=proxy_element) | crops/mobile-content-seo_F-75.png |
| content-seo F-76 | HIGH | rect/e_index_lookup | e23 (card__image motion-reduce object-center
                   o) | **DUPLICATE** | another marker shares this exact position | crops/mobile-content-seo_F-76.png |
| content-seo F-87 | MEDIUM | point/proposed_anchor_section | - | **CAPTURE_SUSPECT** | claims empty/blank region while the above-fold captured flat/void | crops/mobile-content-seo_F-87.png |
| ethics F-16 | MEDIUM | rect/e_index_lookup | e4 (Shop All
                    
                      
      
) | **DUPLICATE** | another marker shares this exact position | crops/mobile-ethics_F-16.png |
| performance-ux F-17 | MEDIUM | rect/e_index_lookup | e23 (card__image motion-reduce object-center
                   o) | **DUPLICATE** | another marker shares this exact position | crops/mobile-performance-ux_F-17.png |
| performance-ux F-18 | MEDIUM | point/proposed_anchor_viewport | - | **POINT_FOR_REGION** | region/banner finding rendered as a single point, not a box over the area | crops/mobile-performance-ux_F-18.png |
| performance-ux F-76 | HIGH | rect/e_index_lookup | e69 (FREE SHIPPING on most orders $75+ — Contiguous US only SHOP ) | **CAPTURE_SUSPECT** | claims empty/blank region while the above-fold captured flat/void | crops/mobile-performance-ux_F-76.png |
| performance-ux F-95 | MEDIUM | rect/e_index_lookup | e84 (Find parts) | **DUPLICATE** | another marker shares this exact position | crops/mobile-performance-ux_F-95.png |
| pricing F-51 | LOW | rect/e_index_lookup | e69 (FREE SHIPPING on most orders $75+ — Contiguous US only SHOP ) | **STACKED** | 2+ markers within 6% on this slide (overlapping circles) | crops/mobile-pricing_F-51.png |
| pricing F-96 | MEDIUM | point/proposed_anchor_element | - | **POINT_FOR_REGION** | region/banner finding rendered as a single point, not a box over the area | crops/mobile-pricing_F-96.png |
| trust-credibility F-15 | MEDIUM | point/proposed_anchor_element | - | **WEAK_ANCHOR** | no concrete element anchor (source=proposed_anchor_element, ve=generated_expected_zone) | crops/mobile-trust-credibility_F-15.png |
| trust-credibility F-27 | MEDIUM | point/proposed_anchor_element | - | **WEAK_ANCHOR** | no concrete element anchor (source=proposed_anchor_element, ve=generated_expected_zone) | crops/mobile-trust-credibility_F-27.png |
| trust-credibility F-28 | MEDIUM | rect/e_index_lookup | e134 (PayPal) | **LOW_CONF_PLACEMENT** | placed via proxy_element (low confidence) - confirm the crop | crops/mobile-trust-credibility_F-28.png |
| visual-cta F-11 | HIGH | point/proposed_anchor_element | - | **CAPTURE_SUSPECT** | claims empty/blank region while the above-fold captured flat/void | crops/mobile-visual-cta_F-11.png |
| visual-cta F-12 | MEDIUM | rect/e_index_lookup | e84 (Find parts) | **DUPLICATE** | another marker shares this exact position | crops/mobile-visual-cta_F-12.png |
| visual-cta F-46 | LOW | rect/e_index_lookup | e69 (FREE SHIPPING on most orders $75+ — Contiguous US only SHOP ) | **STACKED** | 2+ markers within 6% on this slide (overlapping circles) | crops/mobile-visual-cta_F-46.png |
| visual-cta F-67 | MEDIUM | point/proposed_anchor_viewport | - | **CAPTURE_SUSPECT** | claims empty/blank region while the above-fold captured flat/void | crops/mobile-visual-cta_F-67.png |
| category-navigation F-50 | HIGH | rect/e_index_lookup | e105 (header__icon header__icon--menu header__icon--summary link f) | **OK** | exact element anchor (e105, exact_element/high) | crops/mobile-category-navigation_F-50.png |
| pricing F-43 | MEDIUM | rect/e_index_lookup | e89 (Regular price
          
            From $135.99
          ) | **OK** | exact element anchor (e89, exact_element/high) | crops/mobile-pricing_F-43.png |
| trust-credibility F-13 | HIGH | rect/e_index_lookup | e90 (5.0 /
                    5.0
                

            ) | **OK** | exact element anchor (e90, exact_element/high) | crops/mobile-trust-credibility_F-13.png |

## How to use this

1. Read the **Verdict**. If DO NOT SHIP, the above-fold likely didn't render - re-capture before trusting any above-fold finding.
2. Open the crops in `_diagnosis/crops/` for every non-OK row and confirm with your eyes (this is the visual assessment the pipeline can't do deterministically).
3. Group the defects by **owning stage** and tune that stage only:
   - **ACQUISITION** -> scripts/acquire_url.py reveal/settle (scroll-trigger + lazy media); re-capture and re-check the screenshot
   - **SPECIALIST** -> contracts/specialist-prompt-v2.md anchor rules (cite the element the claim is actually about; predicates like 'over $X' must anchor to an element that satisfies them, or to the section)
   - **PLACEMENT** -> scripts/report/v2_markers.py + scripts/assembly/review_state.py (region findings -> box over the section; de-stack absence/head-meta; drop the -ai duplicate from the render set)
4. Re-run the audit, re-run this tool, and confirm the defect counts drop. That loop is the accountability - a stage is 'fixed' when its attributed count goes to ~0.
