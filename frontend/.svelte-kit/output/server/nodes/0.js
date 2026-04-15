

export const index = 0;
let component_cache;
export const component = async () => component_cache ??= (await import('../entries/pages/_layout.svelte.js')).default;
export const universal = {
  "ssr": false,
  "prerender": false
};
export const universal_id = "src/routes/+layout.ts";
export const imports = ["_app/immutable/nodes/0.C61SVfrX.js","_app/immutable/chunks/BHEwTDFk.js","_app/immutable/chunks/DL_tpWUD.js","_app/immutable/chunks/Bqrx5YoG.js","_app/immutable/chunks/BWKQPg7l.js","_app/immutable/chunks/P8Zv2t_H.js","_app/immutable/chunks/BKBzpOr6.js","_app/immutable/chunks/CkLfrO85.js","_app/immutable/chunks/BRuBuhjp.js","_app/immutable/chunks/Ww28zgKY.js"];
export const stylesheets = ["_app/immutable/assets/0.BwFT-6zR.css"];
export const fonts = [];
