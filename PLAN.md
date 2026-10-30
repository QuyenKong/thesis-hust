# PLAN — Thiết lập dự án SUMO cho luận văn thạc sĩ

> Tài liệu này dành cho **Claude Code** chạy trên máy Windows của Viktor.
> Đọc hết trước khi làm. Làm **theo từng phase**, dừng lại báo cáo sau mỗi phase (kết quả, lệnh đã chạy, vấn đề gặp phải) và chờ xác nhận rồi mới sang phase tiếp theo.

---

## 0. Bối cảnh và các quyết định ĐÃ CHỐT (không tự ý thay đổi)

**Đề tài:** Dùng LLM chạy local sinh và tinh chỉnh lặp tập luật hành vi tài xế cho SUMO, để mô phỏng tái hiện được giao thông hỗn hợp ô tô – xe máy **không tuân thủ** tại một nút giao ở Hà Nội. Sau đó dùng mô hình đã hiệu chỉnh để **đánh giá các phương án tổ chức giao thông** (tín hiệu đèn, phân làn, tổ chức hướng rẽ, cưỡng chế). Phân tích then chốt: so thứ hạng phương án giữa SUMO mặc định (giả định người lái tuân thủ) và mô hình đã hiệu chỉnh.

| Hạng mục | Quyết định |
|---|---|
| Vị trí | **1 nút giao duy nhất: Lê Văn Lương × Hoàng Đạo Thúy**, Thanh Xuân, Hà Nội (~21.0053, 105.8047). Nút có đèn, 4 nhánh |
| Loại phương tiện | Chỉ ô tô (`passenger`) và xe máy. Không có người đi bộ, xe buýt, xe tải |
| Khung giờ | Cao điểm sáng 07:30–09:00 |
| Dữ liệu thực | Viktor tự quay video tại nút, nhiều ngày (pipeline xử lý video **nằm ngoài plan này**; plan này chỉ định nghĩa schema dữ liệu quan sát) |
| Kênh luật | **vType (tĩnh) + TraCI (luật có điều kiện)**, cộng **các bản vá mạng tĩnh chỉ dành cho lớp xe vi phạm** (`custom1` = xe máy vi phạm, `custom2` = ô tô vi phạm). LLM KHÔNG sinh/sửa network; LLM chỉ quyết định tỷ trọng kiểu tài xế, tham số và điều kiện kích hoạt |
| Hạ tầng đã xác nhận | **Mọi nhánh có làn rẽ phải liên tục** (làn ngoài cùng bên phải, không bị đèn điều khiển). Lê Văn Lương có **dải phân cách cứng chỉ ở một đoạn ngắn trước vạch dừng**; phía trước không có dải phân cách |
| Rẽ trái trái phép | Một trong 11 hành vi (không phải trọng tâm riêng): người vi phạm đi vào giữa nút trong pha xanh của nhánh mình, **dừng chờ giữa nút**, rồi **rẽ khi pha xanh đi thẳng của hướng đối diện kết thúc** |
| Baseline | B0 = SUMO mặc định; B1 = luật thủ công chuyển từ Saval et al. (2023, PLOS ONE, mô hình GAMA cho Hà Nội) sang SUMO; B2 = Optuna chỉnh tham số trên cấu trúc cố định (= cấu trúc của B1); P1 = LLM chỉnh tham số trên cùng cấu trúc cố định; P2 = LLM sinh cả cấu trúc lẫn tham số; H = cấu trúc do LLM sinh + tham số do Optuna. Mọi phương án dùng **cùng ngân sách số lần chạy SUMO** |
| Thí nghiệm | **E1** (P1 vs B2, cấu trúc cố định): LLM như bộ tối ưu. **E2** (B2 vs H vs P2): giá trị của cấu trúc luật do LLM sinh |
| LLM | Local, gọi qua **OpenAI-compatible API** (Ollama / vLLM / LM Studio). Model mục tiêu: Qwen3.8-27B. Code KHÔNG được phụ thuộc vào một runtime cụ thể |

**Hành vi trong phạm vi (11 hành vi, 3 nhóm):**

- **F1 — Không tuân thủ tín hiệu**
  1. Ngưỡng kiên nhẫn / vượt đèn đỏ (`patience`)
  2. Áp lực bầy đàn: vượt đỏ theo đoàn (`swarm_pressure`)
  3. Xuất phát sớm trước khi đèn xanh (`early_start`)
- **F2 — Tìm khoảng trống khi ùn** (chung một cơ chế: hàng chờ dài → tìm khoảng trống khác để lên đầu hàng)
  4. Khoảng cách ngang, lấn chiếm, luồn lách (`minGapLat`, `encroachment`)
  5. Đi sai làn để né đèn (`S_cheat`)
  6. **Chặn làn rẽ phải liên tục**: xe máy và ô tô có ý định đi thẳng hoặc rẽ trái dừng chờ đèn đỏ trên làn rẽ phải liên tục (30 m cuối trước vạch dừng của làn 0) — **ưu tiên cao**. Làn này chỉ tồn tại ở 30 m cuối; thượng nguồn cả ba làn là làn thường. Rẽ phải được đi cả khi đèn đỏ. Khi đèn xanh, đi thẳng hoặc rẽ trái trên làn này vẫn đúng luật; chỉ việc dừng chờ đèn đỏ ở đó là vi phạm
  7. **Đi trên vỉa hè** để vượt hàng chờ — **ưu tiên cao**
  8. **Đi ngược chiều** ở đoạn không có dải phân cách, cắt về trước đoạn dải phân cách cứng — **giai đoạn sau, tùy kết quả Phase 3**
- **F3 — Tương tác trong nút**
  9. Hệ số ảo tưởng / chấp nhận khoảng trống nhỏ, tạt đầu (`f`)
  10. Rẽ trái trái phép kiểu chờ giữa nút (`illegal_left_box`)
  11. Xe máy đi chậm giữa làn (`I_slow`)

Vì mọi nhánh có làn rẽ phải liên tục, **rẽ phải khi đèn đỏ không phải vi phạm** và không được mô hình như vi phạm.

**Ngoài phạm vi** (KHÔNG cài đặt): người đi bộ, xe buýt, ô tô đỗ bừa dưới lòng đường, mô hình quyết định chọn lộ trình (`U_route`).

---

## 1. Quy tắc làm việc cho Claude Code

- **Không bịa số liệu hiện trường.** Mọi giá trị đo thực địa (bề rộng làn, chu kỳ đèn, nhánh nào cấm rẽ, lưu lượng) lấy từ `config/site.yaml`. Giá trị chưa có thì để `null` kèm comment `# TODO_MEASURE`. Code phải báo lỗi rõ ràng khi gặp `null` ở chỗ bắt buộc, không được tự điền giá trị mặc định.
- **Không đoán tên tham số SUMO.** Mọi attribute vType, option netconvert/sumo phải kiểm tra bằng `sumo --help`, `netconvert --help` hoặc tài liệu chính thức (sumo.dlr.de/docs) trước khi dùng. Bảng bounds tham số (Phase 4) phải ghi nguồn cho từng dòng.
- **Thư mục `scenario_raw/` là bất biến.** Không sửa file trong đó.
- **Mọi thứ phải tái lập được:** network sinh từ script cộng patch file (không sửa tay `.net.xml`), seed cố định, mỗi lần chạy ghi `manifest.json`.
- Windows: dùng `pathlib`, không hardcode `\`. Đọc được cả file `.xml` lẫn `.xml.gz`.
- Python ≥ 3.10, dùng venv. Thêm test `pytest` cho validator, compiler, metric (dùng dữ liệu tổng hợp nhỏ).
- Khi không chắc một hành vi của SUMO: **viết thí nghiệm nhỏ để kiểm chứng**, đừng giả định.

---

## 2. Cấu trúc repo đích

```
thesis-sumo/
├── PLAN.md                        # file này
├── CLAUDE.md                      # tóm tắt quy tắc mục 1 + lệnh hay dùng (tạo ở Phase 0)
├── README.md
├── pyproject.toml / requirements.txt
├── config/
│   ├── site.yaml                  # số liệu hiện trường (TODO_MEASURE)
│   ├── experiment.yaml            # seeds, step-length, lateral-resolution, ngân sách chạy
│   └── llm.yaml                   # base_url, model, temperature, n_samples
├── scenario_raw/                  # bản copy nguyên thư mục OWZ — KHÔNG SỬA
├── scenario/
│   ├── net/
│   │   ├── base.net.xml           # cắt từ OSM, sinh bởi script
│   │   ├── patches/               # *.edg.xml, *.con.xml, *.tll.xml (plain XML)
│   │   └── site.net.xml           # base + patches = mạng dùng để chạy
│   └── demand/
│       ├── candidate_routes.rou.xml
│       └── routes_<day>.rou.xml   # sinh bởi routeSampler từ số đếm
├── data/
│   └── observed/<day>/            # CSV theo schema ở Phase 6 (từ video)
├── rules/
│   ├── schema/rule_spec.schema.json
│   ├── bounds/param_bounds.yaml   # bounds tham số kèm nguồn
│   ├── specs/<spec_id>.json       # bộ luật (thủ công / LLM / Optuna)
│   └── compiled/<spec_id>/        # vtypes.add.xml + traci_rules.json
├── src/thesis_sumo/
│   ├── net/        build_net.py, apply_patches.py
│   ├── demand/     build_demand.py
│   ├── rules/      schema.py, validator.py, compiler.py
│   ├── runtime/    controller.py, rules/*.py   # luật TraCI
│   ├── sim/        runner.py, outputs.py
│   ├── metrics/    m1_headway.py … m11_wrong_way.py, g0_geh.py, distance.py
│   ├── llm/        client.py, prompts/, loop.py
│   ├── baselines/  optuna_search.py
│   └── policy/     evaluate.py                 # đánh giá phương án, so thứ hạng B0 vs mô hình hiệu chỉnh
├── experiments/
│   └── runs/<run_id>/seed_XX/     # output SUMO thô
├── results/
│   ├── metrics.csv                # 1 dòng = 1 spec × 1 seed × 1 day
│   └── figures/
└── tests/
```

---

## Phase 0 — Môi trường và khung repo

1. Kiểm tra `SUMO_HOME`, `sumo --version` (kỳ vọng 1.27.x), `netconvert`, `python`.
2. Tạo venv. Ưu tiên dùng `traci` và `sumolib` từ `%SUMO_HOME%/tools` (thêm vào `sys.path` hoặc `.pth`) để khớp phiên bản với binary SUMO. Thử `import libsumo`: nếu được thì runner hỗ trợ cả `libsumo` (nhanh hơn) và `traci` (dùng để debug với GUI) qua một biến cờ.
3. Tạo cấu trúc thư mục, `git init`, `.gitignore` (bỏ qua `experiments/runs/`, `*.xml.gz` output lớn, video).
4. Copy thư mục OWZ của Viktor vào `scenario_raw/` (hỏi Viktor đường dẫn; thư mục gốc có dạng `D:\hust-master\Thesis\SUMO\2026-10-02-06-34-26`).
5. Tạo `config/site.yaml` theo mẫu dưới, mọi giá trị đo thực địa để `null`:

```yaml
intersection:
  name: "Le Van Luong x Hoang Dao Thuy"
  center_lonlat: [105.8047, 21.0053]
  cut_radius_m: 300            # độ dài mỗi nhánh giữ lại
approaches:                    # điền sau khi map edge id ↔ hướng ở Phase 1
  - id: LVL_W                  # tên logic
    edge: null
    lane_widths_m: null        # TODO_MEASURE, danh sách theo làn
    left_turn_banned: null     # TODO_MEASURE
    u_turn_banned: null        # TODO_MEASURE
    continuous_right_lane: true          # đã xác nhận: mọi nhánh có làn rẽ phải liên tục
    right_lane_separator: null           # TODO_MEASURE: none | paint | bollards
    sidewalk_width_m: null               # TODO_MEASURE
    hard_median_length_m: null           # TODO_MEASURE: chiều dài đoạn dải phân cách cứng trước vạch dừng (0 nếu không có)
signal:
  type: static
  cycle_s: null                # TODO_MEASURE từ video
  phases: null                 # TODO_MEASURE: [{name, duration_s, green_movements}], gồm vàng và all-red
illegal_left:
  approaches: null             # TODO_MEASURE: nhánh có người rẽ trái trái phép
violator_classes:
  moto: custom1                # xe máy vi phạm: rẽ trái bị cấm, rẽ trái/quay đầu từ làn 0 và làn 1 (vượt đèn đỏ), làn vỉa hè
  car: custom2                 # ô tô vi phạm: rẽ trái/quay đầu từ làn 0 và làn 1 (vượt đèn đỏ)
f2_measured_approaches: null   # TODO: 1–2 nhánh dùng để đo nhóm F2 (camera thấy hàng chờ 50–100 m, vỉa hè)
```

**Tiêu chí xong:** `python -c "import traci, sumolib"` chạy được; `pytest` chạy (chưa có test); `CLAUDE.md` đã tạo.

---

## Phase 1 — Network: cắt nút giao và dựng mạng tái lập được

1. `build_net.py`: chạy netconvert từ `scenario_raw/osm_bbox.osm.xml.gz`, chỉ giữ vùng quanh nút (bán kính `cut_radius_m`; kiểm tra option `--keep-edges.in-geo-boundary` hoặc cách tương đương bằng `netconvert --help`). Yêu cầu:
   - Giữ internal links (mặc định), sublane-ready.
   - Đèn tại nút đích: kiểu static. Không để `actuated`.
   - Loại bỏ đèn và nút phụ trên các nhánh nếu chúng làm hàng chờ bị chặn sớm (báo cáo danh sách trước khi xóa).
   - Chỉ giữ edge cho phép `passenger`/`motorcycle`; bỏ footway, service, subway.
2. **Map edge id ↔ hướng.** In bảng: edge id, tên đường, hướng (Bắc/Nam/Đông/Tây), số làn, độ dài, các connection (r/s/l/t). Lưu ý: edge `1071601648#4` không có tên trong OSM, có thể là chiều còn lại của Hoàng Đạo Thúy — phải xác minh. Ghi kết quả vào `site.yaml → approaches[].edge`.
3. **Hiện trạng OSM đã biết:** cả 4 nhánh đều có connection rẽ trái (`l`) và quay đầu (`t`) từ làn trong cùng, trạng thái `g`, trong chương trình đèn 2 pha đoán 41s/4s. OSM không có quan hệ cấm rẽ tại nút này. Mọi bề rộng làn đều là mặc định 3.2 m.
4. `apply_patches.py`: áp các plain-XML patch lên `base.net.xml` qua `netconvert -s base.net.xml -e ... -x ... -i ...`, ra `site.net.xml`. Sinh patch từ `site.yaml`:
   - `lanes.edg.xml`: bề rộng làn thực đo.
   - `turns.con.xml`:
     - Với nhánh `left_turn_banned: true`, xóa connection rẽ trái hợp lệ, rồi **thêm lại connection rẽ trái chỉ cho phép vClass `custom1`** (kiểm tra cú pháp permission ở mức `<connection>` trong docs netconvert). Làm tương tự với `u_turn_banned`.
     - **Làn rẽ phải liên tục** (Viktor 28 và 29/10): cạnh nhánh được cắt ở `right_lane_length_m` (30 m) trước vạch dừng; đoạn thượng nguồn là ba làn thường. Ở đoạn 30 m cuối, làn 0 có connection rẽ phải (luôn `g`) và đi thẳng (mọi xe, theo đèn đi thẳng). Thêm **connection rẽ trái từ làn 0** (nhánh không cấm rẽ trái) và **quay đầu từ làn 0 và làn 1**, chỉ cho `custom1` và `custom2`, theo đèn rẽ trái của nhánh; xe tuân thủ vẫn rẽ trái và quay đầu từ làn 2.
   - `sidewalk.edg.xml` / `sidewalk.con.xml`: trên các nhánh trong `f2_measured_approaches`, thêm **một làn vỉa hè** ở mép phải (bề rộng = `sidewalk_width_m`, chỉ `allow="custom1"`, tốc độ thấp), nối vào hướng rẽ phải và vào làn ngoài cùng trước vạch dừng. Người đi bộ nằm ngoài phạm vi, nên làn này không có tương tác với người đi bộ.
   - `signal.tll.xml`: chương trình đèn static từ `site.yaml → signal`. Link rẽ trái trái phép có trạng thái `g` trong pha xanh đi thẳng của nhánh nó. **Link rẽ phải liên tục ở trạng thái xanh trong mọi pha** (không bị đèn điều khiển).
   - Khi `site.yaml` còn `null`: sinh mạng dùng giá trị OSM hiện tại và **in cảnh báo rõ ràng** là đang dùng giá trị chưa đo.
5. Xuất ảnh/SVG sơ đồ nút (dùng sumolib + matplotlib) có ghi chú edge id và hướng để Viktor đối chiếu với thực tế.

**Tiêu chí xong:** `site.net.xml` sinh được từ đầu chỉ bằng một lệnh; `netconvert` không báo lỗi; có bảng map edge ↔ hướng và hình sơ đồ.

---

## Phase 2 — Baseline chạy được (demand tạm)

1. **vTypes baseline** `rules/compiled/B0/vtypes.add.xml`:
   - `car`: vClass `passenger`.
   - `moto`: vClass `motorcycle`.
   - `moto_violator`: vClass `custom1`; kích thước, tốc độ và động học **sao chép từ giá trị mặc định của `motorcycle`** (đọc docs vClass defaults; vClass custom1 không tự có các giá trị này).
   - `car_violator`: vClass `custom2`; sao chép từ giá trị mặc định của `passenger`.
   - Tất cả dùng `laneChangeModel="SL2015"`; các tham số khác để mặc định SUMO.
2. **Demand tạm** (cho tới khi có số đếm thật):
   - Sinh `candidate_routes.rou.xml` gồm mọi lộ trình hợp lệ qua nút (vào → ra).
   - `build_demand.py` đọc file đếm theo schema `turn_counts.csv` (Phase 6) và chạy `routeSampler.py` (`%SUMO_HOME%/tools/routeSampler.py`, input dạng turn-count / edgeRelation; kiểm tra option bằng `--help`).
   - Tạo file `data/observed/SYNTHETIC/turn_counts.csv` với số đếm giả định **đánh dấu rõ SYNTHETIC**, chỉ để chạy thông pipeline. Không dùng trong kết quả.
3. **sumocfg baseline**, sinh bằng code từ `experiment.yaml`:
   - `step-length` 0.1, `lateral-resolution` 0.4 (để cấu hình được).
   - Output:
     - `tripinfo`, `tlsStates` (timedEvent `SaveTLSStates`);
     - `instantInductionLoop` tại vạch dừng mỗi làn vào và vạch ra mỗi làn ra;
     - `fcd` **lọc theo vùng nút** (bán kính ~60 m) và có vị trí ngang (kiểm tra attribute `posLat` / `--fcd-output.attributes`);
     - `lanechange-output`;
     - SSM device với measure `PET` (`--device.ssm.probability 1`, `--device.ssm.measures "PET"`; kiểm tra docs).
   - Tắt `device.rerouting`. Không dùng `ignore-route-errors` trong config chính thức.
4. `runner.py`: `run(spec_id, day, seed, use_gui=False)` → `experiments/runs/<run_id>/seed_XX/`. Ghi `manifest.json` gồm git hash, phiên bản SUMO, hash của spec, hash của `site.net.xml`, seed, cấu hình. Hỗ trợ chạy song song nhiều seed (multiprocessing, mỗi process một instance SUMO).

**Tiêu chí xong:** B0 chạy 3600 s với 3 seed; báo cáo số teleport, số va chạm, số xe chờ chèn vào mạng (insertion backlog). Nếu có teleport thì tìm nguyên nhân và báo cáo, không giấu bằng option.

---

## Phase 3 — Thí nghiệm khả thi (BẮT BUỘC trước Phase 4)

Bốn thí nghiệm nhỏ, mỗi cái một kịch bản riêng, báo cáo kèm số liệu.

### 3A. Chặn làn rẽ phải liên tục
Làn 0 ở 30 m cuối cho đi thẳng khi xanh, nên xe đi thẳng đứng chờ đèn đỏ ở đó đến từ cách SUMO chọn làn và từ hàng chờ. Câu hỏi: tần suất xe đi thẳng đứng chờ ở làn 0 có gần mục tiêu M9 không, xe rẽ phải phía sau bị kẹt bao lâu, và rẽ trái hoặc quay đầu từ làn 0 và làn 1 lúc đèn đỏ (connection chỉ cho `custom1`/`custom2`) gây bao nhiêu xung đột với dòng đi thẳng từ làn 1 và 2?

### 3B. Làn vỉa hè
Xe `custom1` có vào làn vỉa hè, đi hết và nhập lại đúng chỗ không; có kẹt hoặc teleport ở điểm nhập không.

### 3C. Đi ngược chiều (khả thi hay hoãn)
Kiểm tra tính năng vượt sang làn đối diện của SUMO (tìm trong docs: opposite direction driving / overtaking, option netconvert tạo cặp cạnh đối diện) có chạy với `laneChangeModel="SL2015"` không. Nếu không: thử phương án làn ảo ngược chiều chỉ cho `custom1`, và ghi rõ là SUMO **không tính xung đột** giữa làn ảo và dòng ngược chiều thật. Báo cáo để Viktor quyết định làm hay hoãn.

### 3D. Chờ giữa nút (rẽ trái trái phép)
Câu hỏi cần trả lời: **SUMO (sublane, SL2015) cho bao nhiêu xe máy cùng dừng chờ tại điểm chờ bên trong nút (internal junction) trên link rẽ trái?** Ngoài thực tế có thể có hàng chục xe máy tích tụ giữa nút.

1. Kịch bản test: dòng đi thẳng ngược chiều dày đặc trong pha xanh; nhiều `moto_violator` rẽ trái từ một nhánh.
2. Đo theo từng bước: số xe đang ở trên các internal lane của link rẽ trái; vị trí ngang của chúng; thời điểm chúng xả ra (so với thời điểm pha đối diện chuyển sang vàng/đỏ).
3. Kiểm tra thêm:
   - Xe đang chờ trong nút có tự xả khi pha đối diện kết thúc không, có bị kẹt (deadlock / teleport) không.
   - Chúng tương tác thế nào với xe của hướng giao cắt bắt đầu đi khi pha mới bắt đầu.
4. Báo cáo kèm số liệu, và đề xuất một trong hai hướng:
   - **(a) Native:** internal junction đủ dùng.
   - **(b) Vùng chờ tường minh:** thêm một edge "khu chờ" giữa nút cho `custom1`, có link đèn riêng, xanh khi pha đi thẳng đối diện đỏ. Hướng này dùng khi sức chứa native quá nhỏ so với thực tế.

Thêm cho 3D: xe đang vượt đỏ nhờ tham số `jm*` có còn nhường xe hướng khác theo logic xung đột của nút không (ảnh hưởng trực tiếp đến PET).

**Dừng lại chờ Viktor chọn hướng cho 3C và 3D.**

---

## Phase 4 — Rule spec: schema, validator, compiler

### 4.1 Schema `rule_spec.schema.json` (JSON Schema draft 2020-12)

```jsonc
{
  "spec_id": "string",
  "source": "manual | llm | optuna",
  "provenance": { "model": "...", "prompt_version": "...", "iteration": 0, "sample_idx": 0 },
  "driver_archetypes": [            // -> vTypeDistribution, KHÔNG phải 1 vType
    {
      "id": "moto_compliant",
      "base_vclass": "motorcycle | passenger | custom1 | custom2",
      "share": 0.0,                 // tỷ trọng trong distribution của vClass đó, tổng = 1
      "params": { "<sumo_attr>": 0.0 },      // chỉ attr có trong param_bounds.yaml
      "rationale": "string"          // LLM giải thích (bắt buộc với source=llm)
    }
  ],
  "traci_rules": [
    {
      "rule_type": "early_start | swarm_red_running | queue_space_seeking | illegal_left_box | slow_lane_center",
      "applies_to": ["archetype_id"],
      "params": { },                 // theo schema riêng của từng rule_type
      "rationale": "string"
    }
  ]
}
```

### 4.2 `param_bounds.yaml`

- Danh sách attribute vType được phép tune, kèm `min`, `max`, `default`, `unit`, `model` (vType/carFollow/LC/junction), **`source_url`**, và `behavior_group` (map sang 11 hành vi ở mục 0).
- Các nhóm ứng viên (phải kiểm tra từng tên trong docs trước khi đưa vào):
  - **car-follow:** `tau`, `minGap`, `accel`, `decel`, `sigma`, `speedFactor`, `speedDev`.
  - **sublane:** `minGapLat`, `maxSpeedLat`, `latAlignment`.
  - **LC:** `lcSublane`, `lcPushy`, `lcPushyGap`, `lcAssertive`, `lcImpatience`, `lcTimeToImpatience`, `lcAccelLat`, `lcMaxSpeedLatStanding`, `lcSpeedGain`.
  - **junction:** `impatience`, `jmDriveAfterRedTime`, `jmDriveRedSpeed`, `jmDriveAfterYellowTime`, `jmIgnoreFoeProb`, `jmIgnoreFoeSpeed`, `jmTimegapMinor`.
- Ánh xạ hành vi → tham số (để LLM và Optuna dùng chung không gian):

| Hành vi | vType | TraCI rule |
|---|---|---|
| patience / vượt đỏ | `impatience`, `jmDriveAfterRedTime`, `jmDriveRedSpeed`, `lcImpatience` | — |
| swarm_pressure | — | `swarm_red_running` |
| early_start | — | `early_start` |
| minGapLat / encroachment | `minGapLat`, `latAlignment`, `lcSublane`, `lcPushy`, `lcMaxSpeedLatStanding` | — |
| f (ảo tưởng) | `lcAssertive`, `lcPushyGap`, `jmTimegapMinor`, `jmIgnoreFoeProb`, `tau` | — |
| S_cheat (sai làn né đèn) | — | `queue_space_seeking` (lựa chọn `wrong_lane`) |
| Chặn làn rẽ phải liên tục | tham số vType và cách SUMO chọn làn; rẽ trái/quay đầu từ làn 0 và 1 qua luật vượt đèn đỏ của `custom1`/`custom2` | `queue_space_seeking` (lựa chọn `right_lane`, chỉ khi mạng cấm đi thẳng từ làn 0) |
| Đi trên vỉa hè | tham số của `custom1` | `queue_space_seeking` (lựa chọn `sidewalk`) |
| Đi ngược chiều (sau) | tham số LC đối diện nếu 3C khả thi | `queue_space_seeking` (lựa chọn `opposite`) |
| I_slow | `speedFactor`, `speedDev` (archetype riêng) | `slow_lane_center` (tùy chọn) |
| illegal_left_box | các tham số `jm*` của archetype `custom1` | `illegal_left_box` (chỉ khi Phase 3 chọn hướng b, hoặc cần điều chỉnh lúc xả) |

### 4.3 `validator.py`

- Kiểm tra theo JSON Schema; tên attribute phải nằm trong bounds; giá trị nằm trong `[min, max]`; tổng `share` = 1 cho mỗi vClass; mỗi `rule_type` có params hợp lệ.
- Kiểm tra mâu thuẫn logic, ví dụ `minGapLat` lớn hơn bề rộng làn nhỏ nhất, hoặc `sigma`/`speedDev` ngoài miền hợp lý.
- Trả về danh sách lỗi có cấu trúc (để đưa ngược lại cho LLM).
- **Đếm và log tỷ lệ spec hợp lệ.** Đây là một metric của luận văn.

### 4.4 `compiler.py`

- Spec → `vtypes.add.xml` (`vTypeDistribution` cho mỗi vClass) + `traci_rules.json`.
- Đảm bảo id phù hợp với demand: demand tham chiếu tên distribution (`car`, `moto`, `moto_violator`), compiler sinh ra các distribution đúng các tên đó.

### 4.5 `runtime/controller.py` + `runtime/rules/*.py`

- Registry pattern: mỗi `rule_type` là một class có `on_step(state)`. Controller dùng subscription (không gọi get từng xe ở từng bước) và chỉ xử lý xe trong vùng nút.
- Mỗi lần can thiệp phải ghi log: thời điểm, xe, rule, hành động, **và kết quả có được SUMO thực thi hay không**.
  - Chú ý `setSpeedMode` / `setLaneChangeMode`: override sai có thể tắt cơ chế an toàn hoặc khiến lệnh bị bỏ qua âm thầm.
  - Khôi phục mode sau khi can thiệp xong.
- Logic các rule (tham số là ngưỡng/xác suất mà LLM điền):
  - `early_start`: trong `t_before_green` giây cuối pha đỏ, xe đầu hàng thuộc archetype áp dụng nhích qua vạch với xác suất `p`, tốc độ ≤ `v_max`. Cần đọc thời gian còn lại của pha từ TLS.
  - `swarm_red_running`: xác suất vượt đỏ của một xe tăng theo số xe đã vượt đỏ trong `Δt` giây gần nhất trên cùng nhánh: `p = p0 + k·n` (cắt ở `p_max`).
  - `queue_space_seeking` (gộp sai làn, chặn làn rẽ phải, vỉa hè, ngược chiều): kích hoạt khi hàng chờ ở làn đúng dài ≥ `q`, hoặc thời gian chờ ≥ `t_w`, hoặc đèn sắp xanh. Xe chọn một khoảng trống thay thế **đang tồn tại trong mạng** (`wrong_lane`, `right_lane`, `sidewalk`, `opposite`) theo xác suất `p_*` do LLM điền, tốc độ ≤ `v_creep`. Khi một lựa chọn không có trong mạng (ví dụ phương án chính sách đã chặn vỉa hè), xác suất của nó được **phân bổ lại** cho các lựa chọn còn lại theo tỷ lệ — đây là cơ chế "dồn hành vi" dùng trong đánh giá phương án. Ngoài khi được kích hoạt, xe vi phạm phải bị khóa không vào các làn/liên kết vi phạm (dùng `setLaneChangeMode` hoặc cơ chế tương đương, theo kết quả 3A).
  - `illegal_left_box`: theo kết quả Phase 3.
  - `slow_lane_center` (tùy chọn): giữ archetype I_slow chạy ở giữa làn.

**Tiêu chí xong:** test cho validator (spec đúng/sai), compiler (snapshot XML), mỗi rule TraCI có một kịch bản test chứng minh nó kích hoạt và được thực thi; spec thủ công `B1_manual.json` chạy được qua runner.

---

## Phase 5 — Metric và hàm tương đồng

### 5.1 Schema dữ liệu quan sát `data/observed/<day>/`

Pipeline video sau này phải xuất ra **đúng các file này**. Phía mô phỏng xuất ra cùng schema để dùng chung một bộ hàm metric.

| File | Cột |
|---|---|
| `turn_counts.csv` | `interval_start, interval_end(15'), approach, movement(l/s/r/u/illegal_l), vclass(car/moto), count` |
| `signal_events.csv` | `t, approach_group, state(G/y/r)` |
| `stopline_crossings.csv` | `t, approach, lane_or_lat_m, vclass, track_id, signal_state_at_t` |
| `queue_snapshots.csv` | `cycle_id, t_green_onset, approach, queue_length_m, n_car, n_moto, area_m2` |
| `lateral_snapshots.csv` | `cycle_id, approach, track_id, vclass, lat_m, long_m_from_stopline` |
| `trajectories.parquet` (tầng 2) | `track_id, t, x, y, vclass` trong hệ tọa độ đã homography về mặt đường |
| `box_queue.csv` | `cycle_id, t, approach, n_waiting_in_box, t_clear_start, t_clear_end` |
| `queue_timeseries.csv` | `t (mỗi 2–5 s), approach, queue_length_m, n_car, n_moto` |
| `space_seeking_events.csv` | `t, cycle_id, approach, track_id, vclass, space(wrong_lane/right_lane/sidewalk/opposite), queue_length_m_at_t` |
| `right_turn_delay.csv` | `track_id, approach, vclass, t_enter, t_exit, blocked(bool)` |

### 5.2 Metric

Mỗi metric viết thành một hàm `compute(source) -> distribution | scalar`, chạy được trên cả dữ liệu quan sát lẫn output mô phỏng đã chuyển sang schema trên.

- **G0 (gác cổng, không tính điểm):** GEH của số đếm rẽ theo 15 phút. Yêu cầu GEH < 5 cho ≥ 85% ô; run trượt bị loại.
- **M1:** discharge headway theo vị trí trong hàng (sau khi đèn xanh), theo vClass. Ra phân phối.
- **M2:** xuất phát sớm: số xe qua vạch trong N giây cuối pha đỏ; độ trễ từ lúc xanh tới khi xe đầu tiên qua vạch.
- **M3:** vượt đỏ: phân phối số vi phạm mỗi chu kỳ (tính cả variance/mean); P(vi phạm \| k xe vi phạm trước đó trong Δt).
- **M4:** phân bố vị trí ngang của xe máy tại thời điểm đèn chuyển xanh; khoảng xe máy vượt qua vạch dừng.
- **M5:** chiều dài hàng chờ và mật độ xe máy tại thời điểm đèn chuyển xanh, theo nhánh.
- **M6:** thời gian đi qua nút / tốc độ theo hướng × vClass.
- **M7 (chấp nhận khoảng trống và rẽ trái trái phép):**
  - M7a: số xe chờ giữa nút khi pha đi thẳng đối diện kết thúc, và phân phối thời điểm xả trong chu kỳ;
  - M7b: PET giữa xe rẽ trái trái phép đang xả và xe của hướng giao cắt / xe đi thẳng ngược chiều cuối pha;
  - M7c: tổn thất thời gian khởi động của hướng giao cắt, so giữa các chu kỳ có hàng chờ giữa nút lớn và nhỏ.
- **M8:** tỷ lệ xe ở làn không khớp hướng đi ra (cần tracking).
- **M9 (chặn làn rẽ phải liên tục):** số xe đi thẳng đứng trên làn rẽ phải lúc chuyển xanh, theo độ dài hàng đi thẳng; phân phối thời gian trễ của xe rẽ phải.
- **M10 (vỉa hè):** số xe máy trên vỉa hè mỗi chu kỳ, theo độ dài hàng chờ.
- **M11 (ngược chiều, giai đoạn sau):** số xe đi ngược chiều mỗi chu kỳ, theo độ dài hàng chờ.
- Với nhóm F2, tính thêm **xác suất chọn từng khoảng trống theo độ dài hàng chờ** (từ `space_seeking_events.csv` + `queue_timeseries.csv`): đây là đại lượng ràng buộc trực tiếp các tham số `q`, `t_w`, `p_*` của `queue_space_seeking`.

### 5.3 `distance.py`

- Metric dạng phân phối: Wasserstein-1 chuẩn hóa theo IQR của dữ liệu quan sát. Metric dạng tỷ lệ/vô hướng: sai số tương đối.
- **Sàn nhiễu:** tính cùng các khoảng cách đó giữa các ngày quan sát với nhau. Báo cáo `d_sim_obs / d_day_day` cho từng metric.
- Điểm tổng (dùng cho bộ tối ưu): trung bình có trọng số của các khoảng cách đã chuẩn hóa; trọng số lấy từ `experiment.yaml`. Luôn lưu thêm từng thành phần riêng.

### 5.4 Tách dữ liệu

`experiment.yaml` có `calibration_days` và `validation_days`. LLM và Optuna **chỉ được thấy** thống kê của calibration days. Validation chỉ dùng để đánh giá cuối.

**Tiêu chí xong:** mọi metric chạy được trên output B0 với dữ liệu SYNTHETIC; có test với input dựng tay biết trước đáp án.

---

## Phase 6 — Vòng LLM

1. `llm/client.py`: OpenAI-compatible (`base_url`, `model` lấy từ `llm.yaml`).
   - Hỗ trợ structured output theo JSON Schema (Ollama: tham số `format` = schema; vLLM: structured outputs). Kiểm tra docs của runtime đang dùng.
   - Nếu runtime không hỗ trợ: validate rồi retry, tối đa 3 lần.
   - Lưu nguyên văn request/response (cả phần thinking nếu có) vào `experiments/llm_logs/`.
2. `llm/prompts/`, có version hóa (`v001`, `v002`...):
   - `system.md`: vai trò, mục tiêu realism, ràng buộc "chỉ dùng attribute có trong bounds".
   - `context.md`: mô tả nút giao, các hiện tượng VN đang xét, từ điển tham số (sinh tự động từ `param_bounds.yaml`), schema output.
   - `feedback.md`: kết quả vòng trước gồm khoảng cách theo từng metric, `d_sim_obs/d_day_day`, lỗi từ validator, log can thiệp TraCI. **Không chứa dữ liệu validation.**
3. `llm/loop.py`: mỗi iteration sinh `n_samples` spec, validate, compile, chạy SUMO với `n_seeds` seed, tính metric, giữ spec tốt nhất, tạo feedback cho iteration tiếp theo. **Đếm tổng số lần chạy SUMO** và dừng khi hết ngân sách.
4. Ghi chép đầy đủ: model, quant, temperature, seed của LLM (nếu runtime hỗ trợ), phiên bản prompt.

## Phase 7 — Baseline Optuna và benchmark

1. `baselines/optuna_search.py`: nhận một spec làm **cấu trúc** (archetypes + rule_type đang bật), chỉ tối ưu **tham số** trong cấu trúc đó (bounds từ `param_bounds.yaml` + params của các rule TraCI), cùng hàm mục tiêu, **cùng ngân sách số lần chạy SUMO** với vòng LLM. Dùng cho B2 (cấu trúc của B1) và H (cấu trúc do LLM sinh).
2. `llm/loop.py` có hai chế độ: `params_only` (P1: cấu trúc khóa, LLM chỉ được sửa giá trị; validator từ chối mọi thay đổi cấu trúc) và `full` (P2: LLM sửa cả cấu trúc lẫn tham số).
3. `rules/specs/B1_saval.json`: chuyển các luật của Saval et al. (2023) sang schema (ví dụ xe máy hàng đầu dừng đèn đỏ với xác suất 0,5). Ghi nguồn cho từng luật; mục nào không chuyển được sang SUMO thì ghi rõ lý do.
4. `benchmark.py`: chạy B0, B1, B2, P1, P2, H trên validation days với ≥ 20 seed. Báo cáo theo hai thí nghiệm: **E1** = P1 vs B2; **E2** = B2 vs H vs P2. Ghi `results/metrics.csv`; vẽ phân phối sim vs obs cho từng metric; chạy kiểm định Wilcoxon / Mann-Whitney và tính effect size.
5. Ablation: tắt lần lượt từng rule TraCI / từng nhóm tham số.
6. **Đánh giá phương án tổ chức giao thông** (`policy/evaluate.py`), chỉ chạy khi mô hình tốt nhất đạt R ≤ 1 trên validation days:
   - Mỗi phương án = một bộ patch (đèn / làn / connection) + giả định hành vi, khai báo trong `config/policies/<id>.yaml`. Nhóm: tín hiệu đèn, phân làn (cọc phân cách làn rẽ phải liên tục, chắn vỉa hè, kéo dài dải phân cách cứng, làn riêng xe máy, vùng chờ xe máy), tổ chức hướng rẽ, cưỡng chế (giảm tỷ trọng kiểu vi phạm và xác suất luật TraCI). Danh sách cụ thể do Viktor chốt.
   - Chạy **mỗi phương án với cả B0 (SUMO mặc định) và mô hình đã hiệu chỉnh**, ≥ 20 seed. Chỉ số: độ trễ theo nhánh và loại xe, hàng chờ lớn nhất, năng lực thông qua, số xung đột PET < ngưỡng, tỷ lệ vi phạm, và tỷ lệ chọn từng khoảng trống thay thế (để thấy hành vi bị dồn sang đâu).
   - Xuất **bảng so thứ hạng** phương án giữa hai mô hình (kèm kiểm định thứ hạng, ví dụ Kendall tau).
   - Mọi giả định hành vi (ví dụ mức giảm vi phạm khi tăng cưỡng chế) chạy phân tích độ nhạy và báo cáo khoảng dao động.
   - Không tính chỉ số an toàn cho vỉa hè và làn ảo ngược chiều (SUMO không mô phỏng xung đột ở đó).

---

## 8. Việc cần Viktor cung cấp (Claude Code KHÔNG tự điền)

- Đường dẫn thư mục OWZ trên máy.
- `site.yaml`: bề rộng làn thực đo; nhánh nào cấm rẽ trái/quay đầu; nhánh có người rẽ trái trái phép; chu kỳ và các pha đèn (gồm vàng, all-red); loại phân cách làn rẽ phải; bề rộng vỉa hè; chiều dài đoạn dải phân cách cứng; 1–2 nhánh dùng để đo nhóm F2.
- Quyết định sau Phase 3: làm hay hoãn đi ngược chiều (3C); hướng (a)/(b) cho chờ giữa nút (3D).
- Danh sách phương án tổ chức giao thông cần đánh giá (Phase 7).
- Endpoint LLM local (Ollama hay vLLM, tên model, GPU).
- Dữ liệu quan sát theo schema Phase 5.1 (sau khi xử lý video).

## 9. Thứ tự và điểm dừng

`Phase 0 → 1 → 2 → 3 (DỪNG: quyết 3C, 3D) → 4 → 5 → (DỪNG: chờ dữ liệu thực hoặc chạy tiếp với SYNTHETIC) → 6 → 7`

Sau mỗi phase báo cáo: đã làm gì, lệnh để tái tạo, tiêu chí đạt/chưa đạt, các giả định đã dùng, các mục `TODO_MEASURE` còn lại.
