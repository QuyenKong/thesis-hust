# Hội đồng phản biện, Vòng 2

Căn cứ: nguồn hiện tại (`3_Rule_generation`, `4_Rule_execution`, `5_Experiments`, `6_Conclusions`) và PDF build2 (131 trang). "tr. N" là số trang in ở chân trang; trang trong tệp PDF bằng N + 18. Độ dài các chương trên build2: Ch1 6 trang (tr. 1–6), Ch2 5 (7–11), Ch3 12 (12–23), Ch4 6 (24–29), Ch5 68 (30–97), Ch6 4 (98–101). Mọi đề xuất dưới đây giữ khung GVHD đã chốt: Ch3–4 chỉ trình bày ý tưởng; nút giao, số liệu và kết quả chỉ ở Ch5, tóm tắt và kết luận; Ch1 đi theo trình tự lợi ích, "tuy nhiên", hướng giải quyết.

## A. Tự kiểm lại

- HD-01: cần sửa lại. Theo điều phối, bìa (`Cover.tex:13`, `Cover2.tex:13`, tệp PDF tr. 1–2) ghi đúng tên đề tài đã đăng ký, nên đây không phải chữ sót từ mẫu. Viết lại nhận xét thành: "Tên đăng ký lệch nội dung luận văn. Tác giả cần hỏi GVHD hoặc phòng đào tạo." Tôi rút câu tên đề tài đã gợi ý. Tôi đồng ý với r2_logic, r2_hinhbang và r2_giaothong rằng tác giả không được tự đổi tên trên bìa khi chưa có thủ tục. Ý về `\TITLE`/`pdftitle` (`main.tex:73`, `:121`) vẫn đúng.
- HD-02: còn đúng (`6_Conclusions.tex:45`, tr. 100; chưa có bảng đối chiếu mục tiêu ở 6.1.2, tr. 98). Câu kết luận mẫu của tôi phải sửa theo r2_logic, vì nó có hai vế vượt số liệu. (a) "Mọi lỗi đều là lỗi cấu trúc" sai: P1 có 14/15 lần thử hỏng do lỗi tổng tỷ trọng, và Bảng 5.33 có 4 lỗi giá trị ngoài miền (LG-12). (b) "Hạ điểm tổng bằng cách bỏ bớt luật" sai: B2 vẫn giữ đủ cấu trúc B1 mà có $S$ nhỏ nhất 1,1438, thấp hơn 1,1680 của P2 (LG-02). Câu thay: "P2 mắc chủ yếu lỗi cấu trúc, P1 mắc chủ yếu lỗi tổng tỷ trọng; bộ kiểm tra hợp lệ bắt mọi lỗi trước khi chạy. Từ vòng 2, P2 giữ một cấu trúc thiếu ba loại luật; chưa kiểm tra việc bỏ luật có làm giảm $S$ hay không."
- HD-03: còn đúng (`1_Introduction.tex:78`, `:89–96`, tr. 4–5; E1, E2 xuất hiện lần đầu ở `5_Experiments.tex:503`, tr. 45; `6_Conclusions.tex:23`, tr. 98 vẫn gọi Mục 5.13 là "các đóng góp kỹ thuật"). Thêm theo r2_logic và r2_giaothong: câu hỏi nghiên cứu CH1 không được dùng chữ "an toàn". Viết: "…mà không làm tăng số va chạm mô phỏng và số xe kẹt so với B0". Câu trả lời hiện tại cho CH1 là "chưa đạt", vì B1 bị loại ở 15/15 lần chạy (tr. 72).
- HD-04: còn đúng. Vị trí mới: Ch5 chiếm 68/101 trang. Các mục cần cắt hoặc chuyển phụ lục, đánh số theo build2: 5.3 (tr. 36–37), 5.4 (tr. 38–42), 5.9 (tr. 47–51), 5.10 (tr. 51–53), 5.13 (tr. 77–87), 5.14 (tr. 87–88); các bảng trôi Bảng 5.6, 5.7 (tr. 93–94). Ý phụ "Ch4 chỉ có 3 trang" đã hết, vì Ch4 nay có 6 trang. Về các bảng: chuyển Bảng 5.13 (thư viện) sang phụ lục, cắt Bảng 5.14 và 5.15, như r2_hinhbang đề xuất.
- HD-05: còn đúng (`5_Experiments.tex:12`, tr. 30: "trình bày các thực nghiệm theo thứ tự thời gian"; Mục 5.12 có 20 tiểu mục, tr. 55–77; Bảng 5.18 ở tr. 55). Điều kiện bổ sung theo r2_logic: khi chuyển các mục về mạng cũ sang phụ lục, giữ lại ở thân bài hoặc ở mục Hạn chế ba ý sau: ngưỡng va chạm không được tính lại, mục tiêu M9 (chặn làn rẽ phải) suy từ thiết lập có cọc, và kết luận tự bác của 5.12.12.
- HD-06: còn đúng. Ch5 kết thúc ở tr. 88, sau đó là 9 trang bảng trôi (tr. 89–97). Bảng 5.17 (B0, B1 so với dữ liệu) được bàn ở tr. 53–54 nhưng in ở tr. 96. Bảng 5.12 (sáu phương án) được dẫn ở tr. 45 nhưng in ở tr. 96. Bảng 2.2 vẫn đứng riêng ở tr. 11, sau đoạn kết Ch2 (tr. 10).
- HD-07: còn đúng (tóm tắt không đổi, tệp PDF tr. 3–4). Cần sửa lại câu viết lại của tôi theo r2_logic và r2_giaothong. Chỉ nêu vượt đèn đỏ (0% lên 4,86%), vì B0 đã có 4,00 xe chờ giữa nút mỗi chu kỳ (LG-03). Viết `accel` là "yếu tố lớn nhất trong các biến thể B1 đã thử ở PROXY_D1", không phải nguyên nhân của cả ba chiến dịch (LG-01). Ý (3) sửa theo HD-02 ở trên.
- HD-08: còn đúng (Mục 4.8, tr. 29; tóm tắt; tr. 71–72). Tôi rút tên "bộ lọc an toàn" theo r2_giaothong, vì "va chạm" của SUMO là chồng lấn hình học, không phải chỉ số an toàn. Tôi dùng tên của r2_logic: "đạt tiêu chí chấp nhận (ổn định và va chạm mô phỏng)".
- HD-09: cần sửa lại phạm vi. Theo khung GVHD, việc Ch4 (ý tưởng, `4_Rule_execution.tex:15`, tr. 24) và 5.2.1 (phần riêng của SUMO, `5_Experiments.tex:200`, tr. 35) cùng nói về bộ kiểm tra hợp lệ là chủ ý, nên chấp nhận được, với điều kiện 5.2.1 chỉ nêu phần riêng của SUMO: tên mã lỗi, `lcPushy`/`lcPushyGap`. Lặp thật sự còn ở ba chỗ: 5.3.1 (`:273`, tr. 37), Bảng 5.6, 5.7 (tr. 93–94), và 5.13 kể lại số của 5.12. Ví dụ, đoạn kết chương ở tr. 88 vẫn chép "sức chứa 8 xe" của mạng cũ (LG-14).
- HD-10: đã hết. Mục 3.1 (tr. 12) nay nói "hai phần". Ch4 chứa cả kiểm tra hợp lệ và chỉ số, khớp Hình 1.1. Ch3 và Ch4 không còn tham chiếu tới nhật ký thực nghiệm; grep chỉ thấy `3_Rule_generation.tex:139` trỏ tới Bảng 5.4 (miền giá trị), chấp nhận được. Tôi đồng ý với r2_logic, r2_hinhbang và r2_giaothong.
- HD-11: còn đúng (`6_Conclusions.tex:43–45`, tr. 100). Phải sửa theo r2_logic: bỏ cụm "chính lỗi này chặn mọi chiến dịch". Viết: "`accel` 1,1 m/s² chuyển từ IDM là giá trị chuyển giao chưa kiểm chứng, và là yếu tố lớn nhất trong các biến thể đã thử; riêng nó chưa giải thích hết số xe chờ chèn." Bổ sung vào danh sách hạn chế các ý sau: G0 (cổng GEH) tính trên số đếm 15 phút (GT-05); chỉ một LLM 9B, nhiệt độ 0,7, mỗi chiến dịch chạy một lần (HV-18); chỉ phủ 07:30–08:00 (LG-07).
- HD-12: còn đúng (Mục 5.6 ở tr. 44–45, 5.12.16 ở tr. 73, 5.12.18 ở tr. 75–76; Bảng 5.11, 5.32, 5.33). Câu trích "mọi lỗi là lỗi cấu trúc" phải đọc cùng LG-12.
- HD-13: còn đúng (`1_Introduction.tex:20`, tr. 2; Ch2 tr. 7–11). OPRO, FunSearch và Eureka nay có ở Mục 3.6.1 (tài liệu [20]–[22]) nhưng Ch2 vẫn chưa có (HV-14).
- HD-14: còn đúng (`1_Introduction.tex:92`, tr. 5; `3_Rule_generation.tex:57`, tr. 15; `5_Experiments.tex:112`, tr. 32–33).
- HD-15: còn đúng (`4_Rule_execution.tex:103`, tr. 29; `3_Rule_generation.tex:57`, tr. 15; `6_Conclusions.tex:45`, tr. 100; tóm tắt ở tệp PDF tr. 4 và 6).
- HD-16: còn đúng ("F2" là nhóm hành vi ở tr. 30 và là tên mạng ở Bảng 5.18, tr. 55; danh mục viết tắt vẫn có 6 mục, tr. vi). Cần sửa lại tên tôi đề xuất cho "dữ liệu đại diện": rút "dữ liệu giả lập từ tài liệu" (xem Mâu thuẫn 2). Về tên mạng, đồng ý N1–N6 như r2_logic và r2_hinhbang.
- HD-17: còn đúng. Mục lục ghi "TÀI LIỆU THAM KHẢO…104" (tệp PDF tr. 12), nhưng trang tiêu đề danh mục tài liệu là tr. 102.
- HD-18: còn đúng một phần. Bảng 2.2 đứng một mình ở tr. 11. Hình 5.4, 5.5 (tr. 57–58) có nhãn tiếng Anh. Log build2 còn 36 dòng tràn lề trên 2 pt. Tôi chưa kiểm lại từng trang gần trắng trên build2.

## B. Phản biện chéo

### Đồng ý

Người đọc (ND):
- ND-02, ND-04: đồng ý; trùng HD-06, HD-05, vẫn còn trên build2.
- ND-03: đồng ý. Tên mạng được dùng từ tóm tắt và tr. 30, trong khi bảng định nghĩa (Bảng 5.18) mãi tới tr. 55 mới có.
- ND-05: đồng ý. Thêm đoạn "khái niệm cơ bản" vào Mục 2.2 là đúng chỗ theo khung chương. Nếu thiếu, người đọc không hiểu vì sao giá trị `a` của IDM không dùng được làm `accel` của Krauss.
- ND-06: đồng ý. "Xe chờ chèn" có mặt trong tiêu chí (ii) ở tr. 29 mà không có định nghĩa.
- ND-07: đồng ý về vấn đề. Câu mẫu cần sửa theo r2_logic (ngưỡng suy từ B0 trên mạng cũ, không phải mạng đang dùng).
- ND-08 đến ND-12, ND-14 đến ND-19: đồng ý. ND-09 (giải thích speed mode ở lần dùng đầu tại 5.2, đưa Bảng 5.36 lên) nằm đúng trong Ch5 và hợp khung.

Văn phong (VP):
- VP-01: đồng ý. Đây là gốc của HD-05. Nên đổi tên các tiểu mục của 6.1 thành "Kết quả đạt được, Hạn chế, Hướng phát triển".
- VP-02, VP-03, VP-04, VP-05, VP-09, VP-11, VP-12 đến VP-17: đồng ý. VP-09 (5.2 có mục "a, b" đứng trước 5.2.1) còn đúng trên build2: mục lục cho thấy 5.2 ở tr. 33, còn 5.2.1 tới tr. 35 mới bắt đầu.
- VP-06: đồng ý, hạ xuống mức nhỏ. Cần một tên duy nhất cho B0 ("cấu hình SUMO mặc định (B0)") là quan trọng nhất, vì LG-03 cho thấy B0 không phải "mô hình chuẩn" theo nghĩa của Ch1.
- VP-07: đồng ý (xem Mâu thuẫn 2).
- VP-10: đồng ý, mức nhỏ.

Hình bảng (HB):
- HB-02, HB-03, HB-06, HB-08, HB-10, HB-11, HB-13, HB-14, HB-15, HB-18, HB-20: đồng ý, đều còn đúng trên build2.
- HB-04, HB-05: đồng ý. Hình 5.1 và 5.4 trên build2 vẫn có nhãn tiếng Anh và mã OSM (tr. 31, 57).
- HB-07: đồng ý. Log build2 vẫn có 36 dòng tràn lề trên 2 pt.
- HB-09: đồng ý, hạ xuống mức nhỏ. Kiểm tra mẫu SoICT trước khi đổi toàn bộ 54 bảng sang `booktabs`.
- HB-12: đồng ý, trùng HD-04.
- HB-16: đồng ý. Các phương trình cho $d$, $R$, $S$ nên đặt ở 4.7.2, vì Ch4 là chương ý tưởng nên đúng chỗ.
- HB-17: đồng ý với listing đặc tả B1 trong phụ lục. Hình kiến trúc chỉ nên làm nếu nó thay thế Bảng 5.8 và 5.9, để Ch5 không dài thêm.
- HB-19: đồng ý; giới hạn 200–350 từ của mẫu là thêm một lý do cho HD-07.

Logic (LG):
- LG-01, LG-02: đồng ý; tôi đã sửa HD-02, HD-07, HD-11 theo hai nhận xét này.
- LG-03: đồng ý, mức nghiêm trọng. Đây là lỗi cấu trúc lập luận: khoảng trống nghiên cứu nêu ở Ch1 (tr. 2) và Bảng 2.2 (tr. 11) bị chính Bảng 5.17 bác một phần.
- LG-04: đồng ý. Câu ở `1_Introduction.tex:67` (tr. 4) mâu thuẫn với quy tắc chọn dự phòng ở Mục 5.8.3.
- LG-05 đến LG-10, LG-12, LG-13, LG-16 đến LG-20: đồng ý.
- LG-11: đồng ý, còn đúng. Bảng 5.1 (tr. 89) ghi "(Mục 3.5)", nhưng 3.5 là "Biểu diễn luật". Bảng 2.2 ghi "11 hành vi (Mục 1.4)".
- LG-14: đồng ý; câu đó vẫn ở đoạn kết Ch5 (tr. 88).
- LG-15: đồng ý. Nếu không nêu được mô hình nào đã sinh chiến dịch P2 trên mạng 28/10, thì bỏ Bảng 5.31 và mọi số liệu lấy từ chiến dịch đó.

Học viên (HV):
- HV-02, HV-03, HV-04, HV-07 đến HV-15, HV-17 đến HV-20: đồng ý. HV-02 cần sửa câu viết lại theo LG-01, LG-03, LG-12 (giống HD-07).
- HV-05: đồng ý với phương án viết lại 5.13 thành mục ngắn, ghi rõ phần nào SUMO có sẵn, phần nào tác giả thêm vào.
- HV-06: đồng ý. Phát biểu hình thức ($\theta = (\sigma, \varphi)$, min $S$ với ràng buộc) nên đặt ở Mục 3.1, vì đó là mức ý tưởng. Ch1 chỉ giữ văn xuôi.
- HV-18: đồng ý, mức nghiêm trọng hơn HV ghi. Mọi kết luận về LLM gắn với một mô hình 9B duy nhất, nên lý do chọn mô hình phải có ở Ch1 hoặc Mục 3.6.

Giao thông (GT):
- GT-02: đồng ý, mức nghiêm trọng. Tôi đã kiểm lại. Tr. 31 viết "Đi thẳng hoặc rẽ trái trên làn này khi đèn xanh là đúng luật", trong khi Bảng 5.1 (tr. 89) viết "Rẽ trái và quay đầu chỉ có kết nối từ lane 2". Hai câu mâu thuẫn trực tiếp.
- GT-03, GT-04, GT-06, GT-07, GT-09, GT-10, GT-12, GT-14 đến GT-18, GT-21: đồng ý.
- GT-05: đồng ý. Đây là lỗi trình bày "khẳng định mạnh hơn bằng chứng": trích dẫn TAG khiến người đọc tưởng đã đạt chuẩn TAG.
- GT-08: đồng ý, trùng LG-07.
- GT-11: đồng ý. Định nghĩa vận hành chung đặt ở Bảng 4.1. Các con số riêng của nút, như phạm vi 80 m, đặt ở Ch5.
- GT-13: đồng ý, mức nên sửa.
- GT-19: đồng ý dùng "ngày kiểm định". Về tên dữ liệu, xem Mâu thuẫn 2.

### Phản đối

- ND-01, HB-01, HV-01 (bìa): phản đối cách xếp "sót từ mẫu" và cách sửa "thay bằng tên thật". Tôi cũng tự rút HD-01 với cùng lý do: đây là tên đăng ký, việc đổi phải qua GVHD hoặc phòng đào tạo. Phần `\TITLE`/`pdftitle` của HB-01 và HV-01 vẫn đúng.
- ND-13 (ví dụ một xe chạy xuyên suốt): phản đối vị trí "cuối Chương 4". Ví dụ ND viết dùng HDT_S, `moto_violator`, `custom1`, tức chi tiết của nút và của SUMO. Đặt ở Ch4 sẽ phá khung GVHD (Ch3–4 chỉ trình bày ý tưởng). Đặt ví dụ này ở đầu Mục 5.2, ngay sau Bảng 5.2. Nếu muốn có một ví dụ ở Ch4 thì viết ở mức khái niệm, không có tên nhánh và không có vClass.
- VP-08 (bỏ đoạn tóm tắt cuối Ch2, Ch3, Ch4): phản đối một phần. Mỗi chương cần một đoạn kết 2–3 câu nói chương đã xác lập điều gì và chương sau dùng nó thế nào. Đó là chỗ nối mạch. Tôi đồng ý cắt phần liệt kê lại các mục, và sửa đúng chỗ lặp nguyên văn giữa cuối Ch2 (tr. 10) và đầu Ch3 (tr. 12). Đồng ý bỏ `5_Experiments.tex:1420` (tr. 87).
- HV-16, phương án "bỏ hẳn 5.13, đưa Bảng 5.35 vào 1.5": phản đối, cùng lý do với r2_hinhbang. Bảng 5.35 gắn với SUMO (bề rộng làn ra, speed mode, `custom1`), nên đưa lên Ch1 là kéo chi tiết hiện thực vào chương mở đầu. Ch1 theo khung GVHD chỉ đi từ lợi ích, qua "tuy nhiên", tới hướng giải quyết.
- GT-01, phần "bỏ hành vi 7 khỏi Bảng 3.1, bỏ M10 (đi trên vỉa hè) và lựa chọn `sidewalk`": phản đối đưa vào bản nhận xét như một đề xuất sửa. Đây là quyết định phạm vi, không phải lỗi trình bày. Luận văn hiện mô hình hóa vỉa hè đầy đủ (Bảng 5.1, tr. 89) và Hình 5.2 có vẽ nó. Phần trình bày cần sửa chỉ là: Mục 1.4.2 (tr. 5) phải nói rõ hành vi 8 (đi ngược chiều) bị loại kèm lý do. Đổi chữ "hoãn" thành "ngoài phạm vi" thì tôi đồng ý, nếu tác giả chốt như vậy.
- ND-02 và GT-03, phần "đặt `[H]` cho mọi bảng": phản đối, xem Mâu thuẫn 4.

### Mâu thuẫn

1. **Đánh số làn.** GT-20 đề xuất "làn 1/2/3 tính từ lề phải". VP-05 và ND-15 đề xuất giữ "làn 0/1/2", định nghĩa một lần. Tôi nghiêng về VP-05 và ND-15. Khóa cấu hình (`violator_turn_lanes`), Bảng 5.1, Hình 5.6 và hơn 40 chỗ trong Ch5 đều dùng chỉ số từ 0, nên đánh số lại sẽ dễ lệch một đơn vị. Điều kiện: định nghĩa ở Mục 5.1.3 kèm ba làn vẽ trên Hình 5.2 (GT-03), và chỉ dùng chữ Việt "làn 0".
2. **Tên thay cho "dữ liệu đại diện".** VP-07 đề xuất "dữ liệu thay thế", GT-19 đề xuất "dữ liệu tổng hợp", HD-16 đề xuất "dữ liệu giả lập từ tài liệu". Tôi rút đề xuất của mình, vì "giả lập" dễ lẫn với đầu ra mô phỏng. Tôi nghiêng về VP-07, đồng ý với r2_giaothong và khác với r2_logic, r2_hinhbang. Lý do: luận văn đã có một bộ dữ liệu khác tên SYNTHETIC, chỉ dùng để thử đường ống (tr. 59, tr. 83), mà "synthetic" dịch thẳng là "tổng hợp". Gọi PROXY là "dữ liệu tổng hợp" sẽ trùng nghĩa với SYNTHETIC. Đề xuất: "dữ liệu thay thế (dựng từ tài liệu)", định nghĩa một lần ở Mục 1.4.2.
3. **Số phận Mục 5.13.** HD-09 đề xuất rút gọn, HV-05 đề xuất viết lại thành "hiện thực các đóng góp", HV-16 đề xuất bỏ hẳn. Tôi nghiêng về gộp HD-09 với HV-05: giữ trong Ch5, mỗi giải pháp 2–3 câu, trỏ tới bằng chứng ở 5.12, và ghi rõ phần nào SUMO có sẵn.
4. **Vị trí float.** ND-02 và GT-03 đề xuất `[H]` cho mọi bảng. HB-02, HB-08, HV-09 và HD-06 đề xuất `[!htbp]` kèm `placeins`. Tôi nghiêng về `[!htbp]` + `\usepackage[section]{placeins}` + `\raggedbottom`, và chỉ dùng `[H]` cho bảng ngắn. Lý do: dùng `[H]` cho bảng cao chính là nguyên nhân của các trang nửa trắng (HB-08). Bảng 5.1 và 5.4 nên rút gọn.
5. **Tóm tắt nêu kết quả dương nào.** HD-07 và HV-02 đề xuất nêu vượt đèn đỏ và xe chờ giữa nút. LG-03 và r2_logic chỉ chấp nhận vượt đèn đỏ. Tôi nghiêng về LG-03: chỉ nêu vượt đèn đỏ, kèm một mệnh đề nói hành vi 10 có ở cả B0, vì nó đến từ bản vá mạng.

### Bỏ sót

1. **Thiết kế so sánh được dùng trước khi định nghĩa, và nằm sai tầng.** Ch2 (tr. 10) viết "phương án đối sánh B2 (Mục 5.7)". Đoạn mở Ch5 (tr. 30) và 5.2.1 (tr. 35) dùng B2, P1, P2 và "chế độ P1". Định nghĩa B0–H và E1/E2 tới Mục 5.7 (tr. 45) mới có, sau 15 trang cài đặt, còn Bảng 5.12 thì trôi tới tr. 96. Phần này không có gì riêng của nút giao: sáu phương án ở mức khái niệm, E1/E2, kiểm định Mann–Whitney. Nó tiếp nối trực tiếp Mục 3.6.3 "Hai chế độ". Đề xuất: chuyển phần ý tưởng của thiết kế so sánh thành mục cuối Ch4 (hoặc nối sau 3.6.3). Ch5 chỉ giữ cấu hình cụ thể (ngân sách 36 lần chạy, seed, ngày dữ liệu). Cách này nằm trong khung GVHD và rút ngắn Ch5.
2. **Kết luận Ch6 vẫn báo cáo kết quả trên các mạng đã bỏ.** Mục 6.1.4 (`6_Conclusions.tex:37`, tr. 99) mở đầu bằng B2 trên mạng F2 và hai mạng 28/10, sau đó mới đến mạng 04/11. Chương kết luận chỉ nên nói về kịch bản cuối. Lịch sử các mạng gói trong một câu: "kịch bản được cập nhật theo khảo sát hiện trường; kết quả dưới đây trên phiên bản cuối".
3. **Đoạn kết Ch5 cách xa phần kết quả.** Phần kết quả kết thúc ở 5.12.20 (tr. 77). Sau đó 5.13 và 5.14 chen 11 trang trước đoạn kết chương (tr. 88), và đoạn kết này lặp lại gần hết 6.1.3–6.1.4. Đề xuất: sau 5.12, đặt một đoạn "Tóm tắt kết quả" 4–5 câu trả lời từng câu hỏi nghiên cứu (HD-03). Đoạn kết Ch5 chỉ còn câu nối sang Ch6.
4. **Hình 1.1 chưa làm được bản đồ đọc.** Chú thích hình (tr. 3) gán "các bước 1–4" cho Chương 4, nhưng bước 5 (phản hồi) nằm ở Mục 3.7, và các ô không ghi số mục. Mục 1.6 "Bố cục" chỉ là văn xuôi. Đề xuất: ghi số mục lên từng ô (sinh luật 3.6, kiểm tra 4.1, biên dịch 4.2, thực thi 4.3–4.5, chỉ số 4.6–4.8, phản hồi 3.7). Khi đó Hình 1.1 là sơ đồ của Ch3–4, và người đọc thấy ngay ranh giới hai chương theo khung GVHD.
5. **Mục 1.5 (đóng góp) tự thừa nhận phần chưa có nhưng không nói đóng góp nào bị ảnh hưởng.** Câu cuối Mục 1.5 (tr. 5) viết "Đánh giá cuối … vẫn là phần dự kiến", nhưng không nói đóng góp 4 (khung so sánh công bằng) mới được kiểm chứng ở mức "chạy hết ngân sách", chưa ở mức "so sánh được". Đề xuất: mỗi đóng góp ghi một mệnh đề về mức kiểm chứng hiện có, ví dụ "đã kiểm thử tự động", "đã chạy trên dữ liệu thay thế", "chưa đánh giá cuối". Như vậy Ch6 trả lời đúng theo từng đóng góp.
