# Thay đổi 28/10 (vòng 2): làn 0 (rẽ phải liên tục) cho đi thẳng khi đèn xanh

Đọc `briefs/common.md` trước (luật chung: không git, không bịa số đo, không đoán tên SUMO, scenario_raw bất biến, PROXY_D4/D5 không lộ ra LLM/Optuna).

## Yêu cầu của Viktor (nguyên văn, 28/10)
"làn rẽ phải liên tục thì không cần chờ đèn đỏ, có thể liên tục rẽ phải, khi đèn xanh thì đi vào làn rẽ phải để đi thẳng là đúng luật"
Viktor đã chọn: **cho đi thẳng khi xanh, BỎ cọc phân cách**.

## Ngữ nghĩa mới
- Rẽ phải từ làn 0: luôn tự do (không chờ đèn đỏ) — GIỮ NGUYÊN (link `g` mọi pha).
- Đi thẳng từ làn 0: HỢP LỆ cho mọi xe (kể cả ô tô tuân thủ), theo đèn ĐI THẲNG của nhánh (xanh thì đi, đỏ thì dừng). Không còn "chỉ custom1/custom2".
- Không còn cọc: xe đổi làn tự do giữa làn 0 và làn 1.
- Xe đi thẳng đứng chờ ở làn 0 khi đèn đỏ (chặn xe rẽ phải) vẫn là hành vi 6 (vi phạm) — nhưng nó nay do chọn làn tự nhiên của SUMO + hàng đợi, KHÔNG còn là lựa chọn `right_lane` của luật TraCI `queue_space_seeking` (lựa chọn đó chỉ tồn tại khi đi thẳng từ làn 0 bị cấm).
- `lane_movements` làn 0 của 4 nhánh: `[r, s]` (nhánh 'u'/'l' không đổi).

## Việc cần làm (làm gọn nhất, theo kiểu code xung quanh)
1. `SUMO/src/thesis_sumo/net/apply_patches.py`: thêm giá trị `right_lane_separator: open` (giữ none|paint|bollards nguyên nghĩa cho test cũ): straight connection của làn 0 re-add với quyền của làn (không phải disallow all, không phải chỉ violator); trạng thái TLS của link đó = trạng thái đi thẳng của nhánh (không phải UNCONTROLLED_STATE; chỉ link rẽ phải là `g`); không sinh `split.edg.xml`/`bollards.edg.xml` và không đặt changeLeft/changeRight emergency (bollard_length_m null/0 phải chạy được, kể cả nhánh có vỉa hè: `<edge>.up`, `.sidewalk` vẫn đúng); `write_gui_highlight` không tô vàng làn 0 khi không có cọc (hoặc tô khác — chọn đơn giản nhất, chỉ hiển thị). Sửa docstring đầu file. `_check_site_net`: các kiểm tra xung đột vỉa hè–làn 0 phải còn đúng (link đi thẳng từ làn 0 nay là link mới có thể nhường/xung đột với vỉa hè; không được tạo deadlock như D3 — kiểm chứng bằng chạy B0, 0 teleport kẹt/nhường bất thường).
2. `SUMO/config/site.proxy.yaml`: 4 nhánh `right_lane_separator: open` (source: "Viktor, 2026-10-28 (field): đi vào làn rẽ phải để đi thẳng khi đèn xanh là đúng luật; không còn cọc", evidence field_observation), `lane_movements` làn 0 = `[r, s]` (sửa `lane_movements_source`), bỏ/null `bollard_length_m` nếu code cho phép (nếu `config/site.yaml` chính có TODO_MEASURE thì không đụng; không đưa số bịa). Sửa comment đầu file cho khớp.
3. Rebuild mạng (script build_net, xem docs/WORKFLOW.md) -> `scenario/net/site.proxy.net.xml`, `diagram.svg`, `patches/site.proxy/*` (bỏ `bollards.edg.xml`/`split.edg.xml` nếu không còn dùng). Giữ nguyên các bản vá D2 (vehicle-width + box_pins) và D3 (prohibition vỉa hè).
4. Downstream: tìm mọi nơi giả định làn 0 chỉ rẽ phải / có cọc: `runtime/rules/queue_space_seeking.py` (`available()`: `right_lane` tự không còn vì `mv in marks[0]`; sửa docstring và mọi chỗ dùng bollard edge/merge_zone cho không crash khi không có cọc; `signalled` lanes nay gồm làn 0 straight), `rules/validator.py` + `rules/schema.py` (`p_right_lane`, `merge_zone_m`: spec đặt p_right_lane>0 trên mạng này phải được xử lý rõ ràng — đề xuất: không tồn tại lựa chọn nên bị dồn như PLAN 4.5, hoặc bị validator báo; chọn cách nhất quán với cách `sidewalk`/`wrong_lane` vắng mặt đang xử lý; KHÔNG đổi rules/specs/B0.json nếu không cần), `sim/outputs.py` (dòng ~663 M9 từ làn 0 straight), `metrics/m9_right_lane.py`, `metrics/f2_space_choice.py`, `metrics/common.py`, `proxy/generate.py` (dòng ~663), `llm/feedback.py` (dòng ~81), `llm/prompts/v002/*.md` (mô tả mạng cho LLM phải đúng: không còn cọc, không còn lựa chọn right_lane), `runtime/wrong_lane.py`/`state.py` nếu dùng lane_movements. Nguyên tắc: proxy data (PROXY_D1..D5) mô tả hành vi quan sát; chỉ sửa generator/targets khi chúng mâu thuẫn trực tiếp với mạng mới (ví dụ định nghĩa "cọc"), KHÔNG chỉnh số cho khớp kết quả sim. Nếu phải sinh lại proxy: dùng đúng công thức README của SYNTHETIC/proxy, seed cố định, ghi sha. Nếu không đổi gì ở proxy thì nói rõ.
5. Test: cập nhật/ thêm test nhỏ (net: link thẳng làn 0 mở cho mọi vclass và theo đèn thẳng; rẽ phải làn 0 vẫn `g`; không có split cọc). `.venv/bin/python -m pytest` toàn bộ: hiện 381 passed, 2 xfailed; mục tiêu: không test nào tụt, test nào phải sửa thì ghi lý do.
6. Kiểm tra thực: chạy B0 trên PROXY_D1..D3 (cách chạy: xem `SUMO/experiments/operator/ref/eval_ref_n28.py` và PROGRESS.md bước 4) — báo: va chạm/h, teleport, số xe thẳng đi qua làn 0 (từ output), xe rẽ phải làn 0 có bị chờ đèn đỏ không (phải không), `lane 0 starvation` LVL_W. Không chạy chiến dịch.
7. Cập nhật `SUMO/docs/WORKFLOW.md` (dòng 84 "Làn 0 ... không bị đèn điều khiển, có cọc ...") và docstring liên quan.

## Giới hạn
- Tối đa 3 subagent / 11 process sim cùng lúc. Không đụng `SUMO/experiments/campaigns/*_n28`, `rules/specs/*_n28_best.json`, `report/2026-10-28/README.md` (kết quả vòng 1 giữ để so sánh).
- Không git (chỉ git status/diff).
- Báo cáo cuối (ngắn, <60 dòng): file đã đổi, quyết định đã chọn và lý do, kết quả pytest, kết quả B0, phần chưa chắc.
