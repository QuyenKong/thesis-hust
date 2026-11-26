# Lập luận và nhất quán

## Đánh giá tổng quát (3–5 câu)

Phần lớn các khẳng định ở Tóm tắt và Chương Kết luận đã được rào đúng mức ("quy trình vận hành được", "chưa so sánh được LLM với Optuna"), và các con số lặp lại (403 ca kiểm thử, 36 lần chạy, 15/15, 24 thuộc tính, sáu luật, $S$ của từng chiến dịch) khớp nhau giữa Tóm tắt, Chương 5 và Chương 6. Chỗ yếu nằm ở ba kết luận nhân quả mà các tóm tắt đều nhắc lại nhưng số liệu không đỡ được: gia tốc xe máy là "nguyên nhân chính" khiến cả ba chiến dịch thất bại, P2 "hạ $S$ bằng cách bỏ bớt luật", và P1 "không thể" đủ điều kiện. Baseline B0 được gọi là "SUMO mặc định", trong khi nó đã chạy trên mạng có bản vá và có lớp xe vi phạm. Vì vậy khoảng trống nghiên cứu nêu ở Chương 1 và 2 ("SUMO mặc định không có dừng chờ giữa nút") bị chính thí nghiệm của luận văn bác một phần. Các giới hạn quan trọng, như việc chỉ chạy 1800 s đầu, mục tiêu giả định chiếm hơn nửa $S$, ngưỡng va chạm không tính lại theo mạng và hành vi 9, 11 không có chỉ số, chỉ nằm rải rác trong Chương 5 mà không được gom vào Chương 6. **Lưu ý quy trình:** PDF được giao (128 trang) build từ `5_Evaluation.tex`, `6_Implementation.tex`, `7_Conclusions.tex`, nhưng ba tệp này không có trên đĩa. Nguồn hiện tại là `5_Experiments.tex` (Chương 5) và `6_Conclusions.tex` (Chương 6), và Tóm tắt cùng Chương 1 trong PDF là bản cũ hơn nguồn. Tôi phản biện theo nguồn trên đĩa. Số trang PDF chỉ ghi ở những chỗ nội dung trùng: Chương 4 nguồn ứng với PDF Ch.5 (tr. 23–27), Chương 5 nguồn ứng với PDF Ch.6 (tr. 28–94), Chương 6 nguồn ứng với PDF Ch.7 (tr. 95–98). Trong PDF, Bảng 6.1–6.4 trôi xuống tr. 86–94, cách xa chỗ được nhắc tới (tr. 28–33).

## Nhận xét

### [LG-01] "Nguyên nhân chính là gia tốc xe máy" bị mở rộng cho cả ba chiến dịch
- Mức: nghiêm trọng
- Vị trí: Chapter/0_3_Abstract.tex:15, Chapter/0_4_Abstract_English.tex:15, Chapter/5_Experiments.tex:1437, Chapter/6_Conclusions.tex:33 ↔ Chapter/5_Experiments.tex:1208–1230, 1173 (PDF tr. 3 tóm tắt, tr. 85, 96 ↔ tr. 71, 73)
- Trích: "Optuna và hai chiến dịch LLM ... đều dùng hết ngân sách 36 lần chạy nhưng chưa có đặc tả nào đủ điều kiện; phân tích loại bỏ cho thấy nguyên nhân chính là gia tốc xe máy chuyển giao từ tài liệu trong bộ luật thủ công." / "Bỏ mọi luật, xe máy bỏ `accel` ... 10, 126, 52" / "B2 tìm `accel` của xe máy trong [0,8; 6] m/s², nhưng cả 12 thử nghiệm vẫn có 20–338 xe chờ chèn ở PROXY_D1; thử nghiệm `t000` với `accel` 5,8 vẫn còn 256 xe"
- Vấn đề: Phân tích loại bỏ chỉ chạy trên B1, PROXY_D1, 3 seed. Trả `accel` về mặc định vẫn còn 10–126 xe chờ chèn, và va chạm tăng gấp ba. B2 đã thử `accel` gần 6 mà vẫn còn 256 xe, nên chính dữ liệu của luận văn cho thấy `accel` không đủ giải thích. P2 không dùng cấu trúc B1, và ở PROXY_D2, D3 nó bị loại vì va chạm trên làn và vì có hơn 1 va chạm liên quan can thiệp, chứ không vì xe chờ chèn (5:1173).
- Vì sao quan trọng: Đây là câu nhân quả duy nhất về kết quả chiến dịch có mặt trong Tóm tắt, và người chấm sẽ đọc nó như phát hiện chính.
- Đề xuất sửa: Giới hạn phạm vi và hạ mức khẳng định. Ví dụ: "Trên PROXY_D1 (3 seed), phân tích loại bỏ trên B1 cho thấy `accel` 1,1 m/s² của xe máy là yếu tố lớn nhất được thử, nhưng trả nó về mặc định vẫn chưa hết xe chờ chèn; nguyên nhân thất bại của P2 ở PROXY_D2–D3 là va chạm." Sửa tương ứng ở 5:1437, 6:33 và Appendix_A.tex:100 ("là nguyên nhân chính" → "là yếu tố lớn nhất trong các biến thể đã thử").

### [LG-02] "P2 hạ $S$ bằng cách bỏ bớt luật" không có bằng chứng, và số liệu còn đi ngược
- Mức: nghiêm trọng
- Vị trí: Chapter/6_Conclusions.tex:33, Chapter/5_Experiments.tex:1176, 1285, 1437 ↔ Chapter/5_Experiments.tex:1167, Chapter/Appendix_A.tex:91–92, 100 (PDF tr. 96, 72, 76, 85 ↔ tr. 71, 107)
- Trích: "ở chế độ sinh cả cấu trúc, mô hình hạ $S$ bằng cách bỏ bớt luật" / "$S$ thấp hơn của P2 đến từ đặc tả bỏ bớt một số hành vi" / Bảng 4.campaigns_n1108: "$S$ nhỏ nhất 1,1438 (B2) ... 1,1680 (P2)"
- Vấn đề: (a) B2 vẫn giữ nguyên cấu trúc B1 mà đạt $S$ nhỏ hơn P2 (1,1438 so với 1,1680), nên việc "bỏ luật" không cần để có $S$ thấp. (b) Không có biến thể nào cho P2 thêm lại các luật đã bỏ để so $S$. Chính 5:1176 thừa nhận "chưa tách được" nguồn gốc của phần giảm xe chờ chèn. (c) Bản thân B1/B2 cũng không có `illegal_left_box` và `slow_lane_center`, còn `early_start` và `queue_space_seeking` có xác suất bằng 0. Như vậy B1 cũng "tắt" các hành vi 3, 5, 6, 7, 11. Kiểm tra đủ luật (`coverage`) chỉ áp cho P2, nên khi so P2 với B2 và H ở E2, hai bên không chịu cùng ràng buộc.
- Vì sao quan trọng: Đây là kết luận duy nhất về hành vi của LLM ở chế độ sinh cấu trúc, mà chế độ này là đóng góp chính. Kết luận còn được dùng để biện minh cho một thay đổi phương pháp (`v005`).
- Đề xuất sửa: Viết lại thành quan sát, không quy nhân quả. Ví dụ: "Các đặc tả P2 từ vòng 2 không có `queue_space_seeking`, `uturn_bypass`, `slow_lane_center`; $S$ nhỏ nhất của P2 (1,1680) vẫn lớn hơn của B2 (1,1438). Luận văn chưa kiểm tra việc bỏ luật có làm giảm $S$ hay không." Ở Mục 3.8 (Chương 5), nêu rõ rằng ràng buộc `coverage` chỉ áp cho P2 và cấu trúc B1 dùng cho B2, P1 chỉ có bốn loại luật.

### [LG-03] B0 không phải "SUMO mặc định" theo nghĩa mà Chương 1–2 dùng để nêu khoảng trống
- Mức: nghiêm trọng
- Vị trí: Chapter/1_Introduction.tex:16, Chapter/2_Literature_review.tex:93, Chapter/5_Experiments.tex:488 ↔ Chapter/5_Experiments.tex:690, 699, 774, 89 (PDF tr. 2, 9–10, 26 ↔ tr. 50–51, 55, 86)
- Trích: "Với tham số mặc định, chúng không tạo ra ... dừng chờ có chủ đích giữa nút." / Bảng 2.2: "SUMO mặc định, kể cả với làn con, không biểu diễn ... dừng chờ giữa nút" / "B0: Mô hình mặc định của SUMO, không có luật có điều kiện" ↔ "Số xe chờ giữa nút mỗi chu kỳ (M7a) B0 4,00 ... dữ liệu đại diện 5,59" / "Xe chờ giữa nút có ở cả B0 vì nhu cầu của mọi phương án có xe lớp vi phạm ... qua bản vá mạng" / "Cơ chế điểm chờ nội bộ sẵn có của SUMO tái hiện được cả chuỗi ... Không cần tùy chọn hay sửa mạng."
- Vấn đề: B0 chạy trên mạng có kết nối rẽ trái chỉ cho `custom1`, có vỉa hè, có `internal-junctions.vehicle-width` 3,5 m (5:89), và nhu cầu có lớp xe vi phạm. Thế mà B0 đã đạt 4,00 xe chờ giữa nút mỗi chu kỳ, trong khi B1 chỉ đạt 4,89. Hành vi 10 vì vậy chủ yếu đến từ bản vá mạng cộng cơ chế sẵn có của SUMO, không đến từ luật. Câu "không cần tùy chọn hay sửa mạng" ở 5:774 mâu thuẫn với chính Bảng 3.0 (5:89).
- Vì sao quan trọng: Định nghĩa baseline quyết định cách đọc mọi phép so sánh "B1 khác SUMO mặc định ở đâu". Khoảng trống nghiên cứu ở dòng 1 của Bảng 2.2 bị số liệu của chính luận văn bác một phần.
- Đề xuất sửa: Đổi định nghĩa B0 ở Bảng 3.4 thành: "vType mặc định của SUMO, không có luật TraCI, chạy trên cùng mạng có bản vá và cùng nhu cầu (gồm lớp xe vi phạm) như mọi phương án." Ở Ch1:16 và Bảng 2.2, đổi "dừng chờ giữa nút" thành "dừng chờ giữa nút khi rẽ trái trái phép (cần bản vá mạng cho lớp vi phạm)", hoặc bỏ hành vi này khỏi danh sách những gì SUMO không làm được. Ở 5:774, bỏ "Không cần tùy chọn hay sửa mạng".

### [LG-04] "Một bộ luật không thể 'khớp' dữ liệu nhờ va chạm" mâu thuẫn với tiêu chí và quy tắc dự phòng
- Mức: nghiêm trọng
- Vị trí: Chapter/1_Introduction.tex:67 ↔ Chapter/4_Rule_execution.tex:112, Chapter/5_Experiments.tex:532, 922, 944, 984 (PDF tr. 3 bản build chưa có câu này ↔ tr. 25, 44, 62, 63)
- Trích: "các giới hạn an toàn nằm ở một chỗ ... nên một bộ luật không thể 'khớp' dữ liệu nhờ va chạm" / "Ngưỡng 142 va chạm trong nút/h gần như không loại lần chạy nào" / "khi đó mức trần va chạm không áp dụng" / "`B2_t010` ... va chạm trên làn cao nhất chiến dịch (46,0/h)"
- Vấn đề: Tiêu chí đủ điều kiện cho phép tới 142 va chạm trong nút mỗi giờ và 1 va chạm liên quan can thiệp. Khi không có đặc tả nào đủ điều kiện, quy tắc dự phòng bỏ mức trần va chạm. Trong thực tế đặc tả "tốt nhất" đã được chọn với 46,0 và 51,3 va chạm trên làn mỗi giờ (5:944, 984).
- Vì sao quan trọng: Đây là lý do thứ hai biện minh cho kiến trúc tách sinh và thực thi luật. Số liệu của Chương 5 bác nó trực tiếp.
- Đề xuất sửa: "... nên mọi bộ luật chịu cùng một tiêu chí va chạm; tiêu chí này loại phần lớn các bộ luật dựa vào va chạm, nhưng quy tắc chọn dự phòng hiện chưa áp mức trần va chạm (Mục ...)."

### [LG-05] P1 "không thể" đủ điều kiện: kết luận logic vượt quá bằng chứng
- Mức: nên sửa
- Vị trí: Chapter/6_Conclusions.tex:39, 51, Chapter/5_Experiments.tex:1176, 1235 ↔ Chapter/Appendix_A.tex:9, Chapter/5_Experiments.tex:1228 (PDF tr. 97, 72, 74 ↔ tr. 103, 73)
- Trích: "P1 không thể đủ điều kiện vì giữ cấu trúc B1" / "P1 không thể cho đặc tả đủ điều kiện dù LLM chọn tham số thế nào" / "`accel` có miền [0,8; 6,0] m/s²"
- Vấn đề: Ở P1, LLM được đổi `accel`, `tau`, tỷ trọng và xác suất luật trong miền cho phép. Lập luận "B1 có xe chờ chèn nên mọi tham số trên cấu trúc B1 đều thất bại" không suy ra được từ một điểm B1 duy nhất. Bằng chứng hiện có (12 thử nghiệm B2 và 6 biến thể loại bỏ, mỗi biến thể 3 seed) chỉ là gợi ý.
- Vì sao quan trọng: Câu này biến một hạn chế của ngân sách tìm kiếm thành một bất khả về cấu trúc, và gạt P1 ra khỏi E1 trước khi có đánh giá.
- Đề xuất sửa: "Trong 12 thử nghiệm B2 và 12 đặc tả P1 trên cấu trúc B1, không đặc tả nào hết xe chờ chèn ở PROXY_D1; biến thể B1 với `accel` mặc định vẫn còn 10–126 xe. Điều này gợi ý cấu trúc B1 khó đủ điều kiện ở PROXY_D1, chưa chứng minh là không thể."

### [LG-06] Ngưỡng va chạm "suy từ B0 trên cùng mạng" nhưng thực tế mang từ mạng F2 sang hai mạng khác
- Mức: nên sửa
- Vị trí: Chapter/4_Rule_execution.tex:114 ↔ Chapter/5_Experiments.tex:532, 1017, 1319; Chapter/0_3_Abstract.tex:15 (PDF tr. 25 ↔ tr. 44, 66, 77)
- Trích: "Hai ngưỡng va chạm được suy từ mô hình mặc định trên cùng mạng và đóng băng trước vòng hiệu chỉnh đầu tiên." / "chúng chưa được tính lại trên mạng 29/10, nơi chính B0 vượt ngưỡng va chạm trên làn" / "Trên mạng hiện tại, SUMO mặc định đủ điều kiện ở 15/15 lần chạy"
- Vấn đề: Ngưỡng tính từ B0 trên mạng F2 được dùng nguyên cho mạng 29/10 và 04/11. Khi B0 "đủ điều kiện 15/15" trên mạng 04/11, điều đó một phần là do cách dựng ngưỡng: ngưỡng lấy từ chính B0, nên kết quả này không phải bằng chứng về độ hợp lý của B0. Tóm tắt lại trình bày nó như một kết quả, đặt cạnh "còn bộ luật thủ công thì chưa".
- Vì sao quan trọng: Người đọc Tóm tắt sẽ hiểu rằng SUMO mặc định "tốt hơn" B1. Thực ra phép so sánh dùng một thước đo được hiệu chỉnh theo B0.
- Đề xuất sửa: Ở Ch4:114 viết: "suy từ mô hình mặc định trên mạng tham chiếu và đóng băng; trên SUMO, ngưỡng tính trên mạng F2 và chưa tính lại cho các mạng sau (Mục ...)". Ở Tóm tắt, thêm mệnh đề: "với ngưỡng va chạm suy từ chính SUMO mặc định".

### [LG-07] Khung giờ trong Tóm tắt và Kết luận là 07:30–09:00, nhưng mọi kết quả chỉ phủ 07:30–08:00
- Mức: nên sửa
- Vị trí: Chapter/0_3_Abstract.tex:11, Chapter/6_Conclusions.tex:15 ↔ Chapter/5_Experiments.tex:514, 530, 856 (PDF tr. 3, 95 ↔ tr. 43–44, 59)
- Trích: "trong cao điểm sáng 07:30–09:00" / "vòng hiệu chỉnh và đánh giá dùng 1800 s đầu (07:30–08:00)" / "Kết quả mục này ... chỉ phủ nửa giờ đầu của khung cao điểm"
- Vấn đề: Các chỉ số tính trên cửa sổ [300, 1800) s, tức 07:35–08:00. Tóm tắt, Chương 1 và Chương 6 không nhắc điều này.
- Vì sao quan trọng: Nửa giờ đầu là pha hàng chờ đang hình thành. Kết luận về xe chờ chèn và khóa nút có thể khác ở 08:00–09:00.
- Đề xuất sửa: Ở Tóm tắt và 6:41 thêm: "Mọi kết quả tính trên 30 phút đầu (07:30–08:00, bỏ 5 phút khởi động)."

### [LG-08] Chương 6 thiếu nhiều giới hạn đã được nêu rải rác trong Chương 5
- Mức: nên sửa
- Vị trí: Chapter/6_Conclusions.tex:41, 45 ↔ Chapter/5_Experiments.tex:948, 854, 1365, 894; Chapter/1_Introduction.tex:84 (PDF tr. 97 ↔ tr. 62, 58, 81, 61)
- Trích: "các khóa có mục tiêu giả định chiếm hơn một nửa giá trị $S$ ở mọi đặc tả" / "G0 ở đây không chứng minh độ thực tế" / "sàn nhiễu giữa các ngày suy từ hệ số biến thiên giả định" / "sức chứa hai vùng chờ Hoàng Đạo Thúy chưa đo" / "Khung giờ thấp điểm chưa được thực nghiệm."
- Vấn đề: Mục "Chưa thực hiện" chỉ nêu hai giới hạn: chưa có video và còn giá trị tạm thời. Các giới hạn sau không được gom vào: $S_{\text{assumed}}$ chiếm hơn nửa $S$; G0 (cổng lọc GEH) cao là do cấu tạo; sàn nhiễu giả định; chỉ một nút và một khung giờ, chưa có thấp điểm; hành vi 8 bị hoãn; ngưỡng va chạm không tính lại (LG-06); hành vi 9 và 11 không có chỉ số (LG-09).
- Vì sao quan trọng: Hội đồng đọc Chương Kết luận để biết phạm vi hiệu lực của kết quả. Một giới hạn chỉ nằm trong Chương 5 dày 1400 dòng thì coi như không được nêu.
- Đề xuất sửa: Thêm một mục "Giới hạn" vào Chương 6, liệt kê từng ý trên trong một câu, kèm tham chiếu mục.

### [LG-09] Hành vi 9 và 11 không có chỉ số, nhưng tham số của chúng vẫn được chỉnh; mâu thuẫn với quy tắc cố định tham số
- Mức: nên sửa
- Vị trí: Chapter/4_Rule_execution.tex:97 ↔ Chapter/3_Rule_generation.tex:183, 87; Chapter/5_Experiments.tex:192, 200 (PDF tr. 23 ↔ tr. 16–17, 33, 86–94)
- Trích: "M2 đo xuất phát sớm (hành vi 3); M3 ... (hành vi 1, 2); M4 và M5 ... (hành vi 4); M7 ... (hành vi 10); M8, M9, M10 ... (hành vi 5, 6, 7)" / "Tham số không chỉ số nào ràng buộc được cố định ở giá trị mặc định" / "`slow_lane_center` ... $\delta \in [-1,1]$ m" / v005: "`illegal_left_box` và `slow_lane_center` ... chỉ cần có mặt"
- Vấn đề: Không chỉ số nào đo hành vi 9 (chấp nhận khoảng trống nhỏ) hay hành vi 11 (xe máy đi chậm giữa làn). M7b (độ trễ giải phóng vùng chờ, đại diện cho PET) được gán cho hành vi 10, trong khi Ch3:87 lại nói PET là đại lượng đo của nhóm hành vi từ tài liệu. Theo đúng quy tắc của Ch3:183, $\delta$ phải được cố định. Thế nhưng nó có miền tìm kiếm, và `v005` còn bắt buộc phải có luật này.
- Vì sao quan trọng: Quy tắc "chỉ chỉnh tham số có chỉ số ràng buộc" là lập luận chính để giữ không gian tìm kiếm nhỏ và có nghĩa, và nó bị vi phạm ngay trong luật của luận văn.
- Đề xuất sửa: Ở Ch4:97 thêm một câu: "Hành vi 9 và 11 chưa có chỉ số riêng." Sau đó chọn một trong hai: cố định $\delta$ hoặc nêu ngoại lệ kèm lý do, và gỡ yêu cầu `slow_lane_center` khỏi kiểm tra `coverage` (hoặc giải thích vì sao vẫn giữ).

### [LG-10] Mục tiêu M2 (xuất phát sớm) lấy từ một định nghĩa khác; một số giá trị mục tiêu gắn trích dẫn nhưng không suy ra được từ nguồn
- Mức: nên sửa
- Vị trí: Chapter/4_Rule_execution.tex:85 ↔ Chapter/2_Literature_review.tex:23, Chapter/1_Introduction.tex:18; Chapter/5_Experiments.tex:416–421 (PDF tr. 24 ↔ tr. 6, 1, 41–42)
- Trích: M2: "Tỷ lệ xe qua vạch trong 10 s cuối pha đỏ" / Mai và cs.: "xuất phát sớm (từ khoảng 5 s trở lên trước đèn xanh) 15,82% và 13,55%" / Bảng 3.targets: "M2 ... xe máy LVL; HDT 0,0945; 0,1582 — CG [mai2019signal]"; "M3 ... LVL 0,0649"; "M1 ... 0,254 — CG [vu2015saturation]"
- Vấn đề: M2 đếm xe qua vạch trong 0–10 s trước đèn xanh. Số của Mai đếm xe qua vạch từ khoảng 5 s trở lên trước đèn xanh. Hai đại lượng khác nhau, vậy mà giá trị 0,1582 được chép thẳng. Các giá trị cho Lê Văn Lương (0,0945; 0,0649; 0,0027) không có trong Mai và không có câu nào giải thích cách suy ra. Giá trị 0,254 s cho M1 không nằm trong số liệu của Vu và Nguyen được trích ở Bảng 2.1.
- Vì sao quan trọng: Đây vẫn là giá trị tạm thời, nhưng nhãn "chuyển giao từ tài liệu" kèm trích dẫn khiến người đọc tin rằng con số có nguồn. Chính luận văn đã phải thêm nhãn `literature_transferred` (5:1353) để tránh kiểu nói quá này.
- Đề xuất sửa: Thêm một câu dưới Bảng 3.targets nêu cách chuyển định nghĩa (5 s so với 10 s) và cách suy ra giá trị cho nhánh LVL. Với 0,254 s, ghi rõ phép tính hoặc đổi nhãn thành giả định.

### [LG-11] Tham chiếu chéo trỏ sai mục
- Mức: nên sửa
- Vị trí: Chapter/5_Experiments.tex:91, 1042, 1092, 1118 (`section:3.3`); 5:922, 5:1315 (`section:3.8`); Chapter/2_Literature_review.tex:95 (`section:1.2`) (PDF tr. 86, 66, 68, 69; tr. 62, 77; tr. 10)
- Trích: "Ngày 04/11/2026 cách thứ hai được chọn (Mục 3.4)" / "lựa chọn cắt về của luật `queue_space_seeking` (Mục 3.4)" / "đặc tả tốt nhất được chọn theo số teleport kẹt ... (Mục~\ref{section:3.8})" / "với 11 hành vi (Mục~\ref{section:1.2})"
- Vấn đề: `section:3.3` là "Biểu diễn luật" ở Chương 3, mục này không nói gì về điều kiện nút thông hay lựa chọn cắt về. Nội dung đó nằm ở phần "Luật có điều kiện" của Mục 5.2 (5:172–178), vốn chưa có nhãn. `section:3.8` là "Thiết kế đánh giá", còn quy tắc dự phòng và tiêu chí đủ điều kiện nằm ở `section:ev_eligibility` và `section:ex_config`. `section:1.2` là "Mục tiêu và phạm vi", không phải danh mục hành vi.
- Vì sao quan trọng: Người đọc theo tham chiếu sẽ không tìm thấy nội dung được hứa.
- Đề xuất sửa: Gắn nhãn cho `\subsubsection{Luật có điều kiện}` (ví dụ `subsubsection:impl_rules`) rồi trỏ bốn chỗ về đó. Đổi 5:922 và 5:1315 sang `section:ev_eligibility`. Đổi 2:95 sang `table:1.1`.

### [LG-12] "Mọi lỗi là lỗi cấu trúc" không khớp với bảng lỗi
- Mức: nên sửa
- Vị trí: Chapter/5_Experiments.tex:1185, 1285; Chapter/0_3_Abstract.tex:15; Chapter/6_Conclusions.tex:33 ↔ Chapter/5_Experiments.tex:1183, 1195, 1200 (PDF tr. 72, 76, 96 ↔ tr. 72–73)
- Trích: "Mọi lỗi trong bảng là lỗi cấu trúc" / "LLM cục bộ mắc chủ yếu lỗi cấu trúc" ↔ "Tổng tỷ trọng của một phân phối khác 1: 15"; "Giá trị ngoài miền (lược đồ): 4"; P1: "14/15 lần thử hỏng là lỗi tổng tỷ trọng"
- Vấn đề: Tổng tỷ trọng khác 1 và giá trị ngoài miền là lỗi giá trị. Ở P1 (chế độ chỉ tham số), 14/15 lần thử hỏng là lỗi giá trị, không phải lỗi cấu trúc. Tóm tắt khái quát cho cả hai chiến dịch.
- Vì sao quan trọng: Nhận định về loại lỗi của LLM là một trong hai phát hiện về `qwen3.5:9b` được nêu trong Tóm tắt.
- Đề xuất sửa: "P2 mắc chủ yếu lỗi cấu trúc (mã nguyên mẫu trùng tên phân phối); P1 mắc chủ yếu lỗi tổng tỷ trọng ở phân phối một nguyên mẫu. Bộ kiểm tra hợp lệ bắt mọi lỗi này trước khi chạy."

### [LG-13] Chương 1 khẳng định những điều Chương 5 chưa cho thấy
- Mức: nên sửa
- Vị trí: Chapter/1_Introduction.tex:11, 65 ↔ Chapter/5_Experiments.tex:1173, 1185; Chapter/6_Conclusions.tex:45 (PDF tr. 1, 3 ↔ tr. 71–72, 97)
- Trích: "Bộ luật thu được là một tệp văn bản, dùng lại được cho cả ba nhóm người dùng trên." / "đây là phần cần hiểu biết về hành vi người lái, thứ LLM có thể đề xuất còn bộ tối ưu số thì không" ↔ "Từ vòng 2, cả 12 đặc tả P2 được chạy có cùng cấu trúc với `it02_s01` ... Các vòng sau chỉ đổi tỷ trọng và tham số."
- Vấn đề: Luận văn chưa có bộ luật nào đủ điều kiện, nên chưa "thu được" bộ luật để dùng lại. Năng lực đề xuất cấu trúc của LLM được nêu như sự thật. Thực tế P2 khóa vào một cấu trúc ngay từ vòng 2 và bỏ ba loại luật, và Chương 6 không quay lại đối chiếu giả thuyết này với kết quả đó.
- Vì sao quan trọng: Phần động lực đặt kỳ vọng mà phần kết quả không đáp ứng, và không có chỗ nào nối hai phần lại.
- Đề xuất sửa: Ở 1:11 viết "Bộ luật mục tiêu là một tệp văn bản ...". Ở 1:65 viết "... và đây là phần luận văn giả thuyết LLM có thể đề xuất ...". Ở Chương 6, thêm một câu đối chiếu giả thuyết này với hành vi quan sát được của P2.

### [LG-14] Tóm tắt Chương 5 dùng sức chứa vùng chờ của mạng cũ
- Mức: nên sửa
- Vị trí: Chapter/5_Experiments.tex:1437 ↔ Chapter/5_Experiments.tex:795, 801, 894, 1340 (PDF tr. 85 ↔ tr. 55, 61, 79)
- Trích: "Các thí nghiệm khả thi xác nhận SUMO tự mô phỏng được xe chờ giữa nút với sức chứa 8 xe" ↔ "Số xe dừng lớn nhất là 13, 8, 8, 7 và 10 theo seed 1–5" (vùng chờ 3,5 m) / "sức chứa hai vùng chờ Hoàng Đạo Thúy chưa đo"
- Vấn đề: Con số 8 đo trên vùng chờ 3,2 m của mạng đã bỏ. Trên vùng chờ 3,5 m, kết quả dao động 7–13 tùy seed. Thêm nữa, hành vi 10 hiện diễn ra ở hai nhánh Hoàng Đạo Thúy, nơi sức chứa chưa được đo.
- Vì sao quan trọng: Câu tóm tắt khẳng định một kết quả không còn áp dụng cho mạng đang dùng.
- Đề xuất sửa: "Thí nghiệm khả thi trên nhánh Lê Văn Lương phía tây cho thấy cơ chế sẵn có của SUMO chứa được 7–13 xe chờ (vùng chờ 3,5 m, 5 seed); sức chứa hai vùng chờ Hoàng Đạo Thúy đang dùng chưa đo."

### [LG-15] Không nêu nguồn của "chiến dịch P2 trên mạng 28/10" và phần chạy trên máy phụ
- Mức: nên sửa
- Vị trí: Chapter/5_Experiments.tex:1130, 1135 ↔ Chapter/5_Experiments.tex:959, 928, 1425 (PDF tr. 70 ↔ tr. 63, 62, 84)
- Trích: "dựng lại từ chiến dịch P2 trên mạng 28/10, prompt vòng 3 khoảng 46.300 token" ↔ "P1 và P2 với `qwen3.5:9b` chưa có kết quả chính thức nên không có mặt" / "Một máy Linux phụ chạy bổ sung một phần chiến dịch"
- Vấn đề: Luận văn dùng sản phẩm của một chiến dịch P2 trên mạng 28/10 (đặc tả và phản hồi các vòng, để tính kích thước prompt). Ở chỗ khác lại nói P2 với `qwen3.5:9b` trên mạng này chưa có kết quả. Người đọc không biết chiến dịch đó do LLM nào sinh. Câu về máy phụ không nói phần nào của chiến dịch đã chạy ở đó và có gọi LLM hay không.
- Vì sao quan trọng: Chỉ kết quả của `qwen3.5:9b` mới là kết quả của phương pháp. Hiện số liệu được dùng chỉ là kích thước prompt, nhưng việc không nêu nguồn mở đường cho hiểu nhầm. Nếu sau này có số nào từ chiến dịch đó lọt vào phần kết quả thì lỗi trở thành nghiêm trọng.
- Đề xuất sửa: Ghi rõ mô hình đã sinh chiến dịch P2 trên mạng 28/10. Nếu đó không phải `qwen3.5:9b`, nói rõ chiến dịch chỉ dùng để đo kích thước prompt, không phải kết quả. Ở 5:1425, nói rõ máy phụ chỉ chạy SUMO (nếu đúng) và liệt kê các lần chạy nào đã chạy ở đó.

### [LG-16] Các chỉ số đã định nghĩa nhưng không được báo cáo
- Mức: nên sửa
- Vị trí: Chapter/4_Rule_execution.tex:105, 107; Chapter/3_Rule_generation.tex:87; Chapter/5_Experiments.tex:1336 ↔ Chapter/5_Experiments.tex:684–693, 1008, 1167 (PDF tr. 25, 78 ↔ tr. 50, 65, 71)
- Trích: "Mỗi chỉ số được báo cáo bằng tỷ số $R = d_{\text{sim-obs}}/d_{\text{day-day}}$" / "khi tính điểm tổng, phần sai lệch của các hành vi này được báo cáo tách riêng" / "M7c sẽ không đạt và điều này sẽ được báo cáo"
- Vấn đề: Không bảng kết quả nào báo cáo $R$. $S_{\text{sourced}}$ và $S_{\text{assumed}}$ chỉ xuất hiện ở Bảng 4.ref_n29 và phụ lục, không có ở các bảng chiến dịch trên mạng 04/11. M1 (khoảng xả hàng), M5 (hàng chờ và mật độ), M6 (thời gian qua nút), M7b (độ trễ giải phóng vùng chờ) và M7c (độ dốc tổn thất khởi động) không có giá trị nào cho bất kỳ cấu hình nào. M8 (đi sai làn) theo định nghĩa mới chưa được tính lần nào (5:675, 1125).
- Vì sao quan trọng: Người đọc không kiểm tra được $S$ đến từ đâu. Điều Chương 3 hứa (báo cáo tách riêng phần giả định) không được giữ ở chính các chiến dịch chính.
- Đề xuất sửa: Thêm cột $S_{\text{sourced}}$/$S_{\text{assumed}}$ vào Bảng 4.campaigns_n1108 và 4.ref_n1104. Thêm một bảng $R$ theo nhóm chỉ số cho B0 và B1 trên mạng 04/11. Nếu không làm, sửa Ch4:105 thành "phản hồi cho LLM dùng $R$".

### [LG-17] $S$ ghi tới 4 chữ số và đặt cạnh nhau dù chênh lệch nhỏ và không so được
- Mức: nhỏ
- Vị trí: Chapter/6_Conclusions.tex:37, 39 ↔ Chapter/5_Experiments.tex:1176, 1365 (PDF tr. 96–97 ↔ tr. 72, 81)
- Trích: "B0 đủ điều kiện ở 15/15 lần với $S = 1{,}2174$ ... $S$ nhỏ nhất là 1,1438 với B2, 1,2386 với P1 và 1,1680 với P2" ↔ "$S$ ở Bảng 4.campaigns_n1108 không so trực tiếp được với $S$ của B0 và B1 trên 5 seed" / "tỷ số khoảng cách trên sàn nhiễu chỉ mang tính minh họa"
- Vấn đề: Chương 6 đặt $S$ của B0 (5 seed) ngay trước $S$ của các chiến dịch (1 seed) trong cùng đoạn, điều mà Chương 5 nói là không được làm. Chênh lệch chỉ 0,01–0,08, không có sai số, và sàn nhiễu là giả định.
- Vì sao quan trọng: Người đọc lướt sẽ so 1,1438 với 1,2174 và kết luận B2 tốt hơn B0.
- Đề xuất sửa: Tách hai câu, thêm "(không so trực tiếp được: 1 seed so với 5 seed)", và làm tròn $S$ tới 2 chữ số ở Chương 6.

### [LG-18] "Mười trong 11 hành vi đã được đưa vào mô hình" dễ bị đọc là "đã được mô phỏng"
- Mức: nhỏ
- Vị trí: Chapter/0_3_Abstract.tex:15, Chapter/2_Literature_review.tex:95 ↔ Chapter/5_Experiments.tex:172, 699, 1173 (PDF tr. 3, 10 ↔ tr. 51, 71)
- Trích: "Mười trong 11 hành vi đã được đưa vào mô hình" ↔ "Trên mạng 04/11, lựa chọn `right_lane` không tồn tại" / "B1 đặt xác suất bằng 0 cho `early_start` và cho mọi lựa chọn của `queue_space_seeking`"
- Vấn đề: Mười hành vi có cơ chế trong mã. Nhưng hành vi 6 không còn lựa chọn luật nào trên mạng hiện tại, hành vi 10 đến từ bản vá mạng, B1 cho tỷ lệ bằng 0 với hành vi 3, 5, 7, và P2 bỏ các luật của hành vi 5–7 và 11. Bảng 2.2 còn ghi "với 11 hành vi".
- Vì sao quan trọng: Khoảng cách giữa "có trong mã" và "xuất hiện trong mô phỏng đã chạy" chưa được nói ra.
- Đề xuất sửa: "Mười trong 11 hành vi có cơ chế biểu diễn trong mô hình (tham số, luật TraCI hoặc bản vá mạng); hành vi đi ngược chiều được hoãn." Ở Bảng 2.2 viết "10 trong 11 hành vi".

### [LG-19] Các con số đếm nhỏ không khớp nhau
- Mức: nhỏ
- Vị trí: Chapter/Appendix_A.tex:66 ↔ Appendix_A.tex:90–94; Chapter/5_Experiments.tex:282 ↔ Chapter/1_Introduction.tex:43–48; Chapter/5_Experiments.tex:1273, 595 ↔ Chapter/4_Rule_execution.tex:83–93; Chapter/5_Experiments.tex:297 ↔ 5:204 (PDF tr. 105–107; tr. 34 ↔ tr. 3; tr. 75 ↔ tr. 24)
- Trích: "Cấu trúc của B1 (năm nguyên mẫu, ... bốn loại luật, thêm `uturn_bypass` từ ngày 04/11/2026)" ↔ bảng luật B1 có đúng bốn loại kể cả `uturn_bypass` / "Một vòng hiệu chỉnh gồm sáu bước (Hình 1.1 cho thấy năm bước đầu)" ↔ Hình 1.1 vẽ đủ sáu khối, đánh số 1–5 lệch với Bảng 2.4 / "danh sách chỉ số M1–M8 có thể ràng buộc tham số" ↔ M1–M10 / "`vtypes.add.xml` (ba phân phối kiểu xe)" ↔ "và, nếu đặc tả có nguyên mẫu riêng, `car_violator`"
- Vấn đề: Mỗi chỗ là một lệch đếm nhỏ do sửa không đồng bộ.
- Vì sao quan trọng: Người chấm đối chiếu sẽ thấy, và mất niềm tin vào các con số khác.
- Đề xuất sửa: Sửa thành "ba loại luật, thêm `uturn_bypass`" (hoặc "bốn loại luật, kể cả"); "Hình 1.1 cho thấy cả sáu bước (đánh số khác)"; "M1–M10"; "ba hoặc bốn phân phối".

### [LG-20] Trích dẫn và nguồn của bảng số liệu
- Mức: nhỏ
- Vị trí: Chapter/2_Literature_review.tex:14, 41; Chapter/5_Experiments.tex:1361 ↔ 5:422; Chapter/1_Introduction.tex:20; Chapter/3_Rule_generation.tex:57 (PDF tr. 6–7, 79 ↔ tr. 42, 2, 13)
- Trích: "Số liệu thực nghiệm về hành vi xe máy được luận văn sử dụng" (có dòng Nguyen-Phuoc về xi-nhan) / "Các giá trị có nguồn chủ yếu đến từ bốn nghiên cứu" ↔ M4 "CG [zulkiffli2023stopping]" / "Mô phỏng nút giao bằng mô hình chuẩn thì có" / "**[TODO_CITE: nguồn hoặc mô tả quan sát cho hành vi 11]**"
- Vấn đề: Số liệu xi-nhan (Nguyen-Phuoc) không được dùng ở đâu, trái với chú thích bảng. Danh sách "bốn nghiên cứu" bỏ sót Zulkiffli, nguồn của mục tiêu M4 (vị trí dừng của xe máy). Câu "mô phỏng nút giao bằng mô hình chuẩn thì có" không kèm trích dẫn. Năm hành vi "từ quan sát" (5, 6, 7, 8, 11) không có mô tả nào về cách quan sát (ngày, vị trí, cách ghi), và hành vi 11 còn TODO.
- Vì sao quan trọng: Một phần ba danh mục hành vi dựa vào "quan sát của tác giả" mà không có mô tả kiểm tra được.
- Đề xuất sửa: Bỏ dòng Nguyen-Phuoc hoặc nêu nó dùng cho việc gì. Thêm Zulkiffli vào danh sách ở 5:1361. Thêm một trích dẫn mô phỏng nút giao ở Việt Nam bằng mô hình chuẩn. Thêm một đoạn ngắn mô tả các đợt khảo sát hiện trường (ngày, nhánh, khung giờ, cách ghi nhận) làm cơ sở cho các hành vi "Quan sát".
