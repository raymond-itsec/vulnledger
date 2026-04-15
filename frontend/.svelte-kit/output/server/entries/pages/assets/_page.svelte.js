import { e as ensure_array_like, c as escape_html, d as derived, a as attr } from "../../../chunks/renderer.js";
import { a as api } from "../../../chunks/client2.js";
import { a as auth } from "../../../chunks/auth.svelte.js";
import { M as Modal } from "../../../chunks/Modal.js";
/* empty css                                                       */
const ASSET_TYPES = [
  { value: "repository", label: "Source Code Repository" },
  { value: "browser_extension", label: "Browser Extension" },
  { value: "web_application", label: "Web Application" },
  { value: "api", label: "API" },
  { value: "mobile_app", label: "Mobile App" },
  { value: "other", label: "Other" }
];
const assetsApi = {
  list: (clientId, page = 1, perPage = 25) => {
    const qs = new URLSearchParams({ page: String(page), per_page: String(perPage) });
    if (clientId) qs.set("client_id", clientId);
    return api.get(`/api/assets?${qs}`);
  },
  get: (id) => api.get(`/api/assets/${id}`),
  create: (data) => api.post("/api/assets", data),
  update: (id, data) => api.patch(`/api/assets/${id}`, data)
};
function _page($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let clients = [];
    let filterClient = "";
    let showModal = false;
    let form = {
      client_id: "",
      asset_name: "",
      asset_type: "web_application",
      description: ""
    };
    let saving = false;
    const canEdit = derived(() => auth.user?.role === "admin" || auth.user?.role === "reviewer");
    async function load(p = 1) {
      const res = await assetsApi.list(void 0, p);
      res.items;
      res.page;
      res.pages;
      res.total;
    }
    $$renderer2.push(`<div class="page-header"><h1>Reviewed Assets</h1> `);
    if (canEdit()) {
      $$renderer2.push("<!--[0-->");
      $$renderer2.push(`<button class="btn btn-primary">New Asset</button>`);
    } else {
      $$renderer2.push("<!--[-1-->");
    }
    $$renderer2.push(`<!--]--></div> <div class="filters">`);
    $$renderer2.select({ value: filterClient, onchange: () => load(1) }, ($$renderer3) => {
      $$renderer3.option({ value: "" }, ($$renderer4) => {
        $$renderer4.push(`All Clients`);
      });
      $$renderer3.push(`<!--[-->`);
      const each_array = ensure_array_like(clients);
      for (let $$index = 0, $$length = each_array.length; $$index < $$length; $$index++) {
        let c = each_array[$$index];
        $$renderer3.option({ value: c.client_id }, ($$renderer4) => {
          $$renderer4.push(`${escape_html(c.company_name)}`);
        });
      }
      $$renderer3.push(`<!--]-->`);
    });
    $$renderer2.push(`</div> <div class="card">`);
    {
      $$renderer2.push("<!--[0-->");
      $$renderer2.push(`<p>Loading...</p>`);
    }
    $$renderer2.push(`<!--]--></div> `);
    Modal($$renderer2, {
      title: "New Asset",
      show: showModal,
      onclose: () => showModal = false,
      children: ($$renderer3) => {
        $$renderer3.push(`<form><div class="form-group"><label>Client *</label> `);
        $$renderer3.select({ value: form.client_id, required: true }, ($$renderer4) => {
          $$renderer4.option({ value: "", disabled: true }, ($$renderer5) => {
            $$renderer5.push(`Select client`);
          });
          $$renderer4.push(`<!--[-->`);
          const each_array_2 = ensure_array_like(clients);
          for (let $$index_2 = 0, $$length = each_array_2.length; $$index_2 < $$length; $$index_2++) {
            let c = each_array_2[$$index_2];
            $$renderer4.option({ value: c.client_id }, ($$renderer5) => {
              $$renderer5.push(`${escape_html(c.company_name)}`);
            });
          }
          $$renderer4.push(`<!--]-->`);
        });
        $$renderer3.push(`</div> <div class="form-group"><label>Asset Name *</label> <input${attr("value", form.asset_name)} required=""/></div> <div class="form-group"><label>Type</label> `);
        $$renderer3.select({ value: form.asset_type }, ($$renderer4) => {
          $$renderer4.push(`<!--[-->`);
          const each_array_3 = ensure_array_like(ASSET_TYPES);
          for (let $$index_3 = 0, $$length = each_array_3.length; $$index_3 < $$length; $$index_3++) {
            let t = each_array_3[$$index_3];
            $$renderer4.option({ value: t.value }, ($$renderer5) => {
              $$renderer5.push(`${escape_html(t.label)}`);
            });
          }
          $$renderer4.push(`<!--]-->`);
        });
        $$renderer3.push(`</div> <div class="form-group"><label>Description</label> <textarea>`);
        const $$body = escape_html(form.description);
        if ($$body) {
          $$renderer3.push(`${$$body}`);
        }
        $$renderer3.push(`</textarea></div> <div style="display:flex;gap:0.5rem;justify-content:flex-end;"><button class="btn btn-secondary" type="button">Cancel</button> <button class="btn btn-primary" type="submit"${attr("disabled", saving, true)}>Create</button></div></form>`);
      }
    });
    $$renderer2.push(`<!---->`);
  });
}
export {
  _page as default
};
