<!-- RESEARCH_DATE: 2026-03-11 -->
# Next.js Platform Reference

Platform-specific patterns for the CRO builder when generating Next.js/React ecommerce code. Loaded only during the builder phase.

## App Router File Structure for Ecommerce

```
app/
├── layout.tsx              # Root layout (nav, cart provider, analytics)
├── page.tsx                # Homepage
├── loading.tsx             # Global loading skeleton
├── error.tsx               # Global error boundary
├── not-found.tsx           # 404 page
├── (shop)/
│   ├── layout.tsx          # Shop layout (category nav, breadcrumbs)
│   ├── products/
│   │   ├── page.tsx        # Collection/listing page
│   │   ├── [handle]/
│   │   │   ├── page.tsx    # Product detail page (RSC)
│   │   │   ├── loading.tsx # Product skeleton
│   │   │   └── opengraph-image.tsx  # Dynamic OG image
│   ├── cart/
│   │   └── page.tsx        # Cart page
│   └── checkout/
│       └── page.tsx        # Checkout page
├── api/
│   └── webhooks/
│       └── route.ts        # Webhook handlers
└── middleware.ts            # A/B testing, geo, auth
```

## RSC vs Client Component Boundaries

### Server by Default (Product Data, Pricing, Inventory)
```tsx
// app/(shop)/products/[handle]/page.tsx — Server Component
export default async function ProductPage({ params }: { params: Promise<{ handle: string }> }) {
  const { handle } = await params;
  const product = await getProduct(handle);

  return (
    <main>
      <ProductHero product={product} />
      <TrustBadges />
      <Suspense fallback={<ReviewsSkeleton />}>
        <ProductReviews productId={product.id} />
      </Suspense>
      <Suspense fallback={<RecommendationsSkeleton />}>
        <RelatedProducts handle={handle} />
      </Suspense>
    </main>
  );
}
```

### Client at the Leaf (Interactive Elements)
```tsx
'use client';
// components/add-to-cart.tsx — Client Component
import { useOptimistic, useTransition } from 'react';
import { addToCart } from '@/app/actions';

export function AddToCart({ variantId, available }: { variantId: string; available: boolean }) {
  const [isPending, startTransition] = useTransition();

  return (
    <button
      disabled={!available || isPending}
      onClick={() => startTransition(() => addToCart(variantId))}
      aria-busy={isPending}
    >
      {!available ? 'Sold Out' : isPending ? 'Adding...' : 'Add to Cart'}
    </button>
  );
}
```

### Boundary Placement Strategy
- Push `'use client'` as far DOWN the tree as possible
- Product title, price, description, images = Server Component (no interactivity)
- Add-to-cart button, quantity selector, image gallery, variant picker = Client Component
- Reviews list = Server Component; "Write a Review" form = Client Component
- Never put `'use client'` on a layout or page — wrap only the interactive leaf

## next/image for Product Photos

```tsx
import Image from 'next/image';

// Above-fold hero — priority loading
<Image
  src={product.featuredImage.url}
  alt={product.featuredImage.altText || product.title}
  width={800}
  height={800}
  priority
  sizes="(max-width: 768px) 100vw, 50vw"
  placeholder="blur"
  blurDataURL={product.featuredImage.blurDataURL}
/>

// Gallery thumbnails — lazy loaded
<Image
  src={image.url}
  alt={image.altText || `${product.title} - Image ${i + 1}`}
  width={400}
  height={400}
  sizes="(max-width: 768px) 25vw, 100px"
/>
```

Key rules:
- `priority` on above-fold hero image ONLY (sets fetchpriority="high", disables lazy)
- Always provide `sizes` — without it, Next.js assumes 100vw (wastes bandwidth)
- Use `placeholder="blur"` for perceived performance on product images
- Never skip `alt` text — critical for accessibility and SEO

## Server Actions for Mutations

```tsx
'use server';
// app/actions.ts

import { revalidateTag } from 'next/cache';
import { cookies } from 'next/headers';

export async function addToCart(variantId: string) {
  const cartId = (await cookies()).get('cartId')?.value;
  await commerce.addCartItem(cartId, variantId);
  revalidateTag('cart');
}

export async function applyCoupon(formData: FormData) {
  const code = formData.get('code') as string;
  const cartId = (await cookies()).get('cartId')?.value;
  const result = await commerce.applyCoupon(cartId, code);

  if (!result.success) {
    return { error: result.message };
  }
  revalidateTag('cart');
  return { success: true };
}
```

### Progressive Enhancement
Server Actions work WITHOUT JavaScript — the form submits as a standard POST. This means:
- Add-to-cart works even if JS fails to load
- Critical for mobile users on slow connections
- Use `<form action={serverAction}>` pattern for graceful degradation

### Optimistic Updates
```tsx
'use client';
import { useOptimistic } from 'react';

function CartCount({ count }: { count: number }) {
  const [optimisticCount, addOptimistic] = useOptimistic(
    count,
    (state, delta: number) => state + delta
  );
  // Pass addOptimistic to add-to-cart button
}
```

## Middleware for CRO

### A/B Testing (Cookie-Based Variant Assignment)
```typescript
// middleware.ts
import { NextRequest, NextResponse } from 'next/server';

export function middleware(request: NextRequest) {
  // A/B test assignment
  const variant = request.cookies.get('ab-hero')?.value
    || (Math.random() < 0.5 ? 'control' : 'variant-a');

  const url = request.nextUrl.clone();

  // Rewrite to variant route (invisible to user)
  if (url.pathname === '/') {
    url.pathname = `/experiments/homepage/${variant}`;
    const response = NextResponse.rewrite(url);
    if (!request.cookies.has('ab-hero')) {
      response.cookies.set('ab-hero', variant, { maxAge: 60 * 60 * 24 * 30 });
    }
    return response;
  }

  // Geo-detection for localization
  const country = request.geo?.country || 'US';
  const response = NextResponse.next();
  response.headers.set('x-country', country);
  return response;
}

export const config = { matcher: ['/', '/products/:path*'] };
```

### Why Middleware for CRO?
- Runs at the edge before rendering — zero CLS, zero flicker
- Cookie-based persistence across sessions
- Invisible rewrites (URL stays clean)
- Can combine A/B testing + geo + personalization in one pass

## Streaming + Suspense

### Independent Section Loading
```tsx
// Product page with independent streaming sections
export default async function ProductPage({ params }: Props) {
  const { handle } = await params;
  const product = await getProduct(handle); // Fast — cached

  return (
    <main>
      {/* Immediate render — product data is cached/fast */}
      <ProductHero product={product} />
      <AddToCart variantId={product.variants[0].id} available={product.available} />

      {/* Streams in independently — does not block hero */}
      <Suspense fallback={<ReviewsSkeleton />}>
        <ProductReviews productId={product.id} />
      </Suspense>

      {/* Streams in independently */}
      <Suspense fallback={<RecommendationsSkeleton />}>
        <Recommendations handle={handle} />
      </Suspense>
    </main>
  );
}
```

### Skeleton UIs
Every Suspense boundary needs a meaningful skeleton that matches the final layout dimensions. This prevents CLS when content streams in.

```tsx
function ReviewsSkeleton() {
  return (
    <div className="reviews-skeleton" aria-busy="true" aria-label="Loading reviews">
      <div className="h-6 w-32 bg-gray-200 animate-pulse rounded" />
      {[...Array(3)].map((_, i) => (
        <div key={i} className="mt-4 space-y-2">
          <div className="h-4 w-24 bg-gray-200 animate-pulse rounded" />
          <div className="h-4 w-full bg-gray-200 animate-pulse rounded" />
        </div>
      ))}
    </div>
  );
}
```

## Metadata API

```tsx
// app/(shop)/products/[handle]/page.tsx
import { Metadata } from 'next';
import { cache } from 'react';

const getProduct = cache(async (handle: string) => {
  return commerce.getProduct(handle);
});

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { handle } = await params;
  const product = await getProduct(handle); // Deduped with page render

  return {
    title: product.seo?.title || product.title,
    description: product.seo?.description || product.description.slice(0, 155),
    openGraph: {
      images: [{ url: product.featuredImage.url, width: 1200, height: 630 }],
    },
  };
}
```

Use `React.cache()` to deduplicate the product fetch between `generateMetadata` and the page component — same request, single query.

## Core Web Vitals for Ecommerce

### LCP (Largest Contentful Paint)
- Use `priority` on hero product image (disables lazy loading, adds fetchpriority="high")
- Preload fonts: `next/font` handles this automatically
- Avoid client-side data fetching for above-fold content — use RSC
- Target: <2.5s

### CLS (Cumulative Layout Shift)
- Always set `width` and `height` on `<Image>` (or use `fill` with a sized container)
- Skeleton placeholders must match final content dimensions
- Reserve space for dynamic content (reviews count, price badges)
- Never inject content above the fold after load
- Target: <0.1

### INP (Interaction to Next Paint)
- Keep client components small — split heavy interactions
- Use `useTransition` for non-urgent state updates (filtering, sorting)
- Avoid synchronous state updates in event handlers for large lists
- Use `React.startTransition` for cart updates that trigger re-renders
- Target: <200ms

## 12 Next.js Ecommerce Anti-Patterns

| # | Anti-Pattern | Fix |
|---|-------------|-----|
| 1 | `'use client'` on page or layout | Push to leaf components — only interactive elements need client |
| 2 | Client-side fetch for product data | Use RSC — product data is static/cached, no need for client fetch |
| 3 | Missing `priority` on hero image | Add `priority` to above-fold product image for faster LCP |
| 4 | Missing `sizes` on `<Image>` | Always provide `sizes` — default 100vw wastes bandwidth |
| 5 | Waterfall data fetching | Use `Promise.all()` for independent fetches; Suspense for streaming |
| 6 | Client-side A/B testing | Use middleware for zero-CLS variant assignment |
| 7 | Barrel file imports (`@/components`) | Import directly from component file to reduce bundle size |
| 8 | Missing Suspense on async sections | Every independently-loading section needs its own Suspense boundary |
| 9 | Hardcoded prices/currency | Fetch from commerce API; use Intl.NumberFormat for formatting |
| 10 | No error boundary on product page | Add `error.tsx` — a broken review fetch should not crash the product page |
| 11 | Synchronous cart mutations | Use Server Actions with `useTransition` for non-blocking cart updates |
| 12 | Missing generateMetadata | Every product page needs dynamic metadata for SEO and social sharing |

## Detection Heuristics

How to confirm a site uses Next.js:
- `next.config.*` file in project root
- `"next"` in package.json dependencies
- `__next` div in page source
- `/_next/` in asset URLs
- `*.vercel.app` domain (likely but not certain — ask to confirm)
- `x-powered-by: Next.js` header (if not stripped)
- `.next/` build directory
