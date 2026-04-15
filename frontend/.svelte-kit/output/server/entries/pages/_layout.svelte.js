import { e as ensure_array_like, a as attr, b as attr_class, c as escape_html, d as derived } from "../../chunks/renderer.js";
import { a as auth } from "../../chunks/auth.svelte.js";
import { p as page } from "../../chunks/index.js";
function _layout($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let { children } = $$props;
    const navItems = [
      { href: "/", label: "Dashboard", icon: "⊞" },
      { href: "/clients", label: "Clients", icon: "⊟" },
      { href: "/assets", label: "Assets", icon: "⊠" },
      { href: "/sessions", label: "Sessions", icon: "⊡" },
      { href: "/findings", label: "Findings", icon: "⊘" },
      {
        href: "/templates",
        label: "Templates",
        icon: "⊙",
        roles: ["admin", "reviewer"]
      }
    ];
    let visibleNav = derived(() => navItems.filter((item) => {
      if (!item.roles) return true;
      return auth.user && item.roles.includes(auth.user.role);
    }));
    function isActive(href, currentPath) {
      if (href === "/") return currentPath === "/";
      return currentPath.startsWith(href);
    }
    if (!auth.isAuthenticated) {
      $$renderer2.push("<!--[0-->");
      children($$renderer2);
      $$renderer2.push(`<!---->`);
    } else {
      $$renderer2.push("<!--[-1-->");
      $$renderer2.push(`<div class="app-layout svelte-12qhfyh"><aside class="sidebar svelte-12qhfyh"><div class="sidebar-header svelte-12qhfyh"><h1 class="svelte-12qhfyh">Findings</h1> <span class="version svelte-12qhfyh">v0.1</span></div> <nav class="svelte-12qhfyh"><!--[-->`);
      const each_array = ensure_array_like(visibleNav());
      for (let $$index = 0, $$length = each_array.length; $$index < $$length; $$index++) {
        let item = each_array[$$index];
        $$renderer2.push(`<a${attr("href", item.href)}${attr_class("nav-item svelte-12qhfyh", void 0, { "active": isActive(item.href, page.url.pathname) })}><span class="nav-icon svelte-12qhfyh">${escape_html(item.icon)}</span> ${escape_html(item.label)}</a>`);
      }
      $$renderer2.push(`<!--]--></nav> <div class="sidebar-footer svelte-12qhfyh"><div class="user-info svelte-12qhfyh"><div class="user-name svelte-12qhfyh">${escape_html(auth.user?.full_name || auth.user?.username)}</div> <div class="user-role svelte-12qhfyh">${escape_html(auth.user?.role?.replace("_", " "))}</div></div> <button class="logout-btn svelte-12qhfyh">Logout</button></div></aside> <main class="content svelte-12qhfyh">`);
      children($$renderer2);
      $$renderer2.push(`<!----></main></div>`);
    }
    $$renderer2.push(`<!--]-->`);
  });
}
export {
  _layout as default
};
