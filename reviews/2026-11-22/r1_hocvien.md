# Học viên cùng khóa

> **Ghi chú về vị trí.** PDF được build từ bộ nguồn 7 chương (`5_Evaluation`, `6_Implementation`, `7_Conclusions`). Trên đĩa, `Latex_SOICT/Chapter/` hiện là một bản khác gồm 6 chương: phần đánh giá (Ch5 trong PDF) nằm ở `4_Rule_execution.tex:61–114` cộng `5_Experiments.tex:470–508`; Ch6 trong PDF ứng với `5_Experiments.tex`; Ch7 ứng với `6_Conclusions.tex`. Số dòng dưới đây lấy từ các file đang có trên đĩa. Số trang lấy theo PDF đã build: "PDF tr." là trang trong file PDF, "in" là số trang in ở chân trang (phần thân: PDF = in + 18). Hai bản lệch nhau ở vài chỗ, ví dụ 3.5.1 trên đĩa đã có OPRO/FunSearch/Eureka còn PDF thì chưa. Chỗ nào lệch mình ghi rõ.

## Đánh giá tổng quát

Phần ý tưởng (Ch3–Ch5, PDF tr. 29–45) viết gọn, logic, đọc một lèo không phải lật lại. Từ Ch6 trở đi thì khác: 67 trang, 6.11 có 20 mục con xếp theo ngày, sáu phiên bản mạng. Mình mất mạch ở khoảng PDF tr. 70–80 (in 52–62) và phải lật về Bảng 6.17 bốn năm lần để biết đang ở mạng nào. Vấn đề lớn nhất khi lên bảng: luận văn chưa có câu nào nói "kết quả chính là X", trong khi tóm tắt lại mở đầu bằng một loạt kết quả âm ("không đặc tả nào đủ điều kiện", "SUMO mặc định 15/15, bộ luật thủ công thì chưa"). Có một kết quả dương đáng đưa lên đầu, là Bảng 6.16 cùng Hình 6.3, nhưng nó đang bị đẩy xuống PDF tr. 111. Ngoài ra bìa đang in sai tên đề tài.

## Nhận xét

### [HV-01] Bìa in sai tên đề tài
- Mức: nghiêm trọng
- Vị trí: `Cover.tex:13`, `Cover2.tex:13` (PDF tr. 1–2)
- Trích: "Mô hình thế giới vĩ mô trong trò chơi máy tính"
- Vấn đề: Tên này còn sót lại từ template hoặc từ đề tài cũ, không liên quan gì tới SUMO hay nút giao. Đây là trang đầu tiên hội đồng nhìn thấy.
- Câu hội đồng có thể hỏi: "Tên đề tài đăng ký của em là gì?"
- Đề xuất sửa: Thay bằng tên đề tài đã đăng ký và kiểm tra lại cho khớp từng chữ với quyết định giao đề tài. Sửa ở cả hai file bìa, và cập nhật `\TITLE` trong `main.tex:73` (đang là "LUẬN VĂN THẠC SĨ", nên metadata PDF cũng sai tiêu đề).

### [HV-02] Tóm tắt và kết luận không có "kết quả chính", lại mở đầu bằng kết quả âm
- Mức: nghiêm trọng
- Vị trí: `0_3_Abstract.tex:15` (PDF tr. 3); `6_Conclusions.tex:35–45` (PDF tr. 114–115)
- Trích: "Trên mạng hiện tại, SUMO mặc định đủ điều kiện ở 15/15 lần chạy, còn bộ luật thủ công thì chưa. Optuna và hai chiến dịch LLM ... đều dùng hết ngân sách 36 lần chạy nhưng chưa có đặc tả nào đủ điều kiện"; Ch7: "[TODO: câu kết luận chính về khả năng của LLM cục bộ ...]"
- Vấn đề: Người đọc tóm tắt sẽ hiểu là phương pháp làm mô phỏng tệ hơn SUMO mặc định. Thực ra "đủ điều kiện" chỉ là bộ lọc ổn định (không kẹt, không va chạm quá ngưỡng), không đo độ giống. Theo Bảng 6.16, B0 có 0% xe máy vượt đèn đỏ, còn B1 qua bộ thực thi có 4,86% và 1,56 lượt mỗi chu kỳ mỗi nhánh, gần dữ liệu đại diện hơn hẳn. Đó là kết quả dương duy nhất đo được, nhưng tóm tắt không nhắc tới. Đoạn "Kết quả hiện có" còn kể theo ngày ("Trên mạng ngày 27/10...", "Sau khảo sát hiện trường, kịch bản đổi sang..."), đọc như báo cáo tiến độ.
- Câu hội đồng có thể hỏi: "SUMO mặc định đạt 15/15, bộ luật của em đạt 0/15. Vậy phương pháp của em có tác dụng gì?"
- Đề xuất sửa: Viết lại "Kết quả" theo thứ tự: (1) bộ thực thi tái hiện được hành vi mà B0 không có, kèm số của Bảng 6.16; (2) LLM 9B sinh đặc tả hợp lệ ở 12/16 mẫu P1 và 14/20 mẫu P2, lỗi chủ yếu là lỗi cấu trúc và bị bộ kiểm tra bắt hết trước khi chạy; (3) chưa có đặc tả nào qua tiêu chí ổn định, phân tích loại bỏ chỉ ra nguyên nhân là `accel` của B1. Bỏ các mốc ngày và chuyện đổi mạng khỏi tóm tắt. Ch7 cũng cần một câu kết luận viết được ngay bây giờ, không đợi E1/E2.

### [HV-03] Chương 6 là nhật ký thí nghiệm theo thời gian
- Mức: nghiêm trọng
- Vị trí: `5_Experiments.tex:12` ("trình bày các thực nghiệm theo thứ tự thời gian"); 6.11 ở `5_Experiments.tex:712–1238` (PDF tr. 70–92); Bảng 6.17 ở `5_Experiments.tex:720–734` (PDF tr. 70)
- Trích: tiêu đề mục "Cập nhật kịch bản và kết quả trên hai mạng ngày 28/10", "Thay đổi ngày 04/11 và kết quả tham chiếu trên mạng 04/11", "Ngưỡng này *đã bị hủy* khi..." (`5_Experiments.tex:856`)
- Vấn đề: Có sáu phiên bản mạng, phần lớn số liệu thuộc các mạng đã bỏ (F2, 28/10 đợt 1/2, 29/10), và chính tác giả viết "Số liệu giữa các mạng không so sánh trực tiếp được" (`5_Experiments.tex:718`). File thí nghiệm có 94 dòng chứa mốc ngày. Người đọc phải tự lọc ra cái gì còn hiệu lực. Mình định bỏ qua cả đoạn 6.11.7–6.11.13 vì không biết nó còn liên quan tới kết quả cuối không.
- Câu hội đồng có thể hỏi: "Kết quả nào trong chương này là kết quả cuối? Các mạng cũ còn ý nghĩa gì?"
- Đề xuất sửa: Xếp lại 6.11 theo câu hỏi, không theo ngày: (a) thí nghiệm khả thi cơ chế (vùng chờ giữa nút, 3A–3D, speed mode); (b) B0 so với B1 trên mạng cuối (Bảng 6.16, 6.29); (c) ba chiến dịch trên mạng cuối (Bảng 6.31, 6.32); (d) phân tích loại bỏ (Bảng 6.33). Phần lịch sử mạng F2 → 28/10 → 29/10 thì gom thành một mục ngắn "Quá trình hiệu chỉnh kịch bản" kèm Bảng 6.17, hoặc chuyển xuống phụ lục. Gọi tên mạng bằng phiên bản (v1…v6, "mạng cuối") thay vì ngày.

### [HV-04] Không có câu hỏi nghiên cứu, E1/E2 chỉ xuất hiện ở Ch5
- Mức: nghiêm trọng
- Vị trí: `1_Introduction.tex:78` (mục tiêu i–v, PDF tr. 21–22); E1/E2 lần đầu ở 5.5.1 (PDF tr. 44, `5_Experiments.tex:470–504`)
- Trích: "Luận văn có năm mục tiêu cụ thể: (i) xác định các hành vi ... (v) so sánh luật do LLM sinh với mô hình mặc định..."
- Vấn đề: Mục tiêu (i)–(iv) là "xây dựng X", tức là sản phẩm, không phải câu hỏi. Chỉ mục (v) là câu hỏi, và chưa có kết quả. Hội đồng CNTT thường hỏi "câu hỏi nghiên cứu của em là gì, trả lời đến đâu". Hiện luận văn không có RQ nào trả lời được.
- Câu hội đồng có thể hỏi: "Liệt kê câu hỏi nghiên cứu và cho biết câu nào đã có câu trả lời."
- Đề xuất sửa: Thêm 3 RQ vào 1.4. RQ1: bộ thực thi có tái hiện được các hành vi vi phạm mà mô hình chuẩn không có, mà không làm mô phỏng kém an toàn hơn? Câu này trả lời được ngay bằng Bảng 6.16, Hình 6.3 và tiêu chí va chạm. RQ2: LLM cục bộ có sinh được đặc tả hợp lệ, và lỗi của nó thuộc loại gì? Trả lời được bằng Bảng 6.31 và 6.32. RQ3 (E1/E2): LLM so với Optuna trên cùng ngân sách; câu này còn để dự kiến. Ch7 trả lời lần lượt từng RQ.

### [HV-05] Đóng góp học thuật bị trộn với chuyện gỡ lỗi và công cụ có sẵn
- Mức: nghiêm trọng
- Vị trí: `1_Introduction.tex:89–96` (PDF tr. 22); 6.12 ở `5_Experiments.tex:1240–1420` (PDF tr. 92–102); Bảng 6.34 (PDF tr. 112)
- Trích: "Mục 6.12 trình bày bảy giải pháp kỹ thuật khi hiện thực các đóng góp này"; giải pháp 5 "Chẩn đoán va chạm do bề rộng làn ra khi dựng mạng"; giải pháp 3 "Dùng điểm chờ nội bộ sẵn có của SUMO"
- Vấn đề: 4 đóng góp ở 1.5 cộng với 7 "giải pháp kỹ thuật" ở 6.12 thành 11 thứ, và người đọc không phân biệt được đâu là ý tưởng của tác giả. Giải pháp 5 thực chất là sửa một giá trị mặc định của `netconvert`. Giải pháp 3 kết luận "dùng cơ chế sẵn có" (PDF tr. 72, in 54). Đặt hai mục này ngang hàng với "đặc tả có kiểm soát" hay "chỉ giữ, không đẩy" làm các đóng góp thật bị loãng đi. Có một chỗ làm rất tốt là Bảng 6.2 (ánh xạ khái niệm → SUMO), nhưng nó đang trôi tới PDF tr. 105.
- Câu hội đồng có thể hỏi: "Trong 7 giải pháp, cái nào là của em, cái nào SUMO đã có sẵn? Sửa bề rộng làn có phải đóng góp không?"
- Đề xuất sửa: Giữ 4 đóng góp ở 1.5. Viết lại 6.12 thành "hiện thực các đóng góp", mỗi đóng góp một mục, và ghi rõ phần nào dùng nguyên SUMO/TraCI/Optuna, phần nào tác giả thêm vào. Chuyển giải pháp 5 sang mục "bài học dựng mạng" hoặc vào phần hạn chế. Đưa Bảng 6.2 về đúng chỗ nó được nhắc (xem HV-09).

### [HV-06] Phát biểu bài toán chỉ có văn xuôi, không có ký hiệu
- Mức: nên sửa
- Vị trí: `1_Introduction.tex:22` (PDF tr. 20); các mảnh rời ở `4_Rule_execution.tex:101–114` (PDF tr. 42–43)
- Trích: "cần xây dựng một bộ luật hành vi ... sao cho trình mô phỏng chạy với bộ luật đó tái hiện các hành vi quan sát được ... giống nhất có thể"
- Vấn đề: Các thành phần đều đã có (đặc tả = cấu trúc + tham số, điểm S, tiêu chí đủ điều kiện, ngân sách 36 lần chạy), nhưng nằm rải rác ở ba chương. Chỉ có đúng một công thức là (3.1). Hội đồng CNTT sẽ chờ một dòng kiểu "min S(θ) s.t. ...".
- Câu hội đồng có thể hỏi: "Hàm mục tiêu và ràng buộc của bài toán là gì? Biến quyết định là gì?"
- Đề xuất sửa: Thêm 5–8 dòng vào 1.2 hoặc đầu Ch3: đặc tả θ = (σ, φ), trong đó σ là cấu trúc (tập nguyên mẫu, tập luật) và φ ∈ Φ(σ) là tham số; bài toán là min S(θ; D_cal) với ràng buộc eligible(θ) và số lần chạy ≤ N. P1/B2 cố định σ, P2 tìm cả σ. Như vậy sự khác nhau giữa P1, P2, B2, H hiện ra ngay từ ký hiệu.

### [HV-07] Nói "11 hành vi" nhưng số hành vi thực sự xuất hiện trong mô phỏng ít hơn nhiều
- Mức: nên sửa
- Vị trí: `0_3_Abstract.tex:11`, `1_Introduction.tex:92`, `6_Conclusions.tex:15`; Bảng 6.16 ở `5_Experiments.tex:685–693` (PDF tr. 111); `5_Experiments.tex:699`
- Trích: "Danh mục gồm 11 hành vi"; "B1 đặt xác suất bằng 0 cho `early_start` và cho mọi lựa chọn của `queue_space_seeking`"
- Vấn đề: Hành vi 8 (đi ngược chiều) bị hoãn. Theo Bảng 6.16, M10a (số xe máy trên vỉa hè) bằng 0 ở cả B0 và B1, xuất phát sớm dưới 1%, dừng quá vạch 0,04%. Lựa chọn `right_lane` không còn trên mạng cuối. Các đặc tả P2 bỏ `queue_space_seeking`, `uturn_bypass`, `slow_lane_center`. Nghĩa là trên mạng cuối, bộ luật thật sự kích hoạt chủ yếu là vượt đỏ và lách xe quay đầu. Khi đọc, mình chỉ nhận ra điều này ở PDF tr. 69, còn tóm tắt thì ghi "Mười trong 11 hành vi đã được đưa vào mô hình".
- Câu hội đồng có thể hỏi: "Trong 11 hành vi, bao nhiêu hành vi xuất hiện trong lần chạy cuối, và ở mức nào?"
- Đề xuất sửa: Thêm một bảng phủ hành vi gồm các cột: hành vi | cơ chế (tham số tĩnh / luật / bản vá) | đã cài? | có sự kiện trong B1 trên mạng cuối? | chỉ số đo. Ở tóm tắt, dùng cách nói chính xác: "danh mục 11 hành vi; 10 hành vi có cơ chế trong mô hình; trên bộ luật thủ công B1, X hành vi được kích hoạt".

### [HV-08] Ghi chú nội bộ và từ ngữ của dự án lọt vào bản in
- Mức: nên sửa
- Vị trí:
  - `4_Rule_execution.tex:103` (PDF tr. 43): "**[Câu hỏi cho GVHD: nên làm mượt khoảng cách của tỷ lệ nhỏ ...]**"
  - `3_Rule_generation.tex:57` (PDF tr. 30–31): "**[TODO_CITE: nguồn hoặc mô tả quan sát cho hành vi 11 ...]**"
  - `5_Experiments.tex:867, 877` (PDF tr. 77–78): tiêu đề "Thí nghiệm khả thi Phase 3A--3D", gắn với cách đặt tên phase trong kế hoạch nội bộ
  - `Appendix_B.tex:22, 36` (PDF tr. 127–128): "(bổ sung so với kế hoạch)", "khác kế hoạch ban đầu ở hai điểm"
  - `5_Experiments.tex:1156` (PDF tr. 89): "Giờ Hà Nội ngày 08/11/2026"
  - `5_Experiments.tex:665` (PDF tr. 67–68): "Ngày 31/10 có 9 ca không đạt; nay chúng đều đạt"
- Vấn đề: `\tamthoi` là chủ ý, mình không bàn. Nhưng mấy chỗ trên không phải giá trị tạm thời. Đó là ghi chú làm việc với thầy, và nhắc tới một "kế hoạch" mà hội đồng chưa từng đọc. Câu hỏi cho GVHD in đậm ngay trong mục định nghĩa hàm khoảng cách sẽ khiến hội đồng nghĩ phương pháp chưa chốt.
- Câu hội đồng có thể hỏi: "Câu hỏi cho GVHD này đã có trả lời chưa? Hàm khoảng cách cuối cùng là gì?"
- Đề xuất sửa: Chốt cách xử lý tỷ lệ nhỏ. Nếu giữ nguyên thì viết thành một câu hạn chế. Gỡ TODO_CITE bằng cách mô tả quan sát (thời điểm, địa điểm, cách ghi) nếu không có nguồn. Đổi "Phase 3A–3D" thành "Thí nghiệm khả thi cho nhóm tìm khoảng trống (3 thí nghiệm + 1 kiểm tra)". Bỏ cụm "so với kế hoạch". Bỏ giờ chạy và ngày ra khỏi caption và kết quả kiểm thử.

### [HV-09] Bảng trôi dồn về cuối chương, danh mục bảng lộn thứ tự, trang gần trắng
- Mức: nên sửa
- Vị trí: Bảng 6.1–6.7, 6.10, 6.11, 6.16, 6.34, 6.35 nằm ở PDF tr. 104–112 (in 86–94), sau cả mục 6.13. Trong nguồn, các bảng này dùng `[ht]` (`5_Experiments.tex:80, 121, 146, 180, 218, 245, 284, 405, 446, 677, 1247, 1298`), xen giữa nhiều bảng `[H]`. Danh mục bảng ở PDF tr. 16–17. Trang gần trắng: PDF tr. 64 (6.8.2), tr. 66 (quanh Bảng 6.14).
- Trích: PDF tr. 47 (in 29): "Hình 6.2 minh họa vị trí của chúng, Bảng 6.1 liệt kê chi tiết", nhưng Bảng 6.1 nằm ở PDF tr. 104.
- Vấn đề: Bảng 6.16 là kết quả quan trọng nhất (HV-02), được bàn ở PDF tr. 68–70 nhưng in ở tr. 111. Danh mục bảng in 6.8, 6.9, 6.12… trước 6.1, nhìn như lỗi đánh số. Đọc lần đầu mình tưởng thiếu bảng.
- Đề xuất sửa: Nguyên nhân là trộn `[ht]` với `[H]`. Đổi các bảng `[ht]` của Ch6 sang `[!htbp]` và đặt ngay sau đoạn nhắc tới, hoặc dùng `[H]` cho thống nhất. Có thể thêm `\FloatBarrier` (gói `placeins`) ở đầu mỗi `\section`. Bảng 6.6, 6.7, 6.13, 6.14 có thể chuyển xuống phụ lục (xem HV-15).

### [HV-10] Mã ký hiệu chồng chéo, không có bảng tra
- Mức: nên sửa
- Vị trí: `5_Experiments.tex:23` (PDF tr. 46): "F2 (tìm khoảng trống khi ùn) gồm hành vi 4--8"; `5_Experiments.tex:728`: "F2 (27/10)" là tên một phiên bản mạng; `glossary.tex:5–40` (PDF tr. 18) chỉ có 6 mục
- Trích: "Ngưỡng va chạm đóng băng trên mạng F2" và "Ba bảng nhóm F2 dùng luồng số ngẫu nhiên riêng" (Bảng 6.9)
- Vấn đề: "F2" vừa là nhóm hành vi vừa là tên mạng. Ngoài ra còn B0, B1, B2, P1, P2, H, E1, E2, G0, M1–M10, PROXY_D1–D5, REF_n1104s5, `it03_s02`... Danh mục viết tắt không có mã nào trong số này, cũng không có vType, TLS, SSM, IDM, TPE, IQR.
- Đề xuất sửa: Đổi tên mạng (ví dụ N1…N6, hoặc "mạng v2"). Thêm vào danh mục từ viết tắt một bảng "Ký hiệu phương án và chỉ số", trong đó mỗi chỉ số đi kèm nghĩa, ví dụ "M8 (đi sai làn)", "M9 (chặn làn rẽ phải)", "M10 (đi trên vỉa hè)". Bỏ mã chiến dịch nội bộ (`REF_n1104s5`) khỏi thân bài.

### [HV-11] Thiếu phần phân tích hạn chế, Ch7 đọc như danh sách việc cần làm
- Mức: nên sửa
- Vị trí: `6_Conclusions.tex:43–53` (7.1.5 "Chưa thực hiện", 7.2.1 "Việc trước mắt", PDF tr. 115); câu "chỉ cho biết quy trình vận hành được / chưa cho biết mô phỏng giống..." lặp lại 6 lần (`0_3_Abstract.tex:17`, `1_Introduction.tex:84`, `5_Experiments.tex:437, 1366`, ...)
- Trích: "Việc đầu tiên là quyết định giữ `accel` xe máy của Saval trong B1 hay sửa B1..."
- Vấn đề: 7.2.1 là kế hoạch tuần tới, không phải hướng phát triển. Luận văn không có mục nào phân tích các đe dọa tới hiệu lực: dữ liệu đại diện (PDF tr. 98: "Không có mục tiêu nào mang nhãn `literature`"), một nút giao, mỗi ngày chỉ một seed trong chiến dịch, chỉ một LLM 9B với nhiệt độ 0,7, mạng thay đổi giữa các chiến dịch. Câu rào đón lặp lại nhiều lần nghe phòng thủ, nhưng lại không thay được cho một phân tích có cấu trúc.
- Câu hội đồng có thể hỏi: "Hạn chế lớn nhất của luận văn là gì, và nó ảnh hưởng tới kết luận nào?"
- Đề xuất sửa: Thêm mục 7.x "Hạn chế", chia theo hiệu lực nội (seed, mạng đổi, ngưỡng suy từ B0), hiệu lực ngoài (một nút, dữ liệu chuyển giao) và hiệu lực cấu trúc (khoảng cách tỷ lệ nhỏ, M9 chưa định nghĩa lại). Câu rào đón chỉ cần nói một lần thật rõ ở 1.4.2 và nhắc lại ở mục Hạn chế. Gộp 7.2.1 vào 7.1.5 hoặc bỏ.

### [HV-12] Ngưỡng đủ điều kiện suy từ B0 trên mạng cũ rồi áp lên mạng cuối, người đọc không theo được
- Mức: nên sửa
- Vị trí: `5_Experiments.tex:532` (6.7.3, PDF tr. 62)
- Trích: "Hai ngưỡng va chạm là 4 va chạm trên làn/h và 142 va chạm trong nút/h, suy từ B0 trên mạng F2 ...; chúng chưa được tính lại trên mạng 29/10... Mức của B0 khai báo theo từng chiến dịch: 1,333 ..., 2,667 và 1,333 ..., 1,867"
- Vấn đề: Một đoạn có năm con số ngưỡng thuộc bốn mạng. Người đọc khó biết trên mạng cuối thì ngưỡng nào áp dụng. Ngưỡng lấy từ chính B0 nên câu "B0 đủ điều kiện 15/15" dễ bị hiểu là hiển nhiên. Ngưỡng 142 va chạm trong nút/h "gần như không loại lần chạy nào" (PDF tr. 80), vậy nó dùng để làm gì?
- Câu hội đồng có thể hỏi: "Ngưỡng lấy từ B0 thì B0 qua là đương nhiên phải không? Sao không tính lại trên mạng cuối?"
- Đề xuất sửa: Làm một bảng nhỏ "Cấu hình đánh giá trên mạng cuối" gồm ngưỡng, ngân sách, seed, cửa sổ, chỉ một dòng mỗi mục. Lịch sử ngưỡng chuyển sang phụ lục. Thêm một câu giải thích vì sao lấy B0 làm mốc ("không kém an toàn hơn mô hình chuẩn") và vì sao B0 vẫn có thể trượt (đã trượt trên mạng 29/10).

### [HV-13] Việc chưa quyết định về `accel` của B1 bị nhắc ở bốn chỗ
- Mức: nên sửa
- Vị trí: `5_Experiments.tex:1230` (PDF tr. 92); `Appendix_A.tex:100` (PDF tr. 125); `6_Conclusions.tex:45, 51` (PDF tr. 115)
- Trích: "Việc giữ giá trị của Saval trong B1 hay sửa B1 ... chưa được quyết định."
- Vấn đề: B1 là cấu trúc nền của cả P1 lẫn B2. Luận văn tự chỉ ra rằng chừng nào B1 còn lỗi thì không đặc tả nào dựa trên B1 đủ điều kiện được. Nhắc bốn lần "chưa quyết định" để lộ sự lưỡng lự, và mời hội đồng hỏi vì sao biết nguyên nhân rồi mà không sửa.
- Câu hội đồng có thể hỏi: "Em đã biết nguyên nhân, sao không sửa B1 rồi chạy lại?"
- Đề xuất sửa: Nếu kịp thì quyết định và chạy lại. Nếu không kịp thì trình bày việc này như một phát hiện: "chuyển tham số IDM sang Krauss làm hỏng năng lực thông qua; đây là rủi ro của việc chuyển giao tham số giữa các mô hình bám xe". Nêu một lần ở 6.11 và một lần ở mục Hạn chế. Bỏ cụm "chưa được quyết định".

### [HV-14] Chương 2 mỏng, chưa so sánh với các công trình gần nhất theo từng tiêu chí
- Mức: nên sửa
- Vị trí: `2_Literature_review.tex:68–102` (PDF tr. 26–28); Bảng 2.2 (PDF tr. 28, nằm một mình giữa trang trắng)
- Trích: "Cả ba đều hướng tới cấu hình kịch bản và nhu cầu."
- Vấn đề: Chương 2 dài 5 trang với 23 tài liệu. Ba công trình LLM+SUMO chỉ được mô tả mỗi công trình một câu, không có bảng đặt cạnh nhau theo các tiêu chí (LLM sinh gì, có kiểm tra hợp lệ không, có so với bộ tối ưu không, dữ liệu gì). Trong PDF hoàn toàn không có mảng "LLM làm bộ tối ưu". Bản `.tex` trên đĩa đã thêm OPRO, FunSearch, Eureka vào `3_Rule_generation.tex:192`, nhưng chỉ như lý do để dùng LLM, còn Ch2 vẫn chưa có. Eureka (LLM viết hàm thưởng, chấm bằng mô phỏng, sửa theo phản hồi) gần với khung của luận văn hơn cả AgentSUMO.
- Câu hội đồng có thể hỏi: "Khác gì Eureka hay OPRO? Đóng góp còn lại sau khi trừ đi các công trình đó là gì?"
- Đề xuất sửa: Chuyển đoạn OPRO/FunSearch/Eureka sang 2.3.2 như một tiểu mục "LLM làm bộ tối ưu/bộ sinh có bộ đánh giá". Thay Bảng 2.2 bằng một bảng so sánh: hàng là các công trình (Saval, AgentSUMO, ChatSUMO, SUMO-MCP, OPRO, Eureka, luận văn), cột là các tiêu chí ở trên. Việc này làm được trong một buổi.

### [HV-15] Nhiều nội dung kỹ thuật nội bộ nên chuyển xuống phụ lục
- Mức: nên sửa
- Vị trí: 6.3 Yêu cầu hệ thống, 6.4 Kiến trúc (`5_Experiments.tex:237–392`, PDF tr. 52–59); 6.8.1–6.8.3 (`5_Experiments.tex:537–632`, PDF tr. 62–66); 6.13 (`5_Experiments.tex:1422+`, PDF tr. 102–103)
- Trích: "`optuna` nạp mô-đun `sqlite3` của Python, và tệp `sqlite3.dll` đi kèm Python xung đột với tệp cùng tên đi kèm `libsumo`" (`5_Experiments.tex:572`); Bảng 6.12 liệt kê phiên bản `pyyaml`, `lxml`; Bảng 6.14 đếm số dòng mã
- Vấn đề: Mấy đoạn này đọc như README của repo. Mình đã muốn bỏ qua cả khối PDF tr. 52–66. Chúng còn đẩy kết quả (6.10, 6.11) ra xa phần phương pháp.
- Đề xuất sửa: Giữ trong thân bài: ánh xạ khái niệm sang SUMO (Bảng 6.2), luồng dữ liệu (Bảng 6.8), kiểm thử (gọn lại còn nửa trang). Chuyển xuống phụ lục C "Hiện thực và tái lập": 6.3, Bảng 6.9, 6.12, 6.13, 6.14, chuyện sqlite3/JournalFileOpenLock, đường dẫn thư mục ở 6.13.

### [HV-16] Cùng một câu chuyện được kể ba bốn lần
- Mức: nên sửa
- Vị trí: Bề rộng làn ra được kể ở 6.11.3 (`5_Experiments.tex:805`), 6.12.5 (`:1368`) và 7.1.3 (`6_Conclusions.tex:27`). Speed mode bit 4 ở 4.3, 6.2.2, 6.12.2 (`:1287`) và Bảng 6.2. Vùng chờ giữa nút ở 3.3.5, 6.11.2 (`:740`) và 6.12.3 (`:1323`).
- Trích: 6.12.3 c: "Vùng chờ 3,2 m (mạng ban đầu): tối đa 8 xe..." lặp lại nguyên số liệu của Bảng 6.18
- Vấn đề: Người đọc gặp lại số liệu cũ và không biết mục mới có gì mới. Chương 6 cũng vì thế mà dài thêm khoảng 10 trang.
- Đề xuất sửa: Nếu giữ 6.12 thì mỗi giải pháp chỉ gồm vấn đề, ý tưởng và trỏ tới kết quả ở 6.11, không chép lại số. Cách khác là bỏ hẳn 6.12 và đưa Bảng 6.34 vào 1.5 làm bảng tóm tắt đóng góp.

### [HV-17] Ch5 nói lược đồ có mười bảng, Phụ lục B chỉ liệt kê bảy
- Mức: nên sửa
- Vị trí: `4_Rule_execution.tex:64` (PDF tr. 41, 5.1); `Appendix_B.tex:10–26` (Bảng B.1, PDF tr. 127)
- Trích: "gồm mười bảng: ... và ba bảng cho nhóm tìm khoảng trống (chuỗi thời gian hàng chờ, sự kiện tìm khoảng trống, độ trễ của xe rẽ phải). Định nghĩa đầy đủ nằm ở Phụ lục B.1."
- Vấn đề: Bảng B.1 không có ba bảng mà M9 (chặn làn rẽ phải) và M10 (đi trên vỉa hè) cần dùng. Hội đồng mà lật phụ lục để kiểm tra sẽ thấy ngay chỗ hở.
- Đề xuất sửa: Bổ sung ba dòng vào Bảng B.1, hoặc sửa lại câu ở 5.1 cho khớp.

### [HV-18] Chưa giải thích vì sao chọn LLM cục bộ cỡ 9B
- Mức: nên sửa
- Vị trí: `1_Introduction.tex:31` (PDF tr. 20); 6.6 (PDF tr. 60–61); `5_Experiments.tex:570`
- Trích: "Việc này do một LLM chạy cục bộ thực hiện"; "vừa với 8 GB bộ nhớ của GPU máy chính"
- Vấn đề: Lý do duy nhất đọc được là chuyện phần cứng. Mà phần lớn lỗi thì lại đến từ năng lực của mô hình (Bảng 6.32, P1 có 14/15 lần thử hỏng vì tổng tỷ trọng). Nếu không có lý do nào khác (tái lập, chi phí, dữ liệu không ra ngoài), hội đồng sẽ cho rằng kết quả LLM yếu là do chọn mô hình nhỏ.
- Câu hội đồng có thể hỏi: "Vì sao không thử một mô hình lớn hơn để có cận trên? Kết luận về LLM có tổng quát được không?"
- Đề xuất sửa: Thêm một đoạn ở 1.3 hoặc 3.5 nêu lý do chọn mô hình cục bộ: tái lập được vì trọng số cố định, không phụ thuộc API, chạy được trên máy phổ thông. Ở mục Hạn chế, ghi rõ kết luận chỉ áp dụng cho mô hình cỡ này.

### [HV-19] Điểm S ghi 4 chữ số thập phân nhưng mỗi ngày chỉ chạy một seed
- Mức: nhỏ
- Vị trí: Bảng 6.29 (`5_Experiments.tex:1096–1110`, PDF tr. 86); Bảng 6.31 (`:1153–1175`, PDF tr. 89); `5_Experiments.tex:526`
- Trích: "S nhỏ nhất 1,1438 (t003) | 1,2386 | 1,1680"; "mỗi ngày hiệu chỉnh ... một lần, với seed 1"
- Vấn đề: Với S, người đọc không có độ lệch chuẩn nào để biết chênh 0,03 có ý nghĩa hay không. Bốn chữ số thập phân tạo cảm giác chính xác giả.
- Đề xuất sửa: Làm tròn S về 2 chữ số. Ghi kèm độ lệch chuẩn của S cho B0 và B1 trên 15 lần chạy (đã có dữ liệu `REF_n1104s5`) làm thước đo nhiễu, để người đọc tự so.

### [HV-20] Hình có nhãn tiếng Anh, danh mục viết tắt quá ngắn
- Mức: nhỏ
- Vị trí: Hình 6.1 (PDF tr. 47, ID cạnh SUMO "711526326#1.up out to SW"); Hình 6.4, 6.5 (PDF tr. 72–73: "Halting illegal lefts...", "simulation time (s)"); danh mục viết tắt (PDF tr. 18, `glossary.tex`)
- Vấn đề: Luận văn viết bằng tiếng Việt nhưng nhãn hình lại bằng tiếng Anh. ID cạnh OSM trên Hình 6.1 không giúp gì cho người đọc.
- Đề xuất sửa: Vẽ lại nhãn trục bằng tiếng Việt, nếu script có sẵn thì chỉ mất vài phút. Trên Hình 6.1 chỉ giữ tên bốn nhánh.

## Thứ đáng học (giữ nguyên, đừng cắt)

- **Khuôn "biến đệm + hậu quả nếu thiếu".** Mỗi luật nêu kèm ràng buộc phụ và điều gì xảy ra nếu bỏ nó đi (`3_Rule_generation.tex:96`; Bảng 3.2, PDF tr. 35; ví dụ trần p_max và điều kiện nút thông ở PDF tr. 32–33). Cách này trả lời trước câu hỏi "tại sao cần cái này". Mình sẽ học theo. Nếu ai đề xuất gộp Ch3 cho ngắn thì đừng cắt phần này.
- **Tách ý tưởng khỏi hiện thực.** Ch3–Ch5 không nhắc tới SUMO, còn Bảng 6.2 (`5_Experiments.tex:121–144`, PDF tr. 105) ánh xạ từng khái niệm sang SUMO. Đây là chỗ duy nhất cho người đọc thấy rõ đâu là ý tưởng của tác giả, đâu là công cụ có sẵn. Nên kéo Bảng 6.2 lên, không bỏ.
- **Nhãn bằng chứng và tách S_sourced / S_assumed.** Bảng 6.10 (PDF tr. 110) gắn nhãn CG/GĐ cho từng mục tiêu. `4_Rule_execution.tex:107` tách điểm theo nguồn. Trung thực, và chặn trước câu hỏi "số này ở đâu ra".
- **Khuôn trình bày từng thí nghiệm: Câu hỏi / Thiết lập / Quan sát / Diễn giải / Giả thuyết cần kiểm chứng.** Xem 6.11.2, PDF tr. 71–74, và quy ước ở `5_Experiments.tex:736`. Tách quan sát khỏi diễn giải rất sạch. Khi tái cấu trúc 6.11 (HV-03) nên giữ khuôn này.
- **Bảng 6.16 cùng Hình 6.3** (`5_Experiments.tex:677–708`): đặt B0, B1 và dữ liệu đặt cạnh nhau, có độ lệch chuẩn, caption nói rõ chu kỳ được chọn không đại diện. Đây là chứng cứ mạnh nhất hiện có.
- **Hình 1.1** (`1_Introduction.tex:35–61`, PDF tr. 21): nhìn một lần là hiểu LLM nằm ở đâu và không nằm ở đâu.

## Chuẩn bị bảo vệ

**Nên lên slide:**
1. Hình 1.1 kèm một câu: "LLM chỉ sinh đặc tả ngoài vòng mô phỏng; mọi thứ khác là mã xác định".
2. Bảng 3.1 (11 hành vi, 3 nhóm) đặt cạnh bảng phủ hành vi đề xuất ở HV-07, nói thẳng hành vi nào đang chạy.
3. Nguyên tắc "chỉ gỡ đúng ràng buộc, chỉ giữ không đẩy" kèm Bảng 6.35 (thử speed mode) và số va chạm 55 so với 7 khi bỏ `ignoreIDs` (PDF tr. 96). Đây là đóng góp dễ thuyết phục nhất.
4. Bảng 6.16 cùng Hình 6.3: B0 có 0% vượt đỏ, B1 có 4,86%, dữ liệu đại diện 9,80%.
5. Bảng 6.31 và 6.32: LLM 9B hợp lệ 12/16 và 14/20 mẫu, mọi lỗi là lỗi cấu trúc và bị bắt trước khi chạy. Kèm thiết kế E1/E2 (Bảng 5.2) như phần dự kiến.

**Câu hỏi nên chuẩn bị:**
1. "SUMO mặc định đủ điều kiện 15/15, bộ luật của em 0/15. Phương pháp giúp được gì?" Trả lời bằng sự khác nhau giữa tiêu chí ổn định và độ giống, dẫn Bảng 6.16 và Bảng 6.33.
2. "Không có số đo tại nút, mọi mục tiêu đều chuyển giao hoặc giả định. Vậy 'giống thực tế' đo bằng gì?" Chuẩn bị nói rõ luận văn chứng minh được gì (quy trình chạy được, bộ thực thi an toàn, LLM sinh được đặc tả hợp lệ) và chưa chứng minh được gì.
3. "Phần nào là của em, phần nào SUMO/Optuna có sẵn?" Dùng Bảng 6.2 và 4 đóng góp đã viết lại theo HV-05.
4. "Vì sao chọn LLM 9B cục bộ? Mô hình lớn hơn có đổi kết luận không?" (HV-18)
5. "P2 hạ S bằng cách bỏ luật. Ràng buộc 'đủ sáu luật' ở v005 có làm LLM mất tự do sinh cấu trúc, tức mất đúng thứ em muốn chứng minh không?" Đoạn liên quan: `3_Rule_generation.tex:202`, 6.11.17.
