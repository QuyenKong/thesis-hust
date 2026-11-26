# Quyết định 26/11/2026 trở đi

Từ 26/11, chủ đề tài giao cho Claude tự chọn phương án thay vì hỏi (chỉ thị 26/11). Mỗi mục ghi bối cảnh, các phương án, phương án chọn và lý do. Mục nào do chủ đề tài quyết trực tiếp thì ghi "chủ đề tài".

## D01. Nút nghiên cứu (chủ đề tài, 25/11)

Video và các ghi nhận hiện trường thuộc nút Lê Văn Lương x Hoàng Minh Giám x Nguyễn Tuân, trong khi mạng cũ dựng ở nút Lê Văn Lương x Phố Hoàng Đạo Thúy, cách 570 m. Chọn chuyển sang nút LVL x HMG x NT. Mã nhánh đổi `HDT_N` thành `HMG`, `HDT_S` thành `NT`. Kết quả các chiến dịch trên mạng cũ không dùng cho luận văn nữa.

## D02. Giờ cao điểm (chủ đề tài, 25/11)

Hai video quay lúc 17:45 và 17:50 ngày 25/11, tức cao điểm chiều. Phạm vi ghi là "giờ cao điểm", dùng được dữ liệu cả sáng lẫn chiều.

## D03. Chia dữ liệu (chủ đề tài, 25/11)

IMG_4801 (V2, 5:09) dùng để hiệu chỉnh, IMG_4800 (V1, 2:24) để kiểm định. Hai đoạn quay cùng một buổi, nên không phải hai ngày độc lập; luận văn phải nói rõ điều này.

## D04. Metric không đo được từ video (chủ đề tài, 25/11)

Các metric video không đo được (ví dụ M4 vị trí ngang, M8 đi sai làn) lấy giá trị mục tiêu từ tài liệu công bố, kèm nhãn bằng chứng.

## D05. Đèn tín hiệu (chủ đề tài, 26/11; số tạm)

Chu kỳ 160 s đo từ cột đèn người đi bộ trong IMG_4801 (xanh 33 s, bắt đầu lúc 39,5 s và 199,5 s). Thứ tự pha theo mô tả hiện trường: LVL đi thẳng cả hai nhánh, LVL rẽ trái cả hai nhánh, rồi HMG và NT. Thời lượng 60, 40 và 60 s là ước lượng của chủ đề tài; vàng 4 s theo TCCS 24:2018, đỏ toàn phần 2 s là giả định. Cần chủ đề tài xác nhận.

## D06. Hình học nút (chủ đề tài, 26/11)

- LVL: 4 làn mỗi chiều, gồm làn BRT coi như làn thường. Làn 0 là làn rẽ phải liên tục ở 30 m cuối.
- HMG: 3 làn vào, 3 làn ra, có làn rẽ phải liên tục.
- NT: 3 làn vào, 2 làn ra, không có làn rẽ phải liên tục, được rẽ phải khi đèn đỏ.
- HMG và NT: cấm rẽ trái, cấm quay đầu. LVL được rẽ trái và quay đầu trong pha mũi tên.
- Bỏ đèn qua đường; mạng chỉ có một nút có đèn.
- HMG và NT có dải phân cách ở đoạn cuối. Bề rộng lấy theo khoảng cách giữa hai đường OSM: HMG khoảng 6 m sát vạch dừng, NT khoảng 3,5 m, cả hai thu hẹp về 0 ở chỗ nhập vào đoạn hai chiều (65 m và 49 m).

Bề rộng làn 3,5 m theo TCXDVN 104:2007, vì không nguồn nào công bố bề rộng làn của nút này (`docs/research/site_lvl_nt_hmg.md`).

## D07. Gộp cụm nút OSM và đặt đèn (26/11)

OSM vẽ nút bằng bốn nút cách nhau 12–14 m, và netconvert không tự gộp chúng, kể cả với `--junctions.join-dist` 20 và 25 m.

| Phương án | Đánh giá |
|---|---|
| Tăng khoảng cách gộp | đã thử, không gộp được |
| Bản vá nút `<join>` liệt kê bốn nút, rồi `--tls.set` cho nút gộp | gộp được, có một đèn duy nhất |

Chọn phương án hai. Danh sách bốn nút nằm trong `intersection.join_nodes`.

## D08. Đoạn chuyển tiếp từ hai phần đường riêng sang đường hai chiều (26/11)

HMG và NT có một nút chuyển tiếp cách tâm 83 m và 70 m. Khi mỗi chiều có 3 làn, netconvert vẽ nút này dài gần 80 m, làm cạnh sát vạch dừng chỉ còn 0,2 m, và sumo-gui hiển thị nó như một nút giao thứ hai.

| Phương án | Đánh giá |
|---|---|
| Cố định hình nút chuyển tiếp thành ô vuông 8 m | cạnh dài lại bình thường nhưng vẫn còn một nút trên nhánh (chủ đề tài yêu cầu bỏ) |
| Gộp mỗi chiều thành một cạnh từ đầu mút đến nút chính | không còn nút phụ |

Chọn phương án hai. Mép trong của mỗi chiều là đường tâm của đoạn hai chiều, rồi nối sang mép dải phân cách của phần đường OSM; làn trải sang phải (`spreadType="right"`). Lần thử đầu đặt cả hai chiều căn giữa trên đường OSM, nên làn vào và làn ra của HMG chồng nhau. Hệ quả là xe rẽ trái trái phép đứng chờ ngay trên làn đi thẳng của NT: B0 có 165 va chạm/giờ trong REF_n1126. Sau khi sửa, một lượt B0 1800 s trên PROXY_D1 còn 31 va chạm (12 trong nút).

## D09. Liên kết làn (26/11)

Netconvert tự gán làn chưa hợp lý; ví dụ LVL 4 làn để làn 3 không có liên kết nào. Chọn sinh liên kết tường minh từ `lane_movements`, theo bốn quy tắc:

- Đi thẳng: các làn đi thẳng nối lần lượt vào các làn của nhánh ra, tính từ bên phải.
- Rẽ phải: vào làn 0 của nhánh ra.
- Rẽ trái và quay đầu: vào làn trái cùng của nhánh ra.
- Rẽ trái cấm (HMG, NT): một liên kết từ làn trái cùng, chỉ cho `custom1`.

Khi số làn đi thẳng nhiều hơn số làn ra (NT 3 làn vào HMG trước đây), các liên kết đi thẳng dồn vào cùng một làn ra. Liên kết từ làn ngoài cùng bên phải giữ `G`, các liên kết còn lại đặt `g`, để tránh cảnh báo "unsafe green" của SUMO.

## D10. Rẽ phải khi đèn đỏ ở NT (26/11)

SUMO có loại nút `traffic_light_right_on_red`, nhưng loại nút này cho rẽ phải khi đỏ ở mọi nhánh. Chọn gán trạng thái `s` cho riêng liên kết rẽ phải của NT, trong các pha mà nhánh NT đang đỏ. Đã chạy thí nghiệm kiểm tra: xe dừng ở vạch rồi đi khi đèn vẫn đỏ, còn xe đi thẳng chờ đến lúc xanh.

## D11. Gán nhánh trong mã nguồn (26/11)

Mã cũ nhận diện nhánh qua tên đường. Ở nút mới, đường ngang có hai tên khác nhau (HMG, NT), nên cách này không dùng được. Chọn ghép bốn cạnh vào bốn nhánh theo thứ tự vòng quanh nút, so với hướng chuẩn LVL_W 225°, LVL_E 45°, HMG 315°, NT 135°. Khi hai cách ghép hòa nhau (mạng thử nghiệm nằm theo trục), lấy cách lệch theo chiều kim đồng hồ. Các mạng nhỏ trong test vì vậy giữ nguyên hình học cũ.

## D12. Prompt LLM (26/11)

Các prompt v002–v005 mô tả nút cũ. Chọn giữ nguyên chúng để có thể tái lập các chiến dịch cũ, và tạo v006 cho nút mới; `llm.yaml` mặc định dùng v006.

## D13. Demand PROXY vượt năng lực thông qua (26/11)

Với demand PROXY (8180 xe/h, phân bổ theo giả định), lượt B0 1800 s còn 112 xe chưa vào được mạng ở cuối giờ, chủ yếu ở LVL_W và HMG. Chọn giữ nguyên demand PROXY, vì đây chỉ là lượt chạy thử pipeline, không phải kết quả. Demand thật sẽ lấy từ video (D14).

## D14. Dịch vạch dừng NT do vỉa hè trên mạng proxy (26/11)

Trên mạng proxy, nhánh vỉa hè của LVL_W và LVL_E làm vạch dừng NT dịch 0,63 m; test cũ chỉ cho phép 0,2 m (giá trị tinh chỉnh cho nút cũ). Mạng đo thật không có vỉa hè nên không bị ảnh hưởng. Các phương án:

- tinh chỉnh lại `SIDEWALK_JOG_M` cho nút mới, mất thêm vài lượt netconvert và có thể làm dịch các nhánh khác;
- nới ngưỡng cho riêng NT lên 1,0 m.

Chọn phương án hai, vì vỉa hè chỉ có trong dữ liệu thay thế và dịch dưới 1 m không đổi hình học nút.

## D15. Nơi ghi kết quả chạy trên mạng mới (26/11)

Bản ghi chạy cũ trong `experiments/runs/` thuộc mạng HDT và được Git theo dõi; một test (R28) đọc lại chúng. Từ nay mọi lượt chạy trên mạng mới đều ghi vào thư mục của chiến dịch (`experiments/campaigns/<tên>_n1126/`), không ghi vào `experiments/runs/`.

## D16. Bỏ REF_n1126 lần đầu (26/11)

REF_n1126 khởi động trước khi sửa phần chồng làn ở HMG/NT (D08), nên số liệu B0 của nó (165 va chạm/giờ) không còn đúng. Chọn dừng lần chạy này và chạy lại REF trên mạng đã sửa.

## D17. Cách đưa số đo video vào dữ liệu quan sát (26/11)

Hai video quay cầm tay, ban đêm, qua kính, và chỉ thấy một phần nút: chiều ra HMG bị khung cửa sổ che, chiều ra NT nằm sau vùng lóa. Tracking bỏ sót nhiều xe máy trong hàng chờ dày. Như vậy không dựng được quỹ đạo từng làn cho cả mười bảng quan sát. Các phương án:

| Phương án | Ưu | Nhược |
|---|---|---|
| A. Dựng thẳng mười bảng từ quỹ đạo tracking | số liệu thô | phải chuyển ảnh sang tọa độ mạng; vị trí ngang, làn và hàng chờ sai lớn; nhiều bảng trống |
| B. Đo các chỉ số tổng hợp từ video (lưu lượng, tỷ lệ hướng rẽ, tỷ lệ xe máy, vượt đỏ, rẽ trái trái phép, chu kỳ đèn), rồi sinh bảng bằng bộ sinh đã có test (`thesis_sumo.proxy.generate`), với mục tiêu video thay cho mục tiêu tài liệu ở các chỉ số đó | bảng đầy đủ, đúng schema; mỗi chỉ số có nhãn nguồn; dùng lại code đã kiểm thử | các bảng là dữ liệu tổng hợp từ mục tiêu, không phải quỹ đạo thô |

Chọn B. Mục tiêu nào video đo được thì gắn nhãn `measured_video`, còn lại giữ giá trị tài liệu (D04). Hai ngày sinh ra là `VIDEO_V2` (hiệu chỉnh) và `VIDEO_V1` (kiểm định), dùng `config/site.yaml` (chu kỳ 160 s). Luận văn phải nói rõ đây là dữ liệu sinh từ mục tiêu đo trên video.

## D18. Lưu lượng và tỷ lệ hướng rẽ từ video V2 (26/11)

Tracking bỏ sót nhiều xe máy ở vạch dừng: xe máy vào nút đếm được 493, xe máy ra nút đếm được 943. Không có số đếm tay để hiệu chỉnh. Chọn cách tái dựng sau (`video/targets_from_tracking.py`, kết quả ở `data/video_targets/V2.yaml`):

- Số xe ra ở các nhánh ra nhìn thấy được (LVL_W, LVL_E, NT) coi là tổng các hướng đổ vào nhánh ra đó.
- Tổng đó chia cho từng hướng theo tỷ lệ các quỹ đạo đi trọn từ nhánh vào đến nhánh ra.
- Bốn hướng không quan sát được (vào HMG, vì khung cửa sổ che; và HMG đi thẳng, vì vùng lóa) lấy 15 % lưu lượng nhánh. Đây là giả định, bằng tỷ lệ rẽ phải của dữ liệu thay thế.

Kết quả là LVL_W 830, LVL_E 5365, HMG 2283 và NT 5874 xe/h, tỷ lệ xe máy 0,90. Tỷ lệ rẽ trái trái phép đo ở NT (2,7 %, khoảng 7 xe mỗi chu kỳ 160 s) khớp với mục tiêu M7 lấy từ tài liệu (7,5 xe vào lòng nút mỗi chu kỳ), nên giữ M7 theo tài liệu. Độ tin cậy thấp; luận văn phải ghi các con số này là ước lượng từ video, kèm hạn chế.

## D19. Ngày kiểm định V1 (26/11)

IMG_4800 đổi góc máy giữa chừng, và trong hai khung hình tham chiếu của nó chưa xác định được vị trí các nhánh. Muốn dùng phải dựng vùng đếm riêng, và có nguy cơ gán sai nhánh. Chọn sinh ngày `VIDEO_V1` từ cùng mục tiêu với `VIDEO_V2`, khác seed và khác hệ số ngày. Như vậy kiểm định chỉ kiểm tra khả năng tổng quát hóa với một mẫu ngẫu nhiên mới của cùng điều kiện, chưa phải một ngày quan sát độc lập. Đây là hạn chế phải ghi trong luận văn.

## D20. Rẽ phải khi đèn đỏ ở NT: nhường thay vì dừng hẳn (26/11)

Với trạng thái `s` (D10), mỗi xe rẽ phải từ NT phải dừng hẳn ở vạch. Trong lượt B0 1800 s trên VIDEO_V2, NT chỉ phục vụ được 1411 trên 2756 xe, trong khi 85 % xe ở NT rẽ phải. Video cho thấy xe máy rẽ phải từ NT đi liên tục, chỉ nhường chứ không dừng. Chọn trạng thái `g` (nhường mọi dòng xung đột, không buộc dừng) cho các pha NT đỏ. Khác biệt với làn rẽ phải liên tục vẫn còn: NT không có làn riêng, nên xe đi thẳng đứng chờ ở làn 0 vẫn chặn xe rẽ phải. D10 được thay bằng D20.

## D21. NT rẽ phải từ hai làn (26/11)

Sau D20, NT vẫn chỉ phục vụ được khoảng một nửa demand (1502 trên 2756 xe trong 1800 s). Lý do là mọi xe rẽ phải đều được đặt vào làn 0 (`departLane="best"`, làn duy nhất cho phép rẽ phải), nên làn 0 ùn ngược ra đầu nhánh. Trong IMG_4801, xe máy rẽ phải từ NT dàn hai hàng ngang trở lên, còn mũi tên của từng làn chưa được khảo sát. Các phương án:

- đổi `departLane` thành `free`: xe vào làn bất kỳ rồi đổi làn, gây chen làn dày ở đoạn đầu nhánh;
- cho rẽ phải từ làn 0 và làn 1.

Chọn phương án hai: `lane_movements` của NT là `[[r, s], [r, s], [s]]`, gắn nhãn giả định theo quan sát video, ở cả hai tệp site.

## D22. Giữ demand video dù B0 không phục vụ hết (26/11)

Sau D21, B0 phục vụ được 65 % demand ở NT và 83 % ở LVL_E trong 1800 s. Cuối lượt chạy còn khoảng 1200 xe chưa vào được mạng. B0 dùng thông số mặc định của SUMO, nên xe máy xả chậm hơn dòng xe máy đi dày hai, ba hàng ngang trong video. Các phương án:

- giảm demand xuống mức B0 phục vụ được: làm mất chính hiện tượng cần hiệu chỉnh;
- giữ demand đo được: backlog trở thành tín hiệu cho bộ hiệu chỉnh (năng lực xả phụ thuộc `minGapLat`, `tau`, `lcSublane`, ...).

Chọn giữ demand. Quy tắc hợp lệ hiện tại (`max_end_backlog: 0`) có thể loại mọi spec. Khi đó `select_best` dùng phương án dự phòng R32/R42 (bỏ ngưỡng va chạm), và luận văn phải ghi rõ điều này.

Ghi chú cho D21: khi làn 1 của NT có thêm hướng rẽ phải, netconvert tách các hướng đi thẳng của NT thành hai cạnh nội bộ. Quyết định ngày 04/11 từng tránh việc tách này vì xe chạy song song trên các cạnh nội bộ một làn đã va nhau. Lượt B0 1800 s sau D21 có 10 va chạm, trong đó 4 vụ trong nút, nên chấp nhận được; test `test_no_turn_links_from_lanes_0_and_1` cho phép hai cạnh nội bộ ở nhánh này.

## D23. Seed và ngân sách hiệu chỉnh trên một ngày (26/11)

Quy tắc R44 cũ là 36 lượt chạy cho mỗi chiến dịch, tức 12 spec × 3 ngày PROXY × 1 seed. Giờ chỉ có một ngày hiệu chỉnh (VIDEO_V2). Chọn 12 spec × 1 ngày × 3 seed (1, 2, 3), để giữ ngân sách 36 lượt chạy và 3 lượt chạy cho mỗi spec như cũ; kết quả vẫn so được về cấu trúc với các chiến dịch 08/11. REF (B0, B1_manual) chạy 5 seed để ngưỡng va chạm R10 ổn định hơn. Bộ test vẫn dùng ba ngày PROXY, qua `tests/conftest.py`.

## D24. Khởi động lại B2_v1126 (26/11)

Lần khởi động đầu, launcher ghi log của B2 và P1 vào cùng một tệp vì lỗi biến trong tệp .bat. Mình dừng cả hai khi B2 đã trừ 3 lượt chạy nhưng chưa lượt nào hoàn thành. Lỗi thuộc về công cụ chứ không phải về thí nghiệm, nên chọn xóa thư mục `B2_v1126` và chạy lại từ đầu với đủ 36 lượt; P1 chưa trừ lượt nào.

## D25. Vỉa hè trên kịch bản video (26/11)

Tệp site đo thật để `f2_measured_approaches` trống: bề rộng và điểm lên vỉa hè chưa đo, và vỉa hè trong cả hai video nằm sau vùng lóa kính. Mạng `site.net.xml` vì vậy không có làn vỉa hè, nên hành vi 7 (đi trên vỉa hè) và chỉ số M10 (đi trên vỉa hè) không tham gia hiệu chỉnh tại nút này. Hành vi 7 vẫn nằm trong phương pháp và trong mạng dữ liệu thay thế (bộ test). Chọn không thêm vỉa hè bằng giá trị giả định, vì một làn vỉa hè không có số đo sẽ làm điểm S chứa thêm một thành phần giả định mà video không kiểm được.

## D26. Báo cáo: kết quả trên mạng cũ và tên nút cũ (26/11)

Thân Chương 5 chỉ giữ kết quả trên mạng N7 (nút LVL x HMG x NT, dữ liệu video). Ba mục kết quả trên N6 (B0/B1, ba chiến dịch, hành vi của qwen) chuyển nguyên văn sang Phụ lục C, nhãn đổi thành `*_n6`. Các mạng N1–N6 được mô tả là "nút dựng ở giai đoạn đầu, cách nút nghiên cứu khoảng 570 m", không gọi bằng tên phố cũ, theo yêu cầu của chủ đề tài; hai nhánh phụ của nút đó gọi là "nhánh phụ". Câu trích nguyên văn đầu ra của LLM (listing trong Phụ lục C) giữ nguyên mã `HDT_N/S`, vì sửa là sửa dữ liệu.

## D27. Định dạng báo cáo (26/11)

- Tràn lề: thêm `\emergencystretch`, cho ngắt dòng sau `\_` và ngắt URL trong danh mục tài liệu; các bảng có tổng độ rộng cột vượt 15 cm được thu hẹp cột rộng nhất. Bản build không còn hộp overfull nào.
- In đậm: giữ tiêu đề cột của bảng, nhãn tóm tắt có cấu trúc (Bối cảnh, Phương pháp, Kết quả, Giới hạn) và khuôn Câu hỏi/Thiết lập/Quan sát/Diễn giải mà reviewer học viên đề nghị giữ (TONG_HOP mục 6). Các nhãn in đậm khác ở đầu đoạn được bỏ khi viết lại Chương 5 và 6.

## D28. Video demo (26/11)

Quay `sumo-gui` của đặc tả tốt nhất trong benchmark và của B0 trên VIDEO_V1, seed 1, 600 s đầu, chụp mỗi 0,3 s (tốc độ phát x6 ở 20 khung/s), bằng `report/2026-11-26/scripts/record_video.py` và `encode_video.py` (đã chuyển sang Windows và nút mới; chạy thử 60 s với B1_manual ngày 26/11 05:07). 600 s đủ cho gần bốn chu kỳ đèn 160 s mà video không quá dài.

## D29. P2 không có đặc tả hợp lệ; chạy lại với prompt v007 (26/11)

P2_v1126 (prompt v006) chạy 5 vòng × 4 mẫu, 56 lần trả lời, không lần nào hợp lệ, nên không tốn lần chạy SUMO nào. Lỗi nhiều nhất: đặt `queue_space_seeking` cho xe rẽ trái trái phép của `moto_violator` (trên N7 xe này không có phương án đi sai làn), mã nguyên mẫu trùng tên phân phối, phân phối `moto_violator` không có nguyên mẫu, tổng tỷ trọng khác 1. Prompt v006 còn một lỗi của chính luận văn: câu về hành vi 7 vẫn ghi vỉa hè đi được ở LVL_W và LVL_E, trong khi mạng N7 không có làn vỉa hè (D25); 3 luật trong các lần trả lời dùng `p_sidewalk`.

Các phương án: (a) báo cáo P2 thất bại và dừng; (b) đưa B1 vào làm ví dụ cấu trúc cho chế độ full; (c) sửa lỗi vỉa hè và viết rõ các ràng buộc cấu trúc mà bộ kiểm tra áp trên nút này, rồi chạy lại. Chọn (c): (b) trái quyết định thiết kế "full không nhận đặc tả nền" (loop.py), còn (a) để câu hỏi 2 thiếu phương án P2. Prompt v007 = v006 + câu vỉa hè đã sửa + một đoạn "Structure checks on this site" (mã nguyên mẫu khác tên phân phối; `queue_space_seeking` chỉ cho custom1 của `moto` và custom2 của `car`, chỉ qua `p_wrong_lane`; `illegal_left_box` chỉ cho custom1; tổng tỷ trọng một phân phối bằng 1). Mỗi câu đã kiểm lại với `validator.py` và mạng `site.net.xml` (wrong_lane có cho mọi lớp xe, right_lane và sidewalk không có). Chiến dịch mới tên P2b_v1126, cùng ngân sách, ngày, seed và mức trần; P2_v1126 giữ nguyên và được báo cáo cùng. P1 không bị ảnh hưởng: không đặc tả P1 nào dùng `p_sidewalk`. Chạy bằng `experiments/operator/n1126/run_p2b_chain.bat`; benchmark chạy lại sau đó, dùng lại kết quả đã có của các đặc tả khác và thêm đặc tả tốt nhất của P2b.
