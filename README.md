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


## v4: log Discord webhook, API tải đáng tin hơn

- `DISCORD_WEBHOOK` (tuỳ chọn): mỗi yêu cầu tải hoặc AI (web lẫn API) gửi một thẻ nhúng về kênh Discord: link, IP, trình duyệt, kết quả/lỗi. Lọc bằng `DISCORD_EVENTS`. Đây là log phía máy chủ, không hiện trong DevTools của người dùng.
- `GROQ_API_KEY` đặt trong Render dùng chung cho mọi người; ai muốn dùng khoá riêng thì gửi header `X-Groq-Key`.
- `/api/v1/links` giờ thử mở thật từng file trước khi trả, sửa lỗi Phím tắt báo "Đã lưu" mà không có gì (xem `PROMPT_PHIM_TAT_IPHONE.md`).


## v5: giải bài bằng AI, tự log lỗi và AI chẩn đoán

- **`/api/v1/solve`**: gửi ảnh chụp màn hình đề bài (tải lên dạng tệp, base64 hoặc body ảnh) và/hoặc chữ nhập từ ô hỏi của Phím tắt. Ảnh được nén, model thị giác chép lại đề, model suy luận giải và tự kiểm tra. Chế độ `full/answer/explain/hint/check`, trả JSON hoặc `format=text` / `part=answer` cho Phím tắt. Hướng dẫn: cuối `PROMPT_PHIM_TAT_IPHONE.md` và mục `/docs`.
- **Log lỗi tự động**: lỗi được ghi (xoá khoá/mật khẩu), gửi Discord, rồi nếu có `GROQ_API_KEY` + `DISCORD_WEBHOOK` thì AI đọc traceback và đúng các hàm liên quan trong `app.py` (chọn từ mục lục toàn bộ mã nguồn) và gửi hướng xử lý lên Discord. Có chống trùng, giới hạn mỗi giờ; tắt bằng `ERROR_AI=0`. Xem/gọi AI thủ công ở `/api/v1/errors` (cần `API_KEY`).
- Discord: thêm loại log `solve` và `diagnosis`; tự bỏ bớt khi vượt `DISCORD_PER_MIN` thẻ mỗi phút.
- Biến môi trường mới: `ERROR_AI`, `ERROR_AI_COOLDOWN`, `ERROR_AI_HOURLY`, `ERROR_LOG_FILE`, `SOLVE_LIMIT`, `DISCORD_PER_MIN`.
- `requirements.txt` thêm `pillow-heif` để đọc ảnh HEIC của iPhone.
- Mô hình thị giác mặc định `GROQ_VISION_MODEL` (đổi được trên Render nếu Groq gỡ model).


## v6: Threads thật, phản hồi nhanh hơn, log file lên Discord

- **Threads**: gallery-dl và yt-dlp không hỗ trợ Threads nên trước đây chỉ ra ảnh og (giống chụp màn hình). Giờ đọc thẳng dữ liệu nhúng trong trang bài (và trang `/embed/`, cả `threads.com` lẫn `threads.net`) để lấy video/ảnh/album gốc. Nếu chỉ còn ảnh xem trước, API trả lỗi rõ ràng (`code: preview_only`); thêm `allow_preview=1` nếu vẫn muốn tải ảnh đó. Web hiện dòng cảnh báo. Chưa kiểm thử với Threads thật (sandbox không ra được Internet), cấu trúc dựa trên dữ liệu nhúng của Instagram/Threads.
- **Nhanh hơn**: gọi tikwm "đuổi nhau" (relay → chrome → requests, cách nhau ~1,1 giây, cái nào xong trước thắng), ngắt mạch 45 giây khi bị chặn IP (báo lỗi ngay, khỏi chờ), gộp yêu cầu trùng (`single_flight`), dùng lại kết quả cũ tới 2 giờ nếu tikwm đang lỗi, giải link rút gọn song song, `check=auto` chỉ thử mở link không phải TikTok, tạo zip tiết kiệm RAM.
- **Mã trạng thái `424` thay `502/504`** cho lỗi từ nguồn (Cloudflare thay trang lỗi gốc bằng trang "502" của nó khi thấy 502/504 từ máy chủ gốc, Phím tắt không đọc được nội dung lỗi). Phím tắt và web chỉ dựa vào nội dung/`ok` nên không ảnh hưởng. Giả thuyết này chưa kiểm tra trên Render thật.
- **Khi tikwm trả 403**: đó là tikwm chặn IP Render, code không tự sửa được. Đặt `TIKWM_RELAY` + `RELAY_KEY` (Cloudflare Worker, xem `CLOUDFLARE_API.md`) hoặc `OUTBOUND_PROXY`; lỗi API đã gợi ý cách này.
- **Sửa 3 lỗi do AI chẩn đoán**: mô hình thị giác tối đa 3 ảnh mỗi yêu cầu (`MAX_VISION_IMAGES = 3`); dịch video không có lời thoại trả lỗi 400 rõ ràng; `/api/v1/choices` khi tikwm 403 trả 424 kèm cách sửa.
- **`/api/v1/solve` báo "Chưa có đề bài" dù đã gửi ảnh**: giờ nhận ảnh ở mọi kiểu (tệp bất kỳ tên trường, base64, data URL, body ảnh thô, JSON), form lớn tới 25 MB; nếu vẫn không thấy thì lỗi ghi rõ "Server nhận được: ..." để biết Phím tắt đang gửi gì. Trong Phím tắt, ảnh phải là trường kiểu **Tệp** (Method POST), không phải Văn bản.
- **Gửi chính file lên Discord**: khi có `DISCORD_WEBHOOK`, mỗi video/ảnh/nhạc/zip tải qua máy chủ được gửi kèm file thật lên kênh (kèm link bài, IP, tên file), tải dở thì không gửi, file giống nhau trong 10 phút chỉ gửi một lần. Tắt bằng `DISCORD_FILES=0`, bỏ `file` khỏi `DISCORD_EVENTS`, hoặc giới hạn dung lượng bằng `DISCORD_FILE_MAX_MB`. Ảnh chụp màn hình gửi tới `/api/v1/solve` KHÔNG được gửi lên Discord. Người chạy máy chủ nên cho người dùng biết điều này.
- Biến môi trường mới: `DISCORD_FILES`, `DISCORD_FILE_MAX_MB`; `render.yaml` chạy `--threads 16 --keep-alive 30`.


## v7: tải hàng loạt, lịch sử, tải theo kênh, AI chẩn đoán xịn hơn

- **Tải hàng loạt**: dán nhiều link (web: ô chính hoặc mục "Tải hàng loạt"; API: `/api/v1/batch`) và nhận **một ZIP**. Chạy ở luồng nền, ghi ZIP ra đĩa tạm (không giữ trong RAM, không dính giới hạn ~100 giây của Cloudflare), có tiến độ từng link, `_ket_qua.txt` trong ZIP ghi link nào lỗi. Giới hạn `BATCH_MAX_ITEMS` (30) và `BATCH_MAX_MB` (150); mỗi IP tối đa 2 ZIP cùng lúc; ZIP giữ 30 phút.
- **Lịch sử**: 20 link gần nhất lưu trong trình duyệt (localStorage, không tài khoản), chạm để tải lại, xoá từng mục hoặc tất cả.
- **Tải theo kênh**: nhập `@tên_kênh` hoặc link hồ sơ TikTok, chọn N video mới nhất (1–30) rồi tải ZIP; API `/api/v1/channel` (`format=text`, `zip=1`). Danh sách lấy từ tikwm qua cùng đường relay/chống chặn IP, nên **cần dán lại `cloudflare-api-worker.js` mới (có `/relay-user`)** nếu bạn dùng `TIKWM_RELAY`. Chưa kiểm tra với tikwm thật (sandbox không ra được Internet): dạng JSON của `api/user/posts` dựa theo tài liệu công khai, kiểm thử bằng dữ liệu giả.
- **Sửa "Chưa có đề bài"** trong Phím tắt giải bài: thông báo lỗi giờ nói đúng chuyện đã xảy ra (GET trống, body rỗng, sai kiểu field) và chỉ cách sửa từng bước trong Phím tắt; hướng dẫn riêng cho Phím tắt "Auto Solve from Share Sheet" ở cuối `PROMPT_PHIM_TAT_IPHONE.md`. Nguyên nhân gần như chắc chắn: bước "Get contents of URL" chưa đặt POST + Request Body nên ảnh không được gửi.
- **AI chẩn đoán mọi lỗi, chỉ rõ chỗ trong code**: ghi cả lỗi cấu hình Phím tắt (kèm hình dạng yêu cầu); tự định vị `app.py:dòng` từ traceback, từ câu thông báo lỗi nằm sẵn trong mã và từ route + các hàm nó gọi; AI đọc mã **có số dòng** cùng bối cảnh dự án (tikwm 403 = chặn IP, Cloudflare đổi 502/504, Threads không có trong gallery-dl/yt-dlp, v.v.) để khỏi đề xuất sai; lỗi code thì AI viết lại hàm, `ast` kiểm tra rồi đính kèm file `.diff` (chỉ là đề xuất, không tự áp dụng, chưa chạy thử). Lỗi vượt `ERROR_AI_HOURLY` (mặc định 10) xếp hàng và tự được phân tích khi còn lượt.
- Biến môi trường mới: `BATCH_MAX_ITEMS`, `BATCH_MAX_MB`; `ERROR_AI_HOURLY` mặc định 10.

## v7.1: nhiều nguồn dự phòng khi tikwm bị chặn

Khi tikwm lỗi/chặn IP, server chạy **song song** thêm các dịch vụ tải TikTok khác (tiklydown, lovetik, tikdownloader, ttsave) và dùng kết quả đầu tiên hợp lệ, rồi mới tới trang TikTok, gallery-dl, yt-dlp. Thêm nguồn riêng bằng `TIKTOK_APIS` (mỗi dòng một địa chỉ có `{url}`). Tải theo kênh có thêm đường yt-dlp. **Chưa kiểm tra với các dịch vụ thật** (sandbox không ra Internet, các dịch vụ ngoài có thể đổi/chết bất cứ lúc nào); đọc phản hồi theo kiểu lỏng và kiểm thử bằng dữ liệu giả.
