# Bàn giao 28/10/2026: thay đổi trong ngày, tác động, và cách làm tiếp

File này để phiên sau đọc đầu tiên. Chi tiết vòng 1 nằm ở `README.md` cùng thư mục (mục 0 đến 7). Nhật ký điều phối nằm ở `PROGRESS.md`. Nếu hai file lệch nhau, file này đúng hơn vì nó viết sau.

Mọi dữ liệu quan sát là LITERATURE_PROXY, mỗi ngày 1 seed, nên các số dưới đây là chỉ báo, chưa phải kết quả benchmark. Các spec P1/P2 do Claude Sonnet làm stand-in (`provenance.model = "claude-sonnet (stand-in)"`), không phải kết quả của LLM cục bộ.

## 1. Trạng thái nhanh

| Hạng mục | Trạng thái |
|---|---|
| Vòng 1 (mạng có cọc), id `_n28` | Xong và đã commit (`cc6df0fc`). B2/P1/P2 mỗi bên 24 run, có video và README |
| Thay đổi làn 0 mở (vòng 2) | Code, mạng, test xong và đã commit (`f0727aeb`). pytest 384 passed, 2 xfailed |
| Vòng 2: B0 trên mạng mới (`REF_n28b`) | Xong (số ở mục 4) |
| Vòng 2: B1 (`REF_n28b`) | Đang chạy nền lúc viết file này; kiểm tra `experiments/campaigns/REF_n28b/B1_manual.pkl` |
| Vòng 2: B2/P1/P2 `_n28b` | Chưa chạy |
| Vòng 2: video và report | Chưa làm |

## 2. Hai việc đã đổi trong ngày

### 2.1 Vòng 1: kịch bản 28/10 trên mạng mới (đã có từ trước, tóm tắt)

- Tín hiệu 3 pha: LVL đi thẳng, LVL mũi tên trái (hai nhánh LVL cùng lúc), rồi HDT_N/HDT_S.
- Rẽ trái từ HDT_N và HDT_S bị cấm; xe vi phạm đứng chờ trong hộp nút (illegal-left box). LVL_W và LVL_E rẽ trái hợp lệ.
- Hai bản vá mạng: D2 (vehicle-width 3,5 m ở lượt netconvert cuối cộng `box_pins.con.xml` ghim `contPos` các internal junction còn lại) và D3 (`<prohibition>` ở cửa ra vỉa hè). Cả hai là lựa chọn mô hình hoá, chưa được Viktor duyệt (README mục 7, điểm 2).
- Proxy generator, metrics, rule runtime, prompt LLM v002 và Optuna được sửa theo; PROXY_D1 đến D5 và demand sinh lại.
- Kết quả: không spec nào đủ điều kiện (0/24). Spec tốt nhất theo R32 là `P2_n28_it02_s02` (S 0,9006, va chạm 58,67/giờ, cao hơn B0 34,67/giờ).

### 2.2 Vòng 2: làn rẽ phải liên tục (làn 0) cho đi thẳng khi đèn xanh (yêu cầu của Viktor, chiều 28/10)

**Yêu cầu gốc:** "làn rẽ phải liên tục thì không cần chờ đèn đỏ, có thể liên tục rẽ phải, khi đèn xanh thì đi vào làn rẽ phải để đi thẳng là đúng luật". Viktor chọn: cho đi thẳng khi xanh, bỏ cọc phân cách, chạy lại cả chiến dịch và video. Viktor cũng yêu cầu làm màu vàng của làn 0 trong sumo-gui nhẹ hơn.

**Trước và sau**

| | Trước (vòng 1) | Sau (vòng 2) |
|---|---|---|
| Rẽ phải làn 0 | Luôn `g`, không chờ đèn | Giữ nguyên |
| Đi thẳng từ làn 0 | Cấm với mọi xe; chỉ custom1/custom2 đi được khi tắc, qua lựa chọn `right_lane` của luật `queue_space_seeking` | Mở cho mọi xe, theo đèn đi thẳng của nhánh |
| Cọc phân cách 30 m cuối | Có, chặn đổi làn giữa làn 0 và làn 1 | Bỏ (`right_lane_separator: open`, `bollard_length_m: null` trong `config/site.proxy.yaml`) |
| `lane_movements` làn 0 | `[r]` | `[r, s]` |
| Lựa chọn `right_lane` của luật TraCI | Có | Không còn tồn tại trên mạng này |
| Màu tô làn 0 (sumo-gui, chỉ hiển thị) | Vàng đậm | `255,243,176,128` (#FFF3B0, alpha 0,5), layer 10, cả bốn nhánh. Chưa xem bằng mắt |

**Điều khác biệt về ngữ nghĩa:** xe đi thẳng đứng chờ ở làn 0 khi đèn đỏ (chặn xe rẽ phải, hành vi 6) vẫn là vi phạm, nhưng nay nó phát sinh từ cách SUMO tự chọn làn cộng hàng đợi, không còn do luật TraCI. Vì vậy `sim/outputs.py` chỉ ghi sự kiện `right_lane` và `blocked` cho xe đi thẳng đang dừng (dưới 5 km/h) ở làn 0; xe đi xuyên làn 0 khi xanh không bị đếm.

**Quyết định kỹ thuật agent tự chọn (cần Viktor xem lại):**

1. Đi thẳng làn 0 cạnh vỉa hè (LVL_W, LVL_E) là `g`, không phải `G`. Lý do: đi thẳng làn 0 và đi thẳng từ vỉa hè đổ vào cùng một làn ra; để `G` cả hai thì SUMO cảnh báo "Unsafe green" và `test_validator` hỏng. HDT vẫn `G`.
2. `B1_manual` bỏ `car_seeker` khỏi `queue_space_seeking` (`rules/specs/B1_manual.json` và `rules/compiled/B1_manual/traci_rules.json`). Không còn cọc thì custom2 không còn lựa chọn nào, validator (R27) loại mọi trial có p > 0 và 5 test của `test_optuna` hỏng. Hành vi B1 không đổi vì mọi p đều bằng 0. **Cấu trúc B1 do Viktor cố định ngày 27/10, nên đây là thay đổi cần duyệt.**
3. Không sửa `data/proxy/targets.yaml` và không sinh lại PROXY_D1 đến D5: CSV giống hệt từng byte, chỉ `site_sha256` trong `manifest.json` đổi.
4. `config/site.yaml` (file chính) cũng đổi `right_lane_separator` sang `open` vì `test_config` so khớp hai file; `bollard_length_m` ở đó vẫn là `TODO_MEASURE`.
5. Nhánh có vỉa hè: đoạn `<edge>.mid` biến mất, nay là `<edge>.up` rồi `<edge>`. Routes phải sinh lại vì lý do này.

## 3. Tác động đã biết

- **Va chạm và teleport:** B0 trên mạng mới có va chạm 38,67/giờ, teleport kẹt+nhường 7,33/giờ. Toàn bộ teleport nằm ở D1 seed 1 (11 lần, t khoảng 945 đến 1290 s): một xe máy đi thẳng và hai moto_violator cùng vào nút từ làn 2 HDT_S, chặn nhau ở ô chờ suốt khoảng 300 s, kéo theo cả ba làn LVL_W đứng. Đây là kiểu kẹt ô chờ HDT đã ghi ở D2, không phải link làn 0, nhưng làn 0 mở làm xe rẽ phải chịu ảnh hưởng. D1 seed 2 và 3 không kẹt. Chưa có số tương ứng trên mạng cũ để so tần suất.
- **M9 lệch rất xa chỉ tiêu:** M9a 12,0 so với 0,57 xe/chu kỳ; tỷ lệ rẽ phải bị chặn 0,63 so với 0,065. Hai chỉ tiêu `right_lane_choice_prob` và `lane0_hold_s` trong `targets.yaml` được suy từ giả định có cọc ("merge back before the bollards"). Chúng cần nguồn hoặc định nghĩa mới trước khi đọc điểm M9 của vòng 2 như dấu hiệu mô phỏng sai.
- **Rẽ phải làn 0:** vẫn đi khi đèn thẳng đỏ (5 đến 30 xe mỗi nhánh mỗi run). Nhưng nay bị xe đi thẳng đứng chờ phía trước chặn, thời gian dừng lớn nhất khoảng 56 đến 72 s (xấp xỉ một pha đỏ).
- **LVL_W làn 0 đói lượt:** D2/D3 tối đa 60 đến 65 s (vòng 1 là 178 s); D1 seed 1 là 407 s do vụ kẹt ở trên.
- **Xe đi thẳng qua làn 0:** 158 đến 243 xe mỗi nhánh mỗi run.
- **Vỉa hè:** B0 không có ai đi vỉa hè, nên chưa thử spec có `p_sidewalk` lớn hơn 0 trên mạng mới.
- **LLM:** prompt v002 (`llm/prompts/v002/context.md`) và `llm/feedback.py` đã nói rõ không còn cọc và `p_right_lane` không tồn tại. P2 nếu tạo seeker custom2 sẽ bị validator báo "inapplicable".

## 4. Số liệu vòng 2 hiện có (B0 trên PROXY_D1 đến D3, 1 seed, `REF_n28b`)

| | Vòng 1 (`REF_n28`, có cọc) | Vòng 2 (`REF_n28b`, làn 0 mở) |
|---|---|---|
| Va chạm/giờ | 34,67 | 38,67 |
| Va chạm trong làn/giờ | 2,67 | 1,33 |
| Teleport kẹt+nhường/giờ | 0 | 7,33 |
| S | 1,1235 | 1,2116 |

Số vòng 2 khớp giữa lần agent chạy thử trong `/tmp` và lần chạy chính thức trong `REF_n28b`. Số B1 vòng 2 chưa có.

Nhắc lại: B0 và B1 của vòng 1 có số ở `data/REF_B0_B1.txt`; so sánh vòng 1 với mạng cũ ngày 27/10 chịu thêm chênh lệch demand và site, không quy hết cho patch mạng.

## 5. Cách làm tiếp (đúng thứ tự)

Chạy từ `SUMO/`, dùng `.venv/bin/python`. Không quá 3 subagent cùng lúc và tổng process mô phỏng không quá số lõi trừ 1 (máy 12 lõi).

1. **Chờ `REF_n28b` xong B1.** Dấu hiệu: có `experiments/campaigns/REF_n28b/B1_manual.pkl` và `experiments/campaigns/REF_n28b_run.log` in cả hai dòng B0 và B1. Nếu process (`eval_ref_n28b.py`) đã chết giữa chừng, chạy lại `.venv/bin/python experiments/operator/ref/eval_ref_n28b.py`.
2. **Ngưỡng B0 cho các chiến dịch:** `b0_lane_collisions` = va chạm trong làn của B0 trên mạng mới = **1,3333**/giờ (3 ngày, seed 1). Tính lại bằng `b0_lane_collisions_per_hour(runs_dir=REF_n28b/runs)` nếu muốn kiểm.
3. **Duyệt hai việc trước khi tốn giờ chạy:** B1 bỏ `car_seeker`, và việc để nguyên `targets.yaml` (mục 2.2 và 3). Nếu Viktor đổi ý, kết quả B0/B1 ở mục 4 phải chạy lại.
4. **Chạy ba chiến dịch với id `_n28b`:**
   - B2: `.venv/bin/python -m thesis_sumo.baselines.optuna_search --structure rules/specs/B1_manual.json --campaign B2_n28b --budget 24 --nproc 3 --site config/site.proxy.yaml --b0-lane-collisions 1.3333 --write-best rules/specs/B2_n28b_best.json`
   - P1 và P2: `B0=1.3333 setsid nohup bash experiments/campaigns/supervise_llm_n28b.sh > experiments/campaigns/supervise_n28b.log 2>&1 < /dev/null &`. Script này (đã có, bản sao của `supervise_llm_n28.sh` với id `_n28b`) tự chạy lại loop khi đủ response; vẫn cần stand-in Sonnet trả lời các request: `.venv/bin/python -m thesis_sumo.llm.loop pending --campaign P1_n28b` liệt kê request chưa có response (mỗi iteration 4 spec; lấy cách giao việc cho subagent từ `PROGRESS.md` vòng 1, mục "Stand-in").
5. **Chọn spec tốt nhất theo R32/R42** (R42 giữ nguyên: spec bị loại vì quá tải thì chọn theo ít teleport kẹt/nhường, rồi S), ghi `rules/specs/{B2,P1,P2}_n28b_best.json`.
6. **Quay video** với spec tốt nhất: lệnh nằm trong `PROGRESS.md` (bước 6c vòng 1); đổi `--spec-json` sang `P2_n28b_best.json` (hoặc spec tốt nhất vòng 2) và tên file video. Lần này nên xem lại bằng mắt màu #FFF3B0 của làn 0.
7. **Viết report vòng 2** vào `report/2026-10-28/v2/` (vòng 1 giữ nguyên để so sánh): đặt cạnh số vòng 1, nêu rõ M9 lệch chỉ tiêu do `targets.yaml` suy từ giả định có cọc.

## 6. Việc chưa làm và câu hỏi cần Viktor quyết

Từ vòng 1 (README mục 6 và 7), vẫn còn nguyên: đo sức chứa box HDT; đóng băng lại trần R28 trên mạng mới (đang lấy từ mạng cũ: làn 4, nút 142 mỗi giờ); thêm seed; thêm đầu ra backlog theo nhánh; mũi tên trái LVL chưa chấm ở M1 đến M3; patch D2/D3 chưa duyệt.

Mới ở vòng 2, cần Viktor quyết:

1. Duyệt B1 bỏ `car_seeker`.
2. Cần nguồn hoặc định nghĩa mới cho hai chỉ tiêu M9 (`right_lane_choice_prob`, `lane0_hold_s`) trong `targets.yaml` trước khi đọc điểm M9. Sửa `targets.yaml` thì phải sinh lại manifest.
3. Chấp nhận kiểu kẹt ô chờ HDT_S ở D1 seed 1 (teleport tính vào R32), hay xử lý ở mạng?
4. Đi thẳng làn 0 cạnh vỉa hè là `g` (nhường vỉa hè); có chấp nhận không?
5. Có cần mô phỏng xe đi vào làn 0 khi đèn đỏ như một vi phạm riêng (hiện chỉ đo qua xe dừng ở làn 0), hay giữ như hiện tại?

## 7. Lưu ý vận hành

- Skill `writing-docs-viktor` mà `CLAUDE.md` yêu cầu không có trên máy này; file này theo văn phong report 27/10 và tự kiểm: số khớp nguồn (`REF_n28b_run.log`, báo cáo agent lane 0, `REF_B0_B1.txt`), tách dữ kiện, giả định, khuyến nghị.
- Các thư mục khung video `report/2026-10-27/_rec/` và `report/2026-10-28/_rec/` (khoảng 1,2 GB PNG) và `SUMO/experiments/campaigns/B2_aborted/` không commit (theo cách commit 27/10).
- Stand-in LLM: request nằm ở `SUMO/experiments/llm_logs/<campaign>/requests/<tên>.json`, response phải ghi vào `.../responses/<cùng tên>.json` (loop coi request là đang chờ khi chưa có file response cùng tên).
- Không sửa LaTeX và không chạy campaign H hay Task 15 trong ngày.
