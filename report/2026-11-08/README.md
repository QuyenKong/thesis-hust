# Báo cáo 08/11/2026: thay đổi ngày 04/11, luật cắt về, prompt v004, campaign B2/P1/P2 trên mạng 04/11

Repo `D:\hust-master\Thesis`, branch `master`, máy Windows, SUMO 1.27.0. Mọi số liệu quan sát là proxy (`LITERATURE_PROXY`), không phải số đo tại nút Lê Văn Lương × Hoàng Đạo Thúy. P1 và P2 dùng qwen3.5:9b chạy cục bộ qua Ollama.

## 1. Thay đổi được chốt (làm ngày 04/11, commit ngày 08/11)

- Mạng: bỏ các connection rẽ trái từ làn 0 và quay đầu từ làn 0, 1 chỉ cho `custom1`/`custom2` (thêm ngày 29/10). Rẽ trái và quay đầu chỉ còn từ làn 2. Hai hành vi này sẽ làm lại bằng luật TraCI (TODO trong PLAN 1.4, chưa làm).
- `swarm_red_running` (quyết định D1): xe đã rút "vượt đỏ" chỉ vào nút khi nút thông. Làn ra của link phải còn chỗ (length + minGap), không có xe trên làn nội bộ cắt link, và không có xe đứng trên làn nội bộ của chính link. Nút chưa thông thì xe đợi ở vạch. Đèn hết đỏ trước khi nút thông thì lượt đó ghi là không thực hiện (`junction_blocked`). Luật không có tham số mới.
- `uturn_bypass` (quyết định D2) vào cấu trúc cố định của B1 (`rules/specs/B1_manual.json`: xe máy `p` 0,8, ô tô `p` 0,1, `t_wait` 2 s, giá trị giả định) và vào prompt `v003` (hành vi 11).
- Client LLM: `max_tokens` 4500 trong `config/llm.yaml`. Câu trả lời bị cắt (`finish_reason` = length) tính là một lần thử hỏng. Tin nhắn retry của `v003` kèm trạng thái các phân phối vType của spec. Số đo qwen3.5:9b nằm ở `report/2026-11-03/data/ollama/measurements.md` và `report/2026-11-04/data/ollama/retry/`.
- Windows: `optuna_search.py` nạp `libsumo` trước `optuna` (tránh lỗi DLL `sqlite3.dll`), và journal Optuna khóa bằng `JournalFileOpenLock` vì tạo symlink cần quyền mà user Windows mặc định không có.

Kiểm tra:
- `site.proxy.net.xml` và 7 file patch trong `scenario/net/patches/site.proxy/` trùng với bản sinh lại bằng `python -m thesis_sumo.net.build --site config/site.proxy.yaml` (bỏ qua comment đầu file).
- Bộ test: 394 passed, 2 xfailed, 3 phút 52 giây (`import libsumo, pytest; pytest.main(...)`).

## 2. B0/B1 tham chiếu, `REF_n1104s5`

PROXY_D1–D3 × seed 1–5, 15 run mỗi spec, mỗi run 1800 s, `collision.check-junctions` bật. Lệnh, chạy từ `SUMO/`:

```
.venv/Scripts/python experiments/operator/ref/eval_ref_n1104_s5.py
```

| | B0 29/10 | B0 04/11 | B1 29/10 | B1 04/11 |
|---|---|---|---|---|
| Va chạm/h | 50,27 | 36,13 | 53,07 | 33,33 |
| Va chạm trong làn/h | 18,53 | 1,87 | 3,87 | 0,27 |
| Teleport kẹt/nhường/h | 1,60 | 0,00 | 51,73 | 4,67 |
| S | 1,2247 | 1,2174 | 1,2791 | 1,2494 |
| Run eligible | 0/15 | 15/15 | 0/15 | 0/15 |

Cột 29/10 là `REF_n29s5` (`report/2026-10-29/README.md`, mục 2).

B0 có 15/15 run eligible. Đây là lần đầu B0 qua hết các điều kiện hợp lệ trên mạng proxy. Ở 29/10, cả 15 run B0 đều bị loại vì va chạm trong làn (10–34/h mỗi run). Ở B0 chỉ có thay đổi mạng tác động, vì B0 không có luật TraCI.

B1 vẫn bị loại ở cả 15 run. Số run vi phạm từng điều kiện:

| Lý do loại | B1 29/10 | B1 04/11 |
|---|---|---|
| Xe còn chờ chèn vào mạng lúc kết thúc | 15 run (352–1089 xe) | 14 run (22–457 xe) |
| Va chạm có xe đang bị TraCI can thiệp > 1 | 10 run (2–7) | 14 run (2–6) |
| Teleport không do va chạm > 0 | 14 run (1–63) | 9 run (1–10) |
| Cổng GEH G0 | 15 run | 5 run (cả 5 run PROXY_D1) |
| Va chạm trong làn vượt trần | 5 run | 0 run |

Nút không còn khóa cứng như ngày 29/10: mỗi lần khóa khi đó sinh ra 20–40 teleport, giờ một run có nhiều nhất 10 teleport. Hàng chờ chèn xe vẫn còn, nhiều nhất ở PROXY_D1 (241–457 xe).

B1 có hai thay đổi cùng lúc (luật vượt đỏ chờ nút thông và `uturn_bypass`), nên bảng trên chưa tách được tác dụng riêng của từng luật.

Log can thiệp TraCI của B1, cộng 15 run:
- `swarm_red_running`: 3380 lượt rút ra vượt đỏ, trong đó 1946 lượt thực hiện, 2775 lượt tới vạch khi nút chưa thông nên phải đợi, và 1016 lượt bị hủy vì đèn hết đỏ trước khi nút thông (`junction_blocked`). Như vậy 30 % số lượt vượt đỏ đã rút không thành hành vi trong mô phỏng. Khi hiệu chỉnh `p0`, `k`, `p_max`, tỷ lệ vượt đỏ quan sát được (M3) sẽ thấp hơn tỷ lệ rút ra.
- `uturn_bypass`: 1927 lượt thử, 116 lượt lách qua được, 494 lượt không có khe ngang và không có làn kề, 1317 lượt không vượt qua được xe quay đầu.
- `early_start` và `queue_space_seeking` không can thiệp lần nào (B1 đặt `p` = 0).

## 3. Rẽ trái từ làn 0, quay đầu từ làn 0 và 1 bằng luật TraCI

Ngày 04/11 các connection riêng cho xe vi phạm bị bỏ khỏi mạng (mục 1). Hai hành vi này được làm lại bằng lựa chọn `wrong_lane` của `queue_space_seeking`, gọi là kiểu cắt về (cut-back). Mạng không đổi.

Cách làm:
- Khóa site mới `violator_turn_lanes: {l: [0], u: [0, 1]}` (quan sát của chủ đề tài ngày 29/10, `DECISIONS.md` V3 của report 29/10). Khóa này có ở `config/site.proxy.yaml` và `config/site.yaml`.
- Xe trong hàng chờ (`q`, `t_w` hoặc kiểm tra đèn sắp xanh, như các lựa chọn khác) rút `wrong_lane` với xác suất `p_wrong_lane`. Xe rẽ trái chuyển sang làn 0. Xe quay đầu chuyển sang làn 0 hoặc làn 1, chọn làn có hàng chờ ngắn hơn. Làn đó không có connection tới hướng của xe.
- Khi xe vào cạnh vạch dừng (30 m cuối), luật gửi `changeLane` về làn 2, với laneChangeMode bit 9–8 = 01 và `lcPushy` 1, như `uturn_bypass`. Hai giá trị này được trả lại khi xe qua vạch. Chưa nhập được làn 2 thì xe đứng ở cuối làn sai và chặn xe sau.
- Bỏ qua lựa chọn này cho hướng bị cấm (rẽ trái từ HDT_N, HDT_S) và cho xe đã ở trong 30 m cuối (`past_cut_point`).
- `uturn_bypass` nhận cả xe quay đầu đứng ở làn 0 hoặc 1 (làn không có link quay đầu) làm xe chặn.
- Validator (R27) và runtime dùng chung `runtime/wrong_lane.py`. Trên mạng proxy, `wrong_lane` giờ có cho cả 4 lớp xe. Riêng archetype trong `moto_violator` thì không lựa chọn nào áp dụng được, vì nó chỉ đi hướng rẽ trái bị cấm.
- Không thêm tham số. Prompt `v004` mô tả lại hành vi 5, và mô tả của `p_wrong_lane` trong từ điển tham số cũng được sửa.

Thí nghiệm trước khi viết luật (`exp_cut.py` trong scratch, PROXY_D1, B1 không có luật TraCI, 1200 s, 12 xe được ép đi làn sai). Nếu chỉ cho cắt về khi xe đã ở vạch và đèn của hướng mình xanh, thì đầu làn 2 đã kín. Xe phải đứng ở cuối làn sai từ 1,5 đến 8 phút, và một xe bị teleport. Vì vậy luật cho xe nhập lại ngay khi vào đoạn 30 m cuối. Tăng `lcMaxSpeedLatStanding` lên 3 m/s không làm thay đổi kết quả.

Test mới: `test_queue_space_seeking_cut_back` (mạng nhỏ: xe rẽ trái đi làn 0, cắt về làn 2, rẽ trái, laneChangeMode và `lcPushy` được trả lại), `test_queue_space_seeking_cut_back` của validator, và phần cut-back trong `test_junction_info_on_proxy_net`.

Chạy thử `B1_cut_back` (`rules/specs/B1_cut_back.json`): B1_manual, `queue_space_seeking` áp cho `moto_seeker` và `car_seeker` với `p_wrong_lane` 0,5. PROXY_D1–D3 × seed 1, campaign `AB_cut`, script `experiments/operator/ref/eval_cut_back.py`.
- 49 lượt rút `wrong_lane`. 15 lượt vào được làn sai rồi cắt về: 10 lượt quay đầu từ làn 1 (7 xe máy, 3 ô tô) và 5 lượt từ làn 0. 31 lượt không đổi được làn trong 5 s cho mỗi làn phải vượt (`lane_change_not_done`). 3 lượt rút khi xe đã ở 30 m cuối.
- Trong 15 xe cắt về, 14 xe đi hết hành trình. Một xe bị teleport vì chờ nhường quá lâu ở làn 2 (13 phút sau khi cắt về, do tắc chung). Một ô tô có va chạm ở làn 2, 40 s sau khi cắt về.
- Cả 3 run vẫn bị loại. Va chạm 37,3/h, va chạm trong làn 2,0/h, teleport kẹt/nhường 9,3/h, S 1,2636. Với seed 1 của B1 ở bảng mục 2, va chạm trung bình 42,7/h, va chạm trong làn 0/h, teleport kẹt/nhường 5,3/h. Ba run không đủ để nói luật làm tăng hay giảm các số này.

Giới hạn: xe cắt về vào nút từ làn 2, nên M8 (làn của xe tại vạch dừng, theo vị trí ngang) không ghi nhận nó là đi sai làn. M8 của `B1_cut_back` vẫn là 0 như B1, trong khi chỉ tiêu proxy là 0,249 với xe máy và 0,068 với ô tô. Muốn M8 phản ánh hành vi này thì xe phải vào nút từ làn 0 hoặc 1, tức là cần connection, đúng thứ đã bị bỏ ngày 04/11 vì gây va chạm. Việc chọn giữa hai cách cần chủ đề tài quyết.

## 4. qwen3.5:9b: prompt `v004`

Ngày 04/11, với prompt `v003`, qwen cho 0/3 chuỗi hợp lệ trong 3 lần thử. Có hai nguyên nhân chính:
- Lỗi tổng share: archetype không ghi `distribution` nên rơi vào phân phối mặc định của lớp xe, và hai archetype `custom1` cùng rơi vào `moto_violator`.
- Prompt quá dài: prompt vòng 2 khoảng 26 nghìn token. Prompt vòng 3 còn kèm phản hồi của cả vòng 1 và vòng 2, khoảng 46 nghìn token, vượt cửa sổ 32.768 token, nên với `v003` qwen không chạy hết được một campaign P2.

Thay đổi trong `v004` (`config/llm.yaml` `prompt_version: v004`; `v001` đến `v003` giữ nguyên để tái tạo các campaign cũ):
- Schema đầu ra ở chế độ full có một biến thể cho mỗi `base_vclass`. Mỗi biến thể chỉ có các tham số được đặt trên lớp xe đó (với cận của lớp đó), và chỉ cho các phân phối lớp đó được vào. `distribution` là bắt buộc. Ollama ép tên trường theo schema, nên qwen không đặt được `jmTimegapMinor` cho xe máy thường nữa. Cận số thì Ollama không ép: lượt A có một lần thử đặt giá trị mặc định của SUMO nằm ngoài cận.
- System prompt thêm ba câu: ghi `distribution` cho mọi archetype và cộng share từng phân phối trước khi trả lời, share phải lớn hơn 0, id không được trùng tên phân phối.
- Context: chỉ liệt kê 42 chỉ tiêu có tính điểm (bỏ 18 chỉ tiêu chỉ để báo cáo), và thay bản in đầy đủ của JSON schema bằng một khung mẫu ngắn.
- Phản hồi: gộp kết quả của các spec trong một vòng thành một bảng, mỗi metric một dòng gồm giá trị quan sát và, với mỗi spec, giá trị mô phỏng và R. Chỉ giữ metric có trọng số.
- Lịch sử: vòng gần nhất gửi đầy đủ (JSON của spec và bảng metric). Các vòng cũ hơn chỉ còn vài dòng tóm tắt (S, eligibility, archetype, luật) (`llm/loop.py` `_summary_message`).
- `llm.loop` có thêm tùy chọn `--llm ollama`, để máy Windows dùng qwen mà không phải sửa `active` trong `llm.yaml` (máy Linux vẫn dùng stand-in).

Kích thước prompt P2, dựng lại từ kết quả campaign `P2_n28b` (`experiments/operator/llm/prompt_size_v004.py`; số token ước theo tỷ lệ ký tự/token đo ngày 03/11):

| | `v002` | `v004` |
|---|---|---|
| Vòng 2 | 68.745 ký tự, ~25.200 token | 45.029 ký tự, ~16.500 token |
| Vòng 3 | 126.372 ký tự, ~46.300 token | 58.029 ký tự, ~21.300 token |

Đo trên máy Windows (RTX 4060 8 GB, Ollama, `OLLAMA_CONTEXT_LENGTH=32768`, thinking bật, `max_tokens` 4500). Request là prompt vòng 2 của P2 dựng bằng `v004`. Mỗi chuỗi tối đa 3 lần thử (`LLMClient.generate_spec`), seed 42, 43, 44. Lượt A có schema với `distribution` bắt buộc nhưng chưa tách theo lớp xe, và system prompt chưa có hai câu về share > 0 và id. Lượt B có đủ các thay đổi trên. Script ở `report/2026-11-08/data/ollama/scripts/` (`retry_chain_v004.py`, `retry_chain_v004b.py`), kết quả ở `retry_a/` và `retry_b/`.

| Lượt | Seed | Số lần thử tới khi hợp lệ | Thời gian chuỗi | Lỗi ở các lần thử hỏng |
|---|---|---|---|---|
| A | 42 | 3 | 667 s | bị cắt ở 4500 token; `jmTimegapMinor` trên xe máy (2 lỗi) và id `moto_violator` |
| A | 43 | 3 | 543 s | giá trị mặc định SUMO ngoài cận (`jmDriveAfterRedTime` -1, `jmDriveRedSpeed` 55,56); share = 0 |
| A | 44 | 3 | 473 s | share = 0; id `moto_violator` |
| B | 42 | 2 | 299 s | id `moto_violator` |
| B | 43 | 3 | 704 s | bị cắt ở 4500 token; tổng share `moto` 0,9 |
| B | 44 | 3 | 388 s | tổng share `moto` 1,1 và id `moto_violator`; `queue_space_seeking` trên xe máy thường |

Cả 6 chuỗi đều ra spec hợp lệ trong 3 lần thử (ngày 04/11 với `v003`: 0/3; ngày 03/11 với `v002`: 1/3). Prompt dài 15.919–19.678 token, câu trả lời 1.526–4.500 token, tốc độ sinh 12,5–13,5 token/s. Một lần thử mất 2–6 phút. Lỗi id `moto_violator` xuất hiện ở 4/6 chuỗi dù prompt đã cấm, nhưng lần thử sau đều sửa được. Sáu chuỗi chưa đủ để so lượt A với lượt B.

## 5. Campaign B2, P1, P2 trên mạng 04/11 (`*_n1108`)

Cấu hình chung: PROXY_D1–D3 × seed 1, ngân sách 36 run SUMO mỗi campaign (R44), mỗi run 1800 s. Trần va chạm trong làn khi chọn spec tốt nhất (R10) là 1,8667 + 1 va chạm/h, với 1,8667 là B0 của `REF_n1104s5`. Lệnh, chạy từ `SUMO/`:

```
bash experiments/operator/n1108/run_campaigns.sh b2   # cũng: p1, p2
```

B2 là Optuna với 3 tiến trình. P1 (`params_only`, nền `B1_manual`) và P2 (`full`) dùng qwen3.5:9b (`--llm ollama`), prompt `v004`, 4 mẫu mỗi vòng, tối đa 3 lần thử mỗi mẫu, `max_tokens` 7000, thinking tắt. B2 chạy song song với P1, P2 chạy sau P1.

Thinking tắt bằng `reasoning_effort: none` trong profile `ollama` của `config/llm.yaml` (commit 7706ede). Hai lần khởi động P1 đầu tiên đều hỏng ở lần thử đầu tiên của vòng 1: câu trả lời bị cắt ở 4500 token rồi ở 7000 token, trong đó phần thinking dài 18.554 và 28.585 ký tự, chưa kịp tới JSON. Hai thư mục campaign đó bị xóa trước khi có run nào được tính. Log của chúng nằm ở `data/ollama/p1_cap4500/` và `data/ollama/p1_cap7000_think/`. Với thinking tắt, chạy thử trên prompt vòng 1 cho 3/3 chuỗi P1 và 2/3 chuỗi P2 hợp lệ (`data/ollama/p1_nothink/`, `data/ollama/p2_nothink/`). Chế độ thinking là một phần cấu hình của campaign, nên được ghi vào `loop.json` (`llm.reasoning_effort`).

| | B2 | P1 | P2 |
|---|---|---|---|
| Thời gian | 3 h 25 (06:03–09:28) | khoảng 2 h 25 (đến 09:20) | 1 h 56 (09:20–11:16) |
| Trial hoặc vòng | 12 trial | 4 vòng (3 + 1 theo R45) | 5 vòng (3 + 2 theo R45) |
| Mẫu hợp lệ | 12/12 | 12/16 | 14/20, 2 mẫu hợp lệ nhưng hết ngân sách |
| Lần thử hợp lệ | không có LLM | 12/27 | 14/36 |
| Spec được chạy | 12 | 12 | 12 |
| Spec eligible | 0 | 0 | 0 |
| Run eligible D1 / D2 / D3 | 0/12, 0/12, 0/12 | 0/12, 0/12, 0/12 | 0/12, 6/12, 5/12 |
| S thấp nhất | 1,1438 (`t003`) | 1,2386 (`it01_s01`) | 1,1680 (`it04_s03`) |
| Spec chọn theo R42 | `t002`, S 1,2088 | `it01_s02`, S 1,2984 | `it03_s02`, S 1,1744 |

Giờ là giờ Hà Nội ngày 08/11. Không campaign nào có spec eligible, nên `select_best` xếp hạng theo R42: ít teleport kẹt/nhường nhất, rồi S, không xét trần va chạm. Ba file `rules/specs/{B2,P1,P2}_n1108_best.json` là spec ít tắc nhất theo nghĩa đó, không phải spec eligible. Các campaign chỉ dùng seed 1, nên S ở bảng trên không so trực tiếp được với S của B0 (1,2174) và B1 (1,2494) ở mục 2, vốn tính trên 5 seed.

Lý do bị loại:
- B2 và P1: còn xe chờ chèn vào mạng lúc kết thúc ở cả ba ngày. P1 có ở 36/36 run (PROXY_D1 301–623 xe, PROXY_D2 23–179, PROXY_D3 133–297). B2 có ở 21/36 run (PROXY_D1 20–338 xe ở cả 12 run). Gần như mọi spec đều có run với hơn 1 va chạm có xe đang bị TraCI can thiệp. B2 có thêm 9/12 trial vượt trần va chạm trong làn (4/h mỗi run) ở ít nhất một run. P1 không có run nào bị loại vì lý do này.
- P2: chỉ PROXY_D1 còn xe chờ chèn (4–163 xe, cả 12 spec). Ở PROXY_D2 và PROXY_D3, 11/24 run eligible. Các run còn lại bị loại vì va chạm trong làn vượt 4/h hoặc vì hơn 1 va chạm có xe đang bị TraCI can thiệp.

P1 giữ cấu trúc của B1, mà chính B1 đã có 14/15 run còn xe chờ chèn (mục 2). Vì vậy P1 không thể ra spec eligible, dù qwen chọn tham số thế nào.

Spec của P2 có cấu trúc khác B1. Từ vòng 2, cả 12 spec P2 được chạy có cùng cấu trúc với `it02_s01`. Cấu trúc đó có 5 archetype (`car_compliant`, `car_early_starter`, `moto_compliant`, `moto_slow_center` và `moto_violator_left` lớp `custom1`) và 3 luật (`early_start` cho ô tô, `swarm_red_running` cho xe máy thường, `illegal_left_box`). Các vòng sau chỉ đổi share và tham số. Cấu trúc này không có `queue_space_seeking`, không có `uturn_bypass` (chỉ `it01_s02` có), không có `slow_lane_center` dù có archetype tên `moto_slow_center`, và không có xe đi sai làn. Như vậy S thấp hơn của P2 đến từ spec bỏ bớt một số hành vi của PLAN §0. Ba campaign chưa tách được phần giảm xe chờ chèn của P2 là do tham số vType hay do bỏ các luật có thể chặn làn (cắt về, lách qua xe quay đầu).

## 6. qwen3.5:9b trong campaign

Prompt dài 9.471–24.441 token ở P1 và 7.063–19.895 token ở P2. Câu trả lời dài 1.257–2.256 token. Cả 63 câu trả lời đều kết thúc bình thường (`finish_reason` = stop), không câu nào bị cắt. Mỗi lần thử mất khoảng 1,5–3,5 phút.

P1: 14/15 lần thử hỏng là lỗi tổng share, và cả 14 lần đều sai ở phân phối `moto_violator`. Phân phối này chỉ có một archetype (`moto_violator_saval`), nên share của nó phải là 1, nhưng qwen đổi thành 0,9, 0,85, 0,5, 0,1 hoặc 0,05. Ở 2 lần thử của `it03_s03`, qwen chuyển 0,1 và 0,05 share từ `moto` sang `moto_violator`, nên cả hai phân phối đều sai. Có 4 mẫu (`it01_s03`, `it02_s00`, `it02_s02`, `it04_s00`) hỏng cả 3 lần thử vì lỗi này, dù tin nhắn retry đã nêu rõ tổng share. P1 còn lặp lại một spec: `it01_s02`, `it02_s03`, `it03_s01` và `it04_s02` giống nhau (`early_start` `p` 0,13, `p_sidewalk` 0,75, `p_wrong_lane` 0,25, phần còn lại như B1). Spec này là spec R42 chọn sau vòng 1, nên phản hồi giới thiệu nó là tốt nhất. Ba lần nộp lại tốn 9 run và cho cùng S 1,2984.

P2: ở vòng 1 và 2, 6/8 mẫu không hợp lệ sau 3 lần thử. Đếm theo lỗi trên mọi lần thử hỏng ở P2:

| Lỗi | Số lần |
|---|---|
| id archetype trùng tên phân phối (`car`, `moto`, `moto_violator`, `car_violator`) | 19 |
| tổng share của một phân phối khác 1 | 15 |
| phân phối mà demand dùng không có archetype nào | 7 |
| `queue_space_seeking` áp cho lớp xe không được phép | 6 |
| `queue_space_seeking` không áp dụng được trên site cho archetype trong `moto_violator` | 5 |
| `illegal_left_box` áp cho xe máy thường | 4 |
| giá trị ngoài cận (schema) | 4 |
| `early_start` áp hai lần cho cùng archetype | 1 |

Từ vòng 3, 11/12 mẫu hợp lệ ngay lần thử đầu. Từ vòng 2, lịch sử gửi cho qwen có JSON của một spec hợp lệ (`it02_s01`), và các spec vòng 3–5 giữ đúng cấu trúc đó. Các lỗi ở bảng trên đều là lỗi cấu trúc, và chúng không xuất hiện lại khi qwen giữ nguyên cấu trúc đã qua validator.

## 7. Việc còn lại

- PROXY_D1 còn xe chờ chèn ở mọi spec của cả ba campaign, và ở B1 (mục 2). Khi lỗi này còn, không spec nào eligible được. Trước khi chạy campaign tiếp cần kiểm tra demand của PROXY_D1 so với năng lực thông qua của mạng 04/11. Demand này là số liệu proxy, nên cách xử lý cần chủ đề tài quyết.
- M8 và luật cắt về (mục 3): chọn giữa connection cho xe vi phạm và luật cắt về, cần chủ đề tài quyết.
- Vòng LLM: spec trùng với một spec đã chạy (cùng hash) đang bị tính run lại. Có thể lấy lại kết quả cũ thay vì chạy lại.
- Ở chế độ `params_only`, schema có thể ép share bằng 1 cho phân phối chỉ có một archetype. Ở P1, 12/15 lần thử hỏng chỉ có lỗi ở phân phối đó.
- P2 bỏ `queue_space_seeking`, `uturn_bypass` và `slow_lane_center`. Muốn spec có đủ các hành vi của PLAN §0 thì phải đưa yêu cầu này vào validator hoặc vào điểm số. Việc này cần chủ đề tài quyết.
- Kết quả campaign chỉ có seed 1. Spec R42 chọn của B2 và P2 cần chạy lại với 5 seed, như `REF_n1104s5`, trước khi so với B0 và B1.
