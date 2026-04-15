import { a as attr, e as ensure_array_like, c as escape_html, d as derived } from "../../../chunks/renderer.js";
import "../../../chunks/client.js";
import { R as RISK_LEVELS, a as REMEDIATION_STATUSES, M as MarkdownEditor, f as findingsApi } from "../../../chunks/MarkdownEditor.js";
import { a as auth } from "../../../chunks/auth.svelte.js";
import { M as Modal } from "../../../chunks/Modal.js";
/* empty css                                                       */
function _page($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let sessions = [];
    let templates = [];
    let filterRisk = "";
    let filterStatus = "";
    let searchText = "";
    let showModal = false;
    let saving = false;
    let form = {
      session_id: "",
      title: "",
      description: "",
      risk_level: "medium",
      impact: "",
      recommendation: "",
      remediation_status: "open",
      references: ""
    };
    const canEdit = derived(() => auth.user?.role === "admin" || auth.user?.role === "reviewer");
    async function loadFindings(p = 1) {
      const params = { page: p, per_page: 25 };
      const res = await findingsApi.list(params);
      res.items;
      res.page;
      res.pages;
      res.total;
    }
    function onFilterChange() {
      loadFindings(1);
    }
    let $$settled = true;
    let $$inner_renderer;
    function $$render_inner($$renderer3) {
      $$renderer3.push(`<div class="page-header"><h1>Findings</h1> `);
      if (canEdit()) {
        $$renderer3.push("<!--[0-->");
        $$renderer3.push(`<button class="btn btn-primary">New Finding</button>`);
      } else {
        $$renderer3.push("<!--[-1-->");
      }
      $$renderer3.push(`<!--]--></div> <div class="filters"><input type="text" placeholder="Search title or description..."${attr("value", searchText)} style="min-width:250px;"/> `);
      $$renderer3.select({ value: filterRisk, onchange: onFilterChange }, ($$renderer4) => {
        $$renderer4.option({ value: "" }, ($$renderer5) => {
          $$renderer5.push(`All Risk Levels`);
        });
        $$renderer4.push(`<!--[-->`);
        const each_array = ensure_array_like(RISK_LEVELS);
        for (let $$index = 0, $$length = each_array.length; $$index < $$length; $$index++) {
          let r = each_array[$$index];
          $$renderer4.option({ value: r }, ($$renderer5) => {
            $$renderer5.push(`${escape_html(r)}`);
          });
        }
        $$renderer4.push(`<!--]-->`);
      });
      $$renderer3.push(` `);
      $$renderer3.select({ value: filterStatus, onchange: onFilterChange }, ($$renderer4) => {
        $$renderer4.option({ value: "" }, ($$renderer5) => {
          $$renderer5.push(`All Statuses`);
        });
        $$renderer4.push(`<!--[-->`);
        const each_array_1 = ensure_array_like(REMEDIATION_STATUSES);
        for (let $$index_1 = 0, $$length = each_array_1.length; $$index_1 < $$length; $$index_1++) {
          let s = each_array_1[$$index_1];
          $$renderer4.option({ value: s }, ($$renderer5) => {
            $$renderer5.push(`${escape_html(s.replace("_", " "))}`);
          });
        }
        $$renderer4.push(`<!--]-->`);
      });
      $$renderer3.push(`</div> <div class="card">`);
      {
        $$renderer3.push("<!--[0-->");
        $$renderer3.push(`<p>Loading...</p>`);
      }
      $$renderer3.push(`<!--]--></div> `);
      Modal($$renderer3, {
        title: "New Finding",
        show: showModal,
        onclose: () => showModal = false,
        children: ($$renderer4) => {
          $$renderer4.push(`<form>`);
          if (templates.length > 0) {
            $$renderer4.push("<!--[0-->");
            $$renderer4.push(`<div class="form-group"><label>From Template (optional)</label> <select>`);
            $$renderer4.option({ value: "" }, ($$renderer5) => {
              $$renderer5.push(`— Select a template —`);
            });
            $$renderer4.push(`<!--[-->`);
            const each_array_3 = ensure_array_like(templates);
            for (let $$index_3 = 0, $$length = each_array_3.length; $$index_3 < $$length; $$index_3++) {
              let t = each_array_3[$$index_3];
              $$renderer4.option({ value: t.template_id }, ($$renderer5) => {
                $$renderer5.push(`[${escape_html(t.category)}] ${escape_html(t.name)}`);
              });
            }
            $$renderer4.push(`<!--]--></select></div>`);
          } else {
            $$renderer4.push("<!--[-1-->");
          }
          $$renderer4.push(`<!--]--> <div class="form-group"><label>Session *</label> `);
          $$renderer4.select({ value: form.session_id, required: true }, ($$renderer5) => {
            $$renderer5.option({ value: "", disabled: true }, ($$renderer6) => {
              $$renderer6.push(`Select session`);
            });
            $$renderer5.push(`<!--[-->`);
            const each_array_4 = ensure_array_like(sessions);
            for (let $$index_4 = 0, $$length = each_array_4.length; $$index_4 < $$length; $$index_4++) {
              let s = each_array_4[$$index_4];
              $$renderer5.option({ value: s.session_id }, ($$renderer6) => {
                $$renderer6.push(`${escape_html(s.review_name)}`);
              });
            }
            $$renderer5.push(`<!--]-->`);
          });
          $$renderer4.push(`</div> <div class="form-group"><label>Title *</label> <input${attr("value", form.title)} required=""/></div> <div class="form-group"><label>Risk Level *</label> `);
          $$renderer4.select({ value: form.risk_level }, ($$renderer5) => {
            $$renderer5.push(`<!--[-->`);
            const each_array_5 = ensure_array_like(RISK_LEVELS);
            for (let $$index_5 = 0, $$length = each_array_5.length; $$index_5 < $$length; $$index_5++) {
              let r = each_array_5[$$index_5];
              $$renderer5.option({ value: r }, ($$renderer6) => {
                $$renderer6.push(`${escape_html(r)}`);
              });
            }
            $$renderer5.push(`<!--]-->`);
          });
          $$renderer4.push(`</div> `);
          MarkdownEditor($$renderer4, {
            label: "Description * (Markdown)",
            required: true,
            get value() {
              return form.description;
            },
            set value($$value) {
              form.description = $$value;
              $$settled = false;
            }
          });
          $$renderer4.push(`<!----> `);
          MarkdownEditor($$renderer4, {
            label: "Impact (Markdown)",
            get value() {
              return form.impact;
            },
            set value($$value) {
              form.impact = $$value;
              $$settled = false;
            }
          });
          $$renderer4.push(`<!----> `);
          MarkdownEditor($$renderer4, {
            label: "Recommendation (Markdown)",
            get value() {
              return form.recommendation;
            },
            set value($$value) {
              form.recommendation = $$value;
              $$settled = false;
            }
          });
          $$renderer4.push(`<!----> <div class="form-group"><label>Remediation Status</label> `);
          $$renderer4.select({ value: form.remediation_status }, ($$renderer5) => {
            $$renderer5.push(`<!--[-->`);
            const each_array_6 = ensure_array_like(REMEDIATION_STATUSES);
            for (let $$index_6 = 0, $$length = each_array_6.length; $$index_6 < $$length; $$index_6++) {
              let s = each_array_6[$$index_6];
              $$renderer5.option({ value: s }, ($$renderer6) => {
                $$renderer6.push(`${escape_html(s.replace("_", " "))}`);
              });
            }
            $$renderer5.push(`<!--]-->`);
          });
          $$renderer4.push(`</div> <div class="form-group"><label>References (one per line)</label> <textarea placeholder="CWE-79 https://owasp.org/...">`);
          const $$body = escape_html(form.references);
          if ($$body) {
            $$renderer4.push(`${$$body}`);
          }
          $$renderer4.push(`</textarea></div> <div style="display:flex;gap:0.5rem;justify-content:flex-end;"><button class="btn btn-secondary" type="button">Cancel</button> <button class="btn btn-primary" type="submit"${attr("disabled", saving, true)}>${escape_html("Create Finding")}</button></div></form>`);
        }
      });
      $$renderer3.push(`<!---->`);
    }
    do {
      $$settled = true;
      $$inner_renderer = $$renderer2.copy();
      $$render_inner($$inner_renderer);
    } while (!$$settled);
    $$renderer2.subsume($$inner_renderer);
  });
}
export {
  _page as default
};
