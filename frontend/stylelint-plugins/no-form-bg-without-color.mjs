/**
 * Custom stylelint rule: vl/no-form-bg-without-color
 *
 * Flags any CSS rule whose selector targets <input>, <textarea>, or
 * <select> and sets `background` or `background-color` without a
 * sibling `color` declaration in the same rule block.
 *
 * Rationale: see GitHub issue #28. Setting a background on a form
 * control without an explicit color lets the text inherit from the
 * parent, which on dark sidebars, system-dark-mode, or autofill
 * frequently resolves to white, making it invisible against the white bg.
 * Manual review kept missing this. CI catches it now.
 *
 * Usage in stylelint.config.mjs:
 *   import noFormBgWithoutColor from './stylelint-plugins/no-form-bg-without-color.mjs';
 *   plugins: [noFormBgWithoutColor],
 *   rules: { 'vl/no-form-bg-without-color': true }
 */

import stylelint from 'stylelint';

export const ruleName = 'vl/no-form-bg-without-color';
export const messages = stylelint.utils.ruleMessages(ruleName, {
  missing: (selector, prop) =>
    `Form-control selector "${selector}" sets "${prop}" without "color". ` +
    'Add an explicit color, or remove the background. See #28.',
});

export const meta = {
  url: 'https://github.com/raymond-itsec/vulnledger/issues/29',
};

const FORM_TARGET_REGEX = /\b(input|textarea|select)\b/i;
const BG_PROPS = new Set(['background', 'background-color']);

function plugin(primary) {
  return (root, result) => {
    const validOptions = stylelint.utils.validateOptions(result, ruleName, {
      actual: primary,
      possible: [true, false],
    });
    if (!validOptions || primary !== true) return;

    root.walkRules((rule) => {
      if (!FORM_TARGET_REGEX.test(rule.selector)) return;

      let hasBg = null;
      let hasColor = false;
      rule.walkDecls((decl) => {
        if (BG_PROPS.has(decl.prop.toLowerCase())) hasBg = decl;
        else if (decl.prop.toLowerCase() === 'color') hasColor = true;
      });

      if (hasBg && !hasColor) {
        stylelint.utils.report({
          message: messages.missing(rule.selector, hasBg.prop),
          node: hasBg,
          result,
          ruleName,
        });
      }
    });
  };
}

const rule = stylelint.createPlugin(ruleName, plugin);
rule.ruleName = ruleName;
rule.messages = messages;
rule.meta = meta;

export default rule;
