# Hội đồng phản biện

Ghi chú về vị trí trích dẫn:
- "tr." là số trang in ở chân trang của PDF đã build (128 trang). Trang trong tệp PDF = tr. + 18. Phần tóm tắt và bìa không có số trang in, nên ghi "PDF trang tệp N".
- PDF được build từ các tệp `5_Evaluation.tex`, `6_Implementation.tex`, `7_Conclusions.tex` (xem `main.fls`, `main.log`). Lúc tôi đọc, thư mục `Chapter/` không còn ba tệp này. Cây làm việc chỉ có `5_Experiments.tex` (≈ Chương 6 của PDF) và `6_Conclusions.tex` (≈ Chương 7 của PDF). Nội dung Chương 5 của PDF nằm rải ở `4_Rule_execution.tex:61–114` và `5_Experiments.tex:470–507`. Số dòng `.tex` dưới đây là số dòng của cây làm việc hiện tại, chỉ ghi khi đoạn văn ở đó trùng với PDF. Tác giả cần chốt một bản nguồn duy nhất trước khi in.

## Đánh giá tổng quát (3–5 câu)

Bài toán, độ khó và ý tưởng tách sinh luật khỏi thực thi luật được trình bày rõ ở Chương 1 và Chương 3–4. Cấu trúc tổng thể thì mất cân đối nặng: Chương 6 chiếm 67/98 trang thân bài, viết như nhật ký phòng thí nghiệm theo ngày, và các kết quả chính bị chôn giữa các thử nghiệm trên năm phiên bản mạng đã bỏ. Luận văn không có câu hỏi nghiên cứu. Năm mục tiêu, bốn đóng góp, bảy giải pháp kỹ thuật và hai thí nghiệm E1, E2 không được ánh xạ với nhau. Chương 7 thì để trống chính câu kết luận chính. Tóm tắt và Chương 7 kể kết quả theo trình tự thời gian, dùng thuật ngữ nội bộ, nên phương pháp nghe yếu hơn bằng chứng thực có.

## Nhận xét

### [HD-01] Bìa ghi sai tên đề tài
- Mức: nghiêm trọng
- Vị trí: Cover.tex:13, Cover2.tex:13 (PDF trang tệp 1 và 2)
- Trích: "Mô hình thế giới vĩ mô trong trò chơi máy tính"
- Vấn đề: Tên trên cả bìa chính và bìa lót là tên đề tài khác, còn sót từ mẫu. Trong toàn bộ luận văn không có chỗ nào ghi tên đề tài thật.
- Vì sao quan trọng: Đây là thứ hội đồng nhìn thấy đầu tiên. Lỗi này cũng làm người đọc nghi bản in chưa được rà soát.
- Đề xuất sửa: Thay bằng tên đề tài đã đăng ký ở cả hai tệp. Đặt tên đó ở đầu Tóm tắt nếu mẫu SoICT cho phép. Ví dụ: "Sinh và tinh chỉnh luật hành vi người lái bằng mô hình ngôn ngữ lớn cục bộ cho mô phỏng giao thông hỗn hợp tại nút giao có đèn".

### [HD-02] Chương 7 không có kết luận chính và không trả lời mục tiêu
- Mức: nghiêm trọng
- Vị trí: 6_Conclusions.tex:45 (tr. 97); 1_Introduction.tex:78 (tr. 3–4)
- Trích: "[TODO: câu kết luận chính về khả năng của LLM cục bộ trong hiệu chỉnh luật hành vi, chỉ trong phạm vi dữ liệu đại diện]"; mục tiêu (v): "so sánh luật do LLM sinh với mô hình mặc định, bộ luật viết tay và một bộ tối ưu số trên cùng ngân sách mô phỏng"
- Vấn đề: Câu kết luận chính đang là một chỗ giữ chỗ. Mục 7.1.2 "Đã hoàn thành" liệt kê thành phần phần mềm, không đối chiếu với năm mục tiêu và bốn đóng góp của Chương 1. Mục tiêu (v) chưa đạt (tr. 97: "chưa cho phép kết luận LLM tốt hơn hay kém hơn Optuna"), nhưng không có câu nào nói thẳng "mục tiêu (v) chưa đạt".
- Vì sao quan trọng: Hai tuần trước buổi bảo vệ, hội đồng cần thấy tác giả kết luận được gì từ bằng chứng đang có, kể cả khi kết luận đó có giới hạn. Một chỗ TODO ở vị trí kết luận chính sẽ bị hỏi đầu tiên.
- Đề xuất sửa: Mở đầu 7.1 bằng một bảng 5 dòng: mục tiêu (i)–(v), mức đạt (đạt, đạt một phần, chưa đạt), bằng chứng (mục, bảng). Viết câu kết luận chính từ dữ liệu đang có, có giới hạn phạm vi. Ví dụ: "Trên dữ liệu đại diện, `qwen3.5:9b` sinh được đặc tả hợp lệ cho 12/16 mẫu P1 và 14/20 mẫu P2. Mọi lỗi đều là lỗi cấu trúc, và bộ kiểm tra hợp lệ bắt được trước khi chạy. Ở chế độ sinh cả cấu trúc, mô hình hạ điểm tổng bằng cách bỏ bớt luật. Chưa có đặc tả nào đủ điều kiện, nên chưa so sánh được với Optuna."

### [HD-03] Không có câu hỏi nghiên cứu; mục tiêu, đóng góp, giải pháp và thí nghiệm không ánh xạ với nhau
- Mức: nghiêm trọng
- Vị trí: 1_Introduction.tex:78, 89–96 (tr. 3–4); Mục 5.5.1 (tr. 26, 5_Experiments.tex:503); 6_Conclusions.tex:23 (tr. 95)
- Trích: "Luận văn có năm mục tiêu cụ thể"; "Luận văn có bốn đóng góp chính"; "Mục 6.12 trình bày bảy giải pháp kỹ thuật khi hiện thực các đóng góp này"; Chương 7: "Các đóng góp kỹ thuật rút ra từ quá trình này nằm ở Mục 6.12"
- Vấn đề: Có bốn danh sách đánh số mà không có bảng nối. E1 và E2, hai thí nghiệm thực sự trả lời câu hỏi "LLM có ích không", chỉ xuất hiện lần đầu ở tr. 26. Chương 7 gọi bảy giải pháp là "đóng góp kỹ thuật", nên người đọc không biết luận văn có 4 hay 7 đóng góp.
- Vì sao quan trọng: Hội đồng chấm theo câu hỏi "đóng góp là gì, kiểm chứng ở đâu". Hiện người đọc phải tự dựng phép ánh xạ đó.
- Đề xuất sửa: Thêm mục 1.x "Câu hỏi nghiên cứu" với 2–3 câu hỏi. Ví dụ: CH1: bộ thực thi có tạo ra các hành vi vi phạm mà SUMO mặc định không có, mà không tăng va chạm không? CH2 (E1): với cùng cấu trúc và ngân sách, LLM có chỉnh tham số tốt bằng Optuna không? CH3 (E2): cấu trúc do LLM sinh có giá trị không? Cuối Mục 1.5, thêm một bảng: đóng góp → câu hỏi → mục chứa bằng chứng. Ở Chương 7, trả lời từng câu hỏi theo đúng mã đó. Đổi chữ "đóng góp kỹ thuật" ở tr. 95 thành "giải pháp kỹ thuật".

### [HD-04] Chương 6 chiếm 68% thân bài, nhiều phần nên chuyển phụ lục hoặc cắt
- Mức: nghiêm trọng
- Vị trí: Chương 6, tr. 28–94 (5_Experiments.tex toàn tệp, 1440 dòng)
- Trích: số trang theo chương: Ch1 5, Ch2 5, Ch3 9, Ch4 3, Ch5 5, Ch6 67, Ch7 4
- Vấn đề: Ba chương phương pháp cộng lại có 17 trang, còn Chương 6 có 67 trang. Phần lớn Chương 6 là tài liệu kỹ thuật phần mềm và nhật ký phát triển, không phải đánh giá.
- Vì sao quan trọng: Người chấm đọc bản in sẽ không tìm được kết quả chính. Tỷ lệ này cũng làm luận văn trông như báo cáo dự án hơn là luận văn nghiên cứu.
- Đề xuất sửa (cụ thể theo mục):
  - 6.3 "Yêu cầu đối với hệ thống" (tr. 34–35) cùng Bảng 6.6, 6.7 (tr. 90–91): cắt. Nội dung trùng Chương 3–5 và Bảng 6.5.
  - 6.4 "Kiến trúc phần mềm" (tr. 36–41): giữ Bảng 6.8 (luồng dữ liệu) và một đoạn. Chuyển Bảng 6.9 (3 trang) và 6.4.4 "Thiết kế lớp" sang Phụ lục C "Thiết kế phần mềm".
  - 6.8 "Công cụ và kết quả triển khai" (tr. 44–48): chuyển Bảng 6.12 (phiên bản thư viện) sang phụ lục. Cắt Bảng 6.13 (danh sách hạng mục dự án), Bảng 6.14 (số dòng mã), đoạn xung đột `sqlite3.dll` và `JournalFileOpenLock` (tr. 45–46).
  - 6.9 "Kiểm thử" (tr. 48–50): giữ một đoạn về số ca và hai kiểm thử then chốt. Chuyển Bảng 6.15 sang phụ lục.
  - 6.11: xem HD-05.
  - 6.12 (tr. 74–84): xem HD-09.
  - 6.13 "Triển khai và tái lập" (tr. 84–85): chuyển sang phụ lục.
  - Mục tiêu: Chương 6 còn khoảng 30 trang.

### [HD-05] Mục 6.11 viết như nhật ký theo ngày, kết quả chính bị chôn
- Mức: nghiêm trọng
- Vị trí: Mục 6.11, tr. 52–74 (5_Experiments.tex:712–1238); câu mở Chương 6 (tr. 28, 5_Experiments.tex:12)
- Trích: "Mục 6.11 trình bày các thực nghiệm theo thứ tự thời gian"; Bảng 6.17 "Các phiên bản mạng đại diện" (6 mạng); "Số liệu giữa các mạng không so sánh trực tiếp được"
- Vấn đề: 19 tiểu mục theo ngày (27/10, 28/10 đợt 1, 28/10 đợt 2, 29/10, 04/11, 08/11). Kết quả của năm mạng đã bỏ (6.11.4, 6.11.7–6.11.10, 6.11.12) đứng ngang hàng với kết quả trên mạng cuối. Có cả chi tiết giờ chạy, ví dụ Bảng 6.31: "3 h 25 (06:03–09:28)". Mục 6.10, so sánh chính giữa B0 và B1, lại đặt trước 6.11 và dùng chiến dịch `REF_n1104s5` mà đến 6.11.14 mới được định nghĩa.
- Vì sao quan trọng: Người đọc không biết đâu là kết quả cuối cùng. Hội đồng sẽ hỏi vì sao phải đọc kết quả trên các mạng đã bỏ.
- Đề xuất sửa: Tổ chức lại theo câu hỏi, không theo ngày. (A) Thí nghiệm khả thi đã quyết định thiết kế mô hình (6.11.2 xe chờ giữa nút, 6.11.3 bề rộng làn ra, 6.11.6 Phase 3A–3D): rút gọn, đặt trước phần kết quả hoặc gộp vào 6.1. (B) Kết quả tham chiếu B0, B1 trên mạng cuối 04/11: 6.11.14 gộp với 6.10. (C) Ba chiến dịch B2, P1, P2 trên mạng 04/11 và phân tích nguyên nhân: 6.11.17–6.11.19. Các mục còn lại (6.11.4, 6.11.5, 6.11.7–6.11.13, 6.11.15, 6.11.16) chuyển sang phụ lục "Quá trình phát triển kịch bản". Ở chương chính, chỉ giữ Bảng 6.17 và một đoạn tóm tắt vì sao mạng đổi.

### [HD-06] Các bảng của Chương 6 trôi về sau đoạn kết chương; bảng kết quả chính cách phần bàn luận 43 trang
- Mức: nghiêm trọng
- Vị trí: tr. 86–94 (Bảng 6.1–6.7, 6.10, 6.11, 6.16, 6.34, 6.35); đoạn kết chương ở tr. 85; bảng `table:compare_b0_b1` ở 5_Experiments.tex:677 dùng `[ht]`
- Trích: tr. 50 "Bảng 6.16 cho thấy SUMO mặc định không có lượt vượt đèn đỏ nào", trong khi Bảng 6.16 nằm ở tr. 93
- Vấn đề: Đoạn kết Chương 6 (tr. 85) bị theo sau bởi 9 trang toàn bảng. Danh mục bảng biểu in Bảng 6.8 trước Bảng 6.1. Bảng 6.1 (bản vá mạng), được dẫn ở tr. 29, nằm ở tr. 86. Bảng 6.4 (sáu luật TraCI) nằm ở tr. 88. Chương 2 cũng có lỗi này: Bảng 2.2 đứng sau đoạn kết chương (tr. 10).
- Vì sao quan trọng: Người đọc bản in phải lật đi lật lại. Lỗi này cũng cho thấy tài liệu chưa được rà soát sau khi build.
- Đề xuất sửa: Sau khi rút gọn theo HD-04 và HD-05, kiểm tra lại vị trí bảng. Dùng `[!htbp]` hoặc `[H]` cho các bảng cần đứng cạnh văn bản. Thêm `\FloatBarrier` (gói `placeins`) trước đoạn kết của mỗi chương.

### [HD-07] Tóm tắt kể kết quả theo trình tự thời gian, không nêu đóng góp, nên phương pháp nghe yếu hơn thực tế
- Mức: nghiêm trọng
- Vị trí: 0_3_Abstract.tex:15 (PDF trang tệp 3); 0_4_Abstract_English.tex:15 (PDF trang tệp 5–6)
- Trích: "Trên mạng ngày 27/10, phương án đối sánh Optuna đã dùng hết ngân sách 36 lần chạy… Sau khảo sát hiện trường, kịch bản đổi sang đèn ba pha… Trên mạng hiện tại, SUMO mặc định đủ điều kiện ở 15/15 lần chạy, còn bộ luật thủ công thì chưa."
- Vấn đề: Đoạn "Kết quả hiện có" chiếm hơn nửa tóm tắt. Nó dùng các tên nội bộ ("mạng ngày 27/10", "chiến dịch", "đủ điều kiện", "phân tích loại bỏ") mà người đọc tóm tắt chưa biết nghĩa. Tóm tắt không nêu bốn đóng góp. Kết quả dương có thật không được nêu: B1 qua bộ thực thi cho 4,86% xe máy vượt đèn đỏ, so với 0% ở SUMO mặc định, và tăng M7a (số xe chờ giữa nút) từ 4,00 lên 4,89 mỗi chu kỳ (tr. 50). Câu "SUMO mặc định đủ điều kiện, bộ luật thủ công thì chưa" đọc như phương pháp kém hơn mô hình chuẩn.
- Vì sao quan trọng: Nhiều thành viên hội đồng chỉ đọc kỹ tóm tắt và kết luận.
- Đề xuất sửa: Viết lại phần kết quả theo đóng góp, không theo ngày, gồm 4–5 câu. (1) Quy trình đã cài đặt đầy đủ, kèm 403 ca kiểm thử. (2) So với SUMO mặc định, bộ thực thi tạo ra được vượt đèn đỏ và xe chờ giữa nút mà mô hình mặc định không có, trên dữ liệu đại diện. (3) `qwen3.5:9b` sinh đặc tả hợp lệ ở 12/16 mẫu P1 và 14/20 mẫu P2, lỗi chủ yếu là lỗi cấu trúc. (4) Chưa đặc tả nào qua bộ lọc an toàn và ổn định, do gia tốc xe máy chuyển giao từ tài liệu trong bộ luật nền, nên chưa so sánh được LLM với Optuna. Bỏ các ngày nội bộ.

### [HD-08] Thuật ngữ "đủ điều kiện" dễ bị hiểu là "giống thực tế"
- Mức: nên sửa
- Vị trí: 0_3_Abstract.tex:15 (PDF trang tệp 3); Mục 5.3 (tr. 25, 4_Rule_execution.tex:112); Mục 6.11.14 (tr. 68); 6_Conclusions.tex:39 (tr. 96)
- Trích: "B0 đủ điều kiện ở 15/15 lần chạy. Đây là lần đầu B0 qua mọi điều kiện trên mạng đại diện."
- Vấn đề: "Đủ điều kiện" là bộ lọc an toàn và ổn định: không kẹt, qua G0 (cổng GEH lưu lượng), va chạm dưới ngưỡng. Nó không đo độ giống hành vi. B0 không có vượt đèn đỏ nào mà vẫn "đủ điều kiện". Tóm tắt và Chương 7 dùng từ này mà không giải thích.
- Vì sao quan trọng: Người đọc sẽ hiểu là SUMO mặc định "đạt", còn phương pháp đề xuất "trượt".
- Đề xuất sửa: Đổi thành "qua bộ lọc an toàn" hoặc "chạy hợp lệ". Mỗi lần dùng trong tóm tắt và Chương 7, thêm một mệnh đề giải thích, ví dụ: "B0 qua bộ lọc an toàn (không kẹt, va chạm dưới ngưỡng) nhưng không có hành vi vi phạm nào".

### [HD-09] Cùng một nội dung được kể lại 3–4 lần
- Mức: nên sửa
- Vị trí: bộ kiểm tra hợp lệ: Mục 3.6 (tr. 18–19), 6.2.1 (tr. 33, 5_Experiments.tex:200–202), 6.3.1 (tr. 34, 5_Experiments.tex:273), 6.12.1 (tr. 75–76). Bản ghi can thiệp bảy trường: tr. 22, tr. 34, tr. 41, tr. 77. Mục 6.12.3 (tr. 79) kể lại số liệu vùng chờ 8/10/12 xe và 13/8/8/7/10 xe của 6.11.2. Mục 6.12.5 (tr. 81) kể lại 6.11.3. Mục 6.12.6 (tr. 82–83) kể lại 6.11.6 và 6.11.15.
- Trích: tr. 33 "Bộ kiểm tra hợp lệ chạy năm nhóm kiểm tra. Nhóm (i) đối chiếu đặc tả với lược đồ JSON…", gần như trùng câu chữ với tr. 18
- Vấn đề: Mục 6.12 "Các giải pháp kỹ thuật" (11 trang) thực chất là bản tóm tắt thứ hai của Chương 3–4 cộng Mục 6.11.
- Vì sao quan trọng: Lặp lại làm chương dài thêm mà không thêm thông tin. Hội đồng sẽ coi đây là độn trang.
- Đề xuất sửa: Mỗi khái niệm chỉ mô tả một lần, ở chương phương pháp. Chương 6 chỉ nêu phần riêng của SUMO, như bit speed mode và tên mã lỗi. Mục 6.12 rút còn Bảng 6.34, mỗi giải pháp một đoạn 2–3 câu trỏ tới bằng chứng. Nếu bảy giải pháp là đóng góp, chuyển chúng lên một mục ngay sau phương pháp, không để ở cuối Chương 6.

### [HD-10] Cách chia Chương 3/4/5 không khớp Hình 1.1; chương phương pháp viện dẫn nhật ký thực nghiệm
- Mức: nên sửa
- Vị trí: Hình 1.1 (tr. 3); Mục 3.1 (tr. 11); Mục 3.6 (tr. 18); Chương 4 (tr. 20–22); các tham chiếu ngược ở tr. 15 (Mục 6.11.11), tr. 16 (Mục 6.12.3), tr. 18 (Mục 6.11.17), tr. 21 (Mục 6.12.6)
- Trích: Hình 1.1 đặt "1. Kiểm tra hợp lệ" và "4. Tính chỉ số M1–M10" trong khung "thực thi luật: mã xác định". Tr. 11: "Phương pháp gồm ba phần nối thành một vòng lặp". Tr. 2: "Luận văn tách việc sinh luật khỏi việc thực thi luật".
- Vấn đề: Trong PDF, kiểm tra hợp lệ nằm ở Chương 3 (sinh luật), chỉ số nằm ở Chương 5, trái với Hình 1.1. Chương 1 nói phương pháp có hai phần, Chương 3 nói ba phần. Chương 4 chỉ có 3 trang. Chương 3 biện minh thiết kế bằng lịch sử chạy thử, ví dụ tr. 15: "Điều kiện này được thêm sau khi chẩn đoán cho thấy… (Mục 6.11.11)".
- Vì sao quan trọng: Ranh giới chương là cách người đọc hiểu phương pháp. Hình tổng quan mâu thuẫn với mục lục làm khung phương pháp mờ đi.
- Đề xuất sửa: Chọn một cách chia và dùng thống nhất ở Hình 1.1, Mục 1.3, Mục 3.1 và Mục 1.6. Cây làm việc hiện tại đã đưa kiểm tra hợp lệ và chỉ số vào `4_Rule_execution.tex`. Nếu giữ hướng đó, sửa Mục 3.1 thành "hai phần". Trong Chương 3–4, nêu lý do thiết kế bằng cơ chế ("nếu thiếu… thì…", đã có sẵn). Bỏ hoặc đưa vào chú thích các câu "được thêm sau khi chẩn đoán ngày…".

### [HD-11] Các giới hạn quan trọng nằm rải trong Chương 6, Chương 7 không có mục "Hạn chế"
- Mức: nên sửa
- Vị trí: tr. 58 (G0 không chứng minh độ thực tế vì "số quan sát đại diện và tệp tuyến cùng sinh từ một bộ sinh"); tr. 44, 66, 77 (ngưỡng va chạm "chưa được tính lại trên mạng 29/10"); tr. 41, 65 (mục tiêu M9 (chặn làn rẽ phải) "được suy từ thiết lập có cọc… chưa định nghĩa lại"); tr. 73–74 (gia tốc IDM của Saval chuyển sang `accel` của Krauss); tr. 63, 72 (một seed mỗi ngày); tr. 25 (hàm khoảng cách thưởng cho việc ép hành vi hiếm về 0). Mục 7.1.5 (tr. 97, 6_Conclusions.tex:45) chỉ liệt kê việc chưa làm.
- Trích: tr. 74 "Giá trị này chuyển từ gia tốc cực đại a của mô hình IDM… sang accel của mô hình Krauss"
- Vấn đề: Mỗi giới hạn đều được thừa nhận ở đâu đó, nhưng không có chỗ nào gom lại. Đặc biệt, việc ánh xạ tham số IDM sang Krauss là lỗi trong bộ luật nền B1, và chính lỗi này chặn mọi chiến dịch. Chương 7 lại nêu nó như một "phát hiện".
- Vì sao quan trọng: Hội đồng sẽ tự tìm ra các điểm này và hỏi vì sao không nêu ở kết luận. Một mục hạn chế gom lại đầy đủ sẽ bảo vệ tác giả tốt hơn.
- Đề xuất sửa: Thêm 7.1.x "Hạn chế", mỗi ý một câu: dữ liệu đại diện và G0; ngưỡng va chạm và mạng; định nghĩa M9; một seed mỗi ngày; điểm yếu của hàm khoảng cách với tỷ lệ nhỏ; tham số B1 chuyển giao giữa hai mô hình bám xe khác nhau. Gọi tên lỗi `accel` đúng bản chất: "giá trị chuyển giao chưa kiểm chứng trong bộ luật nền".

### [HD-12] Phần LLM, trọng tâm của đề tài, chiếm rất ít trang và nằm rải rác
- Mức: nên sửa
- Vị trí: Mục 6.6 (tr. 42–43), 6.11.16 (tr. 70), 6.11.18 (tr. 72–73), Bảng 6.11 (tr. 93), Bảng 6.31 (tr. 71), Bảng 6.32 (tr. 73)
- Trích: tr. 72 "P1. 14/15 lần thử hỏng là lỗi tổng tỷ trọng"; tr. 72 "P1 còn nộp lại một đặc tả: it01_s02, it02_s03, it03_s01 và it04_s02 giống nhau"
- Vấn đề: Kết quả về hành vi của LLM chỉ chiếm khoảng 4 trang trong 98 trang thân bài, chia ở ba tiểu mục cách xa nhau. Luận văn không trình bày một đặc tả do LLM sinh kèm phần "lý do" của nó, dù Chương 1 (tr. 2) coi lý do này là một ưu điểm so với bộ tối ưu số. Không có hình nào cho thấy điểm tổng S thay đổi theo vòng lặp.
- Vì sao quan trọng: Tên đề tài đặt LLM ở trung tâm, nên hội đồng sẽ hỏi LLM đã làm được gì.
- Đề xuất sửa: Gom thành một mục "Hành vi của LLM cục bộ" gồm: tỷ lệ hợp lệ theo vòng; phân loại lỗi (Bảng 6.32); hiện tượng nộp lại đặc tả trùng; hiện tượng bỏ bớt luật ở P2; một hình S theo vòng cho P1, P2 và B2. Đưa một đặc tả P2 đầy đủ kèm trường lý do vào phụ lục, rồi bình luận vài câu xem lý do đó có hợp với hiểu biết về hành vi không.

### [HD-13] Tuyên bố mới lạ mạnh hơn phần khảo sát chống đỡ
- Mức: nên sửa
- Vị trí: 1_Introduction.tex:20 (tr. 2); Chương 2 (tr. 6–10)
- Trích: "Trong phạm vi khảo sát của luận văn (Chương 2), chưa có nghiên cứu nào mô phỏng các hành vi đặc trưng của người tham gia giao thông Việt Nam tại một nút giao có đèn."
- Vấn đề: Chương 2 dài 5 trang, toàn luận văn có 23 tài liệu, và không nêu cách tìm tài liệu (cơ sở dữ liệu, từ khóa, khoảng năm). Câu "trong phạm vi khảo sát" không cho biết phạm vi đó rộng đến đâu.
- Vì sao quan trọng: Hội đồng sẽ hỏi đã tìm những gì, chẳng hạn các mô hình VISSIM hay SUMO cho dòng xe máy ở Hà Nội, TP. Hồ Chí Minh, Ấn Độ.
- Đề xuất sửa: Thêm 3–4 câu ở đầu Mục 2.3 nêu nguồn, từ khóa và khoảng năm đã tìm. Thu hẹp tuyên bố, ví dụ: "Trong các nguồn đã tìm (…), chưa có mô hình nào có đồng thời vượt đèn theo đoàn, xuất phát sớm và rẽ trái chờ giữa nút tại một nút có đèn."

### [HD-14] Đóng góp 2 ("danh mục 11 hành vi") chưa kiểm chứng được như đang viết
- Mức: nên sửa
- Vị trí: 1_Introduction.tex:92 (tr. 4); Bảng 3.1 và đoạn trước bảng (tr. 12–13, 3_Rule_generation.tex:57); tr. 31 (5_Experiments.tex:112)
- Trích: "[TODO_CITE: nguồn hoặc mô tả quan sát cho hành vi 11, xe máy đi chậm giữa làn]"; tr. 31 "là quan sát của tác giả ngày 29/10/2026, chưa đếm"
- Vấn đề: 5 trong 11 hành vi có cơ sở là "Quan sát" hoặc "khảo sát hiện trường", nhưng luận văn không mô tả cách quan sát: ở đâu, khi nào, bao lâu, ghi nhận bằng gì. Hành vi 8 (đi ngược chiều) bị hoãn, nên mô hình thực tế có 10 hành vi.
- Vì sao quan trọng: Một đóng góp dựa trên quan sát không có quy trình sẽ bị hỏi "quan sát này có lặp lại được không".
- Đề xuất sửa: Thêm một đoạn hoặc bảng nhỏ mô tả khảo sát hiện trường 28–30/10: vị trí đứng, khung giờ, có quay video hay không, ghi chép gì. Ở Mục 1.5, viết rõ "11 hành vi, trong đó 10 đã mô hình hóa". Xóa dòng TODO_CITE, hoặc thay bằng mô tả quan sát.

### [HD-15] Ghi chú nội bộ và TODO đen đậm còn trong bản in
- Mức: nên sửa
- Vị trí: tr. 25 (4_Rule_execution.tex:103); tr. 12–13 (3_Rule_generation.tex:57); tr. 41 (5_Experiments.tex:400); tr. 52 (5_Experiments.tex:710); tr. 79 (5_Experiments.tex:1341); tr. 83 (5_Experiments.tex:1418); tr. 97 (6_Conclusions.tex:45, ba TODO); Tóm tắt (0_3_Abstract.tex:17, 0_4_Abstract_English.tex:17)
- Trích: tr. 25 "[Câu hỏi cho GVHD: nên làm mượt khoảng cách của tỷ lệ nhỏ… hay giữ nguyên và nêu là hạn chế?]"
- Vấn đề: Một câu hỏi gửi giảng viên hướng dẫn đang nằm trong văn bản chính. Các TODO in đen đậm khác với quy ước `\tamthoi` màu đỏ đã giải thích ở tr. 30, nên người đọc không biết chúng có nghĩa gì.
- Vì sao quan trọng: Bản nộp hội đồng không được chứa trao đổi nội bộ. TODO ở tóm tắt và kết luận cho thấy luận văn chưa hoàn thành.
- Đề xuất sửa: Chốt cách xử lý hàm khoảng cách, rồi viết nó như một quyết định hoặc một hạn chế. Gom mọi TODO thành một danh sách riêng ngoài bản in. Chỗ nào bắt buộc phải giữ thì viết thành câu "chưa có… (dự kiến…)".

### [HD-16] Ký hiệu trùng và tên nội bộ làm người đọc nhầm
- Mức: nên sửa
- Vị trí: "F2" là nhóm hành vi (tr. 28 "F2 (tìm khoảng trống khi ùn)"; tr. 32 "nhóm F2"; Bảng 6.9 tr. 38 "Ba bảng nhóm F2") và cũng là phiên bản mạng (tr. 52 "F2 (27/10)"; tr. 61 "mạng F2"). Tên giai đoạn kế hoạch: tr. 59 "Thí nghiệm khả thi Phase 3A–3D". Mã nội bộ: `REF_n1104s5`, `it01_s02`, `t003`, `B2_n28b_t007` (tr. 64, 71). Danh mục từ viết tắt (PDF trang tệp 18) chỉ có 6 mục, thiếu B0, B1, B2, P1, P2, H, E1, E2, M1–M10, G0.
- Trích: tr. 60 "Hành vi 6 và 7 được cài vào mạng F2"
- Vấn đề: Cùng một nhãn mang hai nghĩa. Tên giai đoạn của kế hoạch làm việc và mã chiến dịch trong mã nguồn bị đưa thẳng vào văn bản. Chữ "dữ liệu đại diện" có thể bị hiểu là dữ liệu đại diện cho nút thật, trong khi đó là dữ liệu dựng từ tài liệu của nút khác.
- Vì sao quan trọng: Người đọc phải nhớ một bộ mã nội bộ, và dễ đọc sai kết quả.
- Đề xuất sửa: Đổi tên nhóm hành vi thành chữ (nhóm "tín hiệu", "khoảng trống", "trong nút") hoặc đổi tên mạng (N1–N6 kèm ngày). Đổi "Phase 3A–3D" thành "thí nghiệm khả thi KT1–KT4". Thay mã chiến dịch bằng mô tả, hoặc định nghĩa chúng một lần trong một bảng. Bổ sung danh mục ký hiệu: phương án B0–H, thí nghiệm E1, E2, chỉ số M1–M10, G0. Cân nhắc đổi "dữ liệu đại diện" thành "dữ liệu giả lập từ tài liệu".

### [HD-17] Mục lục ghi sai trang Tài liệu tham khảo và Phụ lục
- Mức: nhỏ
- Vị trí: main.tex:271–272; Mục lục (PDF trang tệp 11)
- Trích: Mục lục ghi "TÀI LIỆU THAM KHẢO … 101", "PHỤ LỤC … 103"; thực tế ở tr. 99 và tr. 102
- Vấn đề: `\addcontentsline` đặt sau `\printbibliography`, nên ghi số trang cuối cùng của danh mục tài liệu.
- Vì sao quan trọng: Lỗi nhỏ nhưng nhìn thấy ngay khi lật mục lục.
- Đề xuất sửa: Đặt `\phantomsection\addcontentsline{toc}{chapter}{TÀI LIỆU THAM KHẢO}` trước `\printbibliography`, hoặc dùng `\printbibliography[heading=bibintoc]`.

### [HD-18] Trang bỏ trống và hình có nhãn tiếng Anh
- Mức: nhỏ
- Vị trí: tr. 10 (Bảng 2.2 đứng một mình giữa trang), tr. 46 (gần trống), tr. 48 (Bảng 6.14 đứng một mình); Hình 6.4 (tr. 54) và Hình 6.5 (tr. 55)
- Trích: nhãn trong Hình 6.4: "Halting illegal lefts at each opposing green end, all seeds"; Hình 6.5: "simulation time (s)", "vehicles"
- Vấn đề: Bố cục trang lãng phí. Hình có nhãn tiếng Anh trong một luận văn viết bằng tiếng Việt.
- Vì sao quan trọng: Ảnh hưởng đến ấn tượng về độ hoàn thiện.
- Đề xuất sửa: Sửa sau khi rút gọn Chương 6. Vẽ lại nhãn trục và tiêu đề hình bằng tiếng Việt, hoặc bỏ tiêu đề trong hình vì caption đã đủ.
