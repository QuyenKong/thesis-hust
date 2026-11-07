# Báo cáo 08/11/2026: chốt thay đổi ngày 04/11, B0/B1 tham chiếu trên mạng 04/11

Repo `D:\hust-master\Thesis`, branch `master`, máy Windows, SUMO 1.27.0. Mọi số liệu quan sát là proxy (`LITERATURE_PROXY`), không phải số đo tại nút Lê Văn Lương × Hoàng Đạo Thúy. Không chạy campaign B2/P1/P2.

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

## 3. Còn lại

- Luật TraCI cho rẽ trái từ làn 0 và quay đầu từ làn 0, 1 của xe vi phạm (PLAN 1.4).
- qwen3.5:9b chưa ra spec hợp lệ ổn định: prompt `v003` cho 0/3 chuỗi hợp lệ trong 3 lần thử (04/11). Campaign P1/P2 với qwen chưa chạy.
- Campaign B2/P1/P2 trên mạng 04/11 chưa chạy. Kết quả campaign trên mạng 28/10 không so sánh được với bảng trên.
