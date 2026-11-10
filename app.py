"""
TikTok Downloader - dán link, tải video/ảnh/nhạc, có hoặc không watermark.
Có chọn chất lượng cao nhất (độ phân giải thật từ nguồn) và tùy chọn upscale 4K bằng ffmpeg.
Chạy: python app.py  ->  mở http://127.0.0.1:5000
"""
import hmac
import os
import re
import secrets
import shutil
import subprocess
import tempfile
import time
import unicodedata
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import quote, urlparse

import requests
from flask import (Flask, Response, jsonify, redirect, request, send_file,
                   send_from_directory, stream_with_context)

try:
    import yt_dlp
except ImportError:  # yt-dlp là phương án bổ sung, không bắt buộc
    yt_dlp = None

app = Flask(__name__)
# Sau proxy của Render/Koyeb/Cloud Run: nhận đúng https và tên miền để tạo link tuyệt đối
from werkzeug.middleware.proxy_fix import ProxyFix  # noqa: E402
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)
ALLOWED_HOSTS = ("tiktok.com", "vm.tiktok.com", "vt.tiktok.com")
TOKEN_TTL = 15 * 60  # link tải hết hạn sau 15 phút
_tokens = {}  # token -> dict(mode, url, filename, ..., exp)


# ---------- tiện ích ----------
def is_tiktok_url(url: str) -> bool:
    try:
        host = (urlparse(url).hostname or "").lower()
    except ValueError:
        return False
    return any(host == h or host.endswith("." + h) for h in ALLOWED_HOSTS)


def safe_name(text: str, fallback: str = "tiktok") -> str:
    text = re.sub(r"[^\w\-. ]", "", text or "", flags=re.UNICODE).strip()
    return (text[:60] or fallback).replace(" ", "_")


def make_token(filename: str, **extra) -> str:
    now = time.time()
    for t in [t for t, v in _tokens.items() if v["exp"] < now]:
        _tokens.pop(t, None)
    token = secrets.token_urlsafe(16)
    _tokens[token] = {"filename": filename, "exp": now + TOKEN_TTL, **extra}
    return token


def fix_url(u: str) -> str:
    if u and u.startswith("/"):
        return "https://www.tikwm.com" + u
    return u


def codec_label(vcodec: str) -> str:
    v = (vcodec or "").lower()
    if v.startswith(("h264", "avc")):
        return "H.264"
    if v.startswith(("bytevc1", "hev", "hvc", "h265")):
        return "H.265"
    return v.split(".")[0] or "?"


# ---------- nguồn 1: tikwm (hỗ trợ cả ảnh slideshow) ----------
def fetch_tikwm(url: str):
    r = requests.get(
        "https://www.tikwm.com/api/",
        params={"url": url, "hd": 1},
        headers={"User-Agent": UA},
        timeout=20,
    )
    r.raise_for_status()
    j = r.json()
    if j.get("code") != 0 or not j.get("data"):
        raise RuntimeError(j.get("msg") or "tikwm không trả dữ liệu")
    d = j["data"]
    base = safe_name(d.get("title"), d.get("id", "tiktok"))
    items = []

    images = d.get("images") or []
    if images:
        for i, img in enumerate(images, 1):
            items.append({"label": f"Ảnh {i}", "kind": "image", "ext": "jpg",
                          "url": fix_url(img), "filename": f"{base}_{i}.jpg"})
    else:
        if d.get("hdplay"):
            items.append({"label": "Video HD - không watermark", "kind": "video", "ext": "mp4",
                          "url": fix_url(d["hdplay"]), "filename": f"{base}_hd.mp4", "clean": True})
        if d.get("play"):
            items.append({"label": "Video - không watermark", "kind": "video", "ext": "mp4",
                          "url": fix_url(d["play"]), "filename": f"{base}.mp4", "clean": True})
        if d.get("wmplay"):
            items.append({"label": "Video - có watermark", "kind": "video", "ext": "mp4",
                          "url": fix_url(d["wmplay"]), "filename": f"{base}_watermark.mp4"})
    if d.get("music"):
        items.append({"label": "Nhạc nền (MP3)", "kind": "audio", "ext": "mp3",
                      "url": fix_url(d["music"]), "filename": f"{base}_music.mp3"})

    if not items:
        raise RuntimeError("Không tìm thấy media")
    author = (d.get("author") or {})
    return {
        "base": base,
        "title": d.get("title") or "",
        "author": author.get("nickname") or author.get("unique_id") or "",
        "cover": fix_url(d.get("cover") or ""),
        "items": items,
    }


# ---------- nguồn 2: yt-dlp (liệt kê độ phân giải thật) ----------
def fetch_ytdlp(url: str):
    if yt_dlp is None:
        raise RuntimeError("Chưa cài yt-dlp")
    with yt_dlp.YoutubeDL({"quiet": True, "skip_download": True, "noplaylist": True}) as ydl:
        info = ydl.extract_info(url, download=False)

    base = safe_name(info.get("title"), info.get("id", "tiktok"))
    fmts = [f for f in info.get("formats", [])
            if f.get("vcodec") not in (None, "none") and f.get("url") and f.get("format_id")]
    if not fmts:
        raise RuntimeError("yt-dlp không tìm thấy video (có thể là bài ảnh)")

    clean = [f for f in fmts if f.get("format_id") != "download"]  # "download" = có watermark
    wm = [f for f in fmts if f.get("format_id") == "download"]
    clean.sort(key=lambda f: (f.get("height") or 0, f.get("tbr") or 0), reverse=True)

    items, seen = [], set()
    for f in clean:
        h, codec = f.get("height") or 0, codec_label(f.get("vcodec"))
        if (h, codec) in seen or len(items) >= 4:
            continue
        seen.add((h, codec))
        size = f.get("filesize") or f.get("filesize_approx")
        label = f"{h}p {codec}" if h else f"Video {codec}"
        if size:
            label += f" · {size / 1048576:.0f} MB"
        items.append({"label": label + " - không watermark", "kind": "video", "ext": "mp4",
                      "mode": "ytdlp", "format_id": f["format_id"], "page": url,
                      "filename": f"{base}_{h or 'best'}p_{codec.replace('.', '')}.mp4",
                      "height": h})
    if items:
        items[0]["label"] = "★ Chất lượng cao nhất: " + items[0]["label"]
    if wm:
        items.append({"label": "Video - có watermark", "kind": "video", "ext": "mp4",
                      "mode": "ytdlp", "format_id": wm[0]["format_id"], "page": url,
                      "filename": f"{base}_watermark.mp4", "wm": True})
    return {
        "base": base,
        "title": info.get("title") or "",
        "author": info.get("uploader") or "",
        "cover": info.get("thumbnail") or "",
        "items": items,
    }


# ---------- tải từ nguồn ----------
def open_upstream(url: str):
    """Mở kết nối tới file media, thử vài kiểu Referer. Trả về (response, lỗi)."""
    host = (urlparse(url).hostname or "").lower()
    first = "https://www.tikwm.com/" if host.endswith("tikwm.com") else "https://www.tiktok.com/"
    last_err = None
    for ref in dict.fromkeys([first, "https://www.tiktok.com/", None]):
        headers = {"User-Agent": UA, "Accept": "*/*", "Accept-Encoding": "identity"}
        if ref:
            headers["Referer"] = ref
        try:
            r = requests.get(url, stream=True, timeout=(10, 60), headers=headers)
            if r.status_code < 400:
                return r, None
            last_err = f"HTTP {r.status_code}"
            r.close()
        except requests.RequestException as e:
            last_err = f"{type(e).__name__}: {e}"
    return None, last_err


def send_temp(path: str, tmpdir: str, filename: str):
    resp = send_file(path, as_attachment=True, download_name=filename, mimetype="video/mp4")
    resp.call_on_close(lambda: shutil.rmtree(tmpdir, ignore_errors=True))
    return resp


def download_ytdlp(entry):
    if yt_dlp is None:
        raise RuntimeError("Chưa cài yt-dlp")
    tmp = tempfile.mkdtemp(prefix="ttdl_")
    try:
        opts = {"quiet": True, "noplaylist": True, "format": entry["format_id"],
                "outtmpl": os.path.join(tmp, "v.%(ext)s")}
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([entry["page"]])
        files = os.listdir(tmp)
        if not files:
            raise RuntimeError("yt-dlp không tạo ra file")
        return send_temp(os.path.join(tmp, files[0]), tmp, entry["filename"])
    except Exception:
        shutil.rmtree(tmp, ignore_errors=True)
        raise


def upscale_4k(entry):
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("Máy chưa cài ffmpeg")
    tmp = tempfile.mkdtemp(prefix="ttup_")
    try:
        src, out = os.path.join(tmp, "src.mp4"), os.path.join(tmp, "out.mp4")
        up, err = open_upstream(entry["url"])
        if up is None:
            raise RuntimeError(f"Không tải được video gốc ({err})")
        with open(src, "wb") as fh:
            for chunk in up.iter_content(65536):
                fh.write(chunk)
        # cạnh ngắn = 2160 (dọc: 2160x3840, ngang: 3840x2160)
        vf = ("scale='if(gt(iw,ih),-2,2160)':'if(gt(iw,ih),2160,-2)':flags=lanczos,"
              "unsharp=5:5:0.5")
        cmd = [ffmpeg, "-y", "-i", src, "-vf", vf, "-c:v", "libx264", "-preset", "veryfast",
               "-crf", "17", "-pix_fmt", "yuv420p", "-c:a", "copy", "-movflags", "+faststart", out]
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=1200)
        if p.returncode != 0:
            raise RuntimeError("ffmpeg lỗi: " + p.stderr[-300:])
        return send_temp(out, tmp, entry["filename"])
    except Exception:
        shutil.rmtree(tmp, ignore_errors=True)
        raise


def proxy_direct(entry):
    upstream, err = open_upstream(entry["url"])
    if upstream is None:
        app.logger.warning("Tải thất bại: %s | %s", err, entry["url"][:120])
        return jsonify(error=f"Máy chủ nguồn từ chối hoặc không phản hồi ({err}). "
                             "Hãy bấm Tải lại để lấy link mới."), 502

    filename = entry["filename"]
    # Header chỉ nhận latin-1: tên ASCII + filename* (UTF-8) cho tên có dấu
    ascii_name = unicodedata.normalize("NFKD", filename.replace("đ", "d").replace("Đ", "D"))
    ascii_name = re.sub(r"[^A-Za-z0-9._-]", "_", ascii_name.encode("ascii", "ignore").decode())
    headers = {
        "Content-Disposition":
            f"attachment; filename=\"{ascii_name}\"; filename*=UTF-8''{quote(filename)}",
        "Cache-Control": "no-store",
    }
    if upstream.headers.get("Content-Length") and not upstream.headers.get("Content-Encoding"):
        headers["Content-Length"] = upstream.headers["Content-Length"]
    return Response(
        stream_with_context(upstream.iter_content(chunk_size=65536)),
        content_type=upstream.headers.get("Content-Type", "application/octet-stream"),
        headers=headers,
    )


# ---------- routes ----------
@app.get("/")
def index():
    return send_from_directory(app.root_path, "index.html")


@app.post("/api/info")
def api_info():
    url = ((request.get_json(silent=True) or {}).get("url") or "").strip()
    if not is_tiktok_url(url):
        return jsonify(error="Vui lòng nhập link TikTok hợp lệ (tiktok.com, vm.tiktok.com, vt.tiktok.com)."), 400

    errors, res = [], {}
    with ThreadPoolExecutor(max_workers=2) as ex:
        futs = {"tikwm": ex.submit(fetch_tikwm, url), "ytdlp": ex.submit(fetch_ytdlp, url)}
    for name, f in futs.items():
        try:
            res[name] = f.result()
        except Exception as e:
            errors.append(f"{name}: {e}")
    tk, yd = res.get("tikwm"), res.get("ytdlp")
    if not tk and not yd:
        return jsonify(error="Không lấy được media. Link có thể là riêng tư hoặc đã bị xoá.",
                       details=errors), 502

    base_info = tk or yd
    is_photo = bool(tk and any(i["kind"] == "image" for i in tk["items"]))

    items = []
    yd_items = []
    if yd and not is_photo:
        yd_items = [i for i in yd["items"] if not (tk and i.get("wm"))]  # tikwm đã có bản watermark
    items += yd_items

    # Tùy chọn upscale 4K: chỉ khi nguồn thật chưa đạt 2160p và máy có ffmpeg
    best_h = max([i.get("height", 0) for i in yd_items] or [0])
    if tk and not is_photo and shutil.which("ffmpeg") and best_h < 2160:
        src = next((i for i in tk["items"] if i.get("clean")), None)
        if src:
            items.append({"label": "Upscale lên 4K (phóng to bằng ffmpeg, không thêm chi tiết thật)",
                          "kind": "video", "ext": "mp4", "mode": "upscale", "slow": True,
                          "url": src["url"], "filename": f"{base_info['base']}_4k.mp4"})
    if tk:
        items += tk["items"]

    for it in items:
        extra = {k: it.pop(k) for k in ("url", "mode", "format_id", "page") if k in it}
        for k in ("wm", "clean", "height"):
            it.pop(k, None)
        it["token"] = make_token(it["filename"], **extra)
    return jsonify({"title": base_info["title"], "author": base_info["author"],
                    "cover": base_info["cover"], "items": items})


@app.get("/api/download")
def api_download():
    entry = _tokens.get(request.args.get("t", ""))
    if not entry or entry["exp"] < time.time():
        return jsonify(error="Link tải đã hết hạn, hãy bấm Tải để phân tích lại link."), 410
    mode = entry.get("mode", "direct")
    try:
        if mode == "ytdlp":
            return download_ytdlp(entry)
        if mode == "upscale":
            return upscale_4k(entry)
    except subprocess.TimeoutExpired:
        return jsonify(error="Xử lý quá lâu (hơn 20 phút), hãy thử video ngắn hơn."), 504
    except Exception as e:
        app.logger.warning("Lỗi tải (%s): %s", mode, e)
        return jsonify(error=f"Không xử lý được: {e}"), 502
    return proxy_direct(entry)


# ---------- API cho Phím tắt iPhone / script ----------
# Đặt biến môi trường API_KEY để khoá API (rất nên làm khi đưa lên mạng).
def api_key_ok() -> bool:
    expected = os.environ.get("API_KEY", "")
    if not expected:
        return True
    given = request.headers.get("X-API-Key") or request.values.get("key", "")
    return hmac.compare_digest(given.encode(), expected.encode())


def api_fetch():
    """Trả về (data, lỗi_response). Chỉ dùng tikwm: nhanh, có cả ảnh."""
    if not api_key_ok():
        return None, (jsonify(error="Sai hoặc thiếu key."), 401)
    url = (request.values.get("url") or "").strip()
    if not is_tiktok_url(url):
        return None, (jsonify(error="Link TikTok không hợp lệ."), 400)
    try:
        return fetch_tikwm(url), None
    except Exception as e:
        return None, (jsonify(error=f"Không lấy được media: {e}"), 502)


@app.route("/api/v1/info", methods=["GET", "POST"])
def api_v1_info():
    """JSON gồm link tải trực tiếp (hết hạn sau 15 phút)."""
    data, err = api_fetch()
    if err:
        return err
    base = request.host_url.rstrip("/")
    out = {"title": data["title"], "author": data["author"], "video": None,
           "video_hd": None, "video_watermark": None, "music": None, "images": []}
    for it in data["items"]:
        link = f"{base}/api/download?t={make_token(it['filename'], url=it['url'])}"
        if it["kind"] == "image":
            out["images"].append(link)
        elif it["kind"] == "audio":
            out["music"] = link
        elif "watermark" in it["filename"]:
            out["video_watermark"] = link
        elif it["filename"].endswith("_hd.mp4"):
            out["video_hd"] = link
        else:
            out["video"] = link
    out["video_best"] = out["video_hd"] or out["video"]
    # Link gốc từ nguồn (không qua server của bạn, không tốn băng thông). Có thể hết hạn nhanh.
    direct = {"images": [i["url"] for i in data["items"] if i["kind"] == "image"]}
    vids = [i for i in data["items"] if i["kind"] == "video"]
    best = next((i for i in vids if i["filename"].endswith("_hd.mp4")), None) \
        or next((i for i in vids if i.get("clean")), None)
    direct["video_best"] = best["url"] if best else None
    direct["music"] = next((i["url"] for i in data["items"] if i["kind"] == "audio"), None)
    out["direct"] = direct
    return jsonify(out)


@app.route("/api/v1/video", methods=["GET", "POST"])
def api_v1_video():
    """Trả thẳng file mp4 (không watermark, ưu tiên HD). ?wm=1 để lấy bản có watermark."""
    data, err = api_fetch()
    if err:
        return err
    vids = [i for i in data["items"] if i["kind"] == "video"]
    if not vids:
        return jsonify(error="Đây là bài ảnh, hãy dùng /api/v1/info để lấy danh sách ảnh."), 404
    want_wm = request.values.get("wm") in ("1", "true")
    pick = None
    if want_wm:
        pick = next((i for i in vids if "watermark" in i["filename"]), None)
    pick = pick or next((i for i in vids if i["filename"].endswith("_hd.mp4")), None) \
        or next((i for i in vids if i.get("clean")), vids[0])
    if request.values.get("mode") == "redirect":
        # Chuyển hướng thẳng tới nguồn: server không tốn băng thông (Phím tắt tự theo redirect)
        return redirect(pick["url"], code=302)
    resp = proxy_direct({"url": pick["url"], "filename": pick["filename"]})
    if isinstance(resp, Response):
        resp.headers["Content-Type"] = "video/mp4"  # để Phím tắt lưu vào Ảnh được
    return resp


@app.get("/health")
def health():
    """Cho UptimeRobot gọi định kỳ để Render không ngủ."""
    return "ok", 200, {"Cache-Control": "no-store"}


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", 5000)), debug=False, threaded=True)
