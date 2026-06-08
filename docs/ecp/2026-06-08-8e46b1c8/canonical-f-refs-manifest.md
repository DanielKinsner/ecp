# Canonical f_refs manifest

USE ONLY THESE f_refs in priority_path[].f_refs, scope_page_synchronized_refs,
quick_wins_manifest, severity_manifest, humanized_findings[].f_ref, and as the
heading suffix on each finding subsection in audit-{device}.md.

Format: `{cluster} F-{NN}` (zero-padded). The NN integer is
**content-hash-derived** (sha256(surface|baton_index|verdict)[:6] mod 99 + 1)
per `scripts/assembly/pipeline.py:assign_display_indices`. The renderer
re-derives the same hash at parse time and rejects mismatched refs as
out-of-allowlist — paste these integers verbatim, do NOT renumber.

| f_ref | severity | devices_present | title |
|---|---|---|---|
| `category-navigation F-03` | LOW | mobile | Vehicle Fitment Selector Anchors the Compatibility Path |
| `category-navigation F-05` | MEDIUM | mobile | Shop by Vehicle Drawer Lists Only Two Vehicles |
| `category-navigation F-29` | LOW | desktop | Category Cards Expose Subcategories Plus Dedicated CTAs |
| `category-navigation F-41` | LOW | desktop | Top Navigation Is Lean and Clearly Labeled |
| `category-navigation F-45` | MEDIUM | desktop | Category Cards Don't Match the Shop-by-Category Menu Taxonomy |
| `category-navigation F-46` | MEDIUM | desktop | Vehicle Selector Submit Is an Icon-Only Square With No Label |
| `category-navigation F-50` | HIGH | mobile | Only Category Path in First Viewport Is the Hidden Hamburger Drawer |
| `category-navigation F-52` | MEDIUM | desktop | Fitment Selector Floats in an Empty Black Band Above the Fold |
| `category-navigation F-63` | MEDIUM | mobile | Category Carousel Reveals Roughly One Tile, Hiding Catalog Breadth |
| `category-navigation F-88` | LOW | mobile | Search Box Is a Visible Full-Width Input at Page Top |
| `category-navigation F-99` | LOW | desktop | Site Search Is Prominent, Wide, and Top-Positioned |
| `content-seo F-27` | MEDIUM | desktop | Product Card Images Use CSS Class Names as Alt Text |
| `content-seo F-32` | HIGH | desktop,mobile | Title Tag Is Just the Brand Name Repeated Twice |
| `content-seo F-60` | MEDIUM | desktop | No Open Graph Image for Social and AI Previews |
| `content-seo F-61` | HIGH | desktop | Featured Products Carry No Product or Rating Schema |
| `content-seo F-62` | HIGH | mobile | Star Ratings and Prices Shown but No Product Schema |
| `content-seo F-63` | LOW | mobile | Canonical and Mobile Viewport Tags Are Correctly Set |
| `content-seo F-64` | LOW | desktop | Self-Referencing HTTPS Canonical on the Homepage |
| `content-seo F-74` | MEDIUM | desktop | Homepage Has No Meta Description At All |
| `content-seo F-75` | MEDIUM | mobile | Meta Description and Social Preview Are Placeholder Brand Text |
| `content-seo F-76` | HIGH | mobile | Featured Product Images Use CSS Class Names as Alt Text |
| `content-seo F-87` | MEDIUM | mobile | Homepage Has Almost No Descriptive or Benefit-First Copy |
| `ethics F-16` | MEDIUM | page | Privacy Policy Links to Staging Domain, Not Canonical Store |
| `ethics F-30` | LOW | page | Newsletter Signup Purpose Clearly Disclosed at Point of Collection |
| `ethics F-37` | LOW | page | CCPA Privacy Choices Opt-Out Link Present in Footer |
| `ethics F-46` | LOW | page | Product Card Star Ratings Display Genuine Review Counts |
| `ethics F-56` | LOW | page | Newsletter Hero Background Is Decorative Automotive Imagery, Not Product Misrepr |
| `ethics F-64` | LOW | page | No EU Cookie Consent Required — US-Only Targeting Confirmed |
| `ethics F-67` | LOW | page | No Fabricated Urgency or Countdown Timers Detected |
| `ethics F-69` | LOW | page | Free Shipping Threshold Disclosed Upfront in Announcement Bar |
| `performance-ux F-13` | LOW | mobile | Header Tap Targets and Native Dropdowns Meet Mobile Sizing |
| `performance-ux F-17` | MEDIUM | mobile | Featured Collection Product Images Carry No Explicit Dimensions for CLS |
| `performance-ux F-18` | MEDIUM | mobile | No Sticky Header or Cart Once the Visitor Scrolls Past the First Screen |
| `performance-ux F-24` | MEDIUM | desktop | Featured Collection Product Images Show No Reserved Aspect Ratio |
| `performance-ux F-37` | HIGH | desktop | No Above-Fold Image Preload; Category Tile Is an Unprioritized LCP Element |
| `performance-ux F-52` | LOW | desktop | Fonts Preloaded and Logo Eager-Loaded in the Head |
| `performance-ux F-76` | HIGH | mobile | No Above-Fold Image Preload; 74 Checkout Scripts Prefetched on Home Load |
| `performance-ux F-83` | HIGH | desktop | Empty Black Band Wastes the Entire Above-Fold Zone on Desktop |
| `performance-ux F-91` | MEDIUM | desktop | Vehicle Finder Stacks Four Sequential Native Dropdowns With No Default |
| `performance-ux F-95` | MEDIUM | mobile | Vehicle Finder Pushes Two of Four Dropdowns and Find Parts Below the Fold |
| `pricing F-16` | MEDIUM | desktop | Free Shipping Bar States Threshold Without Progress Cue |
| `pricing F-23` | MEDIUM | desktop | Was/Now Anchor Shown On One Product But Not The Grid |
| `pricing F-43` | MEDIUM | mobile | Featured "From $135.99" Price Carries No MSRP or Compare-At Anchor |
| `pricing F-51` | LOW | mobile | Free-Shipping Threshold Stated as a Static Banner With No Progress Framing |
| `pricing F-68` | LOW | mobile | Charm Pricing Used Correctly on Utilitarian Parts |
| `pricing F-96` | MEDIUM | mobile | No Installment / Pay-in-4 Pricing Shown Beside the $135.99 Item |
| `pricing F-97` | HIGH | desktop | No Installment Pricing On Items Over $1,000 |
| `pricing F-98` | HIGH | desktop | Featured Collection Prices Run With No Reference Anchor |
| `trust-credibility F-09` | MEDIUM | desktop | Featured Collection Cards Show Perfect 5.0/5.0 on Only 2-3 Reviews |
| `trust-credibility F-10` | MEDIUM | desktop | Homepage Has No Company-Credibility or Aggregate Trust Block |
| `trust-credibility F-13` | HIGH | mobile | Featured Collection Cards Show 5.0/5.0 With No Review Count |
| `trust-credibility F-15` | MEDIUM | mobile | Star Ratings Carry No AggregateRating Markup for Search Results |
| `trust-credibility F-23` | HIGH | desktop | Most Featured Collection Cards Carry Zero Reviews |
| `trust-credibility F-27` | MEDIUM | mobile | No Guarantee or Return-Policy Reassurance Near the Products |
| `trust-credibility F-28` | MEDIUM | mobile | Payment Badges Sit Only in Footer, Far From Any Buying Decision |
| `trust-credibility F-31` | LOW | mobile | Recognized Payment Brands and Social Links Present in Footer |
| `trust-credibility F-62` | LOW | desktop | Recognized Payment Badges Present in Footer |
| `visual-cta F-08` | MEDIUM | desktop | Hero Band Is Empty Black Space With No Supporting Media |
| `visual-cta F-11` | HIGH | mobile | No Hero Headline or Value Proposition Above the Vehicle Selector |
| `visual-cta F-12` | MEDIUM | mobile | FIND PARTS Button Is Undersized, Not Full-Width, and Its Label Reads Low-Contras |
| `visual-cta F-13` | HIGH | desktop | Hero's Only CTA Is a 59px Icon-Only 'Find parts' Button |
| `visual-cta F-16` | LOW | mobile | SHOP PERFORMANCE Category Card Button Is Clear and Well-Contrasted |
| `visual-cta F-24` | HIGH | desktop | Hero Band Has No Headline or Value Proposition |
| `visual-cta F-27` | MEDIUM | desktop | Only Above-Fold Trust Element Is a Shipping Promo, Not Credibility |
| `visual-cta F-38` | MEDIUM | desktop | Five Identical 'SHOP' Category CTAs Compete With No Primary |
| `visual-cta F-46` | LOW | mobile | Top FREE SHIPPING / SHOP NOW Bar Sits in the Banner-Blindness Zone |
| `visual-cta F-55` | LOW | desktop | Category 'SHOP' Buttons Use High-Contrast Blue Against Dark Cards |
| `visual-cta F-67` | MEDIUM | mobile | No Sticky CTA After the Find Parts Button Scrolls Out of View |

_Total: 68 canonical f_refs across 7 cluster(s)._