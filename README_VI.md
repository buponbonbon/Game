# Chơi VAN DAO trên máy của bạn

Bạn chỉ cần **Python 3.10 trở lên** và một trình duyệt hiện đại (Chrome, Edge,
Firefox hoặc Safari). Khi cài Python trên Windows, chọn **Add Python to PATH**.

1. Trên GitHub, chọn **Code → Download ZIP**.
2. Giải nén toàn bộ tệp ZIP.
3. Trên Windows: nhấp đúp **play.bat**. Hoặc mở Terminal trong thư mục vừa giải nén:

   ```bash
   python run.py
   ```

   Trên macOS/Linux, nếu cần thì dùng `python3 run.py`.

4. Trình duyệt tự mở game. Giữ cửa sổ Terminal đang chạy. Khi muốn tắt server,
   nhấn **Ctrl+C** trong Terminal.

Không cần cài Pygame, npm hay tải tài nguyên từ CDN. Không mở trực tiếp tệp HTML:
game cần server Python để xử lý trận đấu. Nếu trình duyệt không tự mở, mở địa chỉ
local được in trong Terminal.

## Cách chơi nhanh

- Chọn thẻ nhân vật, sau đó chọn ô trống trên chiến trường để triệu hồi.
- Quái đi từ phải sang trái. Bạn thua khi mất cả ba ấn phong của cổng.
- Màn đầu: đặt **Yun** và **Shen Zhu** ở hàng giữa. Yun sinh Qi để mua thêm quân;
  Shen Zhu tấn công. Chuẩn bị thêm quân ở hàng trên/dưới khi được báo đợt mới.
- Phím **1–8** chọn thẻ; **Space** tạm dừng/tiếp tục; **Escape** hủy chọn.
- Chọn nhân vật đã đặt để xem thông tin; **Q** dùng tuyệt kỹ khi đủ 100 Dao.
- Dùng nút âm thanh và tốc độ trong game. Hỗ trợ chuột và cảm ứng; nên chơi ở
  chế độ màn hình ngang.

Tiến trình được lưu trong trình duyệt. Hãy xuất bản lưu trong game trước khi xóa
dữ liệu trình duyệt hoặc chuyển máy. Dùng lại cùng cổng localhost để trình duyệt
nhận ra bản lưu.

Đây là bản game chơi được, chuyển thể gọn từ tài liệu thiết kế bạn gửi; xem
[tình trạng triển khai](docs/BUILD_STATUS.md) để biết phần đã kiểm thử và giới hạn.
