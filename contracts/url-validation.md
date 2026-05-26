<!-- RESEARCH_DATE: 2026-03-11 -->
# URL Validation Rules

Rules for validating URLs before passing them to agent-browser. Applied to ALL URL fetches across /ecp:audit, /ecp:quick-scan, and /ecp:compare.

## Validation Steps

### 1. Scheme Validation
- ALLOW: `http://`, `https://`
- REJECT: `file://`, `ftp://`, `data:`, `javascript:`, `blob:`, all others
- Error: "Only http:// and https:// URLs are supported."

### 2. Host Validation (IPv4)
Reject all private and reserved ranges:
- `10.0.0.0/8` — Private (RFC 1918)
- `172.16.0.0/12` — Private (RFC 1918)
- `192.168.0.0/16` — Private (RFC 1918)
- `127.0.0.0/8` — Loopback
- `169.254.0.0/16` — Link-local
- `169.254.169.254` — Cloud metadata endpoint (AWS, GCP, Azure)
- `0.0.0.0` — Unspecified
- `localhost` — Loopback hostname
- Error: "Cannot fetch private or internal network addresses."

### 3. Host Validation (IPv6)
Reject:
- `::1` — Loopback
- `::ffff:127.0.0.1` — IPv4-mapped loopback
- `fc00::/7` — Unique local addresses
- `fe80::/10` — Link-local addresses
- Error: "Cannot fetch private or internal IPv6 addresses."

### 4. Host Encoding Bypass Prevention
Reject alternate IP encodings that bypass string matching:
- Hex notation: `0x7f000001` (= 127.0.0.1)
- Octal notation: `0177.0.0.1` (= 127.0.0.1)
- Abbreviated IPs: `127.1` (= 127.0.0.1)
- Decimal notation: `2130706433` (= 127.0.0.1)
- Error: "IP address encoding not supported. Use standard dotted notation."

### 5. DNS Rebinding Protection
Validate on the RESOLVED IP at connection time, not just the hostname string.
A hostname like `evil.example.com` could resolve to `169.254.169.254` at fetch time.
- Resolve DNS first
- Check resolved IP against all rules above
- If resolution changes between check and fetch, re-validate

### 6. User Confirmation
First fetch per domain per session requires user confirmation:
- "About to fetch [domain] — proceed?"
- In --auto mode: confirmation is skipped (the agent opted in by providing the URL)
- Track confirmed domains to avoid re-prompting

## URL Normalization (for progress memory matching)

When normalizing URLs for comparison (NOT for fetching — fetch the original URL):
- Strip protocol (https://, http://)
- Strip www. prefix
- Strip trailing slash
- Strip query parameters
- Strip fragment identifiers (#)
- Lowercase the entire string
