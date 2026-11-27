# Kế hoạch chạy lại và benchmark, 27/11/2026

Một lượt chạy đầy đủ trên kịch bản đã sửa, từ REF tới benchmark và hình so sánh. Quyết định nền: D30 (pha đèn tách theo nhánh LVL), D33 (lưu lượng đi thẳng HMG và LVL_W), D35 (xe vào mạng ở tim làn), D32 (chế độ full dùng prompt v007), D34 (bộ hình).

## Điều kiện chung

Mạng N7 (`scenario/net/site.net.xml`) với pha đèn 160 s: LVL_E xanh 50 s, NT–HMG 40 s, LVL_W xanh 55 s, vàng 3 s, đỏ toàn phần 2 s. Ngày hiệu chỉnh VIDEO_V2, ngày kiểm định VIDEO_V1, cả hai sinh lại theo pha mới và lưu lượng mới. Mỗi lần chạy 1800 s sau 240 s khởi động, bước 0,1 s, độ phân giải ngang 0,4 m, bật kiểm tra va chạm trong nút. Mọi phương án đi qua cùng hàm đánh giá, cùng hàm chọn đặc tả (`select_best`: đạt tiêu chí trước, nếu không có thì quy tắc dự phòng ít teleport kẹt nhất rồi $S$ nhỏ nhất).

## Các bước

| Bước | Nội dung | Số lần chạy | Ước thời gian |
|---|---|---|---|
| 1. REF_v1127 | B0, B1_manual × VIDEO_V2 × seed 1–5; lấy va chạm trên làn/h của B0 làm mức trần R10 | 10 | ~30 phút |
| 2a. B2_v1127 | Optuna TPE trên cấu trúc B1, VIDEO_V2 × seed 1–3, 6 tiến trình | 36 | ~3 giờ (song song với 2b) |
| 2b. P1_v1127 | LLM, chế độ chỉ tham số, prompt v006 | 36 | ~2,2 giờ |
| 2c. P2_v1127 | LLM, chế độ đầy đủ, prompt v007 (sau P1 vì dùng chung GPU) | 36 | ~3,3 giờ |
| 3. BENCH_v1127 | B0, B1, B2_best, P1_best, P2_best × VIDEO_V1 × seed 1–20 | 100 | ~1,5 giờ |
| 4. Hình | `figures.py`: chỉ số hành vi, vết xe thời gian–không gian, lưu lượng theo hướng | 0 | ~5 phút |

Chuỗi bắt đầu lại lúc 01:29 ngày 27/11; dự kiến xong khoảng 09:00–10:00.

## Số liệu báo cáo

Cho mỗi phương án trên ngày kiểm định: $S$, số lần qua cổng G0 và tỷ lệ ô đạt GEH, va chạm/h, va chạm trên làn/h, teleport kẹt/h, xe chờ vào mạng cuối lượt, số lần chạy đạt tiêu chí chấp nhận và lý do loại; trung bình, độ lệch chuẩn, nhỏ nhất–lớn nhất trên 20 seed. Các chỉ số hành vi (vượt đèn đỏ, xuất phát sớm, dừng quá vạch, rẽ trái cấm chờ giữa nút, đi sai làn, chờ đỏ trên làn rẽ phải) đặt cạnh mục tiêu của ngày quan sát. Với chiến dịch: phạm vi $S$, đặc tả tốt nhất, số mẫu LLM hợp lệ và các mã lỗi.

## Quy tắc tự quyết trong lúc chạy

- Chiến dịch LLM không sinh được đặc tả hợp lệ nào: ghi nhận như một kết quả, benchmark chạy với các phương án còn lại.
- Một bước chết giữa chừng (lỗi Python, máy khởi động lại): chạy lại `run_chain.bat`; bước đã xong được bỏ qua, chiến dịch tự chạy tiếp từ trạng thái đã lưu, ngân sách đã tiêu không bị tính lại.
- Ollama không phản hồi: chuỗi tự khởi động lại server ba lần; nếu vẫn không được thì bỏ qua chiến dịch đó và ghi vào DECISIONS.
- Số liệu bất thường (va chạm hay xe chờ tăng đột biến so với lượt trước): dừng chuỗi, chạy thí nghiệm tách nguyên nhân một seed trong thư mục tạm, ghi quyết định rồi chạy lại (như D35).
- Không thay đổi mục tiêu, định nghĩa chỉ số, mức trần hay ngân sách giữa chừng một chiến dịch.

## Chống treo khi chạm giới hạn phiên

Toàn bộ tính toán chạy trong một tiến trình nền độc lập với phiên Claude. Một lịch tự kiểm tra (phút 07 và 37 mỗi giờ) đọc `experiments/campaigns/chain_v1127.log` và `docs/HANDOFF_2026-11-27.md`, khởi động lại chuỗi nếu nó chết, và làm tiếp các bước còn lại khi có dòng `chain done`. Khi giới hạn phiên được làm mới, lượt kiểm tra kế tiếp tự làm tiếp; chủ đề tài chỉ cần giữ cửa sổ Claude Code mở.

## Đầu ra cho báo cáo

Bảng chiến dịch và bảng benchmark của Chương 5 viết lại theo số mới; ba hình của D34 thay Hình C.1; mục kịch bản ghi pha đèn mới và bằng chứng từ video; tóm tắt hai thứ tiếng và Chương 6 cập nhật theo kết quả. Commit, push và đồng bộ Overleaf chỉ khi chủ đề tài bảo.
