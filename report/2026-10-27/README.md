# Báo cáo tiến độ — 27/10/2026

Repo `~/Projects/thesis-hust` (một repo, branch `master`), chạy trên **Linux** (Ubuntu 24.04, SUMO 1.27.0 trong `.venv`).

**Lưu ý chung:**
- Mọi số liệu là **proxy** (`LITERATURE_PROXY`, lấy từ tài liệu hoặc giả định), không phải số đo tại nút Lê Văn Lương × Hoàng Đạo Thúy.
- Máy Linux chưa có LLM chạy local. Mọi spec P1/P2 do **Claude Sonnet đóng vai LLM** (`provenance.model` = "claude-sonnet (stand-in)") sinh ra. Đây **không phải** kết quả của phương pháp LLM local.

## 0. Tóm tắt

- **Code:** đã xong toàn bộ, Task 10–14, cùng các hành vi F2 (làn rẽ phải liên tục, xe chặn làn rẽ phải, xe máy đi vỉa hè). Bộ test: 367 passed, 3 xfailed.
- **Ba campaign hiệu chỉnh** (ngân sách 36 run mỗi phương pháp; mỗi spec = 3 run trên PROXY_D1–D3, seed 1):
  - **B2 (Optuna):** xong 36/36, best = `B2_best.json`.
  - **P1, P2 (vòng LLM):** đã có kết quả 2/3 vòng (8 spec mỗi campaign). Vòng 3 đang chạy dở và **tạm dừng theo yêu cầu**: các process đang bị treo (SIGSTOP), chưa kill. `budget.json` đã trừ: P1 33/36, P2 27/36.
- **Phát hiện chính (tạm thời):** mô hình nền quá tải ở nhu cầu proxy 8180 xe/h (R42).
  - **Cả 28 spec + B0 + B1 đều bị loại** (teleport kẹt, backlog, va chạm junction 90–186/h).
  - So theo R32 (teleport kẹt/h, rồi S), **B2 và P1 chưa có spec nào hơn B0**. Chỉ một spec P2 (Sonnet stand-in) hơn B0 ở cả hai tiêu chí.
  - Mới có 1 seed mỗi ngày, nên **chưa kết luận được gì**.
- **LaTeX:** đã cập nhật bản tạm thời (chương 1, 3–6, tóm tắt, phụ lục A). Build sạch, 87 trang (mục 3).
- **Video demo 5 phút:** `video_B2_best_PROXY_D1_seed1.mp4` (mục 2).

## 1. Đã làm được tới đâu

### 1.1 Các commit từ 26/10 (đã push lên `origin/master` lúc 27/10 15:25)

| Commit | Nội dung |
|---|---|
| `0380530` | Chạy được trên cả Windows và Linux (`setup_env.py`, script operator dùng chung, theo dõi run record và ledger) |
| `94f29f4` | Task 10: hàm khoảng cách (W1/IQR, sai số tương đối, sàn nhiễu R, S có trọng số) |
| `7dc93ae` | R28: chạy lại B0 trên Linux, khớp với Windows từng run |
| `a8385e5` | F2-net: làn rẽ phải liên tục (lane 0, cọc phân cách), `custom2` = ô tô vi phạm |
| `cf4f55f` | Phase 3A–3D: thử khả thi chặn làn rẽ phải, vỉa hè, đi ngược chiều, chờ giữa nút |
| `f557c2c` | F2-behaviours: đoạn cọc 30 m, vỉa hè LVL_W, luật `queue_space_seeking` |
| `8acc85c` | F2-metrics: M9 (chặn làn rẽ phải), M10 (vỉa hè) |
| `cfd86ba` | R28 đóng băng trên mạng F2: va chạm lane 4/h, junction 142/h |
| `d24a13b` | Task 11: harness đánh giá, ngân sách khóa theo campaign, `select_best` |
| `481ea06` | Task 12: LLM client (openai + stand-in qua file), prompt v001, feedback chặn rò dữ liệu ngày validation |
| `ccb7520` | Task 14: Optuna B2/H trên cấu trúc cố định |
| `81a9362` | Task 13: vòng lặp LLM chạy tiếp được sau khi ngắt (P1 params_only / P2 full) |
| `85df4c8` | Run record của campaign B2, P1, P2 + log Sonnet stand-in |

### 1.2 Trạng thái theo PLAN

| Hạng mục | Trạng thái |
|---|---|
| Task 1–14 (code) | ✅ |
| F2: làn rẽ phải liên tục, chặn làn rẽ phải, vỉa hè | ✅ |
| F2: đi ngược chiều | ⏸ Hoãn (R38): SUMO không mô phỏng được đáng tin (Phase 3C) |
| Campaign B2 | ✅ 36/36 |
| Campaign P1, P2 | ⏸ 2/3 vòng có kết quả; vòng 3 tạm dừng |
| Campaign H (Optuna trên cấu trúc P2_best) | ⏳ cần P2 xong |
| Task 15: benchmark D4–D5, ≥ 20 seed, E1/E2 | ⏳ |
| LaTeX | 🔄 bản tạm thời |
| Video demo | ✅ bản tạm thời (spec B2_best) |

### 1.3 Kết quả tạm thời của các campaign

Nguồn:
- `data/campaign_specs.csv`: mỗi spec một dòng, trích từ `SUMO/experiments/campaigns/<c>/…/*.pkl`.
- `data/B2_convergence.csv`.
- `data/REF_B0_B1.txt`: B0 và B1 chấm cùng cách, script `SUMO/experiments/operator/ref/eval_ref.py`.

S là trung bình có trọng số của R = khoảng cách sim–quan sát chia cho dao động giữa các ngày. **Càng thấp càng tốt**; S ≈ 1 nghĩa là sai lệch ngang dao động tự nhiên giữa các ngày.

| | Số spec | S nhỏ nhất / trung vị / lớn nhất | Va chạm tổng /h | Va chạm lane /h | Teleport kẹt+yield /h | Best theo R32 |
|---|---|---|---|---|---|---|
| B0 (vType mặc định, không luật) | 1 | 1,181 | 112,7 | 2,0 | 10,7 | — |
| B1 (luật thủ công, F2 p = 0) | 1 | 1,216 | 107,3 | 0,0 | 45,3 | — |
| B2 (Optuna, cấu trúc B1) | 12 | 1,182 / 1,329 / 1,523 | 90,7–168,0 | 2,0–46,0 | 12,0–76,7 | `B2_t010`: 12,0/h, S 1,374 |
| P1 (Sonnet, chỉ tham số, cấu trúc B1) | 8 | 1,159 / 1,188 / 1,262 | 93,3–146,0 | 0,0–1,3 | 24,0–54,0 | `P1_it02_s00`: 24,0/h, S 1,167 |
| P2 (Sonnet, cấu trúc + tham số) | 8 | 1,047 / 1,201 / 1,299 | 136,7–186,0 | 6,0–21,3 | 7,3–30,0 | `P2_it02_s03`: 7,3/h, S 1,084 |

Nhận xét:
- **Không spec nào đủ điều kiện** (ELIGIBLE) vì mạng quá tải. Best được chọn theo R32 (R42): ít teleport kẹt/yield nhất, rồi đến S.
- **B2:** best theo R32 (`B2_t010`) có S **kém hơn B0**. Spec có S thấp nhất (`B2_t007`, S 1,182) chỉ ngang B0.
- **P1:** S thấp hơn B0 một chút (1,159–1,167), và va chạm lane gần 0, nhưng teleport kẹt gấp 2–5 lần B0.
- **P2:** có S thấp nhất (1,047) và `P2_it02_s03` hơn B0 ở cả teleport lẫn S. Đổi lại, va chạm tổng cao hơn B0 (137–186/h so với 113/h).
- **Tỉ lệ spec hợp lệ:**
  - P1: 8/8 ngay lần đầu.
  - P2: vòng 1 chỉ 1/4 hợp lệ ở lần đầu (lỗi logic `lcPushy` + `lcPushyGap`), cả 4 sửa được ở lần thử 2. Tính theo lần trả lời là 8/11.
- **Hạn chế:** 1 seed mỗi ngày, P1/P2 chưa xong, LLM là stand-in, mô hình nền quá tải. Đây chỉ là chỉ báo, **không phải** kết quả E1/E2.

## 2. Video demo

`video_B2_best_PROXY_D1_seed1.mp4`: 5:00, 1600×900, 20 fps, tốc độ ×6. Ghi bằng sumo-gui trên Xvfb, mô phỏng 0–1800 s (07:30–08:00).

- **Spec:** `B2_best`, best của phương pháp duy nhất đã chạy xong. Ngày PROXY_D1, seed 1, check-junctions BẬT.
- **Luật TraCI:** chạy đúng như batch run (cùng `make_controller`, seed, bán kính). Recorder chỉ đọc trạng thái, tô màu và chụp ảnh.

**Màu xe và overlay:**

| Màu | Ý nghĩa | Overlay |
|---|---|---|
| xanh dương / vàng | ô tô / xe máy | — |
| tím | xe rẽ trái trái luật đang đi | — |
| **đỏ** | xe rẽ trái trái luật **đang chờ giữa nút** (trên chuỗi làn nội bộ của lượt rẽ trái bị cấm) | số đang chờ / tích lũy |
| **cyan** | xe **đi thẳng chặn làn rẽ phải** (đứng trên lane 0 trong 80 m trước vạch dừng, cùng phạm vi với M9) | số đang chặn (đang dừng) / tích lũy |
| **cam** | xe rẽ phải **bị kẹt sau xe chặn** (đang dừng, phía sau xe cyan gần nhất) | tổng đang kẹt; nhãn **"+k"** cạnh từng xe chặn = số xe kẹt sau nó |
| **trắng** | xe máy **đi trên vỉa hè** (LVL_W) | số đang có / tích lũy |
| — | **đi ngược chiều** | ghi rõ "KHÔNG mô phỏng (hoãn, R38)" |

Overlay còn có: đồng hồ, pha đèn kèm giây trong chu kỳ, số xe trong mạng, số xe chờ chèn, số xe dừng ở 4 nhánh, va chạm và teleport tích lũy, nhãn "VA CHẠM" hiện 2 s sau mỗi va chạm.

**Kết quả run quay video:** nguồn `data/video_run_manifest.json` và `_rec/frames/frames.json`.

| | Giá trị |
|---|---|
| Va chạm | 85 (55 trong nút: 51 `junction` + 4 `side`; 30 `side` trên làn) |
| Teleport | 92 (7 không do va chạm) |
| Backlog xe chờ chèn lúc 1800 s | 471 (quá tải, R42) |
| Rẽ trái trái luật chờ giữa nút | tích lũy 88 xe, đồng thời tối đa 10, trung bình 2,6 |
| Xe đi thẳng chặn làn rẽ phải | tích lũy 449 xe, đồng thời tối đa 34, trung bình 18,7 |
| Xe rẽ phải kẹt sau xe chặn | đồng thời tối đa 156, trung bình 42,8; một xe chặn có tối đa 78 xe kẹt phía sau |
| Xe máy trên vỉa hè | tích lũy 20 xe, đồng thời tối đa 7 |
| Thời gian quay | 1434 s cho 1800 s mô phỏng |

Lý do có nhiều xe chặn: `B2_best` có 81 % xe `seeker` với `p_right_lane` 0,42. Đây là giá trị Optuna chọn, không phải số đo.

Sau run, bước chuyển đầu ra sang lược đồ quan sát báo lỗi vì `detectors.xml` của run GUI bị hỏng một dòng (dòng 239, t ≈ 44 s). Video không dùng bảng này: mọi số ở trên lấy từ manifest và TraCI. Chưa tìm nguyên nhân.

**Tái tạo (từ thư mục gốc repo):**
```bash
xvfb-run -a -s "-screen 0 1920x1200x24" SUMO/.venv/bin/python report/2026-10-27/scripts/record_video.py \
    --spec-json SUMO/rules/specs/B2_best.json --day PROXY_D1 --seed 1 --end 1800 --every 3 --out report/2026-10-27/_rec
SUMO/.venv/bin/python report/2026-10-27/scripts/encode_video.py --rec report/2026-10-27/_rec \
    --out report/2026-10-27/video_B2_best_PROXY_D1_seed1.mp4 --fps 20
```
Thư mục `_rec/` (khoảng 6000 PNG) không commit.

Hai script là bản Linux của `report/2026-10-26/scripts/`:
- bỏ `ctypes.windll` (watchdog Win32);
- font DejaVu thay Segoe UI;
- gọi `ffmpeg` hệ thống thay `imageio-ffmpeg`;
- chạy kèm controller TraCI của spec.

## 3. LaTeX (bản tạm thời, chưa commit)

Đã sửa `Latex/Chuong/`:
- tóm tắt VN/EN;
- chương 1: phạm vi F1/F2/F3; đi ngược chiều hoãn;
- chương 3: mạng F2, `queue_space_seeking`, M9/M10, hàm khoảng cách và S, vòng LLM, B0–H, ngân sách R44/R45, R32;
- chương 4: gói `evaluate`/`llm`/`baselines`, Phase 3A–3D, bảng R28 trên mạng F2, mục **kết quả tạm thời** với bảng 28 spec + B0/B1;
- chương 5: thêm 5.6 (khả thi F2) và 5.7 (khung so sánh công bằng LLM và Optuna);
- chương 6;
- phụ lục A: spec B1 cập nhật theo `B1_manual.json`.

Build `latexmk -pdf`: 87 trang, 0 lỗi, 0 tham chiếu thiếu.

Luận văn ghi rõ: P1/P2 do Sonnet stand-in sinh, dữ liệu là proxy, chưa có kết luận "LLM hơn Optuna".

**TODO còn trong LaTeX:**
- Kết quả và mô hình:
  - LLM local (model, quant, temperature) và chạy lại P1/P2;
  - phiên bản Sonnet đã dùng làm stand-in;
  - kết quả H, E1, E2;
  - câu kết luận chính.
- Quyết định R35.
- Thông tin bổ sung:
  - cấu hình máy, phiên bản thư viện đã cài;
  - hình chụp sumo-gui;
  - trích dẫn TCVN 13592:2022 và tiêu chuẩn đèn.
- Phần chưa sửa: chương 2 và phụ lục B. Phụ lục B vẫn ghi 7 bảng quan sát, nay code đã có 10.

## 4. Việc tiếp theo

1. **Chạy tiếp P1/P2 vòng 3** (khi Viktor cho chạy): `kill -CONT` các process đang treo, bật lại script giám sát và lịch nhắc mỗi giờ. Sonnet trả lời các request mới.
   - Theo R45: chạy thêm vòng nếu còn ngân sách, tối đa 5 vòng.
   - Xong thì ghi `P1_best.json` và `P2_best.json` (`--write-best`).
2. **Campaign H:** Optuna trên cấu trúc của `P2_best`, 36 run (khoảng 3 h máy).
3. **Task 15 — benchmark:**
   - chạy B0, B1, B2, P1, P2, H trên ngày validation PROXY_D4–D5 với ≥ 20 seed (`allow_validation=True`);
   - E1 = P1 so với B2; E2 = B2 so với H so với P2;
   - thống kê Mann–Whitney + Holm + Cliff's delta;
   - vẽ hình, viết `results/`, `policy/evaluate.py` nếu kịp;
   - implement → review → commit.
4. **LaTeX bản cuối** với kết quả Task 15: điền TODO, sửa chương 2 và phụ lục B, build lại.
5. **Video bản cuối** với spec tốt nhất sau benchmark. Nếu cần, quay thêm một video zoom gần vào LVL_W (vỉa hè và xe chặn làn rẽ phải), vì ở khung 200 m xe máy khá nhỏ.
6. **Xoá lịch nhắc** tự động và báo Viktor khi xong hết.

## 5. Cần Viktor quyết / lưu ý

- **Mô hình nền quá tải (R42):** mọi spec đều bị loại, best chọn theo R32.
  - Nếu muốn có spec đủ điều kiện thật thì phải đổi nhu cầu proxy hoặc ngưỡng backlog. Hiện đang giữ nguyên theo quyết định "Giữ nguyên, dùng R32".
- **Xác nhận các ruling:** R35 (làm mượt sai số của tỉ lệ nhỏ), R36 (trọng số đều), R43 (M9c/M10b chỉ báo cáo), R44 (36 run = 12 spec × 3 ngày × 1 seed), R45 (chạy tới hết ngân sách, tối đa 5 vòng).
- **[S5]:** mẫu số của tỉ lệ vi phạm HDT khi có rẽ phải liên tục.
- **LLM local:** máy này tạm dùng Sonnet. Khi có Ollama, cần chạy lại P1/P2 để có kết quả thật của phương pháp.
- **Va chạm junction cao** ở mọi spec (90–186/h, B0 113/h; ngưỡng đóng băng 142/h). Ở run quay video, 55/85 va chạm nằm trong nút.
