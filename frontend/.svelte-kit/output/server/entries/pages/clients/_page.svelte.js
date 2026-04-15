import { d as derived, a as attr, c as escape_html } from "../../../chunks/renderer.js";
import { a as auth } from "../../../chunks/auth.svelte.js";
import { M as Modal } from "../../../chunks/Modal.js";
/* empty css                                                       */
function _page($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let showModal = false;
    let form = {
      company_name: "",
      primary_contact_name: "",
      primary_contact_email: ""
    };
    let saving = false;
    const canEdit = derived(() => auth.user?.role === "admin" || auth.user?.role === "reviewer");
    $$renderer2.push(`<div class="page-header"><h1>Clients</h1> `);
    if (canEdit()) {
      $$renderer2.push("<!--[0-->");
      $$renderer2.push(`<button class="btn btn-primary">New Client</button>`);
    } else {
      $$renderer2.push("<!--[-1-->");
    }
    $$renderer2.push(`<!--]--></div> <div class="card">`);
    {
      $$renderer2.push("<!--[0-->");
      $$renderer2.push(`<p>Loading...</p>`);
    }
    $$renderer2.push(`<!--]--></div> `);
    Modal($$renderer2, {
      title: "New Client",
      show: showModal,
      onclose: () => showModal = false,
      children: ($$renderer3) => {
        {
          $$renderer3.push("<!--[-1-->");
        }
        $$renderer3.push(`<!--]--> <form><div class="form-group"><label for="company_name">Company Name *</label> <input id="company_name"${attr("value", form.company_name)} required=""/></div> <div class="form-group"><label for="contact_name">Primary Contact Name</label> <input id="contact_name"${attr("value", form.primary_contact_name)}/></div> <div class="form-group"><label for="contact_email">Primary Contact Email</label> <input id="contact_email" type="email"${attr("value", form.primary_contact_email)}/></div> <div style="display:flex;gap:0.5rem;justify-content:flex-end;"><button class="btn btn-secondary" type="button">Cancel</button> <button class="btn btn-primary" type="submit"${attr("disabled", saving, true)}>${escape_html("Create Client")}</button></div></form>`);
      }
    });
    $$renderer2.push(`<!---->`);
  });
}
export {
  _page as default
};
