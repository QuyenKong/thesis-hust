# Học viên cùng khóa, Vòng 2

Quy ước vị trí. "tr." là số trang in ở chân trang của PDF build2 (131 trang); trang trong tệp PDF bằng tr. + 18. Số dòng lấy theo nguồn hiện tại: `3_Rule_generation.tex`, `4_Rule_execution.tex`, `5_Experiments.tex`, `6_Conclusions.tex`. Trong Vòng 1, mình lấy số dòng từ chính bộ nguồn này nên số dòng không đổi, chỉ số trang đổi. Chương 6 của PDF cũ nay là Chương 5, Chương 7 nay là Chương 6.

Đối chiếu nhanh với bản mới. Hình 1.1 và Mục 3.1 đã khớp cách chia chương: Chương 3 sinh luật, Chương 4 làm bước 1–4. Chương 3 và Chương 4 không còn trỏ tới nhật ký thực nghiệm. Ngược lại, độ lệch về độ dài lại tăng: Chương 5 chiếm tr. 30–97 (68/101 trang thân bài), Chương 3 có 12 trang, Chương 4 có 6 trang. Các bảng của Chương 5 vẫn dồn về tr. 89–97, sau đoạn kết chương ở tr. 88.

## A. Tự kiểm lại

- **HV-01: cần sửa lại.** Coordinator cho biết đây là tên đề tài đã đăng ký, không phải chữ còn sót từ mẫu. Nhận xét đúng phải là: tên đăng ký ("Mô hình thế giới vĩ mô trong trò chơi máy tính", `Cover.tex:13`, `Cover2.tex:13`, PDF trang tệp 1–2) lệch với nội dung, tác giả cần hỏi GVHD hoặc phòng đào tạo về thủ tục đổi tên hoặc cách trình bày. Đừng tự sửa bìa. Mức vẫn là nghiêm trọng, vì hội đồng sẽ hỏi ngay câu này. Ý về `\TITLE` (`main.tex:73`, pdftitle đang là "LUẬN VĂN THẠC SĨ") vẫn đúng. Mình nhận phản đối của LG, HB và GT ở điểm này.
- **HV-02: còn đúng, nhưng cần sửa lại đề xuất** (`0_3_Abstract.tex:15`, PDF trang tệp 3–4; `6_Conclusions.tex:35–45`, tr. 99–100). Mình nhận cả ba ý của LG trong r2_logic. (1) Kết quả dương chỉ nên nêu vượt đèn đỏ (0% → 4,86%). Xe chờ giữa nút đã có sẵn ở B0 (4,00 mỗi chu kỳ, Bảng 5.17, tr. 96), và xuất phát sớm, vỉa hè, dừng quá vạch của B1 vẫn gần 0. (2) Câu "lỗi chủ yếu là lỗi cấu trúc" chỉ đúng với P2; P1 hỏng 14/15 lần vì tổng tỷ trọng (LG-12, tr. 75). (3) Với `accel`, viết "yếu tố lớn nhất trong các biến thể B1 đã thử ở PROXY_D1", không viết là nguyên nhân của cả ba chiến dịch (LG-01). Hướng chính của nhận xét không đổi: tóm tắt phải có câu kết quả viết theo đóng góp, không kể theo ngày.
- **HV-03: còn đúng** (`5_Experiments.tex:12` vẫn ghi "theo thứ tự thời gian"; 5.12 ở `5_Experiments.tex:712–1238`, tr. 55–77; Bảng 5.18, tr. 55). Mình đổi tên mạng đề xuất từ "v1…v6" sang N1–N6, vì "v" đã dùng cho phiên bản prompt v001–v005. Lý do lấy từ r2_logic và r2_hinhbang.
- **HV-04: còn đúng, sửa lại cách viết RQ1** (`1_Introduction.tex:78`, tr. 4; E1/E2 ở `5_Experiments.tex:503`, tr. 45). Mình nhận phản đối của GT: bỏ chữ "an toàn". RQ1 viết lại: "Bộ thực thi có tạo ra được hành vi vi phạm mà B0 không có, mà không làm tăng va chạm mô phỏng và số xe kẹt so với B0?" Theo LG, câu trả lời hiện tại cho vế sau là "chưa": B1 bị loại 15/15 lần chạy. Phải viết đúng như vậy. Theo khung GVHD, RQ đặt ở cuối 1.3 hoặc trong 1.4.1, không làm đổi mạch "lợi ích → tuy nhiên → hướng giải quyết".
- **HV-05: còn đúng** (`1_Introduction.tex:89–96`, tr. 5; 5.13 ở `5_Experiments.tex:1240–1420`, tr. 77–87; Bảng 5.35, tr. 97). Sau Vòng 2, cách sửa mình chọn là HD-09: mỗi giải pháp còn 2–3 câu và trỏ tới bằng chứng. Mình rút ý "bỏ hẳn 5.13 rồi đưa bảng lên 1.5", vì HB phản đối đúng: bảng đó gắn với SUMO, đưa lên Chương 1 là trái khung GVHD.
- **HV-06: còn đúng, sửa lại vị trí.** Phát biểu bằng ký hiệu θ = (σ, φ) và min S(θ) với ràng buộc đủ điều kiện và ngân sách nên đặt ở 3.1 (`3_Rule_generation.tex:10–19`, tr. 12). Mục này thuần ý tưởng, không gắn nút cụ thể, nên hợp khung GVHD. Chương 1 chỉ giữ câu văn xuôi ở 1.2. Có thể kèm 3–4 phương trình cho d, R, S ở 4.7.2 (HB-16).
- **HV-07: còn đúng** (`0_3_Abstract.tex:15`; `5_Experiments.tex:699`, tr. 54; Bảng 5.17, tr. 96). Mình nhận hai bổ sung: thêm cột "định nghĩa vận hành" (GT), và để bảng phủ hành vi thay chỗ một trong các bảng trạng thái 5.5, 5.6, 5.7 (r2_hinhbang, Bỏ sót 3), để Chương 5 không dài thêm.
- **HV-08: còn đúng.** Vị trí mới: `4_Rule_execution.tex:103` (tr. 29); `3_Rule_generation.tex:57` (tr. 15); "Phase 3A" ở `5_Experiments.tex:226, 596, 867, 877, 1395, 1430`; `5_Experiments.tex:1156` (caption Bảng 5.32 "Giờ Hà Nội ngày 08/11/2026"); `:665` (tr. 53); `Appendix_B.tex:22, 36`.
- **HV-09: còn đúng và nặng hơn.** Bảng 5.17 được bàn ở tr. 53–54 nhưng in ở tr. 96 (cách 43 trang). Các bảng 5.1–5.7, 5.10–5.12, 5.17, 5.35, 5.36 in ở tr. 89–97. Bảng 2.2 vẫn đứng một mình ở tr. 11.
- **HV-10: còn đúng** (`5_Experiments.tex:23`, tr. 30; Bảng 5.18, tr. 55; `glossary.tex` vẫn có 6 mục, tr. vi). Chốt cách sửa: bỏ mã F1–F3 của nhóm hành vi và đặt tên mạng là N1–N6.
- **HV-11: còn đúng** (`6_Conclusions.tex:43–53`, tr. 100–101). Mục Hạn chế nên gom thêm các ý của GT-05 (G0 tính trên số đếm 15 phút), LG-07 (chỉ 07:30–08:00), r2_logic Bỏ sót 2 (chọn đặc tả trên một seed, trong khi teleport của B1 dao động 0–63 tùy seed) và HV-18.
- **HV-12: còn đúng** (`5_Experiments.tex:532`, tr. 47). Câu ở `4_Rule_execution.tex:114` ("suy từ mô hình mặc định trên cùng mạng") mâu thuẫn trực tiếp với 5.8.3, xem LG-06.
- **HV-13: còn đúng về vị trí, sửa lại câu đề xuất** (`5_Experiments.tex:1230`, tr. 77; `Appendix_A.tex:100`, tr. 110; `6_Conclusions.tex:45, 51`, tr. 100). Mình nhận phản đối của LG và GT. Câu "làm hỏng năng lực thông qua" vừa khẳng định quá mức vừa sai thuật ngữ. Câu thay: "`accel` 1,1 m/s² chuyển từ IDM sang Krauss là yếu tố lớn nhất trong các biến thể đã thử; nó làm giảm khả năng thông hành mô phỏng nhưng riêng nó chưa giải thích hết xe chờ chèn." Ý chính vẫn giữ: chỉ nói một lần, không lặp "chưa được quyết định" ở bốn chỗ.
- **HV-14: còn một nửa.** Vế "PDF chưa có OPRO, FunSearch, Eureka" đã hết, vì ba công trình này nay ở 3.6.1 (`3_Rule_generation.tex:192`, tr. 21). Vế "Chương 2 chưa có bảng so sánh các công trình gần nhất" vẫn đúng (`2_Literature_review.tex:68–102`, tr. 9–11). Mình đồng ý với GT là bảng nên có thêm hàng phía giao thông (GT-18).
- **HV-15: còn đúng** (5.3–5.4 ở `5_Experiments.tex:237–392`, tr. 36–43; 5.9 ở `:537–632`, tr. 47–51; 5.14 ở `:1422+`, tr. 87–88). Theo r2_hinhbang: cắt Bảng 5.14 và 5.15, chuyển Bảng 5.13 sang phụ lục. Mình đồng ý. Thêm lưu ý của GT: Mục 5.1, Bảng 5.1 và Bảng 5.10 phải ở lại thân bài.
- **HV-16: còn đúng, sửa lại cách sửa.** Chọn HD-09, không bỏ hẳn 5.13 (xem HV-05). 5.13 còn chép số liệu cũ, ví dụ "sức chứa 8 xe" ở tr. 88 (LG-14).
- **HV-17: còn đúng** (`4_Rule_execution.tex:64`, tr. 27; `5_Experiments.tex:376`; Bảng B.1 ở `Appendix_B.tex:10–26`, tr. 112).
- **HV-18: còn đúng** (`5_Experiments.tex:570`, tr. 48; `1_Introduction.tex:31`, tr. 3).
- **HV-19: còn đúng** (Bảng 5.30, tr. 71; Bảng 5.32, tr. 74). HB đã rút đề xuất 3 chữ số và theo 2 chữ số. Áp dụng cho cả Bảng A.5.
- **HV-20: một phần đã hết.** Hình 5.3 nay có nhãn tiếng Việt (tr. 54). Hình 5.1 (tr. 31), Hình 5.4 và 5.5 (tr. 57–58) vẫn để tiếng Anh.

**Thứ đáng học (cập nhật).** Giữ nguyên bốn ý của Vòng 1. Đổi số: Bảng 6.2 thành Bảng 5.2 (tr. 90), Bảng 6.16 thành Bảng 5.17 (tr. 96). Bổ sung một ý: ranh giới chương nay khớp Hình 1.1 (tr. 3). Chương 3 và Chương 4 không nhắc tới nút cụ thể (grep "Lê Văn Lương", "07:30" trong hai tệp chỉ ra vài chỗ, đều trong chú thích nguồn). Đây là cách tách ý tưởng khỏi hiện thực mà mình muốn học, và là phần đừng cắt khi sửa Chương 5. Ý "Bảng 6.16 cùng Hình 6.3 là chứng cứ mạnh nhất" phải hẹp lại: chỉ đúng với vượt đèn đỏ (LG-03).

**Chuẩn bị bảo vệ (cập nhật).**
- Slide 4: chỉ nêu vượt đèn đỏ (B0 0%, B1 4,86%, dữ liệu đại diện 9,80%). Nói thẳng rằng xe chờ giữa nút do bản vá mạng cộng cơ chế sẵn có của SUMO tạo ra.
- Slide 5: tách P1 (lỗi tổng tỷ trọng) khỏi P2 (lỗi cấu trúc).
- Câu hỏi 5 cũ (dựa trên tiền đề "P2 hạ S bằng cách bỏ luật") thay bằng: "B2 không bỏ luật mà S vẫn thấp hơn P2. Vậy vì sao em thêm ràng buộc v005?" (LG-02).
- Câu hỏi mới 6: "Tên đề tài là trò chơi máy tính, nội dung là giao thông. Em giải thích thế nào?" Trả lời theo kết quả hỏi GVHD và phòng đào tạo.
- Câu hỏi mới 7: "B0 có 4 xe chờ giữa nút mỗi chu kỳ. Vậy luật rẽ trái chờ giữa nút đóng góp gì?" (LG-03).
- Câu hỏi mới 8: "Bảng 5.17 dùng các lần chạy B1 không đủ điều kiện. Số đó còn tin được không?" (xem Bỏ sót 2).

## B. Phản biện chéo

### Đồng ý

**r1_hoidong**
- HD-02: đồng ý, nghiêm trọng. Câu kết luận viết được ngay từ dữ liệu đang có, nhưng phải theo LG-01 và LG-12.
- HD-03: đồng ý. Trùng HV-04. Bảng nối đóng góp, câu hỏi và bằng chứng làm trong một buổi.
- HD-04: đồng ý, nay áp cho Chương 5. Khả thi trước 12/2026 nếu cắt 5.3 (trùng Chương 3–4 và Hình 1.1) cùng Bảng 5.14, 5.15, và chuyển 5.4.3, 5.9, 5.14 sang Phụ lục C.
- HD-05: đồng ý, vẫn còn ở 5.12. Kèm điều kiện của LG: các giới hạn nằm trong mục bị chuyển đi phải đưa vào mục Hạn chế.
- HD-06: đồng ý, nặng hơn trên bản mới (xem HV-09).
- HD-07: đồng ý về hướng. Ý (2) và ý (4) phải sửa theo LG-03 và LG-01.
- HD-08: đồng ý phần giải thích. Không đổi tên thuật ngữ (xem Mâu thuẫn 5). Không dùng chữ "an toàn" (GT).
- HD-09: đồng ý. Đây là cách sửa mình chọn cho 5.13. Mục 5.2.1 vẫn lặp gần nguyên văn 4.1 (tr. 24 so với tr. 35).
- HD-11: đồng ý thêm mục Hạn chế. Phần `accel` sửa theo LG-01.
- HD-12: đồng ý. Đưa một đặc tả P2 kèm trường lý do vào phụ lục là việc rẻ mà giá trị cao. Hình S theo vòng thì cần script mới, làm sau.
- HD-13: đồng ý. Ba bốn câu về cách tìm tài liệu, làm nhanh.
- HD-14: đồng ý, quan trọng khi bảo vệ. TODO_CITE vẫn còn ở tr. 15.
- HD-15: đồng ý, vẫn còn ở tr. 4, 15, 29, 55, 100.
- HD-16: đồng ý. Phần đổi tên "dữ liệu đại diện" xem Mâu thuẫn 2.
- HD-17: đồng ý, vẫn sai. Mục lục ghi Tài liệu tham khảo ở tr. 104, thực tế bắt đầu ở tr. 102.
- HD-18: đồng ý.

**r1_nguoidoc**
- ND-02, ND-03, ND-04, ND-07, ND-12, ND-14: đồng ý, trùng nhận xét đã nêu và vẫn còn trên bản mới.
- ND-05: đồng ý. Hội đồng CNTT chắc chắn hỏi IDM khác Krauss chỗ nào. Một trang "Khái niệm cơ bản" ở Chương 2 làm được trước hạn.
- ND-06: đồng ý, rẻ: định nghĩa ngay ở lần dùng đầu. "Xe chờ chèn" ở `4_Rule_execution.tex:112` (tr. 29) vẫn chưa được định nghĩa.
- ND-08: đồng ý. Thêm cột tên ngắn cho Bảng 4.1 (tr. 28), ví dụ M8 (đi sai làn), M9 (chặn làn rẽ phải).
- ND-09: đồng ý. Bảng 5.36 nên đứng cạnh 5.2.2.
- ND-10, ND-11: đồng ý. Gộp với HB-15 thành một bảng tra mã và ký hiệu.
- ND-13: đồng ý, kèm điều kiện về khung GVHD. Nếu ví dụ dùng HDT_S thì phải đặt ở Chương 5 (5.2). Nếu đặt cuối Chương 4 thì phải viết chung, không có tên nhánh.
- ND-15, ND-16, ND-17, ND-18: đồng ý. Thêm cột "Ý nghĩa" cho Bảng 5.3, vì Bảng A.1 cũng không có cột này.

**r1_vanphong**
- VP-01: đồng ý. Bỏ đoạn tự bác ở `5_Experiments.tex:1047–1049` là việc rẻ nhất.
- VP-02, VP-03, VP-04, VP-06, VP-11, VP-12, VP-16, VP-17: đồng ý. "Mã tất định" đúng hơn "mã xác định".
- VP-05: đồng ý thống nhất "làn 0/1/2" (xem Mâu thuẫn 1).
- VP-07: đồng ý. Tên thay thế xem Mâu thuẫn 2.
- VP-08: đồng ý giữ một câu nối thay cho đoạn tóm tắt cuối chương.
- VP-09: đồng ý. Hai tiêu đề "a, Tham số tĩnh", "b, Luật có điều kiện" vẫn treo dưới 5.2 (tr. 33–34).
- VP-10: đồng ý, mức nhỏ.
- VP-13: đồng ý. `2_Literature_review.tex:66` nói "ba giới hạn" nhưng liệt kê bốn ý (tr. 9).
- VP-14: đồng ý, ưu tiên thấp.
- VP-15: đồng ý. "cài đặt, Máy chính" vẫn còn ở tr. 87.

**r1_hinhbang**
- HB-02: đồng ý. Dùng `[!htbp]`, `\usepackage[section]{placeins}` và `\raggedbottom`. Đây là sửa một lần mà gỡ được nhiều lỗi nhất.
- HB-03, HB-05, HB-06, HB-07, HB-08, HB-10, HB-11, HB-12, HB-13, HB-14, HB-15: đồng ý, vẫn còn trên bản mới. Ví dụ dòng tràn lề ở tr. 38 và tr. 53; số trang dính vào hàng chấm ở mục lục cho mục 6.1.5.
- HB-04: đồng ý với Hình 5.4 và 5.5. Hình 5.3 đã Việt hóa.
- HB-16: đồng ý. Ba bốn phương trình cho d, R, S là việc rẻ và gỡ luôn một phần HV-06.
- HB-17: đồng ý với listing đặc tả JSON. Đây là câu trả lời nhanh nhất cho câu hỏi "LLM trả về cái gì". Hình kiến trúc TikZ ưu tiên thấp.
- HB-18: đồng ý, ưu tiên thấp.
- HB-20: đồng ý, trùng HV-09.

**r1_logic**
- LG-01: đồng ý, nghiêm trọng. Mình đã kiểm lại Bảng 5.34 (tr. 76): trả `accel` về mặc định vẫn còn 10, 126, 52 xe chờ chèn. B2 thử `t000` với `accel` 5,8 vẫn còn 256 xe.
- LG-02: đồng ý. S của B2 là 1,1438, nhỏ hơn S của P2 là 1,1680, nên "bỏ luật" không phải điều kiện cần để có S thấp.
- LG-03: đồng ý, nên nâng lên ngang các ý chính khi bảo vệ. Định nghĩa B0 ở Bảng 5.12 (`5_Experiments.tex:488`) phải nói rõ B0 chạy trên mạng có bản vá và có lớp xe vi phạm.
- LG-04: đồng ý. `1_Introduction.tex:67` (tr. 4) vẫn viết "không thể khớp nhờ va chạm".
- LG-05, LG-06, LG-07, LG-08: đồng ý.
- LG-09: đồng ý chọn cách rẻ: thêm câu "hành vi 9 và 11 chưa có chỉ số riêng" và nêu ngoại lệ cho δ. Không gỡ kiểm tra `coverage`, vì gỡ thì phải chạy lại chiến dịch.
- LG-10: đồng ý. Thêm một câu dưới Bảng 5.10 giải thích cách đổi định nghĩa từ 5 s sang 10 s.
- LG-11: đồng ý, đã kiểm lại. Bảng 5.1 trỏ "(Mục 3.5)" (Biểu diễn luật) cho lựa chọn cắt về (tr. 89). Bảng 2.2 trỏ "(Mục 1.4)" cho 11 hành vi (tr. 11). Cả hai đều sai.
- LG-12: đồng ý.
- LG-13: đồng ý. Đổi "Bộ luật thu được" thành "Bộ luật mục tiêu" vẫn giữ được mở đầu bằng lợi ích theo khung GVHD.
- LG-14: đồng ý. Câu "sức chứa 8 xe" vẫn ở tr. 88.
- LG-15: đồng ý, nên nâng mức (xem Bỏ sót 3).
- LG-16: đồng ý một phần. Thêm cột S_sourced và S_assumed nếu dữ liệu đã có. Bảng R thì tốn công hơn; cách rẻ là sửa `4_Rule_execution.tex:105` thành "phản hồi cho LLM dùng R".
- LG-17, LG-18, LG-19, LG-20: đồng ý.

**r1_giaothong**
- GT-01: đồng ý rằng bốn chỗ (1.4.2, Bảng 3.1, 5.1.1, tóm tắt) phải nói cùng một điều. Giữ hay bỏ hành vi 7, 8 là quyết định của tác giả với GVHD. Cách rẻ và khả thi nhất: đổi "hoãn" thành "ngoài phạm vi, kèm lý do" cho hành vi 8, và giữ hành vi 7 vì đã có mô hình và có M10.
- GT-02: đồng ý. Hành vi 6 đang gọi một hành vi đúng luật là lệch chuẩn. Sửa chữ, không cần chạy lại.
- GT-03: đồng ý. Sơ đồ phân làn và sơ đồ pha bằng TikZ mất khoảng nửa ngày, dùng lại được cho slide. Đặt ở 5.1, đúng khung GVHD.
- GT-04: đồng ý. Chỉ cần nêu quy tắc phân loại một lượt xe vào M2 hay M3, và cách xử lý đèn vàng.
- GT-05: đồng ý sửa bằng câu chữ: không gọi tiêu chí này là tiêu chí TAG, và ghi rõ GEH tính trên số đếm 15 phút. Tính lại G0 cho mọi lần chạy thì để sau.
- GT-06, GT-07, GT-08, GT-09, GT-10: đồng ý, đều rẻ.
- GT-11: đồng ý. Thêm cột "đo ở đâu" có thể đặt ở Phụ lục B để Bảng 4.1 khỏi phình.
- GT-12: đồng ý, mức nhỏ. Cần kiểm tra lại vạch sơn tại hiện trường.
- GT-13: đồng ý phần đoạn văn nối M1, M5, M6 với các chỉ số quen thuộc. Phần báo cáo thêm độ trễ để sau.
- GT-14, GT-15, GT-17, GT-21: đồng ý. `tau` là giãn cách thời gian mong muốn, không phải thời gian phản ứng.
- GT-18: đồng ý trích bài gốc cho Krauss, IDM và hướng dẫn hiệu chỉnh. Mảng mô hình xe máy thì làm theo khả năng.
- GT-19: đồng ý về "dữ liệu đại diện". Phần đổi tên "ngày đánh giá" xem Mâu thuẫn 4.

### Phản đối

- **HD-01, ND-01, HB-01 (và HV-01 của mình): đã hết theo cách đang viết.** Tên trên bìa là tên đăng ký, nên các tên gợi ý trong HD-01 và ND-01 không được tự đưa lên bìa. Sửa đúng: tác giả hỏi GVHD hoặc phòng đào tạo. Phần macro và pdftitle của HB-01 vẫn giữ.
- **HD-10: đã hết phần chính.** Caption Hình 1.1 nay ghi "các bước 1–4 là mã xác định (Chương 4)" (tr. 3). Mục 3.1 viết "Phương pháp gồm hai phần" (tr. 12). Chương 3 không còn trỏ tới 5.12.x. Chỗ còn lại là Chương 3 trỏ tới Bảng 5.4 để lấy miền giá trị (tr. 19–20), chấp nhận được vì đó là chi tiết hiện thực.
- **HB-09, phần chuyển 54 bảng sang `booktabs`:** phản đối. Tốn công, rủi ro vỡ bảng sát hạn nộp, và mẫu SoICT gốc vẫn dùng bảng kẻ lưới. Chỉ làm phần rẻ: cột `>{\raggedright\arraybackslash}p{}`, cấm ngắt gạch nối trong `\texttt`, và nới cột vClass của Bảng A.3.
- **HB-19, ý "bật lại Lời cảm ơn":** phản đối nếu chưa hỏi. `main.tex:158` ghi "tạm bỏ theo yêu cầu (28/10/2026)", tức có người đã yêu cầu bỏ. Ý giới hạn 200–350 từ cho tóm tắt thì đồng ý, vì đây là quy định của mẫu.
- **GT-16 (bảng v/c theo nhánh và pha):** phản đối. Bảng này thêm một lớp giá trị giả định (lưu lượng bão hòa) mà ít lợi với hội đồng CNTT. Câu hỏi "nhu cầu có khả thi không" đã có câu trả lời rẻ hơn: B0 không còn xe chờ chèn ở cùng nhu cầu (15/15 lần chạy đủ điều kiện, Bảng 5.30). Chỉ cần thêm một câu nói điều này.
- **GT-20, ý "làn 1/2/3 tính từ lề phải":** phản đối (xem Mâu thuẫn 1). Các ý thuật ngữ khác của GT-20 thì đồng ý: "khả năng thông hành", "thời gian đỏ", "giãn cách thời gian".
- **ND-19, ý thay "stick-breaking":** phản đối nhẹ. Hội đồng CNTT biết thuật ngữ này. Giữ lại và thêm nửa câu giải thích. Các ý còn lại của ND-19 thì đồng ý.
- **HD-04, mục tiêu "Chương 6 còn khoảng 30 trang":** phản đối con số, không phản đối hướng. Xuống 30 trang buộc phải viết lại 5.12, không kịp hạn 12/2026. Mục tiêu thực tế là khoảng 45 trang, đạt được bằng cách cắt hoặc chuyển 5.3, 5.4.3, 5.9, 5.14, chuyển các mạng cũ sang phụ lục, và rút 5.13 theo HD-09.

### Mâu thuẫn

1. **Đánh số làn:** VP-05 và ND-15 muốn "làn 0/1/2" như chỉ số SUMO; GT-20 muốn "làn 1/2/3 tính từ lề phải". Mình nghiêng về VP-05. Lý do: Bảng 5.1, Bảng 5.18, khóa `violator_turn_lanes` và các luật đều dùng chỉ số 0, đánh số lại 44 chỗ cộng hình vẽ rất dễ sót. Thêm một câu định nghĩa ở 5.1.3 và vẽ số làn lên sơ đồ phân làn (GT-03).
2. **Tên thay cho "dữ liệu đại diện":** "dữ liệu thay thế (proxy)" (VP-07), "dữ liệu giả lập từ tài liệu" (HD-16), "dữ liệu tổng hợp" (GT-19). Mình nghiêng về VP-07. Nó khớp tên PROXY_D1–D5. Còn chữ "tổng hợp" dễ lẫn với bộ dữ liệu tổng hợp chỉ dùng để thử đường ống mà dự án tách riêng, không bao giờ đưa vào kết quả.
3. **Tên mạng và mã nhóm hành vi:** V1–V6 (VP-01), N1–N6 (HD-16, ND-03), v1…v6 (HV-03 cũ). Chọn N1–N6, đồng thời bỏ F1–F3. Lý do như r2_logic và r2_hinhbang.
4. **"Ngày đánh giá" (ND-18) hay "ngày kiểm định" (GT-19):** mình nghiêng về giữ "ngày đánh giá". Định nghĩa một lần rằng nó tương đương bước kiểm định (validation) trong ngành giao thông. Người đọc chính là hội đồng CNTT, và chữ này đã gắn với "đánh giá cuối E1, E2" ở nhiều chỗ, đổi thì tốn công mà dễ lệch.
5. **Thuật ngữ "đủ điều kiện":** HD-08 muốn đổi thành "qua bộ lọc an toàn"; GT phản đối chữ "an toàn"; VP-04 và ND-07 muốn giữ và giải thích. Chọn giữ "đủ điều kiện", và ở tóm tắt cùng Chương 6 thêm mệnh đề "(không kẹt, không còn xe chờ chèn, qua G0, va chạm mô phỏng dưới ngưỡng)".
6. **Cắt hay chuyển phụ lục:** HD-04 muốn cắt; HB-12 và HV-15 muốn chuyển. Chọn như r2_hinhbang: cắt 5.3 cùng Bảng 5.14, 5.15; chuyển Bảng 5.9, 5.13, 5.16 và 5.14 sang Phụ lục C.
7. **Đặt float:** `[H]` cho mọi bảng (ND-02, GT-03) hay `[!htbp]` cộng `placeins` (HB-02, HV-09). Chọn HB-02. Riêng Bảng 5.17 nên đặt `[H]` ngay trước Hình 5.3 (r2_hinhbang, Bỏ sót 4).
8. **Hành vi 7, 8:** GT-01 có phương án bỏ; HV-07 và LG-18 chỉ yêu cầu viết lại cho chính xác. Chọn viết lại, như r2_logic. Bỏ hai hành vi kéo theo xóa kết quả đã báo cáo, không kịp hạn.

### Bỏ sót

1. **Thủ tục tên đề tài phải làm ngay tuần này.** Không ai tính đến thời gian. Đổi tên đề tài thường cần đơn, chữ ký GVHD và quyết định của trường, và có thể không kịp trước hạn nộp 12/2026. Nếu không đổi được, tác giả cần một đoạn ở 1.1 nối tên đăng ký với nội dung, và chuẩn bị câu trả lời trước hội đồng. Việc này phải xong trước khi sửa bất kỳ chỗ nào khác của bìa.
2. **Kết quả dương duy nhất lấy từ các lần chạy không đủ điều kiện.** Bảng 5.17 (tr. 96) dùng 15 lần chạy B1 của `REF_n1104s5`, mà theo Mục 5.12.14 cả 15 lần đều bị loại (tr. 71–72). Hội đồng sẽ hỏi vì sao lần chạy bị chính tiêu chí của luận văn loại lại được dùng làm bằng chứng. Phải nói trước trong phần Diễn giải của 5.11 (`5_Experiments.tex:699`, tr. 54): B1 bị loại vì xe chờ chèn ở PROXY_D1 và vì va chạm liên quan can thiệp, và các tỷ lệ vượt đỏ vẫn đọc được vì tính trên xe đã qua vạch. Nếu đúng như vậy thì thêm một dòng số liệu chỉ trên PROXY_D2–D3.
3. **Bảng 5.31 dựa trên một chiến dịch không rõ nguồn LLM.** LG-15 nêu vấn đề, nhưng mức "nên sửa" là thấp. Caption Bảng 5.31 (`5_Experiments.tex:1135`, tr. 73) ghi "dựng lại từ kết quả chiến dịch P2 trên mạng 28/10 đợt 2", trong khi 5.12.8 (tr. 65) nói P1, P2 với `qwen3.5:9b` chưa có kết quả trên các mạng này. Nếu chiến dịch đó không do `qwen3.5:9b` sinh, cách sửa an toàn và rẻ nhất là bỏ Bảng 5.31 và đoạn đi kèm, không cố giải thích. Bảng này chỉ dùng để biện minh cho v004, và lý do đó đã nêu được bằng chữ.
4. **Ngân sách 36 lần chạy không được giải thích.** `5_Experiments.tex:526` (tr. 46) chỉ nói 36 lần chạy tương ứng 12 đặc tả, không nói vì sao chọn 36. Với hội đồng CNTT, 12 thử nghiệm Optuna là rất ít; họ sẽ hỏi TPE với 4 thử nghiệm khởi đầu ngẫu nhiên thì học được gì trong 8 lần còn lại. Một câu về thời gian chạy (88–463 s mỗi lần chạy, tr. 88; 1,5–3,5 phút mỗi lần gọi LLM, tr. 75) và về mục tiêu "so sánh ở ngân sách nhỏ, sát thực tế dùng" là đủ. Nếu không có lý do thì đưa vào mục Hạn chế.
5. **Cần phương án dự phòng cho trường hợp E1/E2 không kịp.** Tóm tắt (tr. 4), Chương 6 (tr. 100) và `5_Experiments.tex:710` đều có TODO giữ chỗ cho kết quả chưa chạy. Tác giả nên chốt ngay một trong hai bản. Bản có E1/E2: các chỗ giữ chỗ được điền. Bản không có E1/E2: xóa mọi TODO, chuyển thiết kế E1/E2 sang "Hướng phát triển", và đặt RQ3 rõ là "chưa trả lời". Viết theo bản không có E1/E2 trước thì luận văn luôn nộp được, kết quả về sau chỉ cần thêm vào. Nhân tiện: phần thiết kế so sánh ở 5.7 (`5_Experiments.tex:470–507`), gồm sáu phương án và E1, E2, là ý tưởng, không gắn với nút. Theo khung GVHD có thể chuyển sang cuối Chương 4. Như vậy E1/E2 xuất hiện ở tr. khoảng 29 thay vì tr. 45, gỡ được một phần HV-04 mà không phải viết thêm.
