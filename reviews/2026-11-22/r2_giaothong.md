# Sinh viên Kỹ thuật giao thông — Vòng 2

Căn cứ của vòng này: nguồn 6 chương hiện có trên đĩa, cùng PDF mới `build2/main.pdf` (131 trang). "tr." là số trang in ở chân trang. Trang tệp PDF bằng số in cộng 18. Tôi đã đối chiếu lại các dòng tôi trích ở vòng 1: nội dung nguồn không đổi, chỉ số trang và số hình/bảng đổi theo cách đánh số mới. Chương 6 của PDF cũ nay là Chương 5. Chỉ số và tiêu chí đủ điều kiện nay nằm ở Chương 4.

## A. Tự kiểm lại các nhận xét vòng 1

Điều chỉnh chung: Chương 3 và 4 chỉ trình bày ý tưởng. Vì vậy mọi đề xuất định nghĩa chỉ số và hành vi của tôi được tách làm hai phần. Định nghĩa vận hành tổng quát, dùng ký hiệu và không có số liệu của nút, đặt ở Chương 3 hoặc 4. Giá trị cụ thể của nút Lê Văn Lương x Hoàng Đạo Thúy (30 m, 80 m, 5 s, 5 km/h…) đặt ở Chương 5, Mục 5.1 hoặc 5.8.1.

- GT-01: còn đúng. Vị trí mới: `1_Introduction.tex:82` (tr. 5); `3_Rule_generation.tex:75-76` (Bảng 3.1, tr. 16); `5_Experiments.tex:23` (tr. 30-31), `:888` (tr. 63); `4_Rule_execution.tex:93` (Bảng 4.1, tr. 28); `0_3_Abstract.tex:9, 15`.
- GT-02: còn đúng. Vị trí mới: `5_Experiments.tex:23` (tr. 31, câu "Đi thẳng hoặc rẽ trái trên làn này khi đèn xanh là đúng luật" vẫn còn); `:91, 93` (Bảng 5.1, tr. 89); `:108` (tr. 32-33); `:172` (tr. 34); `:429-430` (Bảng 5.10, tr. 95); `4_Rule_execution.tex:92` (tr. 28).
- GT-03: còn đúng. Vị trí mới: `5_Experiments.tex:108-112` (tr. 32-33); Hình 5.1 (tr. 31); Hình 5.2 (tr. 32). Bảng 5.1 (bản vá mạng) vẫn trôi về tr. 89, trong khi được dẫn ở tr. 31. Sơ đồ phân làn và sơ đồ pha đặt ở Mục 5.1, đúng khung của GVHD.
- GT-04: còn đúng, cần sửa lại đề xuất. Vị trí mới: `4_Rule_execution.tex:85-86` (tr. 28); `2_Literature_review.tex:23` (tr. 7); Bảng 5.4 (tr. 91); Bảng 5.10 (tr. 95); `Appendix_B.tex:17-18, 29` (tr. 112). Đề xuất sửa lại: ở Chương 4 định nghĩa M2 (xuất phát sớm) và M3 (vượt đèn đỏ) loại trừ nhau bằng ký hiệu $T$ ("$T$ giây cuối của thời gian đỏ"), và nói cách xử lý vàng và đỏ toàn phần. Ở Mục 5.8.1 nêu giá trị $T$ (5 s theo Mai và cs., hoặc 10 s kèm lý do).
- GT-05: còn đúng. Vị trí mới: `4_Rule_execution.tex:83` (tr. 28); `2_Literature_review.tex:71` (tr. 9-10); `5_Experiments.tex:514` (tr. 46), `:829` (tr. 60).
- GT-06: còn đúng. Vị trí mới: `5_Experiments.tex:532` (tr. 47), `:738` (tr. 55), `:920-922` (tr. 64-65), `:1004` (Bảng 5.26, tr. 68). Đoạn giải thích "va chạm trong SUMO là chồng lấn hình học" đặt ở Mục 2.2 (nói chung về trình mô phỏng) hoặc 5.12.1. Không đặt ở Chương 4.
- GT-07: còn đúng, nay là Hình 5.1 (tr. 31), Hình 5.2 (tr. 32), Hình 5.4 và 5.5 (tr. 57-58).
- GT-08: còn đúng. Vị trí mới: `5_Experiments.tex:21` (tr. 30), `:530` (tr. 47), `:856` (tr. 61-62); `0_3_Abstract.tex:11`, `0_4_Abstract_English.tex:11`. Chương 3 và 1 nay chỉ ghi "giờ cao điểm hoặc thấp điểm", đúng khung, nên chỉ cần sửa ở Tóm tắt và Chương 5.
- GT-09: còn đúng. Vị trí mới: `4_Rule_execution.tex:90` (tr. 28); Bảng 5.10 (tr. 95); `3_Rule_generation.tex:51` (tr. 14-15), `:87` (tr. 15).
- GT-10: còn đúng, cần sửa lại đề xuất. Vị trí mới: `4_Rule_execution.tex:89` (tr. 28); Bảng 5.10 (tr. 95); `2_Literature_review.tex:27` (tr. 7). Chương 4 định nghĩa M6 (thời gian qua nút) giữa "mặt cắt vào cách vạch dừng $L_{in}$" và "mặt cắt ra". Giá trị $L_{in}$ và cách quy đổi mục tiêu từ tốc độ sang thời gian nêu ở Mục 5.5.
- GT-11: còn đúng, cần sửa lại đề xuất. Vị trí mới: `4_Rule_execution.tex:84, 87, 88` (tr. 28); Bảng 5.10 (tr. 95); `6_Conclusions.tex:59` (tr. 101); `Appendix_B.tex:19-20` (tr. 112). Cột "đo ở đâu / khi nào / ngưỡng" của Bảng 4.1 chỉ ghi dạng tổng quát ("ngưỡng tốc độ dừng $v_{stop}$", "phạm vi quan sát hàng chờ $L_q$"). Giá trị 5 km/h và 80 m nêu ở Mục 5.8.1.
- GT-12: còn đúng, cần sửa lại đề xuất. Vị trí mới: `4_Rule_execution.tex:91` (tr. 28); Bảng 5.1 (tr. 89); `5_Experiments.tex:93`, `:108` (tr. 32), `:516` (tr. 46). Chương 4 định nghĩa M8 (đi sai làn) "tại điểm bắt đầu vạch liền phân làn hoặc mũi tên chỉ hướng". Chương 5 nói điểm đó ở nút thử nghiệm có trùng đầu đoạn 30 m hay không.
- GT-13: còn đúng. Vị trí mới: `4_Rule_execution.tex:97` (tr. 28-29); Bảng 5.17 (tr. 96).
- GT-14: còn đúng. Vị trí mới: `3_Rule_generation.tex:57, 72, 78-80` (tr. 15-16), `:129, 135` (tr. 19). Định nghĩa vận hành của từng hành vi viết dạng tổng quát ở Chương 3, không gắn nhánh hay số đo của nút.
- GT-15: còn đúng, cần sửa lại đề xuất. Vị trí mới: `3_Rule_generation.tex:57` (tr. 15); `5_Experiments.tex:100` (tr. 31), `:104, 110, 112` (tr. 32-33), `:954` (tr. 66), `:1054` (tr. 70). Bảng "các lần quan sát định tính tại nút" đặt ở Chương 5 (Mục 5.1). Chương 3 chỉ ghi "bổ sung từ quan sát tại một nút có đèn, mô tả ở Mục 5.1".
- GT-16: còn đúng. Vị trí mới: Bảng 5.10 (tr. 95); `5_Experiments.tex:922` (tr. 65); `2_Literature_review.tex:29` (tr. 7).
- GT-17: còn đúng. Vị trí mới: `1_Introduction.tex:65` (tr. 4; câu "phần vật lý của chuyển động (bám xe, tránh va chạm, nhường đường) không đổi giữa các kịch bản" nay đã có trong PDF); `3_Rule_generation.tex:113, 117` (tr. 18), `:129` (tr. 19).
- GT-18: còn đúng. Vị trí mới: `2_Literature_review.tex:54` (tr. 8), `:64, 71` (tr. 9-10).
- GT-19: còn đúng, cần sửa lại đề xuất. Vị trí mới: `3_Rule_generation.tex:32` (tr. 13); `5_Experiments.tex:400` (tr. 43), `:437` (tr. 44); `1_Introduction.tex:84` (tr. 5). Tôi rút lại từ "dữ liệu tổng hợp". Trong ngành, "số liệu tổng hợp" thường hiểu là số liệu đã gộp (aggregated). Nên dùng "dữ liệu thay thế (dựng từ tài liệu)" như VP-07 đề xuất. "Ngày kiểm định" thay cho "ngày đánh giá" thì giữ nguyên.
- GT-20: còn đúng, bổ sung một vị trí sót: "năng lực thông qua" còn ở `4_Rule_execution.tex:35` (tr. 25). Các vị trí khác: `3_Rule_generation.tex:87` (tr. 15), `:117, 121` (tr. 18); `4_Rule_execution.tex:85, 97` (tr. 28-29); `5_Experiments.tex:110` (tr. 33); `2_Literature_review.tex:27, 29` (tr. 7).
- GT-21: còn đúng. Vị trí mới: `3_Rule_generation.tex:100` (tr. 17); `Appendix_A.tex:66` (tr. 108); `5_Experiments.tex:850` (tr. 61); Hình 5.6 (`:817`, tr. 60).

## B. Phản biện chéo

### Đã hết trên bản mới
- HD-10: đã hết phần chính. Kiểm tra hợp lệ và chỉ số nay đều ở Chương 4, khớp Hình 1.1. `3_Rule_generation.tex:13` nói "hai phần". Chương 3 không còn câu "được thêm sau khi chẩn đoán… (Mục 6.11.11)".
- HV-14: đã hết vế "PDF không có OPRO/FunSearch/Eureka" (nay ở Mục 3.6.1, tr. 21). Vế "Chương 2 chưa có bảng so sánh" vẫn còn.
- Các ghi chú "PDF build từ bộ 7 chương" trong đầu file của HD, ND, VP, HB, LG, HV: đã hết. Mọi số trang "Chương 6/7" trong các file đó nay là Chương 5/6, trang lệch +2 đến +3.
- HD-01, ND-01, HB-01, HV-01 (tên trên bìa): cách nêu vấn đề đã hết hiệu lực, xem mục Phản đối.

### Đồng ý
- HD-02: đồng ý. Kết luận chính còn là TODO (`6_Conclusions.tex:45`, tr. 100).
- HD-03, HV-04: đồng ý cần câu hỏi nghiên cứu. Xem Phản đối về cách viết RQ1 của HV-04.
- HD-04, HD-05, ND-04, HV-03: đồng ý. Kết quả trên mạng cuối đang bị chôn giữa các mạng đã bỏ. Việc sắp xếp lại nằm gọn trong Chương 5, không đụng cấu trúc chương do GVHD chốt.
- HD-06, ND-02, HB-02, HV-09: đồng ý, còn đúng trên bản mới. Bảng 5.1 (bản vá mạng) và Bảng 5.10 (mục tiêu) vẫn ở tr. 89 và 95. Với người đọc ngành giao thông, đây là hai bảng mô tả nút và nhu cầu, nên càng phải đứng cạnh Mục 5.1.
- HD-08: đồng ý "đủ điều kiện" dễ hiểu nhầm là "giống thực tế". Xem Phản đối về chữ "an toàn".
- HD-11, LG-08, HV-11: đồng ý cần mục "Hạn chế". Nên gộp thêm các hạn chế giao thông: G0 tính trên số đếm 15 phút (GT-05), mục tiêu M9 (chặn làn rẽ phải) dựa trên mạng có cọc, chỉ mô phỏng 07:30-08:00.
- HD-13, HV-14: đồng ý Chương 2 mỏng. Tôi nghiêng về bổ sung cả phía giao thông (GT-18), không chỉ phía LLM.
- HD-14, LG-20: đồng ý, trùng GT-15. Năm hành vi "từ quan sát" không có mô tả cách quan sát.
- HD-15, ND-12, VP-02, HB-03, HV-08: đồng ý. TODO vẫn còn trên bản mới (tr. 15, 29, 100).
- HD-16, ND-03, VP-03, HV-10: đồng ý. "F2" vừa là nhóm hành vi vừa là mạng. Còn đúng ở tr. 30 và tr. 64.
- ND-05: đồng ý. Thiếu khái niệm nền (bám xe, lưu lượng bão hòa, tổn thất khởi động, pha, chu kỳ). Khớp GT-18.
- ND-06: đồng ý. Định nghĩa "xe chờ chèn" đề xuất đúng bản chất giao thông. Tôi đề nghị thêm cụm "nhu cầu chưa được phục vụ" để người làm giao thông nhận ra ngay.
- ND-07, VP-04, HV-02: đồng ý. Tóm tắt dùng thuật ngữ nội bộ và kể theo ngày.
- ND-09: đồng ý.
- ND-14, HB-05, HV-20: đồng ý, trùng GT-07.
- ND-15, VP-05: đồng ý đánh số làn bị dùng lẫn. Xem Mâu thuẫn về cách gọi.
- ND-17, ND-18, ND-19, VP-06: đồng ý.
- VP-01, VP-09, VP-11, VP-15: đồng ý.
- VP-07: đồng ý. Tôi bỏ đề xuất "dữ liệu tổng hợp" của mình (xem GT-19).
- VP-17, HV-17: đồng ý. Phụ lục B (tr. 112) thiếu ba bảng mà M9 (chặn làn rẽ phải) và M10 (đi trên vỉa hè) cần.
- HB-04, HB-06, HB-07, HB-08, HB-09, HB-10, HB-11, HB-13, HB-14, HB-15: đồng ý. HB-06 quan trọng với người đọc bản in đen trắng: con số giả định về hình học và đèn sẽ trông như số đo.
- HB-16: đồng ý. Hàm khoảng cách và điểm tổng cần công thức đánh số.
- HB-17: đồng ý, nhất là ý thêm ảnh hiện trường hoặc ảnh vệ tinh cạnh Hình 5.2 ở Chương 5. Ảnh này giúp người đọc ngành giao thông tự kiểm tra phân làn.
- LG-01: đồng ý, nên nâng thành nhận xét chính về kết quả. Thêm một lý do từ phía giao thông: xe chờ chèn ở PROXY_D1 là dấu hiệu nhu cầu vượt khả năng thông hành của mạng giả định (GT-16). Quy hết cho `accel` là bỏ qua phía nhu cầu.
- LG-02, LG-05, LG-12, LG-13, LG-17: đồng ý.
- LG-03: đồng ý. Hành vi 10 (rẽ trái chờ giữa nút) ở B0 đến từ bản vá mạng cộng điểm chờ nội bộ của SUMO. Từ góc giao thông, gọi B0 là "SUMO mặc định" làm sai phép so sánh "mô hình chuẩn so với thực tế".
- LG-04: đồng ý. Cùng gốc với GT-06: "va chạm" của SUMO không phải tai nạn, nhưng ngưỡng 142/h và quy tắc dự phòng bỏ trần va chạm làm câu "không thể khớp nhờ va chạm" sai.
- LG-06, HV-12: đồng ý.
- LG-07: đồng ý, trùng GT-08.
- LG-09: đồng ý. Hành vi 9 (chấp nhận khoảng trống nhỏ) và 11 (đi chậm giữa làn) không có chỉ số, trùng GT-13 và GT-14.
- LG-10: đồng ý, trùng GT-04 và GT-11.
- LG-11: đồng ý, còn đúng. `5_Experiments.tex:91` vẫn trỏ `section:3.3`, nay là Mục 3.5 "Biểu diễn luật".
- LG-14: đồng ý. Sức chứa vùng chờ phụ thuộc hình học nhánh, nên con số của Lê Văn Lương phía tây không chuyển được sang Hoàng Đạo Thúy.
- LG-15, LG-16, LG-19: đồng ý.
- LG-18, HV-07: đồng ý cần nói rõ hành vi nào thật sự xuất hiện trong lần chạy. Xem Mâu thuẫn về chữ "hoãn". Bảng phủ hành vi của HV-07 nên có thêm cột "định nghĩa vận hành / đo từ video thế nào".
- HV-05: đồng ý. Bài học bề rộng làn nội bộ nên chuyển sang hạn chế của mô hình làn con, không gọi là đóng góp.
- HV-15, HV-16, HV-18, HV-19: đồng ý.
- HD-07, HD-09, HD-12, HD-17, HD-18: đồng ý về vấn đề. Xem Phản đối về câu viết lại của HD-07.

### Phản đối
- HD-01, ND-01, HB-01, HV-01 (bìa "Mô hình thế giới vĩ mô trong trò chơi máy tính"): phản đối cách nêu "sót từ mẫu" và đề xuất tự đổi tên. Theo thông tin mới, đây là tên đề tài đã đăng ký. Đề xuất đúng: "tên đăng ký lệch nội dung, tác giả cần hỏi GVHD hoặc phòng đào tạo". Cả bốn nhận xét đều đưa sẵn một tên thay thế. Tác giả không được tự thay nếu chưa có thủ tục đổi tên.
- HD-07 và HV-02 (câu tóm tắt viết lại): phản đối vế "do gia tốc xe máy chuyển giao từ tài liệu trong bộ luật nền" và "phân tích loại bỏ chỉ ra nguyên nhân là `accel` của B1". Số liệu không đỡ được quan hệ nhân quả này (LG-01): trả `accel` về mặc định vẫn còn 10-126 xe chờ chèn. Nên viết "yếu tố lớn nhất trong các biến thể đã thử".
- HD-07, HD-08 ("qua bộ lọc an toàn") và HV-04 (RQ1 "mà không làm mô phỏng kém an toàn hơn"): phản đối chữ "an toàn". Tiêu chí đủ điều kiện gồm không teleport, không còn xe chờ chèn, qua G0 (cổng GEH lưu lượng) và số va chạm mô phỏng. Không mục nào là chỉ số an toàn giao thông. "Va chạm" SUMO là chồng lấn hình học, còn chỉ số an toàn thật (PET, TTC qua SSM) chưa dùng (GT-06). Người làm an toàn giao thông đọc "bộ lọc an toàn" sẽ hiểu mô phỏng đã được đánh giá an toàn. Nên dùng "bộ lọc tính hợp lệ của lần chạy" hoặc "chạy hợp lệ", và viết RQ1 là "... mà không làm tăng số va chạm mô phỏng và số xe kẹt so với B0".
- HV-13 (câu viết lại "chuyển tham số IDM sang Krauss làm hỏng năng lực thông qua"): phản đối về thuật ngữ và mức khẳng định. "Năng lực thông qua" nên là "khả năng thông hành" (GT-20). "Làm hỏng" khẳng định quá mức (LG-01). Đề xuất: "chuyển giá trị gia tốc của IDM sang Krauss làm giảm khả năng thông hành mô phỏng; đây là rủi ro khi chuyển tham số giữa hai mô hình bám xe khác nhau".
- ND-16 (cột "Ý nghĩa" của Bảng 5.3 coi `tau` là "thời gian phản ứng"): phản đối phần nghĩa. Theo tài liệu SUMO, `tau` là giãn cách thời gian mong muốn tối thiểu. Thời gian phản ứng do `actionStepLength` mô phỏng (GT-21). Cột "Ý nghĩa" nên ghi "giãn cách thời gian mong muốn (s)". `sigma` nên ghi "mức không hoàn hảo của người lái (dao động tốc độ ngẫu nhiên)".
- ND-08 (tên ngắn "M5 (mật độ hàng chờ)", "M4 (vị trí dừng)"): phản đối nhẹ. M5 gồm cả chiều dài hàng chờ, nên gọi "M5 (hàng chờ)". M4 đo vị trí ngang và độ vượt vạch, nên gọi "M4 (vị trí dừng và dừng quá vạch)". Với M1, câu "khoảng thời gian giữa hai xe liên tiếp qua vạch dừng sau khi đèn xanh" cần thêm "trên cùng một làn, bỏ $n$ xe đầu". Nếu không, người làm giao thông sẽ không biết đó là giãn cách bão hòa hay giãn cách thô.
- ND-13 (vị trí "cuối Chương 4" cho ví dụ chạy xuyên suốt với xe vào từ HDT_S): phản đối vị trí. Chương 4 không được nhắc nút cụ thể. Ví dụ phải đặt ở Mục 5.2. Nội dung ví dụ thì đúng về giao thông: xe rẽ trái trái phép vào nút trong thời gian xanh của chính nhánh mình rồi chờ dòng đối diện.
- VP-12 (câu viết lại 3:47 "Bốn nghiên cứu, mỗi nghiên cứu đo một khía cạnh của hành vi vượt đèn đỏ"): phản đối chữ "đo". Saval và cs. không đo vượt đèn đỏ mà giả định xác suất dừng 0,5 trong mô hình. Gao và cs. đo xe đạp điện, không đo xe máy. Đề xuất: "Bốn nghiên cứu, hai đo trên video và hai từ mô hình hoặc loại xe khác, cho bốn khía cạnh của hành vi vượt đèn đỏ."
- VP-04 (bản tiếng Việt "vì mạng mô phỏng không thông qua hết nhu cầu đại diện"): đồng ý ý, sửa từ. Nên viết "không phục vụ hết nhu cầu". Ngành giao thông nói "phục vụ nhu cầu" và "khả năng thông hành", không nói "thông qua nhu cầu".
- HB-17 (ghép ảnh hiện trường bằng `subcaption` cạnh Hình 6.2): đồng ý ý, chỉ lưu ý vị trí nay là Hình 5.2 trong Chương 5.

### Mâu thuẫn
- Cách gọi tên dữ liệu: VP-07 "dữ liệu thay thế", HD-16 "dữ liệu giả lập từ tài liệu", GT-19 (vòng 1) "dữ liệu tổng hợp". Tôi nghiêng về VP-07. "Giả lập" dễ lẫn với đầu ra mô phỏng. "Tổng hợp" trong tiếng Việt ngành thường là số liệu đã gộp. "Thay thế" nói đúng vai trò: dùng thay số đo cho tới khi có video.
- Đánh số làn: ND-15 và VP-05 đề xuất dùng thống nhất "làn 0" (theo chỉ số SUMO). GT-20 đề xuất "làn 1/2/3 tính từ lề phải". Tôi nghiêng về gọi bằng tên chức năng: "làn sát lề phải (làn rẽ phải liên tục)", "làn giữa", "làn sát tim đường". Chỉ số SUMO ghi trong ngoặc một lần ở Mục 5.1.3 và trong `\texttt`. "Làn 0" không có trong cách gọi của ngành. Còn số thứ tự tính từ bên nào thì mỗi tài liệu một kiểu, nên dễ đọc ngược.
- Hành vi 8 (đi ngược chiều): LG-18 và HD-14 đề xuất viết "10 trong 11 hành vi; đi ngược chiều được hoãn", tức giữ nó như hạng mục dở dang. GT-01 đề xuất ghi rõ nó (và có thể cả đi trên vỉa hè) nằm ngoài phạm vi. Tôi nghiêng về GT-01. Phạm vi đề tài đã loại đi ngược chiều, và chữ "hoãn" mời hội đồng hỏi vì sao chưa làm. Với đi trên vỉa hè, cần tác giả chốt: giữ trong mô hình (thì bỏ khỏi danh sách loại trừ) hay loại ra (thì bỏ M10 (đi trên vỉa hè) và lựa chọn `sidewalk`).
- HD-04, HB-12, HV-15 muốn chuyển Mục 5.3-5.4 (yêu cầu hệ thống, kiến trúc) sang phụ lục, còn HV-05 muốn giữ Bảng 5.2 (ánh xạ khái niệm sang SUMO) ở thân bài. Hai đề xuất này không xung đột. Tôi chỉ lưu ý: khi rút gọn, giữ trong thân Chương 5 mọi thứ mô tả nút, nhu cầu và cấu hình đèn (Mục 5.1, Bảng 5.1, Bảng 5.10). Đó là phần người đọc ngành giao thông cần nhất, và hiện đang trôi xa nhất.

### Bỏ sót (vấn đề không ai nêu)
1. Hành vi 6 (chặn làn rẽ phải) mâu thuẫn với chính mô tả làn (GT-02). Theo `5_Experiments.tex:23, 108`, đi thẳng trên làn đó là đúng luật. Vậy xe đi thẳng chờ đỏ trên làn đó không phải vi phạm. Mục tiêu M9 (chặn làn rẽ phải) lại đo "xác suất xe đi thẳng chọn lane 0". Ngoài ra câu "rẽ trái trên làn này khi đèn xanh là đúng luật" trái với Bảng 5.1. Không reviewer nào nêu.
2. Cổng G0 dùng ngưỡng GEH < 5 của TAG trên số đếm 15 phút tách theo loại xe và hướng (GT-05). Tính như vậy lỏng hơn chuẩn khoảng gấp đôi. HD-08 và LG-06 có bàn tiêu chí đủ điều kiện, nhưng không ai thấy lệch đơn vị này.
3. Không có sơ đồ phân làn và sơ đồ pha (GT-03). Các reviewer chỉ nêu Hình 5.1 và 5.2 lệch hướng (ND-14, HB-05). Ngay cả khi sửa hướng, người đọc vẫn không dựng lại được nút: ba làn mỗi nhánh, mũi tên hướng đi, hướng cấm, ba pha và thời gian xanh.
4. Nhu cầu và kết luận "quá tải" không có ước tính khả năng thông hành: không lưu lượng quy đổi, không v/c (GT-16). Điểm này quan trọng cho LG-01: xe chờ chèn có thể là hệ quả của nhu cầu đại diện vượt khả năng thông hành của hình học giả định, không chỉ do `accel`.
5. M7b được gọi "đại diện cho PET" (GT-09), và mục tiêu M6 (thời gian qua nút) cho bằng km/h từ tốc độ giữa tuyến (GT-10). LG-09 có nhắc M7b nhưng không chỉ ra rằng độ trễ giải phóng vùng chờ không phải PET. Hai lỗi khái niệm này làm sai nghĩa hai chỉ số mà người làm giao thông và an toàn giao thông sẽ đọc kỹ nhất.
