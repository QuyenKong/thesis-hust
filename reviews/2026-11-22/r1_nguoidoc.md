# Người đọc ngoài chuyên ngành

> Ghi chú phạm vi. PDF được giao (128 trang) build từ bản 7 chương: `5_Evaluation.tex`, `6_Implementation.tex`, `7_Conclusions.tex` (theo `main.log`, dòng 1778–3004). Thư mục `Chapter/` trên đĩa hiện chỉ có bản 6 chương: `5_Experiments.tex` và `6_Conclusions.tex`; `main.tex` cũng đã đổi theo. Vì vậy số mục và số trang dưới đây theo PDF. Dòng nguồn trỏ tới file hiện có trên đĩa nếu đoạn văn còn nguyên: Chương 6 của PDF tương ứng với `Chapter/5_Experiments.tex`; Mục 3.6 và Chương 5 của PDF nay nằm trong `Chapter/4_Rule_execution.tex`. Trang ghi theo dạng "PDF tr. N (tr. in M)", với tr. in = PDF − 18 ở phần thân.

## Đánh giá tổng quát

Chương 1–5 đọc được. Ý chính "LLM sinh luật ngoài vòng mô phỏng, mã xác định thực thi và chấm" rõ nhờ Hình 1.1 và các đoạn "biến đệm, hậu quả nếu thiếu". Vấn đề nằm ở Chương 6. Đọc chương này, người ngoài ngành gặp liên tiếp mã nội bộ chưa giải thích: tên mạng theo ngày, "F2" mang ba nghĩa, mã chiến dịch, bit của speed mode. Thêm vào đó, kết quả chính bị chôn trong 19 tiểu mục xếp theo thứ tự ngày tháng, còn mười hai bảng (có cả bảng so sánh B0 với B1 và bảng giá trị mục tiêu) bị LaTeX đẩy về cuối chương, cách chỗ dẫn 40–60 trang. Kết luận chính của luận văn ("gia tốc xe máy 1,1 m/s² lấy từ IDM sang Krauss gây xe chờ chèn") dựa trên ba khái niệm chưa được định nghĩa cho người ngoài ngành: mô hình bám xe, xe chờ chèn và teleport. Ngoài ra, bìa luận văn vẫn mang tên đề tài của mẫu.

## Nhận xét

### [ND-01] Bìa và bìa lót ghi sai tên đề tài
- Mức: nghiêm trọng
- Vị trí: Cover.tex:13, Cover2.tex:13 (PDF tr. 1–2)
- Trích: "Mô hình thế giới vĩ mô trong trò chơi máy tính"
- Vấn đề: Tên trên bìa là tên đề tài của file mẫu, không liên quan tới nội dung luận văn.
- Vì sao quan trọng: Đây là dòng chữ đầu tiên hội đồng đọc, nên họ sẽ hiểu sai luận văn nói về gì ngay từ trang 1.
- Đề xuất sửa: Thay bằng tên đề tài thật ở cả hai file, ví dụ "Sinh và tinh chỉnh luật hành vi người lái bằng mô hình ngôn ngữ lớn cục bộ cho mô phỏng giao thông hỗn hợp tại nút giao có đèn".

### [ND-02] Mười hai bảng bị đẩy về cuối Chương 6, cách chỗ dẫn 40–60 trang
- Mức: nghiêm trọng
- Vị trí: Chapter/5_Experiments.tex:80, 121, 146, 180, 218, 245, 284, 405, 446, 677, 1247 (các bảng `[ht]`); PDF tr. 104–112 (tr. in 86–94); danh mục bảng PDF tr. 15–17
- Trích: Mục 6.1.2 ở tr. in 29 viết "Bảng 6.1 liệt kê chi tiết", nhưng Bảng 6.1 nằm ở tr. in 86. Mục 6.10 ở tr. in 50 viết "Bảng 6.16 cho thấy SUMO mặc định không có lượt vượt đèn đỏ nào", nhưng Bảng 6.16 nằm ở tr. in 93.
- Vấn đề: Các bảng đặt `[ht]` bị dồn lại sau các bảng `[H]`, nên toàn bộ trôi về cuối chương: Bảng 6.1–6.7, 6.10 (giá trị mục tiêu), 6.11 (phiên bản prompt), 6.16 (so sánh B0, B1, dữ liệu đại diện), 6.34, 6.35. Danh mục bảng vì thế xếp lộn thứ tự (6.8, 6.9, 6.12… rồi mới 6.1).
- Vì sao quan trọng: Bảng 6.16 là bằng chứng trực quan duy nhất cho thấy bộ thực thi tạo ra hành vi mà SUMO mặc định không có. Bảng 6.2–6.4 là chỗ người đọc cần để hiểu phần SUMO. Muốn đọc chúng, người đọc phải lật đi lật lại vài chục trang.
- Đề xuất sửa: Đặt mọi bảng của chương này là `[H]`, hoặc dùng `[htbp]` kèm `\FloatBarrier` (gói `placeins`) ở cuối mỗi mục. Sau khi sửa, kiểm tra lại thứ tự trong danh mục bảng.

### [ND-03] Tên mạng theo ngày dùng trước khi định nghĩa, còn "F2" mang ba nghĩa
- Mức: nghiêm trọng
- Vị trí: Chapter/5_Experiments.tex:12, 232, 454, 532 (dùng); 716–734 (Bảng 6.17 định nghĩa); 23 và 397 (F2 = nhóm hành vi); 596 (F2 = mã hạng mục); PDF tr. 46, 62, 70, 59 (tr. in 28, 44, 52, 41)
- Trích: tr. in 28: "Ba chiến dịch B2, P1 và P2 … đã chạy trên mạng 04/11". tr. in 44: "suy từ B0 trên mạng F2 … 2,667 và 1,333 va chạm/h trên hai mạng ngày 28/10". tr. in 41: "ba bảng cho nhóm F2 là chuỗi thời gian hàng chờ…"
- Vấn đề: Các tên "mạng F2", "mạng 28/10 đợt 1/2", "mạng 29/10", "mạng 04/11" xuất hiện từ phần tóm tắt ("Trên mạng ngày 27/10") và từ trang đầu Chương 6. Bảng 6.17, nơi định nghĩa chúng, mãi đến tr. in 52 mới có. Thêm vào đó, F2 vừa là nhóm hành vi "tìm khoảng trống khi ùn" (tr. in 28), vừa là tên một phiên bản mạng, vừa là mã hạng mục trong Bảng 6.13.
- Vì sao quan trọng: Đọc "mạng F2" ngay sau "nhóm F2", người đọc sẽ nghĩ đó là mạng dành cho nhóm hành vi F2. Gặp tên mạng theo ngày trước khi biết sáu phiên bản khác nhau ở đâu, người đọc không hiểu vì sao số liệu thay đổi.
- Đề xuất sửa: (1) Chuyển Bảng 6.17 lên Mục 6.1, ngay sau Hình 6.2, và thêm một câu: "Kịch bản đổi theo các đợt khảo sát hiện trường; mỗi phiên bản mạng được gọi theo ngày dựng. Kết quả chính dùng mạng 04/11." (2) Đổi tên mạng để không trùng tên nhóm, ví dụ N1–N6 hoặc "mạng v1 (27/10)". (3) Bỏ mã "F2" ở Bảng 6.13, thay bằng số thứ tự. (4) Trong phần tóm tắt, thay "Trên mạng ngày 27/10" bằng "Trên phiên bản kịch bản đầu tiên (đèn hai pha)".

### [ND-04] Mục 6.11 viết theo nhật ký thời gian nên kết quả chính bị chôn
- Mức: nghiêm trọng
- Vị trí: Chapter/5_Experiments.tex:712–1238; PDF tr. 70–92 (tr. in 52–74), Mục 6.11.1–6.11.20
- Trích: Tên các tiểu mục: "6.11.9 Cập nhật kịch bản và kết quả trên hai mạng ngày 28/10", "6.11.14 Thay đổi ngày 04/11 và kết quả tham chiếu trên mạng 04/11", "6.11.17 Chiến dịch B2, P1, P2 trên mạng 04/11", "6.11.19 Nguyên nhân xe chờ chèn ở PROXY_D1"
- Vấn đề: 19 tiểu mục kết quả xếp theo ngày, trộn kết quả hiện hành với kết quả trên những mạng đã bỏ. Các câu như "Phần không còn áp dụng trên mạng 29/10" (tr. in 61) buộc người đọc tự tính xem điều gì còn đúng. Ba kết quả thật sự trả lời câu hỏi nghiên cứu nằm rải rác ở 6.11.14, 6.11.17 và 6.11.19: B0 đủ điều kiện ở 15/15 lần chạy trên mạng hiện hành, ba chiến dịch không có đặc tả nào đủ điều kiện, và nguyên nhân là `accel` của xe máy.
- Vì sao quan trọng: Hội đồng sẽ không biết đâu là kết quả của luận văn và đâu là lịch sử gỡ lỗi. Đọc theo kiểu nhật ký còn làm phương pháp có vẻ chắp vá hơn thực tế.
- Đề xuất sửa: Tách 6.11 thành hai phần. Phần "Kết quả trên kịch bản hiện hành (mạng 04/11)" gồm tham chiếu B0/B1, ba chiến dịch, hành vi của `qwen3.5:9b` và phân tích nguyên nhân xe chờ chèn. Phần "Các thí nghiệm khả thi và chẩn đoán trong quá trình xây dựng" gồm 6.11.2–6.11.13 và 6.11.15–6.11.16, có thể chuyển một phần sang phụ lục. Mở đầu 6.11 bằng ba câu tóm tắt kết quả chính.

### [ND-05] Thiếu khái niệm nền của giao thông và SUMO, nên kết luận chính không hiểu được
- Mức: nghiêm trọng
- Vị trí: Chapter/2_Literature_review.tex:27, 29, 54, 64 (PDF tr. 24–26, tr. in 6–8); Chapter/5_Experiments.tex:1230 (PDF tr. 91, tr. in 73)
- Trích: tr. in 7: "tham số bám xe (mặc định là mô hình Krauss)". tr. in 8: "Mô hình dùng bám xe IDM và chuyển làn MOBIL". tr. in 6: "headway 1,16 ± 0,65 s", "Hệ số quy đổi xe máy khoảng 0,24", "thời gian tổn thất khởi động". tr. in 73: "Giá trị này chuyển từ gia tốc cực đại a của mô hình IDM … sang accel của mô hình Krauss"
- Vấn đề: Luận văn không có đoạn nào giải thích mô hình bám xe (car-following) hay mô hình chuyển làn là gì, Krauss khác IDM thế nào, và headway, lưu lượng bão hòa, hệ số quy đổi, tổn thất khởi động, pha và chu kỳ đèn nghĩa là gì. Mục 2.2 chỉ liệt kê tên.
- Vì sao quan trọng: Phát hiện chính trong tóm tắt và Mục 6.11.19 là "gia tốc chuyển giao từ tài liệu". Không biết hai mô hình dùng tham số `accel` theo nghĩa khác nhau thì người đọc không hiểu vì sao chép 1,1 m/s² lại thành lỗi. Bảng 2.1 và Bảng 6.10 cũng phần lớn không đọc được.
- Đề xuất sửa: Thêm vào đầu Mục 2.2 một tiểu mục khoảng một trang tên "Khái niệm cơ bản". Tiểu mục này giải thích bằng 1–2 câu cho mỗi khái niệm: mô hình bám xe ("xe sau chọn tốc độ theo khoảng cách và tốc độ xe trước"), Krauss và IDM, mô hình chuyển làn, headway, lưu lượng bão hòa, pha, chu kỳ, đỏ toàn phần. Kèm một hình nút giao có ghi chú vạch dừng, nhánh vào, làn nội bộ, kết nối, liên kết đèn. Ở Mục 6.11.19, thêm một câu nói rõ vì sao giá trị `a` của IDM không tương đương `accel` của Krauss.

### [ND-06] Bốn khái niệm cốt lõi chưa định nghĩa hoặc định nghĩa sau khi đã dùng
- Mức: nghiêm trọng
- Vị trí:
  - "xe chờ chèn": Chapter/4_Rule_execution.tex:112 (PDF tr. 43, tr. in 25); dùng hơn 30 lần trong Chapter/5_Experiments.tex
  - "teleport": dùng trước ở Chapter/5_Experiments.tex:299, 444, 532 (tr. in 35, 42, 44), định nghĩa ở dòng 738 (tr. in 52)
  - "chiến dịch": Chapter/3_Rule_generation.tex:198 (PDF tr. 36, tr. in 18)
  - "khóa": Chapter/4_Rule_execution.tex:107 (PDF tr. 43, tr. in 25)
- Trích: "(ii) không còn xe chờ được đưa vào mạng khi lần chạy kết thúc". "Prompt có phiên bản và được khóa theo từng chiến dịch". "trong mỗi nhóm chia đều cho các chỉ số con …, rồi cho các khóa"
- Vấn đề: Luận văn không giải thích vì sao lại có xe "chờ được đưa vào mạng" (SUMO chỉ thả xe vào khi đầu cạnh vào còn chỗ, nên khi ùn thì xe xếp hàng ngoài mạng). "Teleport" chỉ được định nghĩa sau khi đã xuất hiện ba lần. "Chiến dịch" không có định nghĩa nào. "Khóa" trong công thức điểm tổng S cũng không có định nghĩa.
- Vì sao quan trọng: Kết quả chính (P1 không thể đủ điều kiện vì B1 còn xe chờ chèn ở PROXY_D1) và cách tính điểm S đều dựa trên các khái niệm này.
- Đề xuất sửa: Định nghĩa ngay ở lần dùng đầu. Ví dụ, tr. in 25: "(ii) không còn *xe chờ chèn*, tức xe đã đến giờ xuất phát nhưng chưa được thả vào mạng vì đầu cạnh vào kín chỗ; xe chờ chèn còn lại cho thấy nút không xả kịp nhu cầu". Ở Mục 5.4: "Một *chiến dịch* là một lần chạy trọn ngân sách của một nguồn sinh đặc tả (B2, P1 hoặc P2) với prompt, dữ liệu và mạng cố định". Ở Mục 5.2.2: "*Khóa* là một tổ hợp chỉ số con × nhánh × loại xe (ví dụ M3, tỷ lệ vượt đỏ, xe máy, LVL)". Chuyển định nghĩa teleport từ 6.11.1 lên Mục 5.3.

### [ND-07] Tóm tắt dùng nhiều thuật ngữ nội bộ, người đọc không biết "đủ điều kiện" là gì
- Mức: nên sửa
- Vị trí: Chapter/0_3_Abstract.tex:15; Chapter/0_4_Abstract_English.tex:15 (PDF tr. 3, 5)
- Trích: "Trên mạng ngày 27/10, phương án đối sánh Optuna đã dùng hết ngân sách 36 lần chạy; trong 12 đặc tả của nó, không đặc tả nào đạt tiêu chí đủ điều kiện, vì mô hình nền quá tải ở mức nhu cầu đại diện … Trên mạng hiện tại, SUMO mặc định đủ điều kiện ở 15/15 lần chạy"
- Vấn đề: Đoạn này dùng liền các cụm "tiêu chí đủ điều kiện", "mạng ngày 27/10", "mô hình nền", "nhu cầu đại diện", "phân tích loại bỏ" mà không giải thích. Người đọc phần tóm tắt cũng không hiểu vì sao "SUMO mặc định đủ điều kiện" lại là một kết quả.
- Vì sao quan trọng: Thành viên hội đồng ngoài ngành thường chỉ đọc kỹ phần tóm tắt.
- Đề xuất sửa: Viết lại phần kết quả bằng ngôn ngữ thường và bỏ chi tiết về phiên bản mạng. Ví dụ: "Một lần chạy được chấp nhận khi không có xe kẹt, không có xe phải chờ vào mạng và va chạm không vượt mức của SUMO mặc định. Trên kịch bản hiện hành, SUMO mặc định đạt tiêu chí này ở cả 15 lần chạy; bộ luật viết tay và cả ba phương án hiệu chỉnh (Optuna, LLM chỉnh tham số, LLM sinh cấu trúc) chưa đạt. Nguyên nhân chính là giá trị gia tốc xe máy lấy từ một mô hình khác…"

### [ND-08] Mã chỉ số M1–M10 thiếu tên ngắn và bị dùng trơ mã trong văn bản
- Mức: nên sửa
- Vị trí: Chapter/4_Rule_execution.tex:82–93 (Bảng 5.1, PDF tr. 42, tr. in 24); Chapter/5_Experiments.tex:437, 518, 1125 (tr. in 41, 43, 69)
- Trích: Bảng 5.1: "M1 | Khoảng thời gian xả hàng sau khi đèn xanh". tr. in 41: "nên điểm M9 trên mạng 29/10 chưa đọc được như sai lệch hành vi". tr. in 43: "M9c và M10b chỉ báo cáo, không chấm điểm". tr. in 69: "Đo M8."
- Vấn đề: Bảng 5.1 chỉ có định nghĩa dài, không có tên ngắn để nhớ. Chương 6 dùng "M8", "M9", "M9c" không kèm nghĩa, người đọc phải lật về tr. in 24. Định nghĩa của M1 ("khoảng thời gian xả hàng") và M7c ("độ dốc tổn thất khởi động của hướng giao cắt theo tổng số xe chờ giữa nút") cũng khó hiểu nếu không có ví dụ.
- Vì sao quan trọng: Bảng chỉ số là trung tâm của phần đánh giá, nhưng người đọc không nhớ nổi mười mã trơ.
- Đề xuất sửa: Thêm cột "Tên ngắn" vào Bảng 5.1, ví dụ M1 (xả hàng), M2 (xuất phát sớm), M3 (vượt đỏ), M4 (vị trí dừng), M5 (mật độ hàng chờ), M6 (thời gian qua nút), M7 (chờ giữa nút), M8 (đi sai làn), M9 (chặn làn rẽ phải), M10 (đi vỉa hè). Thêm cột "Hành vi" ghi số hành vi tương ứng. Trong Chương 6, viết mỗi mã kèm nghĩa, ví dụ "M9 (chặn làn rẽ phải)". Với M1, thêm một câu: "khoảng thời gian giữa hai xe liên tiếp qua vạch dừng sau khi đèn xanh".

### [ND-09] Bit của speed mode và lane change mode chỉ được giải thích ở cuối chương
- Mức: nên sửa
- Vị trí: Chapter/5_Experiments.tex:134–135, 174, 178, 209 (PDF tr. 50–52 và tr. 105, tr. in 32–34 và 87); Bảng 6.35 ở PDF tr. 112 (tr. in 94)
- Trích: Bảng 6.2: "Xóa đúng bit 4 của speed mode, giữ bit 3 (nhường xe xung đột)". "Bit 9–8 của lane change mode bằng 01 và lcPushy bằng 1 cho riêng xe đó"
- Vấn đề: Người chưa dùng SUMO không biết speed mode là gì. Bảng 6.35, nơi giải thích bit, nằm ở trang cuối chương, xa chỗ dùng lần đầu 60 trang.
- Vì sao quan trọng: "Chỉ gỡ đúng ràng buộc cần gỡ" là một đóng góp (Mục 1.5, đóng góp 3). Cách trình bày hiện tại biến đóng góp này thành chi tiết kỹ thuật khó đọc.
- Đề xuất sửa: Ở lần dùng đầu, giải thích một câu bằng lời thường: "SUMO cho mỗi xe một dãy cờ an toàn (speed mode), mỗi cờ bật một kiểm tra: phanh trước đèn đỏ, nhường xe xung đột, giữ khoảng cách… Luật vượt đỏ chỉ tắt cờ 'phanh trước đèn đỏ'." Chuyển Bảng 6.35 lên Mục 6.2. Trong văn xuôi, chỉ ghi số bit trong ngoặc.

### [ND-10] Mã định danh kỹ thuật chen vào văn xuôi; nên có bảng tra cứu mã và ký hiệu
- Mức: nên sửa
- Vị trí: Chapter/5_Experiments.tex:14, 675, 867, 938, 1167 (PDF tr. 46, 68, 77, 80, 89)
- Trích: "dữ liệu đại diện (LITERATURE_PROXY)", "chiến dịch tham chiếu REF_n1104s5", "Thí nghiệm khả thi Phase 3A–3D", "B2_t010: 12,0/h; S 1,374", "1,1680 (it04_s03)"
- Vấn đề: Tên thư mục, mã chiến dịch, mã mẫu và mã prompt (`v004`) xuất hiện như thuật ngữ. Ký hiệu toán ($p_0, k, \Delta t, q, t_w, t_g, \sigma, v_{\text{creep}}, \Delta_{\text{release}}, \delta, D_{\text{empty}}, R, S, S_{\text{sourced}}$) chỉ được định nghĩa rải rác trong Chương 3 và 5.
- Vì sao quan trọng: Người đọc phải nhớ hoặc tìm lại hàng chục mã. Họ không biết `REF_n1104s5` chỉ có nghĩa là "B0 và B1 trên mạng 04/11, 5 seed".
- Đề xuất sửa: Thêm "Bảng tra cứu mã và ký hiệu" ở phần đầu luận văn (sau danh mục viết tắt) hoặc ở đầu Chương 6, gồm: B0, B1, B2, P1, P2, H; E1, E2; F1–F3; G0, M1–M10; PROXY_D1–D5; các phiên bản mạng; v001–v005; các ký hiệu toán. Trong văn xuôi, thay mã thư mục bằng mô tả, ví dụ "chiến dịch tham chiếu (B0 và B1, 5 seed, mạng 04/11)", và để mã gốc trong chú thích hoặc phụ lục. "Phase 3A–3D" nên đổi thành "thí nghiệm khả thi 3A–3D".

### [ND-11] Danh mục viết tắt quá ngắn và không gắn với văn bản
- Mức: nên sửa
- Vị trí: glossary.tex:5–40 (PDF tr. 18, tr. in vi); Chapter/2_Literature_review.tex:54, 64; Chapter/5_Experiments.tex:209, 524
- Trích: Danh mục chỉ có sáu mục: GEH, LLM, OSM, PET, SUMO, TraCI. Văn bản dùng "SL2015", "IDM và chuyển làn MOBIL", "trên nền GAMA", "liên kết TLS của chính nó", "bộ lấy mẫu TPE".
- Vấn đề: Các viết tắt IDM, MOBIL, GAMA, SL2015, TLS, TPE, IQR, SSM, JSON, XSD, TCVN, TCCS, OPRO, vType chưa có trong danh mục. TLS và TPE không được mở rộng ở đâu trong văn bản. Không chương nào gọi `\gls`, nên trường `first=` trong glossary.tex không bao giờ có tác dụng.
- Vì sao quan trọng: Người đọc tra danh mục sẽ không tìm thấy phần lớn viết tắt mình gặp.
- Đề xuất sửa: Bổ sung các mục trên vào glossary.tex, tách thành "Từ viết tắt" và "Thuật ngữ" (bám xe, làn con, vùng chờ giữa nút, teleport, xe chờ chèn, nhu cầu, seed, headway). Mở rộng TLS ("traffic light system, hệ đèn tín hiệu") và TPE ("Tree-structured Parzen Estimator") ở lần dùng đầu.

### [ND-12] Ghi chú nội bộ và câu hỏi cho giảng viên hướng dẫn hiện ra trong PDF
- Mức: nên sửa
- Vị trí: Chapter/4_Rule_execution.tex:103 (PDF tr. 43, tr. in 25); Chapter/3_Rule_generation.tex:57 (PDF tr. 30–31); Chapter/5_Experiments.tex:400, 710 (tr. in 41, 52); Chapter/0_3_Abstract.tex:17 (PDF tr. 4)
- Trích: "[Câu hỏi cho GVHD: nên làm mượt khoảng cách của tỷ lệ nhỏ … hay giữ nguyên và nêu là hạn chế?]", "[TODO_CITE: nguồn hoặc mô tả quan sát cho hành vi 11…]", "[TODO: cập nhật khi có dữ liệu thực]"
- Vấn đề: Các ghi chú này in đậm, không thuộc quy ước `\tamthoi`. Người đọc không phân biệt được đâu là nội dung, đâu là việc tác giả còn dở.
- Vì sao quan trọng: Ghi chú gửi GVHD ngay giữa phần định nghĩa hàm khoảng cách làm định nghĩa đó có vẻ chưa chốt.
- Đề xuất sửa: Tắt các ghi chú này trong bản nộp hội đồng bằng một macro, ví dụ `\newcommand{\todo}[1]{}`. Câu hỏi về tỷ lệ nhỏ nên viết lại thành một câu hạn chế: "Với tỷ lệ rất nhỏ, ép hành vi về 0 vẫn cho khoảng cách thấp hơn; luận văn nêu đây là hạn chế."

### [ND-13] Thiếu một ví dụ chạy xuyên suốt cho một xe
- Mức: nên sửa
- Vị trí: cuối Chương 4 (PDF tr. 40, tr. in 22) hoặc đầu Mục 6.2 (PDF tr. 49, tr. in 31)
- Trích: tr. in 20: "khi một xe được sinh ra, trình mô phỏng rút nguyên mẫu cho xe theo tỷ trọng và nạp tham số tĩnh của nguyên mẫu đó một lần"
- Vấn đề: Các khái niệm nguyên mẫu, phân phối, lớp vi phạm, luật có điều kiện, cửa sổ can thiệp, nhật ký và bảng quan sát được giới thiệu riêng rẽ. Không chỗ nào cho thấy chúng nối với nhau thế nào trên một xe cụ thể.
- Vì sao quan trọng: Người ngoài ngành hiểu từng mảnh nhưng không hình dung được một lần chạy diễn ra ra sao.
- Đề xuất sửa: Thêm một khung "Ví dụ" khoảng nửa trang. Một xe máy vào từ HDT_S được rút nguyên mẫu `moto_violator` (lớp custom1) và đi hướng rẽ trái bị cấm qua bản vá. Đèn đỏ, luật vượt đỏ rút trúng nhưng nút chưa thông, nên xe đợi. Khi đèn xanh, xe vào vùng chờ giữa nút, `illegal_left_box` giữ thêm $\Delta_{\text{release}}$ giây. Nhật ký ghi một dòng, và xe được đếm vào M7a (chờ giữa nút). Có thể kèm sơ đồ dòng thời gian.

### [ND-14] Hình 6.1 dùng mã OSM làm nhãn và không cùng hướng với Hình 6.2
- Mức: nên sửa
- Vị trí: Chapter/5_Experiments.tex:31–32 và 66–70 (PDF tr. 47–48, tr. in 29–30)
- Trích: Nhãn trong Hình 6.1: "953158817#2.up out to NW", "LVL_E 37876499#0 in from NE", "HDT_N 953158817… in from NW". Hình 6.2 ghi "Bắc / Nam / Đông / Tây (Lê Văn Lương)".
- Vấn đề: Hình 6.1 vẽ hai trục đường chéo, hướng ghi theo NE/NW/SE/SW. Hình 6.2 vẽ hai trục vuông góc, hướng ghi theo Đông/Tây/Bắc/Nam. Người đọc không biết "HDT_N (phía bắc)" thực ra là nhánh tây bắc. Các nhãn mã cạnh OSM vô nghĩa với người đọc.
- Vì sao quan trọng: Đây là hai hình duy nhất cho thấy nút giao. Hai hình không khớp nhau thì người đọc không định hướng được khi đọc các mục kết quả theo nhánh.
- Đề xuất sửa: Ở Hình 6.1, bỏ mã cạnh, chỉ giữ LVL_W/LVL_E/HDT_N/HDT_S và mũi tên chỉ hướng bắc. Thêm vào chú thích một câu: "Quy ước: LVL_W là nhánh tây nam, …; Hình 6.2 xoay hình về hai trục vuông góc cho dễ đọc."

### [ND-15] Quy ước đánh số làn chỉ nêu trong một bảng và bị dùng lẫn
- Mức: nên sửa
- Vị trí: Chapter/5_Experiments.tex:23, 91, 108, 817, 850 (PDF tr. 46, 104, 48, 75–76)
- Trích: tr. in 28: "trên lane 0 trong 30 m cuối". Bảng 6.1 ở tr. in 86: "Làn ngoài cùng bên phải (lane 0)". Mục 6.11.4: "vạch dừng làn 2 (làn chung cho đi thẳng, rẽ trái và rẽ phải)". Hình 6.6: "ở làn 1 và làn 2"
- Vấn đề: Lane 0 được dùng từ tr. in 28, nhưng quy ước "lane 0 là làn ngoài cùng bên phải" chỉ có ở Bảng 6.1, mà bảng này lại trôi về tr. in 86. Văn bản dùng lẫn "lane 2" và "làn 2". Ở Mục 6.11.4, "làn 2" là làn chung cho mọi hướng trên mạng cũ, trái với quy ước hiện hành (lane 2 cho đi thẳng, quay đầu, rẽ trái).
- Vì sao quan trọng: Hành vi 5 và 6 cùng các chỉ số M8 (đi sai làn), M9 (chặn làn rẽ phải) đều định nghĩa theo số làn.
- Đề xuất sửa: Nêu quy ước một lần ở Mục 6.1.3, kèm làn 0/1/2 vẽ trên Hình 6.2. Dùng thống nhất một dạng ("làn 0"). Ở các mục về mạng cũ, ghi rõ "trên mạng trước F2, làn 2 là làn chung…".

### [ND-16] Bảng 6.3 chỉ có tên thuộc tính tiếng Anh, không nối với khái niệm ở Chương 3
- Mức: nên sửa
- Vị trí: Chapter/5_Experiments.tex:150–163 (Bảng 6.3, PDF tr. 105, tr. in 87); Chapter/3_Rule_generation.tex:100 (PDF tr. 32, tr. in 14)
- Trích: Mục 3.3.1: "bám xe (thời gian phản ứng, khoảng cách tối thiểu, gia tốc, giảm tốc, mức dao động tốc độ)". Bảng 6.3: "tau, minGap, accel, decel, sigma, speedFactor, speedDev"
- Vấn đề: Người đọc phải tự đoán `tau` là thời gian phản ứng, `sigma` là mức dao động. `lcAssertive`, `jmTimegapMinor`, `jmDriveAfterRedTime` thì không đoán được.
- Vì sao quan trọng: Kết quả 6.11.19 và các bảng phụ lục nói về `tau`, `accel`, `minGapLat`, nhưng người đọc không biết các tham số đó điều khiển gì.
- Đề xuất sửa: Thêm cột "Ý nghĩa" vào Bảng 6.3 (mỗi thuộc tính 3–6 từ), hoặc tham chiếu rõ tới Bảng A.1–A.2 nếu phụ lục đã có cột này.

### [ND-17] Tên luật tiếng Anh xuất hiện lần đầu trong bảng, không gắn với tên tiếng Việt
- Mức: nhỏ
- Vị trí: Chapter/3_Rule_generation.tex:104–135 (tiêu đề Mục 3.3.2–3.3.6) và 149–154 (Bảng 3.2) (PDF tr. 32–35, tr. in 14–17)
- Trích: Tiêu đề "3.3.2 Vượt đèn đỏ có hiệu ứng bầy đàn"; bảng 3.2: "swarm_red_running | 1, 2"
- Vấn đề: Văn bản Mục 3.3 không gọi tên mã của luật. Tên mã chỉ có trong Bảng 3.2, sau đó được dùng trơ suốt Chương 6.
- Vì sao quan trọng: Đến Chương 6, người đọc phải nhớ `queue_space_seeking` là luật nào.
- Đề xuất sửa: Ghi mã ngay ở câu đầu mỗi mục, ví dụ "Luật vượt đèn đỏ theo đoàn (`swarm_red_running`) dùng chung cho hành vi 1 và 2." Ở Chương 6, lần đầu mỗi mục nhắc lại tên tiếng Việt.

### [ND-18] Thuật ngữ không thống nhất cho cùng một khái niệm
- Mức: nhỏ
- Vị trí: Chapter/1_Introduction.tex:96 (PDF tr. 22); Chapter/3_Rule_generation.tex:32, 213; Chapter/4_Rule_execution.tex:112; Chapter/5_Experiments.tex:699, 829
- Trích: "các ngày dữ liệu dành riêng" (tr. in 4) / "ngày đánh giá" / "các ngày dành riêng" (tr. in 26); "xe chờ được đưa vào mạng" (tr. in 25) / "xe chưa chèn" / "xe chờ chèn"; "bộ luật thủ công" / "bộ luật viết tay" / "B1"
- Vấn đề: Mỗi khái niệm có hai, ba tên. Người đọc dễ tưởng đó là các khái niệm khác nhau.
- Vì sao quan trọng: Lỗi này cộng dồn với ND-06 và ND-10.
- Đề xuất sửa: Chốt một tên cho mỗi khái niệm: "ngày đánh giá", "xe chờ chèn", "bộ luật viết tay B1". Thay toàn bộ các tên khác, và ghi tên đã chốt vào bảng tra cứu đề xuất ở ND-10.

### [ND-19] Từ tiếng Anh chen vào: chỗ nên dịch, chỗ nên chú thích lần đầu
- Mức: nhỏ
- Vị trí: Chapter/1_Introduction.tex:22 ("seed"); Chapter/2_Literature_review.tex:73 ("define-by-run"); Chapter/5_Experiments.tex:174 ("cut-back"), 328 ("pipeline"), 332 ("runner"), 468 ("thinking", "reasoning_effort"), 524 ("stick-breaking")
- Trích: "tái lập được với cùng seed"; "tỷ trọng các nguyên mẫu lấy trên đơn hình bằng cách bẻ que (stick-breaking)"; "Chế độ suy nghĩ (thinking)"
- Vấn đề: "seed" dùng hàng trăm lần mà không được giải thích lần nào. "define-by-run" và "stick-breaking" không có giải thích, mà cũng không cần cho người đọc. "pipeline", "runner" đã có từ tiếng Việt tương đương nhưng vẫn để song song.
- Vì sao quan trọng: Đây là chỗ vấp nhỏ nhưng lặp lại liên tục.
- Đề xuất sửa: Giữ "seed" nhưng chú thích ở Mục 1.2: "seed (hạt giống của bộ sinh số ngẫu nhiên; cùng seed cho cùng kết quả)". Bỏ "define-by-run". Thay "bẻ que (stick-breaking)" bằng "một phép biến đổi bảo đảm các tỷ trọng cộng lại bằng 1". Dùng thống nhất "đường ống" và "trình chạy", chỉ ghi tiếng Anh trong ngoặc ở lần đầu.
