/**
 * Stylelint config for the VulnLedger frontend.
 *
 * Currently focused on a single custom rule that prevents the recurring
 * white-on-white form input regression tracked in #28 / #29. Standard
 * stylistic linting is intentionally not enabled yet; this is a tightly
 * scoped policy gate, not a full code-style enforcer.
 *
 * To extend later, add stylelint-config-standard to devDependencies and
 * include it in `extends` below.
 */

import noFormBgWithoutColor from './stylelint-plugins/no-form-bg-without-color.mjs';

export default {
  // Parse Svelte single-file components: postcss-html extracts the
  // <style> blocks. Plain .css files are handled by the default parser.
  customSyntax: 'postcss-html',

  plugins: [noFormBgWithoutColor],

  rules: {
    'vl/no-form-bg-without-color': true,
  },

  ignoreFiles: [
    'src/lib/api/generated.ts',
    'src/lib/styles/fonts.css',
    'build/**',
    '.svelte-kit/**',
    'node_modules/**',
  ],
};
