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

## Bản 1.2

- Giữ 8 cultivator và 9 ải, 12–21 wave/ải. Mỗi trận có giai đoạn chuẩn bị,
  tăng áp lực và tổng công kích; tinh anh xuất hiện nhiều dần về cuối.
- Mana riêng từng nhân vật; kỹ năng tự động tiêu mana. Ultimate cần đủ mana,
  Qi và 100 Dao, kèm hồi chiêu. Nút **AUTO OFF** giúp giữ mana cho ultimate.
- Qi tối đa 320 (thiên phú Treasury nâng lên 360 khi Yun còn sống). Chỉ đặt được
  3 Yun; giá trị orb lần lượt 100% / 80% / 60%. Không còn tích 999+ Qi.
- Rê chuột vào nhân vật hoặc thẻ để xem tầm; nút **Range** đổi giữa đánh thường,
  skill và ultimate. **Menu → Cultivator / Enemy Skills** mở sách kỹ năng khi
  tạm dừng: hệ số, sát thương, mana, hồi chiêu, số mục tiêu và phạm vi từng ô.
- Cây thiên phú mỗi nhân vật có 2 nhánh, mỗi nhánh 5 mốc với 2 thiên phú đặc biệt.
  Đá nhận từ chiến thắng; chơi lại ải đã thắng vẫn có phần thưởng nhỏ để nâng tiếp.
- HP quái tăng 5% lũy tiến mỗi ải. Quái tinh anh có thêm HP, giáp và sát thương;
  thủ lĩnh nhỏ buff tốc độ quái trong bán kính 1,5 ô.
- Ba vùng có cảnh quan, kiến trúc và pháp khí cứu nguy riêng: Jade River Ark,
  Heaven Sword Array, Soul-Sealing Bell. Mỗi hàng vẫn chỉ được cứu một lần.
- Nghi thức riêng từng vùng: làm dịu thủy triều, thanh tẩy linh mạch hoặc soi hồn.
  Mỗi lần tốn 35 Qi, hồi 30 giây; xem **Region Mechanics** để học cơ chế chi tiết.
- Sprite nhân vật 64×64, animation riêng cho idle/đánh thường/skill/ultimate.
- 16 câu thoại **tiếng Anh** cho triệu hồi và ultimate, có phụ đề và âm lượng riêng.
  Đây là giọng tổng hợp, được đóng gói sẵn để phát offline.
- Nhạc sảnh và 3 phối khí theo giai đoạn cho mỗi vùng, phong cách cổ phong với
  âm sắc cổ cầm, cổ tranh, tỳ bà, sáo và bộ gõ. Nhạc được tổng hợp, không phải
  bản thu nhạc cụ acoustic. SFX riêng cho từng nhân vật vẫn được giữ.
- Sảnh có thêm chuyển động, bố cục nút cân đối; VT323 được đóng gói sẵn.

Để cập nhật: tắt server Python cũ, giải nén bản mới rồi chạy lại `python run.py`.
Giữ cùng trình duyệt và cổng localhost để dùng tiếp bản lưu. Các nhánh A/B từ bản
cũ giữ hiệu ứng cũ và được tính là mốc 3; mua mốc tiếp theo áp dụng đầy đủ chỉ số
nhánh mới. Hãy xuất bản lưu trước khi chuyển máy hoặc xóa dữ liệu trình duyệt.
