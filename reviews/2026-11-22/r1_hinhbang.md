# Hình thức trình bày

> Ghi chú về vị trí. PDF được build từ `Chapter/5_Evaluation.tex`, `6_Implementation.tex`, `7_Conclusions.tex` (theo `main.fls`). Lúc review, ba tệp này không còn trên đĩa. Nội dung tương ứng nằm trong `4_Rule_execution.tex` (phần chương 5 của PDF), `5_Experiments.tex` (chương 6 của PDF) và `6_Conclusions.tex` (chương 7 của PDF). Số dòng dưới đây là số dòng của các tệp hiện có. Mỗi vị trí đều kèm số trang PDF và trích caption hoặc câu, để tìm lại được nếu số dòng đã lệch. "tr. X (in Y)" nghĩa là trang X của tệp PDF, số trang in là Y.

## Đánh giá tổng quát

Bản PDF chưa đem in nộp được vì ba lỗi lộ ngay: bìa ghi sai tên đề tài, mười hai bảng của chương 6 dồn cả về cuối chương (cách đoạn văn nhắc tới chúng tới 57 trang), và ghi chú nháp như "[Câu hỏi cho GVHD: …]" và các "[TODO…]" in đậm vẫn hiện trong thân bài. Hình vẽ ít (7 hình trên 110 trang) và không đồng đều: hai hình TikZ rõ ràng, nhưng các hình matplotlib để nhãn tiếng Anh, chữ rất nhỏ, và mất phân biệt màu khi in đen trắng. Bảng nào cũng kẻ lưới đầy đủ và dùng cột canh đều hai bên, nên chữ trong cột hẹp bị giãn lỗ chỗ, còn tên mã thì bị ngắt bằng gạch nối. Chương 6 chiếm 67/98 trang thân bài, trong khi chương 4 có 3 trang và chương 5 có 5 trang. Nhiều bảng kỹ thuật của chương 6 nên chuyển sang phụ lục.

## Nhận xét

### [HB-01] Bìa chính và bìa lót ghi sai tên đề tài
- Mức: nghiêm trọng
- Vị trí: `Cover.tex:13`, `Cover2.tex:13` (PDF tr. 1, 2)
- Trích: "Mô hình thế giới vĩ mô trong trò chơi máy tính"
- Vấn đề: tên đề tài trên cả hai bìa là tên một đề tài khác (còn sót lại từ một bản trước), không liên quan đến LLM, SUMO hay nút giao.
- Vì sao quan trọng: bìa là trang đầu tiên hội đồng đọc. Tên này cũng phải khớp với quyết định giao đề tài.
- Đề xuất sửa: thay bằng tên đề tài chính thức ở cả hai tệp. Nên định nghĩa một macro `\def\THESISTITLE{…}` trong `main.tex` để hai bìa và `pdftitle` (đang là "LUẬN VĂN THẠC SĨ", `main.tex:121`) dùng chung một chuỗi.

### [HB-02] Mười hai bảng của chương 6 trôi về cuối chương, danh mục bảng mất thứ tự
- Mức: nghiêm trọng
- Vị trí: `5_Experiments.tex:80` (Bảng 6.1), `:121` (6.2), `:146` (6.3), `:180` (6.4), `:218` (6.5), `:245` (6.6), `:284` (6.7), `:405` (6.10), `:446` (6.11), `:677` (6.16), `:1247` (6.34), `:1298` (6.35). Tất cả đều là `[ht]`. Các bảng 6.8, 6.12–6.15 và 6.17–6.33 dùng `[H]` hoặc `longtable`. Cùng lỗi ở `2_Literature_review.tex:84` (Bảng 2.2).
- Trích: "Bảng 6.1: Bốn bản vá mạng cho hành vi cần không gian riêng." được nhắc ở PDF tr. 47 (in 29) nhưng in ở tr. 104 (in 86). Bảng 6.16 nhắc ở tr. 68 (in 50), in ở tr. 111 (in 93). Bảng 6.34 nhắc ở tr. 92 (in 74), in ở tr. 112 (in 94). Bảng 6.4 còn được chương 3 trỏ tới từ tr. 34 (in 16).
- Vấn đề: Bảng 6.1 cao, chỉ được phép `h`/`t` nên không xếp được, và kẹt trong hàng đợi float tới `\clearpage` cuối chương. Mọi bảng `[ht]` sau nó phải xếp hàng phía sau. Các bảng `[H]` thì xếp ngay, vì vậy các trang 104–112 toàn là bảng, và danh mục bảng (PDF tr. 15–18) đọc thành 6.8, 6.9, 6.12, …, 6.33, rồi mới tới 6.1–6.7, 6.10, 6.11, 6.16, 6.34. Bảng 2.2 cũng bị đẩy lên một trang riêng, gần như trắng (PDF tr. 28, in 10).
- Vì sao quan trọng: người đọc bản in phải lật 50–60 trang để xem một bảng đang được nói tới. Mẫu yêu cầu bảng được giới thiệu và bình luận gần chỗ nó xuất hiện.
- Đề xuất sửa: dùng thống nhất `[!htbp]` cho mọi bảng (bỏ trộn `[H]` với `[ht]`). Thêm `\usepackage[section]{placeins}` để float không vượt qua ranh giới mục. Bảng nào cao hơn khoảng 0,7 trang thì chuyển thành `longtable` hoặc tách đôi. Nếu bắt buộc giữ một số bảng `[H]` thì đổi toàn bộ bảng của chương 6 sang `[H]`, để thứ tự đánh số trùng với thứ tự in.

### [HB-03] Ghi chú nháp và câu hỏi gửi GVHD in ra thân bài
- Mức: nghiêm trọng (với bản nộp)
- Vị trí: `4_Rule_execution.tex:103` (PDF tr. 43, in 25); `3_Rule_generation.tex:57` (tr. 30–31, in 12–13); `5_Experiments.tex:400` (tr. 59), `:710` (tr. 70), `:1341` (tr. 97), `:1418` (tr. 101); `6_Conclusions.tex:45` (tr. 115, in 97, ba TODO liền nhau); `0_3_Abstract.tex:17`, `0_4_Abstract_English.tex:17` (tr. 4, 6)
- Trích: "[Câu hỏi cho GVHD: nên làm mượt khoảng cách của tỷ lệ nhỏ …, hay giữ nguyên và nêu là hạn chế?]"; "[TODO_CITE: nguồn hoặc mô tả quan sát cho hành vi 11 …]"; "[TODO: câu kết luận chính về khả năng của LLM cục bộ …]"
- Vấn đề: các ghi chú này in đậm, màu đen, cùng cỡ chữ với văn bản. Khác với `\tamthoi`, quy ước của chúng không được giải thích ở đâu. Câu hỏi gửi GVHD là trao đổi nội bộ, không thuộc nội dung luận văn.
- Vì sao quan trọng: hội đồng sẽ đọc các đoạn này như phần chưa viết xong. Trang tóm tắt có ngay một TODO.
- Đề xuất sửa: thay bằng macro có thể tắt khi in bản nộp, ví dụ `\newcommand{\todo}[1]{\textcolor{blue}{[#1]}}` và `\renewcommand{\todo}[1]{}` lúc build bản nộp. Chuyển câu hỏi cho GVHD ra ghi chú riêng.

### [HB-04] Hình matplotlib: nhãn tiếng Anh, chữ quá nhỏ, dấu thập phân sai, không đọc được khi in đen trắng
- Mức: nên sửa
- Vị trí: `5_Experiments.tex:770` (Hình 6.4, PDF tr. 72, in 54), `:799` (Hình 6.5, tr. 73, in 55), `:703` (Hình 6.3, tr. 69, in 51)
- Trích: tiêu đề trong Hình 6.4 là "Halting illegal lefts at each opposing green end, all seeds (lines: edges of the 3.2 m internal lane)", trục là "posLat (m)" và "front position past the LVL_W stop line …". Hình 6.5 có trục "vehicles", "simulation time (s)" và chú giải "on box lanes", "halting on box lanes", "target p90".
- Vấn đề: (i) nhãn, tiêu đề và chú giải bằng tiếng Anh, có cả tên biến trong mã (`posLat`), trong khi luận văn viết tiếng Việt. (ii) Ở khổ A4, chữ trong hình chỉ khoảng 5–6 pt. (iii) Trục dùng dấu chấm thập phân ("12.5", "3.2 m"), còn văn bản và bảng dùng dấu phẩy. (iv) Ở Hình 6.5, chữ chú giải phía trên bị đường cam đè lên. (v) Hình 6.3 và 6.5 phân biệt nhóm bằng xanh dương và cam. In đen trắng thì hai màu này thành hai mức xám gần nhau, còn đường ô tô màu xám nhạt gần như biến mất.
- Vì sao quan trọng: đây là các hình kết quả duy nhất của luận văn. Bản in đen trắng sẽ không đọc được.
- Đề xuất sửa: vẽ lại bằng script đã có (`compare.py` và script phase 3). Dùng nhãn tiếng Việt, bỏ tiêu đề trong hình (caption đã đủ), đặt `rcParams['font.size']=9` ở kích thước thật (`figsize` khoảng 6,3 × 3 in), `axes.formatter.use_locale=True` với locale vi hoặc đặt `ticker.FuncFormatter` để có dấu phẩy. Phân biệt nhóm bằng kiểu đường hoặc marker (liền/đứt, tròn/tam giác) bên cạnh màu. Đặt chú giải ra ngoài vùng dữ liệu (`loc='upper center', bbox_to_anchor=(0.5,-0.15)`).

### [HB-05] Hình 6.1 (mạng mô phỏng) và Hình 6.6 (ảnh sumo-gui) chưa đọc được trên giấy
- Mức: nên sửa
- Vị trí: `5_Experiments.tex:31–32` (Hình 6.1, PDF tr. 47, in 29); `:816–817` (Hình 6.6, tr. 75, in 57)
- Trích: Hình 6.1 có tiêu đề "Le Van Luong x Hoang Dao Thuy - site.proxy.net.xml (LITERATURE_PROXY)" và các nhãn "953158817#2.up out to NW", "711526328#0 out to SW".
- Vấn đề: Hình 6.1 ghi mã cạnh OSM ở cỡ chữ khoảng 5 pt. Có nhãn chồng lên nhau và bị cắt ("7: … d" ở bên trái). Tiêu đề viết tiếng Anh không dấu, kèm tên tệp. Các "đường đỏ" mà caption nhắc tới chỉ dài vài pixel. Hình không có mũi tên chỉ hướng bắc, và trục đường chạy chéo tây nam–đông bắc, trong khi Hình 6.2 vẽ trục bắc–nam/đông–tây, nên người đọc không ghép được hai hình. Hình 6.6 là ảnh nền đen, tốn mực khi in, và không đánh dấu hai xe máy mà caption nói đã va chạm.
- Vì sao quan trọng: đây là hình duy nhất cho thấy nút giao thật. Người đọc cần nó để theo dõi các tên nhánh LVL_W, HDT_N dùng suốt chương 6.
- Đề xuất sửa: vẽ lại Hình 6.1 chỉ với bốn nhãn nhánh (LVL_W, LVL_E, HDT_N, HDT_S), một mũi tên chỉ hướng bắc, các liên kết vi phạm vẽ dày hoặc phóng to vùng nút trong một khung nhỏ. Bỏ mã OSM và tiêu đề trong hình. Xoay Hình 6.2 cho cùng hướng, hoặc ghi rõ trong caption là sơ đồ đã xoay. Với Hình 6.6, khoanh hai xe bằng vòng tròn có nhãn "A", "B", hoặc dùng sơ đồ màu sáng của `sumo-gui` (`--gui-settings-file` với `background` trắng).

### [HB-06] Quy ước chữ đỏ cho giá trị tạm thời mất khi in đen trắng và áp dụng không đều
- Mức: nên sửa
- Vị trí: định nghĩa ở `main.tex:60` và `5_Experiments.tex:106` (PDF tr. 48, in 30). So sánh `5_Experiments.tex:532` (tr. 62, in 44: `\tamthoi{4}`, `\tamthoi{142}`) với `:920` (tr. 79, in 61: `\textbf{4 va chạm trên làn/h}`, `\textbf{142 va chạm trong nút/h}`).
- Trích: "Các ngưỡng đóng băng là **4 va chạm trên làn/h** và **142 va chạm trong nút/h**" (in đậm đen), trong khi tr. 62 và tr. 95 in cùng hai số này bằng màu đỏ.
- Vấn đề: khi in đen trắng, `\textcolor{red}` thành chữ đen thường, nên người đọc không còn biết số nào là tạm thời. Cùng một giá trị lúc thì in đỏ, lúc thì in đậm đen. Phần mở đầu chương 6 trỏ tới quy ước ở "Mục 6.1", nhưng quy ước nằm ở 6.1.3.
- Vì sao quan trọng: trên bản in đen trắng, người đọc sẽ hiểu nhầm số giả định là số đo.
- Đề xuất sửa: thêm một dấu không phụ thuộc màu, ví dụ `\newcommand{\tamthoi}[1]{\textcolor{red}{#1}\textsuperscript{\dag}}` hoặc gạch dưới bằng `\uline` (gói `ulem`). Nói rõ quy ước này một lần trong phần Danh mục ký hiệu. Đổi `:920` sang `\tamthoi`. Đổi tham chiếu sang `\ref` của mục 6.1.3.

### [HB-07] Dòng tràn lề phải nhìn thấy rõ trên trang
- Mức: nên sửa
- Vị trí (theo `main.log`, chỉ giữ những chỗ thấy được trên PDF):
  - `5_Experiments.tex:611–631`, Bảng 6.14 rộng hơn khối chữ 51 pt (PDF tr. 66, in 48). Nguyên nhân là cột `l` chứa "Mô-đun cấp gốc (`config`, `evaluate`, `schema_observed`, `__init__`)".
  - `:166`, "jmDriveAfterYel-" lòi ra 15,7 pt (tr. 50); `:1283`, cùng chuỗi lòi ra 49 pt (tr. 94, in 76).
  - `:330`, "`traci_rules.json`" lòi ra 33 pt (tr. 54, in 36).
  - `:437`, "PROXY_D4–" lòi ra 24,6 pt (tr. 59, in 41).
  - `:665`, "`test_junction_info_on_proxy_net`" lòi ra 43 pt (tr. 67, in 49).
  - `:1183`, "`moto_violator`." (tr. 90, in 72); đoạn "Thiết lập. … PROXY_D1–" (tr. 75, in 57).
  - `6_Conclusions.tex:41`, "LITERATURE_PROXY" (tr. 115, in 97).
  - Tài liệu tham khảo [17], URL lòi ra 51 pt (tr. 118, in 100).
- Vấn đề: chữ đơn cách trong `\texttt` không có chỗ ngắt dòng, nên dòng chứa nó lòi ra lề phải.
- Vì sao quan trọng: khi đóng gáy, phần lòi ra sát mép xén. Đây cũng là lỗi dàn trang dễ thấy nhất.
- Đề xuất sửa: định nghĩa `\newcommand{\code}[1]{\texttt{\hyphenchar\font=`\-\relax #1}}`, hoặc chèn `\allowbreak` sau `_` như đã làm ở phụ lục A. Với Bảng 6.14, dùng `p{9cm}` thay `l`. Có thể bọc đoạn văn trong `sloppypar` (đã dùng ở `Appendix_A.tex:57`). Với URL trong tài liệu tham khảo, xem HB-19.

### [HB-08] Khoảng trắng lớn do `[H]` kết hợp với `\flushbottom` của chế độ twoside
- Mức: nên sửa
- Vị trí: `5_Experiments.tex:578` (Bảng 6.13 `[H]`, PDF tr. 64 gần như trống, in 46); `:611` (tr. 66, in 48: tiêu đề 6.8.3, rồi một khoảng trắng khoảng 1/4 trang, Bảng 6.14, lại khoảng trắng, rồi 6.9); tr. 71 (in 53, trước Bảng 6.18); tr. 82 (in 64, trước Bảng 6.24); tr. 85 (in 67, quanh Bảng 6.27); `Appendix_A.tex:68` (tr. 123, in 105: mục A.2 chỉ chiếm 1/3 trang)
- Trích: tr. 64 chỉ có hai dòng "Công việc chia thành 15 hạng mục (Bảng 6.13)." rồi bỏ trống cả trang.
- Vấn đề: `[H]` không cho bảng trôi, nên khi bảng không vừa chỗ còn lại thì nó nhảy sang trang sau. Chế độ `twoside` của `report` mặc định bật `\flushbottom`, nên phần trang còn lại bị kéo giãn đều vào các khoảng cách đoạn.
- Vì sao quan trọng: bản in có nhiều trang nửa trắng, trông như thiếu nội dung.
- Đề xuất sửa: thêm `\raggedbottom` vào preamble và thay `[H]` bằng `[!htbp]` (kết hợp với HB-02).

### [HB-09] Bảng kẻ lưới kiểu cũ, cột canh đều hai bên, mã định danh bị ngắt bằng gạch nối
- Mức: nên sửa
- Vị trí: `2_Literature_review.tex:13` (Bảng 2.1, PDF tr. 24, in 6); `5_Experiments.tex:365` (Bảng 6.9, 3 trang, tr. 56–58); `:720` (Bảng 6.17, tr. 70); `:1153` (Bảng 6.31, tr. 89); `:180` (Bảng 6.4, tr. 106); `Appendix_A.tex:87` (Bảng A.4, tr. 125); `Appendix_B.tex:13` (Bảng B.1, tr. 127); `Appendix_A.tex:71` (Bảng A.3, tr. 124)
- Trích: Bảng 2.1 có ô "Hai nút có đèn ở Hà Nội (Láng Hạ – Láng; Vũ Phạm Hàm – Nguyễn Khang), video" với khoảng trắng giữa các từ rất lớn. Bảng 6.17 có "Lê     Văn Lương tây". Bảng 6.9 ngắt mã thành "Missing-FieldDataError", "In-validSpecError", "Com-mands". Ở Bảng A.3, "motorcycle0,9" dính vào cột bên cạnh.
- Vấn đề: cột `p{}` canh đều hai bên, nên cột hẹp bị giãn chữ. Kẻ khung đầy đủ `|…|` với `\hline` sau mỗi dòng làm bảng nặng nề. Gạch nối chèn vào giữa tên lớp hoặc tên tệp sẽ làm người đọc hiểu sai tên. Cột vClass của Bảng A.3 rộng 2,2 cm, hẹp hơn chuỗi `motorcycle`.
- Vì sao quan trọng: bảng là phương tiện trình bày chính của luận văn (54 bảng, 7 hình). Bảng khó đọc thì cả chương 6 khó đọc.
- Đề xuất sửa: dùng `booktabs` (`\toprule`, `\midrule`, `\bottomrule`), bỏ kẻ dọc, và chỉ kẻ ngang giữa các nhóm dòng. Thêm `\usepackage{array}` (đã có) và khai báo cột `>{\raggedright\arraybackslash}p{…}`, hoặc dùng `tabularx` với cột `X` canh trái. Không cho ngắt từ trong `\texttt` (`\hyphenchar\font=-1`), thay vào đó cho phép ngắt sau `_`. Nới cột vClass của Bảng A.3 lên khoảng 2,6 cm.

### [HB-10] Caption bảng ở phụ lục đặt dưới, ở thân bài đặt trên; dấu chấm cuối caption không thống nhất
- Mức: nên sửa
- Vị trí: `Appendix_A.tex:30` (A.1), `:53` (A.2), `:80` (A.3), `:96` (A.4), `Appendix_B.tex:24` (B.1); PDF tr. 121–127
- Trích: "Bảng A.4: Các luật TraCI của B1" (đặt dưới bảng, không có dấu chấm), trong khi "Bảng A.5: Từng đặc tả đã đánh giá trên mạng F2." (đặt trên bảng, có dấu chấm).
- Vấn đề: 49 bảng trong thân bài đặt caption trên bảng (theo thông lệ Việt Nam), còn năm bảng phụ lục đặt caption dưới. Ví dụ bảng trong mẫu (`_template_orig/Chapter/Appendix_A.tex:72`) cũng đặt caption dưới, nhưng luận văn đã chọn đặt trên, nên phải nhất quán. Trong danh mục bảng, có dòng kết thúc bằng dấu chấm, có dòng không.
- Vì sao quan trọng: quy cách không thống nhất trong cùng một quyển là lỗi hình thức mà thư ký hội đồng thường bắt.
- Đề xuất sửa: chuyển `\caption` lên trước `\begin{tabular}` ở năm bảng phụ lục, và kết thúc mọi caption bằng dấu chấm. Có thể ép thống nhất bằng `\captionsetup[table]{position=top}`.

### [HB-11] Cùng một đại lượng in với số chữ số thập phân khác nhau
- Mức: nên sửa
- Vị trí: Bảng 6.24 (`5_Experiments.tex:965`, PDF tr. 82) và 6.25 (`:996`, tr. 83) in điểm tổng S với 3 chữ số thập phân. Bảng 6.29 (`:1099`, tr. 86), 6.31 (`:1156`, tr. 89) và 6.33 (`:1215`, tr. 91) in S với 4 chữ số. Số va chạm/h là "1,333" ở tr. 62 và "1,8667" ở tr. 62 và 88.
- Trích: B0 trên mạng 29/10 có "S = 1,225" ở Bảng 6.25 nhưng "1,2247" ở Bảng 6.29.
- Vấn đề: cùng một số được làm tròn khác nhau giữa hai bảng liền nhau. 4 chữ số thập phân cho S và cho va chạm/h là độ chính xác giả, vì số lần chạy chỉ là 3 hoặc 15.
- Vì sao quan trọng: người đọc có thể nghĩ hai bảng đo hai thứ khác nhau.
- Đề xuất sửa: chốt một quy tắc, ví dụ S lấy 3 chữ số, tỷ lệ mỗi giờ lấy 1 chữ số, tỷ lệ phần trăm lấy 1–2 chữ số. Áp dụng quy tắc này trong script xuất bảng. Có thể dùng `siunitx` (`\num[round-mode=places,round-precision=3]{…}`, `output-decimal-marker={,}`) cho các cột số, kèm cột `S` căn theo dấu phẩy.

### [HB-12] Chương 6 quá dài; nhiều bảng kỹ thuật nên chuyển sang phụ lục
- Mức: nên sửa
- Vị trí: chương 6 chiếm PDF tr. 46–112 (in 28–94), tức 67/98 trang thân bài. Chương 4 có 3 trang (tr. 38–40), chương 5 có 5 trang (tr. 41–45). Các bảng nên chuyển: 6.9 (`5_Experiments.tex:365`, 3 trang, tr. 56–58), 6.12 phiên bản thư viện (`:541`), 6.13 hạng mục (`:578`), 6.14 số dòng mã (`:611`), 6.15 bộ kiểm thử (`:638`), 6.11 phiên bản prompt (`:446`), 6.30 kích thước prompt (`:1132`).
- Trích: "Bảng 6.14: Kích thước mã nguồn theo gói."; "Bảng 6.12: Thư viện và công cụ sử dụng." (cột "Đã cài" ghi các phiên bản 3.12.10, 6.0.3, …)
- Vấn đề: các bảng này là tư liệu tái lập, không phục vụ lập luận chính, nhưng chen giữa các mục kết quả. Riêng 6.11 có 20 tiểu mục.
- Vì sao quan trọng: người đọc bản in mất mạch giữa phương pháp và kết quả. Tỷ lệ độ dài giữa các chương lệch rõ.
- Đề xuất sửa: tạo Phụ lục C "Chi tiết cài đặt và tái lập", chuyển các bảng trên cùng mục 6.13 vào đó. Trong chương 6 chỉ giữ một câu tóm tắt và tham chiếu tới phụ lục. Cách này còn giảm số float cần xếp chỗ ở HB-02.

### [HB-13] Đề mục: tiểu mục kiểu nhật ký có ngày tháng, sai cấp ở mục 6.2, số trang có ba chữ số dính vào dấu chấm trong mục lục
- Mức: nên sửa
- Vị trí: mục lục PDF tr. 10–11. Ví dụ "6.11.9 Cập nhật kịch bản và kết quả trên hai mạng ngày 28/10", "6.11.10 Kết quả tham chiếu B0, B1 trên mạng 29/10", "6.11.14 Thay đổi ngày 04/11 và kết quả tham chiếu trên mạng 04/11". Sai cấp ở `5_Experiments.tex:142` và `:168` (PDF tr. 49–50): "a, Tham số tĩnh", "b, Luật có điều kiện" đứng ngay dưới mục 6.2, trước 6.2.1. Số trang ba chữ số ở tr. 11–12: "TÀI LIỆU THAM KHẢO......101", "A. MIỀN THAM SỐ … TỪNG ĐẶC TẢ.........103".
- Vấn đề: tiêu đề gắn với ngày chạy và tên phiên bản mạng (F2, 28/10 đợt 1, 29/10, 04/11) chỉ tác giả hiểu. `\subsubsection` đặt thẳng dưới `\section` làm hai mục a, b không có mục cha (chúng cũng không vào mục lục). Số trang 3 chữ số vượt `\contentsmargin` mặc định nên dính vào hàng chấm.
- Vì sao quan trọng: mục lục là thứ hội đồng đọc trước tiên để nắm cấu trúc luận văn.
- Đề xuất sửa: đặt tên tiểu mục theo câu hỏi thực nghiệm (ví dụ "Ảnh hưởng của luật vượt đèn đỏ đến khóa nút"), còn ngày và phiên bản mạng chuyển vào câu đầu của mục hoặc vào Bảng 6.17. Đổi a, b ở 6.2 thành `\subsection` (6.2.1 Tham số tĩnh, 6.2.2 Luật có điều kiện), hoặc thành đoạn chạy in đậm như ở 6.6. Thêm `\contentsmargin{2.5em}` trước `\tableofcontents` (gói `titletoc` đã nạp).

### [HB-14] Caption không tự đứng được; danh mục hình và bảng quá dài
- Mức: nên sửa
- Vị trí: `5_Experiments.tex:1027` (Bảng 6.26), `:1156` (6.31), `Appendix_A.tex:113` (A.5), `5_Experiments.tex:877` (6.21), `:703–705` (Hình 6.3, caption dài 8 dòng); danh mục hình PDF tr. 13–14, danh mục bảng tr. 15–18
- Trích: "Biến thể chẩn đoán của B1 trên PROXY_D2. Số trong ô ghi theo seed 1, 2, 3; …"; "Ba chiến dịch trên mạng 04/11 (…). Giờ Hà Nội ngày 08/11/2026."; "Từng đặc tả đã đánh giá trên mạng F2."; "Kết quả bốn thí nghiệm khả thi Phase 3A–3D."
- Vấn đề: caption dùng mã nội bộ (B1, PROXY_D2, mạng F2, Phase 3A–3D, REF) mà không nói đó là gì. Đọc riêng caption thì không biết bảng đo cái gì. Thông tin "Giờ Hà Nội ngày 08/11/2026" không giúp hiểu bảng. Ngược lại, caption Hình 6.3, 6.4, 6.5 dài 5–8 dòng và được chép nguyên vào danh mục hình, nên danh mục 7 hình chiếm 2 trang.
- Vì sao quan trọng: mẫu yêu cầu bảng và hình được hiểu khi đọc riêng. Danh mục hình và bảng dài, khó tra.
- Đề xuất sửa: viết caption theo dạng "<đại lượng> của <phương án> trên <dữ liệu>", ví dụ "Teleport kẹt và va chạm của bộ luật thủ công B1 khi bỏ từng thành phần, ngày đại diện PROXY_D2". Dùng `\caption[ngắn]{dài}` cho mọi caption dài hơn hai dòng, để danh mục chỉ hiện bản ngắn.

### [HB-15] Danh mục viết tắt thiếu nhiều mục; không có danh mục ký hiệu và mã phương án
- Mức: nên sửa
- Vị trí: `glossary.tex:5–40` (6 mục), PDF tr. 18 (in vi)
- Trích: danh mục chỉ có GEH, LLM, OSM, PET, SUMO, TraCI. Thân bài còn dùng IDM, MOBIL (tr. 26), SSM (tr. 65), TPE (tr. 61), IQR (tr. 42), JSON, XSD (tr. 57), TCVN, TCCS (tr. 48–49), ADAS (TLTK [2]), MCP (tr. 27).
- Vấn đề: thiếu các từ viết tắt phổ biến trong bài. Ngoài ra, các mã B0, B1, B2, P1, P2, H (sáu phương án), E1, E2 (hai thí nghiệm so sánh), G0 và M1–M10 (cổng lưu lượng và mười chỉ số), PROXY_D1–D5 (năm ngày dữ liệu đại diện) và tên các phiên bản mạng (F2, 28/10, 29/10, 04/11) chỉ được định nghĩa trong Bảng 5.1, Bảng 5.2 và Bảng 6.17. Người đọc nhảy vào chương 6 không có chỗ tra.
- Vì sao quan trọng: chương 6 dày đặc các mã này. Luận văn đã có danh mục viết tắt theo mẫu, nên chỉ cần bổ sung.
- Đề xuất sửa: thêm các mục còn thiếu vào `glossary.tex`. Thêm một danh mục "Ký hiệu và mã dùng trong luận văn" (dùng `\newglossary` thứ hai, hoặc một bảng ngắn sau danh mục viết tắt), mỗi mã kèm nghĩa, ví dụ "M8: tỷ lệ đi sai làn", "M9: chặn làn rẽ phải liên tục".

### [HB-16] Công thức chính chỉ viết bằng lời; ký hiệu không thống nhất; font toán khác font chữ
- Mức: nên sửa
- Vị trí: `4_Rule_execution.tex:101–107` (hàm khoảng cách, tỷ số R, điểm tổng S; PDF tr. 42–43, in 24–25); `3_Rule_generation.tex:117`, `:150` ($t_{\text{before}}$) so với `5_Experiments.tex:188` và `Appendix_A.tex:91` ($t_{\text{before\_green}}$); `main.tex:18` (`times`)
- Trích: "khoảng cách giữa mô phỏng và quan sát là khoảng cách Wasserstein bậc 1 chia cho khoảng tứ phân vị (IQR)…"; "Điểm tổng S là trung bình có trọng số của các khoảng cách."
- Vấn đề: cả luận văn chỉ có một phương trình được đánh số, là (3.1). Hàm khoảng cách, quy tắc chặn trên $D_{\text{empty}}$, tỷ số R và trọng số của S, tức phần định nghĩa đánh giá, chỉ được tả bằng lời, nên các chương sau không trỏ tới chúng được. Tham số xuất phát sớm được gọi là $t_{\text{before}}$ ở chương 3 nhưng $t_{\text{before\_green}}$ ở Bảng 6.4 và Bảng A.4. Gói `times` chỉ đổi font chữ thường, nên chữ số trong môi trường toán (ví dụ "$t = 2647$ s", "$[300, 1800)$ s", tr. 62, 75) hiện bằng font Computer Modern, và log có cảnh báo "Font shape `OT1/cmr/m/n' in size <13> not available".
- Vì sao quan trọng: thiếu công thức hiển thị thì phản biện không kiểm tra được cách tính điểm. Ký hiệu lệch giữa các chương làm người đọc tưởng đó là hai tham số khác nhau.
- Đề xuất sửa: viết 3–4 phương trình có đánh số cho $d$, $R$, $S$ và $S_{\text{sourced}}/S_{\text{assumed}}$ ở mục 5.2.2, và tham chiếu chúng bằng `\eqref`. Thống nhất một tên $t_{\text{before}}$. Thay `\usepackage{times}` bằng `\usepackage{mathptmx}` (đổi cả font toán sang Times, tương thích với `vietnam`).

### [HB-17] Thiếu hình ở những chỗ đang phải dùng bảng dài hoặc lời tả
- Mức: nhỏ
- Vị trí: mục 6.4 Kiến trúc phần mềm (PDF tr. 54–58) chỉ có Bảng 6.8 và Bảng 6.9 (3 trang); mục 3.4 Biểu diễn luật (tr. 34–35) chỉ có Bảng 3.3 mô tả cấu trúc đặc tả. Gói `listings` đã nạp (`main.tex:35`) nhưng không có listing nào. Không có ảnh vệ tinh hay ảnh hiện trường của nút.
- Trích: "Bảng 6.9: Các gói con của `thesis_sumo` và quyết định thiết kế." (3 trang)
- Vấn đề: một sơ đồ phụ thuộc giữa các gói (`config`, `net`, `proxy`, `demand`, `rules`, `runtime`, `sim`, `metrics`, `evaluate`, `llm`, `baselines`) sẽ thay được phần lớn Bảng 6.8 và Bảng 6.9. Người đọc chưa thấy một đặc tả JSON thật trông như thế nào.
- Vì sao quan trọng: hội đồng thường hỏi "LLM trả về cái gì". Một listing 15–20 dòng trả lời câu này nhanh hơn Bảng 3.3.
- Đề xuất sửa: vẽ một hình TikZ kiến trúc thay cho Bảng 6.8, và chuyển Bảng 6.9 sang phụ lục (cùng HB-12), để chương 6 không dài thêm. Thêm một listing rút gọn của `B1_manual.json` vào mục A.2 (`\lstset{basicstyle=\ttfamily\small, breaklines=true}`). Nếu có ảnh hiện trường, ghép vào cạnh Hình 6.2 bằng `subcaption`.

### [HB-18] Tài liệu tham khảo: URL giãn khoảng trắng, tên tác giả không thống nhất, một tiêu đề sai chữ hoa
- Mức: nhỏ
- Vị trí: PDF tr. 117–119 (in 99–101); `reference.bib:81`, `:92`, `:112`, `:239`
- Trích: "[Online]. Available: https : / / elib . dlr . de / 104432/" ([2]); "DOI: 10 . 11175 / easts.6.1496" ([10]); "Dealing with mixed and non-normative traffic. an agent-based simulation …" ([5]); "Transport Analysis Guidance; cập nhật ngày 28/05/2026" ([17], mục tiếng Anh xen tiếng Việt)
- Vấn đề: biblatex chèn khoảng co giãn vào URL, nên khi canh đều dòng thì giữa các ký tự `:`, `/`, `.` hở ra. Tên tác giả lúc ghi đầy đủ (Mai Van Hieu, Chu Cong Minh, Nguyen Thi Yen Lien), lúc viết tắt (P. A. Lopez). Kiểu IEEE chuyển tiêu đề về chữ thường, nên "An" thành "an". [22] và [23] không có nơi phát hành hay đường dẫn.
- Vì sao quan trọng: mẫu quy định kiểu IEEE và yêu cầu đủ trường cho tài liệu Internet (`_template_orig/Chapter/7_Reference.tex:32`).
- Đề xuất sửa: thêm `\setlength{\biburlnumskip}{0pt}`, `\setlength{\biburlucskip}{0pt}`, `\setlength{\biburllcskip}{0pt}`, hoặc đặt `\printbibliography` trong `{\raggedright …}`. Bọc "{An}" ở `reference.bib:81`. Viết tên tác giả Việt dạng `family, given` để biblatex tự viết tắt thống nhất (bỏ cặp ngoặc `{{Mai Van Hieu}}`). Chuyển note của [17] sang tiếng Anh, hoặc dùng trường `urldate`.

### [HB-19] Lệch quy định của mẫu ở phần đầu
- Mức: nhỏ
- Vị trí: `0_3_Abstract.tex` (PDF tr. 3–4); `main.tex:158`; `1_Introduction.tex:90` (tr. 22, in 4)
- Trích: mẫu yêu cầu "Sinh viên viết tóm tắt … với 200 đến 350 từ" (`_template_orig/Chapter/0_3_Abstract.tex:8`); "% \subfile{Chapter/0_2_Acknowledgment.tex} % tạm bỏ theo yêu cầu"; mục 1.5 dùng `enumerate` đánh số 1–4.
- Vấn đề: tóm tắt tiếng Việt khoảng 500 từ và tràn sang trang thứ hai (bản tiếng Anh cũng vậy). Trang Lời cảm ơn của mẫu đang tắt. Mẫu yêu cầu liệt kê theo kiểu (i), (ii) trong câu và hạn chế danh sách gạch đầu dòng (`_template_orig/Chapter/Appendix_A.tex:13–14`).
- Vì sao quan trọng: thư ký hội đồng kiểm tra đúng những điểm này khi nhận quyển.
- Đề xuất sửa: rút tóm tắt về một trang (bỏ phần kể các mạng và ngân sách chạy, chỉ giữ kết quả chính). Bật lại Lời cảm ơn trước khi nộp. Chuyển bốn đóng góp ở 1.5 thành một đoạn văn có (i)–(iv), hoặc giữ danh sách nhưng ghi rõ đây là ngoại lệ có chủ ý.

### [HB-20] Chương 2 và chương 4 kết thúc với nửa trang trống, có một trang bảng đứng riêng
- Mức: nhỏ
- Vị trí: `2_Literature_review.tex:84` (Bảng 2.2 `[ht]`, PDF tr. 28, in 10); tr. 26–27 (in 8–9)
- Trích: tr. 28 chỉ có "Bảng 2.2: Giới hạn của các công trình hiện có và hướng xử lý của luận văn." đặt giữa trang, phía trên và phía dưới để trắng.
- Vấn đề: Bảng 2.2 được nhắc ở tr. 27, nhưng không vừa chỗ còn lại nên bị đẩy về cuối chương và đứng một mình trên một trang float. Câu "Bảng 2.2 gom bốn giới hạn …" đứng trước một đoạn văn không nói về bảng.
- Vì sao quan trọng: thêm một trang gần như trống, và bảng tách khỏi đoạn văn nói về nó.
- Đề xuất sửa: đặt `\begin{table}[!htbp]` ngay sau đoạn giới thiệu, hoặc rút bảng xuống còn 3 cột hẹp hơn để vừa tr. 27. Áp dụng chung với HB-02.
