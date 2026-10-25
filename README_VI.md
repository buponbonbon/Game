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

## Bản 1.7: camera cận cảnh và UI mới

- Sảnh mặc định **phóng 1,85×**, camera lướt theo nhân vật. Nút **+ / −** chỉnh
  từ 1,45 đến 2,4×. Cụm chân dung, tiền tệ có icon, minimap và thanh chức năng
  đứng yên trên màn hình, không chạy theo cảnh.
- **M / MAP:** bản đồ giấy minh họa riêng, có các công trình, đường đi và vị trí
  người chơi. Chọn địa điểm → **Travel Here** để đi tới; **Open Facility** mở nhanh.
- Giao diện HTML/CSS rõ nét, nút có icon, hội thoại NPC và bảng nhiệm vụ mới.
  Bỏ dòng “Click to approach”; chỉ hiện nhãn NPC quanh khu vực đang đứng.
- Mỗi avatar có **8 frame đi bộ cho mỗi hướng**, tư thế đứng riêng và căn điểm
  đặt chân. Nhịp bước theo quãng đường; không dừng một frame tại từng nút đường
  đi, không khởi động lại hoạt ảnh ở mỗi nút.
- Vẫn dùng WASD/mũi tên, Shift để chạy, E/Enter để nói chuyện. Vị trí và tiến
  trình được lưu như trước; lưu vị trí không làm mới lại dữ liệu nhân vật chiến đấu.

[Tham khảo UI và chẩn đoán chuyển động](docs/UI_REFERENCE_1_7.md) ghi rõ nguồn đã
đọc và các trang Gunny chính thức bị mạng môi trường chặn.

## Bản 1.6: Thiên Cung môn phái

Sảnh chính được làm lại theo hướng **HD-2D**: tiên cung giữa núi mây, sân đá,
hồ sen, lò luyện đan, vườn linh dược, chợ đèn lồng và cổng thử thách. Cảnh nền gốc
1672×941, nhân vật chi tiết hơn, có hoạt ảnh đi bốn hướng. Chất lượng hình ảnh
được nâng qua độ phân giải và thiết kế; không gọi số bit là thước đo độ đẹp.

- **WASD/phím mũi tên** để đi, giữ **Shift** để chạy, hoặc nhấp vào đất/NPC.
  **E/Enter** nói chuyện; **MAP, Tab hoặc M** mở danh sách 8 điểm đến và tự tìm đường.
- NPC mở chiến dịch, thiên phú, quái vật chí, luyện đan, trồng trọt, cửa hàng,
  nhiệm vụ và thử thách. Thanh dưới cho phép mở nhanh các chức năng.
- Nhiệm vụ ghi mục tiêu, tiến độ và thưởng; có thể ghim theo dõi ở góc sảnh.
  Tiến độ vẫn tự tính như trước, không bắt buộc nhận lại nhiệm vụ để được tính.
- **Avatar** đổi ngoại hình thành Shen Zhu hoặc Yun; Mu Qing mở sau Wharf III.
  Ngoại hình không đổi chỉ số chiến đấu. Vị trí, ngoại hình và nhiệm vụ đang
  theo dõi được lưu cùng bản lưu. Có nút tắt chuyển động trang trí trong Avatar.
- Đèn lồng, chuông ngọc và cờ đã sở hữu xuất hiện trong sảnh mới. Có hiệu ứng
  ánh sáng, gợn nước và cánh hoa. Giao diện sảnh dùng chữ rõ, làm mượt hình ảnh.

Vẫn chỉ cần Python và trình duyệt. Tất cả ảnh đã nằm trong bản tải, bản lưu cũ
vẫn dùng được. Giữ nguyên 8 nhân vật chiến đấu và 9 ải chiến dịch.

## Bản 1.5

- **Animation mới:** 336 khung hình riêng cho 8 cultivator và 13 loại quái/pháp đàn.
  Có chuẩn bị đánh, ra đòn, thu chiêu, dùng skill, ultimate, trúng đòn và tử trận;
  quái có chu kỳ di chuyển 4 khung. Nhịp đánh dùng thời gian của trận, tạm dừng
  cũng dừng animation. Tư thế đứng dùng một khung. Hình được tải theo nhu cầu.
- **Dễ đọc trận hơn:** nền chiến trường dịu xuống, pháp khí cứu nguy gọn hơn,
  thanh máu thông minh, gom số sát thương và giảm độ đậm hiệu ứng. Vào
  **Settings → Battle Visuals** để chỉnh. Cảnh báo ghi rõ vùng tròn/đoạn/lane và
  số giây trước khi chiêu trúng.
- **Quái tinh anh phối hợp:** Guard bảo vệ tinh anh khác ở gần; Mender niệm hồi
  phục, có thể ngắt bằng sát thương hoặc đóng băng. Xem **Squad Tactics** trong
  menu tạm dừng để đọc phạm vi và cách khắc chế chính xác.
- **Regional Trials** ở sảnh: hộ tống xe ngọc, giữ hai đài ngọc và thử thách triều
  đình xương trên các map hiện có. Huy chương không chặn chiến dịch. Trong thử
  thách xương, mất người làm giảm ấn danh dự; hết ấn vẫn có thể thắng huy chương
  đồng. Bạc cần tối đa 3 tổn thất, vàng cần không mất ai và giữ cổng nguyên vẹn.
- Phân bón giảm còn **2 đá**. Spirit Tea cho 3 lượt triệu hồi đầu **+10 mana và
  +20 Dao**; vẫn phải trả đủ mana/Qi và chờ hồi chiêu để ultimate. Thêm **Ledger**
  trong Linh Điền để xem giao dịch, thu hoạch và thưởng trận; sảnh báo cây đã chín.

Giữ nguyên 8 nhân vật và 9 ải chiến dịch. Bản lưu cũ vẫn dùng được.

## Bản 1.4: Linh Điền và kinh tế môn phái

Tại sảnh, chọn **Estate**, hoặc tới NPC trông vườn:

- **Garden:** bắt đầu với 3 ô, mở rộng lên 6 rồi 9 ô. Có Tụ Khí Thảo, Hà Liên,
  Thanh Phong Trúc và Dẫn Hồn Chi; cây chín sau 1–3 trận hoàn tất. Tưới/bón phân
  tăng sản lượng; nâng tưới tự động và nghiên cứu từng cây bằng Insight.
  Cây không héo khi nghỉ chơi. Thắng trận tăng 1 lượt sinh trưởng; thua chỉ tính
  khi qua nửa số wave **và** đủ 60 giây. Thoát trận không giúp cây lớn.
- **Alchemy:** dùng nông sản luyện Spirit Tea, Five-Element Dew và Soul-Ward Elixir.
  Mỗi trận chỉ mang **1 loại, tiêu hao 1 liều khi vào trận thành công**. Công thức
  ghi rõ nguyên liệu, phí, phạm vi và điều kiện kích hoạt. Trang bị ở mục Alchemy.
- **Merchant:** mua hạt giống/phân bón, bán nông sản dư; mua và bật/tắt đồ trang trí
  sảnh, vườn và cung điện. Đồ trang trí không tăng sức mạnh.
- **Missions / Goals / Research:** 3 ủy thác luân phiên, 8 thành tựu và các mốc
  nghiên cứu quái. Bấm **Claim** để nhận thưởng. Không có giới hạn theo ngày.
  Spirit Stones vẫn là tiền chính; Insight dùng nghiên cứu cây và công thức.
  Qi chỉ dùng trong trận, không đổi thành tiền vĩnh viễn.
- **Nursery Defense:** chế độ bảo vệ vườn riêng, 6 wave trong khoảng 2–3 phút,
  chỉ dùng 3 lane giữa. Mỗi luống chịu được 2 lần lọt quái; giữ càng nhiều luống
  càng nhận nhiều loại hạt giống. Có 3 trang hướng dẫn kèm hình trước trận.
- **Reset Talents:** hoàn lại đúng số đá đã dùng để đổi hướng phát triển. Lần đầu
  miễn phí, những lần sau trừ phí 10 đá vào khoản hoàn. Nhánh kiểu cũ vẫn tính
  theo giá mua cũ 35 đá.
- Thiết kế mới cho **8 cultivator và toàn bộ quái/thủ lĩnh**, thêm chi tiết trang
  phục, vũ khí, bóng đổ. Có tư thế đứng/đánh/skill/ultimate riêng cho nhân vật,
  và đứng/đánh/skill cho quái, kết hợp chuyển động trong game. Cảnh vườn và hình
  từng giai đoạn cây cũng được đóng gói sẵn.

Bản lưu cũ tự chuyển sang phiên bản 2; giữ tiền, ải, thiên phú và cài đặt.
Phần thưởng trận được ghi một lần; nếu phản hồi mạng bị mất có thể nhận lại
biên nhận mà không cộng đôi. Tiến trình vẫn lưu cục bộ trong trình duyệt.

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
