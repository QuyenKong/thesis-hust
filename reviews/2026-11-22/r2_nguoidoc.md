# Người đọc ngoài chuyên ngành — Vòng 2

Căn cứ: nguồn 6 chương hiện có trên đĩa và PDF `build2/main.pdf` (131 trang). "tr." là số trang in; trang trong tệp PDF = tr. + 18. Phần tóm tắt ghi "PDF tệp N". Dòng nguồn trong r1 của tôi đã lấy từ bản 6 chương này, nên vẫn dùng được. Chỉ số mục và số trang trong r1 theo PDF cũ, đã quy đổi lại ở dưới.

## A. Tự kiểm lại

- ND-01: cần sửa lại. Tên trên bìa là tên đề tài đã đăng ký, nên tôi rút lại hai ý "sót từ mẫu" và "tự thay tên". Ghi lại thành: tên đăng ký ("Mô hình thế giới vĩ mô trong trò chơi máy tính", Cover.tex:13, Cover2.tex:13, PDF tệp 1–2) lệch nội dung. Người đọc mở bìa sẽ tưởng luận văn nói về trò chơi máy tính. Tác giả cần hỏi GVHD hoặc phòng đào tạo về thủ tục đổi tên hoặc cách trình bày. Bỏ câu tên gợi ý trong r1. Đồng ý với r2_logic, r2_hinhbang, r2_giaothong.
- ND-02: còn đúng, và nặng hơn bản cũ (5_Experiments.tex:80, 121, 146, 180, 218, 245, 284, 405, 446, 479, 677, 1247, 1298; tr. 89–97). Mười ba bảng trôi về cuối Chương 5, kể cả Bảng 5.12 định nghĩa B0–H (xem Bỏ sót 1). Cách sửa thì tôi rút đề xuất "đặt mọi bảng `[H]`". r2_hinhbang chỉ ra đúng rằng `[H]` đã gây trang nửa trắng ở tr. 49 và 51. Tôi theo cách của họ: `[!htbp]`, `\usepackage[section]{placeins}`, `\raggedbottom`, và chỉ giữ `[H]` cho bảng ngắn.
- ND-03: còn đúng. Bảng 5.18 (phiên bản mạng) ở 5_Experiments.tex:716–734, tr. 55. Tên mạng đã được dùng từ 5:12 (tr. 30), 5:532 (tr. 47) và Bảng 5.11 (tr. 96, "Kịch bản hai pha, mạng F2"). "F2" vẫn mang ba nghĩa: nhóm hành vi ở 5:23 (tr. 30), tên mạng, và mã hạng mục ở 5:596 (tr. 50). Tôi chốt tên mạng N1–N6 theo r2_logic và r2_hinhbang, vì "v" đã dùng cho phiên bản prompt.
- ND-04: còn đúng. Mục 5.12 có 20 tiểu mục theo ngày, 5_Experiments.tex:712–1238, tr. 55–77. Việc sắp xếp lại nằm trọn trong Chương 5, không đụng cấu trúc GVHD đã chốt. Tôi nhận điều kiện của r2_logic: các giới hạn nằm trong những mục bị chuyển đi phải được giữ lại ở mục Hạn chế.
- ND-05: còn đúng. 2_Literature_review.tex:27, 29, 54, 64 (tr. 7–9); 5_Experiments.tex:1230 (tr. 77). Tiểu mục "Khái niệm cơ bản" vẫn đặt ở Mục 2.2. Hình minh họa phải là một nút giao chung, không vẽ Lê Văn Lương, để giữ đúng khung.
- ND-06: còn đúng, nhưng đề xuất cần sửa lại ba điểm. Vị trí: "xe chờ chèn" ở 4_Rule_execution.tex:112 (tr. 29); "khóa" ở 4:107 (tr. 28–29); "chiến dịch" ở 3_Rule_generation.tex:198 (tr. 22); teleport được dùng ở 5:444 (tr. 44) và 5:532 (tr. 47), định nghĩa ở 5:738 (tr. 55).
  - Định nghĩa ở Chương 4 phải dùng "trình mô phỏng", không gọi tên SUMO.
  - Không chuyển định nghĩa teleport sang Chương 4, vì "teleport" là từ riêng của SUMO. Đặt định nghĩa ở Mục 5.2 hoặc 5.8.3, tức lần dùng đầu trong Chương 5.
  - Theo r2_logic, không lấy câu "P1 không thể đủ điều kiện" làm ví dụ, vì câu đó khẳng định quá mức (LG-05). Theo r2_giaothong, thêm cụm "nhu cầu chưa được phục vụ" vào định nghĩa xe chờ chèn.
- ND-07: còn đúng (0_3_Abstract.tex:15, PDF tệp 3–4). Câu mẫu trong r1 cần sửa theo r2_logic. Thay "va chạm không vượt mức của SUMO mặc định" bằng "va chạm không vượt ngưỡng suy từ SUMO mặc định trên một phiên bản mạng trước". Thay "nguyên nhân chính là gia tốc" bằng "yếu tố lớn nhất trong các biến thể đã thử" (LG-01).
- ND-08: còn đúng một phần. Bảng 4.1 (4_Rule_execution.tex:82–93, tr. 28) đã có tên cho M8 (đi sai làn), M9 (chặn làn rẽ phải liên tục) và M10 (đi trên vỉa hè). M1–M7 thì chưa có. Mã trơ vẫn còn ở 5:437 (tr. 44), 5:518 (tr. 46) và 5:1125 (tr. 72). Tôi nhận các tên ngắn r2_giaothong sửa: M4 (vị trí dừng và dừng quá vạch), M5 (hàng chờ). M1 thêm "trên cùng một làn, bỏ $n$ xe đầu".
- ND-09: còn đúng. 5_Experiments.tex:134–135 nằm trong Bảng 5.2, mà bảng này trôi về tr. 90. Các dòng 174, 178 ở tr. 34–35; dòng 209 ở tr. 36. Bảng 5.36 giải thích bit nằm ở tr. 97.
- ND-10: còn đúng (5:14 tr. 30; 5:675 tr. 53; 5:867 tr. 62; 5:938 tr. 65; 5:1167 tr. 74).
- ND-11: còn đúng (glossary.tex:5–40; PDF tệp 18).
- ND-12: còn đúng (4:103 tr. 29; 3:57 tr. 15; 5:400 tr. 43; 5:710 tr. 55; tóm tắt PDF tệp 4 và 6).
- ND-13: cần sửa lại vị trí. Chương 4 không được nhắc nút cụ thể, nên đặt ví dụ ở đầu Mục 5.2 (tr. 33), như r2_logic, r2_hinhbang và r2_giaothong đề xuất. Theo r2_logic, B1 không có `illegal_left_box` (Phụ lục A, tr. 110). Vì vậy ví dụ phải dùng một đặc tả có luật này, chẳng hạn đặc tả P2 `it02_s01` (5:1173), và nói rõ đặc tả đó là gì.
- ND-14: còn đúng (5:31–32, 66–70; tr. 31–32).
- ND-15: còn đúng (5:23 tr. 30; 5:91 trong Bảng 5.1 tr. 89; 5:108 tr. 32; 5:817 và 5:850 tr. 59–61). Đề xuất sửa theo hướng gộp ý của các bên (xem Mâu thuẫn 4).
- ND-16: còn đúng về vị trí (Bảng 5.3 ở 5:150–163, tr. 90; 3:100, tr. 17). Tôi sai về nghĩa: `tau` là giãn cách thời gian mong muốn, không phải thời gian phản ứng (GT-21, r2_giaothong). Cột "Ý nghĩa" phải ghi "giãn cách thời gian mong muốn (s)". Câu ở 3:100 cũng cần sửa tương ứng.
- ND-17: còn đúng. Mục 3.4.2–3.4.6 ở 3:104–135, tr. 17–19; Bảng 3.2 ở tr. 20.
- ND-18: cần sửa lại. Tôi bỏ đề xuất "ngày đánh giá", chuyển sang "ngày kiểm định" theo GT-19. Điều kiện: đổi đồng bộ cả "đánh giá cuối E1, E2" (r2_hinhbang). Hai cặp tên còn lại vẫn giữ: "xe chờ chèn" và "bộ luật viết tay B1".
- ND-19: còn đúng (1:22; 2:73; 5:174, 328, 332, 468, 524).

## B. Phản biện chéo

### Đồng ý

**r1_hoidong**
- HD-01: đồng ý việc nêu, nhưng đổi cách gọi và cách sửa như ND-01 ở trên.
- HD-02: đồng ý. Câu kết luận chính vẫn là TODO (6_Conclusions.tex:45, tr. 100).
- HD-03: đồng ý. Câu hỏi nghiên cứu giúp người ngoài ngành biết đọc Chương 5 để tìm gì. Đặt câu hỏi ở Mục 1.4 thì hợp khung GVHD.
- HD-04: đồng ý, kèm điều kiện. Bảng 5.2 (ánh xạ khái niệm sang SUMO), Bảng 5.8 và định nghĩa teleport phải ở lại thân bài, vì người ngoài ngành dùng chúng để nối Chương 3–4 với Chương 5.
- HD-05: đồng ý (trùng ND-04).
- HD-06: đồng ý (trùng ND-02). Về cách sửa, xem Mâu thuẫn 1.
- HD-07: đồng ý. Viết lại theo đóng góp thì cũng tự bỏ được các ngày nội bộ.
- HD-08: đồng ý vấn đề. Về tên gọi, xem Mâu thuẫn 2.
- HD-09: đồng ý. Khung mới đã tách sẵn chỗ: Chương 4 trình bày ý tưởng, Chương 5 chỉ nêu phần riêng của SUMO. Mục 5.2.1 (tr. 35) chép lại năm nhóm kiểm tra của 4.1 (tr. 24) gần như nguyên văn.
- HD-11: đồng ý.
- HD-12: đồng ý. Một đặc tả P2 kèm trường lý do cũng chính là ví dụ cụ thể mà người ngoài ngành cần (ND-13, HB-17).
- HD-13: đồng ý.
- HD-14: đồng ý.
- HD-15: đồng ý (trùng ND-12).
- HD-16: đồng ý (trùng ND-03, ND-10).
- HD-17: đồng ý. main.tex:271–272 vẫn để `\addcontentsline` sau `\printbibliography`.
- HD-18: đồng ý, mức nhỏ.

**r1_vanphong**
- VP-01: đồng ý. Về tên mạng, xem Mâu thuẫn 5.
- VP-02: đồng ý.
- VP-03: đồng ý. Bỏ hẳn F1–F3 là cách gọn nhất.
- VP-04: đồng ý.
- VP-05: đồng ý.
- VP-06: đồng ý. "Mã xác định" có thể bị người đọc CNTT hiểu là mã định danh. "Mã tất định" rõ hơn.
- VP-07: đồng ý vấn đề. Về tên thay thế, xem Mâu thuẫn 3.
- VP-08: đồng ý, với điều kiện giữ một câu nối nói chương sau giải quyết việc gì. Người ngoài ngành cần câu này để biết vì sao chuyển chương.
- VP-09: đồng ý. Mục lục build2 vẫn có "a Tham số tĩnh" ngay dưới 5.2, trước 5.2.1 (main.toc dòng 63–65).
- VP-10: đồng ý, nhưng hạ xuống nhỏ. Lỗi này không làm khó hiểu, chỉ làm văn lặp.
- VP-11: đồng ý.
- VP-12: đồng ý. Câu viết lại cho "khóa" khớp với ND-06.
- VP-13: đồng ý.
- VP-14: đồng ý.
- VP-15: đồng ý.
- VP-16: đồng ý (trùng ND-11).
- VP-17: đồng ý. Đã mở Appendix_B.tex: Bảng B.1 có 7 tệp, trong khi 4_Rule_execution.tex:64 nói mười bảng. Câu "(bổ sung so với kế hoạch)" ở dòng 22 và đoạn ở dòng 36 vẫn còn.

**r1_hinhbang**
- HB-01: đồng ý việc nêu và ý dùng chung macro cho tên đề tài. Cách sửa thì như ND-01 ở trên.
- HB-02: đồng ý. Đây là cách sửa tôi theo.
- HB-03: đồng ý.
- HB-04: đồng ý. Nhãn "posLat", "on box lanes" là tên biến trong mã, người ngoài ngành không đọc được.
- HB-05: đồng ý (trùng ND-14).
- HB-06: đồng ý. Đây là chỗ cách trình bày `\tamthoi` gây hiểu nhầm, nên nằm trong phạm vi được góp ý.
- HB-07: đồng ý.
- HB-08: đồng ý.
- HB-09: đồng ý, nhưng hạ xuống nhỏ. Đây là chuyện thẩm mỹ, trừ chỗ gạch nối chèn vào giữa tên mã (phần đó nên sửa).
- HB-10: đồng ý, mức nhỏ.
- HB-11: đồng ý.
- HB-12: đồng ý, kèm điều kiện như HD-04.
- HB-13: đồng ý.
- HB-14: đồng ý. Caption chứa mã trơ như "PROXY_D2", "mạng F2", "REF" là đúng loại chỗ vấp mà tôi tìm.
- HB-15: đồng ý (trùng ND-10, ND-11).
- HB-16: đồng ý, và nên nâng lên gần nghiêm trọng với người đọc CNTT. Hiện $d$, $R$, $S$ chỉ được tả bằng lời (4_Rule_execution.tex:101–107), nên người có nền ML không kiểm tra được cách tính điểm. Viết công thức ở Mục 4.7.2 không phạm khung, vì đó vẫn là ý tưởng chung.
- HB-17: đồng ý.
- HB-18: đồng ý.
- HB-19: đồng ý.
- HB-20: đồng ý.

**r1_logic**
- LG-01: đồng ý.
- LG-02: đồng ý.
- LG-03: đồng ý. Người ngoài ngành đọc "SUMO mặc định" sẽ tưởng B0 không có gì của tác giả. Thực ra B0 chạy trên mạng có bản vá và có lớp xe vi phạm. Đã kiểm 5_Experiments.tex:774: câu "Không cần tùy chọn hay sửa mạng" vẫn còn.
- LG-04: đồng ý. Câu ở 1_Introduction.tex:67 vẫn còn.
- LG-05: đồng ý.
- LG-06: đồng ý.
- LG-07: đồng ý.
- LG-08: đồng ý.
- LG-09: đồng ý.
- LG-10: đồng ý.
- LG-11: đồng ý, và lỗi vẫn còn trên build2. `section:3.3` nay là Mục 3.5 "Biểu diễn luật". `section:3.8` là Mục 5.7. `section:1.2` là Mục 1.4.
- LG-12: đồng ý.
- LG-13: đồng ý.
- LG-14: đồng ý.
- LG-15: đồng ý.
- LG-16: đồng ý.
- LG-17: đồng ý.
- LG-18: đồng ý.
- LG-19: đồng ý.
- LG-20: đồng ý.

**r1_hocvien**
- HV-01: như HB-01.
- HV-02: đồng ý.
- HV-03: đồng ý.
- HV-04: đồng ý.
- HV-05: đồng ý phần tách đóng góp với công cụ có sẵn. Về vị trí của bảy giải pháp, xem Mâu thuẫn 7.
- HV-07: đồng ý. Một bảng phủ hành vi cũng trả lời câu người ngoài ngành hay hỏi: "11 hành vi, vậy cái nào thật sự chạy?"
- HV-08: đồng ý.
- HV-09: đồng ý.
- HV-10: đồng ý.
- HV-11: đồng ý.
- HV-12: đồng ý.
- HV-13: đồng ý.
- HV-14: đồng ý.
- HV-15: đồng ý, kèm điều kiện như HD-04.
- HV-17: đồng ý (trùng VP-17).
- HV-18: đồng ý.
- HV-19: đồng ý.
- HV-20: đồng ý.

**r1_giaothong**
- GT-02: đồng ý. Lần đọc đầu tôi cũng vấp ở đây: 5:23 nói rẽ trái trên làn 0 là đúng luật, trong khi Bảng 5.1 (5:91) chỉ có kết nối rẽ trái từ làn 2.
- GT-03: đồng ý. Đây là bổ sung đúng nhất cho ND-05 và ND-15. Sơ đồ phân làn và sơ đồ pha đặt ở Mục 5.1, hợp khung.
- GT-04: đồng ý.
- GT-05: đồng ý. Trích "[TAG]" ngay cạnh ngưỡng làm người đọc tưởng đã đạt chuẩn TAG.
- GT-06: đồng ý (trùng ND-06). Cụm "va chạm mô phỏng (chồng lấn)" rất có ích cho người ngoài ngành.
- GT-07: đồng ý.
- GT-08: đồng ý.
- GT-09: đồng ý.
- GT-10: đồng ý.
- GT-11: đồng ý.
- GT-12: đồng ý.
- GT-13: đồng ý.
- GT-14: đồng ý.
- GT-15: đồng ý.
- GT-16: đồng ý.
- GT-17: đồng ý.
- GT-18: đồng ý (trùng ND-05).
- GT-19: đồng ý. Tôi đã đổi ND-18 theo hướng này.
- GT-21: đồng ý. Tôi đã sửa ND-16 theo GT-21.

### Phản đối

- **GT-01**: phản đối phần đề xuất bỏ hành vi 7, bỏ M10 (đi trên vỉa hè) và lựa chọn `sidewalk`. Văn bản không xếp vỉa hè ra ngoài phạm vi. 1_Introduction.tex:82 viết "các không gian chỉ xe vi phạm được dùng (ví dụ vỉa hè) là bản vá tĩnh của mạng", tức vỉa hè nằm trong mô hình qua bản vá. 3_Rule_generation.tex:89 nói hành vi 8 có được mô hình hóa hay không tùy vào thí nghiệm khả thi. Phần đúng của GT-01 chỉ là cách gọi hành vi 8: đổi "hoãn" thành một câu phạm vi rõ ràng, nêu lý do lấy từ thí nghiệm 3C. Việc bỏ hành vi 7 là quyết định phạm vi, nằm ngoài góp ý trình bày.
- **GT-20**, phần "lane 0/1/2 → làn 1/2/3 tính từ lề phải": phản đối. Chỉ số 0/1/2 xuất hiện trong khóa cấu hình `violator_turn_lanes` (5:112), trong Bảng 5.1 và 5.4, và trong cột lược đồ. Đổi sang 1/2/3 thì người đọc phải tự trừ một ở mọi chỗ đối chiếu với bảng. Cách gộp: xem Mâu thuẫn 4.
- **HV-06**: đồng ý cần ký hiệu hình thức, nhưng phản đối vị trí ở Mục 1.2. Khung GVHD cho Chương 1 là: lợi ích, "tuy nhiên", rồi hướng giải quyết. Chèn "min S(θ) s.t. …" vào đó khiến người ngoài ngành gặp ký hiệu trước khi biết S, đặc tả hay tiêu chí chấp nhận là gì. Mục 3.1 (tr. 12) là chỗ đúng: đó là tổng quan phương pháp, vẫn ở mức ý tưởng, và đứng ngay trước các khái niệm cần dùng.
- **HV-16**, phương án "bỏ 5.13 và đưa Bảng 5.35 vào Mục 1.5": phản đối. Bảng 5.35 (5_Experiments.tex:1253–1260) có "bit speed mode", "`custom1`", "B0". Đặt nó ở Chương 1 tức là đưa thuật ngữ SUMO và mã phương án vào chương mà người đọc chưa biết chúng. Điều này cũng lệch khung, vì Chương 1 phải ở mức chung.
- **VP-07**, tên "dữ liệu thay thế": phản đối tên gọi, không phản đối vấn đề. Xem Mâu thuẫn 3.

### Mâu thuẫn

1. **Cách đặt bảng.** Đặt mọi bảng `[H]` (ND-02 r1, GT-03) hay dùng `[!htbp]` kèm `placeins` (HB-02, HV-09, HD-06). Tôi nghiêng về HB-02. Build2 cho thấy `[H]` để lại trang nửa trắng (tr. 49, 51).
2. **Tên "đủ điều kiện".** HD-08 đề xuất "qua bộ lọc an toàn", VP-04 giữ tên cũ và thêm định nghĩa, r2_logic đề xuất "đạt tiêu chí chấp nhận". Tôi nghiêng về "đạt tiêu chí chấp nhận", định nghĩa một lần ở Mục 4.8. "An toàn" hẹp hơn tiêu chí thật, vì tiêu chí còn gồm G0 và xe chờ chèn. "Hợp lệ" thì trùng với "đặc tả hợp lệ" của bộ kiểm tra.
3. **Tên "dữ liệu đại diện".** VP-07 đề xuất "dữ liệu thay thế", HD-16 "dữ liệu giả lập từ tài liệu", GT-19 "dữ liệu tổng hợp (dựng từ tài liệu)". Tôi nghiêng về GT-19. "Giả lập" dễ lẫn với "mô phỏng". "Thay thế" không cho biết dữ liệu lấy từ đâu.
4. **Đánh số làn.** GT-20 đề xuất "làn 1/2/3 tính từ lề phải". ND-15, VP-05 và r2_logic giữ "làn 0/1/2". r2_giaothong muốn gọi theo chức năng. Tôi gộp như sau: định nghĩa "làn 0/1/2" một lần ở Mục 5.1.3, có vẽ trên sơ đồ phân làn (GT-03). Lần đầu nhắc trong mỗi mục thì kèm tên chức năng, ví dụ "làn 0 (làn sát lề phải, rẽ phải liên tục ở 30 m cuối)". Sau đó chỉ dùng chỉ số.
5. **Tên phiên bản mạng.** VP-01 đề xuất V1–V6, HV-03 đề xuất v1…v6, HD-16 và ND-03 đề xuất N1–N6. Tôi chọn N1–N6, trong văn xuôi gọi N6 là "mạng cuối". Chữ "v" đã dùng cho phiên bản prompt và cho biến thể luật.
6. **Tên tập dữ liệu cuối.** ND-18 (r1) đề xuất "ngày đánh giá", GT-19 đề xuất "ngày kiểm định". Tôi theo GT-19, với điều kiện đổi đồng bộ.
7. **Mục 5.13 (bảy giải pháp).** HD-09 muốn rút gọn tại chỗ. HV-05 muốn viết lại thành "hiện thực các đóng góp". HV-16 muốn bỏ và đưa bảng vào Mục 1.5. HD-03 muốn đổi tên thành "giải pháp kỹ thuật". Tôi nghiêng về HD-09 cộng HV-05: giữ ở cuối Chương 5, mỗi giải pháp 2–3 câu trỏ tới bằng chứng, và ghi rõ phần nào là công cụ có sẵn. Không đưa lên Chương 1 (xem Phản đối).
8. **Vị trí phát biểu bài toán hình thức.** HV-06 đề xuất Mục 1.2, tôi đề xuất Mục 3.1. Tôi nghiêng về Mục 3.1, lý do ở phần Phản đối.

### Bỏ sót

1. **Bảng định nghĩa B0–H bị đẩy cách 51 trang. Đây là lỗi mới sinh ra khi cấu trúc lại.**
   - Vị trí: 5_Experiments.tex:477–501 (Bảng 5.12 `[ht]`). Mục 5.7.1 ở tr. 45 chỉ có một câu: "Bảng 5.12 định nghĩa sáu phương án." Bảng in ở tr. 96.
   - Vì sao quan trọng: Trong PDF cũ, bảng này nằm đúng chỗ (Bảng 5.2, tr. in 26). Nay mã B0, B1, B2, P1, P2, H được dùng từ tr. 30 nhưng định nghĩa ở tr. 96. Người ngoài ngành không có chỗ nào gần để tra.
   - Đề xuất: Đặt Bảng 5.12 ngay sau câu dẫn ở 5.7.1, hoặc kéo nó lên đầu Chương 5. Khi chưa sửa float, viết luôn định nghĩa sáu mã vào câu văn ở 5.7.1.
2. **Chương 4 nói bằng từ chung nhưng không có cầu nối sang SUMO.**
   - Vị trí: 4_Rule_execution.tex:26 ("thông qua giao diện điều khiển lúc chạy của trình mô phỏng"); 3_Rule_generation.tex:139 ("Miền giá trị cụ thể … nằm ở Chương 5 (Bảng 5.4)"). Bảng 5.2 (ánh xạ khái niệm sang SUMO) và Bảng 5.4 trôi về tr. 90–91.
   - Vì sao quan trọng: Khung GVHD bắt Chương 3–4 nói ở mức chung, nên Bảng 5.2 thành chỗ duy nhất cho người đọc biết "giao diện điều khiển lúc chạy" chính là TraCI đã giới thiệu ở Mục 2.2. Bảng này lại nằm ở tr. 90.
   - Đề xuất: Thêm một câu ở đầu Chương 4 kiểu "Chương 5 (Bảng 5.2) nêu cách hiện thực từng khái niệm dưới đây trên một trình mô phỏng cụ thể". Đặt Bảng 5.2 ngay đầu Mục 5.2 (tr. 33).
3. **"Seed" chỉ ba thứ khác nhau.**
   - Vị trí: 3_Rule_generation.tex:207 ("mỗi mẫu dùng một seed riêng", tức seed của LLM); 5_Experiments.tex:468 ("seed 42, mẫu thứ $j$ dùng seed $42+j$"); 5:524 ("TPE với seed 0", tức seed của Optuna); 5:526 và các bảng kết quả ("seed 1", "seed 1–5", tức seed của mô phỏng).
   - Vì sao quan trọng: Bảng kết quả chỉ ghi "seed 1". Người đọc không biết đó là seed của mô phỏng hay của LLM. Họ cũng không biết "tái lập được với cùng seed" (1_Introduction.tex:22) nói về seed nào.
   - Đề xuất: Định nghĩa seed một lần (nối với ND-19) và luôn ghi kèm chủ thể: "seed mô phỏng", "seed lấy mẫu của LLM", "seed của Optuna".
4. **Quan hệ giữa nguyên mẫu, phân phối và lớp vi phạm không được vẽ ra, nên lỗi chính của LLM không hiểu được.**
   - Vị trí: Bảng 3.3 (3_Rule_generation.tex:176, tr. 20): "loại phương tiện cơ sở (ô tô, xe máy, hoặc lớp vi phạm của chúng); phân phối mà nó thuộc về; tỷ trọng…". Kết quả về LLM ở 5_Experiments.tex:1183 (P1: 14/15 lần thử hỏng vì tổng tỷ trọng ở `moto_violator`) và 5:1194 (P2: 19 lần mã nguyên mẫu trùng tên phân phối), tr. 75–76.
   - Vì sao quan trọng: Hai lỗi này là phát hiện chính về `qwen3.5:9b`. Người ngoài ngành không biết "phân phối" là gì, cũng không biết vì sao một nguyên mẫu duy nhất phải có tỷ trọng bằng 1. Vì vậy họ không đánh giá được LLM sai "ngớ ngẩn" hay sai vì lược đồ khó.
   - Đề xuất: Ở Mục 3.5, thêm một hình nhỏ hoặc ví dụ chung ba tầng: loại xe → phân phối → các nguyên mẫu có tỷ trọng cộng bằng 1. Ở Mục 5.2, thêm bản cụ thể với `car`, `moto`, `moto_violator`. Ví dụ ở ND-13 có thể dùng lại hình này.
