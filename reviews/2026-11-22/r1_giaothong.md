# Sinh viên Kỹ thuật giao thông

Ghi chú về vị trí trích dẫn. Bản PDF đã build dùng bộ chương cũ (`5_Evaluation.tex`, `6_Implementation.tex`, `7_Conclusions.tex`, theo `main.log`). Trên đĩa hiện có `3_Rule_generation.tex`, `4_Rule_execution.tex`, `5_Experiments.tex`, `6_Conclusions.tex`. Số dòng `.tex` trong file này lấy theo tệp trên đĩa. "PDF tr." là số trang in ở chân trang của bản PDF (trang PDF thứ = số in + 18). Chương 5 của PDF tương ứng `4_Rule_execution.tex` từ dòng 61. Chương 6 của PDF tương ứng `5_Experiments.tex`. Đoạn nào chỉ có trên đĩa thì chỉ ghi dòng `.tex`.

## Đánh giá tổng quát

Người trong ngành giao thông đọc luận văn này sẽ chưa hình dung được nút giao: không có sơ đồ phân làn, không có sơ đồ pha. Hình mạng lưới và hình sơ đồ lại lệch hướng nhau 45°. Phạm vi hành vi tự mâu thuẫn ở hai chỗ. Đi trên vỉa hè và đi ngược chiều nằm trong danh mục, nhưng phần phạm vi không nói gì về chúng. Hành vi 6 (chặn làn rẽ phải) được định nghĩa là lệch chuẩn, trong khi chính luận văn nói đi thẳng trên làn đó là đúng luật. Phần lớn chỉ số chưa có định nghĩa vận hành đủ để người khác đo lại từ video: đo ở đâu, ngưỡng dừng bao nhiêu, xe qua vạch lúc đèn đỏ thì tính vào M2 hay M3. Cổng GEH và chữ "va chạm" của SUMO được trình bày theo cách dễ làm người đọc hiểu sai mức độ hiệu chỉnh và mức an toàn của mô hình.

## Nhận xét

### [GT-01] Phạm vi: đi trên vỉa hè và đi ngược chiều không được tuyên bố ngoài phạm vi, mà lại nằm trong mô hình
- Mức: nghiêm trọng
- Vị trí: Chapter/1_Introduction.tex:82 (PDF tr. 4, Mục 1.4.2); Chapter/3_Rule_generation.tex:75-76 (PDF tr. 13, Bảng 3.1); Chapter/5_Experiments.tex:23, 888 (PDF tr. 28, 60); Chapter/4_Rule_execution.tex:93 (PDF tr. 24, Bảng 5.1); Chapter/0_3_Abstract.tex:9, 15
- Trích: "Người đi bộ, xe buýt, xe tải, ô tô đỗ dưới lòng đường và việc chọn lộ trình không được mô hình hóa ... các không gian chỉ xe vi phạm được dùng (ví dụ vỉa hè) là bản vá tĩnh của mạng." / "7 & ... Xe máy đi trên vỉa hè để vượt hàng chờ" / "8 & ... Đi ngược chiều ở đoạn không có dải phân cách" / "Hành vi 8 được *hoãn* ... nằm trong phần hạn chế" / Tóm tắt: "Mười trong 11 hành vi đã được đưa vào mô hình; hành vi đi ngược chiều được hoãn"
- Vấn đề: Danh sách ngoài phạm vi ở Mục 1.4.2 và Mục 6.1.1 không có đi trên vỉa hè và đi ngược chiều. Ngược lại, vỉa hè được mô hình hóa đầy đủ: hành vi 7, làn vỉa hè 170 m, lựa chọn `sidewalk`, chỉ số M10 (đi trên vỉa hè). Đi ngược chiều thì được gọi là "hoãn", tức một hạng mục còn dang dở, không phải một lựa chọn phạm vi. Tóm tắt còn liệt kê "đi trên vỉa hè khi ùn" là hành vi được tái hiện.
- Vì sao quan trọng: Hội đồng sẽ hỏi vì sao không mô hình hóa đi ngược chiều, và sẽ chấm nó là việc chưa làm xong. Nếu đề tài đã chốt hai hành vi này nằm ngoài phạm vi thì bản thảo đang trình bày ngược với quyết định đó.
- Đề xuất sửa: Cần tác giả kiểm tra lại quyết định phạm vi. Nếu hai hành vi này nằm ngoài phạm vi: thêm chúng vào câu ngoài phạm vi ở Mục 1.4.2 và 6.1.1, kèm một câu lý do; bỏ hành vi 7, 8 khỏi Bảng 3.1 (hoặc tách thành bảng "ngoài phạm vi"); bỏ M10 (đi trên vỉa hè) và lựa chọn `sidewalk`, hoặc ghi rõ chúng không tính vào điểm; đổi chữ "hoãn" thành "ngoài phạm vi"; sửa Tóm tắt và Abstract. Nếu giữ vỉa hè trong mô hình thì phải bỏ nó khỏi mọi câu nói về phạm vi loại trừ và nói rõ chỉ đi ngược chiều bị loại.

### [GT-02] Hành vi 6 (chặn làn rẽ phải) định nghĩa một hành vi đúng luật là lệch chuẩn; mô tả làn tự mâu thuẫn
- Mức: nghiêm trọng
- Vị trí: Chapter/5_Experiments.tex:23 (PDF tr. 28-29); 91, 93 (PDF tr. 86, Bảng 6.1); 108 (PDF tr. 30-31); 172 (PDF tr. 32); 429-430 (PDF tr. 92, Bảng 6.10); Chapter/4_Rule_execution.tex:92 (PDF tr. 24)
- Trích: "Hành vi 6 là việc xe có hướng đi thẳng, rẽ trái hoặc quay đầu đứng chờ đèn đỏ của chính nó trên lane 0 trong 30 m cuối trước vạch dừng. Đi thẳng hoặc rẽ trái trên làn này khi đèn xanh là đúng luật." / "lane 0 là làn rẽ phải liên tục ..., trong đó rẽ phải không theo đèn và đi thẳng theo đèn đi thẳng" / Bảng 6.1: "Rẽ trái và quay đầu chỉ có kết nối từ lane 2" / Bảng 6.10: "Xác suất xe đi thẳng chọn lane 0"
- Vấn đề: (1) Nếu lane 0 cho đi thẳng theo đèn thì xe đi thẳng phải đứng chờ đỏ trên chính làn đó. Đây là hành vi đúng luật, không phải "tìm khoảng trống khi ùn". (2) Câu "rẽ trái trên làn này khi đèn xanh là đúng luật" mâu thuẫn với Bảng 6.1 và dòng 108, nơi rẽ trái chỉ đi từ lane 2. (3) Mục tiêu M9 (chặn làn rẽ phải) là "xác suất xe đi thẳng chọn lane 0", tức đo việc chọn một làn hợp lệ. Dòng 172 cũng thừa nhận hành vi này "đến từ cách SUMO chọn làn và từ hàng chờ".
- Vì sao quan trọng: Người làm tổ chức giao thông sẽ coi đây là tương tác giữa dòng đi thẳng và dòng rẽ phải trên làn dùng chung, không phải vi phạm. Gọi nó là hành vi lệch chuẩn làm sai bản chất của M9 (chặn làn rẽ phải) và của nhóm F2.
- Đề xuất sửa: Cần tác giả kiểm tra lại vạch sơn và biển báo tại nút: lane 0 trong 30 m cuối có cho đi thẳng không, có cho rẽ trái không. Nếu cho đi thẳng: định nghĩa lại hành vi 6 thành hiện tượng "xe đi thẳng chờ đèn đỏ trên làn dùng chung làm chặn dòng rẽ phải liên tục", tách khỏi nhóm hành vi vi phạm, và sửa câu ở dòng 23. Nếu không cho đi thẳng: sửa dòng 108 và Bảng 6.1 cho khớp. Thống nhất một mô tả phân làn duy nhất cho cả chương.

### [GT-03] Không có sơ đồ phân làn và sơ đồ pha; bảng mô tả bản vá trôi xa phần nói về nó
- Mức: nghiêm trọng
- Vị trí: Chapter/5_Experiments.tex:108-112 (PDF tr. 30-31, Mục 6.1.3); Hình 6.1 (5_Experiments.tex:29-33, PDF tr. 29); Hình 6.2 (5_Experiments.tex:38-77, PDF tr. 30); Bảng 6.1 (5_Experiments.tex:80-98, in ở PDF tr. 86)
- Trích: "Mỗi nhánh có ba làn ... Lane 1 đi thẳng; lane 2 đi thẳng và quay đầu, thêm rẽ trái ở hai nhánh Lê Văn Lương." / "đèn có ba pha: Lê Văn Lương đi thẳng; mũi tên rẽ trái và quay đầu của Lê Văn Lương (hai nhánh cùng lúc, đi thẳng đỏ); và Hoàng Đạo Thúy" / "Các trạng thái của chu kỳ là 42/4/2/16/4/2/44/4/2 s."
- Vấn đề: Toàn bộ thông tin phân làn, hướng cấm và tổ chức pha chỉ có trong văn xuôi. Hình 6.1 chỉ có trục cạnh và mã OSM ("953158817#2.up out to NW"), không có làn, vạch dừng hay mũi tên hướng đi. Hình 6.2 không vẽ ba làn, không vẽ mũi tên chỉ hướng của từng làn, không vẽ biển cấm rẽ trái ở Hoàng Đạo Thúy, không vẽ hướng rẽ trái và quay đầu có mũi tên riêng của Lê Văn Lương. Hình chỉ có một vạch dừng ở nhánh tây. Không có sơ đồ pha. Bảng 6.1 (bốn bản vá mạng) được nhắc ở tr. 29 nhưng in ở tr. 86. Các Bảng 6.2-6.7 và 6.10 cũng trôi về tr. 87-92.
- Vì sao quan trọng: Người chưa đến nút giao không dựng lại được nút từ phần trình bày. Họ cũng không kiểm tra được các lập luận phía sau dựa trên hình học: xe đi sai làn, chặn làn rẽ phải, vùng chờ giữa nút.
- Đề xuất sửa: Thêm (a) sơ đồ mặt bằng phân làn cho bốn nhánh: số làn, mũi tên hướng đi trên từng làn, đoạn 30 m của làn rẽ phải liên tục, vạch dừng, hướng cấm rẽ, có kim chỉ Bắc và tên đường trên từng nhánh; (b) sơ đồ pha dạng thông thường: mỗi pha một ô, mũi tên các dòng được đi, kèm biểu đồ thời gian xanh, vàng, đỏ toàn phần trong chu kỳ 120 s. Ghi giá trị tạm thời bằng màu đỏ như quy ước. Đặt `[H]` hoặc `\FloatBarrier` để Bảng 6.1 nằm cạnh Mục 6.1.2.

### [GT-04] M2 (xuất phát sớm) và M3 (vượt đèn đỏ) chồng lấn nhau và lệch định nghĩa của nguồn
- Mức: nghiêm trọng
- Vị trí: Chapter/4_Rule_execution.tex:85-86 (PDF tr. 24, Bảng 5.1); Chapter/2_Literature_review.tex:23 (PDF tr. 6); Chapter/5_Experiments.tex:188 (PDF tr. 88, Bảng 6.4), 417, 420 (PDF tr. 92); Chapter/Appendix_B.tex:17-18, 29 (PDF tr. 109)
- Trích: M2: "Tỷ lệ xe qua vạch trong 10 s cuối pha đỏ" / M3: "Số xe vượt đỏ mỗi chu kỳ ... tỷ lệ vượt đỏ" / Nguồn Mai và cs.: "xuất phát sớm (từ khoảng 5 s trở lên trước đèn xanh)"
- Vấn đề: (1) Một xe qua vạch trong 10 s cuối của đèn đỏ thỏa cả định nghĩa M2 lẫn M3 (qua vạch khi `signal_state_at_t` = `r`). Luận văn không nói lượt đó được tính vào chỉ số nào. (2) Mục tiêu M2 lấy từ Mai và cs., nơi xuất phát sớm là qua vạch từ khoảng 5 s trở lên trước đèn xanh. Còn chỉ số đếm mọi xe trong cửa sổ 10 s. Xe sớm 0-5 s bị đếm thêm, xe sớm hơn 10 s bị bỏ. (3) Chưa nói xe qua vạch lúc đèn vàng và lúc đỏ toàn phần được xếp vào đâu. Ở Việt Nam, đi khi đèn vàng mà không kịp dừng là hợp lệ. Phụ lục B có tách trạng thái `y`, nhưng chương chỉ số không nhắc.
- Vì sao quan trọng: Vượt đèn đỏ và xuất phát sớm là hai hành vi chính của nhóm không tuân thủ tín hiệu. Nếu định nghĩa chồng lấn và lệch nguồn, so sánh mô phỏng với số của Mai không còn cùng một đại lượng.
- Đề xuất sửa: Định nghĩa loại trừ nhau, ví dụ: "vượt đèn đỏ: qua vạch dừng khi đèn của luồng đó đỏ, từ đầu thời gian đỏ đến trước $T$ giây cuối; xuất phát sớm: qua vạch trong $T$ giây cuối của thời gian đỏ"; chọn $T$ khớp nguồn (5 s), hoặc ghi rõ vì sao dùng 10 s. Nói rõ cách xử lý vàng và đỏ toàn phần. Dùng "thời gian đỏ" thay cho "pha đỏ".

### [GT-05] Cổng GEH áp lên số đếm 15 phút theo từng loại xe: dễ hiểu là đã đạt tiêu chuẩn TAG
- Mức: nghiêm trọng
- Vị trí: Chapter/4_Rule_execution.tex:83 (PDF tr. 24, Bảng 5.1); Chapter/2_Literature_review.tex:71 (PDF tr. 8); Chapter/5_Experiments.tex:514 (PDF tr. 43), 829 (PDF tr. 57)
- Trích: "GEH ... của số đếm rẽ theo ô 15 phút × nhánh × hướng × loại phương tiện ... Lần chạy đạt khi tỷ lệ ô có GEH < 5 không nhỏ hơn 0,85 [TAG]" / "tính trên 62 ô theo 15 phút × nhánh × hướng × loại xe"
- Vấn đề: Ngưỡng GEH < 5 của TAG M3.1 dùng cho lưu lượng giờ (xe/h). GEH tăng theo căn bậc hai của độ lớn số đếm. Tính trên số đếm 15 phút cho giá trị bằng một nửa so với khi quy về xe/h, nên "GEH < 5" ở đây tương đương khoảng GEH < 10 theo lưu lượng giờ. Tách thêm theo loại xe và hướng tạo nhiều ô chỉ có vài xe (ví dụ ô tô quay đầu), và các ô này gần như luôn đạt. Ngoài ra G0 tính trên 0-1800 s, gồm cả 300 s khởi động mà các chỉ số khác bỏ qua.
- Vì sao quan trọng: Người làm giao thông đọc "GEH < 5 ở ≥ 85% ô [TAG]" sẽ hiểu mô hình đạt chuẩn hiệu chỉnh lưu lượng của Anh. Thực tế tiêu chí lỏng hơn nhiều. Mục 6.11.4 có thừa nhận G0 "không chứng minh độ thực tế" trên dữ liệu đại diện, nhưng không nói đến lệch đơn vị.
- Đề xuất sửa: Quy số đếm 15 phút về lưu lượng giờ tương đương (×4) trước khi tính GEH, hoặc ghi rõ đây là biến thể chặt/lỏng khác TAG và không gọi là tiêu chí TAG. Báo cáo thêm GEH ở mức nhánh × hướng theo giờ. Nói rõ cửa sổ thời gian của G0 có gồm khởi động hay không.

### [GT-06] "Va chạm", "teleport" và "xe chờ chèn" của SUMO chưa được giải thích theo nghĩa giao thông
- Mức: nghiêm trọng
- Vị trí: Chapter/5_Experiments.tex:532 (PDF tr. 44), 738 (PDF tr. 52), 920-922 (PDF tr. 61-62), 1004 (PDF tr. 65)
- Trích: "Hai ngưỡng va chạm là 4 va chạm trên làn/h và 142 va chạm trong nút/h" / "va chạm trong nút nằm trong 82-156" / "nó chủ yếu ghi nhận rằng va chạm trong nút của mô hình làn con rất phổ biến ngay ở cấu hình mặc định"
- Vấn đề: Luận văn không nói "va chạm" trong SUMO là gì: chồng lấn hình học hoặc khoảng hở âm giữa hai xe, phát hiện bằng `collision.check-junctions`, sau đó xe bị xử lý theo `collision.action`. Người đọc ngành giao thông hiểu "va chạm" là tai nạn, và 82-156 va chạm/h ở một nút là con số phi lý. "Teleport" có định nghĩa ở dòng 738. "Xe chưa chèn được"/"xe chờ chèn" thì không có, dù đây chính là nhu cầu không được phục vụ.
- Vì sao quan trọng: Không giải thích thì người đọc sẽ (a) coi mô hình nền là không dùng được, hoặc (b) hiểu tiêu chí đủ điều kiện như một chỉ tiêu an toàn giao thông. Cả hai đều sai.
- Đề xuất sửa: Thêm một đoạn ở Mục 2.2 hoặc 6.11.1: "va chạm trong SUMO là sự kiện chồng lấn hình học giữa hai xe trong mô phỏng, phần lớn do cách mô hình làn con xử lý các làn nội bộ cắt nhau; không phải chỉ số an toàn và không so được với số tai nạn". Đổi tên thành "va chạm mô phỏng (chồng lấn)". Định nghĩa "xe chưa vào được mạng" là phần nhu cầu bị dồn ở điểm sinh xe vì nhánh vào đã kín. Nói rõ chỉ số an toàn đúng nghĩa là xung đột có PET/TTC dưới ngưỡng (SSM), hiện chưa dùng.

### [GT-07] Hình 6.1 và Hình 6.2 lệch hướng 45°; tên nhánh theo bốn hướng chính không khớp hình
- Mức: nên sửa
- Vị trí: Hình 6.1 (Chapter/5_Experiments.tex:32, PDF tr. 29); Hình 6.2 (5_Experiments.tex:66-69, 76, PDF tr. 30); Hình 6.4, 6.5 (5_Experiments.tex:771, 800, PDF tr. 54-55)
- Trích: Hình 6.1: "LVL_W ... in from SW", "HDT_N ... in from NW", "LVL_E ... in from NE", "HDT_S ... in from SE" / Hình 6.2: "Tây (Lê Văn Lương)", "Bắc", "Nam", "Đông"
- Vấn đề: Mạng thật có Lê Văn Lương chạy Tây Nam-Đông Bắc và Hoàng Đạo Thúy chạy Tây Bắc-Đông Nam. Hình 6.2 vẽ vuông góc theo trục Đông-Tây/Bắc-Nam và ghi nhãn Bắc/Nam như hướng thật, không nói đã xoay hình. Hình 6.2 không ghi tên "Hoàng Đạo Thúy" ở hai nhánh Bắc, Nam. Hình 6.4 và 6.5 đo trên vùng chờ của nhánh Lê Văn Lương phía tây, là nhánh của mạng cũ, nơi rẽ trái còn bị cấm. Trong kịch bản hiện tại, rẽ trái từ Lê Văn Lương là hợp lệ, có mũi tên riêng. Nhãn trục và chú giải của hai hình này, cùng Hình 6.1, vẫn để tiếng Anh.
- Vì sao quan trọng: Người đọc đối chiếu hai hình sẽ không biết nhánh "Bắc" là nhánh nào trên Hình 6.1. Họ cũng dễ hiểu nhầm rằng thí nghiệm vùng chờ đo trên nhánh cấm rẽ của kịch bản hiện tại.
- Đề xuất sửa: Ghi chú ở Hình 6.2: "sơ đồ đã xoay; nhánh 'Tây' là nhánh Tây Nam ..." hoặc vẽ đúng hướng, có kim chỉ Bắc. Ghi tên đường trên cả bốn nhánh. Trong chú thích Hình 6.4, 6.5, ghi rõ đây là mạng trước F2, khi nhánh Lê Văn Lương phía tây còn cấm rẽ trái. Việt hóa nhãn hình.

### [GT-08] Khung giờ nghiên cứu 07:30-09:00, nhưng mọi kết quả chỉ chạy 07:30-08:00
- Mức: nên sửa
- Vị trí: Chapter/5_Experiments.tex:21 (PDF tr. 28), 530 (PDF tr. 44), 856 (PDF tr. 58-59); Chapter/0_3_Abstract.tex:11
- Trích: "cao điểm sáng 07:30-09:00" / "Thời lượng mô phỏng đầy đủ là 3600 s; vòng hiệu chỉnh và đánh giá dùng 1800 s đầu (07:30-08:00)" / "chỉ phủ nửa giờ đầu của khung cao điểm"
- Vấn đề: Khung 07:30-09:00 dài 5400 s, nhưng "thời lượng đầy đủ" lại ghi 3600 s. Mọi chỉ số tính trên [300, 1800) s, tức 25 phút. Đây chỉ là pha hình thành hàng chờ, chưa có đỉnh và pha giải tỏa của cao điểm. Tóm tắt và Mục 6.1.1 vẫn ghi 07:30-09:00 mà không nói điều này.
- Vì sao quan trọng: Hàng chờ, vượt đèn và tìm khoảng trống phụ thuộc mạnh vào trạng thái dòng trong cao điểm. Ghi 07:30-09:00 làm người đọc tưởng kết quả phủ cả khung giờ.
- Đề xuất sửa: Ghi ở Tóm tắt và Mục 6.1.1: "khung nghiên cứu 07:30-09:00; các thực nghiệm hiện tại chỉ mô phỏng 07:30-08:00 và tính chỉ số trên 07:35-08:00". Sửa con số 3600 s cho khớp, hoặc giải thích. Nêu lý do chọn 300 s khởi động, tức 2,5 chu kỳ đèn.

### [GT-09] M7b (độ trễ giải phóng vùng chờ) được gọi là "đại diện cho PET": dùng sai khái niệm PET
- Mức: nên sửa
- Vị trí: Chapter/4_Rule_execution.tex:90 (PDF tr. 24); Chapter/5_Experiments.tex:427 (PDF tr. 92); Chapter/3_Rule_generation.tex:51 (PDF tr. 12), 87
- Trích: "M7b: độ trễ giải phóng vùng chờ (đại diện cho PET)" / mục tiêu "5,65 s ... GĐ (dựa trên [Hsu])" / "PET nhỏ nghĩa là người tham gia giao thông chấp nhận khoảng trống nhỏ"
- Vấn đề: PET là khoảng thời gian từ lúc người thứ nhất rời vùng xung đột đến lúc người thứ hai tới vùng đó. Đây là chỉ số an toàn thay thế, đo trên từng cặp xung đột. Độ trễ từ lúc hết xanh đối diện đến lúc xe chờ rời vùng chờ là một đại lượng khác hẳn: nó phụ thuộc vào thời gian dọn nút và lượng xe còn lại. Mục tiêu 5,65 s "dựa trên" PET 2,15 s của Hsu mà không nói phép biến đổi. Dòng 3_Rule_generation.tex:87 còn liệt kê PET là "đại lượng đo được" của danh mục, trong khi không chỉ số nào đo PET.
- Vì sao quan trọng: Người làm an toàn giao thông sẽ hiểu luận văn có đo PET và sẽ đọc M7b như chỉ số an toàn.
- Đề xuất sửa: Bỏ chữ "đại diện cho PET". Gọi M7b là "thời gian giải phóng xe chờ rẽ trái trong nút". Nếu muốn giữ liên hệ với hành vi 9 (chấp nhận khoảng trống nhỏ) thì đo đúng PET hoặc khoảng trống chấp nhận/từ chối ở điểm xung đột rẽ trái - đi thẳng đối diện. Sửa dòng 87 cho khớp. Nói rõ cách suy ra con số 5,65 s.

### [GT-10] M6 (thời gian đi qua nút) có mục tiêu tính bằng tốc độ; tốc độ "giữa tuyến" được dùng làm tốc độ tiếp cận
- Mức: nên sửa
- Vị trí: Chapter/4_Rule_execution.tex:89 (PDF tr. 24); Chapter/5_Experiments.tex:424-425 (PDF tr. 92); Chapter/2_Literature_review.tex:27 (PDF tr. 6)
- Trích: M6: "Thời gian đi qua nút và qua nhánh vào ... s; phân phối" / Mục tiêu: "Tốc độ tiếp cận; tốc độ qua nút của xe máy (km/h) 27,3; 21,3 ... CG [Chu Cong Minh]" / Nguồn: "tốc độ 27,3 ± 5,2 km/h giữa tuyến, 21,3 ± 5,1 km/h trong dòng hỗn hợp"
- Vấn đề: Chỉ số đo bằng giây, mục tiêu cho bằng km/h. Luận văn không nói quãng đường dùng để quy đổi, tức không nói điểm bắt đầu và kết thúc của "qua nhánh vào" và "qua nút". 27,3 km/h là tốc độ giữa tuyến, không phải tốc độ tiếp cận nút. 21,3 km/h là tốc độ "trong dòng hỗn hợp", không phải tốc độ qua nút có đèn. Giờ cao điểm có hàng chờ thì thời gian qua nhánh vào chủ yếu là thời gian dừng chờ, không suy được từ tốc độ chạy.
- Vì sao quan trọng: M6 là một trong hai chỉ số "dòng tổng thể". Mục tiêu sai bản chất làm sai khoảng cách $d$ và điểm $S$.
- Đề xuất sửa: Định nghĩa M6 bằng hai mặt cắt cụ thể: từ mặt cắt cách vạch dừng X m (cần nêu X) đến mặt cắt cửa ra. Ghi rõ mục tiêu quy đổi từ tốc độ thế nào, hoặc đổi nhãn thành giả định. Đổi tên trong Bảng 6.10 cho đúng nguồn: "tốc độ giữa tuyến", "tốc độ trong dòng hỗn hợp".

### [GT-11] M1 (xả hàng), M4 (vị trí ngang), M5 (hàng chờ) thiếu định nghĩa vận hành
- Mức: nên sửa
- Vị trí: Chapter/4_Rule_execution.tex:84, 87, 88 (PDF tr. 24); Chapter/5_Experiments.tex:416, 423 (PDF tr. 92); Chapter/6_Conclusions.tex:59 (PDF tr. 98); Chapter/Appendix_B.tex:19-20 (PDF tr. 109)
- Trích: M1: "Khoảng thời gian xả hàng sau khi đèn xanh, theo loại phương tiện" / mục tiêu M1: "Khoảng thời gian bão hòa của dòng xe máy (s); hệ số ô tô 0,254; 1,4 CG [Vu]" / M4: "Vị trí ngang của xe máy đang dừng khi đèn chuyển xanh" / M5: "Chiều dài hàng chờ và mật độ xe máy" / Kết luận: "thay phạm vi quan sát hàng chờ hiện đặt 80 m"
- Vấn đề: M1 không nói là giãn cách giữa hai xe liên tiếp hay tổng thời gian xả, tính trên mỗi làn, mỗi nhánh hay mỗi mét bề rộng, bỏ mấy xe đầu. Con số 0,254 s và "hệ số ô tô 1,4" không có trong Bảng 2.1: nguồn Vu và Nguyen ở Bảng 2.1 chỉ ghi "mỗi 1% ô tô giảm lưu lượng bão hòa khoảng 0,4%". M4 không nói vị trí ngang đo so với mốc nào (tim làn, mép lề, tim đường). M5 không nói tiêu chí xe thuộc hàng chờ (ngưỡng tốc độ 5 km/h chỉ xuất hiện trong thí nghiệm vùng chờ) và cách đo chiều dài (từ vạch dừng tới đuôi xe dừng cuối cùng?). Phạm vi quan sát 80 m chỉ được nhắc ở Kết luận.
- Vì sao quan trọng: Lược đồ dữ liệu được thiết kế để đo lại từ video. Thiếu các định nghĩa này thì người xử lý video không đo cùng đại lượng với mô phỏng.
- Đề xuất sửa: Thêm cột "Đo ở đâu / khi nào / ngưỡng" vào Bảng 5.1. Dùng thuật ngữ quen thuộc: "giãn cách thời gian bão hòa (s/xe) của làn/nhánh", "lưu lượng bão hòa", "chiều dài hàng chờ lớn nhất mỗi chu kỳ (m), xe dừng khi v < 5 km/h", "vị trí ngang so với tim làn". Ghi nguồn và cách suy ra 0,254 s và 1,4.

### [GT-12] M8 (đi sai làn) đọc làn tại một điểm mà phía trước đó các làn chưa phân hướng
- Mức: nên sửa
- Vị trí: Chapter/4_Rule_execution.tex:91 (PDF tr. 24); Chapter/5_Experiments.tex:93 (PDF tr. 86), 108 (PDF tr. 30), 516 (PDF tr. 43)
- Trích: "Đi sai làn: tỷ lệ xe rẽ đứng ở làn không có hướng ra của nó, đọc tại điểm trước khi xe có thể cắt về làn đúng" / "Thượng nguồn cả ba là làn thường" / "Không có cọc phân cách: xe đổi làn tự do giữa lane 0 và lane 1 trên cả hai đoạn"
- Vấn đề: Theo chính mô tả của luận văn, trước đoạn 30 m cả ba làn là làn thường. Một xe rẽ trái đang ở lane 0 tại đầu đoạn 30 m chưa vi phạm gì nếu vạch liền và mũi tên chỉ hướng chưa bắt đầu. M8 khi đó đo việc chuyển làn muộn, không đo đi sai làn. Luận văn không nói vạch liền và mũi tên chỉ hướng bắt đầu ở đâu.
- Vì sao quan trọng: Theo quy tắc giao thông, "đi sai làn" phụ thuộc vào vạch sơn và biển. Không gắn với vạch sơn thì M8 không đo được từ video theo cùng nghĩa.
- Đề xuất sửa: Cần tác giả kiểm tra lại vị trí bắt đầu vạch liền và mũi tên chỉ hướng trên từng nhánh. Định nghĩa M8 gắn với vị trí đó, ví dụ "xe rẽ trái có mặt ở làn không có mũi tên rẽ trái tại điểm bắt đầu vạch liền". Nếu điểm này trùng đầu đoạn 30 m thì nói rõ.

### [GT-13] Chưa đặt M1-M10 cạnh các chỉ số quen thuộc của ngành
- Mức: nên sửa
- Vị trí: Chapter/4_Rule_execution.tex:97 (PDF tr. 23-24); Chapter/5_Experiments.tex:693 (PDF tr. 93, Bảng 6.16)
- Trích: "M1 và M6 đo năng lực thông qua và thời gian đi qua nút, chịu ảnh hưởng của mọi hành vi" / Bảng 6.16: "Số lượt qua vạch dừng mỗi giờ 7710 ... 6220 ... 8060"
- Vấn đề: Người làm giao thông sẽ hỏi ngay vì sao không dùng độ trễ (độ trễ kiểm soát trung bình, s/xe), chiều dài hàng chờ lớn nhất hoặc phân vị 95, và lưu lượng qua vạch theo hướng. Luận văn không giải thích quan hệ: M1 gần với lưu lượng bão hòa, M5 gần với hàng chờ khi bắt đầu xanh, M6 gần với độ trễ. "Số lượt qua vạch dừng mỗi giờ" xuất hiện trong bảng so sánh nhưng không phải một chỉ số. Hành vi 9 (chấp nhận khoảng trống nhỏ), 11 (đi chậm giữa làn) và luật vượt xe quay đầu không có chỉ số riêng.
- Vì sao quan trọng: "Độ chân thực" mà ngành chấp nhận trước hết là khớp lưu lượng, hàng chờ và độ trễ. Các chỉ số hành vi chỉ thuyết phục khi đứng cạnh nhóm chỉ số này.
- Đề xuất sửa: Thêm một đoạn hoặc cột nêu tương ứng giữa M1, M5, M6 và lưu lượng bão hòa, hàng chờ, độ trễ, đồng thời nói vì sao chọn dạng phân phối. Cân nhắc báo cáo thêm độ trễ trung bình theo nhánh và lưu lượng qua vạch theo hướng (chỉ báo cáo, không tính điểm). Nói rõ hành vi nào chưa có chỉ số.

### [GT-14] Một số hành vi chỉ mô tả cảm tính, chưa quan sát và đo được
- Mức: nên sửa
- Vị trí: Chapter/3_Rule_generation.tex:57, 72, 78-80, 129, 135 (PDF tr. 12-13, 15-16)
- Trích: hành vi 4: "Khoảng cách ngang nhỏ, lấn chiếm, luồn lách, dừng quá vạch" / hành vi 9: "Chấp nhận khoảng trống nhỏ, tạt đầu" / hành vi 11: "Xe máy đi chậm giữa làn" kèm "[TODO_CITE ...]" / hành vi 10 (bảng): "rẽ khi pha đi thẳng đối diện kết thúc" và (dòng 129): "rẽ khi dòng đi thẳng đối diện ngớt"
- Vấn đề: Hành vi 4 gộp bốn hành vi khác nhau. "Lấn chiếm" và "luồn lách" không có định nghĩa. "Tạt đầu" không nói tạt đầu ai, khoảng cách bao nhiêu. Hành vi 11 không nói "chậm" so với gì, "giữa làn" lệch bao nhiêu, và vì sao đó là lệch chuẩn. Hành vi 10 có hai định nghĩa thời điểm rời vùng chờ khác nhau.
- Vì sao quan trọng: Không định nghĩa được thì không đếm được từ video. Danh mục khi đó không "kiểm chứng được bằng dữ liệu" như dòng 87 tuyên bố.
- Đề xuất sửa: Với mỗi hành vi, viết một định nghĩa vận hành một câu: điều kiện quan sát, vị trí, ngưỡng. Ví dụ hành vi 9: "xe rẽ trái chấp nhận khoảng trống thời gian < X s trước xe đi thẳng đối diện". Tách hành vi 4 thành các mục con, gắn với M4 và M5. Thống nhất định nghĩa của hành vi 10: rời vùng chờ khi có khoảng trống chấp nhận được, hoặc chậm nhất khi hết xanh đối diện.

### [GT-15] "Quan sát" và "khảo sát hiện trường" không có mô tả phương pháp; ranh giới giữa "khảo sát" và "đo" không rõ
- Mức: nên sửa
- Vị trí: Chapter/3_Rule_generation.tex:57 (PDF tr. 12); Chapter/5_Experiments.tex:100 (PDF tr. 29), 104, 110, 112 (PDF tr. 30-31), 954 (PDF tr. 63), 1054 (PDF tr. 67)
- Trích: "Luận văn bổ sung bốn hành vi này từ quan sát giao thông thực tế của tác giả" / "Chiều dài 30 m của đoạn làn rẽ phải lấy từ khảo sát hiện trường, chưa đo" / "Chưa có số liệu đo thực địa" / "Theo khảo sát hiện trường, đèn có ba pha" / "là quan sát của tác giả ngày 29/10/2026, chưa đếm"
- Vấn đề: Không có chỗ nào nói khảo sát ngày 28/10, 29/10, 30/10 làm ở đâu, giờ nào, kéo dài bao lâu, bằng cách nào (đứng quan sát, quay phim, đi xe qua). "Khảo sát hiện trường" trong ngành thường gồm cả đo đạc, nên câu "lấy từ khảo sát hiện trường, chưa đo" khó hiểu: 30 m là ước lượng bằng mắt hay đo?
- Vì sao quan trọng: Hành vi 5-8, 11, luật vượt xe quay đầu, cấu hình ba pha và hướng cấm rẽ đều dựa trên các lần khảo sát này. Người đọc cần biết mức tin cậy của chúng.
- Đề xuất sửa: Thêm một bảng ngắn "Các lần khảo sát định tính tại nút": ngày, khung giờ, vị trí đứng, thời lượng, phương pháp, điều ghi nhận được. Dùng "quan sát định tính tại hiện trường" cho những gì không đo, và "ước lượng bằng mắt" cho con số 30 m nếu đúng như vậy.

### [GT-16] Nhu cầu và "quá tải" trình bày bằng xe/h, không quy đổi, không có tỷ số v/c
- Mức: nên sửa
- Vị trí: Chapter/5_Experiments.tex:413 (PDF tr. 92), 922 (PDF tr. 62); Chapter/2_Literature_review.tex:29 (PDF tr. 6)
- Trích: "Lưu lượng qua vạch theo nhánh ... (xe/h) 2620; 2130; 1800; 1630" / "Với hai làn đi thẳng mỗi nhánh, mạng đại diện quá tải ở mức nhu cầu đại diện 8180 xe/h" / Bảng 2.1: "Hệ số quy đổi xe máy khoảng 0,24"
- Vấn đề: Kết luận "quá tải" không có phép tính khả năng thông hành nào đi kèm: không có lưu lượng quy đổi (xcqđ/h), không có lưu lượng bão hòa theo nhánh, không có tỷ số v/c theo pha. Hệ số quy đổi 0,24 đã trích ở Chương 2 nhưng không được dùng.
- Vì sao quan trọng: Người làm giao thông sẽ hỏi nhu cầu đại diện có khả thi với hình học và chu kỳ giả định không. Nếu v/c > 1 ngay từ đầu thì hàng chờ dồn, xe không vào được mạng, khóa nút là hệ quả của nhu cầu chứ không phải của hành vi. Luận văn nên cho người đọc tự kiểm tra điều đó.
- Đề xuất sửa: Thêm một bảng ước tính khả năng thông hành theo nhánh và pha: lưu lượng quy đổi, thời gian xanh hiệu quả, lưu lượng bão hòa giả định, v/c. Ghi rõ là ước tính trên giá trị tạm thời.

### [GT-17] Một số khẳng định về giao thông không có trích dẫn hoặc mâu thuẫn với chính danh mục hành vi
- Mức: nên sửa
- Vị trí: Chapter/1_Introduction.tex:65 (bản cũ của đoạn này ở PDF tr. 3); Chapter/3_Rule_generation.tex:113 (PDF tr. 14-15), 117 (PDF tr. 15), 129 (PDF tr. 15-16)
- Trích: "Ngược lại, phần vật lý của chuyển động (bám xe, tránh va chạm, nhường đường) không đổi giữa các kịch bản." / "một hậu quả mà người vượt đèn thật tránh vì họ chỉ đi khi thấy có đường" / "xe chỉ bò lên phía trước như người xuất phát sớm ngoài thực tế" / "đây là cách mô hình hóa chấp nhận khoảng trống quen thuộc trong mô phỏng vi mô"
- Vấn đề: Câu ở Chương 1 mâu thuẫn với hành vi 9 (chấp nhận khoảng trống nhỏ). Nhường đường chính là ứng xử chấp nhận khoảng trống, và luận văn coi nó là một hành vi cần hiệu chỉnh. Tài liệu hiệu chỉnh mô phỏng vi mô cũng cho thấy tham số bám xe khác nhau giữa các địa điểm và khung giờ. Ba câu còn lại mô tả hành vi người lái thực tế mà không có nguồn hay quan sát.
- Vì sao quan trọng: Đây là lập luận chính cho việc tách sinh luật khỏi thực thi luật. Người trong ngành sẽ phản bác ngay câu "nhường đường không đổi giữa các kịch bản".
- Đề xuất sửa: Viết lại: "cơ chế tránh va chạm và giới hạn động học do trình mô phỏng giữ; tham số bám xe và chấp nhận khoảng trống vẫn được hiệu chỉnh trong không gian tham số". Gắn nguồn hoặc nhãn "giả định của luận văn" cho ba câu còn lại. Với câu cuối, trích một nguồn về mô hình chấp nhận khoảng trống (ví dụ tài liệu junction model của SUMO hoặc một giáo trình).

### [GT-18] Chương 2 thiếu các công trình nền của mô phỏng vi mô, hiệu chỉnh và dòng hỗn hợp xe máy
- Mức: nên sửa
- Vị trí: Chapter/2_Literature_review.tex:54 (PDF tr. 7), 64 (PDF tr. 8), 71 (PDF tr. 8)
- Trích: "tham số bám xe (mặc định là mô hình Krauss)" / "Mô hình dùng bám xe IDM và chuyển làn MOBIL" / "Hiệu chỉnh mô phỏng vi mô thường được phát biểu là bài toán tối ưu"
- Vấn đề: Krauss, IDM, MOBIL, SL2015 được nhắc nhưng không có trích dẫn. Chương không giới thiệu các họ mô hình bám xe kinh điển (Gipps, Wiedemann, Krauss, IDM). Không có tài liệu hướng dẫn hiệu chỉnh/kiểm định mô phỏng vi mô ngoài TAG; Hollander và Liu chỉ được trích ở Chương 1 và 3. Không có công trình mô hình hóa xe máy trong dòng hỗn hợp ngoài Saval và Semrau, ví dụ các mô hình xe máy chuyển động ngang và luồn lách đã công bố cho dòng hỗn hợp châu Á (tác giả tự chọn nguồn phù hợp). Các khái niệm lưu lượng bão hòa, thời gian tổn thất khởi động, khả năng thông hành dùng ở Chương 5-6 cũng không có tài liệu gốc (HCM hoặc giáo trình, tiêu chuẩn Việt Nam).
- Vì sao quan trọng: Phản biện ngành giao thông sẽ đánh giá Chương 2 là mỏng về phần giao thông. Họ cũng không có cơ sở để đánh giá cách luận văn chọn tham số và chỉ số.
- Đề xuất sửa: Thêm một mục ngắn "Mô hình hành vi trong mô phỏng vi mô" (bám xe, chuyển làn, chấp nhận khoảng trống, có trích bài gốc), một đoạn về quy trình hiệu chỉnh/kiểm định (hướng dẫn của FHWA hoặc tương đương, cùng Hollander và Liu), và một đoạn về mô hình xe máy trong dòng hỗn hợp. Trích tài liệu gốc cho các thuật ngữ khả năng thông hành.

### [GT-19] Cách gọi "hiệu chỉnh / đánh giá" và "dữ liệu đại diện" lệch quy ước của ngành
- Mức: nên sửa
- Vị trí: Chapter/3_Rule_generation.tex:32; Chapter/5_Experiments.tex:400 (PDF tr. 41), 437 (PDF tr. 41-42); Chapter/1_Introduction.tex:84 (PDF tr. 4)
- Trích: "Dữ liệu quan sát của mỗi kịch bản gồm nhiều ngày, chia thành ngày hiệu chỉnh và ngày đánh giá." / "luận văn dựng năm 'ngày đại diện' PROXY_D1-PROXY_D5 ... tổng hợp từ tài liệu"
- Vấn đề: Ngành giao thông tách hiệu chỉnh (calibration) và kiểm định (validation) trên dữ liệu độc lập. Luận văn làm đúng việc đó nhưng gọi bước sau là "đánh giá". Chữ "đánh giá" trong luận văn lại được dùng cho nhiều việc khác (đánh giá một đặc tả, thiết kế đánh giá). "Dữ liệu đại diện" gợi ý một mẫu đại diện cho nút thật, trong khi đây là dữ liệu tổng hợp dựng từ các nút khác.
- Vì sao quan trọng: Người đọc ngành giao thông dễ hiểu nhầm rằng đã có dữ liệu đo tại nút, hoặc rằng bước cuối là kiểm định theo nghĩa thông thường trên dữ liệu thực.
- Đề xuất sửa: Dùng "ngày hiệu chỉnh" và "ngày kiểm định"; gọi bước cuối là "kiểm định". Đổi "dữ liệu đại diện" thành "dữ liệu tổng hợp (dựng từ tài liệu)", hoặc định nghĩa rõ ngay lần đầu dùng ở Chương 1.

### [GT-20] Thuật ngữ giao thông dịch lạ hoặc không thống nhất
- Mức: nhỏ
- Vị trí: Chapter/3_Rule_generation.tex:87, 117, 121 (PDF tr. 15); Chapter/4_Rule_execution.tex:85, 97 (PDF tr. 23-24); Chapter/5_Experiments.tex:23, 108, 110 (PDF tr. 28-31), 1004 (PDF tr. 65); Chapter/2_Literature_review.tex:27, 29 (PDF tr. 6)
- Trích: "năng lực thông qua" / "giây cuối của pha đỏ", "lượt xanh kế tiếp" / "Chia xanh 42/16/44 s" / "headway 1,16 ± 0,65 s", "headway bão hòa 2,11 s" / "lane 0", "lane 1", "lane 2" / "Xe chưa chèn cuối lần chạy", "xe chờ chèn"
- Vấn đề và từ nên dùng:
  - "năng lực thông qua" -> "khả năng thông hành" (cách gọi trong TCVN 13592 và giáo trình).
  - "pha đỏ", "pha xanh", "lượt xanh" -> "thời gian đỏ", "thời gian xanh", "chu kỳ xanh kế tiếp" (pha là tổ hợp các dòng được đi cùng lúc, không phải màu đèn).
  - "chia xanh" -> "phân bổ thời gian xanh".
  - "headway" -> "giãn cách thời gian giữa hai xe liên tiếp"; "headway bão hòa" -> "giãn cách thời gian bão hòa".
  - "hệ số quy đổi" -> "hệ số quy đổi ra xe con (PCU)".
  - "lane 0/1/2" -> "làn 1/2/3 tính từ lề phải", kèm một chú thích về chỉ số làn của SUMO ngay lần đầu dùng.
  - "xe chờ chèn" -> "xe chưa vào được mạng (nhu cầu bị dồn ở điểm sinh xe)".
- Vì sao quan trọng: Trộn tiếng Anh và từ dịch lạ làm phần giao thông trông như viết bởi người ngoài ngành.
- Đề xuất sửa: Thêm các thuật ngữ trên vào `glossary.tex` và thay thống nhất trong mọi chương.

### [GT-21] Một số mô tả về SUMO và về làn chưa chính xác
- Mức: nhỏ
- Vị trí: Chapter/3_Rule_generation.tex:100 (PDF tr. 14); Chapter/Appendix_A.tex:66 (PDF tr. 105); Chapter/5_Experiments.tex:850 (PDF tr. 58), 817 (PDF tr. 57, Hình 6.6)
- Trích: "bám xe (thời gian phản ứng, khoảng cách tối thiểu, ...)" / "khoảng thời gian an toàn T thành tau" / "vạch dừng làn 2 (làn chung cho đi thẳng, rẽ trái và rẽ phải)" / "hai xe máy đi song song ở làn 1 và làn 2"
- Vấn đề: (1) Theo tài liệu SUMO, `tau` là giãn cách thời gian mong muốn tối thiểu của người lái. Gọi nó là "thời gian phản ứng" là cách hiểu lỏng: SUMO mô phỏng thời gian phản ứng bằng `actionStepLength`. Câu ở Phụ lục A ánh xạ đúng hơn. (2) Ở dòng 850, "làn 2" là làn trái cùng theo chỉ số SUMO, nhưng lại được ghi là làn chung có cả rẽ phải. Rẽ phải từ làn trái cùng là bất thường. Cần tác giả kiểm tra lại cấu hình làn của mạng trước F2. (3) Ở Hình 6.6, "làn 1, làn 2" không rõ là chỉ số SUMO hay đếm từ lề phải.
- Vì sao quan trọng: Đây là các lỗi nhỏ, nhưng sinh viên giao thông đọc là thấy ngay và sẽ nghi ngờ phần còn lại.
- Đề xuất sửa: Ở Mục 3.3.1 viết "giãn cách thời gian mong muốn (`tau`)". Kiểm tra và sửa mô tả "làn 2" ở dòng 850. Dùng một quy ước đánh số làn duy nhất trong toàn luận văn.
