# Beysnap · Tải TikTok (video, ảnh, nhạc) + AI

Dán link TikTok → tải **video** (HD, không watermark hoặc có watermark), **ảnh** slideshow (xem từng ảnh, chọn ảnh, tải ZIP), **nhạc MP3**.
Có AI (Groq): phiên âm, phụ đề `.srt`, tóm tắt, gợi ý caption/hashtag, dịch, hỏi đáp về video.
Giao diện Giáng sinh, dùng được trên điện thoại; có API cho Phím tắt iPhone.

## Chạy trên máy
```bash
pip install -r requirements.txt
python app.py        # http://127.0.0.1:5000
```

## Deploy Render (miễn phí)
1. Đưa mã lên GitHub. Render → New → Web Service (hoặc Blueprint với `render.yaml`).
2. Build: `pip install -r requirements.txt`
   Start: `gunicorn -w 1 --threads 8 --timeout 300 -b 0.0.0.0:$PORT app:app` (**bắt buộc `-w 1`**, link tải lưu trong bộ nhớ).
3. Environment:

| Biến | Bắt buộc | Ý nghĩa |
|---|---|---|
| `API_KEY` | nên có | Khoá cho `/api/v1/*` |
| `GROQ_API_KEY` | để dùng AI | Khoá Groq, chỉ lưu ở server, không bao giờ để trong mã hay gửi cho trình duyệt |
| `PYTHON_VERSION` | nên có | `3.12.7` |
| `GROQ_WHISPER_MODEL` | không | mặc định `whisper-large-v3-turbo` |
| `GROQ_CHAT_MODEL` / `GROQ_CHAT_FALLBACK` | không | mặc định `openai/gpt-oss-120b` / `openai/gpt-oss-20b` |
| `TIKWM_RELAY` + `RELAY_KEY` | không | Địa chỉ Cloudflare Worker chuyển tiếp (xem `CLOUDFLARE_API.md`) khi tikwm chặn IP Render |
| `GROQ_VISION_MODEL` | không | mặc định `qwen/qwen3.8-27b` (AI xem ảnh) |
| `AI_LIMIT` | không | số lượt AI mỗi 10 phút mỗi IP (mặc định 20) |

4. Health check path: `/health`. Dùng UptimeRobot gọi `/health` mỗi 5 phút để server không ngủ.

## API (cho Phím tắt, script)
Gửi `POST` dạng form (hoặc GET) với `url` và `key`. Chi tiết và cách làm Phím tắt: `PROMPT_PHIM_TAT_IPHONE.md`.

| Đường dẫn | Việc |
|---|---|
| `/api/v1/info` | JSON: loại bài (video/photo), link video, nhạc, danh sách ảnh, ZIP, `choices` |
| `/api/v1/video` | MP4 không watermark. `quality=hd\|sd\|wm` |
| `/api/v1/music` | MP3 |
| `/api/v1/image` | 1 ảnh. `index=1..N`, `fmt=jpg` |
| `/api/v1/get` | `type=video\|music\|image\|zip` |
| `/api/v1/ai` | `task=summary\|chapters\|caption\|hashtags\|transcript\|srt\|translate\|ideas`, `lang=vi\|en\|...` |
| `/health` | `ok` |

Mặc định tải **qua server** (ổn định). `mode=redirect` chỉ để thử, có thể gây 403.

## Đã làm gì để nhanh
- Gọi nguồn chính (tikwm) trước; yt-dlp chỉ chạy khi cần (nút "Tìm chất lượng cao hơn") hoặc khi nguồn chính lỗi.
- Bộ nhớ đệm 8 phút cho cùng một link, kết nối giữ sẵn (keep-alive), khối truyền 256 KB.
- Ảnh tải song song, ZIP dựng song song; thumbnail dùng lại bộ nhớ đệm của trình duyệt khi bấm tải.
- Tự dán và tự tải khi dán link; đánh thức server ngay khi mở trang.
- Nếu một nguồn bị chặn, API tự thử bản video khác (HD → thường → …).

## Bảo mật
- Đặt `API_KEY`. Không đưa khoá vào GitHub, ảnh chụp màn hình hay chat. Lộ khoá thì tạo lại ngay.
- Có giới hạn tốc độ theo IP cho web, API và AI.

## Lưu ý
- TikTok/tikwm có thể đổi hoặc chặn IP máy chủ bất cứ lúc nào; khi đó sửa hàm `fetch_tikwm`.
- Nút 4K chỉ phóng to bằng ffmpeg (cần ffmpeg, Render free không có sẵn).
- Chỉ tải nội dung bạn có quyền sử dụng, tôn trọng bản quyền tác giả.

## Khi tikwm chặn IP máy chủ (lỗi 403)
Server tự thử lần lượt: Cloudflare Worker (nếu cấu hình) → giả trình duyệt Chrome → requests thường → yt-dlp. Nếu vẫn lỗi:
1. **Cloudflare Worker (miễn phí, luôn bật):** `cloudflare-api-worker.js` vừa là API riêng cho Phím tắt vừa làm cầu nối cho Render (`TIKWM_RELAY` = `https://TEN.workers.dev/relay`, `RELAY_KEY` = `API_KEY` của Worker). Xem `CLOUDFLARE_API.md`. Không đảm bảo thành công vì tikwm có thể chặn cả IP Cloudflare.
2. **Phím tắt trực tiếp:** iPhone gọi tikwm không qua Render, xem `PHIM_TAT_TIKWM_TRUC_TIEP.md`.
3. **Đổi máy chủ:** Oracle Cloud Always Free hoặc chạy trên máy nhà qua Cloudflare Tunnel (IP nhà ít bị chặn).

## Bài ảnh (slideshow) và chẩn đoán
- Server thử lần lượt: tikwm với link gốc → link thật (mở link rút gọn) → đổi `/photo/` thành `/video/` → đọc thẳng trang TikTok → yt-dlp.
- Nếu server không tải được ảnh (nguồn chặn), trình duyệt tự tải ảnh gốc và nút đổi thành "Mở ảnh gốc" (giữ ảnh → Lưu ảnh).
- Chẩn đoán: mở `/api/debug?url=LINK_TIKTOK&key=API_KEY` để xem từng nguồn thành công hay lỗi gì (kèm kiểm tra tải thử ảnh đầu tiên).

## AI (Groq)
**Bật AI:** tab ✨ AI có ô nhập khoá. Tạo khoá miễn phí ở console.groq.com/keys, dán vào ô (lưu trên trình duyệt của bạn, gửi qua HTTPS để gọi Groq, server không lưu). Hoặc đặt `GROQ_API_KEY` trong Render để mọi người dùng chung khoá của bạn.

| Tính năng | Mô tả |
|---|---|
| Phiên âm | Lời thoại + tải `.txt` / `.srt` (Whisper) |
| Tóm tắt, chương, caption, hashtag | Chương theo mốc thời gian cho video dài |
| Dịch phụ đề | 9 ngôn ngữ, giữ mốc thời gian để tải `.srt` |
| Ý tưởng & chấm hook | Điểm câu mở đầu, câu mở đầu gợi ý, 3 ý tưởng video tiếp theo |
| Hỏi đáp | Hỏi về nội dung video |
| AI xem ảnh (bài ảnh) | Mô tả, đọc chữ trong ảnh, alt text, caption, hashtag (tối đa 3 ảnh) |
| 🔊 Đọc to | Dùng giọng đọc có sẵn của trình duyệt, miễn phí |

Giới hạn: gói miễn phí Groq có hạn mức yêu cầu/token mỗi phút và mỗi ngày; phiên âm chỉ nhận file tới 24 MB; AI xem ảnh nhận tối đa 3 ảnh. Khi quá hạn mức, giao diện báo "Groq đang giới hạn tốc độ".
