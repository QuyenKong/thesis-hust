# Tổng hợp phản biện luận văn (Latex_SOICT, bản 22/11/2026)

Bảy reviewer đọc luận văn qua hai vòng. Vòng 1 mỗi người đọc độc lập theo góc nhìn riêng (`r1_*.md`). Vòng 2 mỗi người tự kiểm lại nhận xét của mình trên bản 6 chương hiện tại, rồi phản biện chéo nhận xét của sáu người kia (`r2_*.md`). Bản được đọc ở vòng 2 là PDF build lại từ nguồn hiện tại, 131 trang. Số trang dưới đây là số in ở chân trang của bản đó (trang trong tệp PDF bằng số in cộng 18). Số dòng có dạng `5:1437`, nghĩa là `Chapter/5_Experiments.tex` dòng 1437.

Vòng 1 diễn ra trong lúc luận văn được cấu trúc lại (22:30–22:37 ngày 22/11). Vì vậy một số reviewer đọc PDF bản 7 chương cũ. Vòng 2 đã đối chiếu lại toàn bộ trên bản mới. Nhận xét nào còn hiệu lực mới được đưa vào đây. Nhận xét duy nhất hết hiệu lực là HD-10 (cách chia Chương 3/4 lệch Hình 1.1), vì bản mới đã sửa.

Mã nhận xét: HD hội đồng, ND người đọc ngoài ngành, VP văn phong, HB hình thức, LG lập luận, HV học viên cùng khóa, GT sinh viên giao thông.

## 1. Việc bạn cần quyết định trước khi sửa

Các việc dưới đây quyết định cách sửa nhiều chỗ khác, nên làm trước.

| # | Việc | Chi tiết | Nguồn |
|---|------|----------|-------|
| 1 | Tên đề tài trên bìa | "Mô hình thế giới vĩ mô trong trò chơi máy tính" là tên đã đăng ký nhưng lệch hẳn nội dung. Cần hỏi GVHD hoặc phòng đào tạo ngay tuần này, vì thủ tục đổi tên có thể không kịp hạn nộp. Nếu không đổi được thì cần một đoạn ở 1.1 nối tên đăng ký với nội dung, và chuẩn bị trước câu trả lời cho hội đồng. `pdftitle` hiện là "LUẬN VĂN THẠC SĨ" (`main.tex:73`, `:121`). | HD-01, ND-01, HB-01, HV-01; HV bỏ sót 1 |
| 2 | Bảng 5.31 lấy từ chiến dịch chạy bằng Sonnet | Caption Bảng 5.31 (`5:1135`, tr. 73) ghi số liệu "dựng lại từ kết quả chiến dịch P2 trên mạng 28/10 đợt 2". Mình đã kiểm `SUMO/experiments/campaigns/P2_n28b`: mọi đặc tả ở đó có `"model": "claude-sonnet (stand-in)"`. Tương tự với `P2_n28`, `P1_n28`, `P1_n28b`, `P1`, `P2`. Theo quy ước của bạn, kết quả của Sonnet không được có trong báo cáo. Hướng sửa: bỏ Bảng 5.31 và câu "46.300 token" ở `5:1130`, nêu lý do sửa prompt `v004` bằng lời; hoặc đo lại kích thước prompt trên một chiến dịch qwen. | LG-15, HV bỏ sót 3; mình xác minh |
| 3 | Phạm vi của hành vi 7 (đi trên vỉa hè) và hành vi 8 (đi ngược chiều) | `CLAUDE.md` của dự án xếp cả hai ngoài phạm vi. Luận văn thì mô hình hóa vỉa hè đầy đủ (Bảng 5.1, chỉ số M10 (đi trên vỉa hè), thí nghiệm 3B) và gọi hành vi 8 là "hoãn". GT muốn đưa cả hai ra ngoài phạm vi. LG, HD, HV, ND muốn giữ vỉa hè (vì đã có kết quả) và chỉ đổi "hoãn" thành "ngoài phạm vi, kèm lý do" cho hành vi 8. Dù chọn cách nào, bốn chỗ phải nói cùng một điều: Mục 1.4.2 (tr. 5), Bảng 3.1 (tr. 16), Mục 5.1.1 (tr. 30) và tóm tắt. | GT-01; LG, HD, HV, ND vòng 2 |
| 4 | Hành vi 6 (chặn làn rẽ phải) và mô tả làn 0 | Tr. 31 (`5:23`) viết "Đi thẳng hoặc rẽ trái trên làn này khi đèn xanh là đúng luật". Bảng 5.1 (tr. 89) lại viết "Rẽ trái và quay đầu chỉ có kết nối từ lane 2". Nếu đi thẳng trên làn 0 là đúng luật thì xe đi thẳng chờ đèn đỏ ở đó không vi phạm gì. Khi đó hành vi 6 là tương tác giữa hai dòng trên một làn dùng chung, và mục tiêu của M9 (chặn làn rẽ phải), "xác suất xe đi thẳng chọn lane 0", đo một lựa chọn hợp lệ. Cần đối chiếu với vạch sơn và biển tại nút. Nếu chưa có số đo thì ghi `TODO_MEASURE`. | GT-02; LG, HD đồng ý mức nghiêm trọng |
| 5 | E1/E2 có kịp trước hạn 12/2026 không | Tóm tắt, `5:710`, `5:1418` và `6:45` đang chừa chỗ cho kết quả E1/E2. HV đề xuất viết trước bản không có E1/E2: xóa mọi TODO, đưa E1/E2 vào hướng phát triển, và ghi câu hỏi "LLM so với Optuna" là chưa trả lời. Nếu sau đó có kết quả thì chỉ cần thêm vào. | HV bỏ sót 5 |
| 6 | `accel` của B1 | Sửa B1 rồi chạy lại, hay giữ nguyên và nêu như một hạn chế. Viết theo cách nào thì cũng không được gọi `accel` là "nguyên nhân" (xem Mục 2). Hiện câu "chưa được quyết định" lặp ở bốn chỗ (`5:1230`, `Appendix_A:100`, `6:45`, `6:51`). | HV-13, LG-01 |
| 7 | Lời cảm ơn | `main.tex:158` ghi tạm bỏ theo yêu cầu (28/10). HB-19 đề xuất bật lại, HV phản đối khi chưa hỏi. Mình để nguyên, trừ khi bạn muốn khác. | HB-19, HV vòng 2 |

## 2. Các câu khẳng định mạnh hơn số liệu

Phần này đáng sửa nhất, vì hội đồng sẽ đối chiếu và bắt được. Mọi câu dưới đây đã được ít nhất ba reviewer kiểm lại ở vòng 2. Vòng 1 có năm reviewer đề xuất câu viết lại cho tóm tắt nhưng chính các câu đó cũng mắc những lỗi này. Vòng 2 đã rút các câu đó, nên cột "Viết lại" là bản đã được phản biện.

| Câu hiện tại | Vị trí | Vì sao sai | Viết lại |
|---|---|---|---|
| "nguyên nhân chính là gia tốc xe máy chuyển giao từ tài liệu" | tóm tắt (cả hai bản), `5:1437`, `6:33`, `Appendix_A:100` | Phân tích loại bỏ chỉ chạy trên B1, ngày PROXY_D1, 3 seed. Trả `accel` về mặc định vẫn còn 10, 126 và 52 xe chờ chèn. Thử nghiệm B2 với `accel` 5,8 vẫn còn 256 xe. P2 không dùng cấu trúc B1, và ở PROXY_D2–D3 bị loại vì va chạm. | "`accel` 1,1 m/s² chuyển từ IDM là yếu tố lớn nhất trong các biến thể B1 đã thử ở PROXY_D1; riêng nó chưa giải thích hết số xe chờ chèn." (LG-01) |
| "ở chế độ sinh cả cấu trúc, mô hình hạ S bằng cách bỏ bớt luật" | `6:33`, `5:1176`, `5:1285`, `5:1437` | B2 giữ đủ cấu trúc B1 mà có S nhỏ nhất 1,1438, thấp hơn P2 (1,1680). Chưa có thí nghiệm nào thêm lại các luật đã bỏ để so S. | "Từ vòng 2, P2 giữ một cấu trúc thiếu ba loại luật; chưa kiểm tra việc bỏ luật có làm giảm S hay không." (LG-02) |
| "LLM cục bộ mắc chủ yếu lỗi cấu trúc", "mọi lỗi trong bảng là lỗi cấu trúc" | `5:1185`, `5:1285`, tóm tắt, `6:33` | Ở P1, 14/15 lần thử hỏng vì tổng tỷ trọng khác 1, tức lỗi giá trị. Bảng 5.33 còn có 4 lỗi giá trị ngoài miền. | "P2 mắc chủ yếu lỗi cấu trúc (mã nguyên mẫu trùng tên phân phối); P1 mắc chủ yếu lỗi tổng tỷ trọng; bộ kiểm tra hợp lệ bắt mọi lỗi trước khi chạy." (LG-12) |
| B0 là "mô hình mặc định của SUMO"; khoảng trống "SUMO mặc định không có dừng chờ giữa nút" | `1:16`, Bảng 2.2 (tr. 10–11), Bảng 5.12 (`5:488`), `5:774` | B0 chạy trên mạng có bản vá, có kết nối rẽ trái cho lớp vi phạm và có nhu cầu gồm lớp vi phạm. B0 đã có 4,00 xe chờ giữa nút mỗi chu kỳ (B1 có 4,89). Câu "Không cần tùy chọn hay sửa mạng" ở `5:774` trái với Bảng 5.1. | Định nghĩa lại B0: "vType mặc định, không có luật TraCI, chạy trên cùng mạng có bản vá và cùng nhu cầu như mọi phương án". Trong tóm tắt, kết quả dương chỉ nêu vượt đèn đỏ (B0 0%, B1 4,86%). Thêm một câu nói xe chờ giữa nút có ở cả B0 vì đến từ bản vá mạng. (LG-03) |
| "nên một bộ luật không thể 'khớp' dữ liệu nhờ va chạm" | `1:67` (tr. 4) | Ngưỡng 142 va chạm trong nút mỗi giờ "gần như không loại lần chạy nào" (`5:922`). Khi không đặc tả nào đủ điều kiện, quy tắc dự phòng bỏ mức trần va chạm, và đã chọn đặc tả có 46,0 và 51,3 va chạm trên làn mỗi giờ. | Bỏ vế này ở Chương 1. Đưa giới hạn của quy tắc dự phòng vào mục Hạn chế. VP phản đối câu thay mà LG đề xuất, vì câu đó lại khẳng định một điều chưa có số liệu. |
| "P1 không thể đủ điều kiện dù LLM chọn tham số thế nào" | `6:39`, `6:51`, `5:1176`, `5:1235` | Chỉ có 12 thử nghiệm B2 và 6 biến thể loại bỏ, mỗi biến thể 3 seed. | "...gợi ý cấu trúc B1 khó đủ điều kiện ở PROXY_D1, chưa chứng minh là không thể." (LG-05) |
| G0: "GEH < 5 ở ≥ 85% ô [TAG]" | `4:83` (tr. 28) | Ngưỡng của TAG dùng cho lưu lượng giờ. GEH tăng theo căn bậc hai của số đếm, nên GEH < 5 trên số đếm 15 phút tương đương khoảng GEH < 10 theo giờ. Các ô tách theo loại xe và hướng thường chỉ có vài xe, nên gần như luôn đạt. | Bỏ gắn với TAG, hoặc quy về lưu lượng giờ (nhân 4) trước khi tính. (GT-05) |
| "cao điểm sáng 07:30–09:00" | tóm tắt, `5:21`, `6:15` | Mọi chỉ số tính trên [300, 1800) s, tức 07:35–08:00. `5:530` ghi "thời lượng đầy đủ 3600 s" trong khi khung 07:30–09:00 dài 5400 s. | "Khung nghiên cứu 07:30–09:00; các thực nghiệm hiện tại mô phỏng 07:30–08:00 và tính chỉ số trên 07:35–08:00." (LG-07, GT-08) |
| "Bộ luật thu được là một tệp văn bản, dùng lại được"; "thứ LLM có thể đề xuất còn bộ tối ưu số thì không" | `1:11`, `1:65` | Chưa có bộ luật nào đủ điều kiện. Năng lực đề xuất cấu trúc của LLM mới là giả thuyết. | "Bộ luật mục tiêu là..."; "...phần luận văn giả thuyết rằng LLM có thể đề xuất". (LG-13) |
| "SUMO tự mô phỏng được xe chờ giữa nút với sức chứa 8 xe" | `5:1437` (tr. 88) | Con số 8 đo trên vùng chờ 3,2 m của mạng đã bỏ. Trên vùng chờ 3,5 m thì dao động 7–13 tùy seed. Sức chứa của hai vùng chờ Hoàng Đạo Thúy chưa đo. | Ghi đúng mạng và khoảng giá trị. (LG-14) |
| M7b (độ trễ giải phóng vùng chờ) được ghi là "đại diện cho PET" | `4:90`, `3:87` | PET đo trên từng cặp xung đột. Độ trễ rời vùng chờ là một đại lượng khác. Không chỉ số nào đo PET. | Bỏ "đại diện cho PET". Nói rõ mục tiêu 5,65 s được suy ra thế nào. (GT-09) |
| "Số xe chờ giữa nút của B1 là 4,89, gần mức 5,59 của dữ liệu đại diện hơn B0" | `5:697` (tr. 53–54) | Mục tiêu của nhóm M7 (chờ giữa nút) là giá trị giả định. | Ghi kèm nhãn giả định. (LG bỏ sót 5) |
| Bảng 5.17 dùng làm bằng chứng chính | Bảng 5.17 (tr. 96) | 15 lần chạy B1 trong bảng đều bị chính tiêu chí của luận văn loại. | Nói trước trong phần Diễn giải của 5.11 vì sao tỷ lệ vượt đỏ vẫn đọc được. Nếu có số liệu riêng trên PROXY_D2–D3 thì thêm. (HV bỏ sót 2) |
| Mục tiêu của M2 (xuất phát sớm) lấy giá trị 0,1582 từ Mai và cs. | Bảng 4.1, Bảng 5.10 | M2 (xuất phát sớm) đếm xe qua vạch trong 10 s cuối của thời gian đỏ. Mai và cs. đếm xe qua vạch từ khoảng 5 s trở lên trước đèn xanh. Một lượt qua vạch trong 10 s cuối của thời gian đỏ lại được tính cả vào M3 (vượt đèn đỏ). | Định nghĩa M2 và M3 loại trừ nhau bằng một ký hiệu T. Nêu cách xử lý đèn vàng và đỏ toàn phần. Chọn T khớp nguồn, hoặc giải thích lý do chọn 10 s. (GT-04, LG-10) |

## 3. Vấn đề cấu trúc mà nhiều reviewer cùng nêu

Mọi đề xuất dưới đây nằm trong khung GVHD đã chốt. Chương 3–4 chỉ trình bày ý tưởng. Nút giao, số liệu và kết quả chỉ có ở Chương 5, tóm tắt và kết luận.

### 3.1 Chương 5 dài 68/101 trang thân bài và viết như nhật ký theo ngày

(HD-04, HD-05, ND-04, VP-01, HB-12, HV-03, HV-15). Mục 5.12 có 20 tiểu mục, tiêu đề mang ngày ("Thay đổi ngày 04/11 và kết quả tham chiếu trên mạng 04/11"), và trải trên sáu phiên bản mạng. Kết quả trên các mạng đã bỏ đứng ngang hàng với kết quả trên mạng cuối. Riêng `5:1047–1049` còn để nguyên một kết luận rồi tự bác ở đoạn sau. Các reviewer thống nhất sắp lại 5.12 theo câu hỏi, không theo ngày:
- (A) các thí nghiệm khả thi đã quyết định thiết kế, rút gọn;
- (B) B0 và B1 trên mạng cuối;
- (C) ba chiến dịch B2, P1, P2 và phân tích nguyên nhân;
- các mạng cũ chuyển sang phụ lục "Quá trình xây dựng kịch bản", ở thân bài chỉ giữ Bảng 5.18 kèm một đoạn.

Phần cắt và chuyển cũng được thống nhất. Cắt: Mục 5.3, Bảng 5.14 (hạng mục), Bảng 5.15 (số dòng mã). Chuyển sang Phụ lục C: Bảng 5.9, Bảng 5.13 (thư viện), Mục 5.9, Mục 5.14. Mục 5.13 (bảy giải pháp) giữ trong Chương 5 nhưng rút xuống mỗi giải pháp 2–3 câu, trỏ tới bằng chứng, và ghi rõ phần nào SUMO có sẵn (HD-09, HV-05). HV cho rằng mục tiêu 30 trang của HD không kịp hạn và đề xuất khoảng 45 trang. Có một điều kiện LG đặt ra: các giới hạn đang nằm trong những mục bị chuyển đi (ngưỡng va chạm không tính lại, mục tiêu M9 (chặn làn rẽ phải) suy từ mạng có cọc) phải được giữ lại ở mục Hạn chế. Đoạn tự bác ở `5:1047–1049` thì xóa. Sau 5.12 nên có một đoạn tóm tắt kết quả 4–5 câu (HD bỏ sót 3).

### 3.2 Không có câu hỏi nghiên cứu

(HD-03, HV-04). Hiện luận văn có năm mục tiêu, bốn đóng góp, bảy giải pháp và hai thí nghiệm E1, E2, nhưng không có gì nối chúng với nhau. Đề xuất: thêm 2–3 câu hỏi ở 1.4, và một bảng đi từ đóng góp sang câu hỏi rồi sang bằng chứng. Chương 6 trả lời lần lượt từng câu hỏi. Câu hỏi thứ nhất không được dùng chữ "an toàn" (GT), ví dụ: "Bộ thực thi có tạo ra hành vi vi phạm mà B0 không có, mà không làm tăng va chạm mô phỏng và số xe kẹt so với B0 không?" Theo LG, câu trả lời hiện tại cho vế sau là "chưa", vì B1 bị loại ở 15/15 lần chạy. Mỗi đóng góp cũng nên ghi mức kiểm chứng hiện có (HD bỏ sót 5). Ở Chương 6, gọi bảy giải pháp là "giải pháp kỹ thuật", không gọi là "đóng góp".

### 3.3 Thiết kế so sánh được dùng trước khi định nghĩa

(HD bỏ sót 1, HV bỏ sót 5, ND vòng 2). B0–H và E1/E2 được nhắc từ tr. 10, nhưng tới Mục 5.7 (tr. 45) mới được định nghĩa, còn Bảng 5.12 thì trôi tới tr. 96. Phần này không gắn với nút giao cụ thể, nên phần ý tưởng của nó (sáu phương án, E1/E2, kiểm định Mann–Whitney) có thể chuyển thành mục cuối Chương 4. Chương 5 chỉ giữ cấu hình cụ thể. Cách này hợp khung GVHD và rút ngắn Chương 5.

### 3.4 Tóm tắt

(HD-07, ND-07, VP-04, HB-19, HV-02). Tóm tắt dài khoảng 500 từ, trong khi mẫu quy định 200–350, và tràn sang trang thứ hai. Phần kết quả kể theo ngày ("Trên mạng ngày 27/10..."), mở bằng kết quả âm, dùng thuật ngữ nội bộ ("đủ điều kiện", "mô hình nền", "phân tích loại bỏ"), và còn TODO. Câu "SUMO mặc định đủ điều kiện ở 15/15 lần chạy, còn bộ luật thủ công thì chưa" sẽ được đọc là phương pháp thua mô hình chuẩn. Đề xuất: viết lại thành một trang, theo đóng góp, bỏ ngày, áp các câu đã sửa ở Mục 2. Bản tiếng Anh có "base model" dễ bị đọc là mô hình LLM gốc, "in swarms", "in queues" nghe như dịch máy, và tiêu đề "Results so far" mang giọng báo cáo tiến độ.

### 3.5 Chương 6

(HD-02, HD-11, LG-08, VP-01, HV-11). Câu kết luận chính vẫn là TODO (`6:45`, tr. 100). Chương không có mục Hạn chế. Các tiểu mục chia theo kiểu báo cáo tiến độ ("Đã hoàn thành", "Chưa thực hiện", "Việc trước mắt"). Mục 6.1.4 mở đầu bằng kết quả trên các mạng đã bỏ. Đề xuất đổi các tiểu mục thành "Kết quả đạt được", "Hạn chế", "Hướng phát triển". Mục 6.1 hiện tên là "Kết luận", trùng tên chương (VP bỏ sót 2). Danh sách hạn chế mà các reviewer thống nhất:
- dữ liệu là dữ liệu thay thế, và phần mục tiêu giả định chiếm hơn nửa S;
- G0 (cổng GEH) tính trên số đếm 15 phút;
- ngưỡng va chạm tính trên mạng F2 và chưa tính lại cho các mạng sau;
- mục tiêu M9 (chặn làn rẽ phải) suy từ mạng có cọc;
- chỉ mô phỏng 07:30–08:00, một nút, chưa có thấp điểm;
- mỗi ngày chỉ một seed, trong khi teleport kẹt của B1 dao động 0–63 tùy seed, nên việc chọn đặc tả có thể bị nhiễu seed chi phối;
- quy tắc chọn dự phòng không xét xe chờ chèn;
- chỉ một LLM 9B, nhiệt độ 0,7, mỗi chiến dịch chạy một lần;
- hàm khoảng cách với tỷ lệ nhỏ (thay cho dòng "[Câu hỏi cho GVHD]" ở `4:103`);
- hành vi 9 (chấp nhận khoảng trống nhỏ) và 11 (đi chậm giữa làn) chưa có chỉ số;
- kiểm tra `coverage` chỉ áp cho P2, P1 mất 9/36 lần chạy cho đặc tả trùng, nên "khung so sánh công bằng" chưa cân;
- tầng quỹ đạo được hứa ở `1:22` nhưng chưa có trong lược đồ;
- ngân sách 36 lần chạy chưa được giải thích.

### 3.6 Bảng trôi về cuối chương

(HD-06, ND-02, HB-02, HV-09). Mười ba bảng bị dồn về tr. 89–97, sau cả đoạn kết Chương 5. Bảng 5.17 được bàn ở tr. 53 nhưng in ở tr. 96. Bảng 5.1 được nhắc ở tr. 31 nhưng in ở tr. 89. Danh mục bảng vì thế lộn thứ tự. Nguyên nhân là các bảng `[ht]` nằm xen với bảng `[H]`. Cách sửa được đa số chọn: `[!htbp]`, `\usepackage[section]{placeins}`, `\raggedbottom`, và chỉ dùng `[H]` cho bảng ngắn. Bảng 5.17 nên đặt cạnh Hình 5.3. Không nên ép mọi bảng về `[H]`, vì bản build hiện tại đã cho thấy cách đó tạo trang nửa trắng (tr. 49, tr. 51). Bảng 2.2 cũng đang đứng một mình trên tr. 11.

### 3.7 Ghi chú nội bộ in ra bản PDF

(HD-15, ND-12, VP-02, HB-03, HV-08):
- "[Câu hỏi cho GVHD: ...]" ở `4:103` (tr. 29);
- `[TODO_CITE]` ở `3:57` (tr. 15);
- TODO ở hai bản tóm tắt, `5:400`, `5:710`, `5:1341`, `5:1418` và `6:45`;
- "Phase 3A–3D" (chỉ cần bỏ chữ "Phase");
- "(bổ sung so với kế hoạch)" và "khác kế hoạch ban đầu" ở Phụ lục B;
- "Giờ Hà Nội ngày 08/11/2026" trong caption Bảng 5.32.

Đề xuất: dùng một macro `\todo` tắt được khi build bản nộp.

### 3.8 Mã nội bộ và thuật ngữ chưa định nghĩa

(HD-16, ND-03, ND-05, ND-06, ND-10, ND-11, VP-03, VP-06, HB-15, HV-10):
- "F2" vừa là nhóm hành vi vừa là tên mạng.
- Tên mạng theo ngày được dùng từ tóm tắt, nhưng tới Bảng 5.18 (tr. 55) mới được định nghĩa.
- Mã chiến dịch (`REF_n1104s5`, `it01_s02`) được dùng như thuật ngữ.
- Danh mục viết tắt chỉ có 6 mục.
- "Xe chờ chèn", "chiến dịch", "khóa" chưa có định nghĩa. "Teleport" được dùng trước khi định nghĩa.
- Không có phần khái niệm nền (bám xe, Krauss và IDM, headway, lưu lượng bão hòa, pha, chu kỳ), nên người đọc không hiểu vì sao chép `a` của IDM sang `accel` của Krauss lại thành vấn đề.
- B0 có sáu tên gọi khác nhau. B1 có ba.
- "Mã xác định" dễ đọc thành mã nhận dạng, nên đổi thành "mã tất định". Chữ này cũng có trong Hình 1.1.
- "Seed" dùng cho ba thứ: LLM, Optuna và mô phỏng (ND vòng 2).
- $p$ có bốn nghĩa, $\sigma$ trùng với `sigma` của SUMO (VP bỏ sót 1).
- "Phương án" vừa chỉ phương án thiết kế nút, vừa chỉ B0–H (VP bỏ sót 3).

Đề xuất: thêm khoảng một trang khái niệm nền ở Mục 2.2, và một bảng tra mã và ký hiệu sau danh mục viết tắt. Mỗi mã chỉ số trong bảng kèm nghĩa, ví dụ M8 (đi sai làn), M9 (chặn làn rẽ phải), M10 (đi trên vỉa hè). Định nghĩa trong Chương 4 phải viết chung, không có tên nhánh và không có thuật ngữ SUMO. Teleport thì định nghĩa ở Chương 5.

### 3.9 Người đọc không dựng lại được nút giao

(GT-03, GT-07, ND-14, ND-15, HB-05). Luận văn không có sơ đồ phân làn và sơ đồ pha. Hình 5.1 dùng mã cạnh OSM làm nhãn, chữ khoảng 5 pt. Hình 5.1 và Hình 5.2 lệch hướng nhau 45° mà không ghi chú. Quy ước "lane 0" chỉ có trong Bảng 5.1, mà bảng này lại trôi xa. Đề xuất (HB vòng 2): thay Hình 5.1 bằng một hình hai phần. Phần (a) là mặt bằng phân làn có kim chỉ Bắc, tên đường, chỉ số làn và đoạn 30 m. Phần (b) là sơ đồ ba pha kèm thanh thời gian. Rút văn xuôi ở 5.1.3 tương ứng, như vậy số trang gần như không đổi. Hình này dùng lại được cho slide.

### 3.10 Chỉ số thiếu định nghĩa vận hành

(GT-04, GT-10, GT-11, GT-12, GT-13, HB-16, LG-16):
- M2 (xuất phát sớm) và M3 (vượt đèn đỏ) chồng lấn nhau (xem Mục 2).
- M6 (thời gian qua nút) đo bằng giây, nhưng mục tiêu cho bằng km/h, lấy từ tốc độ giữa tuyến.
- M1 (xả hàng), M4 (vị trí dừng), M5 (hàng chờ) chưa nói đo ở đâu và theo ngưỡng nào.
- M8 (đi sai làn) cần gắn với điểm bắt đầu vạch liền.
- Cả luận văn chỉ có một phương trình được đánh số.
- R, $S_{\text{sourced}}$ và $S_{\text{assumed}}$ được định nghĩa, nhưng không bảng chiến dịch nào báo cáo.

Đề xuất: định nghĩa chung bằng ký hiệu ở Bảng 4.1, và thêm phương trình đánh số cho $d$, $R$, $S$ ở 4.7.2. Giá trị cụ thể của nút (30 m, 80 m, 5 km/h) đặt ở Chương 5. Thêm một đoạn nối M1 (xả hàng), M5 (hàng chờ), M6 (thời gian qua nút) với các chỉ số quen thuộc của ngành: lưu lượng bão hòa, hàng chờ, độ trễ.

### 3.11 Chương 2 mỏng và phần LLM ít

(HD-12, HD-13, HV-14, HV-18, GT-18). Chương 2 dài 5 trang với 23 tài liệu, và không nêu cách tìm tài liệu. Chưa có bảng so sánh với các công trình gần nhất. OPRO, FunSearch và Eureka hiện chỉ có ở 3.6.1. Krauss, IDM, MOBIL không có trích dẫn gốc. Chưa có tài liệu hướng dẫn hiệu chỉnh mô phỏng vi mô hay mô hình xe máy trong dòng hỗn hợp. Lý do chọn một LLM 9B chạy cục bộ chỉ được nói qua chuyện phần cứng. Kết quả về LLM, trọng tâm của đề tài, chỉ chiếm khoảng 4 trang và nằm rải rác. Đề xuất: gom lại thành một mục "Hành vi của LLM cục bộ", đưa một đặc tả P2 qwen có trường lý do vào phụ lục, và thêm một listing JSON ngắn. Listing này trả lời nhanh câu hỏi "LLM trả về cái gì".

### 3.12 Lỗi nhỏ, sửa nhanh
- Tham chiếu chéo trỏ sai: `section:3.3` in ra "Mục 3.5", `section:3.8` in ra "Mục 5.7", Bảng 2.2 in ra "Mục 1.4" (LG-11).
- Mục lục ghi Tài liệu tham khảo ở tr. 104, thực tế bắt đầu ở tr. 102 (HD-17). Sửa bằng `heading=bibintoc`.
- Hai mục "a, Tham số tĩnh" và "b, Luật có điều kiện" treo ngay dưới 5.2, nên đổi thành `\subsection` (VP-09, HB-13).
- Chương 4 nói lược đồ có mười bảng, Phụ lục B chỉ có bảy (VP-17, HV-17).
- Tham số xuất phát sớm mang hai tên, $t_{\text{before}}$ và $t_{\text{before\_green}}$. Gói `times` không đổi font toán (HB-16).
- 36 dòng tràn lề trên 2 pt, chủ yếu do `\texttt` không ngắt dòng được (HB-07).
- Hình 5.4, 5.5 có nhãn tiếng Anh, dùng dấu chấm thập phân, và không đọc được khi in đen trắng (HB-04).
- Màu đỏ của `\tamthoi` mất khi in đen trắng, nên thêm một dấu không phụ thuộc màu (HB-06).
- S ghi tới 4 chữ số và làm tròn khác nhau giữa các bảng (HB-11, LG-17, HV-19).
- Caption phụ lục đặt dưới bảng, còn thân bài đặt trên (HB-10).
- Tài liệu tham khảo có URL giãn khoảng trắng và tên tác giả Việt không thống nhất (HB-18).
- `twoside` làm lề đóng gáy đổi bên, và các chương mở ở trang chẵn. Hỏi quy định in của trường rồi chọn bỏ `twoside` hoặc dùng `\cleardoublepage` (HB bỏ sót 1).
- Bảng 3.2 và Bảng 5.4 trùng nội dung. Bốn bảng "trạng thái" (5.5, 5.6, 5.7, 5.14) chồng nhau, nên giữ một bảng và đổi nó thành bảng phủ hành vi theo HV-07 (HB bỏ sót 2, 3).
- Đoạn kết Chương 2 và đoạn mở Chương 3 gần trùng câu chữ. Nên giữ một câu nối 2–3 câu, bỏ phần liệt kê lại các mục (VP-08; HD phản đối việc bỏ hẳn).
- "Thay vì" xuất hiện 25 lần. Ý "truy nguyên thay vì nới ngưỡng" lặp ba lần (VP-10).
- Thuật ngữ giao thông (GT-20): "năng lực thông qua" nên là "khả năng thông hành", "pha đỏ" nên là "thời gian đỏ", "headway" nên là "giãn cách thời gian". `tau` là giãn cách thời gian mong muốn, không phải thời gian phản ứng (GT-21).
- Tiêu đề cột trộn tiếng Anh: Min, Max, p90, Lane 0 (VP bỏ sót 5).

## 4. Các điểm reviewer bất đồng

| Vấn đề | Các lựa chọn | Đa số sau vòng 2 |
|---|---|---|
| Tên thay cho "dữ liệu đại diện" | "dữ liệu thay thế (dựng từ tài liệu)": VP, GT, HD, HV. "dữ liệu tổng hợp từ tài liệu": LG, HB, ND. | **Dữ liệu thay thế.** Lý do quyết định do VP đưa ra: luận văn đã dùng "tổng hợp" cho dữ liệu SYNTHETIC tùy ý (`5:321`, `5:745`), và `5:1348` dùng chính cụm "số liệu tổng hợp tùy ý" để phân biệt với các ngày PROXY. Định nghĩa một lần ở 1.4.2. |
| Đánh số làn | "làn 0/1/2" định nghĩa một lần: VP, ND, LG, HB, HD, HV. "làn 1/2/3 từ lề phải" hoặc tên chức năng: GT. | **Làn 0/1/2.** Lần đầu ghi kèm tên chức năng, ví dụ "làn 0 (làn sát lề phải, rẽ phải liên tục ở 30 m cuối)", và vẽ chỉ số lên sơ đồ ở 3.9. Đánh số lại khoảng 44 chỗ thì dễ lệch một đơn vị. |
| Tên phiên bản mạng | V1–V6, v1–v6, N1–N6 | **N1–N6** (cả bảy người đồng ý sau vòng 2), vì chữ "v" đã dùng cho prompt `v001`–`v005`. Đồng thời bỏ mã F1–F3 của nhóm hành vi. |
| "Đủ điều kiện" | đổi thành "đạt tiêu chí chấp nhận (ổn định và va chạm mô phỏng)": LG, VP, HD, ND. Giữ nguyên và thêm mệnh đề giải thích: HV. | **Đổi tên.** Không dùng "bộ lọc an toàn", vì va chạm của SUMO là chồng lấn hình học, không phải chỉ số an toàn. Không dùng "chạy hợp lệ", vì "hợp lệ" đã dùng cho đặc tả. |
| "Ngày đánh giá" hay "ngày kiểm định" | kiểm định: GT, ND, HB. Giữ "đánh giá": HV. | Chia đôi. Nếu đổi thì phải đổi đồng bộ cả cụm "đánh giá cuối E1, E2". Không đủ thời gian thì giữ, và định nghĩa nó tương đương bước kiểm định (validation). |
| "Xe chờ chèn" | "xe chờ vào mạng": VP. Giữ: ND vòng 1. | **Xe chờ vào mạng**, định nghĩa theo GT: "xe đã đến giờ xuất phát nhưng chưa vào được mạng vì nhánh vào đã kín; phần nhu cầu chưa được phục vụ". |
| Số chữ số của S | 2 chữ số: LG, HV, HB. 3 trong bảng và 2 trong văn xuôi: VP. | Chọn một quy tắc duy nhất, kèm độ lệch chuẩn của B0 trên 15 lần chạy làm thước đo nhiễu. |
| Bảng v/c theo nhánh và pha | thêm: GT. Ngắn hoặc để phụ lục: HB. Phản đối vì thêm giả định: HV. | Rẻ nhất là một câu: B0 không còn xe chờ chèn ở cùng mức nhu cầu (15/15 lần chạy). |
| Chuyển 54 bảng sang `booktabs` | HB đề xuất. HV, HD phản đối vì sát hạn. | Chỉ làm phần rẻ: cột `>{\raggedright\arraybackslash}p{}`, cấm ngắt gạch nối trong `\texttt`, nới cột vClass của Bảng A.3. |

## 5. Đề xuất đã bị bác ở vòng 2

Các đề xuất dưới đây có trong file `r1_*`. Vòng 2 đã chỉ ra chúng sai hoặc trái khung GVHD, nên đừng làm theo.
- Tự thay tên trên bìa bằng một tên gợi ý (HD-01, ND-01).
- Viết `accel` là lỗi "chặn mọi chiến dịch" (HD-11) hoặc "làm hỏng năng lực thông qua" (HV-13).
- Đưa "xe chờ giữa nút" lên tóm tắt như một kết quả dương (HD-07, HV-02).
- Câu kết luận mẫu "mọi lỗi đều là lỗi cấu trúc, LLM hạ điểm bằng cách bỏ luật" (HD-02).
- Đặt ví dụ chạy xuyên suốt có HDT_S, `moto_violator`, hoặc ví dụ "khóa" có tên nhánh LVL vào Chương 4 (ND-06, ND-13). Nếu có ví dụ thì đặt ở đầu Mục 5.2, dùng một đặc tả có `illegal_left_box` (B1 không có luật này).
- Đưa bảng bảy giải pháp lên Mục 1.5 (HV-16), vì bảng gắn với SUMO.
- Dùng `[H]` cho mọi bảng (ND-02).
- Dùng σ làm ký hiệu cấu trúc đặc tả (HV-06), vì σ đã có hai nghĩa. Dùng $\mathcal{C}$ cho cấu trúc. Phát biểu bài toán đặt ở Mục 3.1, không đặt ở Chương 1.
- Đổi "Phase 3A–3D" thành "KT1–KT4" (HD-16), hoặc gọi đó là thí nghiệm của nhóm tìm khoảng trống (HV-08). Thí nghiệm 3D là về xe chờ giữa nút. Chỉ cần bỏ chữ "Phase".
- Câu viết lại của VP-12 ở `3:47` nói bốn nghiên cứu "đo" vượt đèn đỏ. Thực ra Saval và cs. chỉ giả định trong mô hình, còn Gao và cs. đo trên xe đạp điện.
- Rút Chương 5 xuống còn 30 trang (không kịp hạn). Mục tiêu khoảng 45 trang.

## 6. Phản biện theo từng góc nhìn

### Hội đồng chấm

File: `r1_hoidong.md`, `r2_hoidong.md`.

Bài toán và ý tưởng tách sinh luật khỏi thực thi luật được trình bày rõ. Phần còn lại trông như báo cáo dự án hơn là luận văn nghiên cứu, vì ba lý do: luận văn không có câu hỏi nghiên cứu, Chương 5 chiếm 68% thân bài, và câu kết luận chính để trống. Ba điểm nặng nhất theo người này: B0 không phải "SUMO mặc định" như Chương 1 dùng để nêu khoảng trống (LG-03); tr. 31 mâu thuẫn với Bảng 5.1 về rẽ trái từ làn 0 (GT-02); thiếu lý do chọn LLM 9B (HV-18). Người này còn đề xuất ghi số mục lên từng ô của Hình 1.1, để hình làm luôn bản đồ đọc cho Chương 3–4.

### Người đọc ngoài chuyên ngành

File: `r1_nguoidoc.md`, `r2_nguoidoc.md`.

Người đọc theo kịp Chương 1–4 nhờ Hình 1.1 và các đoạn "biến đệm, hậu quả nếu thiếu". Sang Chương 5 thì vấp liên tục: tên mạng theo ngày, mã F2, mã chiến dịch, bit của speed mode, và các khái niệm chưa định nghĩa như xe chờ chèn, teleport, khóa. Kết luận chính về `accel` không hiểu được nếu chưa biết mô hình bám xe. Người này đề xuất thêm một trang khái niệm nền, một bảng tra mã, và một hình cho quan hệ nguyên mẫu, phân phối, lớp vi phạm. Hình này giúp hiểu hai lỗi chính của `qwen3.5:9b`.

### Biên tập văn phong

File: `r1_vanphong.md`, `r2_vanphong.md`.

Chương 1–4 viết gọn, gần như không có từ sáo, ngoặc kép thống nhất. Tóm tắt, Chương 5 và Chương 6 viết bằng giọng nhật ký thí nghiệm, với khoảng 100 mốc ngày và 91 nhãn in đậm đầu đoạn ở Chương 5. Ngoài ra còn tiếng Anh chen vào câu ("lane 0" 44 lần, "thinking", "Request"), một khái niệm mang nhiều tên, và điệp khúc "thay vì", "không phải X mà là Y". Ở vòng 2, người này soi các câu viết lại của người khác và bắt được bốn câu khẳng định quá số liệu.

### Hình thức trình bày

File: `r1_hinhbang.md`, `r2_hinhbang.md`.

Ba lỗi lộ ngay khi in: bảng trôi, ghi chú nháp, và vấn đề tên trên bìa. Luận văn có 7 hình trên 110 trang, và các hình matplotlib để nhãn tiếng Anh, chữ nhỏ, không đọc được khi in đen trắng. Bảng kẻ lưới với cột canh đều hai bên. Người này nêu thêm lỗi `twoside`, hai bảng luật trùng nhau, bốn bảng trạng thái chồng nhau, và việc Bảng 5.17 tách khỏi Hình 5.3.

### Lập luận và nhất quán

File: `r1_logic.md`, `r2_logic.md`.

Các con số lặp lại giữa các chương nhìn chung khớp nhau: 403 ca kiểm thử, 36 lần chạy, 15/15. Chỗ yếu nằm ở ba kết luận nhân quả mà tóm tắt nhắc lại nhưng số liệu không đỡ được (Mục 2). Thêm vào đó là định nghĩa B0, ngưỡng va chạm suy từ chính B0 trên một mạng khác, và các giới hạn nằm rải rác. Đây là góc nhìn có ảnh hưởng lớn nhất ở vòng 2: sáu reviewer kia sửa lại câu đề xuất của mình theo nó.

### Học viên cùng khóa

File: `r1_hocvien.md`, `r2_hocvien.md`.

Người này đọc Chương 3–4 một mạch, nhưng bắt đầu mất mạch ở khoảng tr. 52–62 và phải lật lại Bảng 5.18 bốn năm lần. Họ cũng đánh giá mỗi đề xuất có kịp hạn 12/2026 hay không. Những thứ nên giữ, đừng cắt khi sửa:
- khuôn "biến đệm cùng hậu quả nếu thiếu" ở Chương 3;
- Bảng 5.2 ánh xạ khái niệm sang SUMO;
- nhãn bằng chứng CG/GĐ và cách tách $S_{\text{sourced}}$/$S_{\text{assumed}}$;
- khuôn Câu hỏi/Thiết lập/Quan sát/Diễn giải cho từng thí nghiệm;
- Hình 1.1;
- ranh giới Chương 3–4 hiện tại.

Câu hỏi bảo vệ nên chuẩn bị (đã sửa sau vòng 2):
1. "SUMO mặc định đạt 15/15, bộ luật của em đạt 0/15. Phương pháp giúp được gì?"
2. "Không có số đo tại nút, vậy 'giống thực tế' đo bằng gì?"
3. "Phần nào là của em, phần nào SUMO hay Optuna có sẵn?"
4. "Vì sao dùng LLM 9B? Mô hình lớn hơn có đổi kết luận không?"
5. "B2 không bỏ luật mà S vẫn thấp hơn P2. Vậy vì sao em thêm ràng buộc v005?"
6. "Tên đề tài là trò chơi máy tính, nội dung là giao thông. Em giải thích thế nào?"
7. "B0 có 4 xe chờ giữa nút mỗi chu kỳ. Vậy luật rẽ trái chờ giữa nút đóng góp gì?"
8. "Bảng 5.17 dùng những lần chạy B1 không đủ điều kiện. Số đó còn tin được không?"

### Sinh viên Kỹ thuật giao thông

File: `r1_giaothong.md`, `r2_giaothong.md`.

Người trong ngành đọc luận văn sẽ không hình dung được nút giao, và sẽ hiểu sai bốn chỗ:
- "va chạm" (thực chất là chồng lấn hình học của SUMO);
- cổng GEH gắn với TAG;
- M7b (độ trễ giải phóng vùng chờ) bị gọi là PET;
- hành vi 6 gọi một hành vi đúng luật là vi phạm.

Thuật ngữ giao thông dịch lạ hoặc không thống nhất. Câu ở `1:65`, "nhường đường không đổi giữa các kịch bản", trái với chính hành vi 9 (chấp nhận khoảng trống nhỏ) và với tham số `jmTimegapMinor` đang được hiệu chỉnh. Ở vòng 2, người này tách mọi đề xuất định nghĩa thành hai tầng: định nghĩa chung đặt ở Chương 3–4, giá trị của nút đặt ở Chương 5.

## 7. Thứ tự sửa gợi ý

1. Ngay: các quyết định ở Mục 1. Riêng tên đề tài và Bảng 5.31 không phụ thuộc việc nào khác, làm được ngay.
2. Nhanh (mỗi việc dưới một buổi):
   - các câu ở Mục 2;
   - ghi chú nội bộ (3.7);
   - các lỗi nhỏ ở 3.12;
   - cách đặt float (3.6);
   - thống nhất tên gọi theo Mục 4;
   - định nghĩa xe chờ vào mạng, teleport, chiến dịch, khóa;
   - thêm "hành vi 9 và 11 chưa có chỉ số riêng" vào 4.7.1.
3. Trung bình:
   - tóm tắt (3.4) và Chương 6 (3.5);
   - câu hỏi nghiên cứu và bảng nối (3.2);
   - chuyển thiết kế so sánh sang Chương 4 (3.3);
   - sơ đồ phân làn và sơ đồ pha (3.9);
   - một trang khái niệm nền và bảng tra mã (3.8);
   - phương trình $d$, $R$, $S$ (3.10).
4. Lớn:
   - sắp lại Chương 5 theo câu hỏi và chuyển mạng cũ sang phụ lục (3.1);
   - mở rộng Chương 2 (3.11);
   - vẽ lại hình matplotlib bằng nhãn tiếng Việt.
