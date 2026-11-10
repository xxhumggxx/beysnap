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
| `AI_LIMIT` | không | số lượt AI mỗi 10 phút mỗi IP (mặc định 10) |

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
| `/api/v1/ai` | `task=summary\|caption\|hashtags\|transcript\|srt\|translate`, `lang=vi\|en\|...` |
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
