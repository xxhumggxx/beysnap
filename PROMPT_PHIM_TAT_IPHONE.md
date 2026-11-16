# Prompt + hướng dẫn làm Phím tắt iPhone (Beysnap)

Tài liệu có 3 phần:
1. **Prompt** để dán vào một trợ lý AI (Claude, ChatGPT…) nếu bạn muốn AI hướng dẫn từng bước.
2. **Hướng dẫn tự làm** 3 Phím tắt, đã viết sẵn.
3. **Sửa lỗi** thường gặp (403, 401, 502…).

> Địa chỉ server của bạn: `https://tiktok-downloader-ddi5.onrender.com`
> Khoá API: lấy ở Render → dịch vụ → **Environment** → `API_KEY`.
> **Đừng dán khoá thật vào chat với AI.** Trong prompt giữ nguyên chữ `<API_KEY>`, chỉ điền khoá thật khi bạn nhập vào app Phím tắt.

---

## 1. PROMPT (sao chép từ dòng dưới)

```
Bạn là chuyên gia app Phím tắt (Shortcuts) trên iPhone, iOS 17 trở lên. Hãy hướng dẫn tôi TỪNG BƯỚC, bằng tiếng Việt,
cách tạo Phím tắt gọi API tải TikTok của tôi. Với mỗi bước ghi rõ: tên hành động (tiếng Anh, kèm tên tiếng Việt nếu biết),
phải điền gì vào từng ô, và biến nào được truyền sang bước sau. Không bỏ qua bước nào, không dùng thuật ngữ mơ hồ.

BỐI CẢNH
- Server của tôi: https://tiktok-downloader-ddi5.onrender.com (chạy trên Render gói miễn phí, có thể "ngủ"; lần gọi đầu có thể mất 30–50 giây).
- Mọi yêu cầu gửi bằng POST, dạng Form (Request Body = Form), có 2 trường bắt buộc:
    url = link TikTok (lấy từ "Shortcut Input" khi người dùng bấm Chia sẻ trong TikTok)
    key = <API_KEY> (tôi sẽ tự điền)
  Dùng POST + Form vì link TikTok chứa ký tự "&" và "?", ghép vào URL sẽ bị cắt. KHÔNG thêm trường mode=redirect
  (gây lỗi 403 vì iPhone bị chuyển thẳng sang máy chủ nguồn).
- Phím tắt phải hiện trong Share Sheet (Show in Share Sheet), nhận loại URL và Text.

CÁC ĐƯỜNG DẪN API
1) POST /api/v1/info  -> trả JSON:
   { "title", "author", "type": "video" hoặc "photo", "image_count": số ảnh,
     "video_best", "video_hd", "video_sd", "video_watermark", "slideshow",   (link tải, có thể null)
     "music",                                                                 (link MP3, có thể null)
     "images": [link ảnh 1, link ảnh 2, ...],                                 (rỗng nếu là video)
     "zip": link ZIP tất cả ảnh hoặc null,
     "choices": ["Video","Nhạc","Ảnh 1","Ảnh 2",...] }
   Mọi "link" là địa chỉ đầy đủ, dùng "Get Contents of URL" (GET, không cần key) để tải file. Link hết hạn sau 15 phút.
   Nếu lỗi, JSON có khoá "error" (chuỗi tiếng Việt).
2) POST /api/v1/video  -> trả thẳng file MP4 không watermark, ưu tiên HD.
     tuỳ chọn: quality = hd | sd | wm (wm là bản có watermark)
3) POST /api/v1/music  -> trả thẳng file MP3
4) POST /api/v1/image  -> trả thẳng 1 ảnh. tuỳ chọn: index = 1,2,3… (mặc định 1), fmt = jpg (đổi sang JPEG cho chắc mở được trên iPhone)
5) POST /api/v1/get    -> tham số type = video | music | image | zip (mặc định tự chọn theo bài)
6) POST /api/v1/ai     -> task = summary | chapters | caption | hashtags | transcript | srt | translate | ideas, lang = vi | en | zh | ja | ko ...
     (cần AI: đặt GROQ_API_KEY trên server Render)
     trả JSON { "task", "lang", "result": "văn bản" }

YÊU CẦU CÁC PHÍM TẮT CẦN LÀM
A. "Tải video 1 chạm": nhận link -> POST /api/v1/video -> Save to Photo Album -> thông báo "Đã lưu".
B. "Tải TikTok (đầy đủ)": đánh thức server bằng GET /health; gọi /api/v1/info; nếu có khoá "error" thì hiện cảnh báo và dừng;
   nếu type = photo thì hiện menu: "Tất cả ảnh" / "Một ảnh theo số" / "Nhạc" / "Video slideshow";
   nếu type = video thì hiện menu: "Video" / "Nhạc".
   - Tải video: lấy "video_best" -> Get Contents of URL -> Save to Photo Album.
   - Tải tất cả ảnh: lấy "images" -> Repeat with Each -> Get Contents of URL (Repeat Item) -> Save to Photo Album.
   - Một ảnh: Ask for Input (kiểu Number, mặc định 1) -> POST /api/v1/image với index = số vừa nhập và fmt = jpg -> Save to Photo Album.
   - Nhạc: lấy "music" -> Get Contents of URL -> Save File (lưu vào Tệp).
C. "AI tóm tắt TikTok": POST /api/v1/ai với task=summary, lang=vi -> lấy "result" -> Show Result và Copy to Clipboard.

CÁCH TRÌNH BÀY
- Với mỗi Phím tắt: danh sách hành động đánh số theo đúng thứ tự trên màn hình.
- Chỉ rõ cách bật "Show in Share Sheet", chọn loại đầu vào, cấp quyền Ảnh và quyền truy cập tên miền onrender.com lần đầu.
- Cuối cùng cho danh sách kiểm tra và cách xử lý lỗi: 401 (sai key), 403 (nguồn chặn), 424 (nguồn không phản hồi hoặc chặn IP; server dùng 424 thay 502 vì Cloudflare thay nội dung lỗi 502/504 bằng trang HTML), chờ lâu (server đang ngủ).
```

---

## 2. Hướng dẫn tự làm (nếu không cần AI)

Mở app **Phím tắt** → dấu **+**. Ở mọi hành động **Lấy nội dung của URL** (Get Contents of URL): bấm *Hiện thêm*, chọn **Phương thức: POST**, **Nội dung yêu cầu: Biểu mẫu**, thêm trường **Văn bản** `url` và `key`.

**Cài đặt chung:** bấm biểu tượng (i) ở phím tắt → bật **Hiển thị trong Trang tính chia sẻ**, loại đầu vào chọn **URL** và **Văn bản**.

### A. "Tải video 1 chạm"
1. **Lấy nội dung của URL** → URL `https://tiktok-downloader-ddi5.onrender.com/api/v1/video`, POST, Biểu mẫu:
   `url` = *Đầu vào phím tắt*, `key` = khoá của bạn.
2. **Lưu vào album ảnh** (Save to Photo Album) ← *Nội dung của URL*.
3. **Hiện thông báo**: "Đã lưu video 🎄".

Thêm `quality` = `wm` nếu muốn bản có watermark, hoặc `sd` nếu muốn file nhỏ.

### B. "Tải TikTok (đầy đủ)" — video, ảnh, nhạc
1. **Lấy nội dung của URL** (GET) → `https://tiktok-downloader-ddi5.onrender.com/health` (đánh thức server, bỏ qua kết quả).
2. **Lấy nội dung của URL** (POST) → `.../api/v1/info`, trường `url` + `key`. Đặt tên biến **Info**.
3. **Lấy giá trị từ điển** (Get Dictionary Value) khoá `error` từ *Info* → **Nếu** có giá trị → **Hiện cảnh báo** (nội dung = giá trị đó) → **Dừng phím tắt** → **Kết thúc Nếu**.
4. **Lấy giá trị từ điển** khoá `type` từ *Info*.
5. **Nếu** *Giá trị từ điển* **là** `photo`:
   - **Chọn từ menu** với 4 mục: `Tất cả ảnh`, `Một ảnh`, `Nhạc`, `Video slideshow`.
   - *Tất cả ảnh*: Lấy giá trị `images` từ *Info* → **Lặp lại với từng mục** → **Lấy nội dung của URL** (GET, URL = *Mục lặp lại*) → **Lưu vào album ảnh**.
   - *Một ảnh*: **Yêu cầu nhập** (kiểu Số, mặc định 1) → **Lấy nội dung của URL** POST `.../api/v1/image` với `url`, `key`, `index` = số vừa nhập, `fmt` = `jpg` → **Lưu vào album ảnh**.
   - *Nhạc*: Lấy `music` từ *Info* → **Lấy nội dung của URL** → **Lưu tệp**.
   - *Video slideshow*: Lấy `slideshow` từ *Info* → **Lấy nội dung của URL** → **Lưu vào album ảnh**.
6. **Còn lại (Otherwise)**:
   - **Chọn từ menu**: `Video`, `Nhạc`.
   - *Video*: Lấy `video_best` từ *Info* → **Lấy nội dung của URL** → **Lưu vào album ảnh**.
   - *Nhạc*: như trên.
7. **Hiện thông báo**: "Xong 🎁".

Cách này chỉ gọi nguồn một lần (bước 2), các bước sau tải từ link đã có nên nhanh hơn.

### C. "AI tóm tắt TikTok"
1. **Lấy nội dung của URL** → `.../api/v1/ai`, POST, Biểu mẫu: `url`, `key`, `task` = `summary`, `lang` = `vi`.
2. **Lấy giá trị từ điển** khoá `result` → **Sao chép vào bảng nhớ** và **Hiện kết quả**.

Đổi `task` thành `caption` (gợi ý caption), `hashtags`, `transcript` (lời thoại), `srt` (phụ đề), `translate` (dịch, kèm `lang`).
Giới hạn mặc định: 10 lượt AI mỗi 10 phút cho mỗi mạng.

---

## 3. Sửa lỗi thường gặp

| Triệu chứng | Nguyên nhân | Cách sửa |
|---|---|---|
| **HTTP 403 / "bị chặn IP"** khi tải | Trường `mode=redirect` làm iPhone tải thẳng từ máy chủ nguồn và bị chặn | **Xoá trường `mode`**. Bản server mới mặc định tải qua server của bạn và tự thử các bản chất lượng khác nếu một nguồn bị chặn |
| Chữ `tikwm chặn IP máy chủ` trong thông báo | Nguồn chặn IP của Render | Đợi vài phút thử lại; nếu lặp lại nhiều ngày, nên chuyển sang máy chủ khác (Oracle Cloud) |
| `Sai hoặc thiếu key` (401) | Sai `key` | Copy lại `API_KEY` trong Render → Environment |
| Chờ rất lâu lần đầu | Render đang thức dậy | Bước `/health` ở đầu Phím tắt B giúp; UptimeRobot giữ server luôn thức |
| `Quá nhiều yêu cầu` (429) | Gọi quá nhanh | Đợi 1 phút |
| Ảnh không mở được trong Ảnh | Định dạng webp/heic | Thêm `fmt` = `jpg` ở bước tải ảnh |
| `AI chưa được bật` (503) | Chưa có `GROQ_API_KEY` trên Render | Thêm biến môi trường rồi deploy lại |


---

# Phím tắt nâng cao (bản mới)

Thay `https://TEN-APP.onrender.com` bằng địa chỉ của bạn và `KEY` bằng API_KEY. Tất cả endpoint nhận `url` (link TikTok, Instagram, Facebook, X, Threads, Pinterest…) và `key`.
Thêm `format=text` ở các endpoint AI để nhận **văn bản thuần**, không cần xử lý JSON.

## Danh sách endpoint

| Endpoint | Việc làm | Tham số thêm |
|---|---|---|
| `/api/v1/get` | tải 1 file (tự chọn video/ảnh) | `type=video\|music\|image\|zip`, `index=2`, `quality=hd\|sd\|wm`, `fmt=jpg` |
| `/api/v1/links` | **mỗi dòng một link tải** (để lưu hết ảnh) | `kind=images\|video\|music\|all` |
| `/api/v1/zip` | tải tất cả ảnh thành 1 file ZIP | |
| `/api/v1/text` | tiêu đề/tác giả/số ảnh | `field=title\|author\|type\|count\|all` |
| `/api/v1/info` | JSON đầy đủ + mọi link | |
| `/api/v1/ai` | AI | `task=` xem bên dưới, `lang=vi\|en\|ja…`, `format=text` |

Các `task` của AI: `summary` (tóm tắt), `describe` (**AI xem hình trong video** rồi mô tả), `transcript` (lời thoại), `srt` (phụ đề), `translate` (dịch, thêm `lang=`),
`caption`, `hashtags`, `chapters`, `ideas` (chấm hook + ý tưởng), `post` (viết bài đăng, thêm `platform=tiktok|instagram|facebook|x|threads|youtube`),
`comments` (5 bình luận gợi ý), `script` (viết lại thành kịch bản 30–45 giây), `ask` (hỏi đáp, thêm `q=câu hỏi`), `all` (gói tất cả).

Video chỉ có nhạc/không có lời: AI tự cắt vài khung hình ra xem, nên `summary`, `caption`… vẫn đúng nội dung (không còn bịa lời như "Ghiền Mì Gõ").

## Phím tắt 1 – Lưu TẤT CẢ ảnh vào thư viện Ảnh
1. **Nhận văn bản từ Bảng nhớ tạm** (Get Clipboard) hoặc **Nhận URL từ Đầu vào Shortcut**.
2. **Lấy nội dung của URL**: URL `https://TEN-APP.onrender.com/api/v1/links`, Phương thức **POST**, Nội dung yêu cầu **Biểu mẫu**: `url` = (Clipboard), `key` = KEY, `kind` = `images`.
3. **Tách văn bản** theo **Dòng mới**.
4. **Lặp lại với từng mục**: **Lấy nội dung của URL** (mục lặp) → **Lưu vào Album ảnh** (Recents).
5. (tuỳ chọn) **Hiển thị thông báo** "Đã lưu".
Muốn chỉ lưu video: đổi `kind` thành `video` (bước 4 vẫn dùng được, chỉ có 1 dòng).

## Phím tắt 2 – Menu AI (tóm tắt, mô tả, caption, dịch…)
1. **Chọn từ Menu** với các mục: Tóm tắt, Mô tả video, Caption, Hashtag, Dịch, Kịch bản, Bình luận, Viết bài Facebook, Hỏi AI.
2. Mỗi nhánh **Đặt biến** `task` = `summary` / `describe` / `caption` / `hashtags` / `translate` / `script` / `comments` / `post` / `ask`.
   - Nhánh "Hỏi AI": thêm **Yêu cầu nhập** (câu hỏi) → biến `q`. Nhánh "Viết bài": biến `platform` = `facebook`.
3. **Lấy nội dung của URL**: POST `https://TEN-APP.onrender.com/api/v1/ai`, Biểu mẫu: `url`, `key`, `task` (biến), `format` = `text`, và `q`/`platform` nếu có.
4. **Sao chép vào Bảng nhớ tạm** rồi **Hiển thị kết quả** (Show Result).
AI chạy mất 10–40 giây với video; nếu hiện "LỖI: …" là lời nhắn thật của server (hết lượt Groq, thiếu GROQ_API_KEY…).

## Phím tắt 3 – Phụ đề tiếng Việt cho video nước ngoài
`/api/v1/ai` với `task=translate`, `lang=vi`, `format=text` → **Tạo tệp** (đuôi .txt) → **Chia sẻ**. Muốn file phụ đề .srt thì dùng `task=srt` (tiếng gốc).

## Phím tắt 4 – Một chạm: tải xong + viết caption
Ghép phím tắt 1 hoặc `type=video` với một **Lấy nội dung của URL** tới `/api/v1/ai?task=caption&format=text`, rồi **Sao chép vào Bảng nhớ tạm** để dán thẳng khi đăng.

## Lỗi thường gặp
- `LỖI: ... Thiếu khoá Groq` → đặt `GROQ_API_KEY` trong Render > Environment.
- `HTTP 429` → đang gọi quá nhanh hoặc hết lượt Groq miễn phí, đợi vài phút.
- Link Instagram/Facebook/Threads riêng tư hoặc cần đăng nhập thì không tải được; cookie là tuỳ chọn cuối cùng (`COOKIES_TXT`).


---

# Phím tắt "Chọn ảnh số mấy" (1, 2, 3, 4… hoặc nhiều ảnh)

Số thứ tự ảnh trùng với số trên web và trong bài đăng (ảnh 1 là ảnh đầu tiên).
Tham số `index` dùng được ở `/api/v1/get`, `/api/v1/image`, `/api/v1/zip`, `/api/v1/links`:

| index | Ý nghĩa |
|---|---|
| `2` | chỉ ảnh số 2 |
| `1,3` | ảnh 1 và ảnh 3 |
| `1-3` | ảnh 1 đến 3 |
| `all` | tất cả ảnh |

Nếu chọn nhiều ảnh ở `/api/v1/get` hoặc `/api/v1/image`, server trả về một file ZIP chứa đúng các ảnh đó. Muốn lưu thẳng từng ảnh vào thư viện Ảnh thì dùng `/api/v1/links`.

## Cách dựng (7 bước)
1. **Nhận URL từ Đầu vào Shortcut** hoặc **Lấy Bảng nhớ tạm** → đặt biến `link`.
2. **Lấy nội dung của URL**: POST `https://TEN-APP.onrender.com/api/v1/choices`, Biểu mẫu `url` = `link`, `key` = KEY.
   Kết quả là danh sách dòng: `1`, `2`, `3`, `4`, `all` (bài video thì là `video`, `music`).
3. **Tách văn bản** theo **Dòng mới**.
4. **Chọn từ Danh sách** (bật **Chọn nhiều**) → bạn tích ảnh 1, 3… hoặc `all`.
5. **Kết hợp văn bản** các mục đã chọn, dấu phân cách **Tự chỉnh** `,` → đặt biến `chon`.
6. **Lấy nội dung của URL**: POST `https://TEN-APP.onrender.com/api/v1/links`, Biểu mẫu `url` = `link`, `key` = KEY, `kind` = `images`, `index` = `chon`.
7. **Tách văn bản** theo **Dòng mới** → **Lặp lại với từng mục**: **Lấy nội dung của URL** (mục lặp) → **Lưu vào Album ảnh**.

Nếu bài là video, bước 4 sẽ hiện `video`/`music`: thêm **Nếu** `chon` là `video` thì gọi `/api/v1/get` với `type=video`, còn `music` thì `type=music` rồi **Lưu vào Tệp**.

## Bản đơn giản: chỉ cần 1 ảnh
Hỏi số ảnh bằng **Yêu cầu nhập** (kiểu Số) → biến `n` → **Lấy nội dung của URL** POST `/api/v1/get` với `url`, `key`, `type` = `image`, `index` = `n` → **Lưu vào Album ảnh**.
Thêm `fmt` = `jpg` nếu ảnh gốc là WebP/HEIC mà Ảnh trên iPhone không mở được.


---

# Sửa lỗi "Get Contents of URL failed because Shortcuts couldn't convert from Rich Text to URL"

**Nguyên nhân:** trong bước "Lặp lại với từng mục", một dòng không phải là link (thường là dòng thông báo lỗi do chọn sai loại, ví dụ yêu cầu `kind=images` cho bài video). Shortcuts cố biến chữ đó thành URL nên báo lỗi.

**Đã sửa ở server:** `/api/v1/links` giờ tự trả đúng thứ bài đăng có (bài video mà yêu cầu ảnh thì trả link video), và luôn trả văn bản thuần. Thêm tham số `choice` nhận thẳng giá trị từ `/api/v1/choices`.

**Cách dựng gọn, không cần Nếu/Otherwise (khuyến nghị):**
1. **Nhận văn bản từ Đầu vào Shortcut** (nếu trống: Bảng nhớ tạm) → biến `link`.
2. **Lấy nội dung của URL**: POST `https://TEN-APP.onrender.com/api/v1/choices` (Biểu mẫu `url`, `key`).
3. **Tách văn bản** theo dòng mới → **Chọn từ Danh sách** (bật Chọn nhiều).
4. **Kết hợp văn bản** bằng `,` → biến `chon`.
5. **Lấy nội dung của URL**: POST `/api/v1/links` với `url`, `key`, `choice` = `chon`.
6. **Nếu** kết quả **bắt đầu bằng** `http`: **Tách văn bản** theo dòng mới → **Lặp lại với từng mục** → **Lấy nội dung của URL** (mục lặp) → **Lưu vào Album ảnh**. **Nếu không**: **Hiển thị kết quả** (là thông báo lỗi).

Nếu bạn vẫn dùng nhánh Nếu: ô giá trị của "Otherwise if Selected Item is …" phải điền `music` (trong ảnh bạn gửi ô này đang trống), và các nhánh nên so sánh với đúng chữ thường `video` / `music` mà `/choices` trả về. Nhạc không lưu được bằng "Lưu vào Album ảnh", dùng **Chia sẻ** hoặc **Lưu vào Tệp**.

# AI "nghe" video

- Server tách âm thanh video thành WAV 16 kHz rồi mới đưa Whisper, tự tăng âm lượng khi tiếng nhỏ, và **bỏ qua Whisper nếu video im lặng/không có tiếng** (không còn câu bịa kiểu "Hãy subscribe cho kênh Ghiền Mì Gõ").
- Thêm `speech=vi` vào `/api/v1/ai` để Whisper nghe tiếng Việt chuẩn hơn khi có nhạc nền; trên web chọn "Tiếng Việt" ở ô ngôn ngữ cạnh nút Phân tích.
- Video chỉ có nhạc thì AI xem 4 khung hình để mô tả nội dung.


---

# Sửa lỗi: Phím tắt báo "Đã lưu" nhưng thư viện Ảnh không có gì (Facebook…)

**Nguyên nhân:** "Hiển thị thông báo Đã lưu" luôn chạy dù bước tải thất bại. Khi nguồn (Facebook) chặn máy chủ, server từng trả về trang HTML/JSON lỗi với đuôi .jpg; "Lưu vào Album ảnh" nhận file hỏng nên lặng lẽ không lưu gì. Ảnh WebP cũng bị Ảnh trên iPhone bỏ qua.

**Đã sửa ở server (không cần đổi Phím tắt vẫn đỡ hơn):**
- Server không còn coi trang HTML/JSON là file; nguồn trả sai loại thì báo lỗi thật.
- `/api/v1/links` mặc định **thử mở từng file trước** và chỉ trả link tải được. Nếu không có file nào tải được, trả HTTP 424 và một dòng bắt đầu bằng `LỖI:` kèm lý do.
- Ảnh WebP/AVIF tự đổi sang JPEG khi tải.

**Sửa Phím tắt để không báo sai nữa:**
1. Sau bước **Lấy nội dung của URL** (`/api/v1/links`), thêm **Nếu** `Nội dung của URL` **bắt đầu bằng** `http`.
2. Trong nhánh **Nếu**: Tách theo dòng mới → Lặp lại → Lấy nội dung của URL → Lưu vào Album ảnh → (sau Kết thúc lặp) **Hiển thị thông báo** "Đã lưu".
3. Trong nhánh **Nếu không**: **Hiển thị kết quả** (`Nội dung của URL`), đó là lý do thật.
Đặt thông báo "Đã lưu" **trong nhánh thành công**, không đặt ngoài.

Nếu vẫn lỗi với Facebook: bài thường phải công khai; bài riêng tư/nhóm cần cookie (`COOKIES_TXT`) hoặc `OUTBOUND_PROXY` trên Render.


---

# Log về Discord (DISCORD_WEBHOOK) & dùng chung một khoá Groq

**Discord webhook:** tạo ở kênh Discord: Cài đặt kênh → Tích hợp → Webhook → Tạo webhook → Sao chép URL. Dán vào Render → Environment → `DISCORD_WEBHOOK`.
Mỗi lần có người tải hoặc dùng AI (web lẫn API), kênh đó nhận một thẻ gồm: link, IP, trình duyệt/app, tiêu đề hoặc lỗi. Lọc bớt loại log bằng `DISCORD_EVENTS=get,error` (mặc định gửi cả `info,get,ai,ingest,error`).
Đây là log phía máy chủ (server gọi Discord trực tiếp, không qua trình duyệt người dùng), nên người dùng không thấy request này khi họ tự kiểm tra mạng trên máy họ — đó là cách Discord webhook hoạt động, không có mẹo che giấu nào thêm. Vì log chứa IP/link thật của người dùng, nếu bạn chia sẻ máy chủ cho người khác dùng thì nên nói rõ điều này với họ.

**Dùng chung một khoá Groq:** đặt `GROQ_API_KEY` trong Render > Environment (đã hỗ trợ sẵn). Mọi người dùng web hoặc API đều dùng được AI mà không cần tự nhập khoá; ai muốn dùng khoá riêng vẫn có thể gửi header `X-Groq-Key` để không dùng chung hạn mức với người khác.


---

# Phím tắt "Giải bài": chụp màn hình hoặc nhập vào ô

API: `POST {BASE}/api/v1/solve` (không cần link). AI đọc ảnh, **chép lại đề cho bạn kiểm tra**, rồi giải và tự kiểm tra phép tính.

## Cách A: chụp màn hình đề bài (đơn giản nhất)
1. **Chụp ảnh màn hình** (hoặc **Chọn ảnh** nếu đề nằm trong thư viện).
2. **Chuyển đổi ảnh** → định dạng **JPEG** (tránh lỗi định dạng lạ; server vẫn đọc được PNG/HEIC/WebP).
3. **Lấy nội dung của URL**: địa chỉ `{BASE}/api/v1/solve`, Phương thức **POST**, Nội dung yêu cầu **Biểu mẫu**:
   - `key` = API key của bạn (kiểu Văn bản)
   - `image` = **Ảnh đã chuyển đổi** (kiểu **Tệp**, đừng chọn Văn bản)
   - `format` = `text`
4. **Hiển thị kết quả** (`Nội dung của URL`).

## Cách B: gõ đề vào ô hiện lên
1. **Hỏi nhập liệu** (Văn bản), câu hỏi: "Nhập đề bài".
2. **Lấy nội dung của URL**: `{BASE}/api/v1/solve`, **POST**, Biểu mẫu: `key`, `text` = **Nhập được cung cấp**, `format` = `text`.
3. **Hiển thị kết quả**.

## Gộp cả hai trong một phím tắt
**Chọn từ Menu** ("Ảnh chụp màn hình" / "Nhập chữ") rồi làm nhánh A hoặc B tương ứng. Muốn vừa gửi ảnh vừa chỉ định câu: thêm `text` = "giải câu 3" cùng với `image`.
Chạy từ **Nút Sườn/Back Tap/Siri**: thêm bước đầu **Chụp ảnh màn hình** rồi chạy nhánh A, không cần mở app.

## Tham số hữu ích (thêm vào Biểu mẫu)
| Tham số | Giá trị | Tác dụng |
|---|---|---|
| `mode` | `full` (mặc định) · `answer` · `explain` · `hint` · `check` | đáp án + từng bước · chỉ đáp án · giảng như dạy học · chỉ gợi ý, không cho đáp án · chấm bài làm của bạn (bài làm đặt trong `text`) |
| `subject` | `auto` · `math` `physics` `chemistry` `biology` `code` `english` `literature` `history` `geography` `economics` | ép môn học (mặc định AI tự nhận) |
| `level` | vd `lớp 9`, `đại học` | giải thích đúng trình độ |
| `lang` | `vi` `en` `zh` `ja` `ko`… | ngôn ngữ trả lời |
| `think` | `low` · `medium` · `high` | bài khó dùng `high` (chậm hơn) |
| `part` | `answer` · `steps` · `question` | thay cho `format=text`: chỉ trả đúng một phần để **Hiển thị thông báo** hoặc **Đọc to** |

Ví dụ "chỉ đọc to đáp án": Biểu mẫu `key`, `image`, `part=answer` → **Đọc văn bản** (`Nội dung của URL`).

## Lưu ý
- Ảnh càng rõ, cắt sát phần đề thì AI đọc càng chuẩn. Kết quả luôn kèm dòng "📝 Đề: …" là đề AI **đã đọc được**: nếu dòng này sai thì đáp án cũng sai, hãy chụp lại.
- Lỗi trả về bắt đầu bằng `LỖI:` (vd. "AI không đọc được đề bài trong ảnh"), Phím tắt hiện ra bình thường.
- AI có thể sai, nhất là bài nhiều bước hoặc có hình vẽ phức tạp. Dùng `mode=hint` hoặc `mode=check` nếu bạn muốn học thay vì chép đáp án.
- Dùng chung hạn mức Groq miễn phí; mặc định 30 bài mỗi 10 phút mỗi IP (`SOLVE_LIMIT`). Cùng một đề gửi lại trong 30 phút trả ngay từ bộ nhớ đệm.


---

# Log lỗi tự động & AI chẩn đoán gửi Discord

Cần `DISCORD_WEBHOOK` và `GROQ_API_KEY` trên Render. Mỗi lỗi mới của server:
1. được ghi lại (đã xoá khoá/mật khẩu/proxy) và gửi thẻ **error** lên Discord;
2. chương trình tự định vị chỗ nghi ngờ trong code (traceback, dòng chứa đúng câu thông báo lỗi, route và các hàm nó gọi), AI đọc các hàm đó **kèm số dòng** rồi gửi thẻ **diagnosis**: nguyên nhân, loại lỗi (code / cấu hình / cấu hình Phím tắt / nguồn chặn IP / người dùng), vị trí `app.py:dòng`, cách xử lý (kèm tên biến môi trường cần đặt), cách kiểm tra, độ chắc chắn;
3. nếu là lỗi code, AI viết lại đúng hàm đó; chương trình kiểm tra bằng `ast` (cú pháp, tên biến chưa định nghĩa) rồi đính kèm file **`.diff`** (chưa chạy thử, không tự áp dụng, hãy đọc kỹ trước khi sửa).

Cả lỗi **cấu hình Phím tắt** (vd. gửi GET trống tới `/solve`) cũng được ghi, kèm “hình dạng yêu cầu” (phương thức, kiểu nội dung, tên trường, không có giá trị) để AI chỉ đúng chỗ cần sửa.

Chống ngốn hạn mức Groq dùng chung: cùng một lỗi tối đa 1 lần phân tích mỗi 15 phút, tối đa 10 lần mỗi giờ (`ERROR_AI_COOLDOWN`, `ERROR_AI_HOURLY`); lỗi vượt hạn mức xếp hàng và tự được phân tích khi còn lượt. Tắt hẳn: `ERROR_AI=0`.

Xem lại và gọi AI thủ công (cần `API_KEY`):
- Danh sách: `{BASE}/api/v1/errors?key=KEY&format=text`
- Chi tiết + traceback: thêm `&id=3`
- Nhờ AI chẩn đoán: thêm `&analyze=1` (thêm `&force=1` để chẩn đoán lại)
Làm Phím tắt "Xem lỗi server": **Lấy nội dung của URL** (GET, địa chỉ trên) → **Hiển thị kết quả**.

**Minh bạch:** để phân tích, các hàm liên quan trong `app.py` và traceback (đã xoá bí mật) được gửi tới Groq; AI chỉ nhận văn bản và không có công cụ chạy lệnh. Log lỗi nằm trong bộ nhớ và file tạm nên mất khi Render khởi động lại (gói miễn phí tự ngủ sau 15 phút không dùng), kênh Discord mới là nơi lưu lâu dài. Chẩn đoán của AI chỉ là gợi ý, hãy đọc trước khi sửa code. Nếu người khác dùng chung máy chủ, nên nói rõ với họ rằng IP, link và đề bài họ gửi được ghi vào log Discord của bạn.

## Cập nhật v6: Threads, lỗi 424, giải bài, file lên Discord

- **Threads**: server đọc thẳng video/ảnh/album gốc của bài. Nếu Threads chặn IP máy chủ và chỉ còn ảnh xem trước, API trả lỗi (`preview_only`) thay vì lưu một ảnh giống chụp màn hình. Trong Phím tắt, dòng `LỖI: …` không bắt đầu bằng `http` nên nhánh **Nếu … bắt đầu bằng http** sẽ hiện thông báo lỗi thay vì "Đã lưu". Thêm `&allow_preview=1` vào URL nếu bạn vẫn muốn tải ảnh xem trước.
- **Lỗi nguồn là HTTP 424** (không còn 502/504). Phím tắt chỉ cần đọc nội dung phản hồi, không cần kiểm tra mã.
- **/api/v1/solve báo "Chưa có đề bài" dù đã gửi ảnh chụp màn hình**: trong bước **Lấy nội dung của URL** đặt Phương thức **POST**, Body **Biểu mẫu**, thêm trường (tên tuỳ ý, ví dụ `image`) kiểu **Tệp** và chọn ảnh chụp màn hình; thêm trường **Văn bản** `text` nếu muốn gửi kèm chữ. Đừng chọn kiểu Văn bản cho ảnh. Nếu vẫn lỗi, thông báo mới ghi "Server nhận được: …", cho biết Phím tắt đang gửi những trường nào.
- **Nhanh hơn**: dùng `choice=` của `/api/v1/choices` thay vì nhiều bước Nếu; `/api/v1/links` không còn thử mở từng link TikTok (đã đáng tin) nên trả gần như ngay.
- **Nhắc minh bạch**: nếu máy chủ bật `DISCORD_WEBHOOK`, video/ảnh bạn tải qua máy chủ (không phải ảnh chụp màn hình giải bài) cũng được gửi lên kênh Discord của người quản trị.


---

# Cập nhật v7: sửa "Chưa có đề bài", tải hàng loạt, tải theo kênh

## Sửa Phím tắt "Auto Solve from Share Sheet" bị "Chưa có đề bài"

Triệu chứng: bước **Show** hiện “Chưa có đề bài…”. Nguyên nhân thường gặp nhất: ở các bước **Get contents of URL** (Lấy nội dung của URL) bạn chỉ điền địa chỉ `…/api/v1/solve` nên Phím tắt gửi một yêu cầu **GET trống**. Dòng đó đang **thu gọn** (chỉ thấy URL và mũi tên ›); ảnh ở bước **Convert … to JPEG** hay chữ ở bước **Ask for Text** phía trên **không tự đi theo**, phải đặt vào **Request Body**.

Thử nhanh server có ổn không (trình duyệt trên iPhone): mở `{BASE}/api/v1/solve?key=KEY&text=2%2B2&format=text`. Ra đáp án thì server đúng, lỗi nằm ở Phím tắt.

Sửa **cả 3 bước Get contents of URL** trong Phím tắt của bạn (nhánh Share Sheet, nhánh “Chụp ảnh màn hình”, nhánh “Nhập văn bản”). Ở mỗi bước, bấm mũi tên **›** ở cuối dòng để mở rộng rồi đặt:

| Nhánh | Method | Request Body | Các field (bấm **Add new field**) |
|---|---|---|---|
| Share Sheet (`Shortcut Input` → JPEG) | **POST** | **Form** | **File**: Key `image`, Value = biến **JPEG image** (kết quả bước Convert) · **Text**: Key `key`, Value = API key · **Text**: Key `format`, Value `text` |
| Chụp ảnh màn hình (`Take screenshot` → JPEG) | **POST** | **Form** | như trên, Value của `image` = **JPEG image** của bước Convert ngay phía trên |
| Nhập văn bản (`Ask for Text`) | **POST** | **Form** | **Text**: Key `text`, Value = biến **Provided Input** (kết quả Ask for Text) · `key` · `format` = `text` |

Lưu ý khi chọn biến cho `image`: bấm vào ô Value, chọn biến **JPEG image** (không phải “Screenshot”, không phải “Shortcut Input” nếu bạn đã Convert). Field `image` phải là kiểu **File**, không phải Text. Sai kiểu thì lỗi mới sẽ ghi “Server nhận được: …” cho biết Phím tắt thực sự gửi gì (vd. “POST, kiểu multipart/form-data, image: chữ 12 ký tự”).

Bản gọn nhất (3 bước, không cần Convert vì server đọc được PNG/HEIC): **Take screenshot** (hoặc nhận ảnh từ Share Sheet) → **Get contents of URL** (`{BASE}/api/v1/solve`, POST, Form: `image` = File ảnh, `key`, `format=text`) → **Show** `Contents of URL`.

Mọi lỗi kiểu này đều tự gửi lên Discord kèm chẩn đoán của AI (loại “cấu hình Phím tắt”).

## Phím tắt "Tải hàng loạt" (nhiều link thành một ZIP)
1. **Hỏi nhập liệu** (Văn bản nhiều dòng): "Dán các link, mỗi dòng một link". (Hoặc **Nhận** văn bản từ Share Sheet.)
2. **Lấy nội dung của URL**: `{BASE}/api/v1/batch`, **POST**, Form: `key`, `urls` = **Nhập được cung cấp** (Text), `wait` = `75`, `format` = `text`.
3. **Nếu** `Nội dung của URL` **bắt đầu bằng** `http` →
   **Lấy nội dung của URL** (chính link ZIP đó, GET) → **Lưu tệp** (chọn thư mục Tệp).
   **Khác**: **Hiển thị thông báo** `Nội dung của URL` (đang xử lý hoặc lỗi).

Hết `wait` mà ZIP chưa xong thì dòng trả về là `ĐANG XỬ LÝ 2/5: <link>`; mở link đó (hoặc chạy lại bước 2 với `GET {BASE}/api/v1/batch/ID?key=KEY&format=text`) để lấy link ZIP khi xong. `kind` = `video` · `music` · `images` · `all`. Tối đa 30 link mỗi ZIP; ZIP giữ 30 phút.

## Phím tắt "Tải theo kênh" (N video mới nhất của @username)
1. **Hỏi nhập liệu**: "Tên kênh (vd. @tiktok)". Thêm **Hỏi nhập liệu** (Số) “Bao nhiêu video?” (1–30).
2. **Lấy nội dung của URL**: `{BASE}/api/v1/channel`, **POST**, Form: `key`, `user` = tên kênh, `count` = số video, `zip` = `1`, `wait` = `75`, `format` = `text`.
3. Giống bước 3 của "Tải hàng loạt": nếu bắt đầu bằng `http` thì lấy file ZIP và **Lưu tệp**.
Muốn tự chọn video: bỏ `zip=1`, giữ `format=text` để nhận mỗi dòng một link video, đưa vào **Chọn từ Danh sách** rồi nối các link đã chọn vào `urls` của `/api/v1/batch`.

Cần `TIKWM_RELAY` đã cập nhật: dán lại `cloudflare-api-worker.js` mới (có `/relay-user`) vào Worker, xem `CLOUDFLARE_API.md`.

## Trên web
Ô nhập chính nhận cả `@tên_kênh` (hiện lưới video để chọn rồi tải ZIP) và nhiều link cùng lúc (tự mở **Tải hàng loạt**). Mục **Lịch sử gần đây** nhớ 20 link trong chính trình duyệt này (không cần tài khoản, không gửi đi đâu); chạm để tải lại, **Xoá lịch sử** để dọn.

## Cập nhật v7.3
- Webhook khi ZIP xong: thêm tham số `webhook=https://...` (hoặc webhook Discord) vào `/api/v1/batch` để máy chủ báo khi xong, Phím tắt không cần chờ.
- Chia sẻ có thời hạn: `POST /api/share` rồi gửi link `/s/<id>` cho người khác.
