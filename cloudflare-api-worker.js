// Beysnap API trên Cloudflare Workers: miễn phí, luôn bật (không ngủ), IP khác Render.
// Cùng các đường dẫn với bản Render để Phím tắt chỉ cần đổi địa chỉ:
//   /api/v1/info  /api/v1/video  /api/v1/music  /api/v1/image  /api/v1/get  /health
// Thêm /relay: trả nguyên JSON của tikwm, để server Render dùng làm cầu nối (TIKWM_RELAY).
// Biến cần đặt (Settings > Variables and Secrets): API_KEY = khoá bí mật do bạn tự đặt.
// Không có: AI, ZIP, đổi sang JPEG, chất lượng yt-dlp (đã có ở bản Render).

const TW = "https://www.tikwm.com";
const UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36";
const LINK_TTL = 15 * 60; // giây
const enc = new TextEncoder();
const sleep = ms => new Promise(r => setTimeout(r, ms));
const memo = new Map(); // nhớ kết quả vài phút trong cùng một isolate

const json = (obj, status = 200) => new Response(JSON.stringify(obj), {
  status, headers: { "Content-Type": "application/json; charset=utf-8", "Cache-Control": "no-store" },
});

/* ---------- tiện ích ---------- */
async function readParams(req) {
  const p = {};
  for (const [k, v] of new URL(req.url).searchParams) p[k] = v;
  if (req.method === "POST") {
    const ct = req.headers.get("content-type") || "";
    try {
      if (ct.includes("application/json")) Object.assign(p, await req.json());
      else for (const [k, v] of await req.formData()) if (typeof v === "string") p[k] = v;
    } catch { /* bỏ qua body lỗi */ }
  }
  return p;
}
function extractUrl(text) { const m = String(text || "").match(/https?:\/\/[^\s]+/); return m ? m[0] : ""; }
function isTikTok(u) {
  try { const h = new URL(u).hostname.toLowerCase(); return h === "tiktok.com" || h.endsWith(".tiktok.com"); }
  catch { return false; }
}
function safeName(t, fb = "tiktok") {
  const s = String(t || "").replace(/[^\p{L}\p{N}\-_. ]/gu, "").trim().slice(0, 60);
  return (s || fb).replace(/ /g, "_");
}
const fixUrl = u => (u && u.startsWith("/") ? TW + u : u);
function extOf(u, dflt) {
  const m = new URL(u).pathname.toLowerCase().match(/\.(jpe?g|png|webp|heic|avif)$/);
  return m ? m[1].replace("jpeg", "jpg") : dflt;
}
function cd(filename) {
  const ascii = filename.replace(/đ/g, "d").replace(/Đ/g, "D").normalize("NFKD").replace(/[^\x00-\x7F]/g, "")
    .replace(/[^A-Za-z0-9._-]/g, "_");
  return `attachment; filename="${ascii}"; filename*=UTF-8''${encodeURIComponent(filename)}`;
}
const b64u = s => btoa(s).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
const unb64u = s => atob(s.replace(/-/g, "+").replace(/_/g, "/"));
async function hmac(secret, data) {
  const k = await crypto.subtle.importKey("raw", enc.encode(secret), { name: "HMAC", hash: "SHA-256" }, false, ["sign"]);
  const sig = new Uint8Array(await crypto.subtle.sign("HMAC", k, enc.encode(data)));
  return [...sig].map(b => b.toString(16).padStart(2, "0")).join("").slice(0, 32);
}
function sameStr(a, b) { // so sánh không để lộ thời gian
  a = String(a); b = String(b); let d = a.length ^ b.length;
  for (let i = 0; i < Math.max(a.length, b.length); i++) d |= (a.charCodeAt(i) || 0) ^ (b.charCodeAt(i) || 0);
  return d === 0;
}

/* ---------- tikwm ---------- */
function normalize(d) {
  const base = safeName(d.title, d.id || "tiktok");
  const imgs = d.images || [];
  const videos = [];
  if (imgs.length) {
    if (d.play) videos.push({ quality: "slide", url: fixUrl(d.play), filename: `${base}_slideshow.mp4` });
  } else {
    if (d.hdplay) videos.push({ quality: "hd", url: fixUrl(d.hdplay), filename: `${base}_hd.mp4` });
    if (d.play) videos.push({ quality: "sd", url: fixUrl(d.play), filename: `${base}.mp4` });
    if (d.wmplay) videos.push({ quality: "wm", url: fixUrl(d.wmplay), filename: `${base}_watermark.mp4` });
  }
  const audio = d.music ? { url: fixUrl(d.music), filename: `${base}_music.mp3` } : null;
  const images = imgs.map((u, i) => {
    u = fixUrl(u);
    return { index: i + 1, url: u, filename: `${base}_${String(i + 1).padStart(2, "0")}.${extOf(u, "jpg")}` };
  });
  if (!videos.length && !audio && !images.length) throw new Error("Không tìm thấy media");
  return { base, title: d.title || "", author: (d.author && (d.author.nickname || d.author.unique_id)) || "",
           isPhoto: images.length > 0, videos, audio, images };
}
async function tikwmRaw(url) {
  let last = "không rõ";
  for (let i = 0; i < 3; i++) {
    let r;
    try {
      r = await fetch(`${TW}/api/?hd=1&url=${encodeURIComponent(url)}`,
        { headers: { "User-Agent": UA, "Referer": TW + "/", "Accept": "application/json" } });
    } catch { last = "không kết nối được tikwm"; await sleep(500); continue; }
    if (r.status !== 200) { last = `HTTP ${r.status}` + ([403, 429].includes(r.status) ? " (tikwm chặn IP máy chủ)" : ""); continue; }
    let j; try { j = await r.json(); } catch { last = "tikwm trả về trang lạ (có thể chặn IP máy chủ)"; continue; }
    if (j.code === 0 && j.data) return j;
    last = String(j.msg || "tikwm không trả dữ liệu");
    if (/limit/i.test(last)) { await sleep(1500); continue; }
    break;
  }
  throw new Error(last);
}
async function getData(url) {
  const hit = memo.get(url);
  if (hit && hit.exp > Date.now()) return hit.data;
  const data = normalize((await tikwmRaw(url)).data);
  if (memo.size > 200) memo.clear();
  memo.set(url, { exp: Date.now() + 5 * 60e3, data });
  return data;
}
function pickVideos(data, quality) {
  const order = { hd: ["hd", "slide", "sd", "wm"], sd: ["sd", "slide", "hd", "wm"], wm: ["wm", "hd", "slide", "sd"] }[quality] || ["hd", "slide", "sd", "wm"];
  return [...data.videos].sort((a, b) => order.indexOf(a.quality) - order.indexOf(b.quality));
}

/* ---------- tải file ---------- */
async function openUpstream(url) {
  let last = "";
  for (const ref of [TW + "/", "https://www.tiktok.com/", null]) {
    const h = { "User-Agent": UA, "Accept": "*/*" }; if (ref) h.Referer = ref;
    try {
      const r = await fetch(url, { headers: h });
      if (r.status < 400) return { r };
      last = `HTTP ${r.status}`;
    } catch (e) { last = "không kết nối được"; }
  }
  return { err: last };
}
function passThrough(r, filename, ctype) {
  const h = new Headers();
  h.set("Content-Type", ctype || r.headers.get("content-type") || "application/octet-stream");
  const cl = r.headers.get("content-length");
  if (cl && !r.headers.get("content-encoding")) h.set("Content-Length", cl);
  h.set("Content-Disposition", cd(filename)); h.set("Cache-Control", "no-store");
  return new Response(r.body, { status: 200, headers: h });
}
async function streamFirst(cands, ctype) { // cands: [{url, filename}]
  const errs = [];
  for (const c of cands) {
    const { r, err } = await openUpstream(c.url);
    if (r) return passThrough(r, c.filename, ctype);
    errs.push(err);
  }
  return json({ error: `Máy chủ nguồn từ chối hoặc không phản hồi (${errs.join(", ")}). Thử lại sau ít phút.` }, 502);
}
async function signLink(origin, upstream, filename, ctype, secret) {
  const e = Math.floor(Date.now() / 1000) + LINK_TTL, u = b64u(upstream), c = ctype || "";
  const s = await hmac(secret, `${u}|${filename}|${e}|${c}`);
  return `${origin}/dl?u=${u}&n=${encodeURIComponent(filename)}&e=${e}&c=${encodeURIComponent(c)}&s=${s}`;
}

/* ---------- xử lý yêu cầu ---------- */
async function handleDl(url, env) {
  const q = url.searchParams, u = q.get("u") || "", n = q.get("n") || "tiktok", e = q.get("e") || "", c = q.get("c") || "";
  if (!(Number(e) > Date.now() / 1000)) return json({ error: "Link tải đã hết hạn, hãy gọi /api/v1/info lại." }, 410);
  if (!sameStr(await hmac(env.API_KEY, `${u}|${n}|${e}|${c}`), q.get("s") || "")) return json({ error: "Chữ ký không hợp lệ." }, 403);
  return streamFirst([{ url: unb64u(u), filename: n }], c || null);
}

async function handleApi(req, url, env) {
  if (!env.API_KEY) return json({ error: "Chưa đặt biến API_KEY trong Worker." }, 500);
  const p = await readParams(req);
  const given = req.headers.get("x-api-key") || p.key || "";
  if (!sameStr(given, env.API_KEY)) return json({ error: "Sai hoặc thiếu key." }, 401);
  const tk = extractUrl(p.url);
  if (!isTikTok(tk)) return json({ error: "Link TikTok không hợp lệ." }, 400);

  if (url.pathname === "/relay") { // cầu nối cho server Render
    try { return json(await tikwmRaw(tk)); } catch (e) { return json({ code: -1, msg: e.message }, 502); }
  }
  let data;
  try { data = await getData(tk); } catch (e) { return json({ error: `Không lấy được media: ${e.message}` }, 502); }

  const path = url.pathname;
  if (path === "/api/v1/info") {
    const o = url.origin, S = env.API_KEY;
    const out = { title: data.title, author: data.author, type: data.isPhoto ? "photo" : "video",
      image_count: data.images.length, video_best: null, video_hd: null, video_sd: null,
      video_watermark: null, slideshow: null, music: null, images: [], zip: null };
    const keyOf = { hd: "video_hd", sd: "video_sd", wm: "video_watermark", slide: "slideshow" };
    for (const v of data.videos) out[keyOf[v.quality]] = await signLink(o, v.url, v.filename, "video/mp4", S);
    out.video_best = out.video_hd || out.video_sd || out.slideshow;
    if (data.audio) out.music = await signLink(o, data.audio.url, data.audio.filename, "audio/mpeg", S);
    for (const im of data.images) out.images.push(await signLink(o, im.url, im.filename, "", S));
    out.choices = [...(out.video_best ? ["Video"] : []), ...(out.music ? ["Nhạc"] : []), ...data.images.map(i => `Ảnh ${i.index}`)];
    return json(out);
  }

  let kind = path === "/api/v1/video" ? "video" : path === "/api/v1/music" ? "music"
           : path === "/api/v1/image" ? "image" : path === "/api/v1/get" ? (p.type || "auto").toLowerCase() : "";
  if (!kind) return json({ error: "Không có đường dẫn này." }, 404);
  if (kind === "auto") kind = data.isPhoto ? "image" : "video";

  if (kind === "video") {
    const quality = p.quality || (["1", "true"].includes(String(p.wm)) ? "wm" : "hd");
    const c = pickVideos(data, quality);
    if (!c.length) return json({ error: "Bài này không có video." }, 404);
    return streamFirst(c, "video/mp4");
  }
  if (kind === "music") {
    if (!data.audio) return json({ error: "Bài này không có nhạc." }, 404);
    return streamFirst([data.audio], "audio/mpeg");
  }
  if (kind === "image") {
    if (!data.images.length) return json({ error: "Bài này không có ảnh, hãy dùng type=video." }, 404);
    const idx = parseInt(p.index || "1", 10);
    if (!(idx >= 1 && idx <= data.images.length)) return json({ error: `index phải từ 1 đến ${data.images.length}.` }, 400);
    return streamFirst([data.images[idx - 1]], null);
  }
  return json({ error: "type phải là video, music hoặc image." }, 400);
}

export default {
  async fetch(req, env) {
    const url = new URL(req.url);
    try {
      if (url.pathname === "/health") return new Response("ok", { headers: { "Cache-Control": "no-store" } });
      if (url.pathname === "/") return json({ name: "beysnap-api", ok: true });
      if (url.pathname === "/dl") return await handleDl(url, env);
      if (url.pathname.startsWith("/api/v1/") || url.pathname === "/relay") return await handleApi(req, url, env);
      return json({ error: "Không có đường dẫn này." }, 404);
    } catch (e) {
      return json({ error: "Lỗi nội bộ: " + (e && e.message || e) }, 500);
    }
  },
};
