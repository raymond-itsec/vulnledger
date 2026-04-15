import { e as ensure_array_like, c as escape_html } from "../../../chunks/renderer.js";
import { a as api } from "../../../chunks/client2.js";
/* empty css                                                       */
const SESSION_STATUSES = ["planned", "in_progress", "completed", "cancelled"];
const sessionsApi = {
  list: (assetId, page = 1, perPage = 25) => {
    const qs = new URLSearchParams({ page: String(page), per_page: String(perPage) });
    if (assetId) qs.set("asset_id", assetId);
    return api.get(`/api/sessions?${qs}`);
  },
  get: (id) => api.get(`/api/sessions/${id}`),
  create: (data) => api.post("/api/sessions", data),
  update: (id, data) => api.patch(`/api/sessions/${id}`, data)
};
function _page($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let filterStatus = "";
    async function load(p = 1) {
      const res = await sessionsApi.list(void 0, p);
      res.items;
      res.page;
      res.pages;
      res.total;
    }
    $$renderer2.push(`<div class="page-header"><h1>Review Sessions</h1></div> <div class="filters">`);
    $$renderer2.select({ value: filterStatus, onchange: () => load(1) }, ($$renderer3) => {
      $$renderer3.option({ value: "" }, ($$renderer4) => {
        $$renderer4.push(`All Statuses`);
      });
      $$renderer3.push(`<!--[-->`);
      const each_array = ensure_array_like(SESSION_STATUSES);
      for (let $$index = 0, $$length = each_array.length; $$index < $$length; $$index++) {
        let s = each_array[$$index];
        $$renderer3.option({ value: s }, ($$renderer4) => {
          $$renderer4.push(`${escape_html(s.replace("_", " "))}`);
        });
      }
      $$renderer3.push(`<!--]-->`);
    });
    $$renderer2.push(`</div> <div class="card">`);
    {
      $$renderer2.push("<!--[0-->");
      $$renderer2.push(`<p>Loading...</p>`);
    }
    $$renderer2.push(`<!--]--></div>`);
  });
}
export {
  _page as default
};
