# Báo cáo 29–30/10/2026: làn rẽ phải liên tục 30 m, chẩn đoán teleport, xe quay đầu chặn xe sau

Repo `D:\hust-master\Thesis` (branch `master`), chạy trên Windows (SUMO 1.27.0). Mọi thay đổi chưa commit: working tree bẩn so với `42ec69a`. Các quyết định trong ngày được liệt kê ở `DECISIONS.md`.

Lưu ý chung:
- Mọi số liệu là proxy (`LITERATURE_PROXY`), không phải số đo tại nút Lê Văn Lương × Hoàng Đạo Thúy.
- Không chạy campaign B2/P1/P2. Các số dưới đây là B0/B1 tham chiếu và các run chẩn đoán.
- Mỗi run dài 1800 s, trừ hai video (0–1500 s).

## 0. Tóm tắt

- Mạng (mục 1): làn 0 giờ chỉ là làn rẽ phải liên tục ở 30 m cuối. Mỗi cạnh tiếp cận được tách tại vạch dừng − 30 m. Có thêm các link chỉ dành cho custom1/custom2: rẽ trái từ làn 0 (LVL_W, LVL_E) và quay đầu từ làn 0, 1 (cả 4 nhánh), theo đèn rẽ trái. Vi phạm hành vi 6 nay là đứng chờ trên làn 0 trong 30 m cuối khi đèn của chính xe đó đỏ.
- B0/B1 tham chiếu (mục 2, `REF_n29s5`, 3 ngày × 5 seed):
  - B0: va chạm 50,3/h, va chạm trong làn 18,5/h, teleport kẹt/nhường 1,6/h, S 1,225.
  - B1: va chạm 53,1/h, va chạm trong làn 3,9/h, teleport kẹt/nhường 51,7/h, S 1,279.
  - Cả hai đều `excluded`.
- Teleport của B1 (mục 3.1) đến từ những lần nút bị khóa cứng. Tắt luật vượt đỏ theo đám (`swarm_red_running`, p = 0) thì teleport kẹt/nhường về 0 ở cả 3 seed của PROXY_D2. Bỏ các link mới từ làn 0/1 thì không hết.
- Va chạm trong làn của B0 (mục 3.2) tăng khoảng 6 lần so với mạng 28/10: 50 so với 8 trên 5 run PROXY_D1. Với B0, khác biệt duy nhất có tác dụng là chỗ tách cạnh 30 m. Cơ chế chưa tìm ra.
- Xe quay đầu chặn xe sau (mục 4): Viktor quan sát thấy, đo được (ví dụ HDT_N, B1, PROXY_D1, seed 1: 79 xe máy bị chặn khi đèn của chúng xanh, 4462 xe·giây). Đã thêm luật TraCI `uturn_bypass` và spec `B1_uturn_bypass`. Trên kịch bản nhỏ luật chạy đúng. Trên mạng proxy hiệu quả còn thấp: trong hàng xe máy dày (ba hàng ngang trên làn 3,5 m) SUMO không còn khe ngang để lách.
- Hai video (mục 5): `video1_B1_manual_PROXY_D2_seed1.mp4` (trước) và `video2_B1_uturn_bypass_PROXY_D2_seed1.mp4` (sau). Cùng ngày, seed, 0–1500 s.
- Test (mục 6): các test liên quan qua hết, trừ `test_short_run_on_new_net` (do mạng mới, mục 3.2) và `test_committed_B1_compiled_matches_spec` (CRLF khi checkout trên Windows). Phần lớn fail khi chạy cả bộ là do `libsumo` không nạp được DLL trên máy này.

## 1. Mạng: làn 0 là làn rẽ phải liên tục ở 30 m cuối

Mô tả của Viktor (29/10):
- Thượng nguồn có 3 làn thường. Chỉ 30 m cuối trước vạch dừng, làn 0 là làn rẽ phải liên tục: rẽ phải được cả khi đèn đỏ.
- Khi xanh, xe đi thẳng hoặc rẽ trái đi trên làn 0 là đúng luật.
- Xe có hướng đi thẳng, rẽ trái hoặc quay đầu mà dừng chờ đèn đỏ trên làn 0 trong 30 m cuối là vi phạm.

Đã làm:

| Phần | Thay đổi | File |
|---|---|---|
| Site | `right_lane_length_m: 30` cho 4 nhánh (proxy có nguồn Viktor 29/10, `field_observation`) | `config/site.proxy.yaml`, `config/site.yaml`, `config.py` |
| Mạng | Tách cạnh tại vạch dừng − 30 m (nút `<edge>.right_lane`); link rẽ trái từ làn 0 và quay đầu từ làn 0, 1, `allow="custom1 custom2"`, cùng trạng thái đèn với link rẽ trái/quay đầu gốc | `net/apply_patches.py` (`split_m`, `lane0_extras`, `_box_pins`) |
| Đo vi phạm | Hành vi 6 = xe hướng s/l/u, tốc độ < 5 km/h, trên làn 0, trong cạnh vạch dừng, khi link của chính nó đỏ | `sim/outputs.py` (`_own_signal_red`, `Geometry.right_lane_m`) |
| Prompt LLM | Mục 6 và câu "Not violations" của `v002`; phần mô tả nhánh trong `feedback.py` | `llm/prompts/v002/context.md`, `llm/feedback.py` |
| Tài liệu | PLAN, WORKFLOW, chương 3 LaTeX (2 dòng bảng) | `PLAN.md`, `SUMO/docs/WORKFLOW.md`, `Latex/Chuong/3_Cong_nghe.tex` |

Kết quả trên mạng `site.proxy.net.xml`:
- Cạnh vạch dừng dài 29,9–30,2 m ở cả 4 nhánh.
- Chuỗi TLS có 38 link: link 28–37 là link mới.
- Lựa chọn `p_wrong_lane` của `queue_space_seeking` chỉ chuyển xe sang làn kề bên. Vì vậy nó không đưa xe rẽ trái từ làn 2 sang làn 0. Xe vi phạm chỉ vào các link mới khi SUMO tự chọn làn.
- Ở `REF_n29` (B1, seed 1): rẽ trái từ làn 0 có 1 xe/ngày (chỉ LVL_W, D1 và D2); quay đầu từ làn 0/1 có 6–14 xe/ngày. B0 không có xe nào đi các link mới.

## 2. B0/B1 tham chiếu

`REF_n29s5`: PROXY_D1–D3 × seed 1–5, mỗi spec 15 run. Script: `SUMO/experiments/operator/ref/eval_ref_n29_s5.py`.

| | `REF_n28b` B0 (3 run) | `REF_n29s5` B0 (15 run) | `REF_n28b` B1 (3 run) | `REF_n29s5` B1 (15 run) |
|---|---|---|---|---|
| Va chạm/h | 38,67 | 50,27 | 21,33 | 53,07 |
| Va chạm trong làn/h | 1,33 | 18,53 | 0,00 | 3,87 |
| Teleport kẹt+nhường/h | 7,33 | 1,60 | 3,33 | 51,73 |
| S | 1,2116 | 1,2247 | 1,2538 | 1,2791 |

`REF_n28b` chỉ có 1 seed mỗi ngày, nên so sánh hai cột chỉ cho thấy chiều hướng. Số teleport kẹt/nhường của B1 theo từng run:

| Ngày | seed 1 | seed 2 | seed 3 | seed 4 | seed 5 |
|---|---|---|---|---|---|
| D1 | 6 | 3 | 0 | 42 | 4 |
| D2 | 42 | 7 | 1 | 29 | 21 |
| D3 | 42 | 7 | 40 | 28 | 39 |

9/15 run có ≥ 20 teleport. Mỗi lần nút khóa sinh ra khoảng 20–40 teleport.

## 3. Chẩn đoán

### 3.1 Teleport kẹt/nhường của B1: luật vượt đỏ làm khóa nút

Trạng thái lúc giây 1290 của B1, PROXY_D2, seed 1:
- Khoảng 38 xe đứng yên trong nút. Riêng làn nội bộ quay đầu làn 2 của HDT có 7 xe vi phạm rẽ trái.
- Hàng chờ dồn ngược ra 3 làn của cả LVL_W và LVL_E.

Các run chẩn đoán đều là B1, PROXY_D2:

| Biến thể | seed 1 | seed 2 | seed 3 |
|---|---|---|---|
| Mạng hiện tại | 42 | 7 | 1 |
| Bỏ hết link mới từ làn 0/1 | 38 | | |
| Chỉ bỏ link rẽ trái từ làn 0 | 33 | | |
| Chỉ bỏ link quay đầu từ làn 0/1 | 13 | | |
| Không tách 30 m, không link mới (giống mạng 28/10) | 3 | 16 | 3 |
| Mạng hiện tại, `swarm_red_running` p0 = p_max = 0 | 0 | 0 | 0 |

Đọc bảng:
- Tắt luật vượt đỏ thì không còn lần khóa nào. Va chạm vẫn ở mức cũ (31/22/29 so với 21/30/28). Luật vượt đỏ là điều kiện cần cho việc khóa nút.
- Bỏ link mới không hết khóa (38 so với 42). Mạng 28/10 cũng có khóa (16 ở seed 2). Với 3 seed thì không tách được phần đóng góp của mạng mới.
- Viktor muốn giữ đủ các hành vi (V4 trong `DECISIONS.md`), nên không có gì bị bỏ.

### 3.2 Va chạm trong làn của B0 tăng vì tách cạnh 30 m

B0 không có luật TraCI nên chạy thẳng bằng `sumo`, PROXY_D1, seed 1–5, cùng tùy chọn với runner:

| Mạng | Va chạm trong làn (5 run) | Va chạm trong nút (5 run) |
|---|---|---|
| 28/10 (`git show HEAD`) | 8 | 88 |
| Hiện tại | 50 | 90 |

Với B0, khác biệt duy nhất có tác dụng là chỗ tách 30 m: B0 không có xe nào đi các link mới, và nối đi thẳng giữa hai mạng giống hệt nhau.

Va chạm trong làn của B0 (`REF_n29s5`, 15 run) phần lớn là xe đi thẳng va xe đi thẳng cùng nhánh, trên làn 0 và làn 1 của cạnh **thoát**. Ví dụ: 24 lần trên `408823207#0_0` (HDT_S thẳng), 19 lần trên `37871458#0_0` (HDT_N thẳng).

Cơ chế chưa tìm ra. Nghi vấn là việc đổi làn bị dồn vào cạnh vạch dừng chỉ dài 30 m. Đây cũng là lý do `test_short_run_on_new_net` fail: 1 va chạm ngang ở giây 77 giữa hai xe đi thẳng HDT_S làn 2, trong lúc đổi làn. Mạng 28/10 không có va chạm này.

## 4. Xe quay đầu chặn xe sau

Viktor quan sát (30/10, nhiều nhất ở nút quay đầu Hoàng Minh Giám về Hoàng Minh Giám, tức HDT_N): xe máy quay đầu dừng chờ, các xe sau cùng làn bị chặn theo. Ngoài thực tế phần lớn xe máy sẽ lách sang bên hoặc sang làn kề; ô tô ít khi đổi làn để vượt.

Đo trên REF_n29, B1, PROXY_D1, seed 1, lấy mẫu mỗi 1 s. Định nghĩa: xe quay đầu đứng yên trên cạnh vạch dừng; xe sau cùng làn, không quay đầu, cách < 12 m, đứng yên trong khi link của chính nó xanh.

| Nhánh | Xe máy đi thẳng bị chặn (xe·s) | Xe vi phạm rẽ trái bị chặn (xe·s) | Ô tô (xe·s) | Số xe máy khác nhau |
|---|---|---|---|---|
| HDT_N | 1409 | 3053 | 0 | 79 |
| HDT_S | 285 | 833 | 22 | 101 |
| LVL_E | 658 | 615 | 209 | 47 |
| LVL_W | 1720 | 111 | 231 | 83 |

B0 cũng có hiện tượng này: ở HDT_N là 1207 xe·s, 79 xe. Hiện tượng vì vậy không do các link mới tạo ra.

Khi xe sau đứng ngay sau xe quay đầu, xem từ `fcd`, ví dụ HDT_N làn 2 lúc giây 310: làn rộng 3,5 m có ba hàng xe máy đứng song song (posLat 1,3; −0,1; −1,3). Hàng giữa là đoàn xe vi phạm rẽ trái đang chờ vào hộp. Khoảng cách dọc giữa các xe máy đứng là 1,9 m (minGap của Saval), ngắn hơn chiều dài xe máy 2,2 m. SUMO không cho xe chồng lên nhau nên xe sau không có đường lách.

### 4.1 Luật `uturn_bypass`

File `SUMO/src/thesis_sumo/runtime/rules/uturn_bypass.py`; tham số `p` [0, 1] và `t_wait` [0, 10] s trong `rules/schema.py`.

1. Xe bị chặn: đứng sau một xe quay đầu đang đứng trên cùng làn vạch dừng, cách ≤ 10 m, chồng ngang với nó, đèn của chính nó xanh.
2. Sau `t_wait` giây, luật bốc một lần với xác suất `p` cho mỗi cặp xe sau – xe quay đầu.
3. Nếu bốc trúng:
   - Lách ngang (`changeSublane`) vào khe ngang gần nhất bên cạnh xe quay đầu, lề 0,1 m (Saval et al. 2023, Sec 4).
   - Không có khe thì đổi sang làn kề có nối tới hướng đi của xe (`changeLane`).
4. Trong lúc can thiệp:
   - Bit 9–8 của `laneChangeMode` đặt là 01 ("avoid immediate collisions") thay cho 10.
   - `lcPushy` = 1, đặt cho riêng xe đó qua `setParameter`, nên không đổi vType.
   - Cả hai được trả lại khi kết thúc. Speed mode không đổi.

Spec `rules/specs/B1_uturn_bypass.json` là `B1_manual` giữ nguyên, thêm `uturn_bypass` cho các archetype xe máy (`p` 0,8) và ô tô (`p` 0,1), `t_wait` 2 s. Các giá trị này là giả định từ mô tả định tính của Viktor.

Kiểm tra:
- Kịch bản nhỏ (`tests/test_runtime.py::test_uturn_bypass_changes_lane`): một ô tô sau xe quay đầu bị giữ đứng ở vạch dừng.
  - Không có luật: ô tô chờ tới khi xe quay đầu đi (qua vạch lúc 78,1 s).
  - Có luật: ô tô đổi làn lúc 58,4 s và qua vạch lúc 63,2 s.
  - Cũng trong kịch bản này, khi bên cạnh trống, xe máy tự lách qua mà không cần luật (posLat −0,95 m).
- Mạng proxy (B1_uturn_bypass, PROXY_D1, seed 1), qua ba phiên bản luật:

| Phiên bản | Số lần bốc trúng | Vượt được | Kết quả không đạt |
|---|---|---|---|
| v1: chỉ lệnh lách/đổi làn, lề 0,3 m | 144 | 8 | 88 không có khe/làn, 48 không vượt trong 6 s |
| v2: + laneChangeMode 01 | 150 | 16 | 77 không có khe/làn, 57 không vượt |
| v3: + `lcPushy` 1, lề 0,1 m (bản dùng cho video 2) | 150 | 13 | 42 không có khe/làn, 95 không vượt |

  Số xe máy đi thẳng bị chặn (xe·s, trước → v3): HDT_N 1409 → 1071, HDT_S 285 → 494, LVL_E 658 → 899, LVL_W 1720 → 795. Một run một seed nên chưa nói được là có giảm.

Hạn chế:
- Trong hàng xe máy dày, SUMO giữ hình học không chồng lấn, nên xe sau chỉ lách được khi có khe ngang thật.
- Ngoài thực tế xe máy đứng sát nhau hơn 1,9 m và len qua các khe dọc. Muốn có hành vi đó cần một trong hai điều chỉnh, đều là quyết định của Viktor (mục 7):
  - minGap của xe máy khi đứng nhỏ hơn.
  - Cho phép xe vi phạm rẽ trái đứng lệch sang trái (latAlignment).

## 5. Video

Cách quay giống 28/10: sumo-gui chạy luật TraCI, chụp màn hình mỗi 3 bước (0,3 s), sau đó ghép chú thích và mã hóa ở 20 fps (tốc độ ×6). Script là bản Windows: `scripts/record_video.py` (thêm watchdog chống treo của bản 26/10) và `scripts/encode_video.py` (font Segoe UI, ffmpeg của `imageio-ffmpeg`).

| | Video 1 (trước) | Video 2 (sau) |
|---|---|---|
| File | `video1_B1_manual_PROXY_D2_seed1.mp4` | `video2_B1_uturn_bypass_PROXY_D2_seed1.mp4` |
| Spec | `B1_manual` | `B1_uturn_bypass` |
| Khoảng mô phỏng | 0–1500 s (07:30–07:55) | 0–1500 s |
| Độ dài, dung lượng | 4:10, 48 MB | 4:10, 53 MB |
| Va chạm (trong nút / trong làn) | 21 (20 / 1) | 26 (24 / 2) |
| Teleport (không do va chạm) | 40 (19) | 26 (0) |
| Xe chờ chèn ở 1500 s | 289 | 187 |

Video 1 khớp với run batch `REF_n29s5/B1_manual__PROXY_D2/seed_01`: 19 teleport kẹt/nhường đầu tiên giống từng dòng, 21 va chạm. Nút bắt đầu khóa khoảng giây 1290.

Ở video 2, luật `uturn_bypass` bốc trúng 81 lần:
- 3 lần đổi làn thành công.
- 50 lần lách ngang nhưng không vượt được trong 6 s.
- 19 lần không có khe và không có làn kề phù hợp.
- 9 lần đổi làn không thành.

Video 2 không có lần khóa nút nào (0 teleport kẹt/nhường, so với 19 ở video 1). Với một seed và một mô phỏng nhạy với thay đổi nhỏ, chưa quy được kết quả này cho luật mới: ở `REF_n29s5`, cùng spec B1 mà số teleport kẹt/nhường dao động từ 0 đến 42 tùy seed.

Xe máy đi thẳng bị chặn sau xe quay đầu khi đèn của chính nó xanh (xe·s, cùng định nghĩa với mục 4, 0–1500 s), video 1 → video 2:
- HDT_N: 184 → 53
- HDT_S: 76 → 132
- LVL_E: 3948 → 1373
- LVL_W: 225 → 626

Kết quả lẫn lộn. Phần lớn mức chặn ở LVL_E của video 1 rơi vào lúc nút đang khóa.

Màu trong video:
- Xanh dương: ô tô. Vàng: xe máy.
- Tím: xe vi phạm rẽ trái. Đỏ: xe vi phạm đang chờ giữa nút.
- Xanh lơ: xe không rẽ phải trên làn 0 gần vạch dừng. Đây không tự động là vi phạm, vì đứng lúc xanh là hợp lệ.
- Cam: xe rẽ phải đứng sau một xe xanh lơ.
- Trắng: xe máy trên vỉa hè.

Video chưa có màu riêng cho xe quay đầu chặn xe sau. Lần quay đầu tiên của video 1 bị treo ở khung 2342 khi máy đang chạy 7 tiến trình sim cùng lúc, nên đã quay lại từ đầu.

## 6. Test

Các file test đã sửa:
- `test_outputs_synthetic.py`: kỳ vọng F2 theo định nghĩa mới, thêm 3 trường hợp.
- `test_demand.py`: số cạnh của route.
- `test_net.py`, `test_validator.py`: link mới, luật mới.
- `test_runtime.py`: 2 test của `uturn_bypass`.

Ngoài ra đã sinh lại `routes_SYNTHETIC.rou.xml` (seed 1).

Pytest toàn bộ, chạy lại sau khi thêm luật (30/10, 03:00): 340 passed, 41 failed, 6 errors, 2 xfailed. Chạy lại riêng từng test fail/error thì còn 9:
- `test_net.py::test_short_run_on_new_net`: do mạng mới, mục 3.2. Chưa nới điều kiện.
- `test_compiler.py::test_committed_B1_compiled_matches_spec`: file `rules/compiled/B1` checkout với CRLF (`core.autocrlf=true`), không do thay đổi trong ngày.
- 6 test `test_optuna.py`: `OSError: [WinError 1314] A required privilege is not held by the client` khi Optuna tạo symlink cho file journal. Đây là quyền Windows, lỗi môi trường.
- `test_runtime.py::test_junction_info_on_proxy_net`: `ImportError: DLL load failed while importing _libsumo`, kể cả khi chạy riêng.

Các test còn lại fail khi chạy cả bộ do `libsumo` không nạp được DLL, và qua khi chạy riêng. Lỗi DLL và quyền symlink cần kiểm lại trên máy Linux.

## 7. Cần Viktor quyết

1. Khóa nút ở B1 (mục 3.1). Có ba hướng:
   - Coi đây là thuộc tính của mô hình.
   - Thêm điều kiện cho luật vượt đỏ: không vào nút khi lối ra đang kín.
   - Để P1/P2 tự chỉnh p0.
2. Va chạm trong làn của B0 tăng 6 lần do tách 30 m (mục 3.2). Cần tìm cơ chế trước khi chạy campaign. B0 hiện vượt xa trần R10 của chính nó.
3. `uturn_bypass`:
   - Có đưa vào cấu trúc của B1/P1/B2 và prompt LLM không? Hiện chỉ có trong spec video.
   - Có chấp nhận minGap nhỏ hơn cho xe máy khi đứng chờ không? Nếu không, luật ít có tác dụng trong hàng dày.
4. Làn 0 của LVL có thêm vạch `l` không? Hiện `lane_movements` làn 0 là `[r, s]`, nên rẽ trái từ làn 0 bị đếm là `wrong_lane`.
5. Xóa các thư mục chạy chẩn đoán chưa track:
   - `SUMO/experiments/campaigns/AB_*`, `AB3_*`.
   - `REF_n29` (1 seed, đã có `REF_n29s5` thay thế).
   - `report/2026-10-29/_rec`, `_rec2`: thư mục run của hai video, khoảng 190 MB mỗi cái, không bị git ignore. Khung PNG đã xóa sau khi mã hóa; số liệu video đã chép vào `data/video1_run_manifest.json`, `data/video2_run_manifest.json`.

## 8. Lệnh tái lập

Chạy từ `SUMO/` trên Windows:

```bash
.venv/Scripts/python -m thesis_sumo.net.build --site config/site.proxy.yaml
.venv/Scripts/python -m thesis_sumo.demand.build_demand --net scenario/net/site.proxy.net.xml --counts data/observed/PROXY_D1/turn_counts.csv --seed 101
.venv/Scripts/python -m thesis_sumo.proxy.generate
.venv/Scripts/python -m thesis_sumo.demand.build_demand --net scenario/net/site.proxy.net.xml --counts data/observed/SYNTHETIC/turn_counts.csv --seed 1
.venv/Scripts/python experiments/operator/ref/eval_ref_n29_s5.py
```

Video, chạy từ thư mục gốc repo. `imageio-ffmpeg` được cài vào một thư mục riêng rồi trỏ `PYTHONPATH` tới đó:

```bash
SUMO/.venv/Scripts/python report/2026-10-29/scripts/record_video.py --spec-json SUMO/rules/specs/B1_manual.json --day PROXY_D2 --seed 1 --end 1500 --every 3 --out report/2026-10-29/_rec
SUMO/.venv/Scripts/python report/2026-10-29/scripts/encode_video.py --rec report/2026-10-29/_rec --out report/2026-10-29/video1_B1_manual_PROXY_D2_seed1.mp4 --fps 20
SUMO/.venv/Scripts/python report/2026-10-29/scripts/record_video.py --spec-json SUMO/rules/specs/B1_uturn_bypass.json --day PROXY_D2 --seed 1 --end 1500 --every 3 --out report/2026-10-29/_rec2
SUMO/.venv/Scripts/python report/2026-10-29/scripts/encode_video.py --rec report/2026-10-29/_rec2 --out report/2026-10-29/video2_B1_uturn_bypass_PROXY_D2_seed1.mp4 --fps 20
```
