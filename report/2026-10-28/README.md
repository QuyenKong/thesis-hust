# Báo cáo tiến độ — 28/10/2026

Repo `~/Projects/thesis-hust` (branch `master`), chạy trên **Linux** (SUMO 1.27.0 trong `.venv`). Mọi thay đổi trong ngày **chưa commit** (working tree bẩn so với `685b4fe`).

**Lưu ý chung:**
- Mọi số liệu là **proxy** (`LITERATURE_PROXY`, lấy từ tài liệu hoặc giả định), không phải số đo tại nút Lê Văn Lương × Hoàng Đạo Thúy.
- Máy Linux chưa có LLM chạy local. Mọi spec P1/P2 do **Claude Sonnet đóng vai LLM** (`provenance.model` = "claude-sonnet (stand-in)") sinh ra. Đây **không phải** kết quả của phương pháp LLM local.
- Mỗi spec chạy 3 ngày PROXY_D1–D3 × **1 seed**, mỗi run 1800 s. Đây là kết quả hiệu chỉnh, **chưa phải** benchmark (Task 15). PROXY_D4/D5 không được dùng.
- Manifest của các run ghi commit `685b4fe` kèm `git_dirty` = true: code chạy là working tree chưa commit, nên chưa tái lập được chỉ từ commit.

## 0. Tóm tắt

- **Kịch bản đổi theo thông tin hiện trường của Viktor** (`config/site.proxy.yaml`):
  - rẽ trái bị cấm từ HDT_N và HDT_S (xe vi phạm chờ giữa nút ở HDT); rẽ trái và quay đầu từ LVL_W, LVL_E hợp lệ, có mũi tên riêng;
  - đèn 3 pha (LVL_straight 42 s, LVL_left 16 s, HDT_green 44 s, mỗi pha thêm vàng 4 s và đỏ toàn phần 2 s, chu kỳ 120 s; thời lượng là giả định);
  - thêm vỉa hè thứ hai ở LVL_E.

  Mọi thứ dựng trên mạng cũ (routes, PROXY_D1–D5, B0/B1, campaign, video) đã làm lại.
- **Code** (mục 1): sửa proxy generator, metrics, runtime/rules, LLM/Optuna cho kịch bản mới. Sửa thêm hai lỗi mô hình mạng phát hiện khi chạy thử: xe đi thẳng đâm xe chờ giữa nút ở HDT, và kẹt cứng ở cửa ra vỉa hè. Review độc lập: không BLOCKER, 2 MAJOR (đã xử lý), 8 MINOR. Bộ test: 381 passed, 2 xfailed (chạy lại lúc viết report).
- **B0 trên mạng mới** (mục 2): va chạm 34,7/h (mạng cũ 112,7/h), không còn teleport kẹt/nhường, S 1,124 (cũ 1,181). Nhu cầu và site cũng đổi, nên mức giảm không quy hết cho patch mạng.
- **Campaign `_n28`** (mục 3), mỗi phương pháp 24 run (B2 8 trial; P1, P2 mỗi cái 2 vòng × 4 spec):
  - **Không spec nào đủ điều kiện** (24/24 excluded). Best chọn theo R32.
  - Best chung là `P2_n28_it02_s02`: không teleport kẹt/nhường, S 0,901 (B0 1,124). Đổi lại, va chạm 58,7/h và va chạm lane 6,0/h đều **cao hơn B0** (34,7 và 2,7), vượt trần R10 (3,67/h).
  - 1 seed mỗi ngày, LLM là stand-in, nên **chưa kết luận được gì** về LLM so với Optuna.
- **Video** (mục 4): `video_P2_n28_best_PROXY_D1_seed1.mp4`, 5 phút, spec `P2_n28_best`, PROXY_D1, seed 1. Kết quả run quay trùng với run chiến dịch. Trong cả video không có xe rẽ phải nào bị kẹt sau xe chặn (không có màu cam).
- **Điều phối** (mục 5): 0 lần chạm usage limit. Mất khoảng 3 giờ 40 phút do phiên điều phối chính khởi động lại.

## 1. Đã làm gì

### 1.1 Thứ tự bước

PLAN ngày gồm: 1 mạng và demand → 2 sửa code → 3 dữ liệu proxy → 4 B0/B1 → 5 campaign → 6 video.

Bước 1 dừng giữa chừng:
- `build_demand` lỗi vì `data/observed/*/turn_counts.csv` còn theo mạng cũ;
- `proxy/generate.py` lỗi trên site mới (`ValueError` high − low < 0 trong `arrivals()`).

Thứ tự thực tế: sửa code (bước 2) → sinh proxy (bước 3) → sinh demand. Đây là quyết định tự chọn, ghi ở mục 7.

### 1.2 Code đã sửa ở bước 2

Test viết trước (theo báo cáo các subagent). Đường dẫn tính từ `SUMO/src/thesis_sumo/`.

**A. Proxy generator, metrics, chỉ tiêu**

| Chỗ sửa | Nội dung |
|---|---|
| `proxy/generate.py` `arrivals()` (dòng 382) | Lỗi high − low < 0: chu kỳ illegal-left đầu tiên của HDT kết thúc trước khi xe sớm nhất tới vạch. Nay bỏ qua chu kỳ đó. |
| `proxy/generate.py` thứ tự phục vụ | Mỗi nhánh phục vụ một lần (trước đó HDT_N/HDT_S bị phục vụ hai lần). |
| `proxy/generate.py` `movement_segments()` (226), `own_heads()` (246) | Đèn 3 pha: rẽ trái LVL phục vụ theo chu kỳ riêng (pha LVL_left). |
| `proxy/generate.py` khác | M7c cộng số xe chờ của mọi box. `signal_state_at_t` là trạng thái liên kết của chính xe (rẽ phải làn liên tục luôn G). Xe đi làn rẽ phải chỉ sinh ở nhánh có `continuous_right_lane`. |
| `metrics/common.py` `own_head_movements()` (200), `own_head_tracks()` (213); `m1_headway.py`, `m2_early_start.py`, `m3_red_running.py` | M1–M3 bỏ xe thuộc đầu đèn riêng: `signal_events` chỉ có nhóm đi thẳng, không có onset của mũi tên. Rẽ trái LVL không được chấm ở M1–M3, ở cả sim và proxy. |
| `metrics/m7_illegal_left.py` | M7c lấy tổng `n_waiting_in_box` của hai box HDT. |
| `data/proxy/targets.yaml` | Xem bên dưới. |

Thay đổi trong `data/proxy/targets.yaml` (đã kiểm bằng `git diff`):
- `n_waiting_in_box` = 6: áp cho từng box HDT. Đây là chỉ tiêu cũ của LVL_W, ghi "not re-derived".
- `crossing_start_delay_per_waiter_s` = 0,3 s/xe, cộng số xe chờ của hai box.
- `sidewalk_choice_prob` = 0,03: áp nguyên cho LVL_E ("not re-derived").
- `path_length_m` tính lại từ mạng mới: {s 41,6; r 13,5; l 42,3; u 15,4; illegal_l 43,4} (cũ {40,6; 13,1; 40,9; 15,9; 36,5}).
- Đơn vị của `early_start_share` và `red_run_share` ghi "straight head only".

Không có số đo mới nào được thêm.

Test: `test_left_arrow_movements_not_classified_on_the_straight_head`, `test_m7_two_illegal_left_approaches` (`tests/test_metrics.py`), test M10 cho hai vỉa hè, `test_three_stages_and_two_illegal_left_approaches` (`tests/test_proxy.py`). Các test box/M7 cũ chuyển từ LVL_W sang HDT_N/HDT_S.

**B. Runtime, rules, sim**

Lỗi giả định cũ lớn nhất: trạng thái đèn của xe lấy theo nhóm đèn đi thẳng của nhánh, nên rẽ trái LVL trong pha mũi tên bị tính là vượt đỏ. Nay mỗi xe xét theo liên kết TLS của chính làn nó đi.

| Chỗ sửa | Nội dung |
|---|---|
| `runtime/state.py` `JunctionInfo.link_of_internal` (dòng 96) | Bảng làn nội bộ → chỉ số liên kết TLS. |
| `runtime/state.py` `Step.signal()` (282), `Step.red_id_of()` (286), `crossings` (369) | Trạng thái đèn và bộ đếm chuyển đỏ theo liên kết. |
| `runtime/rules/base.py` `Rule.link_of()` (168) | Liên kết của xe, cache một lần `getRoute` mỗi xe. |
| `runtime/rules/early_start.py`, `swarm_red_running.py` | Dùng liên kết của chính xe. |
| `runtime/rules/queue_space_seeking.py` | Chỉ đo headway khi nhóm đèn của nhánh đang G. |
| `sim/outputs.py` `crossing_states()` (540) | `signal_state_at_t` theo liên kết của xe. |
| `sim/outputs.py` `check_shared_green()` (404) | Chỉ báo lỗi khi hai nhánh HDT đều từng xanh nhưng không bao giờ xanh cùng lúc. |

Chỉ sửa chữ (không đổi hành vi):
- `rules/schema.py:157`, docstring `illegal_left_box.py` và `state.py`;
- `rules/specs/B0.json`, comment trong `rules/compiled/B0/vtypes.add.xml`;
- `schema_observed.py` (docstring);
- comment `fcd_radius_m` trong `config/experiment.yaml`, help text `--b0-lane-collisions` trong `baselines/optuna_search.py`.

`B1_manual.json` không đổi (luật không gắn nhánh). `B2_best.json` của campaign cũ không đụng.

Test: `test_swarm_uses_own_link_signal`, `test_early_start_waits_for_own_link_green`, `test_junction_info_on_proxy_net` (cập nhật; `tests/test_runtime.py`), `test_crossing_state_is_own_link`, `test_shared_green_check_needs_both_greens` (`tests/test_runner.py`).

**C. LLM và Optuna**

- Prompt `llm/prompts/v002/` mô tả kịch bản 28/10: 3 pha, rẽ trái bị cấm ở HDT, hai vỉa hè, làn rẽ phải liên tục ở mọi nhánh. Không có số mới, không nhắc tới ngày dữ liệu. `v001` giữ nguyên, vẫn tải được.
- `config/llm.yaml`: `prompt_version: v002`. `llm/loop.py` có cờ `--prompt-version`, khoá theo campaign trong `loop.json`.
- `llm/client.py`: báo lỗi nếu thiếu thư mục prompt.
- `llm/feedback.py` `_site_text()` (dòng 70): in hướng xanh của từng pha.
- Campaign id tách theo thư mục (`budget.json`, `loop/`, `study.journal`).
- Test: `test_v002_context_describes_28_10_scenario`, `test_feedback_lists_every_per_approach_metric` (`tests/test_llm.py`), `test_new_campaign_id_has_own_budget_and_state`, `test_prompt_version_default_override_and_lock` (`tests/test_loop.py`).

**D2 và D3. Hai lỗi kịch bản phát hiện sau khi sửa code** (Opus debug; sửa trong `net/apply_patches.py`)

*D2 — xe chờ giữa nút ở HDT bị xe đi thẳng đối diện đâm.*
- Nguyên nhân: netconvert đặt điểm chờ (internal junction) với giả định xe rộng 1,8 m. Xe máy chờ ở mép làn (theo báo cáo subagent: posLat +1,3 m trên làn 3,5 m) nằm lấn vào làn đi thẳng đối diện đang xanh cùng pha. SUMO coi xe trước điểm chờ là ngoài vùng xung đột, nên xe đi thẳng không phanh. Mạng cũ không gặp lỗi này vì khi đó dòng cắt ngang đang đỏ lúc xe chờ.
- Sửa: thêm một pass netconvert cuối với `--internal-junctions.vehicle-width` = bề rộng làn nội bộ (3,5 m; `build_site_net`, dòng 570). `_box_pins()` (dòng 394) ghim mọi internal junction khác về vị trí mặc định bằng `contPos` (file mới `scenario/net/patches/site.proxy/box_pins.con.xml`). Kết quả: chỉ điểm chờ illegal-left dời (theo báo cáo subagent: 22,56/22,75 → 19,96/20,38 m).
- Đã thử và loại: vehicle-width 3,5 m cho toàn mạng (62 va chạm, vì dời cả điểm chờ quay đầu ở HDT); chỉ `contPos` trên hai liên kết (xe kẹt, 5–6 teleport/run). Hai số này theo báo cáo subagent, chưa đối chiếu.
- Test: `test_box_waiting_point_clear_of_concurrent_foes` (`tests/test_net.py`).

Số trước → sau, PROXY_D1, 1800 s, seed 1/2/3 (đã đối chiếu với `/tmp/d2/{base,vwut}_*.txt`, trừ dòng ghi chú):

| | B0 | B1_manual |
|---|---|---|
| Va chạm | 32/22/48 → 11/29/17 | 17/29/28 → 16/10/17 |
| Teleport không do va chạm | 0/0/0 → 0/0/2 | 17/27/17 → 3/3/0 |
| Backlog cuối | 71/84/130 → 142/100/181 | 768/721/595 → 395/534/474 |
| Xe đối diện đâm xe chờ | 14/10/27 → 0/0/0 (theo báo cáo subagent, chưa đối chiếu) | — |

Backlog B0 tăng vì box chứa ít xe chờ hơn (giải thích của subagent).

Còn lại (theo báo cáo subagent):
- 7–12 va chạm/run giữa xe cùng làn 2 ở HDT (đi thẳng, rẽ trái, quay đầu chung làn). Mô hình sublane không ngăn chồng lấn trên các làn nội bộ cách nhau dưới 3,5 m trong 10–20 m đầu. Mạng cũ cũng có hiện tượng này (`:J_18_0`, 5–7/run).
- LVL_E left nhường LVL_W left (xem MAJOR-1).
- Chưa kiểm PROXY_D2–D5 và sức chứa box.

*D3 — kẹt cứng ở cửa ra vỉa hè LVL_E/LVL_W.*
- Hiện tượng: với spec thử `p_sidewalk` 0,6, từ khoảng 840 s xe vỉa hè đứng cuối vỉa hè và xe rẽ phải làn 0 đứng ở vạch, cả hai không nhúc nhích quá 55 s.
- Nguyên nhân: liên kết rẽ phải từ vỉa hè và liên kết đi thẳng HDT cắt ngang (cùng đổ vào một cạnh ra) nhường nhau cả hai chiều. Tình huống này kích hoạt khi `swarm_red_running` cho xe HDT vượt đỏ (speedMode 15) chờ khe hở. Mạng cũ (chỉ vỉa hè LVL_W) đã có cặp tương tự.
- Sửa: `_sidewalk_patches()` (dòng 336) thêm `<prohibition>`:
  - dòng HDT đi thẳng không còn nhường người đi vỉa hè;
  - người đi vỉa hè vẫn nhường HDT;
  - xe làn 0 vẫn nhường vỉa hè.

  `_check_site_net()` (dòng 432) kiểm điều này. Hai dòng `<prohibition>` mới nằm trong `scenario/net/patches/site.proxy/sidewalk.con.xml`. Test: `test_sidewalk_right_yields_one_way` (`tests/test_net.py`).
- Số trước → sau (theo báo cáo subagent, chưa đối chiếu; `/tmp/d3` không còn run record). B1_probe `p_sidewalk` 0,6, seed 1, 1800 s, trên mạng đã sửa D2:
  - teleport 28 → 13 (jam 8 → 0, yield 9 → 1);
  - xe làn 0 chờ quá 55 s: E 39 → 1, W 54 → 10;
  - thời gian chờ lâu nhất ở làn 0: E 348 → 74 s, W 411 → 178 s.

  B0/B1 (không ai đi vỉa hè) giống hệt trước và sau.
- Còn lại:
  - xe làn 0 LVL_W chờ tới 178 s ("đói lượt");
  - các cặp nhường lẫn nhau (12,26), (1,26), (12,15) liên quan box HDT chưa xử lý;
  - luật `right_lane`: xe đi thẳng nằm lại làn 0 của đoạn `.mid` chặn xe rẽ phải.

Mạng build lại bằng `python -m thesis_sumo.net.build --site config/site.proxy.yaml`:
- đổi `base.net.xml` (chỉ header), `diagram.svg`, `patches/site.proxy/sidewalk.con.xml`, `site.proxy.net.xml`;
- thêm `patches/site.proxy/box_pins.con.xml`.

### 1.3 Review độc lập (Opus, chỉ đọc)

Không BLOCKER, 2 MAJOR, 8 MINOR. Nội dung review theo báo cáo của reviewer; phần sửa đã kiểm bằng `git diff`.

- **MAJOR-1:** docstring ghi sai hướng nhường. Thực tế LVL_E left (link 4) nhường LVL_W left (link 16). Mạng cũ không có quan hệ xung đột giữa hai link này; đây là tác dụng phụ của vehicle-width ở D2. **Đã sửa docstring.** Chưa đo độ trễ rẽ trái W so với E, nên M5/M1/M6 ở LVL_E có thể lệch vì mạng chứ không vì hành vi.
- **MAJOR-2:** `illegal_left.mode_source` trong `site.proxy.yaml` ghi đã kiểm sức chứa box, nhưng repo không có bằng chứng. **Đã viết lại:** chỉ kiểm va chạm; sức chứa box HDT chưa đo; chỉ tiêu M7 p90 = 10/box có thể không đạt ở chế độ native (`TODO_DECIDE`).
- **MINOR đã xử lý:**
  - test M7c: thay kiểm intercept (ngoại suy xa, nhiễu) bằng kiểm mean(y) − β·mean(x) ≈ d0;
  - `docs/WORKFLOW.md`: bỏ "LVL_green 64 s", ghi 3 pha.
- **MINOR còn lại:**
  - `targets.yaml` M2/M3: mẫu số "straight head" chưa có transfer note;
  - `swarm_red_running` đếm n theo nhánh, trong khi vượt đỏ xét theo liên kết;
  - `_realised` (khoảng cách split) không kiểm lại sau pass netconvert cuối;
  - thiếu test cho việc `box_pins` giữ nguyên các internal junction khác, và cho quan hệ nhường LVL-left;
  - `supervise_llm.sh` cũ hard-code P1/P2 (đã có `supervise_llm_n28.sh`).
- **Xfail của test proxy:**
  - bỏ xfail strict "LVL_W red" (nay lệch −6,9 %);
  - giữ 2 xfail cho ô tô: reviewer chạy thêm 20 ngày, không thấy thiên lệch; mức +49 % trên D1–D5 là nhiễu.
- **Reviewer đã kiểm** (chưa đối chiếu lại):
  - `path_length_m` tính lại từ net khớp chính xác;
  - `junction_geometry` trên net mới đúng cho HDT_N/HDT_S;
  - M2/M3 xe máy nằm trong ±7 % chỉ tiêu;
  - prompt v002 khớp file site.

### 1.4 Dữ liệu proxy, demand, test (bước 3)

Lệnh (cwd `SUMO/`):
```bash
.venv/bin/python -c "from thesis_sumo.demand.build_demand import build_candidate_routes; build_candidate_routes('scenario/net/site.proxy.net.xml','scenario/demand/candidate_routes.rou.xml')"
.venv/bin/python -m thesis_sumo.proxy.generate          # 5 ngày + routes_PROXY_D1..D5
.venv/bin/python -m thesis_sumo.rules.compiler rules/specs/B1_manual.json --site config/site.proxy.yaml
```

- `build_candidate_routes` phải chạy trước `proxy.generate` (generate không tự sinh candidate).
- Sau khi sửa chữ trong `site.proxy.yaml` (MAJOR-2), proxy được sinh lại. CSV và routes y hệt; `site_sha256` trong manifest = `6a293a17…`, khớp file hiện tại.
- Compile `B1_manual`: nội dung không đổi. B0 là vType viết tay, compiler từ chối (đúng thiết kế).
- Demand dùng vType `car`, `moto`, `moto_violator`. Không có route vào vỉa hè: xe đi vỉa hè được điều khiển bằng TraCI.
- Routes PROXY_D1 có 416 xe `moto_violator` (đã đếm), toàn rẽ trái trái luật từ HDT (theo báo cáo: HDT_N 203, HDT_S 213). HDT không có rẽ trái hợp lệ; LVL_W/LVL_E có `l` và `u` cho ô tô và xe máy.
- `SYNTHETIC`: không có script sinh. Công thức trong `docs/SYNTHETIC_README.md` tái tạo đúng file cũ (0/124 ô sai). File được sinh lại bằng công thức đó, với split "illegal" chuyển từ LVL_W sang HDT_N/HDT_S. Sau đó chạy `build_demand --seed 1`. README SYNTHETIC đã cập nhật.

**Test:**
- Sau bước 3 (log điều phối viên): 381 passed, 2 xfailed, 0 failed (113 s).
- Chạy lại lúc viết report (`cd SUMO && .venv/bin/python -m pytest -q -p no:cacheprovider`, trong khi sumo-gui quay video chạy nền): **381 passed, 2 xfailed, 0 failed** (118 s).

## 2. Mạng cũ và mạng mới (bước 4)

Nguồn:
- `data/REF_B0_B1.txt` (bảng từng ngày);
- `SUMO/experiments/campaigns/{REF,REF_n28}/{B0,B1_manual}.pkl` và `manifest.json` của từng run.

Đã tính lại toàn bộ từ pkl và manifest; khớp file. Script `SUMO/experiments/operator/ref/eval_ref_n28.py` là bản sao của `eval_ref.py`, chỉ đổi id campaign. PROXY_D1–D3, seed 1, 1800 s; tỉ lệ /h = tổng 3 run / 1,5 h.

| | B0 cũ | B0 mới | B1_manual cũ | B1_manual mới |
|---|---|---|---|---|
| Va chạm tổng /h | 112,7 | 34,7 | 107,3 | 41,3 |
| Va chạm lane /h | 2,0 | 2,7 | 0,0 | 0,0 |
| Va chạm junction /h | 110,7 | 32,0 | 107,3 | 41,3 |
| Teleport kẹt+nhường /h | 10,7 | 0,0 | 45,3 | 24,0 |
| Teleport do va chạm /h | 112,7 | 34,7 | 107,3 | 41,3 |
| Backlog cuối, TB/run | 113 | 47 | 353 | 409 |
| S | 1,181 | 1,124 | 1,216 | 1,198 |
| Ngày đủ điều kiện | 1/3 | 2/3 | 0/3 | 0/3 |
| Eligibility (cả spec) | excluded | excluded | excluded | excluded |

Lý do bị loại trên mạng mới:
- **B0:** chỉ PROXY_D1 bị loại (backlog 142 > 0; va chạm lane 6/h > trần 4/h). D2, D3 đạt.
- **B1_manual:** cả 3 ngày bị loại, đều vì teleport không do va chạm, backlog, và trượt cổng GEH (0,800 / 0,833 / 0,783 < 0,85). D2 có thêm 2 va chạm với xe đang bị TraCI can thiệp (> 1).

Giá trị B0 cho trần R10 của campaign mới: `--b0-lane-collisions 2.6667` (va chạm lane B0 trên REF_n28), nên trần là 3,67/h.

**Giới hạn của so sánh:**
- Không quy hết mức giảm va chạm cho patch mạng: giữa REF và REF_n28, `routes_hash` (cả 3 ngày) và `site_hash` cũng đổi. Số xe nạp: D1 4557 → 4694, D2 3768 → 3736, D3 3865 → 3760.
- **Chưa có backlog theo nhánh:** manifest chỉ ghi tổng. Vì vậy chưa biết backlog B1_manual (409 xe/run) dồn ở nhánh nào.
- 1 seed; chênh lệch giữa các ngày lớn (B0 mới: 22 / 48 / 34 va chạm/h).
- Trần va chạm của R28 (`max_collisions_per_hour` 4, `max_junction_collisions_per_hour` 142 trong `config/experiment.yaml`) đóng băng trên mạng cũ ngày 27/10 và **chưa** đo lại trên mạng mới (mục 7).

## 3. Kết quả 2 vòng campaign (bước 5)

Nguồn:
- `data/campaign_specs.csv` (mỗi spec một dòng);
- `data/B2_convergence.csv`;
- `data/campaign_summary.txt`.

Đã tính lại từ `SUMO/experiments/campaigns/{B2_n28/optuna_results, P1_n28/loop/results, P2_n28/loop/results}/*.pkl` bằng `select_best` (b0 = 2,6667); khớp file.

Ngân sách 24 run mỗi phương pháp (`budget.json`: 24/24), PROXY_D1–D3 × seed 1. Lệnh (cwd `SUMO/`):
```bash
.venv/bin/python -m thesis_sumo.baselines.optuna_search --structure rules/specs/B1_manual.json --campaign B2_n28 \
    --budget 24 --nproc 3 --site config/site.proxy.yaml --b0-lane-collisions 2.6667 --write-best rules/specs/B2_n28_best.json
B0=2.6667 bash experiments/campaigns/supervise_llm_n28.sh   # P1_n28 (params_only, base B1_manual), P2_n28 (full); --prompt-version v002
```

S là trung bình có trọng số của R = khoảng cách sim–quan sát chia cho dao động giữa các ngày. **Càng thấp càng tốt.**

| | Số spec | S nhỏ nhất / trung vị / lớn nhất | Va chạm tổng /h | Va chạm lane /h | Teleport kẹt+yield /h | Best theo R32 |
|---|---|---|---|---|---|---|
| B0 (vType mặc định, không luật) | 1 | 1,124 | 34,7 | 2,7 | 0,0 | — |
| B1 (luật thủ công) | 1 | 1,198 | 41,3 | 0,0 | 24,0 | — |
| B2 (Optuna, cấu trúc B1) | 8 | 1,091 / 1,190 / 1,227 | 28,7–104,7 | 0,7–51,3 | 0,0–35,3 | `B2_n28_t000`: 0,0/h, S 1,160 |
| P1 (Sonnet, chỉ tham số, cấu trúc B1) | 8 | 1,018 / 1,102 / 1,226 | 40,7–84,7 | 0,0–1,3 | 0,0–30,7 | `P1_n28_it02_s02`: 0,0/h, S 1,057 |
| P2 (Sonnet, cấu trúc + tham số) | 8 | 0,901 / 1,025 / 1,065 | 51,3–113,3 | 5,3–10,7 | 0,0–18,7 | `P2_n28_it02_s02`: 0,0/h, S 0,901 |

**Nhận xét (dữ kiện):**
- **Không spec nào đủ điều kiện** (0/24). Best chọn theo R32/R42: ít teleport kẹt+nhường nhất, rồi đến S. Có 7 spec cùng 0,0/h teleport kẹt+nhường (5 của P2, 1 của P1, 1 của B2), nên S quyết định thứ hạng.
- **Best chung** là `P2_n28_it02_s02` (`rules/specs/P2_n28_best.json`), cũng là spec có S thấp nhất trong 24 spec.
  - S 0,901, thấp hơn B0 (1,124).
  - Va chạm tổng 58,7/h và va chạm lane 6,0/h đều **cao hơn B0** (34,7 và 2,7), và vượt trần R10 lane (3,67/h).
  - Spec này là "ít kẹt xe nhất", **không phải** "đủ điều kiện".
- **So với B0, theo từng tiêu chí:**
  - S thấp hơn B0: P2 8/8 spec; P1 4/8 (cả 4 spec vòng 2); B2 1/8 (`t001`).
  - Va chạm tổng thấp hơn B0: chỉ 2 spec, đều của B2 (`t001` 33,3/h, `t003` 28,7/h). Không spec nào của P1, P2.
  - Va chạm lane trong trần R10: P1 8/8, B2 1/8, P2 0/8.
  - B0 có 0 teleport kẹt+nhường, nên không phương pháp nào thấp hơn B0 ở chỉ số này.
- **B2:** best theo R32 (`t000`) khác spec có S thấp nhất (`t001`, S 1,091, teleport kẹt+nhường 23,3/h). `t000` được chọn vì không kẹt, nhưng va chạm lane 51,3/h và va chạm tổng 104,7/h, cao nhất của B2. Theo `B2_convergence.csv`, best S đạt 1,091 ở trial 1 và không trial nào sau đó (2–7) thấp hơn.
- **P1, P2 theo vòng:** S nhỏ nhất giảm từ vòng 1 sang vòng 2 (P1 1,124 → 1,018; P2 0,997 → 0,901). Với 1 seed và 4 spec mỗi vòng, đây chưa phải bằng chứng hội tụ.
- **Tỉ lệ spec hợp lệ** (`SUMO/experiments/llm_logs/<camp>/validity_log.csv`):
  - P1_n28: 8/8 ngay lần đầu.
  - P2_n28: 6/8 lần đầu; 8/8 sau retry; tính theo lần trả lời là 8/10. Hai spec lỗi đều ở vòng 1, mỗi spec 2 lỗi `logic`:
    - `it01_s00`: gán `early_start` và `swarm_red_running` cho `car_seeker` (custom2), trong khi hai luật này chỉ nhận passenger/motorcycle/custom1;
    - `it01_s01`: gán `early_start` cho `car_seeker`, và đặt cả `lcPushy` lẫn `lcPushyGap`.

    Cả hai sửa được ở lần thử 2. Vòng 2: 4/4 hợp lệ lần đầu.

**So với mạng cũ** (report 27/10, mục 1.3). Đây **không** phải so sánh trên cùng điều kiện: khác mạng, khác nhu cầu và site, khác số spec (B2: 12 cũ so với 8 mới; P1/P2: 8 so với 8).

| | Mạng | Số spec | S nhỏ nhất / trung vị / lớn nhất | Va chạm tổng /h | Teleport kẹt+yield /h | Best theo R32 |
|---|---|---|---|---|---|---|
| B0 | cũ / mới | 1 / 1 | 1,181 / 1,124 | 112,7 / 34,7 | 10,7 / 0,0 | — |
| B2 | cũ | 12 | 1,182 / 1,329 / 1,523 | 90,7–168,0 | 12,0–76,7 | `B2_t010`, S 1,374 |
| B2 | mới | 8 | 1,091 / 1,190 / 1,227 | 28,7–104,7 | 0,0–35,3 | `B2_n28_t000`, S 1,160 |
| P1 | cũ | 8 | 1,159 / 1,188 / 1,262 | 93,3–146,0 | 24,0–54,0 | `P1_it02_s00`, S 1,167 |
| P1 | mới | 8 | 1,018 / 1,102 / 1,226 | 40,7–84,7 | 0,0–30,7 | `P1_n28_it02_s02`, S 1,057 |
| P2 | cũ | 8 | 1,047 / 1,201 / 1,299 | 136,7–186,0 | 7,3–30,0 | `P2_it02_s03`, S 1,084 |
| P2 | mới | 8 | 0,901 / 1,025 / 1,065 | 51,3–113,3 | 0,0–18,7 | `P2_n28_it02_s02`, S 0,901 |

Trên cả hai mạng:
- P2 có S thấp nhất và va chạm tổng cao nhất trong ba phương pháp. Va chạm trung bình theo spec: mạng mới P2 81,8/h, B2 46,8/h, P1 55,2/h; mạng cũ P2 163,7/h, B2 117,8/h, P1 117,0/h (`data/campaign_summary.txt`);
- P1 giữ va chạm lane gần 0;
- không spec nào đủ điều kiện.

**Hạn chế:** 1 seed mỗi ngày, 3 ngày, LLM là stand-in, mỗi phương pháp chỉ 2 vòng / 8 trial. Đây là chỉ báo, **không phải** kết quả E1/E2.

## 4. Video

`video_P2_n28_best_PROXY_D1_seed1.mp4`: 5:00 (5999 khung, 299,95 s ở 20 fps), 1600×1138, tốc độ ×6, 56 MB. Ghi bằng sumo-gui trên Xvfb, mô phỏng 0–1800 s (07:30–08:00), chụp mỗi 3 bước (0,3 s).

- **Spec:** `P2_n28_best` = `P2_n28_it02_s02`, best chung theo R32/R42 (lý do ở mục 3). Hai file chỉ khác `spec_id` và câu `description` (đã so). PROXY_D1, seed 1, check-junctions BẬT.
- **Luật TraCI:** chạy như batch run. Recorder chỉ đọc trạng thái, tô màu và chụp ảnh.
- **Kết quả không đổi khi quay:** run quay video (backend `traci`, có GUI) trùng với run chiến dịch `P2_n28_it02_s02__PROXY_D1/seed_01` (backend `libsumo`) ở mọi số trong bảng dưới, ở số xe nạp/chèn (4694/4684), và ở số dòng của 10 bảng quan sát. Bước chuyển đầu ra sang lược đồ quan sát chạy được (lỗi `detectors.xml` của 27/10 không lặp lại).

**Màu xe và overlay:**

| Màu | Ý nghĩa | Overlay |
|---|---|---|
| xanh dương / vàng | ô tô / xe máy | — |
| tím | xe rẽ trái trái luật đang đi (`moto_violator`) | — |
| **đỏ** | xe rẽ trái trái luật **đang chờ giữa nút**, chỉ ở HDT_N và HDT_S | số đang chờ / tích lũy, theo nhánh |
| **cyan** | xe **đi thẳng chặn làn rẽ phải** (làn 0, cả 4 nhánh) | số đang chặn (đang dừng) / tích lũy |
| **cam** | xe rẽ phải **bị kẹt sau xe chặn** | tổng đang kẹt; nhãn "+k" cạnh từng xe chặn |
| **trắng** | xe máy **đi trên vỉa hè** (LVL_E, LVL_W) | số đang có / tích lũy, đếm riêng từng vỉa hè |
| — | **đi ngược chiều** | dòng "Đi ngược chiều: KHÔNG mô phỏng (hoãn, R38)" |

Overlay còn có (theo `scripts/encode_video.py`):
- đồng hồ;
- pha đèn: tên pha, pha k/9 của chương trình 3 pha, giây trong chu kỳ 120 s;
- số xe trong mạng, số xe chờ chèn, số xe dừng ở 4 nhánh;
- va chạm và teleport tích lũy;
- nhãn "VA CHẠM" hiện 2 s sau mỗi va chạm.

**Kết quả run quay video.** Nguồn: `data/video_run_manifest.json` (khối `video` và các trường của manifest); đã so với `SUMO/experiments/campaigns/P2_n28/runs/P2_n28_it02_s02__PROXY_D1/seed_01/manifest.json`.

| | Giá trị |
|---|---|
| Va chạm | 44 (40 trong nút, 4 trên làn); theo loại: 29 `junction`, 13 `lateral`, 2 `rear_end`; 9 va chạm có xe đang bị TraCI can thiệp |
| Teleport | 44, đều do va chạm (kẹt 0, nhường 0) |
| Backlog xe chờ chèn | 0 lúc 1800 s (lớn nhất 2) |
| `valid_strict` | false (có va chạm) |
| Rẽ trái trái luật chờ giữa nút | tích lũy 206 xe (HDT_N 92, HDT_S 114); đồng thời tối đa 18, trung bình 2,5 (HDT_N tối đa 8, TB 0,77; HDT_S tối đa 12, TB 1,72) |
| Xe đi thẳng chặn làn rẽ phải | tích lũy 123 xe; đồng thời tối đa 5, TB 0,66; đang dừng hẳn tối đa 1, TB 0,03 |
| Xe rẽ phải kẹt sau xe chặn | tối đa 0: **màu cam không xuất hiện** trong cả video |
| Xe máy trên vỉa hè | tích lũy 14 (LVL_E 7, LVL_W 7); đồng thời tối đa 4, TB 0,41 (LVL_E tối đa 2, TB 0,17; LVL_W tối đa 3, TB 0,24) |
| Thời gian chạy (wall time của run) | 782,85 s cho 1800 s mô phỏng |

44 va chạm trong 0,5 h là 88/h (lane 8/h), khớp với PROXY_D1 trong pkl của `P2_n28_it02_s02`. Con số 58,7/h ở mục 3 là trung bình của 3 ngày (88 / 38 / 50).

**Hạn chế:**
- Video là 1 run (PROXY_D1, seed 1), chỉ để minh hoạ, không phải kết quả.
- Spec này vượt trần R10 va chạm lane (mục 3) nên không đủ điều kiện.
- Làn 0 tô vàng trong sumo-gui nên xe máy vàng khó nhìn trên làn này.
- Mỗi vỉa hè dài 170 m, nhưng khung nhìn chỉ thấy khoảng 50 m cuối (điều phối viên ước khi xem khung hình). Panel vẫn đếm đủ cả đoạn.
- `frames.json` có 6000 khung (t = 0,3–1800 s), nhưng chỉ có 5999 ảnh PNG: khung cuối (t = 1800 s) không có ảnh.

**Tái tạo (từ thư mục gốc repo):**
```bash
xvfb-run -a -s "-screen 0 1920x1200x24" SUMO/.venv/bin/python report/2026-10-28/scripts/record_video.py \
    --spec-json SUMO/rules/specs/P2_n28_best.json --day PROXY_D1 --seed 1 --end 1800 --every 3 --out report/2026-10-28/_rec
SUMO/.venv/bin/python report/2026-10-28/scripts/encode_video.py --rec report/2026-10-28/_rec \
    --out report/2026-10-28/video_P2_n28_best_PROXY_D1_seed1.mp4 --fps 20
cp report/2026-10-28/_rec/video_run_manifest.json report/2026-10-28/data/video_run_manifest.json
```
Thư mục `_rec/` (khoảng 6000 PNG) không commit.

Hai script là bản sửa của `report/2026-10-27/scripts/` cho kịch bản 28/10:
- màu đỏ lấy từ `JunctionInfo.box_lanes`;
- màu trắng lấy từ `JunctionInfo.sidewalk`;
- cyan/cam xét làn 0 của cả 4 nhánh;
- pha đèn đọc bằng `getAllProgramLogics` / `getPhaseName` / `getNextSwitch`;
- bố cục 1600×1138, chữ đặt ở dải trên và dưới.

## 5. Điều phối

| Ai | Việc |
|---|---|
| Opus (subagent) | Bước 2 (A, B, C song song); debug D2, D3; review độc lập (chỉ đọc); sửa script video; viết report này |
| Sonnet (subagent) | Bước 1 (mạng, demand); bước 3 (proxy, pytest); bảng bước 4; stand-in P1/P2 (mỗi request một subagent mới, chỉ đọc file request, ghi `experiments/llm_logs/<camp>/responses/<id>.json`); gom spec ở bước 6a |
| Điều phối viên (phiên Opus chính) | Dọn process cũ; build lại mạng; sinh SYNTHETIC; chạy B0/B1 và campaign nền; sửa 5 chỗ nhỏ sau review |

- **Usage limit:** 0 lần chạm trong ngày.
- **Sự cố:**
  - Phiên điều phối chính khởi động lại, khoảng 05:03 đến 08:44 (đồng hồ máy). Mất khoảng **3 giờ 40 phút**.
  - Subagent D3 bị dừng giữa chừng và được resume từ transcript.
  - Lúc đó không có process nền nào chạy, nên không mất kết quả mô phỏng.
- **Tiến độ mô phỏng:** bước 4 chạy 09:21–09:41; bước 5 chạy 09:41–11:28. Tổng số process mô phỏng đồng thời ≤ 11.
- **PROXY_D4/D5** không lộ cho LLM stand-in hay Optuna.
- Một stand-in Sonnet (P1 vòng 2, s03) tạo thêm script phụ `/tmp/mk_it02_s03_a1.py`, ngoài các tệp được phép. Không ảnh hưởng kết quả.
- **Yêu cầu của Viktor trong ngày:** không sửa script video trước khi bước 5 xong. Bản nháp đã dừng và xoá lúc 10:20; script được sửa lại sau bước 5.
- Một số mốc giờ trong `PROGRESS.md` (quanh 10:00) là ước chừng; đồng hồ máy khi đó khoảng 09:50–09:58.

## 6. Việc tiếp theo (khuyến nghị)

Đây là đề xuất, chưa làm:

1. **Đo sức chứa box HDT** (như `experiments/phase3/box_capacity.py` đã làm cho LVL_W), rồi quyết định chỉ tiêu M7 p90 = 10/box.
2. **Đo độ trễ rẽ trái LVL_W so với LVL_E** trên B0, để biết quan hệ nhường mới (MAJOR-1) có làm lệch M1/M5/M6 ở LVL_E không.
3. **Chấm mũi tên trái LVL ở M1–M3:** ghi onset của mũi tên vào `signal_events`, để đo vượt đỏ / xuất phát sớm của rẽ trái LVL.
4. **Đo lại trần R28** (va chạm lane và junction của B0) trên mạng mới, trước khi chạy thêm campaign.
5. **Thêm seed/ngày** cho B0, B1 và các best trước khi đọc chênh lệch S; chênh lệch giữa các ngày hiện rất lớn.
6. **Thêm đầu ra backlog theo nhánh** vào manifest.
7. Xử lý các MINOR còn lại ở mục 1.3; xoá `supervise_llm.sh` cũ nếu không dùng nữa.

Ngoài phạm vi lần này: campaign H (Optuna trên cấu trúc `P2_n28_best`), Task 15 (benchmark D4–D5, ≥ 20 seed, E1/E2), cập nhật LaTeX.

## 7. Cần Viktor quyết / lưu ý

**Quyết định đã tự chọn trong ngày (cần duyệt):**
1. **Đổi thứ tự bước:** sửa code → sinh proxy → sinh demand (mục 1.1).
2. **Patch mạng D2/D3 là lựa chọn mô hình hoá:**
   - vehicle-width 3,5 m chỉ cho điểm chờ illegal-left, các internal junction khác ghim lại;
   - `<prohibition>` ở cửa ra vỉa hè.

   Chấp nhận, hay chọn cách khác (ví dụ explicit waiting edge, PLAN 3D hướng b)?
3. **Áp chỉ tiêu cũ cho phần mới của kịch bản** (`targets.yaml`): `n_waiting_in_box` 6 cho từng box HDT; `crossing_start_delay_per_waiter_s` 0,3 s/xe cộng hai box; `sidewalk_choice_prob` 0,03 cho LVL_E. Cần nguồn hoặc duyệt. Mẫu số "straight head" của M2/M3 cần transfer note.

**Tác dụng phụ và giới hạn mô hình:**

4. **LVL_E left nhường LVL_W left** (tác dụng phụ của D2): đo độ trễ trước. Tuỳ chọn: `pass="true"` cho cả hai liên kết.
5. **LVL_W làn 0 "đói lượt"** tới 178 s: có đảo ưu tiên Phase 3B (người đi vỉa hè nhường xe làn 0) không?
6. **Rẽ trái LVL** (đầu đèn riêng) không được chấm ở M1–M3; vượt đỏ và xuất phát sớm của mũi tên không được đo.
7. **Vỉa hè proxy** chỉ sinh cho xe máy đi thẳng. Nguồn có nói "hoặc rẽ phải", nhưng chưa có chỉ tiêu.
8. **Va chạm vẫn cao và chưa có spec đủ điều kiện.** B0 mới có 32,0 va chạm trong nút/h; best P2 có 58,7 va chạm tổng/h. Trần R10 lane đã lấy theo B0 mới (3,67/h), nhưng trần R28 (4/h lane, 142/h junction) vẫn lấy từ mạng cũ và chưa đóng băng lại. Có đóng băng lại R28 trên mạng mới không?
9. **Backlog theo nhánh** chưa có đầu ra.

**TODO_MEASURE / TODO_DECIDE còn lại:**

10. Thời lượng pha 42 / 16 / 44 s + 4 + 2 là giả định (`TODO_MEASURE`). Vạch làn, vỉa hè (rộng 3,0 m, bắt đầu cách vạch dừng 170 m, tốc độ 5 m/s) và đoạn cọc 30 m đều là "assumed".
11. Sức chứa box HDT chưa đo; chỉ tiêu M7 p90 = 10/box (`TODO_DECIDE`).

**Văn bản và quy trình:**

12. `docs/research/proxy_targets.md` và `docs/research/phase3_box_capacity.md` chưa cập nhật cho HDT. Chờ Viktor duyệt; không sửa LaTeX trong ngày.
13. **Skill `writing-docs-viktor`** mà `CLAUDE.md` yêu cầu **không có** trên máy này (gọi công cụ Skill báo "Unknown skill"; điều phối viên cũng không tìm thấy trong `~/.claude/skills` và `.claude/skills`). Report này theo văn phong và bố cục của report 27/10 và tự kiểm theo checklist riêng: số khớp dữ liệu gốc, nguồn của từng số, phân biệt dữ kiện / giả định / khuyến nghị.
14. **Commit:** toàn bộ thay đổi trong ngày (code, mạng, proxy, routes, campaign `_n28`, `rules/specs/*_n28_best.json`, prompt v002) chưa commit. Chờ Viktor cho phép.
