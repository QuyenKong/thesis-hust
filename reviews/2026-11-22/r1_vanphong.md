# Biên tập văn phong

## Đánh giá tổng quát (3–5 câu)

Chương 1 đến Chương 4 viết gọn: câu ngắn, mỗi khẳng định có số hoặc trích dẫn, gần như không có từ sáo (không gặp "then chốt", "toàn diện", "Tóm lại"), ngoặc kép thống nhất kiểu ``…'', không có em dash. Vấn đề nằm ở Tóm tắt, Chương 5 (THỰC NGHIỆM VÀ ĐÁNH GIÁ) và Chương 6 (KẾT LUẬN). Các phần này viết bằng giọng nhật ký thí nghiệm: khoảng 100 mốc ngày ("mạng 29/10", "từ ngày 08/11/2026"), mã nội bộ không giải nghĩa (B0…H, PROXY\_D1, F2, M9), kết luận cũ để nguyên rồi bác bỏ ngay trong cùng mục, và các ghi chú `[TODO]`, `[Câu hỏi cho GVHD]` in đậm trong bản in. Tiếng Anh chen vào câu ở những chỗ đã có từ Việt thông dụng ("lane 0", "thinking", "Request", "Phase 3A--3D").

Lưu ý về bằng chứng: PDF được giao (128 trang) build từ `5_Evaluation.tex`, `6_Implementation.tex`, `7_Conclusions.tex`. Các tệp này không còn trên đĩa. `main.tex` hiện nạp `5_Experiments.tex` và `6_Conclusions.tex`, và cả Tóm tắt lẫn Chương 1 trong PDF đều khác nguồn hiện tại. Vì vậy tôi chỉ dẫn vị trí theo dòng `.tex` của nguồn hiện tại. Số trang PDF sẽ sai cho tới khi build lại.

## Nhận xét

### [VP-01] Giọng nhật ký thí nghiệm và báo cáo tiến độ thay cho giọng luận văn
- Mức: nghiêm trọng
- Vị trí: Chapter/5_Experiments.tex:951, 1089, 1047–1049, 665, 12; Chapter/6_Conclusions.tex:17, 27, 43; Chapter/0_3_Abstract.tex:15; Chapter/Appendix_B.tex:22, 36
- Trích:
  - 5:1089 (tiêu đề) "Thay đổi ngày 04/11 và kết quả tham chiếu trên mạng 04/11"
  - 5:665 "Ngày 31/10 có 9 ca không đạt; nay chúng đều đạt."
  - 5:1047 viết "nên khác biệt có tác dụng là điểm tách cạnh", rồi 5:1049 viết "kết luận ở phần quan sát rằng khác biệt đến từ điểm tách cạnh là không đúng."
  - 6:27 "Trên mạng 29/10, va chạm trên làn của B0 là 18,53/h; trên mạng 04/11, chỉ bỏ các kết nối…"
  - 0_3:15 "Trên mạng ngày 27/10, … Sau khảo sát hiện trường, kịch bản đổi sang đèn ba pha…"
  - Appendix_B:36 "Lược đồ đã cài đặt khác kế hoạch ban đầu ở hai điểm."
- Vấn đề: Ngày tháng được dùng làm tên phiên bản mạng, làm tiêu đề mục và làm mốc cho mọi thay đổi (grep `dd/1x` ra 94 lần trong Chương 5). Nhiều mục ghi lại diễn biến công việc: kết luận sai được giữ nguyên và bị bác ở đoạn sau, có "nay", có "kế hoạch ban đầu" (tức PLAN.md nội bộ). Chương 6 chia mục theo kiểu báo cáo tiến độ: "Đã hoàn thành", "Chưa thực hiện", "Việc trước mắt".
- Vì sao quan trọng: Hội đồng đọc luận văn như kết quả đã chốt. Một mục tự bác kết luận của chính nó làm người đọc nghi ngờ các mục còn lại. Ngày tháng không mang thông tin kỹ thuật: người đọc phải tra Bảng 5.x (phiên bản mạng) mới biết "mạng 29/10" khác "mạng 04/11" ở đâu.
- Đề xuất sửa: (1) Đặt cho mỗi phiên bản mạng một nhãn ngắn (V1–V6) kèm cột mô tả trong bảng phiên bản mạng (5:723), rồi trong văn bản gọi theo nội dung khác biệt. (2) Bỏ ngày khỏi tiêu đề và khỏi câu, trừ những chỗ ngày là dữ liệu thật (ngày quay video, ngày khảo sát). (3) Mỗi mục chỉ nêu kết luận cuối. Bỏ phần quan sát đã bị bác. (4) Đổi tiêu đề Chương 6 thành "Kết quả đạt được", "Hạn chế", "Hướng phát triển".
  - Câu viết lại cho 6:27: "Hai phiên bản mạng V5 và V6 chỉ khác nhau ở các kết nối dành cho xe vi phạm xuất phát từ làn 0 và làn 1. Bỏ các kết nối này làm va chạm trên làn của cấu hình SUMO mặc định (B0) giảm từ 18,53 xuống 1,87 va chạm/giờ, dù không xe nào của B0 đi qua chúng. Cơ chế của ảnh hưởng này chưa xác định."
  - Tiêu đề viết lại cho 5:1089: "Bỏ kết nối vi phạm từ làn 0 và 1: kết quả của B0 và B1".

### [VP-02] Ghi chú nội bộ, câu hỏi cho GVHD và TODO in ra trong bản luận văn
- Mức: nghiêm trọng
- Vị trí: Chapter/4_Rule_execution.tex:103; Chapter/0_3_Abstract.tex:17; Chapter/0_4_Abstract_English.tex:17; Chapter/6_Conclusions.tex:45; Chapter/3_Rule_generation.tex:57; Chapter/5_Experiments.tex:400, 710, 1341, 1418
- Trích:
  - 4:103 "\textbf{[Câu hỏi cho GVHD: nên làm mượt khoảng cách của tỷ lệ nhỏ …, hay giữ nguyên và nêu là hạn chế?]}"
  - 6:45 "\textbf{[TODO: câu kết luận chính về khả năng của LLM cục bộ trong hiệu chỉnh luật hành vi, chỉ trong phạm vi dữ liệu đại diện]}"
  - 0_4:17 "\textbf{[TODO: final E1/E2 results with a local LLM]}"
- Vấn đề: Đây là lời nhắn cho người hướng dẫn và mẫu điền chỗ trống (skill mục 24, 25, 29). Chúng in đậm ngay trong Tóm tắt, phần đầu tiên hội đồng đọc. Chương 6 không có câu kết luận chính, chỉ có chỗ trống đánh dấu TODO.
- Vì sao quan trọng: Nếu bản đọc thử hoặc bản nộp còn sót một dòng như vậy, hội đồng sẽ coi đó là bản nháp. Câu hỏi cho GVHD nằm trong mục phương pháp còn cho thấy một quyết định thiết kế chưa chốt.
- Đề xuất sửa: Chuyển câu hỏi ở 4:103 ra tệp ghi chú riêng hoặc thành chú thích `%`. Trong văn bản chỉ giữ hạn chế: "Quy tắc này chưa xử lý hết trường hợp tỷ lệ rất nhỏ: … nên ép hành vi về 0 vẫn cho khoảng cách nhỏ hơn. Mục 6.x nêu đây là một hạn chế của hàm khoảng cách." Trong Tóm tắt, bỏ TODO và kết thúc ở câu giới hạn. Nếu cần nhắc việc còn thiếu, dùng một macro tắt được khi build bản nộp, ví dụ `\todo{}` rỗng ở chế độ final. Không để chữ in đậm trong thân bài.

### [VP-03] Mã nội bộ không kèm nghĩa; mã F2 mang hai nghĩa
- Mức: nghiêm trọng
- Vị trí: Chapter/6_Conclusions.tex:31, 33, 39, 53, 57, 59; Chapter/5_Experiments.tex:23, 376, 922, 596, 888, 1017; Chapter/0_3_Abstract.tex:15
- Trích:
  - 6:31 "mục tiêu M9 chưa được định nghĩa lại theo mô hình này … nên M8 phải đọc làn ở đầu đoạn 30~m"
  - 6:59 "thí nghiệm sức chứa vùng chờ … và thí nghiệm 3B"
  - 5:23 "F2 (tìm khoảng trống khi ùn) gồm hành vi 4--8", trong khi 5:596 viết "Mạng F2 (làn rẽ phải liên tục, …)" và 5:922 viết "Trong kiểm tra chức năng nhóm F2"
  - 5:888 "chỉ số tương ứng (M11) … không được hiện thực"
  - 6:39 "P1 không thể đủ điều kiện vì giữ cấu trúc B1; P2 có 11/24 lần chạy đủ điều kiện ở PROXY\_D2 và PROXY\_D3"
- Vấn đề: Chương 6 dùng trơ các mã B0, B1, B2, P1, P2, H, PROXY\_D1, M8, M9, "3B", "v005", "xfail". Người đọc chỉ đọc Kết luận sẽ không hiểu. Riêng "F2" vừa là nhóm hành vi tìm khoảng trống, vừa là tên một phiên bản mạng, vừa là mã hạng mục trong Bảng 5.x (5:596). Câu 5:922 "nhóm F2" vì vậy đọc theo hai nghĩa đều được.
- Vì sao quan trọng: Kết luận và Tóm tắt là hai phần được đọc riêng. Mã trùng làm sai nghĩa câu, không chỉ khó đọc.
- Đề xuất sửa: Bỏ mã F1/F2/F3 cho nhóm hành vi và gọi bằng tên ("nhóm tìm khoảng trống"), vì Chương 3 đã gọi như vậy. Đổi tên mạng theo VP-01. Ở Chương 6, lần đầu mỗi mã xuất hiện thì kèm nghĩa trong ngoặc. Viết lại 6:31: "Xe đi sai làn rồi cắt về làn đúng trước vạch dừng, nên M8 (đi sai làn) phải đọc làn của xe ở đầu đoạn 30~m thay vì tại vạch. Mục tiêu của M9 (chặn làn rẽ phải liên tục) chưa được định nghĩa lại theo mô hình làn 30~m."

### [VP-04] Tóm tắt hai bản: thuật ngữ mơ hồ và câu tiếng Anh chưa tự nhiên
- Mức: nên sửa
- Vị trí: Chapter/0_3_Abstract.tex:9, 13, 15; Chapter/0_4_Abstract_English.tex:9, 15
- Trích:
  - 0_3:15 "không đặc tả nào đạt tiêu chí đủ điều kiện, vì mô hình nền quá tải ở mức nhu cầu đại diện" / 0_4:15 "because the base model is overloaded at the proxy demand"
  - 0_3:15 "SUMO mặc định đủ điều kiện ở 15/15 lần chạy" / 0_4:15 "default SUMO is eligible in 15 of 15 runs"
  - 0_4:9 "vehicles run red lights in swarms, … ride on the sidewalk in queues"
  - 0_4:15 tiêu đề đoạn "Results so far"
  - 0_3:13 "Mã xác định kiểm tra đặc tả theo lược đồ…"
- Vấn đề: Nội dung hai bản khớp nhau. Lỗi nằm ở câu chữ. Trong một luận văn về LLM, "base model" sẽ bị đọc là mô hình LLM gốc, trong khi ý tác giả là mạng mô phỏng không thông qua hết nhu cầu. "Đủ điều kiện/eligible" là thuật ngữ riêng của Chương 4 nhưng Tóm tắt dùng mà không giải thích. "In swarms" và "in queues" nghe dịch máy; "in queues" còn có thể hiểu là xe xếp hàng trên vỉa hè. "Results so far" là giọng báo cáo tiến độ. "Mã xác định" nghĩa là mã nhận dạng, không phải mã tất định (xem VP-06).
- Vì sao quan trọng: Người đọc Tóm tắt không có ngữ cảnh của các chương sau.
- Đề xuất sửa:
  - EN: "Motorcyclists run red lights in groups, start before the green, weave laterally, stop in the right-turn lane, ride on the sidewalk to bypass queues, and turn left illegally by waiting inside the junction."
  - EN: "None of its 12 specifications meets the acceptance criteria, because the simulated network cannot carry the proxy demand without gridlock." và "default SUMO meets all acceptance criteria (no gridlock, no vehicles left waiting to enter, flow and collision limits) in 15 of 15 runs".
  - EN: đổi "Results so far" thành "Results".
  - VN: "vì mạng mô phỏng không thông qua hết nhu cầu đại diện"; lần đầu dùng "đủ điều kiện" thì giải thích: "đạt cả năm tiêu chí chấp nhận (không kẹt, không còn xe chờ vào mạng, qua cổng lưu lượng, va chạm dưới ngưỡng)".

### [VP-05] Tiếng Anh chen vào câu khi đã có từ Việt thông dụng; "lane" và "làn" lẫn trong cùng câu
- Mức: nên sửa
- Vị trí: Chapter/5_Experiments.tex:890, 23, 1144, 1151, 468, 867 (tiêu đề), 870, 328; Chapter/6_Conclusions.tex:27, 31
- Trích:
  - 5:890 "chủ yếu vì xe ở làn 1--2 không kịp sang lane 0"
  - 5:1144 "Request là prompt vòng 2 của P2 dựng bằng v004; thinking bật"
  - 5:468 định nghĩa "Chế độ suy nghĩ (thinking)", nhưng 5:1151 viết "Thinking bị tắt vì … phần thinking dài 18.554 … ký tự"
  - 5:867 (tiêu đề) "Thí nghiệm khả thi Phase 3A--3D trên mạng có làn rẽ phải liên tục"
  - 5:870 "chạy trên kịch bản đồ chơi riêng"
- Vấn đề: "lane 0/1/2" xuất hiện 44 lần, xen với "làn 1", "làn 2" (5:765, 5:850, 5:890). "Phase" (8 lần), "backend", "runtime", "pipeline", "Request" đều có từ Việt tương đương. Thuật ngữ đã Việt hóa ("chế độ suy nghĩ") lại bị bỏ ngay ở các đoạn sau. "Kịch bản đồ chơi" là dịch từng chữ "toy scenario".
- Vì sao quan trọng: Câu đọc như ghi chú kỹ thuật nội bộ. Việc "lane 0" và "làn 1" cùng có mặt khiến người đọc phải tự hỏi đây là hai khái niệm hay một.
- Đề xuất sửa: Định nghĩa một lần "làn 0 là làn ngoài cùng bên phải (lane 0 trong SUMO)", sau đó chỉ dùng "làn 0/1/2". Giữ nguyên văn tiếng Anh chỉ cho tên thuộc tính SUMO trong `\texttt{}`. Viết lại 5:1144: "Yêu cầu gửi LLM là prompt vòng 2 của P2, dựng bằng phiên bản v004; bật chế độ suy nghĩ, giới hạn 4500 token." Viết lại 5:870: "Ba thí nghiệm 3A, 3B, 3C chạy trên các mạng thử nhỏ dựng riêng." Tiêu đề 5:867: "Bốn thí nghiệm khả thi 3A–3D trên mạng có làn rẽ phải liên tục".

### [VP-06] Một khái niệm, nhiều tên gọi
- Mức: nên sửa
- Vị trí: Chapter/1_Introduction.tex:11, 9; Chapter/5_Experiments.tex:652, 858, 490; Chapter/2_Literature_review.tex:66; Chapter/0_3_Abstract.tex:15; Chapter/4_Rule_execution.tex:112; Chapter/5_Experiments.tex:850, 1015
- Trích:
  - "mã xác định" (12 lần, ví dụ 1:11) nhưng 5:652 viết "Tính tất định của bộ sinh dữ liệu"
  - B1 được gọi là "bộ luật viết tay" (1:78, 5:490), "bộ luật thủ công" (0_3:15, 5:858) và "phương án thủ công" (2:66)
  - Xe chưa vào được mạng được gọi là "xe chờ được đưa vào mạng" (4:112), "xe chưa chèn được" (5:850) và "xe chờ chèn" (5:1015)
  - B0 được gọi là "mô hình chuẩn", "mô hình mặc định", "SUMO mặc định", "cấu hình mặc định", "cấu hình cơ sở" và "mô hình nền" (23 lần, sáu tên)
  - 1:9 dùng "ngã giao" trong khi toàn văn dùng "nút giao"
- Vấn đề: Đây là lỗi đổi từ đồng nghĩa (skill mục 14). "Mã xác định" còn sai nghĩa, vì "xác định" trong tiếng Việt kỹ thuật thường hiểu là nhận dạng.
- Vì sao quan trọng: Người đọc tưởng "mô hình chuẩn" (mô hình hành vi của trình mô phỏng nói chung) và "B0" (một cấu hình cụ thể) là hai thứ khác nhau, trong khi có chỗ tác giả dùng chúng như một.
- Đề xuất sửa: Chọn một tên cho mỗi khái niệm và ghi vào một bảng thuật ngữ ngắn ở cuối Chương 1 hoặc trong danh mục: "mã tất định"; "bộ luật viết tay B1"; "xe chờ vào mạng" (định nghĩa ở 4:112); "mô hình chuẩn" chỉ dùng cho khái niệm chung, "cấu hình SUMO mặc định (B0)" dùng cho cấu hình cụ thể.

### [VP-07] "Dữ liệu đại diện" gợi nghĩa ngược với bản chất dữ liệu
- Mức: nên sửa
- Vị trí: Chapter/1_Introduction.tex:84; Chapter/5_Experiments.tex:14, 104, 400, 922; Chapter/0_3_Abstract.tex:15, 17
- Trích:
  - 5:400 "luận văn dựng năm ``ngày đại diện'' PROXY\_D1--PROXY\_D5"
  - 5:922 "mạng đại diện quá tải ở mức nhu cầu đại diện 8180 xe/h"
- Vấn đề: Trong tiếng Việt, "đại diện" nghĩa là "mang tính đại diện" (representative), tức là phản ánh được nút giao. Dữ liệu này thật ra được dựng từ tài liệu về nút khác, và một phần giá trị là giả định. Từ này còn gắn vào "mạng", "cấu hình", "nhu cầu", "mục tiêu", nên câu 5:922 đọc như thể số liệu đã đo tại nút.
- Vì sao quan trọng: Nghĩa gợi ra trái với điều tác giả muốn nói, và trái với chính các câu rào đón trong luận văn ("chưa cho biết mô phỏng giống giao thông thực").
- Đề xuất sửa: Đổi thành "dữ liệu thay thế" và định nghĩa một lần: "dữ liệu thay thế (proxy) là dữ liệu dựng từ số liệu đã công bố ở nút khác và từ giả định, dùng tạm khi chưa có video". Với mạng, gọi "mạng thử nghiệm", không gọi "mạng đại diện".

### [VP-08] Đầu và cuối chương lặp lại ý vừa nói
- Mức: nên sửa
- Vị trí: Chapter/2_Literature_review.tex:104; Chapter/3_Rule_generation.tex:8, 217; Chapter/4_Rule_execution.tex:8, 118; Chapter/5_Experiments.tex:1420, 1437; Chapter/6_Conclusions.tex:9
- Trích:
  - 2:104 "Chương này đã cho thấy mỗi hướng hiện có giải quyết được một phần của bài toán…", và 3:8 mở đầu gần như nguyên văn: "Chương 2 cho thấy mỗi hướng tiếp cận hiện có giải quyết được một phần của bài toán…"
  - 3:217 "Chương này đã nêu tổng quan phương pháp và trình bày phần sinh luật: kịch bản…, danh mục…, cơ sở…, dạng biểu diễn…, lý do…, và vòng tinh chỉnh…"
  - 5:1420 "Bảy giải pháp trên có chung một nguyên tắc: mọi thứ … đều phải đi qua một điểm kiểm tra tường minh…"
- Vấn đề: Mỗi chương kết bằng một đoạn liệt kê lại các mục, rồi chương sau mở bằng chính đoạn đó (skill mục 40). Đoạn 5:1420 gán cho bảy giải pháp "một nguyên tắc chung", sau đó liệt kê lại cả bảy.
- Vì sao quan trọng: Phần tóm tắt cuối chương không mang thông tin mới. Riêng 5:1437 lặp gần hết Chương 6.
- Đề xuất sửa: Bỏ các đoạn tóm tắt cuối chương 2, 3, 4. Mỗi chỗ chỉ giữ một câu nối nếu cần, ví dụ thay 3:217 bằng "Một đặc tả do LLM sinh mới chỉ là văn bản; Chương 4 trình bày cách kiểm tra và thực thi nó." Thay câu đầu 3:8 bằng "Chương này trình bày phần đầu của phương pháp, phần sinh luật." Bỏ 5:1420.

### [VP-09] In đậm đầu đoạn tràn lan, khuôn tiểu mục lặp và nhảy cấp tiêu đề
- Mức: nên sửa
- Vị trí: Chapter/5_Experiments.tex:142, 168 (nhảy cấp); 1264–1418 (khuôn Vấn đề/Giải pháp/Kết quả); 920, 946, 894, 1022; Chapter/4_Rule_execution.tex:42–50
- Trích:
  - 5:116 `\section{Hiện thực phương pháp trên SUMO}`, rồi 5:142 là `\subsubsection{Tham số tĩnh}`, không có `\subsection` ở giữa. Bản in sẽ hiện "a, Tham số tĩnh" ngay dưới 5.2.
  - 5:920 "Các ngưỡng đóng băng là \textbf{4 va chạm trên làn/h} và \textbf{142 va chạm trong nút/h}"
  - 5:946 "\textbf{Diễn giải có cơ sở.}"; 5:894 "\textbf{Phần không còn áp dụng trên mạng 29/10.}"
  - 5:1022 "\textbf{Câu hỏi.} … \textbf{Thiết lập.} B1 trên PROXY\_D2…" (hai nhãn trên một dòng)
- Vấn đề: Chương 5 có 91 nhãn in đậm đầu đoạn. Bộ nhãn "Thiết lập / Quan sát / Diễn giải" thống nhất và hữu ích, nhưng nhiều nhãn khác chỉ dùng một lần và là nhãn tạm. Bảy giải pháp kỹ thuật đều được chia thành `\subsubsection{Vấn đề}`, `{Giải pháp}`, `{Kết quả}`, tức 21 tiêu đề con, mỗi tiêu đề chỉ có một hai đoạn. Ngoài ra còn in đậm cả con số (skill mục 16, 17, 20).
- Vì sao quan trọng: Tiêu đề nhảy cấp làm mục lục và cách đánh số hỏng. Khi in đậm quá nhiều, không còn chỗ nào thật sự nổi bật.
- Đề xuất sửa: Đổi 5:142 và 5:168 thành `\subsection`. Giữ bộ nhãn "Thiết lập / Quan sát / Diễn giải / Giả thuyết cần kiểm chứng" và bỏ các nhãn khác. Ở Mục 5.x (bảy giải pháp), bỏ ba `\subsubsection` của mỗi giải pháp, mở mỗi giải pháp bằng một câu nêu vấn đề. Bỏ in đậm số ở 5:920.

### [VP-10] Điệp khúc đối lập "thay vì", "chứ không", "không phải X mà là Y"
- Mức: nên sửa
- Vị trí: Chapter/5_Experiments.tex:1269, 1258, 1377, 1420, 507; Chapter/3_Rule_generation.tex:192, 194
- Trích:
  - 5:1269 "Rủi ro lớn nhất khi để LLM sinh luật không phải là giá trị chưa tối ưu, mà là đầu ra không chạy được"
  - Cùng một ý "truy nguyên thay vì nới ngưỡng" lặp ba lần: 5:1258 ("Truy nguyên nhân thay vì nới ngưỡng"), 5:1377 ("Luận văn không nới ngưỡng va chạm mà truy nguyên nhân"), 5:1420 ("va chạm và kẹt được truy nguyên thay vì nới ngưỡng")
  - 3:194 "phương pháp không dựa vào việc LLM đúng mà dựa vào bộ lọc phía sau"
- Vấn đề: "thay vì" xuất hiện 25 lần, cộng với "chứ không" và "không phải… mà…". Phần lớn các câu này không bác bỏ một hiểu lầm nào có thật (skill mục 11). Câu đọc như khẩu hiệu.
- Vì sao quan trọng: Mẫu câu này là dấu hiệu "văn AI" mà skill liệt kê. Khi lặp nhiều lần cùng một ý, nó thành lời tự khen.
- Đề xuất sửa: Nêu thẳng điều đã làm. 5:1269: "Rủi ro lớn nhất khi để LLM sinh luật là đầu ra không chạy được, hoặc chạy được nhưng sai mà không báo lỗi." 5:1377: "Nguyên nhân được truy bằng danh mục từng va chạm và các thí nghiệm đổi một yếu tố mỗi lần (Mục 5.x)." Chỉ giữ "thay vì" khi phương án bị loại thật sự đã được cân nhắc, như ở 5:1334.

### [VP-11] Câu và đoạn nhồi nhiều mệnh đề
- Mức: nên sửa
- Vị trí: Chapter/5_Experiments.tex:12, 200, 89; Chapter/6_Conclusions.tex:27; Chapter/3_Rule_generation.tex:121
- Trích:
  - 5:200 "Nhóm (v) chỉ chạy ở chế độ P2, từ prompt \texttt{v005}: đặc tả phải dùng đủ sáu loại luật TraCI và mỗi loại phải được bật ở ít nhất một mục, tức $p > 0$ với …, $p_0 > 0$ với …, và ít nhất một xác suất lựa chọn lớn hơn 0 với …; … không có xác suất nên chỉ cần có mặt."
  - 5:12 là một đoạn gồm 14 câu: vừa giới thiệu bố cục 12 mục, vừa báo trạng thái "Tại ngày 08/11/2026…", vừa nêu kết quả chiến dịch.
- Vấn đề: Câu dài, chứa danh sách lồng trong danh sách, ngăn bằng dấu chấm phẩy. Đoạn mở Chương 5 gộp ba việc khác nhau.
- Vì sao quan trọng: Người đọc phải đọc lại mới tách được điều kiện của từng luật.
- Đề xuất sửa: Viết lại 5:200: "Nhóm (v) chỉ chạy ở chế độ P2 và áp dụng từ prompt v005. Nhóm này yêu cầu đặc tả có đủ sáu loại luật TraCI và bật mỗi loại cho ít nhất một nguyên mẫu. Với `early_start` và `uturn_bypass`, bật nghĩa là $p > 0$. Với `swarm_red_running`, bật nghĩa là $p_0 > 0$. Với `queue_space_seeking`, bật nghĩa là có ít nhất một xác suất lựa chọn lớn hơn 0. Hai luật `illegal_left_box` và `slow_lane_center` không có xác suất nên chỉ cần có mặt." Với 5:12, giữ phần bố cục, chuyển câu trạng thái sang Mục 5.x (Trạng thái triển khai) và chuyển kết quả sang Mục 5.x (các chiến dịch).

### [VP-12] Câu dịch gượng, bị động "bởi", từ chưa định nghĩa
- Mức: nhỏ
- Vị trí: Chapter/1_Introduction.tex:71; Chapter/5_Experiments.tex:202, 1340, 12; Chapter/3_Rule_generation.tex:47; Chapter/4_Rule_execution.tex:107
- Trích:
  - 1:71 "đọc được bởi người làm quy hoạch"
  - 5:202 "Danh sách này gửi ngược lại cho LLM được."
  - 5:1340 "nên lỗi cũ không quay lại mà không bị phát hiện"
  - 5:12 "Tại ngày 08/11/2026" (dịch từ "as of")
  - 3:47 "Bốn nghiên cứu cho bốn mảnh của cùng một hành vi."
  - 4:107 "trong mỗi nhóm chia đều cho các chỉ số con …, rồi cho các khóa" ("khóa" chưa được định nghĩa ở chỗ nào trước đó)
- Đề xuất sửa: 1:71 thành "người làm quy hoạch đọc được". 5:202 thành "Danh sách lỗi được gửi lại nguyên văn cho LLM." 5:1340 thành "nên kiểm thử sẽ báo lỗi nếu cách giữ xe cũ được đưa lại vào mã." 3:47 thành "Bốn nghiên cứu, mỗi nghiên cứu đo một khía cạnh của hành vi vượt đèn đỏ." 4:107 thành "…rồi chia đều cho các đại lượng thành phần của chỉ số con (gọi là khóa, ví dụ từng nhánh hoặc từng loại xe)."

### [VP-13] Báo trước số lượng cho đủ nhịp, có chỗ đếm sai
- Mức: nhỏ
- Vị trí: Chapter/2_Literature_review.tex:66; Chapter/5_Experiments.tex:119, 1273; Chapter/3_Rule_generation.tex:192
- Trích:
  - 2:66 "Công trình này có ba giới hạn. Cấu trúc luật do người lập mô hình chọn. Tham số được hiệu chỉnh cho một đoạn phố… Mô hình không có xuất phát sớm…, và chạy trên GAMA thay vì SUMO." Đoạn này có bốn ý mà nói là ba.
  - 5:119 "vì ba lý do", nhưng lý do 3 (libsumo) là một phần của lý do 2 (TraCI).
  - 5:1273 "Bốn quyết định thiết kế: Mỗi dòng…", sau đó các quyết định viết thành đoạn liền, không đánh dấu.
- Vấn đề: Câu "có ba/bốn X" đứng trước hầu hết các liệt kê (13 lần chỉ với "ba"). Có chỗ số lượng nói ra không khớp số ý thật (skill mục 13).
- Đề xuất sửa: Chỉ báo trước số lượng khi người đọc cần đếm. 2:66 có thể viết "Công trình này khác bài toán của luận văn ở bốn điểm:" rồi dùng `enumerate`. 5:119 viết "SUMO có mô hình làn con cho dòng xe máy, và có giao diện TraCI (cùng bản chạy trong tiến trình là libsumo) cho phép…".

### [VP-14] Cách viết số, đơn vị, ngày giờ không thống nhất
- Mức: nhỏ
- Vị trí: Chapter/5_Experiments.tex:468, 1144, 1160, 532, 920; Chapter/2_Literature_review.tex:33, 41; Chapter/5_Experiments.tex:597
- Trích:
  - 5:468 "cửa sổ ngữ cảnh 32.768 token. Câu trả lời giới hạn 7000 token": cùng một đoạn, một số có dấu phân cách hàng nghìn, một số không.
  - 5:1144 "câu trả lời 1.526--4.500 token", nhưng cùng đoạn có "bị cắt ở 4500 token"
  - 2:41 "17142 xe"; 2:33 "2681 người"
  - 5:1160 "3~h~25 (06:03--09:28)"
  - 5:532, 5:920 "va chạm trên làn/h", "va chạm trong nút/h"
  - 5:597 "28--30/10"; Tóm tắt tiếng Anh viết "27 October"; nơi có năm, nơi không
- Đề xuất sửa: Chọn một quy ước, ví dụ dấu chấm phân cách hàng nghìn cho mọi số từ 1.000 trở lên ("7.000 token", "17.142 xe"), hoặc không phân cách cho mọi số dưới 100.000; ghi quy ước một lần. Thời lượng viết "3 giờ 25 phút". Đơn vị tỷ lệ viết sau danh từ đầy đủ: "số va chạm trên làn mỗi giờ" hoặc "va chạm/giờ (trên làn)". Bỏ ngày khỏi văn bản (VP-01); chỗ nào cần giữ ngày thì luôn ghi đủ năm.

### [VP-15] Lỗi dấu câu, chữ hoa và trình bày
- Mức: nhỏ
- Vị trí: Chapter/5_Experiments.tex:1425, 765, 1273, 801
- Trích:
  - 5:1425 "biến \texttt{SUMO\_HOME} trỏ tới thư mục cài đặt, Máy chính chạy Windows 11 Pro": dấu phẩy đứng trước chữ hoa, đúng ra phải là dấu chấm.
  - 5:765 "Các điểm đáng chú ý: Trong mọi chu kỳ…": viết hoa sau dấu hai chấm.
  - 5:1273 "Bốn quyết định thiết kế: Mỗi dòng của tệp miền mang bằng chứng.": cũng viết hoa sau dấu hai chấm.
  - 5:801 "\end{figure} Số va chạm mỗi lần chạy là 0--1": đoạn văn dính liền sau môi trường hình, không có dòng trống. Đoạn này sẽ nối vào đoạn trước một cách không chủ đích.
- Đề xuất sửa: 5:1425 thay dấu phẩy bằng dấu chấm. 5:765 bỏ "Các điểm đáng chú ý:" và mở thẳng bằng "Trong mọi chu kỳ…". 5:1273 viết "Có bốn quyết định thiết kế." rồi xuống đoạn. 5:801 thêm dòng trống sau `\end{figure}`.

### [VP-16] Viết tắt dùng mà không giải nghĩa; danh mục từ viết tắt thiếu
- Mức: nhỏ
- Vị trí: Chapter/2_Literature_review.tex:64; Chapter/5_Experiments.tex:524, 589, 377; glossary.tex
- Trích:
  - 2:64 "Mô hình dùng bám xe IDM và chuyển làn MOBIL."
  - 5:524 "Optuna dùng bộ lấy mẫu TPE với seed 0"
  - 5:377 "Tệp sinh ra khai báo XSD của SUMO"
- Vấn đề: IDM, MOBIL, TPE, XSD, GAMA không được giải nghĩa ở lần đầu dùng. Danh mục viết tắt chỉ có sáu mục (GEH, LLM, OSM, PET, SUMO, TraCI). SSM được giải nghĩa ở 5:589, trong một ô bảng, nên người đọc không tìm lại được.
- Đề xuất sửa: Giải nghĩa ở lần đầu dùng, ví dụ "mô hình bám xe IDM (Intelligent Driver Model)", "bộ lấy mẫu TPE (Tree-structured Parzen Estimator)". Thêm IDM, MOBIL, TPE, SSM, XSD, IQR vào `glossary.tex`.

### [VP-17] Số bảng của lược đồ quan sát không khớp giữa các chương
- Mức: nhỏ
- Vị trí: Chapter/4_Rule_execution.tex:64; Chapter/5_Experiments.tex:376, 397; Chapter/Appendix_B.tex:8, 22
- Trích:
  - 4:64 "một lược đồ dữ liệu quan sát gồm mười bảng … và ba bảng cho nhóm tìm khoảng trống"
  - Appendix_B:8 "Bảng B.1 trình bày lược đồ đã cài đặt", nhưng bảng chỉ có bảy tệp, không có ba bảng của nhóm tìm khoảng trống.
  - Appendix_B:22 "\texttt{traversals.csv} (bổ sung so với kế hoạch)"
- Vấn đề: Chương 4 hứa "định nghĩa đầy đủ nằm ở Phụ lục B", nhưng Phụ lục B thiếu ba bảng. Phụ lục so sánh với "kế hoạch", một tài liệu nội bộ mà người đọc không có.
- Đề xuất sửa: Thêm ba bảng còn thiếu vào Bảng B.1, hoặc sửa 4:64 cho khớp. Bỏ "(bổ sung so với kế hoạch)" và đoạn Appendix_B:36 "khác kế hoạch ban đầu". Phần về tầng quỹ đạo chưa cài đặt chuyển sang mục hạn chế.
