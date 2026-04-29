# Self-hosted webfonts

VulnLedger ships its webfonts as part of the app — no third-party CDN, no
external requests, no IP leak to US-based providers. This file documents
what's bundled and the license under which we redistribute it.

## Why self-hosted

- **GDPR**: external font CDNs (Google Fonts, Adobe Fonts) leak visitor IPs to
  third parties. German courts have ruled this violates GDPR without consent
  (Munich Regional Court, AZ. 3 O 17493/20, 2022).
- **Auditability**: shipping fonts in-tree means the exact byte content is
  pinned in git and reviewed alongside code.
- **CSP**: lets us run `font-src 'self'` with no third-party allowances.
- **Air-gapped deployments**: works offline / on isolated networks.

## Bundled families

### Inter

- **File**: `inter/InterVariable.woff2`
- **Version**: 4.66 (variable, full weight axis 100–900)
- **Author**: Rasmus Andersson — <https://rsms.me/inter/>
- **Source**: <https://github.com/rsms/inter>
- **License**: SIL Open Font License 1.1 — see `inter/LICENSE.txt`
- **Used for**: all UI text (`var(--font-sans)`)

### JetBrains Mono

- **File**: `jetbrains-mono/JetBrainsMono-Variable.woff2`
- **Version**: 2.304 (variable, weight axis 100–800)
- **Author**: JetBrains s.r.o.
- **Source**: <https://github.com/JetBrains/JetBrainsMono>
- **License**: SIL Open Font License 1.1 — see `jetbrains-mono/OFL.txt`
- **Used for**: code, finding IDs, technical values (`var(--font-mono)`)

## SIL Open Font License 1.1 — what it permits

- ✅ Use in commercial products
- ✅ Embed in documents
- ✅ Bundle with software (this repo)
- ✅ Modify and redistribute (with the same license)
- ❌ Sell the font files standalone (we don't)
- ❌ Use the Reserved Font Name on a derivative (we don't create derivatives)

The OFL text is included verbatim alongside each font file. Do not delete
the LICENSE / OFL files when refactoring `static/fonts/` — they are the
condition of redistribution.

## Updating

Variable fonts almost never need updating; both families have stable
typographic shapes. If you do upgrade:

1. Download new WOFF2 from the official source URL above
2. Verify with `file <file>.woff2` — must say "Web Open Font Format (Version 2)"
3. Compare visual specimen against the design pack to confirm no metric drift
4. Update version number in this file
5. Commit
