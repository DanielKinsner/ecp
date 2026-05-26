# Reference Live-Link Check

Internal maintenance file. This is a live URL health pass, not a claim-content audit.

- Generated: 2026-04-24
- Refresh command: `python3 scripts/check-reference-links.py`
- Error/server-error URLs receive a slower retry before this report is written.
- Treat 401/403/405/429 as reachable-but-blocked unless manual review shows otherwise.

## Summary

| Metric | Value |
| --- | --- |
| Unique URLs checked | 1195 |
| Action-required URLs | 108 |
| Blocked/rate-limited URLs | 204 |
| Placeholder/example URLs | 17 |

## Status Mix

| Status | Count |
| --- | --- |
| live | 866 |
| blocked-or-rate-limited | 204 |
| dead | 81 |
| error | 22 |
| placeholder | 17 |
| server-error | 5 |

## Action Queue

| Status | HTTP | Files | URL |
| --- | --- | --- | --- |
| error |  | cookie-consent-and-compliance.md | https://advmetrics.co/ |
| dead | 404 | title-formulas-serp-psychology.md | https://ahrefs.com/blog/google-title-rewrites/ |
| error |  | cta-design-and-placement.md | https://asktog.com/atc/principles-of-interaction-design/ |
| dead | 404 | merchandising-psychology.md | https://baymard.com/research/category-navigation |
| dead | 404 | filtering-ux.md, grid-layout.md, order-confirmation.md ... | https://baymard.com/research/mobile-commerce |
| dead | 404 | eye-tracking-and-scan-patterns.md, hero-section-psychology.md, mobile-conversion.md | https://baymard.com/research/mobile-ecommerce |
| dead | 404 | image-quantity-types.md, thumbnail-design.md | https://baymard.com/research/product-lists |
| error |  | benefit-first-descriptions.md | https://bigstarcopywriting.com.au/ |
| dead | 404 | mobile-conversion.md | https://blog.hubspot.com/marketing/form-conversion-rate-form-field |
| dead | 404 | color-psychology.md | https://blog.hubspot.com/marketing/seasonal-marketing |
| error |  | cta-design-and-placement.md | https://blog.logrocket.com/ux-design/primary-secondary-tertiary-buttons-ux/ |
| error |  | loyalty-programs.md | https://bondbl.com/ |
| error |  | loyalty-programs.md | https://bondbrandloyalty.com/loyalty-report/ |
| error |  | ai-search-agentic-discovery.md | https://business.adobe.com/blog/perspectives/generative-ai-and-the-future-of-commerce |
| dead | 404 | cognitive-load-management.md | https://commandc.com/insights/color-variant-conversion/ |
| error |  | cta-design-and-placement.md | https://contentverve.com/cta-button-best-practices/ |
| dead | 404 | cta-design-and-placement.md | https://conversionfanatics.com/case-studies/ |
| dead | 404 | cross-cultural-considerations.md | https://corporate.payu.com/blog/how-local-payment-methods-help-you-reach-global-customers/ |
| error |  | cross-cultural-considerations.md | https://design.fusionfabric.cloud/foundations/rtl |
| dead | 404 | cta-design-and-placement.md | https://designcourse.com/article/primary-secondary-tertiary-actions |
| dead | 404 | product-cards.md | https://developer.apple.com/design/human-interface-guidelines/inputs/touch-interactions/ |
| dead | 404 | color-psychology.md | https://doi.org/10.1080/00140139.2013.790489 |
| dead | 404 | social-proof-patterns.md | https://doi.org/10.1080/0144929X.2023.2250339 |
| dead | 404 | cross-cultural-considerations.md | https://doi.org/10.1108/CCSM-01-2017-0010 |
| dead | 404 | tiered-pricing.md | https://doi.org/10.1509/jmr.11.0258 |
| dead | 404 | color-psychology.md | https://export.ebay.com/en/listing/listing-best-practices/photos/picture-requirements/ |
| error |  | image-seo-alt-text.md | https://getflowbox.com/ |
| dead | 404 | mobile-conversion.md | https://gitnux.org/dark-mode-statistics/ |
| error |  | order-confirmation.md | https://growthsuite.com/ |
| dead | 404 | mobile-conversion.md | https://hcil.umd.edu/research/ |
| dead | 404 | abandoned-cart-psychology.md | https://help.klaviyo.com/hc/en-us/articles/115005086787 |
| dead | 404 | media-performance-optimization.md | https://httparchive.org/reports/media |
| dead | 404 | cta-design-and-placement.md | https://info.usablenet.com/2024-report-on-digital-accessibility-lawsuits |
| dead | 404 | cognitive-load-management.md | https://kinde.com/blog/business/saas-pricing-page-best-practices/ |
| dead | 404 | accessibility.md | https://m3.material.io/foundations/accessibility/overview |
| dead | 404 | grid-layout.md | https://m3.material.io/foundations/accessible-design/accessibility-basics |
| error |  | order-confirmation.md | https://parcellab.com |
| error |  | buyers-remorse.md | https://parcellab.com/ |
| dead | 404 | cognitive-load-management.md | https://plumrocket.com/blog/trust-badges-conversion |
| dead | 404 | content-freshness-signals.md | https://sparktoro.com/blog/a-critical-examination-of-the-google-search-api-document-leak/ |
| dead | 404 | image-seo-alt-text.md | https://sparktoro.com/blog/how-much-of-googles-search-traffic-is-actually-going-to-google/ |
| dead | 404 | color-psychology.md | https://speero.com/blog/color-psychology |
| dead | 404 | color-psychology.md | https://speero.com/blog/google-41-shades-of-blue |
| dead | 404 | trust-and-credibility.md | https://stripe.com/blog/payment-method-conversion-rate |
| dead | 404 | cross-cultural-considerations.md | https://stripe.com/guides/state-of-european-checkouts-2024 |
| dead | 404 | mobile-conversion.md | https://stripe.com/newsroom/news/adding-payment-methods-can-boost-revenue-by-up-to-14 |
| dead | 404 | cross-cultural-considerations.md | https://stripe.com/resources/more/local-payment-methods-101 |
| dead | 404 | personalization-psychology.md | https://thegood.com/insights/social-proof-ecommerce/ |
| dead | 404 | eye-tracking-and-scan-patterns.md | https://videowise.com/blog/shoppable-video-statistics |
| dead | 404 | cta-design-and-placement.md | https://vwo.com/blog/cta-button-tips/ |
| dead | 404 | cognitive-load-management.md | https://vwo.com/blog/single-page-vs-multi-page-checkout/ |
| dead | 404 | cta-design-and-placement.md | https://vwo.com/blog/state-of-ab-testing/ |
| dead | 404 | cta-design-and-placement.md | https://vwo.com/blog/whitespace-and-conversion-rate/ |
| dead | 404 | cta-design-and-placement.md | https://wisernotify.com/blog/cta-stats/ |
| dead | 404 | cognitive-load-management.md | https://wisernotify.com/blog/product-badges-ecommerce/ |
| dead | 404 | cognitive-load-management.md | https://wpmanageninja.com/docs/ninja-tables/styling-your-table/pricing-table-design-tips/ |
| dead | 404 | cross-cultural-considerations.md | https://www.adyen.com/payment-methods-guide |
| dead | 404 | merchandising-psychology.md | https://www.algolia.com/products/ai-powered-search/merchandising-studio/ |
| dead | 404 | scarcity-urgency.md | https://www.ama.org/marketing-news/new-research-about-time-based-urgency-in-online-retail/ |
| dead | 404 | ugc-reviews-seo.md | https://www.amsive.com/insights/seo/how-googles-algorithm-updates-favor-authentic-ugc/ |
| dead | 404 | ugc-integration.md | https://www.bazaarvoice.com/blog/why-user-generated-content-is-authentic/ |
| dead | 404 | eeat-product-pages.md, image-seo-alt-text.md | https://www.bazaarvoice.com/research-and-insights/ |
| dead | 404 | ugc-reviews-seo.md | https://www.bazaarvoice.com/resources/bazaarvoice-shopper-experience-index/ |
| dead | 404 | ar-3d-visualization.md | https://www.brandxr.io/consumer-augmented-reality-shopping-statistics |
| dead | 404 | cta-design-and-placement.md | https://www.campaignmonitor.com/resources/knowledge-base/the-most-powerful-element-in-email-marketing-is-your-cta/ |
| dead | 404 | trust-and-credibility.md | https://www.conversion-rate-experts.com/guarantee-article/ |
| server-error | 500 | cross-cultural-considerations.md | https://www.crisoltranslations.com/our-blog/ecommerce-localisation/ |
| error |  | eye-tracking-and-scan-patterns.md | https://www.cxpartners.co.uk/our-thinking/what_people_see_before_they_buy_design_guidelines_for_ecommerce_product_pages_with_eyetracking_data |
| dead | 404 | color-psychology.md | https://www.emailonacid.com/blog/article/email-development/dark-mode-for-email-everything-you-need-to-know/ |
| dead | 404 | cross-cultural-considerations.md | https://www.emplicit.co/blog/why-localization-is-critical-for-global-e-commerce |
| dead | 404 | cross-cultural-considerations.md | https://www.entrepreneur.com/growing-a-business/why-offering-local-payment-methods-is-critical-for-global/466291 |
| error |  | cookie-consent-and-compliance.md | https://www.etracker.com/en/ |
| error |  | video-integration.md | https://www.eyeviewdigital.com/ |
| error |  | social-commerce-psychology.md | https://www.fcc.gov/consumers/guides/stop-unwanted-robocalls-and-texts |
| server-error | 503 | pricing-psychology.md | https://www.fedex.com/ |
| dead | 404 | eye-tracking-and-scan-patterns.md | https://www.goodvidio.com/blog/ |
| dead | 404 | cta-design-and-placement.md | https://www.growthrock.co/case-studies/ |
| dead | 404 | color-psychology.md | https://www.ijcesen.com/index.php/ijcesen/article/view/dark-mode-systematic-review |
| dead | 404 | color-accuracy.md | https://www.iso.org/standard/43393.html |
| error |  | cross-cultural-considerations.md | https://www.kvk.nl/en/international-business/selling-to-germany/ |
| error |  | pricing-psychology.md | https://www.mckinsey.com/capabilities/growth-marketing-and-sales/how-we-help-clients/clm-online-retailer |
| error |  | personalization-psychology.md | https://www.mckinsey.com/capabilities/growth-marketing-and-sales/our-insights/the-value-of-getting-personalization-right-or-wrong-is-multiplying |
| dead | 404 | cta-design-and-placement.md | https://www.nngroup.com/articles/form-design-best-practices/ |
| dead | 404 | mobile-conversion.md | https://www.nngroup.com/articles/gestures-go-rogue/ |
| dead | 404 | cta-design-and-placement.md | https://www.nngroup.com/articles/microcopy/ |
| dead | 404 | content-freshness-signals.md | https://www.nytimes.com/2007/06/03/technology/03google.html |
| dead | 404 | eye-tracking-and-scan-patterns.md | https://www.objectiveexperience.com/eye-tracking-2021-you-look-where-they-look/ |
| dead | 404 | review-collection.md | https://www.postscript.io/resources/ |
| dead | 404 | ugc-integration.md | https://www.powerreviews.com/insights/state-of-ugc/ |
| dead | 404 | cognitive-load-management.md | https://www.profitero.com/blog/amazon-best-seller-badges-glance-views |
| dead | 404 | cross-cultural-considerations.md | https://www.rapyd.net/resource/state-of-cross-border-payments-2024/ |
| dead | 404 | personalization-psychology.md | https://www.retail-systems.com/rs/Wunderkind_70_Percent_Believe_Advertisers_Dont_Respect_Digital_Experience.php |
| dead | 404 | mobile-conversion.md | https://www.salecycle.com/blog/featured/remarketing-report-2024/ |
| server-error | 500 | personalization-psychology.md | https://www.salesforce.com/news/stories/customer-engagement-research-2023/ |
| dead | 404 | color-psychology.md | https://www.semrush.com/blog/web-accessibility-seo/ |
| dead | 404 | cross-cultural-considerations.md | https://www.shopify.com/plus/solutions/global-ecommerce |
| dead | 404 | trust-and-credibility.md | https://www.signifyd.com/resources/report/state-of-commerce/ |
| dead | 404 | mobile-conversion.md | https://www.smashingmagazine.com/2015/01/inconspicuous-design-decisions-affect-user-experience/ |
| server-error | 500 | cross-cultural-considerations.md | https://www.star-ts.com/blog/multilingual-numbers-and-currency-formatting/ |
| server-error | 503 | page-performance-psychology.md | https://www.taylorfrancis.com/books/mono/10.1201/9780203736166/psychology-human-computer-interaction-stuart-card |
| dead | 404 | trust-and-credibility.md | https://www.tidio.com/blog/ecommerce-trust/ |
| error |  | social-commerce-psychology.md | https://www.tiktok.com/business/ |
| dead | 404 | eye-tracking-and-scan-patterns.md | https://www.tobii.com/resource-center/scientific-publications |
| error |  | cta-design-and-placement.md | https://www.tractionmarketing.co.nz/blog |
| dead | 404 | cognitive-load-management.md | https://www.winsomemarketing.com/marketing/decision-fatigue-product-variants |
| dead | 404 | color-accuracy.md | https://www.xrite.com/categories/calibration-profiling/colorchecker |
| dead | 404 | cognitive-load-management.md | https://www2.psychology.uiowa.edu/faculty/mordkoff/InfoProc/pdfs/Hick%201952.pdf |
| dead | 404 | cognitive-load-management.md | https://zuko.io/blog/checkout-form-benchmark-report |

## What This Does Not Prove

- It does not prove the source still supports the claim.
- It does not prove statistics are copied correctly.
- It does not prove legal or platform guidance is current.
- Use this report to choose manual source-verification batches.
