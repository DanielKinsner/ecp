# Engagement diagnosis - 2026-06-08-8e46b1c8 (desktop)

**Verdict: DO NOT SHIP - re-capture / review**

- above-fold captured flat/void (56% void rows) with 19 scroll-trigger / 19 lazy / 0 video elements in the DOM - hero likely UNRENDERED
- 24/25 findings have a stage-attributed defect

## Stage attribution (who is accountable)

| count | attribution | owning stage | tune |
|---|---|---|---|
| 7 | STACKED | PLACEMENT | scripts/report/v2_markers.py + scripts/assembly/review_state.py (region findings -> box over the section; de-stack absence/head-meta; drop the -ai duplicate from the render set) |
| 6 | CAPTURE_SUSPECT | ACQUISITION | scripts/acquire_url.py reveal/settle (scroll-trigger + lazy media); re-capture and re-check the screenshot |
| 6 | WEAK_ANCHOR | SPECIALIST | contracts/specialist-prompt-v2.md anchor rules (cite the element the claim is actually about; predicates like 'over $X' must anchor to an element that satisfies them, or to the section) |
| 3 | DUPLICATE | PLACEMENT | scripts/report/v2_markers.py + scripts/assembly/review_state.py (region findings -> box over the section; de-stack absence/head-meta; drop the -ai duplicate from the render set) |
| 1 | OK | - | no action |
| 1 | LOW_CONF_PLACEMENT | PLACEMENT | scripts/report/v2_markers.py + scripts/assembly/review_state.py (region findings -> box over the section; de-stack absence/head-meta; drop the -ai duplicate from the render set) |
| 1 | PREDICATE_MISMATCH | SPECIALIST | contracts/specialist-prompt-v2.md anchor rules (cite the element the claim is actually about; predicates like 'over $X' must anchor to an element that satisfies them, or to the section) |

## Acquisition / capture signals

- DOM render-risk: scroll-trigger=19 animate--=19 lazy-img=19 video=0
- Above-fold void-row fraction: 0.555  (>= 35% + render-risk => capture-suspect=True)
- Above-fold element desert: 0px (largest no-element vertical gap in the first viewport)

## Per-finding accountability  (LOOK AT THE CROP for each non-OK row)

| f_ref | sev | shape/source | anchor (element text) | attribution | reason | crop |
|---|---|---|---|---|---|---|
| category-navigation F-46 | MEDIUM | rect/e_index_lookup | e117 (Find parts) | **DUPLICATE** | another marker shares this exact position | crops/desktop-category-navigation_F-46.png |
| category-navigation F-52 | MEDIUM | rect/e_index_lookup | e86 (Select Make
                  
                
            ) | **CAPTURE_SUSPECT** | claims empty/blank region while the above-fold captured flat/void | crops/desktop-category-navigation_F-52.png |
| content-seo F-27 | MEDIUM | rect/e_index_lookup | e35 (card__image motion-reduce object-center
                   o) | **STACKED** | 2+ markers within 6% on this slide (overlapping circles) | crops/desktop-content-seo_F-27.png |
| content-seo F-32 | HIGH | point/proposed_anchor_element | - | **WEAK_ANCHOR** | no concrete element anchor (source=proposed_anchor_element, ve=generated_expected_zone) | crops/desktop-content-seo_F-32.png |
| content-seo F-60 | MEDIUM | point/proposed_anchor_element | - | **WEAK_ANCHOR** | no concrete element anchor (source=proposed_anchor_element, ve=generated_expected_zone) | crops/desktop-content-seo_F-60.png |
| content-seo F-61 | HIGH | point/proposed_anchor_element | - | **WEAK_ANCHOR** | no concrete element anchor (source=proposed_anchor_element, ve=generated_expected_zone) | crops/desktop-content-seo_F-61.png |
| content-seo F-74 | MEDIUM | point/proposed_anchor_element | - | **WEAK_ANCHOR** | no concrete element anchor (source=proposed_anchor_element, ve=generated_expected_zone) | crops/desktop-content-seo_F-74.png |
| ethics F-16 | MEDIUM | rect/e_index_lookup | e4 (Information
                        
  

                   ) | **LOW_CONF_PLACEMENT** | placed via proxy_element (low confidence) - confirm the crop | crops/desktop-ethics_F-16.png |
| performance-ux F-24 | MEDIUM | rect/e_index_lookup | e40 (card__image motion-reduce object-center
                   o) | **STACKED** | 2+ markers within 6% on this slide (overlapping circles) | crops/desktop-performance-ux_F-24.png |
| performance-ux F-37 | HIGH | rect/e_index_lookup | e35 (card__image motion-reduce object-center
                   o) | **CAPTURE_SUSPECT** | claims empty/blank region while the above-fold captured flat/void | crops/desktop-performance-ux_F-37.png |
| performance-ux F-83 | HIGH | rect/e_index_lookup | e88 (Select Year
                  
                
            ) | **CAPTURE_SUSPECT** | claims empty/blank region while the above-fold captured flat/void | crops/desktop-performance-ux_F-83.png |
| performance-ux F-91 | MEDIUM | rect/e_index_lookup | e86 (Select Make
                  
                
            ) | **DUPLICATE** | another marker shares this exact position | crops/desktop-performance-ux_F-91.png |
| pricing F-16 | MEDIUM | rect/e_index_lookup | e34 (FREE SHIPPING on most orders $75+ — Contiguous US only SHOP ) | **STACKED** | 2+ markers within 6% on this slide (overlapping circles) | crops/desktop-pricing_F-16.png |
| pricing F-23 | MEDIUM | rect/e_index_lookup | e104 (Regular price
          
            From $135.99
          ) | **STACKED** | 2+ markers within 6% on this slide (overlapping circles) | crops/desktop-pricing_F-23.png |
| pricing F-97 | HIGH | point/proposed_anchor_element | - | **WEAK_ANCHOR** | no concrete element anchor (source=proposed_anchor_element, ve=generated_expected_zone) | crops/desktop-pricing_F-97.png |
| pricing F-98 | HIGH | rect/e_index_lookup | e104 (Regular price
          
            From $135.99
          ) | **PREDICATE_MISMATCH** | finding says OVER $1,848 but anchored to a $135.99 element | crops/desktop-pricing_F-98.png |
| trust-credibility F-09 | MEDIUM | point/e_index_lookup | e105 (5.0 /
                    5.0
                

            ) | **STACKED** | 2+ markers within 6% on this slide (overlapping circles) | crops/desktop-trust-credibility_F-09.png |
| trust-credibility F-10 | MEDIUM | point/proposed_anchor_section | - | **WEAK_ANCHOR** | no concrete element anchor (source=proposed_anchor_section, ve=generated_expected_zone) | crops/desktop-trust-credibility_F-10.png |
| trust-credibility F-23 | HIGH | rect/e_index_lookup | e104 (Regular price
          
            From $135.99
          ) | **STACKED** | 2+ markers within 6% on this slide (overlapping circles) | crops/desktop-trust-credibility_F-23.png |
| visual-cta F-08 | MEDIUM | point/proposed_anchor_element | - | **CAPTURE_SUSPECT** | claims empty/blank region while the above-fold captured flat/void | crops/desktop-visual-cta_F-08.png |
| visual-cta F-13 | HIGH | rect/e_index_lookup | e117 (Find parts) | **DUPLICATE** | another marker shares this exact position | crops/desktop-visual-cta_F-13.png |
| visual-cta F-24 | HIGH | point/proposed_anchor_element | - | **CAPTURE_SUSPECT** | claims empty/blank region while the above-fold captured flat/void | crops/desktop-visual-cta_F-24.png |
| visual-cta F-27 | MEDIUM | rect/e_index_lookup | e34 (FREE SHIPPING on most orders $75+ — Contiguous US only SHOP ) | **STACKED** | 2+ markers within 6% on this slide (overlapping circles) | crops/desktop-visual-cta_F-27.png |
| visual-cta F-38 | MEDIUM | rect/e_index_lookup | e29 (Performance 


                      IntakesExhaustCoolingDr) | **CAPTURE_SUSPECT** | claims empty/blank region while the above-fold captured flat/void | crops/desktop-visual-cta_F-38.png |
| category-navigation F-45 | MEDIUM | rect/e_index_lookup | e33 (Electronics


                      LightingWiringInfotainme) | **OK** | exact element anchor (e33, exact_element/high) | crops/desktop-category-navigation_F-45.png |

## How to use this

1. Read the **Verdict**. If DO NOT SHIP, the above-fold likely didn't render - re-capture before trusting any above-fold finding.
2. Open the crops in `_diagnosis/crops/` for every non-OK row and confirm with your eyes (this is the visual assessment the pipeline can't do deterministically).
3. Group the defects by **owning stage** and tune that stage only:
   - **ACQUISITION** -> scripts/acquire_url.py reveal/settle (scroll-trigger + lazy media); re-capture and re-check the screenshot
   - **SPECIALIST** -> contracts/specialist-prompt-v2.md anchor rules (cite the element the claim is actually about; predicates like 'over $X' must anchor to an element that satisfies them, or to the section)
   - **PLACEMENT** -> scripts/report/v2_markers.py + scripts/assembly/review_state.py (region findings -> box over the section; de-stack absence/head-meta; drop the -ai duplicate from the render set)
4. Re-run the audit, re-run this tool, and confirm the defect counts drop. That loop is the accountability - a stage is 'fixed' when its attributed count goes to ~0.
