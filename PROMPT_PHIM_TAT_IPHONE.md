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
6) POST /api/v1/ai     -> task = summary | caption | hashtags | transcript | srt | translate, lang = vi | en | zh | ja | ko ...
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
- Cuối cùng cho danh sách kiểm tra và cách xử lý lỗi: 401 (sai key), 403 (nguồn chặn), 502 (nguồn không phản hồi), chờ lâu (server đang ngủ).
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
