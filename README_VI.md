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
- Chọn nhân vật đã đặt để xem thông tin; **Q** dùng tuyệt kỹ khi đủ 100 Dao, mana và Qi; tuyệt kỹ có hồi chiêu riêng.
- Dùng nút âm thanh và tốc độ trong game. Hỗ trợ chuột và cảm ứng; nên chơi ở
  chế độ màn hình ngang.

Tiến trình được lưu trong trình duyệt. Hãy xuất bản lưu trong game trước khi xóa
dữ liệu trình duyệt hoặc chuyển máy. Dùng lại cùng cổng localhost để trình duyệt
nhận ra bản lưu.

Đây là bản game chơi được, chuyển thể gọn từ tài liệu thiết kế bạn gửi; xem
[tình trạng triển khai](docs/BUILD_STATUS.md) để biết phần đã kiểm thử và giới hạn.

## Bản 1.3

- **Mỗi ải có nhạc riêng:** 9 chủ đề × 3 phối khí theo giai đoạn, cộng nhạc sảnh,
  tổng 28 bản nhạc offline. Khi quái đông hoặc có áp lực tinh anh/boss, nhạc tự
  chuyển cao trào; vẫn giữ âm sắc cổ cầm, cổ tranh, tỳ bà, sáo và bộ gõ.
- **Đợt cuối dồn cả 5 lane:** 35–51 quái trong cùng đợt tổng công kích. Lính đông
  quân có 80% HP và 85% ATK thường; tinh anh/thủ lĩnh vẫn giữ chỉ số riêng mạnh hơn.
  Đội hình sát thương diện rộng, đỡ đòn và khắc chế theo vùng có vai trò rõ hơn.
- Nút **A:ON / A:OFF** cạnh tốc độ, hoặc phím **A**, bật/tắt tự dùng ultimate.
  Auto xét tầm của ultimate, lượng mana/Qi/Dao và hồi chiêu; chờ mục tiêu đáng dùng
  chiêu, tự buff/hồi phục khi đồng đội cần. Cài đặt được giữ cho trận tiếp theo.
- 16 câu thoại **tiếng Anh** mới, chia câu và thay đổi nhịp, ngắt nghỉ, năng lượng
  để hợp tính cách. Đây vẫn là giọng tổng hợp được đóng gói sẵn, không cần mạng.
- Thiên phú đã học có nền xanh, viền vàng và dấu tích; chưa học được làm xám.
  Mốc kế tiếp có viền ngọc. Vẫn chọn được mốc khóa để đọc điều kiện/chỉ số.
- Hiệu ứng riêng cho từng cultivator: linh tuyền, kiếm trận, sen lửa, băng tinh,
  địa chấn, lôi kích, lá hồi phục và trận đồ. Tư thế tung chiêu được giữ khi bị đánh.
- Mỗi lần vào ải có **3 trang hướng dẫn kèm hình**. Trận tạm dừng hoàn toàn cho
  đến khi bấm **Enter Battle**; nút **?** và menu tạm dừng mở lại hướng dẫn.
- Cảnh nền kiểu RPG 16-bit được thiết kế mới: phủ gỗ bến sông lồng đèn, đài ngọc
  trên núi nổi và lăng mộ đồng dưới lòng đất. Cung điện và ba pháp khí cứu nguy
  có thiết kế riêng, không dùng chung một hình đổi màu.

Vẫn giữ 8 nhân vật, 9 ải, mana riêng từng đơn vị, Qi tối đa 320 và cây thiên phú
hai nhánh. Mỗi hàng chỉ có một lần cứu nguy. Chơi lại ải đã thắng vẫn nhận ít đá
để nâng thêm thiên phú. Xem **Menu → Cultivator / Enemy Skills** để đọc hệ số,
chi phí và phạm vi từng ô; nút **Range** đổi vùng đánh thường/skill/ultimate.

Để cập nhật: tắt server Python cũ, giải nén bản mới rồi chạy lại `python run.py`.
Giữ cùng trình duyệt và cổng localhost để dùng tiếp bản lưu. Nên xuất bản lưu
trước khi đổi máy hoặc xóa dữ liệu trình duyệt.
