# Báo cáo vòng 2 — 28/10/2026 (làn 0 mở cho đi thẳng khi xanh)

Repo `~/Projects/thesis-hust` (branch `master`), Linux, SUMO 1.27.0. Vòng 1 (mạng có cọc, id `_n28`) nằm ở `../README.md` và giữ nguyên để so sánh. File này là vòng 2 (id `_n28b`). Bối cảnh và các quyết định kỹ thuật: `../HANDOFF.md`. Nhật ký điều phối: `../PROGRESS.md`. Số liệu thô: `data/`.

**Lưu ý chung (giống vòng 1):**
- Mọi số liệu quan sát là **proxy** (`LITERATURE_PROXY`), không phải số đo tại nút Lê Văn Lương × Hoàng Đạo Thúy.
- Spec P1/P2 do **Claude Sonnet đóng vai LLM** (`provenance.model` = "claude-sonnet (stand-in)"). Đây **không phải** kết quả của phương pháp LLM local.
- Mỗi spec chạy PROXY_D1 đến D3 × **1 seed**, mỗi run 1800 s. Đây là kết quả hiệu chỉnh, chưa phải benchmark. PROXY_D4/D5 không dùng.
- Manifest các run ghi `git_dirty` = true và hash commit không đồng nhất giữa B0, B1 và các campaign (`685b4fe`, `cc6df0f`, `84406c9`). Hash đầu vào (net `5b6355f8`, site `9ba38295`, routes theo ngày) thì đồng nhất ở mọi run vòng 2.

## 0. Tóm tắt

- **Thay đổi theo yêu cầu của Viktor:** làn 0 (làn rẽ phải liên tục) vẫn rẽ phải không chờ đèn; đi thẳng từ làn 0 khi đèn xanh nay hợp lệ; bỏ cọc phân cách; màu làn 0 trong sumo-gui nhạt hơn (`#FFF3B0`, alpha 0,5).
- **Kết quả:** không spec nào đủ điều kiện (**0/23 spec**, B0 và B1_manual cũng bị loại). Best chọn theo R32/R42 (ít teleport kẹt/nhường nhất, rồi S nhỏ nhất).
- **Best chung** là `P2_n28b_it02_s03`: S 1,0122 (B0 1,2116), va chạm 35,33/h (B0 38,67/h), không có teleport kẹt/nhường (B0 7,33/h). Đổi lại, va chạm trong làn **12,0/h so với 1,33/h của B0**, vượt trần R10 (B0 + 1 = 2,33/h). Spec này vẫn `excluded`.
- **Kết luận so sánh LLM với Optuna: chưa rút được.** 1 seed mỗi ngày, LLM là stand-in, không spec nào eligible.
- **Việc cần Viktor quyết** (mục 5): B1 bỏ `car_seeker`, hai chỉ tiêu M9 trong `targets.yaml`, kiểu kẹt ô chờ HDT_S ở D1, tín hiệu `g` của làn 0 đi thẳng cạnh vỉa hè.
- **Có một lỗi quy trình ảnh hưởng số liệu:** `P2_n28b_it01_s00` mất kết quả (3 run đã tính vào budget). P2 chỉ còn 7 spec có điểm. Chi tiết ở mục 3.4.

## 1. Mạng và kịch bản vòng 2

Nguồn: `../HANDOFF.md` mục 2.2. Tóm tắt phần đổi:

| | Vòng 1 | Vòng 2 |
|---|---|---|
| Rẽ phải từ làn 0 | Luôn `g` (không chờ đèn) | Giữ nguyên |
| Đi thẳng từ làn 0 | Cấm; chỉ custom1/custom2 đi khi tắc (lựa chọn `right_lane` của luật TraCI) | Mở cho mọi xe, theo đèn đi thẳng của nhánh |
| Cọc 30 m cuối nhánh | Có | Bỏ (`right_lane_separator: open`, `bollard_length_m: null`) |
| `lane_movements` làn 0 | `[r]` | `[r, s]` |
| Lựa chọn `right_lane` của `queue_space_seeking` | Có | Không còn trên mạng này |

Hệ quả cho phần đo: xe đi thẳng đứng chờ ở làn 0 lúc đèn đỏ (chặn xe rẽ phải, hành vi 6) nay do SUMO tự chọn làn, không còn do luật TraCI. `sim/outputs.py` chỉ ghi sự kiện `right_lane` và `blocked` cho xe đi thẳng đứng dưới 5 km/h ở làn 0.

Kiểm thử: pytest 384 passed, 2 xfailed (lúc triển khai, commit `f0727aeb`).

## 2. Mốc tham chiếu B0 và B1 (`REF_n28b`, 3 ngày × 1 seed)

Nguồn: `data/REF_B0_B1.txt`.

| | B0 vòng 1 | B0 vòng 2 | B1 vòng 1 | B1 vòng 2 |
|---|---|---|---|---|
| Va chạm/h | 34,67 | 38,67 | 41,33 | 21,33 |
| Va chạm trong làn/h | 2,67 | 1,33 | 0,00 | 0,00 |
| Teleport kẹt+nhường/h | 0,00 | 7,33 | 24,00 | 3,33 |
| S | 1,1235 | 1,2116 | 1,1975 | 1,2538 |
| Backlog còn chờ chèn xe (TB mỗi run) | 47 | 0 | 409 | 394 |

- Cả bốn đều `excluded`. B1 vòng 2 bị loại ở cổng G0 GEH (0,767; 0,800; 0,783) và backlog chèn xe 290 đến 553 xe mỗi run: **va chạm thấp của B1 đi cùng việc gần 400 xe không vào được mạng**, nên không đọc nó là "B1 tốt hơn B0".
- B0 vòng 2 có toàn bộ teleport kẹt/nhường ở D1 (11 lần, t khoảng 945 đến 1290 s): ba xe vào ô chờ ở HDT_S cùng lúc, chặn nhau khoảng 300 s, kéo theo cả ba làn LVL_W. Đây là hiện tượng của mạng, chưa được xử lý (mục 5).
- Vòng 1 và vòng 2 khác nhau ở net, routes và hash site, nên chênh lệch không quy hết cho thay đổi làn 0.

## 3. Chiến dịch `_n28b`

Mỗi phương pháp có budget 24 run. B2 (Optuna) 8 trial; P1 (LLM chỉ chỉnh tham số, cấu trúc `B1_manual`) và P2 (LLM sinh cả cấu trúc) mỗi cái 2 vòng × 4 spec. Nguồn: `data/campaign_summary.txt`, `data/campaign_specs.csv`, `data/B2_convergence.csv`.

### 3.1 Best theo từng phương pháp (R32/R42)

| Phương pháp | Spec | S | Va chạm/h | Làn/h | Teleport kẹt+nhường/h |
|---|---|---|---|---|---|
| B0 (mốc) | — | 1,2116 | 38,67 | 1,33 | 7,33 |
| B1_manual (mốc) | — | 1,2538 | 21,33 | 0,00 | 3,33 |
| B2_n28b | `B2_n28b_t007` | 1,2823 | 32,67 | 9,33 | 0,00 |
| P1_n28b | `P1_n28b_it02_s03` | 1,1369 | 42,67 | 0,00 | 2,00 |
| P2_n28b | `P2_n28b_it02_s03` | **1,0122** | 35,33 | 12,00 | 0,00 |

Cả ba đều `excluded`. Các file `rules/specs/{B2,P1,P2}_n28b_best.json` khớp nội dung với spec trong campaign (chỉ khác `spec_id`, `description`, `provenance`).

### 3.2 Phân bố trên các spec có điểm

| Phương pháp | n spec | S min / trung vị / max | Va chạm/h TB | Làn/h TB | Kẹt+nhường/h TB |
|---|---|---|---|---|---|
| B2_n28b | 8 | 1,1028 / 1,2755 / 1,3902 | 40,08 | 11,00 | 14,75 |
| P1_n28b | 8 | 1,1369 / 1,2238 / 1,3881 | 44,00 | 1,92 | 14,08 |
| P2_n28b | 7 | 1,0122 / 1,2340 / 1,2820 | 57,14 | 17,52 | 5,24 |

Quan sát (dữ kiện, chưa phải kết luận):
- S thấp nhất thuộc P2 (1,0122), nhưng trung vị S của P2 (1,2340) chỉ thấp hơn B2 (1,2755) và P1 (1,2238) rất ít. Chênh lệch ở mức best là một spec, 1 seed mỗi ngày.
- P2 có va chạm trung bình cao nhất (57,14/h) và va chạm trong làn cao nhất (17,52/h).
- P1 giữ va chạm trong làn thấp (TB 1,92/h; best 0,00/h) vì cấu trúc `B1_manual` không có lựa chọn đổi làn. Best của P1 không phải spec có va chạm ít nhất, vì R32 ưu tiên ít teleport kẹt/nhường trước.
- B2: best theo R32 (`t007`, S 1,2823, kẹt+nhường 0) khác best theo S thuần (`t001`, S 1,1028, kẹt+nhường 2,00/h). Vòng 1 cũng khác như vậy.

### 3.3 So với vòng 1

| Phương pháp | Best vòng 1 (S) | Best vòng 2 (S) | Ghi chú |
|---|---|---|---|
| B2 | `B2_n28_t000` 1,1602 | `B2_n28b_t007` 1,2823 | |
| P1 | `P1_n28_it02_s02` 1,0572 | `P1_n28b_it02_s03` 1,1369 | |
| P2 | `P2_n28_it02_s02` 0,9006 | `P2_n28b_it02_s03` 1,0122 | |

S của cả B0 và các best đều tăng ở vòng 2. Không so trực tiếp được vì mạng, routes, site và tập spec khác nhau (P2 vòng 2 có 7 spec). Bảng chỉ để tham khảo.

### 3.4 Độ hợp lệ của spec LLM và spec bị mất

- P1: 8/8 hợp lệ ngay lần đầu.
- P2: 5/8 hợp lệ ngay lần đầu, 8/8 sau retry, 8/11 tính theo lần thử. Ba spec lỗi (`it01_s01`, `it01_s02`, `it01_s03`) đều do `logic:1`: stand-in dùng `car_seeker` (custom2) trong khi mạng mới không còn lựa chọn nào cho nó. Lần retry `#a2` bỏ `car_seeker` thì hợp lệ.
- **Spec bị mất:** `P2_n28b_it01_s00` hợp lệ ở lần đầu nhưng có trạng thái `lost`: 3 run đã tính vào budget nhưng không có kết quả (không có pkl). Nguyên nhân khả dĩ nhất: tôi dừng nhầm tiến trình bằng `TaskStop` lúc P2 đang đánh giá (ghi ở `../PROGRESS.md`). Hệ quả: P2 có 7 spec, tổng chung 23 spec, budget vẫn 24/24. Chưa chạy lại spec này; nếu cần, phải chạy bổ sung ngoài budget và ghi rõ.

## 4. Video

File: `video_P2_n28b_best_PROXY_D1_seed1.mp4` (5999 khung, 299,9 s ở 20 fps, tốc độ x6, 1600x1138, 72 MB). Spec `P2_n28b_best` (= `P2_n28b_it02_s03`), PROXY_D1, seed 1, 0 đến 1800 s, sumo-gui 1.27.0. Số của run quay nằm ở `data/video_run_manifest.json`.

- **Run quay trùng run campaign** `P2_n28b_it02_s03` PROXY_D1 seed 1: 22 va chạm (làn 7, nút 15), 22 teleport do va chạm, 0 teleport kẹt/nhường, backlog chèn xe 0 (tối đa 2). Run vẫn `valid_strict` = false (22 teleport, 22 va chạm).
- Trong video: xe rẽ trái trái luật chờ giữa nút ở HDT_N và HDT_S (tối đa 20 xe cùng lúc, tích lũy 208); xe máy đi vỉa hè ở LVL_E và LVL_W (tích lũy 15, tối đa 3); xe đi thẳng chặn làn 0 (màu cyan) và xe rẽ phải kẹt phía sau (màu cam), nay xuất hiện nhiều: cùng lúc tối đa 62 xe chặn (53 đứng hẳn) và 68 xe bị chặn, tối đa 28 xe sau một xe chặn. Ở vòng 1 (có cọc) không có xe cam nào.
- Số "xe rẽ phải kẹt" này là đếm theo định nghĩa của vòng 2 (xe đi thẳng đứng dưới 5 km/h ở làn 0). Chưa so với chỉ tiêu vì `targets.yaml` chưa suy lại (mục 5, điểm 2).
- Màu làn 0: khung t = 540 s cho thấy dải làn 0 sát lề tô nhạt ở cả bốn nhánh, mặt đường vẫn đọc rõ. Tôi chỉ xem một khung; Viktor nên xem lại trên màn hình của mình.
- Lần quay đầu dùng nhầm sumo-gui 1.28.0 (biến môi trường `SUMO_HOME` của shell trỏ `~/sumo-venv`), cho 26 va chạm thay vì 22; đã bỏ và quay lại bằng 1.27.0 của `.venv`.

## 5. Việc cần Viktor xem và quyết

1. **B1 bỏ `car_seeker`** (`rules/specs/B1_manual.json`). Cấu trúc B1 do Viktor cố định ngày 27/10; không còn cọc thì custom2 không còn lựa chọn và validator (R27) loại mọi trial có p > 0. Hành vi B1 không đổi vì mọi p đều bằng 0.
2. **M9 lệch rất xa chỉ tiêu.** `right_lane_choice_prob` và `lane0_hold_s` trong `targets.yaml` được suy từ giả định có cọc ("merge back before the bollards"), không còn đúng với mạng làn 0 mở. Đến khi có nguồn hoặc định nghĩa mới, **không đọc điểm M9 vòng 2 như dấu hiệu hành vi sai**. Chưa sửa `targets.yaml`.
3. **Kiểu kẹt ô chờ HDT_S ở D1** (mục 2): chấp nhận (teleport tính vào R32) hay xử lý ở mạng?
4. **Đi thẳng từ làn 0 cạnh vỉa hè (LVL_W, LVL_E) là `g`, không phải `G`.** Để `G` cả hai thì SUMO cảnh báo "Unsafe green" và `test_validator` hỏng. HDT vẫn `G`.
5. **Trần R28 trên mạng mới** vẫn lấy từ mạng cũ (làn 4/h, nút 142/h): chưa đóng băng lại.
6. **Màu `#FFF3B0` của làn 0** trong sumo-gui: đã xem trong khung video (xem mục 4).

Còn nguyên từ vòng 1: đo sức chứa box HDT; thêm seed; backlog theo nhánh; mũi tên trái LVL chưa chấm ở M1 đến M3; patch D2/D3 chưa duyệt.

## 6. Tái lập

Từ `SUMO/`, dùng `.venv/bin/python`:

```bash
# B2
python -m thesis_sumo.baselines.optuna_search --structure rules/specs/B1_manual.json --campaign B2_n28b \
  --budget 24 --nproc 3 --site config/site.proxy.yaml --b0-lane-collisions 1.3333 --write-best rules/specs/B2_n28b_best.json
# P1 / P2 (hai vòng, mỗi vòng cần trả lời request ở experiments/llm_logs/<campaign>/requests/)
python -m thesis_sumo.llm.loop --campaign P1_n28b --mode params_only --base rules/specs/B1_manual.json --nproc 5 \
  --write-best rules/specs/P1_n28b_best.json --budget 24 --iters 2 --site config/site.proxy.yaml \
  --b0-lane-collisions 1.3333 --prompt-version v002
python -m thesis_sumo.llm.loop --campaign P2_n28b --mode full --nproc 3 \
  --write-best rules/specs/P2_n28b_best.json --budget 24 --iters 2 --site config/site.proxy.yaml \
  --b0-lane-collisions 1.3333 --prompt-version v002
```

Lệnh quay và dựng video: 
```bash
P=$PWD/SUMO/.venv/lib/python3.12/site-packages/sumo   # bắt buộc: SUMO_HOME của shell có thể trỏ bản 1.28
SUMO_HOME=$P PATH="$PWD/SUMO/.venv/bin:$PATH" xvfb-run -a -s "-screen 0 1920x1200x24" SUMO/.venv/bin/python \
  report/2026-10-28/scripts/record_video.py --spec-json SUMO/rules/specs/P2_n28b_best.json --day PROXY_D1 --seed 1 \
  --end 1800 --every 3 --out report/2026-10-28/v2/_rec
SUMO/.venv/bin/python report/2026-10-28/scripts/encode_video.py --rec report/2026-10-28/v2/_rec \
  --out report/2026-10-28/v2/video_P2_n28b_best_PROXY_D1_seed1.mp4 --fps 20
```.

## 7. Giới hạn và điều chưa kiểm

- 1 seed mỗi ngày, 3 ngày; không có khoảng tin cậy. Chênh lệch giữa các best nhỏ so với biến động giữa các ngày (va chạm của B0 theo ngày: 32, 24, 60/h).
- Dữ liệu quan sát là proxy; `targets.yaml` chưa suy lại cho mạng làn 0 mở.
- Spec P1/P2 do Claude Sonnet stand-in tạo từ phản hồi của vòng trước; không có LLM local trên máy này.
- Spec stand-in do subagent chỉ tự kiểm bằng mắt; validator của loop kiểm lại trước khi chạy (ba spec P2 vòng 1 bị loại ở bước này).
- Các file trong `data/` do subagent gom; tôi chỉ đối chiếu số best và B0/B1 với báo cáo của nó, chưa tính lại từng dòng từ pkl.
- Không sửa LaTeX và không chạy Task 15 trong ngày.
