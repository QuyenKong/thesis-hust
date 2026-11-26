# Biên tập văn phong, vòng 2

Quy ước vị trí. Dòng `.tex` theo nguồn hiện tại. Số dòng không đổi so với vòng 1, vì vòng 1 tôi đã đọc nguồn sau khi tái cấu trúc. "tr. N" là số trang in trên bản build2; trang trong tệp PDF bằng N + 18. Tóm tắt không có số trang in nên ghi "PDF tệp N". Chỗ nào có dấu "~" là trang ước theo mục lục, tôi chưa mở trang đó để kiểm.

## A. Tự kiểm lại

- VP-01: còn đúng, nhưng cần sửa lại đề xuất. Vị trí: 5:951 (tr. 66), 5:1089 (tr. 71), 5:1047–1049 (tr. 69–70), 5:665 (~tr. 52), 6:17/27/43 (tr. 98–100), 0_3:15 (PDF tệp 3–4), Appendix_B:22, 36 (tr. 112). Có hai chỗ sửa.
  - Tên phiên bản mạng: đổi đề xuất V1–V6 thành N1–N6, theo r2_logic và r2_hinhbang. Chữ "v" đã dùng cho phiên bản prompt `v001`–`v005` và cho biến thể luật v1–v3 (Bảng 5.29).
  - Câu viết lại cho 6:27: không gọi B0 là "cấu hình SUMO mặc định", vì LG-03 chỉ ra B0 chạy trên mạng có bản vá. Bản mới: "Hai phiên bản mạng N5 và N6 chỉ khác nhau ở các kết nối dành cho xe vi phạm xuất phát từ làn 0 và làn 1. Bỏ các kết nối này làm va chạm trên làn của cấu hình cơ sở B0 giảm từ 18,53 xuống 1,87 va chạm/giờ, dù không xe nào của B0 đi qua chúng. Cơ chế của ảnh hưởng này chưa xác định."
- VP-02: còn đúng. Vị trí: 4:103 (tr. 29, đã mở trang), 0_3:17 (PDF tệp 4), 0_4:17 (PDF tệp 6), 3:57 (tr. 15), 5:400 (~tr. 43), 5:710 (~tr. 55), 5:1341 (~tr. 82), 5:1418 (~tr. 86), 6:45 (tr. 100).
- VP-03: còn đúng. 5:23 (tr. 30), 5:172 (tr. 34, "nhóm F2"), 5:922 (~tr. 65), 5:596 (~tr. 50); 6:31, 6:53, 6:57, 6:59 (tr. 99–101). Riêng 6:59 "thí nghiệm 3B" vẫn để trơ (tr. 101, đã mở trang).
- VP-04: còn đúng, nhưng cần sửa lại câu viết lại.
  - Bản tiếng Việt: theo r2_giaothong, đổi thành "vì mạng mô phỏng không phục vụ hết nhu cầu đại diện". Ngành nói "phục vụ nhu cầu", không nói "thông qua nhu cầu".
  - Bản tiếng Anh: theo LG-03 và LG-06, viết lại thành: "the baseline (SUMO default vehicle types on the patched network, no TraCI rules) meets all acceptance criteria in 15 of 15 runs, with collision thresholds derived from this same baseline".
  - Tên thuật ngữ: đổi "acceptance criteria / tiêu chí chấp nhận" thành "tiêu chí chấp nhận (ổn định và va chạm)", theo r2_logic.
- VP-05: còn đúng. 5:890 (~tr. 64), 5:1144 (tr. 73), 5:867 (tiêu đề 5.12.6, tr. 62), 5:870 (tr. 62), 5:468 (~tr. 45). r2_giaothong đề xuất gọi làn theo chức năng. Tôi giữ "làn 0/1/2" và trả lời ở mục Mâu thuẫn.
- VP-06: còn đúng, nhưng cần sửa lại một ý. Không gọi B0 là "cấu hình SUMO mặc định (B0)" như tôi đề xuất ở vòng 1. Gọi là "cấu hình cơ sở B0 (vType mặc định, không luật TraCI, trên cùng mạng có bản vá)", vì B0 đã có xe chờ giữa nút nhờ bản vá (LG-03). Hình 1.1 (1:56, tr. 3) cũng in chữ "mã xác định", nên phải sửa cả trong hình.
- VP-07: còn đúng. Về tên mới: r2_logic và r2_hinhbang chọn "dữ liệu tổng hợp từ tài liệu", r2_giaothong rút đề xuất đó và theo VP-07. Tôi giữ "dữ liệu thay thế". Lý do kèm bằng chứng nằm ở mục Mâu thuẫn 2.
- VP-08: còn đúng. 2:104 (tr. 11), 3:8 (tr. 12), 3:217 (tr. 23), 4:118 (tr. 29, đã mở trang), 5:1420 (tr. 87, đã mở trang), 5:1437 (tr. 88, đã mở trang), 6:9 (tr. 98).
- VP-09: còn đúng. Đã mở tr. 33–34: "a, Tham số tĩnh", "b, Luật có điều kiện" vẫn nằm thẳng dưới 5.2.
- VP-10, VP-11: còn đúng, vị trí như vòng 1. 5:1269 (~tr. 78), 5:1377 (~tr. 84), 5:200 (tr. 35), 5:12 (tr. 30).
- VP-12: còn đúng, nhưng cần sửa lại câu viết lại cho 3:47. r2_giaothong chỉ đúng một lỗi: Saval và cộng sự không đo vượt đèn đỏ, còn Gao và cộng sự đo xe đạp điện. Câu viết lại mới: "Bốn nghiên cứu cho bốn khía cạnh của hành vi vượt đèn đỏ. Hai nghiên cứu đo trên video xe máy, một nghiên cứu là mô hình, một nghiên cứu đo trên xe đạp điện."
- VP-13: còn đúng. 2:66 (tr. 9), 5:119 (tr. 33, đã mở trang), 5:1273 (~tr. 78).
- VP-14: còn đúng. Gộp với HB-11 thành một quy ước số chung, theo r2_hinhbang.
- VP-15: còn đúng. 5:1425 (tr. 87, đã mở trang: "trỏ tới thư mục cài đặt, Máy chính").
- VP-16: còn đúng. Danh mục viết tắt vẫn có 6 mục.
- VP-17: còn đúng. 4:64 (tr. 27); Bảng B.1 (tr. 112) có 7 tệp. Bổ sung theo r2_logic (Bỏ sót 4): 1:22 (tr. 2) liệt kê "quỹ đạo" là đầu vào, nhưng tầng quỹ đạo không có trong lược đồ (Appendix_B:36). Hai chỗ phải khớp nhau.
- Ghi chú vòng 1 về PDF lệch nguồn: đã hết. Build2 khớp nguồn.

## B. Phản biện chéo

### Bìa (HD-01, ND-01, HB-01, HV-01): phản đối cách gọi lỗi

Bốn nhận xét gọi tên trên bìa là chữ còn sót từ mẫu. Theo điều phối viên, "Mô hình thế giới vĩ mô trong trò chơi máy tính" là tên đề tài đã đăng ký chính thức. Nên ghi lại là "tên đăng ký lệch nội dung; tác giả cần hỏi GVHD hoặc phòng đào tạo về thủ tục đổi tên". Mức vẫn nghiêm trọng, vì hội đồng sẽ hỏi.

Tên mới mà HD-01 và ND-01 đề xuất ("Sinh và tinh chỉnh luật hành vi người lái…") dùng chữ "người lái". Trong khi đó văn bản dùng "tài xế" và "người tham gia giao thông" (VP-06). Nếu được đổi tên, nên chọn một trong hai chữ mà văn bản đang dùng.

### Đồng ý

- HD-02: Chương 6 để trống câu kết luận chính (tr. 100). Câu viết lại của HD-02 có lỗi, xem Phản đối 1.
- HD-03, HV-04: thiếu câu hỏi nghiên cứu. Đặt câu hỏi ở 1.4 là hợp với khung Chương 1 mà GVHD đã chốt (lợi ích, rồi vấn đề, rồi hướng giải quyết).
- HD-04, HB-12, HV-15: Chương 5 dài 68 trang (tr. 30–97). Chuyển phần tài liệu phần mềm sang phụ lục.
- HD-05, ND-04, HV-03: kết quả viết theo ngày, trùng VP-01. Xếp lại theo câu hỏi vẫn nằm trong khung, vì mọi việc diễn ra trong Chương 5.
- HD-06, ND-02, HB-02, HV-09: còn đúng. Bảng 5.1 in ở tr. 89, sau đoạn kết chương (tr. 88), trong khi tr. 31 đã nhắc tới nó.
- HD-09, HV-16: một nội dung kể lại nhiều lần. Về Mục 5.13, tôi theo r2_hinhbang chọn cách của HD-09.
- HD-11, LG-08, HV-11: Chương 6 thiếu mục Hạn chế. Câu rào đón "chưa cho biết mô phỏng giống…" lặp ít nhất 5 lần (0_3:17, 1:84, 5:437, 5:1366, 5:1437), đọc như lời phòng thủ.
- HD-12, HD-13, HD-14, GT-14, GT-15: đồng ý. Cả năm là vấn đề cách trình bày, không phải phương pháp.
- HD-15, ND-12, HB-03, HV-08: trùng VP-02.
- HD-17: còn đúng. Mục lục ghi Tài liệu tham khảo ở trang 104, thực tế bắt đầu ở tr. 102 (đã mở trang).
- ND-05, ND-06 (phần ý; chỗ đặt định nghĩa xem Phản đối 4), ND-08, ND-09, ND-11, ND-14, ND-16, ND-17, ND-18 (phần ý; tên gọi xem Mâu thuẫn 4), ND-19: đồng ý.
- HB-04 đến HB-11, HB-14 (phần ý), HB-15 đến HB-20: đồng ý. HB-18 còn đúng ở tr. 102–104: URL giãn chữ ("https : / / elib . dlr . de"), mục [5] in "traffic. an agent-based", mục [18] có "cập nhật ngày 28/05/2026" bằng tiếng Việt chen trong một mục tiếng Anh.
- HV-05, HV-07, HV-12, HV-13 (phần ý), HV-14, HV-17, HV-18, HV-20: đồng ý.
- LG-01 đến LG-19: đồng ý phần chẩn đoán. Mục này là phần sửa sai đáng giá nhất của vòng này, vì nó cho thấy nhiều câu viết lại của người khác (và một câu của tôi) khẳng định quá dữ liệu. LG-11 còn đúng: Bảng 5.1 (tr. 89) trỏ "lựa chọn cắt về … (Mục 3.5)", mà 3.5 là "Biểu diễn luật".
- GT-01 đến GT-21: đồng ý phần chẩn đoán. GT-20 đúng ở ba thuật ngữ: "năng lực thông qua" nên đổi thành "khả năng thông hành", "pha đỏ" thành "thời gian đỏ", "headway" thành "giãn cách thời gian". Đánh số làn xem Mâu thuẫn 3.

### Đã hết trên bản mới

- HD-10: đã hết. Chương 3 không còn trỏ sang nhật ký thực nghiệm. Grep tham chiếu từ 1–4 sang các nhãn kết quả chỉ còn 1:96 (trỏ tới bảy giải pháp). 3:13 đã ghi "hai phần", khớp Hình 1.1 và mục lục.
- Các ghi chú vị trí "PDF lệch nguồn" trong r1 của mọi người: đã hết.

### Phản đối (chủ yếu là câu viết lại)

1. **HD-02, HD-07, HV-02 (và HV "Chuẩn bị bảo vệ", ý 5): câu viết lại nói "mọi lỗi đều là lỗi cấu trúc".** LG-12 đúng. Ở P1, 14/15 lần thử hỏng là lỗi tổng tỷ trọng (5:1183), tức lỗi giá trị. Bảng lỗi P2 cũng có "giá trị ngoài miền" (5:1200). Chỉ được viết: "P2 mắc chủ yếu lỗi cấu trúc; P1 mắc chủ yếu lỗi tổng tỷ trọng".
2. **HD-07 (ý 2) và HV-02 (ý 1): "bộ thực thi tạo ra được vượt đèn đỏ và xe chờ giữa nút mà mô hình mặc định không có".** Câu này sai với chính Bảng 5.16 (5:690): B0 có 4,00 xe chờ giữa nút mỗi chu kỳ, B1 có 4,89. Chỉ vượt đèn đỏ là có ở B1 mà không có ở B0. Viết lại: "Luật vượt đèn đỏ qua bộ thực thi cho 4,86% xe máy vượt đỏ, trong khi B0 không có lượt nào; xe chờ giữa nút có ở cả hai, vì đến từ bản vá mạng."
3. **HD-07 (ý 4), HV-02 (ý 3), HV-13, ND-07: quy nhân quả "nguyên nhân là `accel`" cho mọi chiến dịch.** Khẳng định này mạnh hơn dữ liệu (LG-01, LG-05). P2 bị loại ở PROXY\_D2–D3 vì va chạm, không vì xe chờ vào mạng. Câu của HV-13 ("chuyển tham số IDM sang Krauss làm hỏng năng lực thông qua") vừa khẳng định quá dữ liệu, vừa dùng thuật ngữ sai (GT-20). Dùng câu viết lại của LG-01.
4. **ND-06 và ND-13: đặt định nghĩa và ví dụ có địa danh vào Chương 4.** Theo khung GVHD đã chốt, Chương 4 chỉ trình bày ý tưởng.
   - Ví dụ "khóa" của ND-06 ("M3, tỷ lệ vượt đỏ, xe máy, LVL") đặt ở 4.7.2 thì có tên nhánh của nút thật. Ví dụ phải chung: "M3 (vượt đèn đỏ), xe máy, một nhánh".
   - Đề xuất chuyển định nghĩa teleport lên Mục 4.8 sẽ đưa thuật ngữ riêng của SUMO vào chương ý tưởng. 4:112 đã có cách nói chung ("bị trình mô phỏng loại khỏi mạng vì kẹt"). Nên định nghĩa teleport ở đầu Chương 5 (5.8.3).
   - Khung ví dụ của ND-13 ("xe máy vào từ HDT\_S") chỉ đặt được ở Chương 5. Nếu đặt cuối Chương 4 thì phải bỏ địa danh.
5. **HD-08: "chạy hợp lệ".** Chữ "hợp lệ" đã dùng cho bộ kiểm tra đặc tả ("đặc tả hợp lệ", "tỷ lệ đặc tả hợp lệ") và cho cờ `valid_strict`. Dùng thêm cho tiêu chí chấp nhận lần chạy sẽ thành ba nghĩa. "Qua bộ lọc an toàn" thì hẹp hơn tiêu chí thật (r2_logic).
6. **LG-04, câu viết lại cho 1:67:** "tiêu chí này loại phần lớn các bộ luật dựa vào va chạm". Câu này lại khẳng định một điều chưa có số liệu, vì chính 5:922 viết "ngưỡng 142 va chạm trong nút/h gần như không loại lần chạy nào". Ở Chương 1 chỉ nên bỏ vế "nên một bộ luật không thể 'khớp' dữ liệu nhờ va chạm", rồi để giới hạn của quy tắc dự phòng vào mục Hạn chế ở Chương 6.
7. **HV-06: ký hiệu θ = (σ, φ).** σ đã có hai nghĩa trong luận văn: sai số ước lượng của `queue_space_seeking` (3:123, Bảng 3.2) và thuộc tính `sigma` của SUMO (Bảng 5.3, Phụ lục A). Thêm σ = "cấu trúc" là nghĩa thứ ba. Nên dùng ký hiệu khác, ví dụ $\mathcal{C}$ cho cấu trúc, $\theta$ cho tham số. Ký hiệu "eligible(θ)" cũng nên đổi thành ký hiệu toán, ví dụ $\theta \in \Theta_{\text{chấp nhận}}$.
8. **HV-08: đổi "Phase 3A–3D" thành "Thí nghiệm khả thi cho nhóm tìm khoảng trống (3 thí nghiệm + 1 kiểm tra)".** Câu này sai nội dung. Thí nghiệm 3D là về xe chờ giữa nút (hành vi 10, nhóm tương tác trong nút) (5:884). Đề xuất của ND-10 ("thí nghiệm khả thi 3A–3D") đơn giản hơn và đúng.
9. **HD-16: đổi "Phase" thành "KT1–KT4".** Cách này đổi một mã nội bộ lấy một mã mới. Văn bản vốn đã viết "3A", "3B" (6:59), nên bỏ chữ "Phase" là đủ.
10. **HB-14, caption mẫu:** "Teleport kẹt và va chạm của bộ luật thủ công B1 khi bỏ từng thành phần, ngày đại diện PROXY\_D2". Caption này dùng "bộ luật thủ công", tên mà VP-06 và ND-18 đề nghị bỏ, đồng thời giữ "ngày đại diện". Viết lại sau khi chốt thuật ngữ, ví dụ: "Teleport kẹt và va chạm của bộ luật viết tay B1 khi bỏ từng thành phần (ngày PROXY\_D2)."
11. **ND-03, câu mẫu (1):** "mỗi phiên bản mạng được gọi theo ngày dựng". Câu này giữ nguyên cách gọi mạng theo ngày, trái với đề xuất (2) của chính ND-03 và với VP-01.

### Mâu thuẫn

1. **"Đủ điều kiện" đổi thành gì.** HD-08 ("qua bộ lọc an toàn", "chạy hợp lệ"), ND-07 ("được chấp nhận"), VP-04 ("đạt tiêu chí chấp nhận"), r2_logic ("đạt tiêu chí chấp nhận (ổn định và va chạm)"). Tôi nghiêng về cách của r2_logic. Nó đủ rộng để bao cả G0 (cổng GEH lưu lượng) và điều kiện không còn xe chờ vào mạng, và không trùng chữ "hợp lệ" (Phản đối 5).
2. **Tên thay cho "dữ liệu đại diện".** VP-07 và r2_giaothong chọn "dữ liệu thay thế"; GT-19 vòng 1, r2_logic và r2_hinhbang chọn "dữ liệu tổng hợp từ tài liệu"; HD-16 chọn "giả lập". Tôi giữ "dữ liệu thay thế". Bằng chứng: luận văn đã dùng "tổng hợp" theo nghĩa *synthetic, tùy ý*.
   - 5:321 viết "kiểm thử tự động … trên dữ liệu tổng hợp nhỏ".
   - 5:745 viết "Nhu cầu tổng hợp riêng cho thí nghiệm".
   - 5:1348 còn viết "Số liệu tổng hợp tùy ý không kiểm tra được quy trình ở độ lớn thực" để *phân biệt* chính các ngày PROXY với loại số liệu đó.
   - Luận văn còn có một bộ dữ liệu khác tên SYNTHETIC (5:808, 5:1352).

   Gọi các ngày PROXY là "dữ liệu tổng hợp" sẽ đồng nhất chúng với thứ mà 5:1348 đang bác. Phản bác "thay thế không nói nguồn" của r2_logic giải quyết được bằng định nghĩa một lần: "dữ liệu thay thế: dựng từ số liệu đã công bố ở nút khác và từ giả định". r2_giaothong thêm một lý do từ phía ngành: "số liệu tổng hợp" thường hiểu là số liệu đã gộp.
3. **Đánh số làn.** VP-05, ND-15, r2_logic và r2_hinhbang chọn "làn 0/1/2" định nghĩa một lần; GT-20 chọn "làn 1/2/3 từ lề phải"; r2_giaothong chọn tên chức năng. Tôi nghiêng về "làn 0/1/2", kèm hình và định nghĩa ở 5.1.3. Lý do: chỉ số này trùng khóa cấu hình `violator_turn_lanes`, cột lược đồ và các bảng. Tên chức năng ("làn sát lề phải") hợp với văn xuôi mô tả, nhưng quá dài khi lặp 44 lần, ví dụ trong "quay đầu từ làn 0 và làn 1". Cách dung hòa: lần đầu ghi cả hai, "làn 0 (làn sát lề phải, làn rẽ phải liên tục ở 30 m cuối)".
4. **Tên của "xe chờ chèn".** ND-18 giữ "xe chờ chèn"; GT-20 đề xuất "xe chưa vào được mạng (nhu cầu bị dồn ở điểm sinh xe)"; VP-06 đề xuất "xe chờ vào mạng". Tôi nghiêng về "xe chờ vào mạng", và lấy câu giải thích của GT-20 làm định nghĩa ở lần dùng đầu. "Chèn" là dịch từng chữ của *insertion* trong SUMO. Cụm của GT-20 đúng nhưng dài quá để lặp 25 lần.
5. **Tên phiên bản mạng.** V1–V6 (VP-01), v1…v6 (HV-03), N1–N6 (HD-16, ND-03). Tôi rút V1–V6 và theo N1–N6 (xem A, VP-01).
6. **Số chữ số thập phân của S.** HB-11 muốn 3 chữ số; HV-19 và LG-17 muốn 2. Tôi nghiêng về 3 chữ số trong bảng, vì bảng phải khớp với Phụ lục A.3, và 2 chữ số trong văn xuôi của Tóm tắt và Chương 6, kèm độ lệch chuẩn của B0 trên 15 lần chạy làm thước đo nhiễu. Ghi quy tắc này một lần.
7. **Hai mục a, b ở 5.2.** HB-13 cho phép đổi thành "đoạn chạy in đậm"; VP-09 đề xuất `\subsection`. Tôi giữ `\subsection`. Chương 5 đã có 91 nhãn in đậm đầu đoạn, không nên thêm.
8. **Mã F1–F3.** ND-10 đưa F1–F3 vào bảng tra cứu; VP-03, HD-16 và r2_hinhbang đề nghị bỏ. Tôi giữ đề nghị bỏ. Đưa vào bảng tra cứu thì vẫn còn "F2" mang hai nghĩa.

### Bỏ sót (tối đa 5)

1. **Ký hiệu mang nhiều nghĩa.**
   - $p$ chỉ ít nhất bốn thứ: xác suất vượt đỏ trong phương trình (3.1), xác suất của `early_start`, xác suất của `uturn_bypass` (Bảng 3.2, 3:149–154), và phân vị trong $p_{90}$ (5:856, 5:920).
   - $\sigma$ (sai số ước lượng, 3:123) trùng với thuộc tính `sigma` của SUMO (Bảng 5.3, Appendix_A:21).

   HB-16 chỉ bắt được $t_{\text{before}}$. Đề xuất: dùng chỉ số dưới theo luật ($p_{\text{early}}$, $p_{\text{bypass}}$), viết phân vị là "phân vị 90", và đổi sai số ước lượng thành $\varepsilon$.
2. **Tiêu đề lặp tên cấp trên** (skill mục 20).
   - Chương 6 "KẾT LUẬN" có mục 6.1 "Kết luận" (6:11, tr. 98).
   - Phụ lục B "LƯỢC ĐỒ DỮ LIỆU QUAN SÁT" có đúng một mục B.1 cùng tên (Appendix_B:5, tr. 112).
   - Tên Phụ lục A "MIỀN THAM SỐ, BỘ LUẬT B1 VÀ …" để trơ mã B1 trong tiêu đề (main.tex:288).

   Đề xuất: đổi 6.1 thành "Kết quả đạt được"; bỏ tiêu đề B.1; thay "B1" bằng "bộ luật viết tay".
3. **"Phương án" mang hai nghĩa.** Chương 1 dùng "phương án" cho phương án thiết kế nút ("so sánh các phương án hình học", 1:9; "đánh giá quá cao phương án đang thử", 1:11). Chương 5 dùng "sáu phương án" cho B0–H (5:477). Một số câu viết lại của người khác ("ba phương án hiệu chỉnh", ND-07) chồng thêm nghĩa thứ ba. Đề xuất: với B0–H, dùng "cấu hình so sánh" hoặc giữ "phương án đối sánh" đầy đủ, không rút gọn thành "phương án".
4. **Mục tiêu viết bằng cụm mơ hồ "giống nhất có thể".** Cụm này có ở 0_3:11, 0_4:11 ("as closely as possible"), 1:22 và 6:15. Đây là câu khẩu hiệu, không đo được. Luận văn đã có thước đo (khoảng cách giữa chỉ số mô phỏng và quan sát), nhưng phần phát biểu bài toán không nối tới nó. Viết lại 1:22: "…sao cho sai lệch giữa các chỉ số hành vi tính từ mô phỏng và từ dữ liệu quan sát là nhỏ nhất, trong khi lần chạy vẫn ổn định và không va chạm quá ngưỡng." Câu này không nêu số hiệu chỉ số, nên vẫn hợp với Chương 1.
5. **Tiêu đề cột bảng trộn tiếng Anh và chữ viết tắt.** Có "Min", "Max" (Appendix_A:16, 39), "Chờ TB", "p90", "Max" (5:756), "Lane 0" (5:726), và `valid_strict` làm tiêu đề cột (5:837). Đề xuất: "Cận dưới", "Cận trên", "Trung bình", "Phân vị 90", "Lớn nhất", "Làn 0". Tên cờ chỉ để trong thân bảng hoặc chú thích.
