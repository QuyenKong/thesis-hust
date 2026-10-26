# PROGRESS — theo dõi run proxy-benchmark-loop

> Ghi chú: trước run này, controller đã cài sẵn Ollama 0.40.10 và model `qwen3.5:9b` (lưu tại `D:\ollama\models`) vào ngày 2026-10-25.

**Mục tiêu:** chạy đầy đủ phương pháp PLAN.md Phase 1–7 trên dữ liệu proxy dựa trên literature, với đúng 3 vòng LLM refinement, sau đó benchmark và viết report.

- Spec: [docs/superpowers/specs/2026-10-25-proxy-benchmark-loop-design.md](superpowers/specs/2026-10-25-proxy-benchmark-loop-design.md)
- Plan: [docs/superpowers/plans/2026-10-25-proxy-benchmark-loop.md](superpowers/plans/2026-10-25-proxy-benchmark-loop.md) (15 task; thứ tự thực hiện 1,2,3,4,6,5,7,8,…,15)
- Branch: `proxy-run`

**Vai trò:** Điều phối: Opus 5.5 · Code: Opus · Thao tác/test/SUMO: Sonnet · Ghi chép: Sonnet

**Ký hiệu:** ✅ xong · 🔄 đang làm · ⏳ chưa làm · ⚠️ vướng

## Tóm tắt các con số quan trọng

Cập nhật sau mỗi lượt; cập nhật lần này sau Task 9. Tất cả là proxy (literature), không phải số đo tại nút LVL x HDT. **Lưu ý: các số B0 bên dưới đo khi `collision.check-junctions` TẮT; R28 bắt buộc bật nên operator đang đo lại, các số này sẽ đổi.**

| Mục | Giá trị | Ghi chú / nguồn |
|---|---|---|
| Thời gian chạy một run 1800 s (B0, PROXY_D1–D3, SSM tắt, 3 run song song) | 88–463 s mỗi run; D1 chậm nhất (463 / 376 / 310 s), D2 122–229 s, D3 88–273 s | Task 4b operator. Run 3600 s trên D1 mất 20+ min nên dùng `sim.calib_end_s: 1800` (R31). Trước R22 (SSM bật cho mọi xe) 1200 s mất 29–39 min |
| Thời gian chạy khác | B0 600 s = 42,7 s; SYNTHETIC 3600 s = 150–261 s; B1 + controller 600 s = 63–99 s (controller `on_step` 3–7 s) | Task 4 operator, Task 9 (máy có tải song song nên dao động tới 1,5 lần) |
| B0 va chạm (check-junctions TẮT, 1800 s, 9 run D1–D3 x 3 seed) | 2, 0, 2, 2, 6, 0, 0, 2, 0 /h; trung bình 1,56/h, p90 2,8; cổng R17 (≤ 5/h) đạt | Task 4b operator. Trước khi sửa bề rộng làn thoát: 46–62 va chạm/h trên D1 |
| B0 teleport không do va chạm (jam + yield, 1800 s) | D1: 14, 22, 10; D2: 22, 23, 2; D3: 0, 11, 0. 7/9 run có teleport, chỉ D3 seed 1 và 3 là `valid_strict`; mọi teleport jam/yield là xe máy | Task 4b operator. B0 chưa ELIGIBLE (`max_noncollision_teleports: 0`) |
| Ngưỡng va chạm đã đóng băng | `max_collisions_per_hour: 3` (commit `eae2050`, check-junctions TẮT) — đã bị thay bằng `null` ở Task 9 fix 1; operator đang tính lại cả ngưỡng lane và junction với check-junctions BẬT (R28) | Chưa có giá trị mới |
| Sức chứa box (xe rẽ trái trái luật dừng trong box, `target`, 5 seed x 900 s) | Box 3,2 m: 8 ở mọi seed, 2 cột ngang. Box 3,5 m (sau R21): 13, 8, 8, 7, 10; 3 cột ngang; va chạm 0–1/run (trước 10–24) | Task 4b operator, Phase 3 re-check. Target M7a: trung bình 6, p90 10, p95 11; check-junctions TẮT |
| Tỉ lệ thoát sớm khỏi box (target 20 % số xe vào) | Task 5 (box 3,2 m, dòng đối diện ~1500 xe/h): 62 %. Task 7 R15 check (PROXY_D1, 1 seed, 1200 s, box 3,5 m): B0 = 14,6 % (7 xe thoát sớm / 51 xe vào box), `jmTimegapMinor` 0,5 = 38,1 % (16 / 48) | Chỉ 1 seed nên mang tính gợi ý; target nằm giữa hai giá trị |
| GEH (G0, ô 15 phút x approach x movement x loại xe, 0–1800 s) | Tỉ lệ GEH < 5: 0,92–1,00 ở cả 9 run (D1: 0,919 / 0,952 / 1,000); ngưỡng `min_share` 0,85. Mức approach x movement (gộp loại xe): 0,844–1,000 | Task 4b operator. Số "quan sát" proxy cùng sinh từ một generator, nên GEH cao chỉ cho thấy nút phục vụ được nhu cầu |
| Nguyên nhân tắc nghẽn của B0 | 217 xe rẽ trái trái luật (2,4 % xe) ở LVL_W gây gridlock làn 2; bỏ chúng thì teleport jam/yield về 0/0/3 | Task 4b operator (R23); là phát hiện về hành vi B0, không phải lỗi mạng |

## Bảng trạng thái

| # | Task | Trạng thái | Link / commit |
|---|---|---|---|
| 1 | Config loading và proxy site file (research) | ✅ | `4657a64` |
| 2 | Network (Phase 1) | ✅ | `4d52cfc` (`cdcce12..4d52cfc`) |
| 3 | B0 vTypes, demand và sumocfg (Phase 2 phần 1) | ✅ | `00cb1f5` (`4d52cfc..00cb1f5`) |
| 4 | Runner và manifest (Phase 2 phần 2) | ✅ (code + operator; nguyên nhân va chạm tìm ra, sửa ở 4b) | `a8b0722`, `096ce58` (`00cb1f5..096ce58`); operator `ed6030e` |
| 4b | Corrective: bề rộng làn thoát (R21), SSM tắt + gộp cảnh báo (R22), chạy lại cổng B0 (R17/R24) | ✅ | `52ae484`, `90b302c` (`586349a..90b302c`); operator `eae2050`, `1f1281f` |
| 5 | In-box waiting experiment (Phase 3, ghi quyết định, không dừng) | ✅ | `aedc7c1`, `e0c1faf` (`8d752b9..e0c1faf`) |
| 6 | Proxy observed data (targets + generator) | ✅ | `a76bca4`, `8d752b9` (`9b8d013..8d752b9`) |
| 7 | Param bounds, rule schema, validator (Phase 4.1–4.3) | ✅ | `b9b77cb`, `586349a` (`e0c1faf..586349a`) |
| 8 | Compiler (Phase 4.4) | ✅ | `ad1f8bb` (`90b302c..ad1f8bb`) |
| 9 | TraCI runtime controller và rules (Phase 4.5) | ✅ (operator đang tính lại hai ngưỡng va chạm, R28) | `ac325b4`, `4023408` (`ad1f8bb..4023408`) |
| 10 | Metrics M1–M8, G0 và distance (Phase 5) | ✅ (Linux) | xem nhật ký 2026-10-26 |
| 11 | Experiment harness (evaluation chung + budget counter) | ⏳ | |
| 12 | LLM client, prompts v001, feedback | ⏳ | |
| 13 | LLM loop — 3 vòng | ⏳ | |
| 14 | Optuna baseline B2 | ⏳ | |
| 15 | Benchmark và report | ⏳ | |

## Quyết định đã đưa ra (rulings)

Nguồn: `.superpowers/sdd/2026-10-25-proxy-benchmark-loop/progress.md`, mục "Rulings" (pre-flight của controller).

- **R1:** thứ tự thực hiện 1,2,3,4,6,5,7,…,15 (Task 6 trước Task 5) vì quyết định capacity của T5 cần target M7a. Nếu sai: không mất gì, T6 không phụ thuộc T5.
- **R2:** Task 6 cũng build `scenario/demand/routes_<day>.rou.xml` cho PROXY_D1–D5 bằng build_demand (seed cố định theo ngày), runner chọn routes theo `day`; thiếu thì evaluate_spec không chạy được. Nếu sai: sửa lại nhỏ quy ước đường dẫn.
- **R3:** danh sách cột schema §5.1 nằm trong một module `src/thesis_sumo/schema_observed.py` (tạo ở T4), T6 và T10 import, tránh ba bản copy lệch nhau. Nếu sai: không đáng kể.
- **R4:** scribe sở hữu `docs/PROGRESS.md` (tạo ở T1, thêm entry sau mỗi task từ các file report của implementer/operator); implementer chỉ ghi vào file report của mình. Nếu sai: PROGRESS chậm một task.
- **R5:** các bước chạy thí nghiệm (T4 bước 3–4, T5, T9 B1, T10 B0 report, T12 smoke call, T13, T14, T15) do operator chạy sau khi code của coder qua review; coder giao CLI chạy được. Nếu sai: thêm một lần dispatch cho mỗi task như vậy.
- **R6:** làm việc trực tiếp trên branch `proxy-run`, không dùng worktree (editable install và `.venv` gắn với đường dẫn này). Nếu sai: không mất gì, `main` không bị đụng.
- **R7:** `site.yaml` đo thực còn null thì build mạng raise `MissingFieldDataError` thay vì "build với giá trị OSM + cảnh báo" như PLAN 1.4, vì CLAUDE.md (raise khi null bắt buộc) chặt hơn và `site.proxy.yaml` đã phủ trường hợp chưa đo. Nếu sai: site đo một phần chưa build được cho đến khi thêm cờ fallback.
- **R8 (Điều phối):** `sim.fcd_radius_m` 60→120 m; `SNAPSHOT_RANGE_M` chuyển thành config `observation.queue_range_m: 80`; generator proxy cắt hàng đợi cùng 80 m; M5 có thêm scalar `share_censored`, vì 35 m chặn mất hàng đợi giờ cao điểm. Nếu sai: sửa một giá trị config rồi chạy lại; fcd lớn gấp ~2–2,5 lần (xóa fcd sau khi chuyển đổi trong các run của loop).
- **R9 (Điều phối):** thêm bảng dẫn xuất `traversals.csv` vào `schema_observed.TABLES` (`track_id, vclass, approach, movement, exit_approach, lat_m_at_stopline, t_range_entry, t_stopline, t_exit`), do `to_observed_schema` và generator proxy cùng sinh. M6 = `t_exit−t_stopline` và `t_stopline−t_range_entry` theo movement × vclass; M8 = tỉ lệ xe có làn (suy từ `lat_m_at_stopline` + bề rộng làn) không cho phép movement đó, bản đồ làn→movement lấy từ vạch kẻ làn trong site file (T6 thêm trường có source/evidence). Spec yêu cầu M1–M8. Nếu sai: thừa một CSV.
- **R10 (Điều phối):** chính sách hợp lệ của run (thay quy tắc "có va chạm là loại" trong plan, xem giải thích bên dưới). Nếu sai: ngưỡng quá lỏng có thể cho qua spec nhiều artifact; số đếm strict luôn được công bố.
- **R11:** `box_queue` giữ ngữ nghĩa theo từng chu kỳ: `t` = lúc xanh đi thẳng của hướng đối diện kết thúc; `n_waiting_in_box` = số xe vi phạm đang dừng trong box tại `t`; `t_clear_start/t_clear_end` = lần ra khỏi box đầu/cuối của TẤT CẢ xe vi phạm đã vào box trong chu kỳ đó (kể cả xe thoát sớm qua khoảng trống, nên `t_clear_start` có thể sớm hơn `t`). Generator T6 phải tái tạo y hệt; code assert approach rẽ trái trái luật và approach đối diện cùng pha xanh, nếu không thì raise. Quan sát được trên video bằng cách theo dõi xe ra khỏi box. Nếu sai: định nghĩa lại hai cột ở sim + generator.

- **R12:** Task 6 (coder) chạy song song với campaign operator của Task 4; hai bên chạm file rời nhau (chỉ `experiment.yaml` dùng chung: operator sửa `validity.*`, coder sửa `data_split`, đọc lại trước khi sửa). Tiết kiệm ~30 phút. Nếu sai: xung đột merge ở `experiment.yaml`, sửa đơn giản.
- **R13:** `targets.yaml` có thêm giá trị evidence thứ ba `literature_transferred` (số lấy từ nguồn nhưng chuyển sang địa điểm/mẫu số/quốc gia khác) kèm `transfer_note`; báo cáo gộp `literature` + `literature_transferred` thành "có nguồn" nhưng liệt kê riêng các mục transferred, vì reviewer chỉ ra nhãn `literature` bị nói quá. Nếu sai: chỉ đổi nhãn.
- **R14 (Điều phối):** Phase 3 → (a) native được xác nhận (giữ 8 xe, 2 hàng ngang, không deadlock, thoát 4,7 s sau vàng của hướng đối diện, headway thoát 0,5 s). Phải báo p90 bị cắt (8 so với target 10). Sau này chạy lại Phase 3 trên hình học đo thực. Nếu sai: dựng lại net và chạy lại các vòng.
- **R15 (Điều phối):** rule TraCI `illegal_left_box` chỉ GIỮ/NHƯỜNG, không bao giờ đẩy xe qua xung đột; tham số `release_lag_s` [0,4] (cộng vào thời điểm thoát native, qua slowDown/stop) và `max_clear_into_cross_green_s` [0,6]; không đổi speedMode/bit an toàn junction. Xe thoát sớm điều khiển bằng vType `jmTimegapMinor` trên custom1 [0,5; 3] s (giả định), KHÔNG qua TraCI; loại `jmIgnoreFoeProb`/`jmIgnoreFoeSpeed`. Cận `minGap` [0,5; 2,5] m cho MỌI archetype xe máy; cận dưới `minGapLat` 0,3 m. Task 7 chạy kiểm tra nhỏ trên PROXY_D1: B0 so với `jmTimegapMinor` 0,5 cho xe thoát sớm. Nếu sai: tỉ lệ thoát sớm vẫn 0 thì thêm rule gap-acceptance ở vòng 2, ghi như thay đổi schema.
- **R16 (Điều phối):** M7b chấm bằng `clear_lag_s` dựa trên bảng (định nghĩa trong `targets.yaml`, một hàm cho sim và obs từ `box_queue` + `stopline_crossings` + `traversals.t_exit`); SSM PET chỉ để chẩn đoán (có lọc), nhãn báo cáo "PET proxy (box clear lag)", vì SSM giữa xe chờ và dòng đối diện là artefact hình học. Nếu sai: kết luận an toàn yếu hơn, nêu ở limitations.
- **R17 (Điều phối, tạm thời):** cổng trước mọi vòng LLM = B0 trên PROXY_D1, 3600 s × 3 seed, kèm phân loại va chạm. Nếu ≤ 5 va chạm/giờ thì đi tiếp với ngưỡng max(2, p90 B0); nếu cao hơn thì chặn cho đến khi tìm ra nguyên nhân (ví dụ patch bề rộng). Operator phải làm rõ vì sao 203/250 va chạm Phase 3 có loại `junction` trong khi `collision.check-junctions` mặc định tắt. Ngưỡng trong `experiment.yaml` phải chốt trước vòng 1. Nếu sai: phí một campaign ~6 phút.
- **R18:** schema dành cho LLM (tập con JSON-Schema an toàn với Ollama: thuộc tính liệt kê rõ từ bounds, tham số từng rule là key riêng, không dùng if/then/propertyNames/uniqueItems, provenance do harness chèn) sinh ở Task 12 (`llm_schema()`) và thử với Ollama thật; schema đầy đủ vẫn dùng để validate, vì bộ chuyển ngữ pháp của Ollama âm thầm bỏ cấu trúc không hỗ trợ. Nếu sai: tỉ lệ spec hợp lệ thấp hơn (đây là một thước đo của luận văn).
- **R19:** mở rộng `RULE_VCLASSES`: early_start, swarm_red_running, wrong_lane_dodge áp cho cả xe máy và ô tô (target M2/M3/M8 có phần ô tô); slow_lane_center chỉ xe máy; illegal_left_box chỉ custom1. Việc implementer thu hẹp trước đó không có cơ sở trong PLAN hay ruling. Nếu sai: rule cho ô tô có thể thiếu thực tế, LLM/Optuna đặt p≈0 là xong.
- **R20:** các vấn đề không gian tìm kiếm của Optuna (bật/tắt mặc định vắng, loại trừ lcPushy/lcPushyGap, mặc định tham số rule, simplex tỉ lệ) xử lý ở Task 14 bằng helper `search_space()`, không thuộc Task 7. Nếu sai: Task 14 làm lại.
- **R21 (Điều phối):** bề rộng làn thoát = bề rộng làn vào, qua danh sách mới `exits: [{id, edge, lane_widths_m, _source, _evidence}]` trong site (TCVN 13592:2022 Bảng 10, evidence `literature`; `site.yaml` để `null # TODO_MEASURE`); có test mọi internal lane có bề rộng bằng làn ra tương ứng; chạy lại Phase 3 `target` (5 seed) vì box giờ rộng 3,5 m. Bước nhảy 3,2 m là mặc định không có nguồn do chính ta để lại. Nếu sai: va chạm quay lại trên net đo thực, báo như giới hạn của sublane.
- **R22 (Điều phối):** SSM tắt trong run loop/calibration/Optuna (không ghi option `device.ssm.*`; đã kiểm chứng tương đương `probability 0`); tập chẩn đoán của benchmark (seed 1–3 mỗi spec) bật SSM bằng `--device.ssm.explicit` = id `moto_violator`; mọi run có `--aggregate-warnings 20`, không bao giờ `-W`; manifest vẫn đếm đúng số cảnh báo. Nếu sai: mất PET chẩn đoán không dùng để chấm.
- **R23 (Điều phối):** nhu cầu proxy 8180 xe/h hợp lý (v/c≈0,37 mỗi approach, Y≈0,33), KHÔNG hạ. G0 vẫn là cổng cứng cho eligibility/best-spec; M1–M8/R/S vẫn tính và báo cho mọi run kể cả B0 (nhãn "G0 fail"); feedback LLM có tỉ lệ GEH pass; nếu vòng nào không có spec eligible thì xếp hạng theo tiêu chí trong R32. Operator tìm nút thắt trước: nếu là artefact mạng thì patch, nếu là hành vi vType B0 thì là phát hiện của luận văn. Nếu sai: không có P eligible, báo thẳng.
- **R24 (Điều phối):** quy trình đặt ngưỡng: sau R21/R22 chạy B0 trên PROXY_D1–D3 x 3 seed, `max_collisions_per_hour = max(2, ceil(p90 của 9 tỉ lệ))`, đóng băng và commit TRƯỚC vòng 1, không đổi sau khi thấy kết quả LLM; cổng R17 (B0 ≤ 5/h) giữ nguyên; nếu run 3600 s > ~5 min thì dùng `calib_end_s` 1800. Nếu sai: phí ~25 phút.
- **R25 (Điều phối):** KHÔNG chấp nhận `junctionModel.ignoreIDs` trên xe cắt ngang (điểm chờ cách tâm làn nội bộ lane-2 của HDT_N 0,03 m; 0 va chạm chỉ vì check-junctions đang tắt). Bỏ `yield_cross_green` và tham số `max_clear_into_cross_green_s` (đổi schema/`TRACI_RULE_PARAMS` trước vòng 1); chỉ giữ `release_lag_s` [0,4] bằng `setSpeed(0)` thuần, cấm `ignoreIDs` ở mọi nơi (test grep); thêm test giữ xe với `--collision.check-junctions` → 0 va chạm junction, 0 teleport yield. Thay thế tham số thứ hai của R15. Nếu sai: LLM chỉ kéo dài được thời gian dọn box; nếu target muốn trễ đường cắt ít hơn native thì M7c không đạt (báo cáo).
- **R26 (Điều phối):** B1_manual bỏ rule illegal_left_box (Saval et al. không có chờ trong box; box chạy native như B0). Nếu sai: B1 không có đòn bẩy M7 (trung thực với baseline từ literature).
- **R27 (Điều phối):** wrong_lane_dodge trên site không có connection dùng được thì validator báo `logic` "rule inapplicable on this site" để LLM khỏi phí spec; không thêm connection; M8 trong sim chỉ qua vị trí ngang; ghi vào limitations. Nếu sai: không mất gì.
- **R28 (Điều phối):** `--collision.check-junctions` BẬT trong mọi run kể cả đếm validity; manifest tách `n_collisions_lane` / `n_collisions_junction`; cổng R17 (B0 ≤ 5/h) tính trên va chạm lane; va chạm junction bị chặn bởi ngưỡng suy từ B0 `max(2, ceil(p90))` và được báo cáo; tính lại và đóng băng cả hai ngưỡng theo R24 (B0 PROXY_D1–D3 x 3 seed, check bật) TRƯỚC vòng 1, ghi lại giá trị cũ 3 và lý do. Box là trọng tâm M7, số đếm không thấy box là thiếu trung thực. Nếu sai: ~9 run lại, ngưỡng lỏng hơn.
- **R29 (Điều phối):** test R25 trên net chữ thập nhỏ (một xe chờ bị giữ, dòng cắt ngang, check-junctions bật): giữ thuần lag 3 → 0 va chạm junction; lag 0 → 0; đối chứng âm với `ignoreIDs` → > 0. Operator kiểm cặp seed trên proxy: giữ so với lag 0, va chạm junction không hơn native quá 1/h. Nếu sai: không phát hiện được nếu giữ xe gây va chạm trên net thật.
- **R30 (Điều phối):** cửa sổ "bị can thiệp" (R10) mở cho đến khi xe tới làn không-internal đầu tiên sau vạch dừng; va chạm được gán cho can thiệp nếu một trong hai bên đang trong cửa sổ. Nếu sai: cửa sổ quá rộng làm số va chạm "can thiệp" cao hơn thực.
- **R31 (Điều phối):** `sim.calib_end_s: 1800` dùng cho loop, Optuna VÀ benchmark (lệch spec mục 3, ghi lại; báo cáo nói "chỉ 07:30–08:00"); M1–M8 tính trên cửa sổ [300, 1800) s ở cả hai phía (warm-up 300 s); G0 trên hai bin 15 phút của 0–1800 s; chẩn đoán: B0 và P_best 3600 s x 3 seed trên D4 (run D1 3600 s mất 20+ phút). Nếu sai: đánh giá thấp gridlock tăng dần.
- **R32 (Điều phối):** giữ `max_noncollision_teleports: 0`; xếp hạng dự phòng của R23 đổi thành số teleport jam/yield trung bình mỗi giờ rồi S (GEH không còn phân biệt); feedback LLM có số teleport và vị trí. Nếu sai: P_best = "ít gridlock nhất", báo cáo phải nói rõ.
- **R33 (Điều phối):** giữ time-to-teleport mặc định 300 s ở mọi nơi; một run chẩn đoán B0 D1 với `-1` để phân biệt deadlock với kẹt chậm; không bao giờ dùng `--ignore-junction-blocker`. Nếu sai: nhỏ.
- **R34 (Điều phối):** giữ cận `minGap` [0,5; 2,5] m; chú thích trong `param_bounds.yaml` chỉ trích nguồn standstill gap có nguồn (Saval Bảng 11, 1,9 m) hoặc ghi "assumed"; lý do "sức chứa" bị bỏ vì thu hẹp theo output SUMO là tuning. Nếu sai: vài mẫu LLM bị phí.

- **R35 (Điều phối, Task 10, chờ Viktor xác nhận):** mọi khoảng cách theo ngày trong `distance.metric_distance` bị chặn trên ở `D_EMPTY` = 2,0 (một phía không có sự kiện / scalar không xác định cũng bằng `D_EMPTY`), để LLM/Optuna không giảm được điểm bằng cách triệt tiêu một hành vi đến mức không còn sự kiện nào. Chưa xử lý: với tỉ lệ nhỏ (M2/early/car ≈ 0,0087, M3/share/car), sim = 0 tốn 1,0 còn sim > 2× quan sát tốn 2,0, nên ép về 0 vẫn rẻ hơn; hai khóa này chiếm ~4 % và ~3 % trọng số và `d_day_day` ≈ 1,5 (chủ yếu là nhiễu). Phương án làm mượt sai số tỉ lệ (vd chia cho max(obs, độ phân tán giữa các ngày)) là quyết định của Viktor. Nếu sai: đổi một hàm, chạy lại điểm.
- **R36 (Điều phối, Task 10):** `score.weights` chia đều theo nhóm M1–M8 (plan Task 10 "equal across M1–M8, log as my call"); trong nhóm chia đều cho chỉ số con (M7a/b/c) rồi cho các khóa; chỉ khóa được chấm mới có trọng số; tổng được chuẩn hóa lại theo các nhóm có mặt (để thêm M9–M11 sau). `observation.metric_window_s: [300, 1800]` theo R31. Nếu sai: sửa `experiment.yaml`.

- **R37 (Viktor, 2026-10-26):** làn rẽ phải liên tục = lane 0 hiện có của 3 làn OSM (không thêm làn); làn đi thẳng còn 2. B0 quá tải trên mạng này là một phát hiện (xem nhật ký F2-net), không sửa bằng mạng. `right_lane_separator: bollards` ở mọi nhánh (Viktor quan sát, evidence `field_observation`): connection đi thẳng từ lane 0 được giữ nhưng `disallow="all"` (không ai đi thẳng từ làn rẽ phải; giữ để chỉ số link đèn không dịch). Hệ quả: hành vi 6 (chặn làn rẽ phải) không xảy ra tại vạch dừng; chỉ có thể xảy ra ở đoạn trước cọc, cần biết cọc bắt đầu từ đâu (TODO_MEASURE) — xét ở Phase 3A. Rẽ phải ở làn liên tục khi đèn đỏ không phải vi phạm: loại khỏi M1/M2/M3/M4/M7c ở cả hai phía; generator proxy cho xe rẽ phải liên tục đi không dừng.

**R10 giải thích cho Viktor (đổi quy tắc "va chạm là loại"):** Plan ban đầu nói bất kỳ run nào có va chạm đều bị loại. Nhưng ngay cả B0 (cấu hình gốc, chưa có luật LLM) cũng va chạm khoảng vài lần mỗi giờ mô phỏng (xe máy sublane, hai xe cùng làn rẽ), nên nếu giữ quy tắc đó thì gần như mọi run đều bị loại và không so sánh được gì. Quy tắc mới: manifest vẫn ghi `valid_strict` (0 teleport, 0 va chạm) và thêm số liệu chi tiết (teleport không do va chạm, va chạm theo loại, va chạm có xe bị TraCI can thiệp). Một run vẫn được tính (ELIGIBLE) khi: không có teleport ngoài va chạm; không còn xe kẹt chưa chèn được cuối run; qua cổng GEH; số va chạm ≤ max(2, p90 của B0 trên các seed dev, quy về 3600 s); và tối đa 1 va chạm liên quan xe bị TraCI can thiệp. Spec chỉ được chọn làm best nếu tỉ lệ va chạm trung bình theo seed ≤ trung bình B0 + 1 va chạm/giờ. Run bị loại vẫn tính vào budget. Báo cáo cuối công bố cả số strict lẫn số eligible, nên không giấu va chạm nào.

## Nhật ký

### 2026-10-25 — Task 1: Config loading và literature-proxy site file

Commit `4657a64` · Review: Approved (4 minor hoãn lại) · Trạng thái implementer: DONE_WITH_CONCERNS

**Đã làm:**
- `src/thesis_sumo/config.py`: `load_site/load_experiment/load_llm`, `Site.require()`, `MissingFieldDataError` (null bắt buộc thì raise, KeyError cho key sai). `load_site()` mặc định luôn đọc `config/site.yaml`, không tự fallback sang proxy.
- `config/site.yaml`: chỉ thêm `site_source: MEASURED`, mọi giá trị vẫn `null # TODO_MEASURE`.
- `config/site.proxy.yaml` (`site_source: LITERATURE_PROXY`): điền các giá trị TODO_MEASURE, mỗi key có `<key>_source` và `<key>_evidence`; các `edge:` để `null` cho Task 2.
- `docs/research/proxy_sources.md`: bảng giá trị, 13 nguồn [S1]–[S13], các giá trị phụ cho task sau.
- `tests/test_config.py`: 10 test.

**Lệnh tái tạo:**
- `.venv/Scripts/python -m pytest tests/test_config.py -v` (10 passed)
- `.venv/Scripts/python -m pytest` (13 passed)

**Tiêu chí:** đạt — null bắt buộc raise `MissingFieldDataError` nêu tên key; `load_site()` không đọc proxy ngầm; proxy được đánh dấu `LITERATURE_PROXY`; mọi giá trị proxy có source + evidence; tổng phase = cycle. Chưa đạt: không có.

**Số liệu proxy đã chọn:**

| Giá trị | Nguồn | Evidence |
|---|---|---|
| lane_widths_m = [3.5, 3.5, 3.5] (4 approach) | TCVN 13592:2022 cl. 9.2.3 Table 10; 3 làn từ OSM `lanes=3` và VietnamFinance 2026 | literature |
| `LVL_W.left_turn_banned` = true | không tìm thấy lệnh cấm tại nút này; suy từ các cấm rẽ trái ở trục lân cận (Tố Hữu–Vũ Trọng Khánh 2022; LVL–Khuất Duy Tiến) | assumed |
| các `left_turn_banned` khác, mọi `u_turn_banned` = false | OSM không có restriction relation gần nút | assumed |
| signal.cycle_s = 120 | TCCS 24:2018/TCĐBVN cl. 6.7.5; Mai et al. 2019 (127 s tại Láng Hạ–Láng) | literature |
| phases: LVL green 64 / yellow 4 / all-red 2; HĐT green 44 / yellow 4 / all-red 2 | 2 pha: TCCS cl. 6.4.2; yellow 4 s: TCCS cl. 6.7.6; all-red và split | assumed (cả key) |
| illegal_left.approaches = [LVL_W] | theo lệnh cấm; box-waiting của xe máy có ở Láng Hạ–Láng (Mai et al. 2019) | assumed |

**Giả định:** ban rẽ trái ở LVL_W và illegal left của nó; không có cấm rẽ nào khác; all-red 2 s; split xanh 64/44 s; HĐT coi là main street.

**TODO_MEASURE còn lại (toàn bộ trong `config/site.yaml`):** bề rộng từng làn; cấm rẽ từng approach; cycle, phases, split (có protected left hay không); approach có illegal left; turning counts theo loại xe 07:30–09:00.

**Vướng mắc / việc cho task sau:**
1. Task 2 phải kiểm tra hướng của `LVL_W` (có phải approach inbound giờ cao điểm sáng không); nếu không thì chuyển ban sang approach đúng. Chưa kiểm chứng.
2. Task 2 khi sinh tlLogic phải map `dir` `L`→`l`, `R`→`r`, nếu không sẽ sót link.
3. Lane width là chuẩn thiết kế, không phải đo thực tế.
4. Phase split không có cơ sở lưu lượng; chỉ yellow là literature.
5. Số liệu lưu lượng proxy lấy từ Láng Hạ–Láng (cùng hành lang, cách 2–3 km), gộp AM và PM; chưa có số đếm LVL × HĐT.

### 2026-10-25 — Task 2: Network (PLAN Phase 1)

Commits `cdcce12..4d52cfc` (`4d52cfc`) · Review: Approved, spec compliant (6 minor hoãn lại) · Trạng thái implementer: DONE_WITH_CONCERNS

**Đã làm:**
- Mạng tái tạo từ OSM bằng một lệnh (~3 s): cắt bán kính `cut_radius_m` 300 m, chỉ giữ 4 arm, một TLS static; `base.net.xml` rồi `site.proxy.net.xml` (patch plain-XML, không sửa tay `.net.xml`).
- Cấm rẽ trái ở LVL_W: connection chỉ `allow="custom1"` (cả hai internal lane); tlLogic sinh từ site file (6 pha 64/4/2/44/4/2, chu kỳ 120 s), `L`→`l`, `R`→`r`.
- Sinh `edge_table.csv`, `removed_nodes.csv`, `diagram.svg`; điền `approaches[].edge` trong cả `site.proxy.yaml` và `site.yaml` (là hình học, không phải số đo); thêm `pyproj>=3.6`.
- Gỡ 11 nút ưu tiên của ngõ/phố nhánh và 1 đèn trên arm (`cluster_2291072471_443393357`, HĐT x Nguyễn Thị Thập, 266 m phía NW); kết quả 8 edge, 9 node, chỉ còn TLS đích.

**Lệnh tái tạo:**
- `.venv/Scripts/python -m thesis_sumo.net.build --site config/site.proxy.yaml` (exit 0)
- `.venv/Scripts/python -m thesis_sumo.net.build --site config/site.yaml` (exit 2, nêu `lane_widths_m is null ... TODO_MEASURE`, không ghi file)
- `.venv/Scripts/python -m pytest tests/test_net.py -v` (18 passed); `.venv/Scripts/python -m pytest` (31 passed)

**Tiêu chí:** đạt — build từ đầu bằng một lệnh, netconvert không lỗi, có edge table và diagram, build lần hai byte-identical (CSV, patch, diagram). Chưa đạt: không có.

**Ánh xạ approach:**

| Approach | Edge | Hướng vào |
|---|---|---|
| LVL_W | `711526326#1` | từ SW, inbound giờ cao điểm sáng, có cấm rẽ trái |
| LVL_E | `37876499#0` | từ NE |
| HDT_N | `953158817#2` | từ NW; gộp way OSM không tên 1071601648 (xác nhận là HĐT qua Wikidata Q10769156) |
| HDT_S | `1346358303` | từ SE |

Kiểm tra kết nối khớp PLAN 1.3: r từ làn 0, s từ làn 0–2, l và t từ làn 2 ở cả 4 approach. Premise Task 1 (LVL_W là approach inbound) được xác nhận, giữ nguyên ban ở LVL_W; việc map `L`→`l` đã giải quyết.

**Giả định:** chỉ giữ 4 arm; đổi tên edge không tên bằng patch (không phải số đo); arm dài 261–594 m (netconvert giữ nguyên cả edge nằm một phần trong vùng cắt); lane width chỉ áp cho edge inbound (outbound mặc định 3.2 m); cấm U-turn làm giống cấm rẽ trái (proxy không dùng); màu tín hiệu s/r là `G`, l/t là `g`.

**TODO_MEASURE còn lại:** như Task 1 (bề rộng làn, cấm rẽ, cycle/phases/split, approach có illegal left, turning counts). Edge id không còn mở.

**Vướng mắc / việc cho task sau:**
1. Task 3/4: arm không đối xứng (261–594 m) nên khoảng cách xe được chèn vào khác nhau giữa các approach.
2. Làn trái nhất (BRT thực tế) vẫn cho mọi loại xe vì không import lane access (giống OWZ export).
3. Header netconvert trong net đã commit chứa đường dẫn tuyệt đối và timestamp, đổi mỗi lần build (test bỏ qua).
4. Cấm U-turn là re-add `custom1`; nếu U-turn violator ngoài scope thì nên chỉ delete.

**Review:** Approved; 6 minor hoãn lại: (1) độ dài arm 261–594 m so với bán kính cắt 300 m; (2) header netconvert chứa đường dẫn tuyệt đối và timestamp; (3) làn outbound giữ 3.2 m mặc định, chưa ghi trong file proxy; (4) chưa kiểm tra mọi link TLS đều xanh ở một pha nào đó; (5) `KeyError` trần khi chưa đặt `SUMO_HOME`; (6) test tích hợp chấp nhận cả `G` lẫn `g`.

### 2026-10-25 — Task 3: B0 vTypes, demand và sumocfg (PLAN Phase 2 phần 1)

Commits `4d52cfc..00cb1f5` (`00cb1f5`) · Review: Approved, spec compliant (5 minor hoãn lại) · Trạng thái implementer: DONE_WITH_CONCERNS

**Đã làm:**
- `rules/compiled/B0/vtypes.add.xml`: 3 `vTypeDistribution` (`car`, `moto`, `moto_violator`), mỗi cái một vType `<id>_B0`, `laneChangeModel="SL2015"`; moto_violator = motorcycle mặc định + vClass `custom1` (kiểm bằng libsumo).
- `src/thesis_sumo/demand/build_demand.py`: 16 route ứng viên (inbound→outbound), movement r/s/l/u/`illegal_l`; đọc `turn_counts.csv` chặt (raise khi sai cột, interval khác 900 s, count âm, car `illegal_l`, count không khớp route); routeSampler chạy một lần mỗi loại xe, kiểm tổng số xe.
- `src/thesis_sumo/sim/sumocfg.py`: `write_sumocfg` dùng `sumo --save-configuration` (SUMO tự từ chối option lạ); outputs.add.xml gồm 12+12 instant loop, SaveTLSStates, poly `fcd_zone` bán kính 60 m; tripinfo, fcd `.xml.gz`, lanechange, statistic, collision, SSM (PET).
- `data/observed/SYNTHETIC/` (4297 xe/h, 80–85 % moto, chỉ để test pipeline), `routes_SYNTHETIC.rou.xml` (seed 1: car 783, moto 3412, moto_violator 102).

**Lệnh tái tạo:**
- `.venv/Scripts/python -m thesis_sumo.demand.build_demand --net ... --counts data/observed/<day>/turn_counts.csv --seed N`
- `.venv/Scripts/python -m pytest tests/test_demand.py tests/test_sumocfg.py -v` (15 passed); `.venv/Scripts/python -m pytest -q` (46 passed)

**Tiêu chí:** đạt (theo review: spec compliant). Chưa đạt: không có.

**Smoke run 3600 s, seed 1, B0, SYNTHETIC (thông tin cho Task 4):**

| Mục | Kết quả |
|---|---|
| Exit / thời gian | 0 / 117 s (~31× real time) |
| Chèn xe | 4297/4297, waiting cuối 0 |
| Halting | max 56, mean 19 (mạng tải nhưng không gridlock) |
| Collision → teleport | 5 (2 car rear-end cuối làn 2 ở HDT_N, LVL_E; 1 moto side ở LVL_W straight; 2 moto ở HDT_N, HDT_S straight) |
| Dung lượng | fcd 15.8 MB, tls_states 5.9 MB, detectors 6.2 MB, ssm 0.16 MB (789 PET conflict) |
| Cảnh báo log | 69 438 "bad internal lane geometry" (links 10/22), 506 "SSM device detected collision", 27 emergency braking |

**Giả định:** interval turn_counts tính bằng giây mô phỏng; `departLane="best" departSpeed="max"` cho mọi xe; seed routeSampler = seed + k·1000; output mang id vType thành viên (`moto_B0`) nên metrics cần map type→distribution; personCapacity moto = 1 theo binary (docs ghi 2); tâm fcd_zone lấy từ node trong net; SYNTHETIC có độ lớn tùy ý.

**TODO_MEASURE còn lại:** như Task 1–2 (không có mục mới).

**Vướng mắc / việc cho task sau:**
1. Task 4 phải báo cáo và tìm nguyên nhân 5 collision/teleport (nghi sublane + làn trái/u nhường nhau); chưa ẩn bằng option nào.
2. SSM không tính được PET cho cặp trái đối đầu HDT (links 10/22) do hình học net, gây ~12 MB log/run; runner nên tóm tắt log, không tắt. Không ảnh hưởng illegal left của LVL_W (link 16).
3. Task 4 chuyển `TURN_COUNT_COLUMNS` sang `schema_observed.py` (R3); T6 và T10 dùng cùng đơn vị interval.
4. Warm-up phải phủ thời gian chạy từ điểm chèn tới vạch dừng (~16 s HDT_S đến ~36 s LVL_E).
5. `run.sumocfg` chứa đường dẫn tuyệt đối, run dir không di chuyển được; input ghi bằng hash trong manifest (Task 4).

**Review:** Approved; 5 minor hoãn lại: (1) seed stride `seed+k*1000` có thể trùng; (2) `read_turn_counts` không loại hàng trùng/interval lệch (liên quan generator T6); (3) `device_rerouting` true âm thầm thành probability 1; (4) test sumocfg chạy với cwd=cfg.parent nên chưa kiểm claim output tương đối; (5) id interval `{begin:g}` thành `1e+06` (thẩm mỹ).

### 2026-10-25 — Task 4: Runner, manifest và chuyển đổi sang observed schema (PLAN Phase 2.4, 5.1)

Commits `a8b0722`, `096ce58` (`00cb1f5..096ce58`) · Review: lần 1 "Needs fixes" (4 Important), fix round 1 xử lý hết, re-review "all findings addressed" · Trạng thái: code ✅, operator đang chạy B0 3 seed + điều tra va chạm (Task 4 vẫn 🔄) · Session từng dừng một lần vì chạm usage limit rồi chạy tiếp.

**Đã làm:**
- `src/thesis_sumo/schema_observed.py` (R3): cột §5.1, `INTERVAL_S`, `MOVEMENTS`, `VCLASSES`, `normalise_state`, helper chu kỳ; `build_demand.py` import từ đây.
- `src/thesis_sumo/sim/runner.py`: `run()`, `run_many()` (spawn Pool, mỗi job một SUMO), CLI, `manifest.json` (git hash, sumo version, hash net/routes/spec/site, config hiệu lực, teleport/va chạm, backlog, cảnh báo log, valid). Không có option nào ẩn teleport hay va chạm; output trong `experiments/runs/<spec_id>__<day>/seed_XX/`.
- `src/thesis_sumo/sim/outputs.py`: `to_observed_schema(run_dir)` ghi CSV vào `observed_schema/` bằng một lượt đọc fcd; đọc được `.xml` và `.xml.gz`.
- Fix round 1: test với "sự thật độc lập" (`tests/test_outputs_synthetic.py`, net và fcd tự dựng, giá trị kỳ vọng tính tay); `opposing_of` raise `ValueError` rõ ràng; xe biến mất trong box không còn bị gán nhãn sai; test determinism; `n_teleports_noncollision`; áp dụng R8–R11 (bảng `traversals`, `queue_range_m` 80, chính sách hợp lệ, `check_shared_green`).

**Lệnh tái tạo:**
- `.venv/Scripts/python -m thesis_sumo.sim.runner --spec B0 --day SYNTHETIC --seeds 1 2 --site config/site.proxy.yaml --end 900 --nproc 2` (thêm `--gui` để dùng traci + sumo-gui)
- `.venv/Scripts/python -m pytest -q` (75 passed)

**Tiêu chí:** đạt phần code (75 test pass, schema đúng cột, manifest đủ trường, smoke run chạy). Chưa đạt/chưa làm: chạy B0 3600 s × 3 seed, điều tra nguyên nhân va chạm, kiểm tra sumo-gui (bước 3–4, operator).

**Smoke sau fix (900 s, SYNTHETIC, B0):**

| seed | wall | teleport tổng / không do va chạm | va chạm (rear/lateral/junction/other) | backlog cuối/max | valid_strict |
|---|---|---|---|---|---|
| 1 | 23,5 s | 2 / 0 | 2 (1/1/0/0) | 0/1 | False |
| 2 | 23,6 s | 1 / 0 | 1 (0/1/0/0) | 0/1 | False |

- Mọi teleport của B0 là do va chạm (jam/yield/wrongLane = 0). Hàng đợi tối đa 37,9 m, không bị cắt ở 80 m. `traversals` 930 hàng (4 hàng `t_exit` NaN do còn trong mạng lúc 900 s). fcd ~5,1 MB / 900 s (~20 MB / giờ). Ước tính run 3600 s ~85 s + ~6 s chuyển đổi.

**Giả định:** approach_group = approach id (trạng thái lấy từ các link đi thẳng); turn_counts bin theo thời điểm qua vạch dừng; `lateral_snapshots` chỉ giữ xe đang dừng, cả hai vclass; console bị bỏ trong batch run (toàn bộ nằm ở `sumo.log`, manifest có `warnings_top`); thư mục seed bị xóa và dựng lại khi chạy lại; `exit_approach` map theo góc gần nhất (tối đa 45°); `queue_range_m` 80 là lựa chọn mô hình, thay bằng phạm vi camera thực.

**TODO_MEASURE / TODO_DECIDE còn lại:** TODO_MEASURE như Task 1–3 (không có mục mới). `validity.max_collisions_per_hour` đang `null` (điền từ B0 p90, sàn 2, sau khi operator chạy xong); `queue_range_m` thay bằng độ phủ camera đo được.

**Vướng mắc / việc cho task sau:**
1. Operator: chạy B0 3 seed, điều tra va chạm (rear-end làn l/u, moto side collision trên làn nội bộ đi thẳng; nghi sublane), điền `max_collisions_per_hour`.
2. Task 6: generator phải sinh `traversals` và `box_queue` theo R9/R11, censor hàng đợi 80 m, thêm lane→movement map vào site file.
3. Task 10: M6/M8 dùng `traversals`; M5 thêm `share_censored`; M7b PET từ `ssm.xml`.
4. Task 9: runner gọi `controller_factory(backend, inputs, run_dir)` rồi `.on_step(t)`, controller có thể có `intervened(vehicle_id, t)`.
5. `wall_time_s` chưa gồm thời gian chuyển đổi.

**Review:** lần 1 Needs fixes (4 Important: dẫn xuất chưa được kiểm với sự thật độc lập; ngữ nghĩa box_queue → R11; KeyError ở opposing; xe biến mất trong box bị gán nhãn sai). Fix round 1 xử lý cả 4 cộng minor 4 (determinism) và 9 (teleport không do va chạm); re-review: all findings addressed. 9 minor hoãn lại: 3 mới (`box_queue` NaN/NaN mơ hồ giữa "còn trong box" và "chưa có xe vào", outputs.py:556; `is_eligible` chia cho 0 khi cửa sổ dài 0, runner.py:869; đẳng thức `n_tp_noncoll` chỉ nằm trong comment, runner.py:943) và 6 của review đầu (1–3, 5–8: hàng movement trùng, `setdefault` làn nội bộ, assert gắn với B0, `run()` bọc mọi exception / Pool có thể treo, `rmtree` im lặng, chưa test đủ cả hai biến thể `.xml`/`.xml.gz`, `empty_table` không dùng).

### 2026-10-25 — Task 6: Proxy targets và observed data PROXY_D1–D5 (spec 4.2)

Commits `a76bca4`, `8d752b9` (`9b8d013..8d752b9`) · Review: Approved sau 1 fix round (I1 tiêu chí 15 % bị định nghĩa lại so với nominal; I2 nhãn literature nói quá → R13; minor 2 snapshot thiếu xe chờ trong box) · Trạng thái implementer: DONE_WITH_CONCERNS

**Đã làm:**
- `data/proxy/targets.yaml` (mỗi target có value, unit, family, `between_day_cv`, source, evidence) và `docs/research/proxy_targets.md` (bảng target, định nghĩa Task 10 phải dùng lại, thống kê dẫn xuất, giới hạn, trích dẫn [T1]–[T8]).
- `src/thesis_sumo/proxy/generate.py`: generator mức sự kiện từng xe (không đọc output SUMO) sinh 7 CSV + `manifest.json`; CLI sinh D1–D5 (seed 101–105) và `scenario/demand/routes_PROXY_D{k}.rou.xml` qua `build_demand` (R2).
- `lane_movements` thêm vào `site.proxy.yaml` (assumed) và `site.yaml` (`null # TODO_MEASURE`) theo R9; `data_split` trong `experiment.yaml`: calibration D1–D3, validation D4–D5 (chỉ stage hunk của Task 6, hunk của operator giữ nguyên).
- Fix round 1: chuẩn hóa day factor (chia cho trung bình D1–D5 của từng target, nên trung bình 5 ngày = giá trị nominal; CV giữa các ngày không đổi); R13 áp dụng cho cả 14 nhãn `literature` → `literature_transferred` kèm `transfer_note` (cả `signal.cycle_s`); `add_box_waiters` đưa xe chờ trong box vào `lateral_snapshots` như `sim.outputs`.

**Lệnh tái tạo:**
- `.venv/Scripts/python -m thesis_sumo.proxy.generate` (D1–D5 + routes, ~14 s)
- `.venv/Scripts/python -m pytest tests/test_proxy.py tests/test_config.py -q -rxX` (38 passed, 1 xfailed); full suite 102 passed, 1 xfailed, 1 failed (xem Vướng mắc 1)

**Tiêu chí:** đạt — mọi scalar trong ±15 % của nominal trên trung bình thô 5 ngày, trừ car red running (xfail, bên dưới); ngày commit tái tạo được từng dòng; routes khớp turn_counts; site đo thực còn null thì raise. Chưa đạt: car red running +18,3 % (~22 sự kiện trong 5 ngày, sai số Poisson ~21 %, nên không khả thi với 5 ngày; `xfail(strict=True)`; kiểm tra chạy 36000 s cho thấy generator không lệch).

**Target chính (đều là proxy, không phải số đo tại nút LVL x HDT):**

| Target | Giá trị | Nguồn | Evidence |
|---|---|---|---|
| G0 lưu lượng | LVL_W 2620, LVL_E 2130, HDT_N 1800, HDT_S 1630 (tổng 8180 veh/h) | tổng từ [S5] Láng Hạ–Láng; chia approach là giả định | assumed |
| G0 CV giữa các ngày của lưu lượng | 0,087 | [T6] Abdy & Hellinga 2007 (Bắc Mỹ) | literature_transferred |
| G0 tỉ lệ xe máy | 0,865 | [S5] 14148/16352 | literature_transferred |
| M1 headway bão hòa xe máy | 0,254 s, cv 0,56 | [T1] Tuan & Man 2015 (HCMC, quy theo bề rộng); cv từ [T2] | literature_transferred |
| M1 hệ số ô tô / xe máy | 1,4 | [T1] f_PC | literature_transferred |
| M2 đi sớm (xe máy / ô tô) | LVL 9,45 % / 0,27 %; HDT 15,82 % / 0,68 % | [S5] Table 3 (LVL), Table 2 (HDT) | literature_transferred |
| M3 vượt đèn đỏ (xe máy / ô tô) | LVL 6,49 % / 0,27 %; HDT 11,06 % / 0,50 % | [S5] Table 3 / Table 2 | literature_transferred |
| M4 xe máy đứng quá vạch dừng | 63 % | [T3] Malaysia | literature_transferred |
| M6 tốc độ tiếp cận / trong nút (xe máy) | 27,3 ± 5,2 / 21,3 ± 5,1 km/h | [T2] Minh et al. 2005 (Hà Nội) | literature_transferred |
| M7a xe rẽ trái trái luật chờ trong box | trung bình 6 mỗi chu kỳ (vào 7,5, var/mean 1,5) | chỉ có mô tả định tính ở [S5] | assumed |
| M7a thoát sớm qua khoảng trống | 20 % số xe vào | [S5] định tính | assumed |
| M7b clear lag (PET proxy) | 5,65 s, lognormal cv 0,5 | dựng trên [T7] PET 2,15 s (Đài Loan) + offset giả định | assumed |
| M7c trễ xuất phát của đường cắt | 0,3 s mỗi xe chờ | không tìm thấy nguồn | assumed |
| M8 chọn sai làn khi rẽ (xe máy / ô tô) | 0,25 / 0,05 | không có số đo; gợi ý yếu từ [T8] | assumed |

**Số liệu sinh ra (dẫn xuất):** 7602–9099 xe/ngày (3600 s); 224 xe rẽ trái trái luật/giờ; hàng đợi 11–13 m (tối đa 24 m, không bị cắt ở 80 m); M7a `n_waiting` mean 6,0, var 7,8, max 13 (Task 5 dùng số này). Lệch so với nominal: car early start −12,1 %, car wrong-lane +8,3 %, M7c slope −5,7 %, M7c intercept +4,3 %, red running xe máy LVL_W −5,5 %; còn lại trong ±4 %.

**Giả định:** tỉ lệ rẽ và cả khối M7 là assumed; một day factor chung cho mọi approach (tương quan hoàn toàn); lane markings theo layout connection của netconvert (OSM không có `turn:lanes`; làn trái nhất BRT được coi là làn thường); offset tín hiệu 0; `box_wait_position_share` assumed. Định nghĩa M1, M2/M3 (ngưỡng 10 s), M7b, M7c, M8 nằm ở `docs/research/proxy_targets.md` §2 và Task 10 phải dùng y hệt.

**Lưu ý quan trọng — day factor đã chuẩn hóa:** trung bình 5 ngày của mọi target bằng đúng nominal theo cấu tạo, nghĩa là D1–D5 bị ràng buộc với nhau qua trung bình (calibration D1–D3 và validation D4–D5 không độc lập hoàn toàn); độ phân tán giữa các ngày không đổi. Một generator tạo cả 5 ngày nên validation D4–D5 trên proxy yếu hơn validation trên ngày thật; `d_day_day` đến từ CV giả định nên R chỉ mang tính minh họa.

**TODO_MEASURE còn lại:** như Task 1–5 (thêm `lane_movements` trong `site.yaml`). Toàn bộ target assumed ở trên chờ số đo thật.

**Vướng mắc / việc cho task sau:**
1. `tests/test_runner.py::test_is_eligible_needs_collision_threshold` fail khi `validity.max_collisions_per_hour: 15` của operator (chưa commit) nằm trong working tree; ai commit giá trị đó phải sửa test.
2. Rủi ro G0: lưu lượng proxy gấp ~2 lần SYNTHETIC với rẽ trái cho phép ở làn 2; nếu B0 không phục vụ nổi thì cổng GEH loại run. Operator nên kiểm B0 trên PROXY_D1 sớm (đã thành R17).
3. Hàng đợi ngắn và dày (12–14 m); mật độ M5 bị ô tô chi phối; Task 10 có thể cần M5 từ `lateral_snapshots`, một định nghĩa duy nhất cho cả hai phía.
4. [T3], [T4], [T8] chỉ đọc qua abstract/snippet; [T4] nói về xe đạp điện, không phải xe máy.

**Review:** Approved sau 1 fix round. Minor hoãn lại: `generate.py` ~700 dòng (nên tách tables/site_plan); đuôi hàng đợi không nối chuỗi `JAM_GAP`; `git_commit` trong manifest là commit cha; generator import `sim.outputs` (kéo theo sumolib); [T4] chỉ mang tính định tính; day factor chuẩn hóa ràng buộc D1–D5 (đã nêu ở trên).

### 2026-10-25 — Task 5: In-box waiting experiment (PLAN Phase 3, quyết định (a) native)

Commits `aedc7c1`, `e0c1faf` (`8d752b9..e0c1faf`) · Review: Approved sau 1 fix round (I1 chỉ thử dòng đối diện dày; I2 minGap 1,9 chỉ ngoại suy; I3 từ vựng evidence mở rộng toàn cục + hằng số trùng lặp) · Trạng thái implementer: DONE_WITH_CONCERNS

**Đây từng là hard stop của PLAN (Phase 3); theo R1 và R14 nó chỉ ghi quyết định rồi đi tiếp. Giải thích cho Viktor:**
- Câu hỏi: xe máy rẽ trái trái luật chờ ngay giữa nút (trong "box") — SUMO có tự mô phỏng được cảnh này không, hay phải sửa mạng (phương án (b), `box_edge`, thêm cạnh/đèn riêng cho box)?
- Quyết định (a): dùng SUMO nguyên bản (native). Thí nghiệm cho thấy SUMO tự để tối đa 8 xe chờ trong box, xếp 2 hàng ngang, không deadlock, không teleport ngoài va chạm, và thoát đều đặn ngay sau khi hướng đối diện hết xanh (mục tiêu M7a trung bình là 6 xe, nên 8 là đủ).
- Vì sao không chọn (b): native đã đạt yêu cầu, còn (b) tốn công dựng và kiểm lại mạng mà không có bằng chứng cần thiết. Điều phối xác nhận ở R14 và quy định cách điều khiển bằng rule ở R15.
- Chưa hoàn hảo: sức chứa 8 thấp hơn p90 của target (10) nên đuôi phân phối M7 bị cắt. Có thể nâng bằng cách hạ `minGap` (xem bảng). Có 0 % thoát sớm khi dòng đối diện rất dày, nhưng 62 % khi dòng đối diện ở mức ngày proxy (target 20 %), nên rule LLM chủ yếu phải kìm thoát sớm.
- Viktor có thể đảo ngược quyết định này (đổi `illegal_left.mode` sang `box_edge` và yêu cầu dựng lại net); chi phí là dựng lại net và chạy lại các vòng (R14), và `box_edge` hiện chưa được cài (`NotImplementedError`).

**Đã làm:**
- `experiments/phase3/box_capacity.py` (một file ~530 dòng): 25 run × 900 s (seed 1–5 mỗi kịch bản), observer TraCI không can thiệp, ghi theo từng bước số xe trong box, vị trí ngang, thoát khỏi box so với vàng đối diện, deadlock, teleport, va chạm, tương tác với đường cắt; kết quả `experiments/phase3/results_native.csv`, báo cáo `docs/research/phase3_box_capacity.md`, 2 hình PNG.
- `illegal_left.mode: native` trong `config/site.proxy.yaml` (`mode_evidence: experiment`, có `mode_source`); `config/site.yaml` để `mode: null # TODO_DECIDE`. `build_site_net` bắt buộc có `mode`, `ValueError` nếu lạ, `NotImplementedError` nếu `box_edge`. Không dựng patch `box_edge`, không có `test_box_edge_signal` vì (b) không được chọn.
- Fix round 1: kịch bản `target_modopp` (đối diện 1300 xe máy + 200 ô tô/h, gần PROXY_D1–D3) và `sat_mg18` (minGap 1,8 m); `results_<tag>.csv` gộp theo (scenario, seed); `EVIDENCE`, `EXPERIMENT_EVIDENCE`, `EXPERIMENT_EVIDENCE_KEYS = ("illegal_left.mode",)`, `allowed_evidence` đặt trong `config.py` (nhãn `experiment` chỉ hợp lệ cho khóa này), bỏ các bản sao trong tests.

**Lệnh tái tạo:**
- `.venv/Scripts/python experiments/phase3/box_capacity.py --nproc 8 --tag native` (thêm `--reanalyse` để phân tích lại run đã xong)
- `.venv/Scripts/python experiments/phase3/box_capacity.py --scenarios target_modopp sat_mg18 --tag native --reanalyse`
- `.venv/Scripts/python -m pytest -q` (105 passed, 1 xfailed, 1 failed do test eligibility, xem Task 6)

**Tiêu chí:** đạt — log từng bước số xe/vị trí ngang/thoát so với vàng-đỏ/deadlock/teleport/tương tác đường cắt; số liệu, quyết định và md. Chưa đạt/không làm: `test_box_edge_signal` (vì chọn (a)).

**Sức chứa của box (xe moto_violator dừng trong box, đo được, 5 seed mỗi mức):**

| `minGap` custom1 | Sức chứa |
|---|---|
| 2,5 m (B0) | 8 |
| 1,8 m | 10 |
| 1,0 m | 12 |

Các mức 0,5 m (→ 14), 1,9–2,5 m (→ 8) và cột thứ ba khi `minGapLat` ≤ 0,25 chỉ là dự đoán theo công thức hàng, chưa thử.

**Thoát sớm (so với target 20 % số xe vào):**

| Dòng đối diện | Thoát sớm |
|---|---|
| Rất dày (4700 xe/h, kịch bản gốc) | 0 % |
| Mức ngày proxy (~1500 xe/h, `target_modopp`) | 62 % (4,17 mỗi chu kỳ); chờ trung bình 2,6, p90 6, max 7 |

**Số liệu khác:** xe chờ dừng ở via point, 2 hàng ngang (posLat ≈ −1,15 và 0…+0,65 m); thoát đầu tiên 4,7 s sau vàng đối diện (0,7 s sau đỏ), headway 0,52–0,68 s (target 0,5 s); box trống sau 8,2 s với 8 xe và 10,4 s với 12 xe; 3,4–4,6 xe còn trong box lúc HĐT xanh, làm làn 2 HDT_N qua vạch trễ 0,4–1,1 s (B0) hoặc 1,6–2,7 s (12 xe), hệ số ~0,2–0,5 s mỗi xe (target M7c 0,3); không deadlock, không teleport ngoài va chạm, thời gian ở box tối đa 70,4 s; 334 va chạm trong 25 run, gần hết giữa xe đi thẳng cùng dòng (vấn đề sublane của B0), 1 va chạm có xe vi phạm.

**Giả định:** nhu cầu thí nghiệm là tổng hợp, không phải dữ liệu proxy (dòng đối diện 4700 xe/h chọn để không còn khoảng trống); chu kỳ 0 bị loại khỏi thống kê gộp (khởi động); "sức chứa" = số xe halting tối đa trong box lúc xanh đối diện; các khoảng tham số khuyến nghị cho `illegal_left_box` là giả định, Task 7 phải tìm nguồn và đặt cận.

**TODO_MEASURE / TODO_DECIDE còn lại:** không có TODO_MEASURE mới. `illegal_left.mode` trong `site.yaml` là TODO_DECIDE, chờ số đếm xe chờ trong box thực.

**Vướng mắc / việc cho task sau:**
1. Đuôi M7 bị cắt ở 8: cận `minGap` của custom1 ở Task 7 phải cho ≤ 1,9 m (R15 đặt [0,5; 2,5]).
2. SSM báo ~300 cặp "va chạm" giả mỗi run giữa xe chờ và xe thẳng LVL_E (điểm chờ cách tâm làn 1,61 m, nửa bề rộng 1,60 m), PET ≈ 0; không dùng SSM cho M7 (R16).
3. B0 vẫn có 9–27 teleport do va chạm mỗi run 900 s giữa xe đi thẳng (vấn đề Task 4; R17).
4. Gợi ý `p_early_leave` TraCI trong md bị R15 thay thế: thoát sớm điều khiển bằng `jmTimegapMinor`.

**Review:** Approved sau 1 fix round. Minor hoãn lại (5): p90 bị cắt cần ghi chú; tham số dòng dày là tổng hợp; thông báo lỗi `mode` ở site thật (TODO_MEASURE hay TODO_DECIDE); `box_capacity.py` ~530 dòng chưa có test; parse chuỗi id dễ vỡ; `EXPERIMENT_EVIDENCE_KEYS` chỉ được enforce trong test.

### Ghi chú tiến độ — tạm dừng lần 2

Phiên làm việc dừng lần thứ hai vì chạm usage limit (Task 4 operator và Task 5 coder bị cắt giữa chừng, đã resume qua SendMessage), sau đó chạy tiếp. Task 4 vẫn 🔄 (operator chạy cổng B0 trên PROXY_D1); Task 7 🔄.

### 2026-10-25 — Task 4 (phần operator): chiến dịch B0, điều tra va chạm, ngưỡng validity

Commit `ed6030e` · Trạng thái: DONE_WITH_CONCERNS · Task 4 chuyển ✅ (nguyên nhân đã tìm ra, sửa ở Task 4b)

**Đã làm:** chạy B0 trên SYNTHETIC 3 seed x 3600 s; thử cổng R17 trên PROXY_D1; lập catalogue 31 va chạm, chụp màn hình sumo-gui, thí nghiệm một-yếu-tố trên net; đặt `validity.max_collisions_per_hour`. Script và kết quả nhỏ ở `experiments/operator/task4/` (run thô không commit).

**Lệnh tái tạo:** `.venv/Scripts/python -m thesis_sumo.sim.runner --spec B0 --day SYNTHETIC --seeds 1 2 3 --site config/site.proxy.yaml --nproc 3` (4 phút 38 s tổng); PROXY_D1 chạy bằng binary `sumo` qua `experiments/operator/task4/run_variant.py proxyD1_base --routes scenario/demand/routes_PROXY_D1.rou.xml`.

**Kết quả (net cũ, bề rộng làn thoát 3,2 m, check-junctions mặc định tắt):**

| Kịch bản | Va chạm/h theo seed 1, 2, 3 | Ghi chú |
|---|---|---|
| B0 SYNTHETIC | 5, 16, 10 (p90 14,8) | teleport không do va chạm 0/0/2, backlog 0 |
| B0 PROXY_D1 | 62, 52, 46 (p90 60) | backlog cuối 25/0/133; runner chết `bad allocation` ở 800–900 s do SSM tràn log (~1,5 triệu dòng/giờ) |
| Thử: làn thoát 3,5 m (scratch) | SYNTHETIC 0, 2, 0 (tổng 31 → 2); PROXY_D1 tổng 160 → 10 | nhưng PROXY_D1 sinh teleport jam/yield 18/32/10 và backlog 73/2/0 |

- **Nguyên nhân:** bước nhảy bề rộng, 3,5 m làn vào so với 3,2 m làn ra và làn nội bộ (netconvert cho làn nội bộ bề rộng của làn ra). Xe máy sublane bám vạch làn (posLat tới ±1,5 m), bước vào làn nội bộ hẹp hơn nhưng tâm vẫn cách nhau 3,5 m. Trong 31 va chạm: 20 là vào nút, 8 ở cuối làn gần vạch dừng, 3 là va chạm sublane khi đổi làn cách vạch 16–18 m (vốn có của SUMO, còn lại 2 va chạm dư sau khi sửa).
- Các yếu tố khác: `--lateral-resolution` 0,2 cho 40 va chạm (tệ hơn), 0,8 cho 12 (tốt hơn nhưng chưa hết); LC2013 cho ô tô không dùng được cùng sublane; `--collision.check-junctions` đẩy 31 lên 86 (thêm va chạm giữa các làn nội bộ cắt nhau).
- Kiểu `junction` trong output KHÔNG phải do check-junctions: va chạm trên làn nội bộ luôn được ghi là `junction` (15/31 ở run mặc định). Vậy 203/250 va chạm Phase 3 là va chạm thật trên làn nội bộ, khớp với vấn đề bề rộng. Đã trả lời câu hỏi của R17.
- `validity.max_collisions_per_hour: 60` (đặt tạm, từ p90 PROXY_D1), thay bằng giá trị đúng ở Task 4b.
- GUI: sumo-gui không vẽ bề rộng làn nội bộ; chỉ chụp được một ảnh mỗi phiên (crash khi chụp liên tiếp). t=128 s: box giữ 1–3 xe máy, khớp với `box_queue`.

**Tiêu chí:** đạt phần điều tra (có nguyên nhân, đề xuất sửa cụ thể). Chưa đạt: cổng R17 trên PROXY_D1 FAIL (46–62/h so với giới hạn 5/h), dẫn tới R21–R24 và Task 4b.

**Giả định:** số liệu PROXY_D1 lấy từ binary `sumo` không có fcd/ssm/detector (trên SYNTHETIC cách này tái tạo đúng 5/16/10).

**TODO_MEASURE còn lại:** như Task 1–3.

**Vướng mắc / việc cho task sau:** (1) áp patch bề rộng làn thoát (R21); (2) SSM tràn log, cần tắt/gộp (R22); (3) PROXY_D1 bão hòa kể cả khi hết va chạm, cần tìm nút thắt (R23); (4) test `test_is_eligible_needs_collision_threshold` fail với giá trị 60, coder sửa (làm ở 4b).

### 2026-10-25 — Task 4b: sửa bề rộng làn thoát, SSM, và chạy lại cổng B0 (R21–R24)

Commits `52ae484`, `90b302c` (`586349a..90b302c`) và operator `eae2050`, `1f1281f` · Review: lần 1 "Needs fixes" (I1 chưa có test cho parser cảnh báo không gộp; I2 regex tham lam có thể che cảnh báo), fix round 1 xử lý hết, review sạch · Trạng thái: coder DONE_WITH_CONCERNS, operator DONE_WITH_CONCERNS · ✅

**Đã làm (coder):**
- R21: danh sách `exits` trong `site.proxy.yaml` (4 edge ra: `711526328#0`, `37877893#0`, `408823207#0`, `37871458#0`, mỗi cái `[3.5, 3.5, 3.5]`, evidence `literature`) và `site.yaml` (`null # TODO_MEASURE`); `build_net` thêm `exit_edges`/`outbound_edges`; `_lane_patch` ghi cả edge ra; build raise `MissingFieldDataError` nêu `exits.2.lane_widths_m` khi null. Net dựng lại byte-identical với net scratch của operator; cả 56 làn đều 3,5 m. 4 test mới (internal lane bằng làn ra, exits ánh xạ đúng, null và đếm sai làn bị từ chối).
- R22: `sim.ssm.mode` (`"off"`, `violators`, `all`; phải đặt trong dấu nháy vì PyYAML đọc `off` là `False`), mặc định `"off"` (không ghi option `device.ssm.*`; đã đo byte-identical với `probability 0`); `--ssm violators` dùng `--device.ssm.explicit` (217 xe vi phạm ở PROXY_D1); `--aggregate-warnings 20` luôn bật, không bao giờ `-W`. Sửa `summarise_log` để đếm đúng dòng "N total messages of type": log gộp (libsumo, 68 dòng) và không gộp (sumo, 119 901 dòng) cho cùng `n_warnings` 119 877.
- Fix round 1: test parser cảnh báo thuần; regex fullmatch (nếu sai thì chỉ đếm thừa tối đa 20 dòng, không bao giờ giấu); `write_sumocfg` dùng `Path.resolve()` (sửa lỗi `runs_root` tương đối); manifest có `ssm_n_explicit`; đánh dấu `phase3_box_capacity.md` là superseded bởi R21.

**Lệnh tái tạo:**
- `.venv/Scripts/python -m thesis_sumo.net.build --site config/site.proxy.yaml`
- `.venv/Scripts/python -m thesis_sumo.sim.runner --spec B0 --day PROXY_D1 --seeds 1 --site config/site.proxy.yaml --end 600 --ssm off`
- `.venv/Scripts/python -m pytest -q` (172 passed, 1 xfailed)
- Operator: `experiments/operator/task4b/run_b0.sh` (`... --spec B0 --day PROXY_Dk --seeds 1 2 3 --nproc 3 --ssm off --end 1800`)

**Smoke 600 s, PROXY_D1, seed 1, SSM tắt:**

| Net | Wall | Va chạm | Teleport (tổng / không do va chạm) | Đang chạy lúc 600 s |
|---|---|---|---|---|
| Mới, thoát 3,5 m | 51,2 s | 0 | 0 / 0 | 330 |
| Cũ, thoát 3,2 m | 46,5 s | 8 | 8 / 0 | 258 |

**Cổng B0 chạy lại (operator, PROXY_D1–D3 x 3 seed, 1800 s, check-junctions TẮT):**
- Va chạm/h: 2, 0, 2, 2, 6, 0, 0, 2, 0; trung bình 1,56, p90 2,8, nên ngưỡng `max(2, ceil(2,8)) = 3`, đóng băng ở `eae2050`. R17 (≤ 5/h) ĐẠT (từ 46–62/h trên net 3,2 m). Toàn bộ là va chạm side. Lưu ý lượng tử hóa: với 1800 s một va chạm bằng 2/h.
- Chạy 1800 s thay 3600 s vì D1 3600 s mới tới t≈1750 s sau 10 phút (20+ phút/run); key `sim.calib_end_s` chưa tồn tại lúc đó (thêm ở Task 9 fix 1, R31).
- **B0 chưa ELIGIBLE:** 7/9 run có teleport jam/yield (D1: 14, 22, 10; D2: 22, 23, 2; D3: 0, 11, 0), D1 seed 1 còn 161 xe chưa chèn. Chỉ D3 seed 1 và 3 là `valid_strict`. (Văn bản báo cáo operator ghi "8/9 run" nhưng bảng của chính nó cho 7/9; ở đây dùng số theo bảng.)
- **Nút thắt (R23):** mọi teleport jam/yield là xe máy (chỉ 4 ô tô trong ~130 dòng in ra), thành cụm cùng giây; lần đầu hầu như luôn ở vạch dừng làn 2 (dùng chung S/L/R) của LVL_W rồi lan tới các link làn 2 trong box. Link 10/22 là foe nhưng nhường một chiều, không phải deadlock tương hỗ. Thí nghiệm một-yếu-tố (D1, 3 seed): bỏ 217 xe rẽ trái trái luật (2,4 % xe) thì teleport tổng còn 0, 0, 3; bỏ mọi rẽ trái thì 0, 3, 2 và không còn jam/yield; `minGap` 1,5 m còn tệ hơn (68 và 103 teleport ở seed 1, 2). Kết luận: do hành vi vType mặc định của B0 (xe rẽ trái trái luật chờ trong box), KHÔNG phải artefact mạng, không đề xuất patch; đây là mục tiêu cải thiện của LLM (R23).
- Nhu cầu D1 cao hơn D2/D3 khoảng 20 % (4556 / 3765 / 3857 xe trong 1800 s); cả bốn arm của D1 chạm trần hàng đợi 80 m ở 600–900 s.
- **GEH:** tỉ lệ GEH < 5 ở mức lớp-xe: D1 0,919 / 0,952 / 1,000, D2 và D3 từ 0,984 đến 1,000; ở mức approach x movement: 0,844–1,000 (0,844 là D1 seed 1, run có backlog). Mọi run vượt `min_share` 0,85 ở mức lớp-xe. Cảnh báo: số quan sát proxy cùng sinh từ generator nên chỉ cho thấy nút phục vụ đủ nhu cầu.
- **Phase 3 re-check (R21), `target`, 5 seed x 900 s:** halting tối đa trong box 13, 8, 8, 7, 10 (trước đó cố định 8); 3 cột ngang (trước 2); span ngang 2,5–2,6 m; va chạm 0–1/run (trước 10–24). Target M7a: trung bình 6,0, p90 10, p95 11; trung bình thực 4,9–6,9, max 13 vượt p95. Box không còn là cận sức chứa dưới target. Operator sửa 1 chỗ ở `experiments/phase3/box_capacity.py` (`ssm_violator_conflicts` trả bảng rỗng khi không có `ssm.xml`).

**Tiêu chí:** đạt — net 3,5 m, test, SSM mặc định tắt, log gộp đếm đúng, R17 đạt, ngưỡng đã đóng băng. Chưa đạt: B0 eligible (7/9 run có teleport jam/yield; kết quả này được R23 chấp nhận).

**Giả định:** bề rộng làn thoát bằng làn vào (TCVN 13592:2022 Bảng 10); mọi số ở đây đo khi check-junctions TẮT (R28 ban hành sau); số B0 cũ ở Task 4 và Phase 3 (3,2 m) bị thay thế.

**TODO_MEASURE còn lại:** thêm `exits[].lane_widths_m` trong `site.yaml`; còn lại như trước.

**Vướng mắc / việc cho task sau:** (1) R28: tính lại hai ngưỡng với check-junctions BẬT (operator đang làm); (2) wall time có thể tăng khi mạng bão hòa; (3) mode `violators` raise khi routes không có xe vi phạm (cố ý); (4) lượng tử hóa 2/h của p90 trên 1800 s.

**Review:** sạch sau 1 fix round. Minor hoãn lại (2): giá trị cảnh báo có dấu cách bị đếm đôi (tối đa 20 dòng, đã ghi nhận); manifest `sumo_options` `ssm.explicit` chỉ là ghi chú, không có danh sách id.

### 2026-10-25 — Task 7: Param bounds, rule schema, validator, B1 (PLAN 4.1–4.3)

Commits `b9b77cb`, `586349a` (`e0c1faf..586349a`) · Review: Approved sau 1 fix round (I1 schema không an toàn với Ollama, chuyển sang R18/Task 12; I2 thu hẹp `RULE_VCLASSES`, sửa ngay theo R19; thêm provenance/rationale chặt, `jmTimegapMinor` chỉ custom1) · Trạng thái implementer: DONE_WITH_CONCERNS · ✅

**Đã làm:**
- `rules/bounds/param_bounds.yaml` (24 dòng): mỗi dòng có model, unit, `behavior_group`, metric ràng buộc, min/max/default, `by_vclass` tùy chọn, `source_url` (trang sumo.dlr.de/docs) và `range_source`/`range_evidence`. Cố định (min = max = default, vì không metric nào ràng buộc): `lcAccelLat`, `jmDriveAfterYellowTime`. Loại theo R15: `jmIgnoreFoeProb`, `jmIgnoreFoeSpeed` (validator báo `unknown_attr` kèm lý do).
- `rules/schema/rule_spec.schema.json` (draft 2020-12, `additionalProperties: false`, `source: llm` bắt buộc provenance và rationale không rỗng), `src/thesis_sumo/rules/schema.py` (`TRACI_RULE_PARAMS`, `RULE_VCLASSES`), `src/thesis_sumo/rules/validator.py` (`validate`, mã lỗi `schema`/`unknown_attr`/`out_of_bounds`/`share_sum`/`rule_params`/`logic`, `ValidityLog`, CLI), `rules/specs/B1_manual.json`, `experiments/r15_timegap/early_leave_check.py`.
- Kiểm tên SUMO: cả 26 ứng viên trong PLAN 4.2 tồn tại ở 1.27.0, nạp được với XSD validation; XSD thu hẹp hai khoảng: `lcImpatience` [0, 1] (docs ghi -1..1), `jmDriveAfterRedTime` [0, 10] (mặc định -1 tương ứng bỏ thuộc tính). Không có tên nào phải bỏ.
- Thí nghiệm `lcPushy` so với `lcPushyGap`: đặt cả hai thì `lcPushyGap` bị bỏ qua âm thầm, nên thành `logic` issue.
- B1 là chuyển từ Saval et al. 2023 (PLOS ONE 18(3): e0281658, Bảng 11 Hà Nội, Sec 4), evidence `literature_transferred`: ô tô accel 1,2 / decel 4,8 / tau 2,5 / minGap 1,1; xe máy accel 1,1 / decel 4,6 / tau 0,8 / minGap 1,9 / minGapLat 0,3 (0,1 của paper bị kẹp theo cận R15); `swarm_red_running` p0 = p_max = 0,5, k = 0.

**Lệnh tái tạo:**
- `.venv/Scripts/python -m pytest tests/test_validator.py -q` (50 passed); `.venv/Scripts/python -m pytest -q` (155 passed, 1 xfailed, 1 failed: test eligibility do giá trị của operator, sửa ở 4b)
- `.venv/Scripts/python experiments/r15_timegap/early_leave_check.py --day PROXY_D1 --seeds 1 --end 1200 --values 0.5 --nproc 2`

**Kiểm tra R15 (B0 so với `jmTimegapMinor` 0,5 trên `moto_violator`, PROXY_D1, 1 seed, 1200 s, net 3,2 m, SSM bật):**

| Biến thể | Xe vào box | Thoát sớm | Chờ TB tại cuối xanh đối diện | Tỉ lệ thoát sớm | Teleport (tổng / không do va chạm) | Wall |
|---|---|---|---|---|---|---|
| B0 (1 s) | 51 | 7 | 4,1 | 0,146 | 19 / 1 | 1753 s |
| `jmTimegapMinor` 0,5 | 48 | 16 | 2,6 | 0,381 | 21 / 2 | 2315 s |

Đòn bẩy đúng chiều, target 0,2 nằm giữa hai giá trị, nên cận [0,5; 3] bao quanh target và không cần rule gap-acceptance dự phòng của R15. Chỉ 1 seed, 1200 s, không run nào `valid_strict`.

**Tiêu chí:** đạt — validator trả toàn bộ lỗi trong một danh sách, mọi hàng bounds có nguồn, mọi hàng nạp được trong SUMO ở min và max. Chưa đạt: không có.

**Giả định:** khoảng của các thuộc tính còn lại là assumed (mỗi dòng có `range_source`); `jmTimegapMinor` [0,5; 3] s là giả định; `behavior_group` là danh sách vì một số thuộc tính phục vụ hai hành vi; validator chỉ chạy với site proxy (site đo thực thiếu bề rộng làn sẽ raise `MissingFieldDataError` khi spec đặt `minGapLat`); B1 áp rule cho cả custom1 (hiểu R19 là "thêm passenger", giữ custom1).

**TODO_MEASURE / TODO_DECIDE còn lại:** không có mục mới.

**Vướng mắc / việc cho task sau:** (1) B1 không có đòn bẩy M8 (wrong_lane_dodge, slow_lane_center không có trong B1) và không có rule ô tô; (2) B1 vượt M3 theo thiết kế (p = 0,5 so với target 6,5–11 %); (3) tham số IDM của Saval chạy trong Krauss, tau ô tô 2,5 s có thể hạ lưu lượng bão hòa (theo dõi cổng G0); (4) SSM tràn log làm chậm run (xử lý ở 4b); (5) Optuna: R20; schema cho LLM: R18.

**Review:** Approved sau 1 fix round. Minor hoãn lại (3): `validate()` nạp lại bounds/schema mỗi lần gọi (chi phí cho Optuna); B1 swarm p0 = p_max = 0,5 vượt M3 (theo dõi ở T9); thứ tự `behavior_group` của `jmTimegapMinor` đổi.

### 2026-10-25 — Task 8: Compiler (PLAN 4.4)

Commit `ad1f8bb` (`90b302c..ad1f8bb`) · Review: Approved, sạch (5 minor hoãn lại) · Trạng thái implementer: DONE_WITH_CONCERNS · ✅

**Đã làm:**
- `src/thesis_sumo/rules/compiler.py`: `compile_spec(spec, out_dir=None, *, site=None)` gọi validator trước, raise `InvalidSpecError` (có `.issues`) và không ghi gì khi spec sai. Sinh `vtypes.add.xml` (3 `vTypeDistribution` theo thứ tự `car`, `moto`, `moto_violator`; mỗi archetype là một vType với id bằng archetype id, `laneChangeModel="SL2015"`, `probability` bằng share) và `traci_rules.json` (chỉ khi spec có rule; xóa file cũ nếu có).
- custom1 nhận trước 13 thuộc tính mặc định xe máy (`CUSTOM1_MOTORCYCLE_DEFAULTS`, giống file B0 viết tay) rồi spec ghi đè.
- Tham số bằng giá trị mặc định vẫn ghi tường minh (vì một số mặc định phụ thuộc thuộc tính khác: lcPushyGap = minGapLat, lcMaxSpeedLatStanding = maxSpeedLat, jmDriveRedSpeed = maxSpeed).
- File sinh ra khai báo `xsi:noNamespaceSchemaLocation`, nên SUMO (mặc định `--xml-validation local`) kiểm XSD mỗi lần nạp; file không khai báo thì thuộc tính lạ bị bỏ qua âm thầm (đã thử).
- `rules/specs/B0.json` biên dịch ra vType tương đương từng thuộc tính với `rules/compiled/B0/vtypes.add.xml` viết tay; file viết tay được giữ và `compile_spec` từ chối ghi đè (`HAND_WRITTEN`). Thêm `tests/snapshots/B1_vtypes.add.xml` (đã đọc trước khi đóng băng) và `.gitattributes` `tests/snapshots/** -text` (máy có `core.autocrlf=true`).
- Thí nghiệm `getTypeID` (libsumo, 120 s): xe lấy từ distribution báo id vType thành viên, không phải id distribution (moto_a 185 / moto_b 66 so với xác suất 0,7/0,3); thành test vĩnh viễn. Task 9 khớp xe qua `vtype_ids` trong `traci_rules.json`.

**Lệnh tái tạo:**
- `.venv/Scripts/python -m thesis_sumo.rules.compiler rules/specs/B1_manual.json --site config/site.proxy.yaml` (không có `--site` thì exit 2 trên site đo thực vì thiếu bề rộng làn; cố ý)
- `.venv/Scripts/python -m pytest tests/test_compiler.py -q` (29 passed); `.venv/Scripts/python -m pytest -q` (201 passed, 1 xfailed)

**Tiêu chí:** đạt — snapshot B1 byte-equal, mọi thuộc tính ghi ra nằm trong bounds, SUMO nạp được với XSD validation, B0.json tương đương file viết tay. Chưa đạt: không có.

**Giả định:** vType id bằng archetype id; không ghi `traci_rules.json` cho spec không có rule (runner raise khi file tồn tại), nên `CompiledSpec.traci_rules` là `Path | None`; `rules/compiled/B1_manual/` là build artifact, chưa commit.

**TODO_MEASURE còn lại:** không có mục mới.

**Vướng mắc / việc cho task sau:** validator chưa từ chối archetype id bắt đầu bằng `DEFAULT_` (SUMO âm thầm định nghĩa lại vType mặc định), cần thêm ở Task 12 để tính vào tỉ lệ hợp lệ.

**Review:** Approved, sạch. Minor hoãn lại (5): validator nên từ chối id `DEFAULT_*` (làm ở dispatch Task 12); CLI in traceback thô khi JSON thiếu/sai; chú thích guard `HAND_WRITTEN`; `test_only_allowed_attributes` chỉ chạy trên B1; kiểm XSD phụ thuộc `SUMO_HOME`.

### 2026-10-25/26 — Task 9: TraCI runtime controller và 5 rule (PLAN 4.5)

Commits `ac325b4`, `4023408` (`ad1f8bb..4023408`) · Review: lần 1 "Needs fixes" (Critical: `ignoreIDs`, thành R25; I1 cửa sổ can thiệp đóng ở vạch dừng, thành R30; I2 dự án không bật check-junctions, thành R28; I3 test không thấy va chạm junction và có `--no-warnings`), fix round 1 xử lý hết (R25–R31, R34), re-review sạch · Trạng thái implementer: DONE_WITH_CONCERNS · ✅ (operator đang tính lại hai ngưỡng R28)

**Giải thích cho Viktor — lỗi an toàn mà review phát hiện (`ignoreIDs`):**
- Bối cảnh: rule `illegal_left_box` giữ xe máy rẽ trái trái luật đứng yên trong giữa nút ("box") thêm một lúc rồi mới cho đi. Điểm chờ nằm sát đường đi của dòng xe cắt ngang (HĐT), nên SUMO bắt dòng cắt ngang phải nhường xe đang bị giữ, làm dòng đó bị kẹt trong pha xanh.
- Cách chữa đầu tiên của coder: đặt tham số `junctionModel.ignoreIDs` trên các xe cắt ngang, tức là bảo họ "coi như không thấy" những xe đang bị giữ. Run thử 600 s không còn kẹt và không có va chạm, nên coder nghĩ là ổn.
- Vì sao sai: cả dự án lúc đó TẮT `collision.check-junctions`, nên SUMO không đếm va chạm giữa các xe đi trên các làn nội bộ cắt nhau. "0 va chạm" chỉ vì thước đo không nhìn thấy. Khi reviewer bật check-junctions, xe cắt ngang lao xuyên qua xe đang bị giữ: 55 va chạm trong nút so với 7 khi không dùng `ignoreIDs`. Tức là luật nhìn có vẻ an toàn thực ra cho xe chạy xuyên nhau. Nếu để nguyên, LLM sẽ học cách khai thác lỗ hổng này và kết quả luận văn sai.
- Cách sửa (fix round 1):
  - **R25:** bỏ hẳn `ignoreIDs` (có test grep cấm xuất hiện trong `src/`) và bỏ rule `yield_cross_green` cùng tham số `max_clear_into_cross_green_s`. Rule chỉ còn `release_lag_s` [0, 4] s: giữ xe đứng yên bằng `setSpeed(0)` thuần rồi thả. Hệ quả chấp nhận: nếu giữ kéo vào pha xanh của dòng cắt ngang thì dòng đó phải đợi (đúng với thực tế xe chắn trong nút); LLM chỉ kéo dài được thời gian dọn box.
  - **R28:** BẬT `--collision.check-junctions` trong mọi run; manifest tách `n_collisions_lane` và `n_collisions_junction`; hai ngưỡng (lane và junction) phải tính lại từ B0 với check bật. Trong lúc chờ, `max_collisions_per_hour` và `max_junction_collisions_per_hour` để `null` và `is_eligible` raise cho đến khi có giá trị, nên không run nào bị chấm bằng ngưỡng cũ.
  - **R29:** test trên net chữ thập nhỏ (check-junctions bật, dòng cắt ngang mỗi 2 s): giữ thuần lag 3 cho 0 va chạm junction, lag 0 cho 0, còn đối chứng âm (cố tình dùng `ignoreIDs` trong test) cho 1–2 va chạm. Test thấy được lỗi cũ nên nó không thể quay lại âm thầm.
  - **R30:** xe bị TraCI can thiệp được tính là "đang bị can thiệp" cho tới khi qua nút (tới làn không-internal đầu tiên sau vạch dừng), không phải chỉ tới vạch dừng; va chạm được gán cho can thiệp nếu một trong hai bên đang trong cửa sổ. Trước đó nhiều va chạm trong nút của xe vượt đèn đỏ bị tính là "không liên quan can thiệp".

**Đã làm:**
- `runtime/state.py` (`JunctionInfo`, `StepReader`: một subscription ngữ cảnh junction bán kính `sim.fcd_radius_m` + một subscription TLS), `runtime/controller.py` (`Controller`, `make_controller`, RNG riêng mỗi rule, seed `"<seed>:<i>:<rule_type>"`), `runtime/rules/` (5 rule: `early_start`, `swarm_red_running`, `wrong_lane_dodge`, `illegal_left_box`, `slow_lane_center`; mỗi xe chỉ một can thiệp tại một thời điểm), `runner` tự tạo controller khi có `traci_rules.json`; manifest thêm `interventions`, `interventions_log`, `controller_wall_s`; `interventions.csv` (`t, veh_id, rule, action, executed, reason, t_end`).
- Fix round 1 ngoài R25/R28–R30: **R26** B1_manual bỏ rule box (vType không đổi, snapshot không đổi); **R27** `runtime/wrong_lane.py` dùng chung cho runtime và validator, validator báo `logic` khi `wrong_lane_dodge` không có connection dùng được (trên net proxy cả car và moto đều bị từ chối); **R31** `sim.calib_end_s: 1800` là mặc định của `runner.run`; **R34** chú thích `minGap` chỉ trích Saval Bảng 11 (1,9 m); sửa đếm vạch dừng (teleport không còn bị đếm là vượt vạch).
- SUMO đã kiểm bằng thí nghiệm: để vượt đèn đỏ chỉ cần xóa bit4 của speedMode (mode 15; bit3 và các bit an toàn giữ nguyên); `vehicle.getNextLinks` rỗng trên làn nội bộ nên thời điểm thả native suy từ tốc độ xe chờ đầu; setter kiểu `setLateralAlignment` tạo bản sao vType `typeid@vehid` nên không dùng (slow_lane_center dùng `changeSublane`); subscription bán kính 120 m chỉ tốn thêm ~1,4 s Python mỗi 600 s.

**Lệnh tái tạo:**
- `.venv/Scripts/python -m thesis_sumo.rules.compiler rules/specs/B1_manual.json --site config/site.proxy.yaml` (cần trước khi chạy `--spec B1_manual`)
- `.venv/Scripts/python -m thesis_sumo.sim.runner --spec B1_manual --day PROXY_D1 --seeds 1 --site config/site.proxy.yaml --end 600`
- `.venv/Scripts/python -m pytest -q` (221 passed, 1 xfailed)

**Kết quả B1 trên PROXY_D1, 600 s, seed 1, check-junctions BẬT (sau fix, máy có tải song song):**

| Run | Wall | Controller `on_step` | Va chạm lane / junction | Teleport (tổng / không do va chạm) |
|---|---|---|---|---|
| B1 chỉ vType | 211 / 138 s | – | 0 / 7 | 11 / 4 |
| B1 vType + controller, rule không bao giờ kích hoạt | 199 s | 6,6 s | 0 / 7 | 11 / 4 |
| B1_manual (swarm + early_start) | 63 / 87 s | 3,0 / 4,0 s | 0 / 13 (1 liên quan can thiệp) | 13 / 0 |

- Chi phí controller 3–7 s mỗi 600 s; quỹ đạo giống hệt khi rule tắt (628 bản ghi tripinfo, `diff` rỗng). Với check bật, vType B1 tự gridlock (chỉ 628 chuyến xong trong 600 s so với 1050 khi check tắt); B1_manual nhanh hơn vì có swarm rule, nên chênh thời gian là hành vi, không phải chi phí controller. Overhead controller 1,11x trong báo cáo đầu (mục tiêu 1,5x).
- Swarm: 80 quyết định, 53 thực thi, 27 `red_ended_before_crossing`; early_start p = 0 nên 0 can thiệp (69 lần bốc thăm). Trước fix (check tắt): 0 va chạm, 0 teleport, 44/84 swarm thực thi.

**Tiêu chí:** đạt — 5 rule chạy, libsumo và traci cho `interventions.csv` giống nhau, overhead controller trong mục tiêu. Chưa đạt/phụ thuộc: ngưỡng va chạm lane và junction chờ operator (R28); kiểm cặp seed hold so với lag 0 trên proxy (R29, operator) chưa có.

**Giả định:** hằng số mô hình trong module (FRONT_ROW_M 2,5 m, HALT 5 km/h, JAM_GAP 10 m, RELEASE_SPEED 0,1 m/s, LANE_CHANGE_TIMEOUT 5 s; slow_lane_center dung sai 0,2 m, ổn định 3 s, cooldown 2 s); trạng thái nhóm lấy từ các link đi thẳng của approach; `wrong_lane_dodge` coi "sai làn" theo `lane_movements` của site, nên trên net proxy chỉ ghi `no_connection` (S_cheat không có đòn bẩy trên net này); log trễ 0,1 s so với SUMO.

**TODO_MEASURE / TODO_DECIDE còn lại:** hai ngưỡng va chạm mới `null` (tính lại theo R28; chưa gắn nhãn `TODO_DECIDE` trong file).

**Vướng mắc / việc cho task sau:** (1) `is_eligible` raise cho tới khi operator đóng băng hai ngưỡng với check-junctions bật; (2) check bật làm B1 vType có 7 va chạm junction và 4 teleport jam/yield trong 600 s, cần so với B0 cùng điều kiện; (3) `rules/compiled/B1_manual/` chưa commit (build artifact); (4) B1 không có rule box nên M7 chỉ do native.

**Review:** sạch sau 1 fix round. Minor hoãn lại: validator và runtime lấy quyền xe từ hai nguồn khác nhau (connection `allow` so với via-lane allowed); `usable_dodges` KeyError với mã hướng lạ; cửa sổ R30 cho can thiệp không thực thi có thể gán thừa; `n_collisions_junction` gồm cả va chạm đuôi trên làn nội bộ; các null mới thiếu nhãn `TODO_DECIDE`; `phase3_box_capacity.md` còn ghi `release_lag [0,6]`; `DIR_TO_MOVEMENT` t→t so với t→u; `test_backends`/`test_compiler` còn `--no-warnings`; cùng các minor của review đầu (cannot_stop một làn, executed khác causal với box hold, cache không dọn, độ phủ parity, cột log dư).

### Ghi chú tiến độ — tạm dừng lần 3

Phiên làm việc dừng lần thứ ba vì chạm usage limit, sau đó đã resume và chạy tiếp.

### 2026-10-26 — Chuyển sang Linux

Repo gộp thành một git ở `Thesis/` (`SUMO/.git` đã xóa, hash commit cũ không tra được). Máy Linux: `SUMO/scripts/setup_env.py` (eclipse-sumo 1.27.0 trong `.venv`, `sumo_tools.pth` đặt `SUMO_HOME`), git-lfs cài vào `~/.local/bin`. Ledger cũ ở Windows (bị gitignore); ledger mới `SUMO/.superpowers/sdd/2026-10-26-linux-continuation/progress.md` (nay được track). Chưa có Ollama: vòng LLM tạm dùng agent Claude Sonnet, spec ghi `provenance.model` "claude-sonnet (stand-in)", không phải kết quả của LLM local. Commit `0380530`.

**Lệch giữa `PLAN.md` mới và ledger/spec cũ (theo PLAN):** thêm lớp `custom2` (ô tô vi phạm); hành vi F2 (làn rẽ phải liên tục, vỉa hè, ngược chiều) với M9–M11 và các bảng `queue_timeseries`, `space_seeking_events`, `right_turn_delay`; gộp luật thành `queue_space_seeking` (thay `wrong_lane_dodge`); Phase 3 tách 3A–3D; baseline B0/B1/B2/P1/P2/H với E1/E2 (thay B0/B1/B2/P); thêm `policy/evaluate.py`. `CLAUDE.md` vẫn ghi "wrong-way driving" ngoài phạm vi, trái với PLAN (8. đi ngược chiều, tùy Phase 3).

### 2026-10-26 — Task 10: Metrics M1–M8, G0 và distance (PLAN Phase 5)

Review: lần 1 "changes requested" (Critical: `cycle_of` dùng mốc xanh đã cắt theo cửa sổ nên mọi xe rẽ trái trái luật sau mốc cuối bị gán vào chu kỳ đó, release time M7a tới 1807 s trên PROXY_D2, IQR quan sát ~1050 s, M7a gần như mù; Important: tối ưu có thể giảm điểm bằng cách không sinh sự kiện), fix round 1 xử lý cả hai, re-review approved với điều kiện ghi R35/R36 · ✅

**Đã làm:** `metrics/distance.py` (W1/IQR với dự phòng sd → |mean| → 1; sai số tương đối; `D_EMPTY` 2,0; `pair_stats`, `ratio` với `R_FLOOR` 0,05; `split_weights` phân cấp; `compare` → `DistanceReport` có `S`, `S_sourced`, `S_assumed`, `to_row`, `summary_lines` không chứa tên ngày; `compute_all`). `common.cycle_of` dùng mọi mốc xanh. `experiment.yaml`: `observation.metric_window_s`, `score.weights` (R36). Test mới `test_m7_day_past_window_same_as_truncated`, `test_empty_never_beats_wrong`.

**Lệnh tái tạo:** `cd SUMO && .venv/bin/python -m pytest -q tests/test_metrics.py` (23 passed); toàn bộ `.venv/bin/python -m pytest -q` (244 passed, 1 xfailed).

**Tiêu chí:** đạt — mọi metric chạy trên bảng dựng tay có đáp án và trên ngày proxy, khoảng cách luôn hữu hạn. Chưa làm: chạy metric trên output B0 (sau khi R28 Linux xong).

**Vướng mắc:** R35 phần tỉ lệ nhỏ (xem rulings) chờ Viktor.

### 2026-10-26 — R28: B0 với check-junctions BẬT, chạy lại trên Linux (9/9 run)

Lệnh: `.venv/bin/python -m thesis_sumo.sim.runner --spec B0 --day PROXY_Dk --seeds 1 2 3 --site config/site.proxy.yaml --nproc 3 --ssm off` (k = 1, 2, 3 song song; 1800 s; log `experiments/operator/task9/linux_run_PROXY_D*.txt`; manifest và collisions.xml được track).

| Ngày / seed | Va chạm lane | Va chạm junction | Teleport (tổng / không do va chạm) | Backlog cuối | Wall (s) |
|---|---|---|---|---|---|
| D1 / 1 | 2 | 45 | 47 / 0 | 0 | 192 |
| D1 / 2 | 3 | 66 | 69 / 0 | 0 | 179 |
| D1 / 3 | 2 | 44 | 50 / 4 | 0 | 243 |
| D2 / 1 | 0 | 47 | 47 / 0 | 0 | 111 |
| D2 / 2 | 0 | 44 | 44 / 0 | 0 | 113 |
| D2 / 3 | 1 | 57 | 62 / 4 | 0 | 156 |
| D3 / 1 | 2 | 35 | 57 / 20 | 0 | 380 |
| D3 / 2 | 0 | 57 | 57 / 0 | 0 | 112 |
| D3 / 3 | 1 | 42 | 43 / 0 | 0 | 107 |

- **Tái lập Windows → Linux:** 8 run đã có trên Windows (report 2026-10-26) cho đúng từng số va chạm lane/junction và teleport trên Linux (cùng SUMO 1.27.0). D3 seed 1 (bị kill trên Windows) nay có số.
- Quy về /h: lane 4, 6, 4, 0, 0, 2, 4, 0, 2 (p90 4,4); junction 90, 132, 88, 94, 88, 114, 70, 114, 84 (p90 117,6). Công thức R24 cho `max_collisions_per_hour` = 5 và `max_junction_collisions_per_hour` = 118. Ngưỡng junction 118/h gần như không lọc gì (như đã dự báo). Không run nào `valid_strict`; D1/3, D2/3, D3/1 có teleport không do va chạm.
- **KHÔNG đóng băng:** task F2-net đổi mạng (lane 0 thành làn rẽ phải liên tục, connection đi thẳng cho custom1/custom2), nên ngưỡng phải tính lại trên mạng F2 trước vòng 1 (R24 yêu cầu đóng băng trên mạng dùng cho vòng lặp). Hai ngưỡng trong `experiment.yaml` vẫn `null`.
- **Metrics B0 vs PROXY_D1–D3 (checkpoint cuối Phase 5, 9 run):** G0 đạt ở cả 9 run (tỉ lệ ô GEH < 5: 1,0; D3/1 0,90). S = 1,17 (có nguồn 0,52, giả định 0,66). Lệch lớn nhất: M5 hàng chờ 53,9 m so với 11,5 m (sim>obs); M1 headway xe máy 0,47 s so với 0,31 s; M4 độ sâu vượt vạch 21,8 m so với 2,0 m (nghi xe chờ trong box bị tính, cần kiểm tra); M3 không có xe vượt đỏ (B0 không có luật); M8 = 0 (B0 không đổi làn sai).

### 2026-10-26 — Task F2-net: làn rẽ phải liên tục, custom2, khóa site F2 (PLAN 0, 1.4, 2.1)

Implementer + 1 vòng sửa (rẽ phải khi đỏ bị M2/M3 tính là vi phạm, trái PLAN 0) · Review lần 1 "changes requested" (năng lực giảm 1/3 → Viktor quyết R37; generator dàn hàng chờ trên cả 3 làn → sửa `queue_width`) · Viktor chọn cọc phân cách → lane 0 đi thẳng `disallow="all"`.

**Đã làm:**
- Site: `continuous_right_lane` (true, 4 nhánh), `right_lane_separator` (bollards), `sidewalk_width_m`, `hard_median_length_m` (`null # TODO_MEASURE`), `violator_classes {moto: custom1, car: custom2}`, `f2_measured_approaches` (null); proxy `lane_movements` lane 0 = `[r]`; nhãn evidence mới `field_observation` chỉ cho hai khóa Viktor xác nhận.
- Mạng: link rẽ phải liên tục `g` ở mọi pha; lane 0 đi thẳng giữ nhưng không ai đi được (bollards; `paint`/`none` thì chỉ custom1 custom2); chỉ số link không đổi; `continuous_right_lane: false` cho lại đúng patch cũ. Làn vỉa hè: chỉ kiểm tra khóa rồi `NotImplementedError` (thêm làn mép dời mọi chỉ số làn; PLAN chưa nói điểm bắt đầu/nhập) — Phase 3B thử trong kịch bản riêng.
- B0/compiler: phân phối `car_violator` (custom2, mặc định passenger chép tường minh, kiểm bằng libsumo), không bắt buộc trong spec; outputs ánh xạ custom2 → car. Demand chưa có xe custom2.
- Metrics/generator: rẽ phải liên tục không phải vượt đỏ/xuất phát sớm (`common.uncontrolled_tracks`); generator cho chúng đi không dừng; hàng chờ dàn trên làn có đèn. PROXY_D1–D5 và routes sinh lại. `docs/research/proxy_targets.md` §2/§3 cập nhật; cờ: [S5] tính tỉ lệ HDT trên "all flows" (có cả rẽ phải) nên trên mẫu số mới số vi phạm mỗi chu kỳ ở HDT thấp hơn trước — chờ Viktor.
- 2 xfail strict mới (tỉ lệ 5 ngày lệch > 15 % do ngẫu nhiên): LVL_W xe máy vượt đỏ +17,6 % (reviewer: 200 campaign trung bình +0,1 %, SD 4,5 %; bộ D1–D5 hiện tại là lần rút hiếm ~3,8 SD), ô tô xuất phát sớm −19 %; xfail cũ ô tô vượt đỏ nay −45 %.

**Lệnh tái tạo:** `.venv/bin/python -m thesis_sumo.net.build --site config/site.proxy.yaml`; `.venv/bin/python -m thesis_sumo.proxy.generate`; `.venv/bin/python -m pytest -q` (272 passed, 3 xfailed).

**Phát hiện (B0, PROXY_D1, seed 1, check-junctions bật, mạng lane 0 rẽ phải, trước khi đặt cọc):** 600 s: va chạm lane/junction 1/17, teleport 18/0, backlog 0. 1800 s: 4/63, teleport 75 (8 không do va chạm), backlog cuối 23 (reviewer: 286 ở lần chạy khác, đỉnh 445), hàng chờ chạm 80 m ở 66 % chu kỳ (mạng cũ 26 %), kẹt chủ yếu ở LVL_W làn 1–2. B0 trên mạng này không ELIGIBLE (backlog). Ngưỡng R28 phải tính lại trên mạng này.

### Bước tiếp theo

- Operator đang tính lại hai ngưỡng va chạm (lane và junction) với `check-junctions` BẬT (R28): B0 trên PROXY_D1–D3 x 3 seed rồi đóng băng và commit trước vòng 1 (R24); kèm kiểm cặp seed hold so với lag 0 (R29) và một run chẩn đoán B0 D1 với time-to-teleport `-1` (R33).
- Task 10 (metrics M1–M8, G0, distance) 🔄, dispatch từ `4023408`.
- Sau đó Task 11–15: harness (11), LLM client/prompts/feedback (12; thêm schema LLM theo R18 và từ chối id `DEFAULT_*`), vòng LLM 3 lần (13), Optuna B2 (14, `search_space()` theo R20), benchmark và report (15).
