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


## Khi bị "HTTP 403 (tikwm chặn IP máy chủ)" (link ảnh/video đều lỗi)

IP của Render là IP trung tâm dữ liệu nên tikwm/TikTok hay chặn. Thứ tự cách cứu (từ dễ đến chắc):

1. **Tự cứu bằng trình duyệt của bạn (có sẵn, không cần cấu hình):** khi gặp lỗi chặn, web hiện khung "🛟 Máy chủ bị chặn IP".
   Trình duyệt (IP nhà bạn) tự lấy dữ liệu từ tikwm rồi gửi cho máy chủ (`/api/ingest`). Nếu tikwm không cho trình duyệt gọi chéo (CORS),
   web hướng dẫn 3 bước: mở dữ liệu → sao chép → dán → "Dùng dữ liệu này". Sau đó ảnh/ZIP/AI dùng bình thường.
2. **Cloudflare Worker relay** (`CLOUDFLARE_API.md`): đặt `TIKWM_RELAY` và `RELAY_KEY` trong Render > Environment.
3. **Proxy IP dân cư:** đặt `OUTBOUND_PROXY=http://user:pass@host:port` trong Render > Environment (áp dụng cho tikwm, tải file và yt-dlp).
4. Phím tắt iPhone gọi tikwm trực tiếp: `PHIM_TAT_TIKWM_TRUC_TIEP.md`.

**AI phiên âm:** ưu tiên nhạc nền (nhẹ nhất) → video tikwm → nếu không có link thì yt-dlp tự tải âm thanh (≤24 MB). Nếu mọi nguồn bị chặn IP,
lỗi sẽ nói rõ và gợi ý `OUTBOUND_PROXY`.


## Hỗ trợ nhiều nền tảng

Dán link Instagram, Facebook (kể cả fb.watch), X/Twitter, Threads, Pinterest, Reddit, Bluesky, Tumblr, Snapchat, Vimeo… vào cùng ô nhập.
Cách hoạt động: **gallery-dl** lấy ảnh/video của bài (nhiều ảnh hiện thành gallery để chọn + ZIP), **yt-dlp** lấy video chất lượng cao,
Threads và trang khác dùng thẻ og:image/og:video. Bài ảnh TikTok cũng có thêm gallery-dl làm đường dự phòng.
API v1 và AI dùng được cho tất cả các link này.

Lưu ý thật: Instagram/Facebook/Threads thường chỉ cho bài công khai, và hay đòi đăng nhập khi gọi từ IP máy chủ.
Nếu báo lỗi, xuất cookies.txt (định dạng Netscape) từ trình duyệt đã đăng nhập (tiện ích "Get cookies.txt LOCALLY"),
dán toàn bộ nội dung vào biến môi trường `COOKIES_TXT` trên Render. Dùng tài khoản phụ, không dùng tài khoản chính.


## Cập nhật AI & API (v2)

- Whisper không còn "bịa lời" (ví dụ "Hãy subscribe cho kênh Ghiền Mì Gõ") khi video chỉ có nhạc: các đoạn không phải lời nói bị lọc.
- Video ít/không có lời thoại: AI cắt 4 khung hình (thư viện `av`, không cần cài ffmpeg) và cho mô hình thị giác xem, nên tóm tắt/caption đúng nội dung.
- Nút "AI xem video" hoạt động cho cả video; tab AI có đủ tóm tắt, chương, caption, hashtag, hỏi đáp, dịch, ý tưởng.
- API mới: `/api/v1/links`, `/api/v1/zip`, `/api/v1/text`; `/api/v1/ai` thêm các task `describe`, `ask`, `post`, `comments`, `script`, `all` và `format=text`. Chi tiết và cách dựng phím tắt: `PROMPT_PHIM_TAT_IPHONE.md`.
- iPhone: sau khi tải xong, chạm nút để mở bảng chia sẻ và chọn "Lưu video"/"Lưu ảnh" vào thư viện Ảnh.


## Giao diện mới & chọn ảnh qua API

- Giao diện kiểu "kẹo ngọt": pastel, viền dày như sticker, linh vật dễ thương, tim/sao bay nhẹ, có chế độ tối tự động, nút bấm to dễ chạm trên iPhone.
- API ảnh nhận `index=2`, `1,3`, `1-3` hoặc `all` (khớp số thứ tự ảnh trong bài); `/api/v1/choices` trả danh sách để hiện "Chọn từ Danh sách" trong Phím tắt. Hướng dẫn từng bước ở cuối `PROMPT_PHIM_TAT_IPHONE.md`.


## Tài liệu API: /docs

Mở `https://TEN-APP.onrender.com/docs` (cũng vào được bằng `/api/v1`): trang hướng dẫn đầy đủ có ví dụ curl tự điền địa chỉ + API key của bạn,
bảng tham số từng endpoint, các task AI, mã lỗi, biến môi trường, hướng dẫn Phím tắt iPhone và nút **Thử ngay** để gọi thử trực tiếp.
Cần có file `docs.html` nằm cạnh `app.py` trên GitHub.


## v3: giao diện kiểu Apple, nghe âm thanh chuẩn hơn, sửa lỗi Phím tắt

- Giao diện mới sạch như Apple: nền xám nhạt, thẻ trắng bo lớn, điều khiển phân đoạn, nút xanh, tự đổi sáng/tối.
- AI tách âm thanh video thành WAV 16 kHz, tăng âm lượng khi nhỏ, bỏ qua video im lặng, có ô chọn ngôn ngữ lời nói (`speech=`).
- `/api/v1/links?choice=...` nhận thẳng lựa chọn từ `/api/v1/choices`, tự trả đúng loại, sửa lỗi "Rich Text to URL" trong Phím tắt.
- `requirements.txt` có thêm `av` (cắt khung hình + tách âm thanh) và `audioop-lts` cho Python 3.13.
