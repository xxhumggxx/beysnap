# Phím tắt tải trực tiếp (không qua server Render)

Dùng khi Render bị tikwm chặn IP (lỗi `HTTP 403 (tikwm chặn IP máy chủ)`).
iPhone của bạn gọi thẳng tikwm bằng mạng nhà/4G nên thường không bị chặn, và không tốn băng thông Render.
Hạn chế: không có AI, không có ZIP, tikwm giới hạn 1 yêu cầu mỗi giây.

## Video
1. **Receive** URLs và Text từ **Share Sheet**.
2. **Get Contents of URL** → `https://www.tikwm.com/api/`, Method **POST**, Request Body **Form**:
   - `url` = *Shortcut Input*
   - `hd` = `1`
3. **Get Dictionary Value** → `data` từ *Contents of URL*.
4. **Get Dictionary Value** → `hdplay` từ *Dictionary Value* ở bước 3. **Set Variable** `link`.
5. **If** `link` **does not have any value** → **Get Dictionary Value** `play` từ dữ liệu bước 3 → **Set Variable** `link` → **End If**.
6. **Replace Text**: trong `link`, tìm `^/`, thay bằng `https://www.tikwm.com/`. Bấm *Show More* và bật **Regular Expression**. (Bước này để xử lý link tương đối; link đầy đủ thì giữ nguyên.)
7. **Get Contents of URL** (GET) ← *Replaced Text*.
8. **Save to Photo Album** ← *Contents of URL*.

Bản có watermark: dùng khoá `wmplay` thay cho `hdplay`.

## Ảnh slideshow
Sau bước 3: **Get Dictionary Value** `images` → **Repeat with Each** → trong vòng lặp: **Replace Text** (như bước 6) → **Get Contents of URL** → **Save to Photo Album**. Thêm **Wait** 1 giây cuối vòng lặp.

## Nhạc
Khoá `music` → Replace Text → Get Contents of URL → **Save File**.

Nếu cũng báo 403 ngay trên iPhone thì tikwm đang chặn cả mạng của bạn, hãy thử lại sau ít phút.
