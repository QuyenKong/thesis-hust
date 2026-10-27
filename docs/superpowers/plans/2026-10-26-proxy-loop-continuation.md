# Proxy-benchmark-loop: phần còn lại + 3 hành vi mới — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

> **Trạng thái: BẢN NHÁP, viết khi chưa có repo `SUMO/` trên máy Linux.** Mọi tên module, hàm và đường dẫn bên dưới lấy từ luận văn (`Latex/Chuong/3–5`) và `report/2026-10-26/README.md`, chưa đối chiếu với code. Task 0 bắt buộc chạy trước: đối chiếu plan với code và ledger, sửa chỗ lệch. Nếu ledger `.superpowers/sdd/2026-10-25-proxy-benchmark-loop/progress.md` mô tả Task 10–15 khác plan này, **ledger thắng** cho Task 10–15; plan này chỉ là nguồn chính cho phần mới (Task N1–N4).

**Goal:** Hoàn tất Task 10–15 của vòng proxy-benchmark, đồng thời thêm ba hành vi: rẽ phải liên tục, xe đi thẳng chặn làn rẽ phải khi hàng chờ dài, và xe máy đi ngược chiều để kịp đèn xanh.

**Architecture:** Giữ nguyên pipeline hiện có: spec JSON → validator → compiler → runner + TraCI controller → observed schema → metrics. Rẽ phải liên tục là patch tĩnh của mạng/đèn, sinh từ `site.proxy.yaml`. Hai hành vi còn lại đi theo đúng khuôn của hành vi rẽ trái trái luật: có spike khả thi với tiêu chí đặt trước, sau đó chỉ thêm luật TraCI hoặc chỉnh sửa mạng tĩnh nếu spike đạt.

**Tech Stack:** Python ≥3.10 (venv 3.12), SUMO 1.27.0 (libsumo/traci), pytest, numpy/pandas/scipy, jsonschema, openai ≥1.30 (Ollama `qwen3.5:9b`), optuna ≥3.5.

**Spec:** `SUMO/PLAN.md`, `SUMO/docs/superpowers/specs/2026-10-25-proxy-benchmark-loop-design.md`, ledger ở trên, `SUMO/docs/PROGRESS.md`. Ba hành vi mới chưa có spec; quyết định phạm vi nằm trong mục "Quyết định cần chốt" bên dưới.

## Global Constraints

- SUMO 1.27.0; mọi thuộc tính vType và option `sumo`/`netconvert` phải kiểm tra bằng `--help` hoặc tài liệu chính thức trước khi dùng (CLAUDE.md của repo SUMO).
- Không sửa tay `.net.xml`; mọi thay đổi mạng đi qua patch plain XML sinh từ cấu hình site.
- Giá trị đo thực chưa có thì để `null` + `TODO_MEASURE`; mọi giá trị proxy mới mang nhãn `literature` / `literature_transferred` / `assumed` kèm nguồn.
- Luật TraCI chỉ được GIỮ hoặc xoá đúng bit speed mode có tên. Cấm `ignoreIDs`, cấm `jmIgnoreFoe*`, cấm đổi vType qua TraCI.
- `collision.check-junctions` luôn BẬT; seed dev là 1–3; chạy 0–1800 s; warm-up metrics 300 s.
- Mỗi xe tại một thời điểm chỉ chịu tối đa một can thiệp; mọi can thiệp ghi vào `interventions.csv`.
- LLM và Optuna không được thấy PROXY_D4–D5.
- Thuộc tính hoặc tham số luật không có chỉ số nào ràng buộc thì phải cố định, không đưa vào không gian tìm kiếm.
- Trước mỗi lần chạy runner: `pgrep -af "sumo|runner"` phải rỗng (ngoài các tiến trình đã biết là của phiên khác).

## Quyết định cần chốt (người dùng) — chặn Task N1–N4

1. **Rẽ phải liên tục ở nhánh nào?** Đề xuất: cả 4 nhánh, nhãn `assumed`, vì chưa có số đo. Lane 0 chuyển thành làn chỉ rẽ phải hay vẫn dùng chung thẳng + phải? Đề xuất: **chỉ rẽ phải**, vì nếu dùng chung thì hành vi "chặn làn rẽ phải" xảy ra tự nhiên, không cần luật.
2. **Đi ngược chiều có đưa vào phạm vi luận văn không?** Hiện Ch.1 và Ch.3 ghi rõ là ngoài phạm vi. Nếu đưa vào, phải sửa Ch.1 §1.2, Ch.3 §3.2 và câu "một chỉnh sửa mạng tĩnh duy nhất".
3. **Target proxy cho hai chỉ số mới (M9, M10)** sẽ là `assumed`, vì mình chưa tìm thấy số liệu công bố. Chấp nhận như vậy, hay tìm tài liệu trước?

## Thứ tự và lý do

```
T0 đối chiếu → T10 metrics (độc lập mạng) → N1 rẽ phải liên tục (đổi mạng)
→ N2 spike chặn làn → N3 spike ngược chiều → N4 rule/net + M9/M10
→ T-R28 chẩn đoán va chạm + chốt ngưỡng trên MẠNG CUỐI → T11 → T12 → T13 → T14 → T15
```

Mọi thay đổi mạng hoặc demand đều làm mất hiệu lực các run B0 và ngưỡng R28. Vì vậy N1–N4 phải xong **trước** khi chốt R28; nếu làm ngược thì phải chạy lại R28 hai lần. Task 10 không phụ thuộc mạng nên làm trước.

## Review Focus

1. **Xe đi thẳng bị kẹt vĩnh viễn trên làn chỉ rẽ phải** (không có kết nối tới cạnh tiếp theo), sinh teleport jam. Mong đợi: luật chặn làn luôn có điểm thoát; test N2 đếm teleport jam = 0.
2. **Xe ngược chiều đâm trực diện dòng ra**: check-junctions không bắt được va chạm trên làn thường. Mong đợi: va chạm làn của xe ngược chiều được đếm riêng trong manifest; test N3/N4 khẳng định số này có trong manifest.
3. **Đổi đèn cho rẽ phải liên tục làm lệch chỉ số link của tlLogic**, khiến pha của hướng khác bị sai. Mong đợi: test N1 so trạng thái mọi link không phải rẽ phải trước và sau patch phải giống nhau.
4. **Cổng G0 với ô có m = c = 0** (chia cho 0). Mong đợi: ô đó tính là đạt, không ra NaN; test trong Task 10.
5. **Vòng LLM bị Ollama trả JSON hỏng hoặc timeout**: không được tiêu ngân sách SUMO, không crash vòng. Test trong Task 12.

---

### Task 0: Đối chiếu plan với code

**Files:** chỉ đọc; sửa chính file plan này.

- [ ] Clone hoặc copy repo SUMO vào `SUMO/`, thêm `.gitmodules` nếu dùng submodule.
- [ ] Đọc ledger (phần cuối), `docs/PROGRESS.md`, `git status`. Liệt kê các thư mục scratch của agent thao tác. Không xoá gì.
- [ ] Ghép tên thật vào plan: module metrics, chữ ký `Rule.on_step`, `RULE_REGISTRY`, mã lỗi validator, hàm patch đèn trong `net`, khoá cấu hình trong `experiment.yaml`.
- [ ] Tạo venv Linux, chạy `pytest -q`. Mong đợi: 221 passed, 1 xfailed (`test_metrics.py` có thể lỗi import `distance`; ghi lại nếu có).
- [ ] Ghi lại: máy Linux có cho kết quả giống từng byte với manifest Windows không? Chạy lại B0/D1/seed1 600 s và so `n_collisions*` với `runs/B0_PROXY_D1_seed01_manifest.json` (cắt theo 600 s). Nếu lệch, mọi run R28 phải chạy trên cùng một máy.

### Task 10: Metrics M1–M8, G0, distance (theo ledger)

**Files:**
- Modify (đang dở, chưa commit): `src/thesis_sumo/metrics/common.py`: review trước, làm tiếp từ phần cổng G0.
- Review: 10 file `metrics/*.py`, `tests/test_metrics.py`.
- Create: `src/thesis_sumo/metrics/distance.py`.

**Interfaces (Produces):**
- `geh_gate(sim: DataFrame, obs: DataFrame, *, threshold=5.0, min_pass=0.85) -> GateResult(pass_rate: float, passed: bool, n_cells: int)`. Ô gồm 15 phút × approach × movement × vclass.
- `distance.metric_distance(sim, obs) -> float`: phân phối → W1 / IQR(obs); vô hướng → |sim−obs|/|obs|.
- `distance.noise_floor(days: list) -> dict[str, float]`: trung bình khoảng cách theo cặp ngày.
- `distance.score(sim_metrics, obs_metrics, floor, weights) -> ScoreResult(per_metric_ratio: dict, total: float)`. Nếu `weights` là `None` thì báo `TODO_DECIDE` error, không tự điền.

- [ ] Test G0: `geh(m=100,c=100)==0`; `geh(m=0,c=0)` ô tính là đạt; tỷ lệ 17/20 ô đạt → `passed is True` (0,85 ≥ 0,85), 16/20 → False.
- [ ] Test distance: W1 của hai mẫu giống nhau = 0; dịch toàn bộ mẫu một đoạn = IQR thì W1/IQR = 1,0; vô hướng sim=110, obs=100 → 0,10; IQR(obs)=0 → lỗi rõ ràng, không inf.
- [ ] Chạy test → FAIL → implement → PASS → `pytest -q` toàn bộ.
- [ ] Đặt cửa sổ tính metrics vào `experiment.yaml` (warm-up 300 s, kết thúc 1800 s).
- [ ] Review (subagent code-reviewer) → commit `feat(metrics): M1-M8, G0 gate, distance`. Cập nhật PROGRESS.md.

### Task N1: Rẽ phải liên tục (patch tĩnh)

**Files:**
- Modify: `config/site.proxy.yaml`: thêm `approaches[].right_turn_continuous: {value: bool, source, evidence: assumed}` và `lane_directions` cho lane 0 = `r`.
- Modify: `config/site.yaml`: cùng khoá, `null` + `TODO_MEASURE`.
- Modify: module patch đèn/kết nối trong `src/thesis_sumo/net/`: (a) kết nối lane 0 chỉ còn rẽ phải; (b) link rẽ phải trong `tlLogic` mang state `g` (xanh phải nhường) ở mọi pha. Phải kiểm tra `netconvert --help` và tài liệu tlLogic xem state cố định `g` hay `s` (rẽ phải khi đỏ, bắt dừng trước) mới đúng ngữ nghĩa. Đề xuất `s` ở pha đỏ và `G`/`g` ở pha xanh, vì Việt Nam yêu cầu nhường đường.
- Test: `tests/test_net.py`.

- [ ] Test: mọi link rẽ phải của 4 nhánh không có state `r` ở bất kỳ pha nào; mọi link khác giữ nguyên state từng ký tự so với mạng trước patch; dựng lại 2 lần giống từng byte (test hiện có).
- [ ] Test: `site.yaml` có `right_turn_continuous: null` thì build báo `MissingFieldDataError`.
- [ ] Implement → PASS.
- [ ] Chỉnh demand: lane 0 hết đi thẳng nên routeSampler phải còn khả thi; chạy `test_demand`. Kiểm tra proxy D1–D5 vẫn sinh được.
- [ ] Chạy khói B0/D1/seed1 600 s: ghi va chạm, teleport và backlog vào PROGRESS (không phải kết quả, chỉ để biết mạng sống).
- [ ] Review → commit `feat(net): continuous right turn (assumed)`.

### Task N2: Spike khả thi "xe đi thẳng chặn làn rẽ phải"

Theo đúng khuôn của Phase 3 box-capacity: câu hỏi, tiêu chí đặt trước, script quan sát không can thiệp.

**Files:** Create `experiments/spike_right_block/run.py`, `docs/research/spike_right_block.md`.

- [ ] Câu hỏi: SUMO có giữ được một xe có route đi thẳng đứng trên làn chỉ rẽ phải tại vạch dừng, sau đó cho nó chuyển về làn thẳng khi đèn xanh, mà không teleport và không va chạm không?
- [ ] Hai cách cần thử, mỗi cách 3 seed × 600 s trên mạng chữ thập nhỏ:
  - (A) TraCI: `changeSublane`/`changeLane` + `setLaneChangeMode` (xoá đúng các bit cần xoá, xác định bằng thí nghiệm như bit speed mode của red-running), sau đó giữ xe.
  - (B) Tĩnh: thêm kết nối đi thẳng từ lane 0 chỉ cho một vClass mới (`custom2`, "moto_blocker"), giống cách làm cho `custom1`.
- [ ] Tiêu chí chọn (đặt trước): teleport jam = 0, va chạm liên quan blocker ≤ 1/run, xe rẽ phải phía sau thực sự bị chặn (độ trễ qua vạch của xe rẽ phải tăng > 0 s so với khi không có blocker). Nếu cả A và B đều đạt, chọn B (tĩnh, không tốn TraCI). Nếu cả hai trượt, dừng lại và báo người dùng.
- [ ] Ghi kết quả + quyết định vào `docs/research/spike_right_block.md` và PROGRESS (ruling mới).

### Task N3: Spike khả thi "đi ngược chiều để kịp đèn"

**Files:** Create `experiments/spike_wrong_way/run.py`, `docs/research/spike_wrong_way.md`.

- [ ] Kiểm tra trước bằng `sumo --help`/`netconvert --help` và tài liệu: hỗ trợ lái sang làn ngược chiều (`--opposites.guess`, `lcOpposite`) có hoạt động với `--lateral-resolution` + SL2015 trên SUMO 1.27 không. Ghi đường dẫn tài liệu.
- [ ] Hai cách cần thử:
  - (A) Overtake ngược chiều native (`lcOpposite*`) chỉ cho một vClass vi phạm.
  - (B) Tĩnh: một làn hẹp ngược chiều (vd 1,0 m, chỉ cho `custom3`) dọc mép trái làn ra của cùng trục, nối vào gần vạch dừng của nhánh vào.
- [ ] Tiêu chí chọn (đặt trước): xe vi phạm đến vạch dừng sớm hơn xe cùng hàng chờ; va chạm làn của xe vi phạm được ghi vào `collisions.xml`; tổng va chạm/h không tăng quá X so với không có xe vi phạm (**X do người dùng chốt**; đề xuất ≤ 2/h). Nếu không đạt, đề xuất giữ hành vi này ngoài phạm vi và ghi vào Ch.6 (hướng phát triển).

### Task N4: Hiện thực hai hành vi + chỉ số M9/M10

Chỉ làm phần nào có spike đạt. Hình dạng cụ thể phụ thuộc kết quả N2/N3; dưới đây là trường hợp spike chọn luật TraCI. Nếu spike chọn cách tĩnh thì thay bằng patch net + vClass, giống `custom1`.

**Files:**
- Modify: `src/thesis_sumo/rules/schema.py`: thêm luật `right_lane_block` {`q_min_m` ∈ [5,80], `p` ∈ [0,1]} và (nếu đạt) `wrong_way_rush` {`q_min_m` ∈ [5,80], `p` ∈ [0,1], `t_before_green_s` ∈ [0,10]}. Miền là `assumed`.
- Create: `src/thesis_sumo/runtime/rules/right_lane_block.py`, `wrong_way_rush.py`; đăng ký vào `RULE_REGISTRY`.
- Modify: validator: luật không áp dụng được ở nhánh không có `right_turn_continuous` → mã `logic` (giống `wrong_lane_dodge`).
- Create: `src/thesis_sumo/metrics/m9_right_block.py` (tỷ lệ chu kỳ có làn rẽ phải bị chặn tại thời điểm bắt đầu xanh), `m10_wrong_way.py` (tỷ lệ xe máy dùng làn ngược chiều).
- Modify: `schema_observed.py` nếu M9/M10 cần cột mới; proxy generator và `data/proxy/targets.yaml` thêm target `assumed`.
- Test: `tests/test_runtime.py`, `tests/test_validator.py`, `tests/test_metrics.py`, `tests/test_proxy.py`.

- [ ] Test runtime, mỗi luật một kịch bản trên mạng nhỏ: luật bật thì có ≥1 can thiệp `executed=True`; luật tắt (`p=0`) thì quỹ đạo giống hệt không có controller; không teleport jam; speed mode và lane-change mode được khôi phục.
- [ ] Test backend: libsumo và traci cho cùng `interventions.csv`.
- [ ] Test validator: `right_lane_block` trên site không có rẽ phải liên tục → lỗi `logic`; tham số ngoài miền → `rule_params`.
- [ ] Test metrics M9/M10 trên bảng dựng tay, giá trị tính tay.
- [ ] Thêm hai luật vào B1 với `p=0` (giữ cấu trúc cho tối ưu, giống `early_start`).
- [ ] Review → commit. Cập nhật PROGRESS, và đánh dấu Ch.1/Ch.3 của luận văn cần sửa phạm vi.

### Task R28: Chẩn đoán va chạm junction + chốt ngưỡng (agent thao tác)

Phải làm trên **mạng cuối** (sau N1–N4).

- [ ] `pgrep -af "sumo|runner"`: phải không còn tiến trình sót.
- [ ] Thí nghiệm một yếu tố trên D1, 3 seed, check-junctions BẬT (README §7.2): (a) bỏ xe vi phạm; (b) tắt sublane; (c) tách lane 2 thành làn chỉ đi thẳng hoặc chỉ rẽ. Bảng: va chạm lane/junction mỗi run.
- [ ] **Cổng quyết định (người dùng):** nếu ngưỡng theo R24 trên B0 vẫn ở khoảng 120/h (không lọc được gì), chọn giữa: sửa nguyên nhân gốc rồi chạy lại B0, hay chấp nhận ngưỡng cao và ghi rõ là giới hạn.
- [ ] Chạy B0 trên D1–D3 × seed 1–3 (gồm cả D3 seed 1 từng bị kill), tính `max(2, ceil(p90))` riêng cho lane và junction, ghi vào `experiment.yaml`, commit **trước** vòng LLM 1.

### Task 11: Harness đánh giá + bộ đếm ngân sách

- Produces: `evaluate(spec_path, days, seeds) -> EvalResult(score, per_metric, runs, eligible: bool)`; `Budget(total_runs).charge(n)` raise `BudgetExceeded`.
- [ ] Test: spec không hợp lệ thì không trừ ngân sách; chạy 36 run thì lần thứ 37 raise; run không đủ điều kiện (theo ngưỡng R28) không được chọn làm best.
- [ ] Chốt `budget.sumo_runs = 36`, `score.weights` (**người dùng chốt**; đề xuất chia đều M1–M10) trong `experiment.yaml`.

### Task 12: LLM client, prompt, feedback

- Produces: `LLMClient(base_url, model, temperature).generate_specs(prompt, n) -> list[dict]` qua openai SDK; `build_prompt(round, feedback) -> str` (prompt có version); `build_feedback(eval_result, validator_errors, interventions) -> str` (không chứa D4–D5).
- [ ] Test (mock HTTP): JSON hỏng → retry tối đa K lần rồi bỏ mẫu, không tốn ngân sách; timeout → như trên; mọi request/response lưu nguyên văn.
- [ ] Test: feedback không chứa chuỗi `PROXY_D4`/`PROXY_D5`.
- [ ] Schema gửi LLM là tập con an toàn với structured decoding của Ollama; validator từ chối id archetype trùng tên vType mặc định của SUMO.
- [ ] Chốt `llm.yaml`: base_url Ollama, `qwen3.5:9b`, temperature, `n_samples=4`.

### Task 13: Vòng LLM 3 vòng

- [ ] 3 vòng × 4 spec × 3 seed trên D1–D3 = 36 run. Ghi tỷ lệ spec hợp lệ theo vòng, khoảng cách theo chỉ số qua các vòng, spec best.
- [ ] Kiểm tra Ollama đang chạy (`curl` qua skill curl-preflight) trước khi bắt đầu.

### Task 14: Optuna B2

- [ ] Cùng không gian (bounds + tham số luật), cùng `score`, cùng 36 run (12 trial × 3 seed), cấu trúc = B1 (gồm cả hai luật mới với `p` mở).
- [ ] Test: sampler có seed thì tái lập được; không gian sinh ra từ `param_bounds.yaml` (không lặp lại khai báo).

### Task 15: Benchmark + báo cáo

- [ ] B0, B1, B2, P × D4–D5 × 20 seed; Mann–Whitney + Holm + Cliff's delta; chẩn đoán 3600 s × 3 seed cho B0 và P trên D4 (bật SSM).
- [ ] Bảng kết quả + cập nhật Ch.4–6 của luận văn (kể cả các TODO va chạm B0 và phạm vi mới).

## Ngoài plan (YAGNI)

Ablation từng luật, kịch bản chính sách 0/50/100 %, và chạy 3600 s cho vòng hiệu chỉnh: chỉ làm nếu còn thời gian sau Task 15.
