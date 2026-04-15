import { c as escape_html } from "./renderer.js";
import "clsx";
/* empty css                                    */
function Modal($$renderer, $$props) {
  let { title = "", show = false, onclose, children } = $$props;
  if (show) {
    $$renderer.push("<!--[0-->");
    $$renderer.push(`<div class="overlay svelte-ta60gp" role="dialog" aria-modal="true"><div class="modal svelte-ta60gp"><div class="modal-header svelte-ta60gp"><h2 class="svelte-ta60gp">${escape_html(title)}</h2> <button class="close-btn svelte-ta60gp">×</button></div> <div class="modal-body svelte-ta60gp">`);
    if (children) {
      $$renderer.push("<!--[0-->");
      children($$renderer);
      $$renderer.push(`<!---->`);
    } else {
      $$renderer.push("<!--[-1-->");
    }
    $$renderer.push(`<!--]--></div></div></div>`);
  } else {
    $$renderer.push("<!--[-1-->");
  }
  $$renderer.push(`<!--]-->`);
}
export {
  Modal as M
};
