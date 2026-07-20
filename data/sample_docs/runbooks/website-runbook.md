# Website Runbook

Owner: Web team (Leo Martins, @leom · Hana Kim, @hanak). Channel: #web.
Stack: Next.js on Vercel · headless CMS (Contentful) · marketing site at company.com, app at app.company.com.

## Deploying the website

- Merges to `main` in `company/website` auto-deploy to production via Vercel.
- Every PR gets a preview URL — share it in the PR description for review.
- Rollback: Vercel dashboard → Deployments → "Promote to Production" on the last good build.
  Rollback first, debug after; a broken marketing site is lost revenue by the minute.

## Site is down or slow

1. Check https://status.vercel.com before anything else.
2. Check the edge cache hit rate in the Vercel analytics tab — a hit-rate cliff usually means
   a bad cache-control header shipped in the last deploy.
3. Core Web Vitals regressions: run `npm run lighthouse` locally against the preview build;
   the budget is LCP < 2.5 s, CLS < 0.1, INP < 200 ms. The CI `lighthouse-budget` job blocks
   merges that exceed budgets by >10%.

## CMS content changes

- Marketing edits content in Contentful; publishing triggers an incremental rebuild (~90 s).
- If a published change doesn't appear, check the webhook delivery log in Contentful first,
  then the on-demand revalidation endpoint (`/api/revalidate`) logs in Vercel.
- Schema/content-model changes are code-reviewed: they live in `cms/migrations/` and run via CI.

## SEO guardrails

- Every page needs a unique title + meta description; the `seo-lint` CI job enforces this.
- Redirects live in `redirects.config.js` — never delete a public URL without a 301.
- Robots and sitemap are generated at build time; if staging gets indexed, check that the
  `X-Robots-Tag: noindex` header is present on all non-production domains.

## Accessibility

Target: WCAG 2.1 AA. axe checks run in CI on key templates. Common failures:
missing alt text from CMS entries (fix content, not code), contrast on new brand colors
(escalate to design), and focus traps in modals (use the shared `Dialog` component).

## A/B tests

Experiments run through the `experiments.json` config with an end date — no permanent flags.
Ended experiments must be removed within one sprint; @hanak audits monthly.
