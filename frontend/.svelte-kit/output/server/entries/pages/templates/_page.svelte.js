import { a as attr, e as ensure_array_like, c as escape_html, d as derived } from "../../../chunks/renderer.js";
import { a as auth } from "../../../chunks/auth.svelte.js";
import { R as RISK_LEVELS, M as MarkdownEditor } from "../../../chunks/MarkdownEditor.js";
/* empty css                                                         */
import { M as Modal } from "../../../chunks/Modal.js";
function _page($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let showModal = false;
    let saving = false;
    const canEdit = derived(() => auth.user?.role === "admin" || auth.user?.role === "reviewer");
    let form = {
      stable_id: "",
      name: "",
      category: "",
      title: "",
      description: "",
      risk_level: "medium",
      impact: "",
      recommendation: "",
      references: ""
    };
    let $$settled = true;
    let $$inner_renderer;
    function $$render_inner($$renderer3) {
      $$renderer3.push(`<div class="page-header"><h1>Finding Templates</h1> `);
      if (canEdit()) {
        $$renderer3.push("<!--[0-->");
        $$renderer3.push(`<button class="btn btn-primary">New Template</button>`);
      } else {
        $$renderer3.push("<!--[-1-->");
      }
      $$renderer3.push(`<!--]--></div> `);
      {
        $$renderer3.push("<!--[0-->");
        $$renderer3.push(`<p>Loading...</p>`);
      }
      $$renderer3.push(`<!--]--> `);
      Modal($$renderer3, {
        title: "New Template",
        show: showModal,
        onclose: () => showModal = false,
        children: ($$renderer4) => {
          $$renderer4.push(`<form>`);
          {
            $$renderer4.push("<!--[0-->");
            $$renderer4.push(`<div class="form-group"><label>Stable ID *</label> <input${attr("value", form.stable_id)} required="" placeholder="e.g. custom/my-finding-type"/></div>`);
          }
          $$renderer4.push(`<!--]--> <div class="form-group"><label>Name *</label> <input${attr("value", form.name)} required="" placeholder="e.g. My Custom Finding"/></div> <div class="form-group"><label>Category</label> <input${attr("value", form.category)} placeholder="e.g. custom, injection, authentication"/></div> <div class="form-group"><label>Finding Title</label> <input${attr("value", form.title)} placeholder="Default title when applied"/></div> <div class="form-group"><label>Risk Level</label> `);
          $$renderer4.select({ value: form.risk_level }, ($$renderer5) => {
            $$renderer5.push(`<!--[-->`);
            const each_array_3 = ensure_array_like(RISK_LEVELS);
            for (let $$index_3 = 0, $$length = each_array_3.length; $$index_3 < $$length; $$index_3++) {
              let r = each_array_3[$$index_3];
              $$renderer5.option({ value: r }, ($$renderer6) => {
                $$renderer6.push(`${escape_html(r)}`);
              });
            }
            $$renderer5.push(`<!--]-->`);
          });
          $$renderer4.push(`</div> `);
          MarkdownEditor($$renderer4, {
            label: "Description (Markdown)",
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
          $$renderer4.push(`<!----> <div class="form-group"><label>References (one per line)</label> <textarea placeholder="CWE-79 https://owasp.org/...">`);
          const $$body = escape_html(form.references);
          if ($$body) {
            $$renderer4.push(`${$$body}`);
          }
          $$renderer4.push(`</textarea></div> <div style="display:flex;gap:0.5rem;justify-content:flex-end;"><button class="btn btn-secondary" type="button">Cancel</button> <button class="btn btn-primary" type="submit"${attr("disabled", saving, true)}>${escape_html("Create Template")}</button></div></form>`);
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
