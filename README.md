# thesis-sumo

Dùng LLM sinh luật hành vi tài xế cho SUMO, để mô phỏng giao thông hỗn hợp ô tô và xe máy tại nút giao Lê Văn Lương x
Hoàng Đạo Thúy (Hà Nội), giờ cao điểm sáng. Phạm vi và các phase nằm trong `PLAN.md`, quy tắc làm việc trong
`CLAUDE.md`, quy trình đầy đủ kèm sơ đồ trong `SUMO/docs/WORKFLOW.md`.

Mọi lệnh bên dưới chạy trong thư mục `SUMO/`. Trên Linux thay `.venv/Scripts/python` bằng `.venv/bin/python`.

# Phần 1. Kiểm tra và cài đặt môi trường

Làm một lần cho mỗi máy. Phần này chưa chạy mô phỏng.

## Bước 1. Kiểm tra máy đã có gì

Mở PowerShell và chạy từng lệnh:

```powershell
py -3.12 --version        # cần: Python 3.12.x
git --version             # cần: có hiện số phiên bản
git lfs version           # cần: có hiện số phiên bản
echo $env:SUMO_HOME       # cần: một đường dẫn, ví dụ C:\Program Files (x86)\Eclipse\Sumo\
& "$env:SUMO_HOME\bin\sumo.exe" --version     # cần: Eclipse SUMO sumo v1.27.0
```

Lệnh nào báo lỗi hoặc trống thì cài mục tương ứng ở Bước 2. Lệnh nào đạt thì bỏ qua mục đó.

## Bước 2. Cài những gì còn thiếu

| Thiếu | Cách cài |
|---|---|
| Python 3.12 | Tải bản cài đặt từ python.org, tick "Install launcher for all users" |
| Git | Tải từ git-scm.com |
| Git LFS | Tải từ git-lfs.com, rồi chạy `git lfs install` một lần |
| SUMO 1.27.0 | Tải bản Windows từ sumo.dlr.de, đúng phiên bản 1.27.0 |
| `SUMO_HOME` trống | Tìm "Edit the system environment variables", thêm biến `SUMO_HOME` trỏ tới thư mục cài SUMO. Sau đó mở terminal mới |

Trên Linux không cần cài SUMO: Bước 5 tự cài gói `eclipse-sumo==1.27.0` vào `.venv`.

## Bước 3. Lấy code

```bash
git clone <địa chỉ repo>
cd <thư mục repo>/SUMO
```

## Bước 4. Tải các tệp lớn

```bash
git lfs pull
```

Bỏ bước này thì thiếu các tệp `.gz` và hình ảnh.

## Bước 5. Tạo `.venv`

```powershell
py -3.12 scripts/setup_env.py        # Windows
python3.12 scripts/setup_env.py      # Linux
```

Phải đứng trong thư mục `SUMO/`. Script chạy vài phút và tạo `SUMO/.venv`. Không cần "activate" `.venv`, các lệnh
sau gọi thẳng `.venv/Scripts/python`.

Không tự chạy `pip install libsumo`. Nếu môi trường hỏng, xóa thư mục `.venv` rồi chạy lại Bước 5.

## Bước 6. Kiểm tra môi trường đã cài đúng

```bash
.venv/Scripts/python -m pytest -q
```

Kết quả mong đợi: khoảng 367 passed, 3 xfailed. Có test lỗi thì sửa xong mới sang Phần 2.

# Phần 2. Chạy demo

Giả định Phần 1 đã xong. Làm lần lượt từ Bước 1.

## Bước 1. Mở terminal tại thư mục `SUMO/`

```powershell
cd D:\hust-master\Thesis\SUMO
```

## Bước 2. Chọn bộ luật (spec) muốn xem

| Spec | Là gì |
|---|---|
| `B0` | SUMO mặc định. Xe tuân thủ đèn và làn, không có hành vi vi phạm |
| `B1_manual` | Luật viết tay, chuyển từ bài báo Saval et al. (2023). Có vượt đèn đỏ, xuất phát sớm, chặn làn rẽ phải, đi vỉa hè |
| `B2_best` | Luật cấu trúc như B1, các con số do Optuna chỉnh |

Nên bắt đầu bằng `B1_manual`, vì xem được hành vi vi phạm.

## Bước 3. Biên dịch spec

Chỉ cần với `B2_best`. `B0` và `B1_manual` đã biên dịch sẵn trong `rules/compiled/`, có thể bỏ qua bước này.

```bash
.venv/Scripts/python -m thesis_sumo.rules.compiler rules/specs/B2_best.json --site config/site.proxy.yaml
```

Thành công khi lệnh in ra dòng `wrote ... vtypes.add.xml and ... traci_rules.json`.

## Bước 4. Chạy mô phỏng có cửa sổ sumo-gui

```bash
.venv/Scripts/python -m thesis_sumo.sim.runner --spec B1_manual --day PROXY_D1 --seeds 1 --site config/site.proxy.yaml --end 600 --gui --ssm off
```

Giải thích các tham số:

| Tham số | Ý nghĩa |
|---|---|
| `--spec B1_manual` | bộ luật ở Bước 2 |
| `--day PROXY_D1` | ngày nhu cầu giao thông (D1 đến D5) |
| `--seeds 1` | một lần chạy với seed 1 |
| `--end 600` | dừng sau 600 giây mô phỏng |
| `--gui` | mở cửa sổ sumo-gui |

## Bước 5. Điều khiển trong cửa sổ sumo-gui

1. Bấm nút Play (hoặc Ctrl+A).
2. Ô Delay ở thanh trên: đặt 50 đến 100 ms để xem kịp.
3. Zoom vào giữa nút giao: Ctrl + lăn chuột.
4. Đổi "standard" thành "real world" ở danh sách Scheme để thấy rõ xe máy và ô tô.
5. Muốn biết một xe thuộc kiểu nào: chuột phải vào xe, chọn Show Parameter, đọc `type`
   (`moto_violator_saval` là xe máy rẽ trái trái phép, `moto_seeker` là xe máy có thể lên vỉa hè hoặc chặn làn rẽ phải).

## Bước 6. Chạy không cửa sổ để lấy số liệu

```bash
.venv/Scripts/python -m thesis_sumo.sim.runner --spec B1_manual --day PROXY_D1 --seeds 1 2 3 --site config/site.proxy.yaml --nproc 3 --ssm off
```

Kết quả nằm ở `experiments/runs/B1_manual__PROXY_D1/seed_01/` (và `seed_02`, `seed_03`). Mỗi thư mục gồm:

| Tệp | Nội dung |
|---|---|
| `manifest.json` | số va chạm, số xe bị teleport, số xe tồn đọng cuối run |
| `observed_schema/*.csv` | 10 bảng số liệu cùng định dạng với dữ liệu quan sát |
| `sumo.log` | log của SUMO |

Mặc định mỗi seed chạy 1800 giây và mất vài phút. Chạy lại cùng spec và ngày sẽ ghi đè thư mục cũ.

## Bước 7. Mở lại một lần chạy cũ (chỉ với B0)

```powershell
& "$env:SUMO_HOME\bin\sumo-gui.exe" -c experiments/runs/B0__PROXY_D1/seed_01/run.sumocfg
```

Không dùng cách này với `B1_manual` và `B2_best`: các hành vi vi phạm chỉ xảy ra khi chạy qua `thesis_sumo.sim.runner`.

## Lưu ý

Dữ liệu `PROXY_D1` đến `PROXY_D5` là dữ liệu proxy sinh từ tài liệu, không đo tại nút giao. Các spec P1 và P2 do Claude
Sonnet thay cho LLM chạy cục bộ.

Lỗi đã biết (kiểm tra ngày 2026-10-28): Bước 4 hiện dừng ở giây 0,4 với thông báo
`Vehicle 'moto_0_0' has no valid route. No connection between edge '37876499#0.up' and edge '37876499#0'`.
Commit `update 28/10` đã dựng lại mạng đường `scenario/net/site.proxy.net.xml`, trong đó cạnh `37876499#0.up` nối sang
`37876499#0.sidewalk` và `37876499#0.mid`. Các tệp `scenario/demand/routes_PROXY_D*.rou.xml` vẫn đi tuyến
`37876499#0.up 37876499#0`. Phải sinh lại demand bằng `thesis_sumo.demand.build_demand` thì demo mới chạy được trên
commit này.

# Trạng thái

- [x] Phase 0: môi trường và khung repo
- [ ] Phase 1: network
- [ ] Phase 2: baseline B0
- [ ] Phase 3: thí nghiệm chờ giữa nút (điểm dừng: chọn a/b)
- [ ] Phase 4: rule spec, validator, compiler, runtime TraCI
- [ ] Phase 5: metric và hàm khoảng cách
- [ ] Phase 6: vòng LLM
- [ ] Phase 7: baseline Optuna và benchmark
