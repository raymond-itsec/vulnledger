import { a as attr, c as escape_html, d as derived } from "../../chunks/renderer.js";
import { a as auth } from "../../chunks/auth.svelte.js";
function _page($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let username = "";
    let password = "";
    let loggingIn = false;
    const canEdit = derived(() => auth.user?.role === "admin" || auth.user?.role === "reviewer");
    if (!auth.isAuthenticated) {
      $$renderer2.push("<!--[0-->");
      $$renderer2.push(`<div class="login-page svelte-1uha8ag"><div class="login-card svelte-1uha8ag"><h1 class="svelte-1uha8ag">Security Findings Manager</h1> <p class="subtitle svelte-1uha8ag">Sign in to continue</p> `);
      {
        $$renderer2.push("<!--[-1-->");
      }
      $$renderer2.push(`<!--]--> <form><div class="form-group"><label for="username">Username</label> <input id="username" type="text"${attr("value", username)} required="" autocomplete="username"/></div> <div class="form-group"><label for="password">Password</label> <input id="password" type="password"${attr("value", password)} required="" autocomplete="current-password"/></div> <button class="btn btn-primary login-btn svelte-1uha8ag" type="submit"${attr("disabled", loggingIn, true)}>${escape_html("Sign In")}</button></form> `);
      {
        $$renderer2.push("<!--[-1-->");
      }
      $$renderer2.push(`<!--]--></div></div>`);
    } else {
      $$renderer2.push("<!--[-1-->");
      $$renderer2.push(`<div class="page-header"><h1>Dashboard</h1> `);
      if (canEdit()) {
        $$renderer2.push("<!--[0-->");
        $$renderer2.push(`<div style="display:flex;gap:0.5rem;"><a href="/clients" class="btn btn-secondary btn-sm">New Client</a> <a href="/findings?new=1" class="btn btn-primary btn-sm">New Finding</a></div>`);
      } else {
        $$renderer2.push("<!--[-1-->");
      }
      $$renderer2.push(`<!--]--></div> `);
      {
        $$renderer2.push("<!--[0-->");
        $$renderer2.push(`<p>Loading...</p>`);
      }
      $$renderer2.push(`<!--]-->`);
    }
    $$renderer2.push(`<!--]-->`);
  });
}
export {
  _page as default
};
