# Hình thức trình bày, vòng 2

> Vòng này dùng bản build mới (`scratchpad/build2/main.pdf`, 131 trang, cùng `main.log`). Bản này gồm 6 chương: Ch3 `3_Rule_generation`, Ch4 `4_Rule_execution`, Ch5 `5_Experiments`, Ch6 `6_Conclusions`. "tr. N" là số trang in ở chân trang; trang trong tệp PDF = N + 18. Số dòng `.tex` lấy theo các tệp hiện có (log của build2 khớp các số dòng này). Mọi đề xuất dưới đây giữ khung GVHD đã chốt: Ch3–4 chỉ trình bày ý tưởng, nút giao và kết quả chỉ ở Ch5.

## A. Tự kiểm lại nhận xét vòng 1

- HB-01: cần sửa lại. Tên trên bìa ("Mô hình thế giới vĩ mô trong trò chơi máy tính", `Cover.tex:13`, `Cover2.tex:13`, PDF tệp tr. 1–2) là tên đề tài đã đăng ký, không phải chữ sót từ mẫu. Ghi lại thành: tên đăng ký lệch nội dung, tác giả cần hỏi GVHD hoặc phòng đào tạo về thủ tục điều chỉnh tên. Ý phụ vẫn còn đúng: `\TITLE` = "LUẬN VĂN THẠC SĨ" (`main.tex:73`) đang được dùng làm `pdftitle` (`main.tex:121`).
- HB-02: còn đúng (vị trí mới: `5_Experiments.tex:80, 121, 146, 180, 218, 245, 284, 405, 446, 677, 1247, 1298`). Bảng 5.1 được nhắc ở tr. 31 nhưng in ở tr. 89. Bảng 5.17 được nhắc ở tr. 53, in ở tr. 96. Bảng 5.4 được Ch3 trỏ tới từ tr. 20, in ở tr. 91. Danh mục bảng xếp 5.8, 5.9, 5.13 … 5.34 trước 5.1 (PDF tệp tr. 16–17).
- HB-03: còn đúng (vị trí mới: `4_Rule_execution.tex:103` tr. 29 [Câu hỏi cho GVHD]; `3_Rule_generation.tex:57` tr. 15; `5_Experiments.tex:400` tr. 43, `:710` tr. 55, `:1341` tr. 82, `:1418` tr. 86; `6_Conclusions.tex:45` tr. 100; `0_3_Abstract.tex:17`, PDF tệp tr. 4).
- HB-04: còn đúng (vị trí mới: Hình 5.3 `5_Experiments.tex:703` tr. 54; Hình 5.4 `:770` tr. 57; Hình 5.5 `:799` tr. 58).
- HB-05: còn đúng (vị trí mới: Hình 5.1 `5_Experiments.tex:31` tr. 31; Hình 5.6 `:816` tr. 60).
- HB-06: còn đúng (vị trí mới: `main.tex:60`; `5_Experiments.tex:14` tr. 30 ghi "theo quy ước ở Mục 5.1" trong khi quy ước nằm ở 5.1.3; `:920` tr. 64 in đậm đen "4 va chạm trên làn/h", "142 va chạm trong nút/h").
- HB-07: còn đúng. Các Overfull trong `main.log` của build2 có cùng số dòng nguồn với vòng 1. Ví dụ: `5_Experiments.tex:615–631` (Bảng 5.15 rộng hơn khối chữ 51 pt, tr. 51), `:665` (43 pt, tr. 53), `:1283` (49 pt, tr. 79), tài liệu tham khảo [18] (51 pt, tr. 103–104).
- HB-08: còn đúng (vị trí mới: tr. 49 có tiêu đề 5.9.2 cùng một câu, còn lại để trắng, vì Bảng 5.14 `[H]` ở `5_Experiments.tex:578`; tr. 51 quanh Bảng 5.15; `Appendix_A.tex:68` tr. 108).
- HB-09: còn đúng (Bảng 2.1 tr. 7–8 có ô "Láng Hạ – Láng; Vũ Phạm Hàm – Nguyễn Khang" bị giãn chữ; Bảng 5.18 tr. 55; Bảng 5.32 tr. 74; Bảng A.3 tr. 109 có "motorcycle" dính sang cột bên cạnh).
- HB-10: còn đúng (Bảng A.1–A.4, B.1 vẫn đặt caption dưới bảng, tr. 106–112).
- HB-11: còn đúng (Bảng 5.26 tr. 68 ghi "1,225", Bảng 5.30 tr. 71 ghi "1,2247"). Đề xuất về số chữ số cần chỉnh theo mục Mâu thuẫn 2 bên dưới.
- HB-12: còn đúng. Ch5 chiếm tr. 30–97, tức 68 trên 101 trang thân bài; Ch4 chiếm 6 trang, Ch3 chiếm 12 trang. Đề xuất giữ nguyên trong khung GVHD: chỉ chuyển bảng kỹ thuật sang phụ lục, không tách hay gộp chương.
- HB-13: còn đúng (vị trí mới: hai mục "a, Tham số tĩnh" và "b, Luật có điều kiện" đứng ngay dưới 5.2, `5_Experiments.tex:142, 168`, tr. 33–35; tiêu đề ghi ngày ở 5.12.9–5.12.14 trong mục lục, PDF tệp tr. 10; số trang 3 chữ số dính vào hàng chấm ở "6.1.5 Chưa thực hiện…100", "TÀI LIỆU THAM KHẢO…104", PDF tệp tr. 11–12).
- HB-14: còn đúng (vị trí mới: Bảng 5.27 tr. 69, Bảng 5.32 tr. 74, Bảng 5.22 tr. 63, Bảng A.5 tr. 111; danh mục hình chiếm PDF tệp tr. 13–14).
- HB-15: còn đúng (`glossary.tex` vẫn chỉ có 6 mục, tr. vi).
- HB-16: còn đúng nhưng hẹp lại. Ch4 đã đưa R và $D_{\text{empty}}$ vào câu chữ (`4_Rule_execution.tex:101–107`, tr. 28–29), nhưng cả luận văn vẫn chỉ có một phương trình đánh số là (3.1) ở tr. 17. Tham số vẫn mang hai tên: $t_{\text{before}}$ ở Bảng 3.2 (tr. 20), $t_{\text{before\_green}}$ ở Bảng 5.4 và Bảng A.4. Lỗi font `OT1/cmr` vẫn còn trong log.
- HB-17: còn đúng nhưng hẹp lại. Hình 1.1 đã đủ làm sơ đồ vòng lặp LLM. Còn thiếu sơ đồ kiến trúc cho Mục 5.4 (tr. 38–42) và một listing đặc tả JSON.
- HB-18: còn đúng (vị trí mới: tr. 102–104; [2], [10] vẫn có URL/DOI bị giãn khoảng trắng; [18] vẫn tràn lề).
- HB-19: còn đúng. Tóm tắt tiếng Việt vẫn tràn sang trang thứ hai (PDF tệp tr. 3–4). Mục 1.5 vẫn dùng `enumerate` (tr. 5).
- HB-20: còn đúng. Bảng 2.2 đứng một mình trên tr. 11, phía trên để trắng nửa trang.

## B. Phản biện chéo

Vị trí trích trong các r1 khác theo bản 7 chương, nên số chương và trang đã lệch: "Chương 6/Mục 6.x" cũ nay là "Chương 5/Mục 5.x", và trang in cũ + 2 đến + 3 ≈ trang mới. Tôi đã mở lại từng vị trí trên build2. Nhận xét nào còn nội dung thì tính là còn hiệu lực, dù số trang đã đổi.

### Đồng ý

**r1_hoidong**
- HD-01: đồng ý về hiện tượng, nhưng cần đổi hướng: tên là tên đăng ký, nên ghi "tên đăng ký lệch nội dung, hỏi GVHD/phòng đào tạo", không ghi là sót từ mẫu (xem Phản đối 1).
- HD-02, HD-03: đồng ý. Câu kết luận chính vẫn là TODO (`6_Conclusions.tex:45`, tr. 100). Bảng nối mục tiêu → bằng chứng đề xuất ở HD-02 cũng là một bảng ngắn hợp lý.
- HD-04: đồng ý. Ch5 chiếm 68/101 trang (cách tính đã đổi: Ch4 nay 6 trang). Hướng cắt và chuyển phụ lục khớp HB-12.
- HD-05: đồng ý. 5.12 vẫn có 20 tiểu mục theo ngày (mục lục, PDF tệp tr. 10–11).
- HD-06: đồng ý (trùng HB-02, HB-20). Cách sửa xem Mâu thuẫn 1.
- HD-07, HD-08: đồng ý. Đoạn "Kết quả hiện có" vẫn kể theo ngày (PDF tệp tr. 3).
- HD-09: đồng ý. Đây cũng là nguyên nhân chính làm Ch5 dài.
- HD-11, HD-12, HD-13, HD-14, HD-15: đồng ý. HD-15 trùng HB-03.
- HD-16: đồng ý. "F2" vẫn mang hai nghĩa: nhóm hành vi ở tr. 30, tên mạng ở Bảng 5.18 tr. 55.
- HD-17: đồng ý, tôi bỏ sót lỗi này ở vòng 1. Trên build2, mục lục ghi "TÀI LIỆU THAM KHẢO…104" và "PHỤ LỤC…106", nhưng danh mục tài liệu bắt đầu trước tr. 104 (tr. 104 đã là trang chứa [19]–[27]), còn trang "PHỤ LỤC" là tr. 105. Cách sửa `heading=bibintoc` là đúng.
- HD-18: đồng ý (trùng HB-04, HB-08).

**r1_nguoidoc**
- ND-01: như HD-01, cần đổi hướng.
- ND-02: đồng ý về lỗi. Cách sửa "đặt mọi bảng `[H]`" xem Mâu thuẫn 1.
- ND-03, ND-04: đồng ý. Bảng 5.18 (phiên bản mạng) vẫn ở tr. 55, sau khi tên mạng đã được dùng từ tr. 30.
- ND-05, ND-06, ND-07: đồng ý. "Khóa" vẫn chưa được định nghĩa ở `4_Rule_execution.tex:107` (tr. 29). Đề xuất thêm khoảng 1 trang khái niệm cho Ch2 không làm Ch5 dài thêm.
- ND-08: đồng ý một phần. Bảng 4.1 (tr. 28) đã có tên ngắn cho M8, M9, M10, nhưng M1–M7 vẫn chưa có. Cột "Tên ngắn" vẫn cần.
- ND-09, ND-10, ND-11, ND-12: đồng ý. ND-11 và ND-10 trùng HB-15.
- ND-13: đồng ý. Ví dụ nên đặt ở đầu 5.2 để giữ Ch4 ở mức ý tưởng.
- ND-14: đồng ý (trùng HB-05, GT-07).
- ND-15, ND-16, ND-17, ND-18, ND-19: đồng ý. Cách đánh số làn ở ND-15 xem Mâu thuẫn 3.

**r1_vanphong**
- VP-01, VP-02, VP-03: đồng ý. Cách đặt tên mạng xem Mâu thuẫn 5.
- VP-04, VP-05, VP-06: đồng ý.
- VP-07: đồng ý cần đổi tên. Chọn tên nào xem Mâu thuẫn 4.
- VP-08: đồng ý. Đoạn kết Ch2 (tr. 10) và đoạn mở Ch3 (tr. 12) vẫn gần trùng câu chữ.
- VP-09: đồng ý (trùng HB-13). Bỏ 21 `\subsubsection` Vấn đề/Giải pháp/Kết quả ở 5.13 cũng làm mục lục gọn hơn.
- VP-10, VP-11, VP-12, VP-13: đồng ý.
- VP-14: đồng ý. Nên gộp với HB-11 thành một quy ước số chung (dấu phân cách hàng nghìn, số chữ số thập phân).
- VP-15: đồng ý. Dấu phẩy trước "Máy chính" vẫn còn (tr. 87).
- VP-16, VP-17: đồng ý. Bảng B.1 vẫn chỉ có 7 tệp (tr. 112), trong khi Ch4 4.6 (tr. 27) nói mười bảng.

**r1_logic** (ngoài góc nhìn hình thức; tôi chỉ kiểm vị trí và trích)
- LG-01 đến LG-10: đồng ý, vị trí trích vẫn đúng trên build2. LG-04 nay có cả trong PDF: câu "không thể 'khớp' dữ liệu nhờ va chạm" ở tr. 4. LG-09: Mục 4.7.1 (tr. 27) vẫn không nói hành vi 9 và 11 chưa có chỉ số.
- LG-11: đồng ý, và trên build2 lỗi còn rõ hơn. Bảng 2.2 (tr. 11) ghi "với 11 hành vi (Mục 1.4)", tức trỏ vào Mục tiêu và phạm vi. Bảng 5.1 (tr. 89) trỏ "lựa chọn cắt về … (Mục 3.5)", tức trỏ vào Biểu diễn luật. Nguyên nhân là nhãn `section:3.3` nằm ở `3_Rule_generation.tex:159` và `section:1.2` ở `1_Introduction.tex:74`.
- LG-12 đến LG-18: đồng ý.
- LG-17 (S ghi 4 chữ số): đồng ý, xem Mâu thuẫn 2.
- LG-19: đồng ý. `5_Experiments.tex:282` vẫn ghi "Hình 1.1 cho thấy năm bước đầu", trong khi Hình 1.1 (tr. 3) vẽ khối "Sinh luật" không đánh số và năm khối đánh số 1–5.
- LG-20: đồng ý.

**r1_hocvien**
- HV-01: như HD-01, cần đổi hướng. Ý về `\TITLE`/pdftitle vẫn đúng.
- HV-02, HV-03, HV-04, HV-05: đồng ý.
- HV-06: đồng ý. Một phương trình bài toán ở 1.2 cũng giải quyết một phần HB-16.
- HV-07: đồng ý. Bảng phủ hành vi nên thay cho Bảng 5.5 hoặc 5.6 (xem Bỏ sót 3), để Ch5 không dài thêm.
- HV-08, HV-10, HV-11, HV-12, HV-13: đồng ý.
- HV-09: đồng ý (trùng HB-02, HB-08).
- HV-14: đồng ý, vẫn còn: OPRO, FunSearch, Eureka nay nằm ở 3.6.1 (tr. 21) nhưng Ch2 chưa có. Mở rộng Ch2 không vi phạm khung.
- HV-15: đồng ý (trùng HB-12).
- HV-16: đồng ý về hiện tượng. Cách sửa xem Mâu thuẫn 6.
- HV-17, HV-18: đồng ý.
- HV-19: đồng ý, xem Mâu thuẫn 2.
- HV-20: đồng ý (trùng HB-04, HB-05, HB-15).

**r1_giaothong**
- GT-02, GT-04, GT-05, GT-06: đồng ý, vị trí trích vẫn đúng (Bảng 4.1 tr. 28; 5.1.1 tr. 30).
- GT-03: đồng ý. Đây là chỗ cần hình rõ nhất. Hình 5.2 (tr. 32) không vẽ làn, mũi tên hướng đi hay pha đèn. Về cách làm, xem Phản đối 4.
- GT-07: đồng ý (trùng HB-05, ND-14).
- GT-08 đến GT-15: đồng ý.
- GT-16: đồng ý. Bảng v/c nên ngắn (4 nhánh × 3 pha), hoặc đặt ở phụ lục.
- GT-17, GT-18, GT-19, GT-21: đồng ý. Câu "phần vật lý … nhường đường không đổi" vẫn ở tr. 4.
- GT-20: đồng ý phần thuật ngữ, trừ đề xuất đánh số làn (xem Phản đối 3).

### Đã hết

- HD-10: đã hết. Mục 3.1 (tr. 12) nay nói "hai phần". Caption Hình 1.1 (tr. 3) gán sinh luật cho Ch3 và bước 1–4 cho Ch4, khớp với mục lục. Ch3 không còn trỏ ngược vào nhật ký thực nghiệm.
- Ý phụ trong HD-04 ("Ch4 3 trang") đã hết: Ch4 nay 6 trang. Phần chính của HD-04 vẫn còn.

### Phản đối

1. **HD-01, ND-01, HV-01**: phản đối cách sửa, không phản đối việc nêu. Tên trên bìa là tên đề tài đã đăng ký chính thức, nên đề xuất "thay bằng tên đề tài thật" (kèm tên gợi ý) không làm được nếu chỉ sửa `Cover.tex`. Ghi lại thành: tên đăng ký lệch nội dung, tác giả hỏi GVHD hoặc phòng đào tạo về thủ tục đổi tên. Chỉ sau khi có quyết định mới thì mới sửa hai tệp bìa và `pdftitle`.
2. **ND-02** (đặt mọi bảng của chương là `[H]`): phản đối. Build2 đã cho thấy hậu quả của `[H]`: tr. 49 gần trắng vì Bảng 5.14 `[H]` không vừa chỗ còn lại, và tr. 51 có hai khoảng trắng quanh Bảng 5.15. Nếu đổi thêm 12 bảng `[ht]` sang `[H]`, Ch5 sẽ có thêm khoảng chục trang nửa trắng, vì `twoside` bật `\flushbottom`. Xem Mâu thuẫn 1.
3. **GT-20** (đổi "lane 0/1/2" thành "làn 1/2/3 tính từ lề phải"): phản đối. Chỉ số làn tính từ 0 xuất hiện trong định danh mã và dữ liệu mà luận văn in ra: khóa `lane0_hold_s` (tr. 43), Bảng 5.10 (tr. 95, "chọn lane 0"), Bảng 5.1, caption Hình 5.6 ("làn 1 và làn 2"). Đánh số lại từ 1 trong văn xuôi sẽ tạo hai hệ đánh số cùng tồn tại, đúng loại lệch mà GT-21 và ND-15 đang bắt. Nên làm theo VP-05 và ND-15: định nghĩa một lần "làn 0 là làn ngoài cùng bên phải (chỉ số SUMO)" và vẽ chỉ số lên sơ đồ phân làn ở GT-03.
4. **GT-03** (thêm hai hình mới vào Ch5): đồng ý về nội dung, phản đối việc thêm hình riêng. Ch5 đã dài 68 trang. Nên thay Hình 5.1 (mã cạnh OSM, khó đọc, xem HB-05) bằng một hình gồm hai `subfigure`: (a) mặt bằng phân làn có kim chỉ Bắc, chỉ số làn và đoạn 30 m, (b) sơ đồ ba pha kèm thanh thời gian 42/4/2/16/4/2/44/4/2 s. Sau đó rút gọn đoạn văn xuôi tương ứng ở 5.1.3 (tr. 32–33) và rút Bảng 5.1 còn hai cột ngắn. Số trang gần như không đổi.
5. **HV-16, phương án "bỏ hẳn 5.13 và đưa Bảng 5.35 vào 1.5"**: phản đối. Bảng 5.35 gắn với SUMO (bề rộng làn ra, speed mode, `custom1`). Đưa nó vào 1.5 sẽ kéo chi tiết hiện thực lên chương mở đầu, trái tinh thần tách ý tưởng khỏi hiện thực mà GVHD đã chốt cho Ch3–4. Nên giữ Bảng 5.35 trong Ch5 theo HD-09.

### Mâu thuẫn

1. **Cách đặt float**: `[H]` cho mọi bảng (ND-02, GT-03) đối với `[!htbp]` kèm `\FloatBarrier` (HB-02, HV-09, HD-06). Tôi nghiêng về `[!htbp]` + `\usepackage[section]{placeins}` + `\raggedbottom`, chỉ giữ `[H]` cho bảng ngắn dưới khoảng 1/3 trang. Lý do: cách này vừa giữ bảng trong mục của nó, vừa không tạo trang nửa trắng (HB-08). Bảng cao như 5.1, 5.4 thì nên rút gọn hoặc chuyển phụ lục, thay vì ép bằng `[H]`.
2. **Số chữ số của S**: HB-11 (3 chữ số) đối với LG-17, HV-19 (2 chữ số kèm độ lệch chuẩn). Tôi rút đề xuất của mình và theo 2 chữ số. Các chênh lệch giữa phương án là 0,02–0,08 (ví dụ 1,14 so với 1,17 ở Bảng 5.32), nên 2 chữ số vẫn phân biệt được. Độ lệch chuẩn của S trên 15 lần chạy cho người đọc thước đo nhiễu. Quan trọng nhất là chỉ dùng một quy tắc cho mọi bảng, mọi đoạn văn và phụ lục A.5 (hiện ghi 3 chữ số).
3. **Đánh số làn**: GT-20 (1/2/3 từ lề phải) đối với VP-05, ND-15 (giữ 0/1/2, định nghĩa một lần). Tôi nghiêng về VP-05, ND-15, lý do ở Phản đối 3.
4. **Tên thay cho "dữ liệu đại diện"**: VP-07 ("dữ liệu thay thế"), HD-16 ("dữ liệu giả lập từ tài liệu"), GT-19 ("dữ liệu tổng hợp, dựng từ tài liệu"). Tôi nghiêng về GT-19. "Giả lập" dễ lẫn với đầu ra mô phỏng, mà luận văn lại nhấn mạnh bộ sinh độc lập với SUMO (tr. 83). "Thay thế" thì không nói dữ liệu đến từ đâu. Đổi tên nào cũng phải đổi cùng lúc ở caption (Bảng 5.10, 5.17), tiêu đề cột "Dữ liệu đại diện" và danh mục ký hiệu (HB-15).
5. **Tên các phiên bản mạng**: V1–V6 (VP-01), N1–N6 (HD-16, ND-03), v1…v6 (HV-03). Tôi nghiêng về N1–N6. Chữ "v" đã dùng cho phiên bản prompt (`v001`–`v005`, Bảng 5.11) và cho biến thể luật (v1–v3, Bảng 5.29). Cùng lúc nên bỏ mã F1–F3 của nhóm hành vi theo VP-03, để "F2" không còn hai nghĩa.
6. **Số phận Mục 5.13 (bảy giải pháp)**: HD-09 (rút còn Bảng 5.35 kèm mỗi giải pháp 2–3 câu), HV-05 (viết lại thành "hiện thực các đóng góp"), HV-16 (bỏ hẳn). Tôi nghiêng về HD-09. Cách này bỏ được 21 tiêu đề `\subsubsection` (VP-09, HB-13), giảm khoảng 8 trang, và không đẩy chi tiết SUMO lên Ch1.
7. **Phạm vi hành vi 7 và 8**: GT-01 (đưa ra ngoài phạm vi, bỏ khỏi Bảng 3.1) đối với HV-07, LG-18 (giữ danh mục 11, nói rõ 10 có cơ chế). Đây là quyết định nội dung của tác giả, không thuộc góc nhìn hình thức. Về hình thức, chỉ yêu cầu bốn chỗ nói cùng một điều: Mục 1.4.2 (tr. 5), Bảng 3.1 (tr. 16), 5.1.1 (tr. 30) và tóm tắt.
8. **Bảng hạng mục, số dòng mã, phiên bản thư viện**: HD-04 (cắt Bảng 5.14, 5.15) đối với HB-12, HV-15 (chuyển phụ lục). Tôi nghiêng về HD-04 với Bảng 5.14 (hạng mục, trạng thái) và 5.15 (số dòng mã), vì hai bảng này không phục vụ lập luận nào. Bảng 5.13 (thư viện) thì chuyển phụ lục, vì nó cần cho tái lập.
9. **Tên tập dữ liệu cuối**: ND-18 chốt "ngày đánh giá", GT-19 đề xuất "ngày kiểm định". Tôi nghiêng về GT-19, với điều kiện đổi đồng bộ cả "đánh giá cuối E1, E2" (tr. 45, 77, 100), để không còn một chỗ nào giữ tên cũ.

### Bỏ sót (góc nhìn hình thức)

1. **Chế độ `twoside` làm lề đóng gáy đổi bên, và chương mở ở trang chẵn.** `main.tex:1` khai báo `twoside`, `main.tex:5` đặt `left=3.5cm, right=2.5cm`. Ở chế độ hai mặt, `geometry` hiểu đó là lề trong và lề ngoài, nên trang chẵn có lề 3,5 cm ở bên phải. So tr. 3 (PDF tệp tr. 21, khối chữ lệch phải) với tr. 4 (PDF tệp tr. 22, khối chữ lệch trái). Nếu luận văn in một mặt, mọi trang chẵn chỉ còn 2,5 cm ở mép đóng gáy. Ngoài ra, mỗi chương mở bằng `\newpage` (`main.tex:240–263`), nên Ch3 (tr. 12), Ch4 (tr. 24) và Ch6 (tr. 98) bắt đầu ở trang chẵn, tức trang trái khi in hai mặt. Đề xuất: hỏi quy định in của trường. In một mặt thì bỏ `twoside`. In hai mặt thì thay `\newpage` trước mỗi `\chapter` bằng `\cleardoublepage`. Mẫu gốc (`_template_orig/main.tex`) cũng mắc lỗi này, nên sửa ở đây không làm lệch mẫu về mặt nội dung.
2. **Hai bảng luật trùng nhau, và chương ý tưởng trỏ sang một float ở cách 71 trang.** Bảng 3.2 (tr. 20) và Bảng 5.4 (tr. 91) cùng liệt kê sáu luật với tham số. Bảng 5.4 chỉ thêm miền giá trị và vClass, nhưng chép lại phần mô tả hành vi. Đoạn trước Bảng 3.2 ("nằm ở Chương 5 (Bảng 5.4)", tr. 19–20) đưa người đọc từ chương ý tưởng sang một bảng in ở tr. 91. Đề xuất: giữ Bảng 3.2 ở mức ý tưởng. Rút Bảng 5.4 chỉ còn các cột "Luật | Miền tham số trên SUMO | vClass", đặt ngay sau 5.2.2 bằng `[!htbp]`. Cách này cũng gỡ được một bảng cao khỏi hàng đợi float (HB-02).
3. **Bốn bảng "trạng thái" chồng nhau.** Bảng 5.5 (trạng thái thành phần, tr. 92), Bảng 5.6 (chức năng, cột "Trạng thái", tr. 93), Bảng 5.7 (sáu bước, cột "Trạng thái", tr. 94) và Bảng 5.14 (hạng mục, tr. 50) đều lặp "Đã triển khai/Hoàn thành" cho cùng các thành phần. Đề xuất: giữ một bảng duy nhất. Có thể chuyển nó thành bảng phủ hành vi mà HV-07 đề xuất (hành vi | cơ chế | có sự kiện trong B1 | chỉ số), để thông tin trạng thái phục vụ lập luận. Ba bảng còn lại thì bỏ.
4. **Hình 5.3 tách khỏi bảng số của nó.** Caption Hình 5.3 (tr. 54) viết "số trung bình nằm ở Bảng 5.17", nhưng Bảng 5.17 in ở tr. 96, trong khi hình và đoạn bàn luận ở tr. 53–54. Cặp hình–bảng này là bằng chứng mạnh nhất mà HV-02 và HD-07 muốn đưa lên tóm tắt. Đề xuất: đặt Bảng 5.17 bằng `[H]` ngay trước Hình 5.3 (bảng chỉ cao khoảng 1/3 trang), hoặc ghép hai cái thành một float chung bằng `\captionof`.
