# Quyết định ngày 27/11/2026

Tiếp nối `docs/DECISIONS_2026-11-26.md` (D1–D29). Chủ đề tài cho phép tự quyết trong lúc chạy thí nghiệm và ghi lại ở đây.

## D30. Pha đèn tách theo nhánh LVL (27/11)

Chủ đề tài đánh giá lại tại hiện trường: mỗi nhánh LVL có pha xanh riêng, gồm đi thẳng, rẽ trái và quay đầu cùng lúc, khoảng 53–60 s, đỏ khoảng 107–115 s. NT–HMG chỉ đi thẳng, xanh 40 s, đỏ 115 s. Hai nhánh LVL xen kẽ, NT–HMG chen giữa.

Kiểm tra trên dữ liệu theo vết thật của IMG_4801 (`video/runs/V2_IMG_4801/od_tracks.csv`, 309 s, khoảng hai chu kỳ):

| Pha | Xe rời nhánh, chu kỳ 1 | Chu kỳ 2 |
|---|---|---|
| LVL_E đi thẳng và rẽ trái | khoảng 0–45 s | 152–205 s |
| NT (rẽ phải, đi thẳng, rẽ trái cấm) | 44–85 s | 205–245 s |
| LVL_W đi thẳng | 88–143 s | 256–303 s |

Mỗi đợt xả lặp lại sau 160–161 s, khớp chu kỳ đo từ đèn đi bộ. Pha NT bắt đầu cùng lúc đèn đi bộ xanh (39,5 s và 199,5 s trong `light_rgb.csv`). Phương án ba pha ngày 26/11 (hai nhánh LVL cùng đi thẳng, rồi cùng rẽ trái, rồi NT–HMG) không khớp dữ liệu này: LVL_E rẽ trái xả cùng lúc với LVL_E đi thẳng, còn LVL_W đi thẳng xả sau NT.

Ghi chú: các bảng `data/observed/VIDEO_V*/` được sinh từ `site.yaml` (`manifest.json`: "generated, not field data"), nên không dùng được để đo pha đèn; chỉ `od_tracks.csv` và `light_rgb.csv` là số đo thật.

Chọn chu kỳ 160 s với LVL_E xanh 50 s, NT–HMG 40 s, LVL_W xanh 55 s; mỗi lần chuyển pha vàng 3 s và đỏ toàn phần 2 s (chủ đề tài chọn phương án này). Độ dài xanh lấy theo độ dài đợt xả, sai số khoảng ±3 s vì chỉ có hai chu kỳ. Đèn xe của các nhánh không thấy trong video, nên vàng và đỏ toàn phần vẫn là giả định (`TODO_MEASURE`). NT–HMG giữ rẽ phải như cũ; rẽ trái từ NT và HMG vẫn cấm, chỉ lớp xe vi phạm được rẽ, trong pha NT–HMG.

Hệ quả: dựng lại `site.net.xml`, sinh lại VIDEO_V1/V2 (trạng thái đèn và các chỉ số theo đèn đổi theo), chạy lại REF, B2, P1, P2 và benchmark dưới tên `*_v1127`. Kết quả `*_v1126` giữ nguyên làm lịch sử. Test `test_proxy_has_same_structure_as_site` cho phép tên giai đoạn trong `stage_totals_s` khác nhau giữa hai tệp site.

## D31. Xe máy vào mạng dàn ngang (27/11)

Chủ đề tài nhận xét: ngoài thực tế, xe chờ trên đoạn đệm xếp lộn xộn, còn trong mô phỏng chỉ xếp một hàng. Một nguyên nhân là cách đưa xe vào mạng: `departLane="best"` và không đặt `departPosLat`, nên theo mặc định `center` của SUMO mọi xe máy vào mạng trên đường tim làn, nối đuôi nhau. Điều này cũng giới hạn số xe vào được mỗi giây và làm hàng chờ vào mạng lên tới hơn 1000 xe.

Chọn `departPosLat="random_free"` cho `moto` và `moto_violator` (tài liệu SUMO: thử mười vị trí ngang ngẫu nhiên, nếu đều bị chiếm thì dùng vị trí trống). Đây là thiết lập đưa xe vào mạng, áp dụng cho mọi đặc tả, kể cả B0. Cách xe xếp ở vạch dừng (`latAlignment`, `minGapLat`, `lcSublane`, ...) vẫn là hành vi do bộ luật hiệu chỉnh; B0 giữ giá trị mặc định của SUMO để hình so sánh thấy được khác biệt.

## D32. Chỉ chạy chế độ full với prompt v007 (27/11)

Ngày 26/11, chế độ full với prompt v006 không cho đặc tả hợp lệ nào trong 60 lần thử (D29), còn v007 cho 11/20 mẫu hợp lệ. Chiến dịch full ngày 27/11 (`P2_v1127`) chỉ chạy v007. Kết quả v006 của ngày 26/11 vẫn được báo cáo như một quan sát về hành vi của LLM.

## D33. Sửa lưu lượng đi thẳng của HMG và LVL_W (27/11)

Chủ đề tài nhận xét lưu lượng HMG đi NT và LVL_W đi LVL_E quá thấp so với thực tế, và yêu cầu đặt mỗi cặp hướng đi thẳng đối diện bằng nhau, theo giá trị cao hơn. Trong video, lối ra HMG bị khung cửa che, nên HMG đi thẳng chỉ là giả định 15 % (D18); vạch dừng LVL_W ở xa máy quay, nên đếm thiếu.

Đổi trong `data/video_targets/targets_video.yaml`: HMG đi thẳng từ 348 lên 906 xe/h (bằng NT đi thẳng), LVL_W đi thẳng từ 598 lên 3217 xe/h (bằng LVL_E đi thẳng). Các hướng khác giữ nguyên số xe/h. Lưu lượng nhánh: LVL_W từ 830 lên 3448, HMG từ 2283 lên 2841 xe/h; tỷ lệ hướng của hai nhánh này tính lại. Hai giá trị mới là ước lượng của chủ đề tài, không phải số đo, và được ghi như vậy trong tệp mục tiêu.

Số xe đếm trong ngày sinh không bằng đúng mục tiêu: bộ sinh mô phỏng xe xả theo pha đèn, nên với 40 s xanh nhánh NT chỉ qua được khoảng 85 % mục tiêu trong cửa sổ đếm. Trong VIDEO_V2, HMG đi thẳng là 788 và NT đi thẳng là 730 xe/h; LVL_W đi thẳng là 3070 và LVL_E đi thẳng là 3380 xe/h.

## D34. Bộ hình so sánh (27/11)

Chủ đề tài chọn ba loại hình cho Chương 5, mỗi hình có B0 (SUMO mặc định) và đặc tả LLM tốt nhất, thêm B2 khi cần:

- vết xe thời gian–không gian trên một nhánh LVL qua hai chu kỳ, nền tô theo trạng thái đèn;
- cột chỉ số hành vi (mục tiêu / B0 / B2 / LLM), kèm va chạm và xe chờ vào mạng;
- lưu lượng theo hướng: đếm từ video so với mô phỏng, dải GEH 5.

Hình C.1 cũ (`traj_b0_b1.png`, mạng N6, dữ liệu PROXY) được thay bằng bộ hình này. Chú thích mỗi hình ghi rõ B0, B1, B2, P1, P2 là gì. Phía "video" chỉ dùng số đo thật (lưu lượng theo vết, đèn đi bộ); các chỉ số hành vi mục tiêu của ngày VIDEO là dữ liệu sinh từ tài liệu và được ghi rõ như vậy.

## D35. Rút lại D31: xe máy vào mạng ở tim làn như mặc định (27/11, 01:29)

Lượt REF_v1127 đầu tiên (bắt đầu 01:03) cho B0 110,4 va chạm/h, trong đó 64,8 va chạm trên làn, so với 20,0 và 8,0 của REF_v1126. Phần lớn là va chạm phía sau và va chạm sườn giữa xe máy ở đoạn thượng lưu của LVL_E và LVL_W; nhiều xe đứng yên bị đâm liên tiếp ở cùng một vị trí. Để tách nguyên nhân, B0 seed 1 trên VIDEO_V2 chạy lại bằng `sumo` với pha đèn mới và bốn tệp tuyến (thư mục tạm, không thuộc chiến dịch nào):

| Lưu lượng | Vị trí ngang khi vào mạng | Va chạm/h | Xe vào được mạng | Xe còn chờ |
|---|---|---|---|---|
| cũ (26/11) | tim làn | 22 | 6263 | 949 |
| cũ (26/11) | `random_free` | 82 | 6246 | 966 |
| mới (D33) | tim làn | 64 | 6879 | 1437 |
| mới (D33) | `random_free` | 96 | 7335 | 981 |

Riêng pha đèn mới không làm tăng va chạm (22/h, gần mức 20/h ngày 26/11). `random_free` làm va chạm tăng khoảng bốn lần mà với lưu lượng cũ không đưa thêm được xe nào vào mạng. Cách giải thích hợp lý nhất: xe máy của B0 dùng `latAlignment` mặc định `center`, nên xe vào mạng lệch tâm sẽ kéo ngang về tim làn và quệt xe bên cạnh. Chọn rút D31: mọi xe vào mạng ở tim làn như trước. Việc xe máy dàn hàng ngang khi chờ đèn để bộ luật hiệu chỉnh qua `latAlignment`, `minGapLat`, `lcSublane`, đúng với phân công chủ đề tài đã chọn (vạch dừng do bộ luật).

Lưu lượng mới của D33 tự nó nâng va chạm của B0 lên khoảng 64/h trong lượt thử này, do hàng chờ dài hơn ở LVL_W và LVL_E. Đây là phản ứng của mô hình mặc định với nhu cầu chủ đề tài yêu cầu, nên giữ nguyên; mức trần R10 của các chiến dịch lấy theo B0 của REF_v1127 như quy tắc cũ. REF_v1127 đầu tiên được chuyển ra thư mục tạm, chuỗi chạy lại từ đầu lúc 01:29.

## D36. Video demo tốc độ 3x và bảng hồ sơ hành vi (27/11)

Chủ đề tài yêu cầu video demo phát ở tốc độ 3x (video 26/11 là 6x). Chọn chụp mỗi 2 bước mô phỏng (0,2 s) và mã hóa 15 khung/s: 0,2 s × 15 = 3 s mô phỏng mỗi giây video. Lệnh: `record_video.py --every 2`, `encode_video.py --fps 15`; quay B0 và đặc tả tốt nhất trên VIDEO_V1, seed 1, 600 s đầu, sau khi benchmark xong.

Theo kết luận chủ đề tài chọn (kết luận về bộ luật như một tổng thể), `experiments/operator/n1127/profile.py` lập bảng hồ sơ hành vi trên ngày kiểm định: cột mục tiêu, B0, B1 và các đặc tả tốt nhất; hàng theo ba nhóm hành vi, rồi S và các hàng ổn định; kèm danh sách hành vi mà mỗi đặc tả không thể tạo ra (không có luật, xác suất 0, hoặc luật chỉ gắn với nguyên mẫu tỷ trọng 0). Kiểm thử trên BENCH_v1126 cho kết quả hợp lý (ví dụ B1 có `early_start` với p = 0 và `queue_space_seeking` với cả ba xác suất bằng 0). Bóc tách từng luật (B1 bỏ một luật, 5 seed) chỉ làm nếu còn thời gian sau benchmark, và chỉ đưa vào phụ lục.

## D37. Cặp video A/B và bộ hình cho báo cáo (27/11)

Yêu cầu của chủ đề tài (qua phiên thesis-03): một cặp video để so sánh trực quan và một bộ hình, tất cả trên mạng v1127, ngày kiểm định VIDEO_V1.

Video A là B0 (SUMO mặc định, trước hiệu chỉnh), Video B là bộ luật tốt nhất của BENCH_v1127; không gọi V1/V2 để khỏi nhầm với tên ngày. Hai video cùng ngày, cùng seed, cùng khung thời gian (ba chu kỳ sau khởi động, 480–960 s), cùng khung nhìn, cùng tốc độ 3x (D36), cùng chú giải màu, có lớp ghi pha đèn và đồng hồ mô phỏng. Khung nhìn xoay `--angle -45` (traci `gui.setAngle`): LVL nằm ngang, phía Tố Hữu bên trái, HMG phía trên, NT phía dưới, gần góc máy IMG_4801 nhìn từ tòa HUD; đã thử cả hai dấu, `+45` làm LVL dựng đứng. Ghép bằng `report/2026-11-27/scripts/combine_video.py`: bản hai khung A | B và bản ba khung có thêm đoạn IMG_4801 phát cùng tốc độ (video thật chỉ dài 309 s, nên khung thật giữ ảnh cuối khi hết). Ảnh tĩnh cho Hình A1 lấy cùng thời điểm từ hai lần quay cộng một khung IMG_4801.

Bộ hình (B0 so với bộ luật tốt nhất, thêm mục tiêu quan sát khi có): F-A cặp ảnh sumo-gui cùng giây, chọn tự động thời điểm có nhiều hành vi cùng lúc nhất trong lần chạy của bộ luật (ưu tiên cuối pha đỏ của LVL), kèm JSON tọa độ điểm ảnh của từng hành vi, hành vi có p = 0 ghi là vắng; D1 cột hồ sơ hành vi theo ba nhóm; D2 vết xe thời gian–không gian ở vạch dừng; D3 tần suất số xe vượt đỏ mỗi chu kỳ mỗi nhánh kèm tỷ số phương sai/trung bình; D4 mật độ hai chiều vị trí xe máy dừng lúc đầu pha xanh; D5 quỹ đạo trong một chu kỳ; D6 chuỗi thời gian số xe chờ giữa nút; D7 cột độ ổn định. D1, D3, D7 lấy trung bình 20 seed; D2, D4, D5, D6 và F-A dùng cùng một seed. Nhãn tiếng Việt, hậu tố `_v1127`, lưu vào `Latex_SOICT/Figure/`. Ba hình của D34 trùng với D1, D2 và hình lưu lượng; giữ cả hình lưu lượng.

## D38. Ổ D: đầy giữa chiến dịch; chuyển tệp thô cũ sang C: và chạy tiếp (27/11, 04:45)

Khoảng 04:21, ổ D: hết chỗ trống (0 GB trên 488 GB; riêng `experiments/campaigns/` chiếm 108 GB). B2_v1127 chết với `OSError(28, 'No space left on device')` khi đang ở thử nghiệm t006 (21/36 lần chạy đã tính), P1_v1127 có 3 lần chạy của vòng 3 không ghi được manifest (33/36 lần chạy đã tính).

Chọn không xóa gì: các tệp thô lớn không được git theo dõi (`fcd.xml.gz`, `lanechange.xml`, `tripinfo.xml`) của các chiến dịch trên mạng cũ (P1/B2/P2_n1108, REF_n29s5, REF_n1126, REF_n1104s5, AB_d1, AB_d1v) và của ba chiến dịch v1126 (P1, B2, P2b; số đã tổng hợp xong) được chuyển bằng `robocopy /MOV` sang `C:\thesis_archive\SUMO_campaigns\`, giữ nguyên cấu trúc thư mục; `manifest.json`, `collisions.xml`, `observed_schema/` ở lại chỗ cũ. Ổ D: còn 58,9 GB, đủ cho phần còn lại (ước khoảng 45 GB). BENCH_v1126 giữ nguyên vì `figures.py` và `profile.py` đã chạy thử trên nó.

Các chiến dịch được chạy tiếp theo cơ chế tiếp tục đã có, không chạy lại từ đầu: thử nghiệm Optuna đang dở không có kết quả lưu được báo FAIL và giữ 3 lần chạy đã tính (B2 còn 15 lần chạy, tức 5 thử nghiệm, tổng 11 thử nghiệm hoàn chỉnh thay vì 12); mẫu LLM đã tính lần chạy mà chưa có kết quả được đánh dấu `lost`. Vòng 3 của P1 không có tệp kết quả nào (cả ba mẫu đều mất, kể cả mẫu s00 đã chạy đủ ba seed, vì tệp kết quả không ghi được lúc đĩa đầy), nên P1 mất 9 lần chạy, B2 mất 3. Chọn không nới ngân sách giữa chừng (quy tắc của kế hoạch): P1 còn 3 lần chạy cho một mẫu ở vòng 4, tức 27 lần chạy có kết quả so với 33 của B2. Chênh lệch này nghiêng về B2 và phải ghi cùng kết quả ở câu hỏi 2. Chuỗi được dừng hẳn và chạy lại `run_chain.bat` lúc 04:45.

## D39. Dọn ổ D: theo yêu cầu chủ đề tài (27/11, khoảng 10:20)

Chủ đề tài cho xóa các phần làm từ tháng 10 trong `SUMO/` và tệp thô của BENCH_v1126 (đã xác nhận phạm vi). Đã xóa: `experiments/runs/` (B0 SYNTHETIC/PROXY, phase3, r15_timegap, task9), các chiến dịch tháng 10 trong `experiments/campaigns/` (REF, B2, P1, P2, AB3_*, AB_*, *_n28, *_n28b, REF_n29, REF_n29s5 và log, các `supervise_llm*.sh`), `experiments/llm_logs/` của các chiến dịch đó, và `fcd.xml.gz`, `lanechange.xml`, `tripinfo.xml` của BENCH_v1126 (300 tệp; manifest, collisions, observed_schema còn nguyên). Tệp git theo dõi được xóa bằng `git rm` (1404 dòng xóa trong `git status`, chưa commit), nên vẫn khôi phục được từ lịch sử git; tệp ngoài git mất hẳn. Giữ nguyên `scenario_raw/` (bất biến theo CLAUDE.md), `legacy/` và mọi thứ `*_v1127`. Ổ D: từ 30,7 GB lên 53,6 GB trống. Hệ quả: không chạy lại được `figures.py`, `profile.py`, `fa.py` trên BENCH_v1126 nữa (cần fcd); chúng đã được thử xong trước đó.

## D40. Bộ luật cuối dùng cho video và hình so sánh (27/11, 12:20)

BENCH_v1127 (VIDEO_V1 × seed 1–20) xong lúc 11:57: B0 S 0,993; B1 1,059; B2 0,941; P1 1,087; P2 1,062. Không đặc tả nào đạt tiêu chí chấp nhận ở lần chạy nào. Theo quy tắc chọn dự phòng của luận văn (ít teleport kẹt/h nhất, rồi $S$ nhỏ nhất), trong các bộ luật B2 đứng đầu (4,7/h, so với B1 12,0, P1 15,7, P2 24,4); B2 cũng có $S$ nhỏ nhất, qua cổng G0 ở 20/20 lần chạy và ít xe chờ vào mạng nhất (454). Chọn bộ luật cuối ("RS") cho cặp video A/B, hình F-A và D2–D7 là `B2_v1127_best`. LLM tốt nhất là P2 (`P2_v1127_best`, S 1,062); hình hồ sơ hành vi (D1) có đủ B0, B2, P1, P2, và cặp hình B0 | P2 được giữ với tên `fig_spacetime_llm_v1127.png`, `fig_flows_llm_v1127.png` để so sánh riêng phần LLM.
