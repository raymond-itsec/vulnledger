# VulnLedger security findings register

Stable record of every security finding raised against this codebase.
Each row maps a `VL-YYYY-NNN` ID to a GitHub issue and notes the date
it was discovered and (when fixed) the date it was closed.

| ID | Title | Severity | Status | Found | Fixed | Issue |
|---|---|---|---|---|---|---|
| VL-2026-001 | Username enumeration via login timing oracle | Med-High | Fixed | 2026-04-30 | 2026-04-30 | [#11](../../issues/11) |
| VL-2026-002 | `window.location.href` in dashboard row click | Info | Fixed | 2026-04-30 | 2026-04-30 | [#12](../../issues/12) |
| VL-2026-003 | Auth-gate gap on `/app/*` paths in Caddy | Low-Med | Fixed | 2026-04-30 | 2026-04-30 | [#13](../../issues/13) |
| VL-2026-004 | Forwarding headers not blocked at edge | Low-Med | Fixed | 2026-04-30 | 2026-04-30 | [#14](../../issues/14) |
| VL-2026-005 | Body-size limit only on attachments path | Low | Fixed | 2026-04-30 | 2026-04-30 | [#15](../../issues/15) |
| VL-2026-006 | `caddy-ratelimit` module not version-pinned | Low | Fixed | 2026-04-30 | 2026-04-30 | [#16](../../issues/16) |
| VL-2026-007 | Missing modern security headers | Info | Fixed | 2026-04-30 | 2026-04-30 | [#17](../../issues/17) |
| VL-2026-008 | No HTTP timeouts configured | Low | Fixed | 2026-04-30 | 2026-04-30 | [#18](../../issues/18) |
| VL-2026-009 | Edge CSP only `frame-ancestors` | Low-Med | Fixed | 2026-04-30 | 2026-04-30 | [#19](../../issues/19) |
| VL-2026-010 | `POST /api/findings` 500 - nested transaction | High (functional) | Fixed | 2026-04-30 | 2026-05-01 | [#20](../../issues/20) |
| VL-2026-011 | Sidebar active state and breadcrumb mis-derive on /app sub-paths | Low (UX) | Fixed | 2026-04-30 | 2026-05-01 | [#21](../../issues/21) |
| VL-2026-012 | Login rate-limit bypass via path normalization | Low | Fixed | 2026-04-30 | 2026-04-30 | [#23](../../issues/23) |
| VL-2026-013 | Caddy attachment body-cap matcher misconfigured — uploads >1MB silently fail | Medium (functional) | Fixed | 2026-04-30 | 2026-04-30 | [#24](../../issues/24) |
| VL-2026-014 | Caddy session-hint gate hardcoded; drifts from backend env | Low | Fixed | 2026-05-01 | 2026-05-01 | [#31](../../issues/31) |
| VL-2026-015 | Admin user create/update under-validated; 500s on duplicates | Medium | Fixed | 2026-05-01 | 2026-05-01 | [#32](../../issues/32) |
| VL-2026-016 | SvelteKit auth checks are client-only; no server-side enforcement | Low | Open | 2026-05-01 | — | [#34](../../issues/34) |
| VL-2026-017 | Invite redemption lacks row-level lock; relies on downstream unique constraint | Low | Open | 2026-05-02 | — | [#41](../../issues/41) |
| VL-2026-018 | Onboarding cookie scoped to wrong path; whole invited-user signup flow returns 401 | High (functional) | Fixed | 2026-05-05 | 2026-05-05 | [#59](../../issues/59) |
| VL-2026-019 | Invite verification returns 404 for invalid credential; should be 401 | Low | Fixed | 2026-05-05 | 2026-05-05 | [#60](../../issues/60) |
| VL-2026-020 | HTML5 form validation overrides unified error UI on onboarding form | Low (UX) | Fixed | 2026-05-05 | 2026-05-05 | [#61](../../issues/61) |

## Scope of the register

A finding earns a `VL-YYYY-NNN` ID and a row here when it **affects
behavior** — security, correctness, performance, or user-visible UX.
Pure code-hygiene work (refactors, doc-only changes, chore PRs) lives
as a plain GitHub issue with the appropriate area + `enhancement`
labels and is **not** registered here, even when it was discovered
during an audit sweep.

Borderline cases default to inclusion: if uncertain whether something
touches behavior, give it a VL- ID.

## Conventions

- IDs are `VL-YYYY-NNN` — year-prefixed, monotonic within the year, never reused.
- Every finding has a corresponding GitHub issue, regardless of whether it
  was already fixed when discovered.
- Closing happens via `Closes #N` in the commit message that lands the fix —
  GitHub auto-closes the issue when that commit hits `main`.
- Severity scale: Info / Low / Medium / High / Critical.
- Status: Open / In progress / Fixed / Dismissed / Won't fix.
