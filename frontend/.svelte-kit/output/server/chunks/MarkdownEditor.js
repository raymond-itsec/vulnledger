import { a as api } from "./client2.js";
import { c as escape_html, b as attr_class, a as attr, a3 as attr_style, a4 as bind_props, a5 as stringify } from "./renderer.js";
/* empty css                                           */
/* empty css                                             */
const RISK_LEVELS = ["critical", "high", "medium", "low", "informational"];
const REMEDIATION_STATUSES = ["open", "in_progress", "resolved", "accepted_risk", "false_positive"];
const findingsApi = {
  list: (params) => {
    const qs = new URLSearchParams();
    if (params?.session_id) qs.set("session_id", params.session_id);
    if (params?.risk_level) qs.set("risk_level", params.risk_level);
    if (params?.remediation_status) qs.set("remediation_status", params.remediation_status);
    if (params?.search) qs.set("search", params.search);
    qs.set("page", String(params?.page || 1));
    qs.set("per_page", String(params?.per_page || 25));
    return api.get(`/api/findings?${qs}`);
  },
  get: (id) => api.get(`/api/findings/${id}`),
  create: (data) => api.post("/api/findings", data),
  update: (id, data) => api.patch(`/api/findings/${id}`, data),
  history: (id) => api.get(`/api/findings/${id}/history`)
};
function MarkdownEditor($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let {
      value = "",
      label = "",
      required = false,
      minHeight = "120px"
    } = $$props;
    let showPreview = false;
    $$renderer2.push(`<div class="md-editor svelte-1wy3hso">`);
    if (label) {
      $$renderer2.push("<!--[0-->");
      $$renderer2.push(`<div class="md-header svelte-1wy3hso"><label class="svelte-1wy3hso">${escape_html(label)}</label> <div class="md-tabs svelte-1wy3hso"><button type="button"${attr_class("tab svelte-1wy3hso", void 0, { "active": !showPreview })}>Write</button> <button type="button"${attr_class("tab svelte-1wy3hso", void 0, { "active": showPreview })}>Preview</button></div></div>`);
    } else {
      $$renderer2.push("<!--[-1-->");
    }
    $$renderer2.push(`<!--]--> `);
    {
      $$renderer2.push("<!--[-1-->");
      $$renderer2.push(`<textarea${attr("required", required, true)}${attr_style(`min-height: ${stringify(minHeight)};`)} placeholder="Supports Markdown: **bold**, *italic*, \`code\`, [links](url), lists..." class="svelte-1wy3hso">`);
      const $$body = escape_html(value);
      if ($$body) {
        $$renderer2.push(`${$$body}`);
      }
      $$renderer2.push(`</textarea>`);
    }
    $$renderer2.push(`<!--]--></div>`);
    bind_props($$props, { value });
  });
}
export {
  MarkdownEditor as M,
  RISK_LEVELS as R,
  REMEDIATION_STATUSES as a,
  findingsApi as f
};
