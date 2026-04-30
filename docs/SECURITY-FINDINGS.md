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
| VL-2026-010 | `POST /api/findings` 500 — nested transaction | High (functional) | Open | 2026-04-30 | — | [#20](../../issues/20) |
| VL-2026-011 | Breadcrumb mismatches active sidebar item on error page | Info | Open | 2026-04-30 | — | [#21](../../issues/21) |
| VL-2026-012 | Login rate-limit bypass via path normalization | Low | Open | 2026-04-30 | — | [#23](../../issues/23) |
| VL-2026-013 | Caddy attachment body-cap matcher misconfigured — uploads >1MB silently fail | Medium (functional) | Fixed | 2026-04-30 | 2026-04-30 | [#24](../../issues/24) |

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
