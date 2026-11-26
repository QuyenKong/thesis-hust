# Phiếu đếm tay từ video giờ cao điểm

Thư mục này chứa số liệu Viktor đếm tay từ hai video quay tại nút Lê Văn Lương x Hoàng Đạo Thúy, mỗi
video khoảng 5 phút trong giờ cao điểm sáng. Phiếu đã điền là dữ liệu hiện trường thật. Sau khi điền
xong, một script sẽ chuyển các phiếu này thành `config/site.yaml` và các bảng `data/observed/V1/`,
`data/observed/V2/` theo schema PLAN §5.1. Video không được commit (`*.mp4` nằm trong `.gitignore`).

## Cấu trúc

```
video_counts/
  site_survey.yaml      điền 1 lần cho cả nút: làn, vạch, vỉa hè, mốc khoảng cách
  V1/                   video 1
    00_video.yaml       thông tin video, camera thấy được nhánh nào
    01_signal.yaml      mốc đổi đèn
    02_turn_counts.yaml đếm xe theo hướng, theo phút
    03_queue_at_green.yaml  hàng chờ lúc đèn chuyển xanh
    04_red_crossings.yaml   xe qua vạch khi đèn đỏ, xe đầu tiên sau xanh
    05_illegal_left_box.yaml  rẽ trái trái phép chờ giữa nút
    06_space_seeking.yaml   chen làn rẽ phải, leo vỉa hè, đi sai làn để vượt hàng
    07_wrong_lane.yaml      xe rẽ đứng sai làn ở mốc 30 m
    08_discharge.yaml       (tùy chọn) số xe qua vạch theo 2 s sau khi xanh
    09_travel_time.yaml     (tùy chọn) thời gian đi qua nút, tốc độ
  V2/                   video 2, cùng các tệp
```

## Quy ước chung

- Thời gian ghi theo đồng hồ của trình phát video, dạng `"mm:ss"` hoặc `"mm:ss.s"`, có dấu nháy kép.
  Giờ thực ở giây `00:00` ghi một lần trong `00_video.yaml`.
- Ô chưa đếm để `null`. Ô đã xem mà không có xe nào thì ghi `0`. Hai giá trị này khác nhau: `null` là
  chưa có số liệu, `0` là đã quan sát và không thấy.
- Không thấy được (camera không bao quát, bị che) thì để `null` và ghi lý do vào `notes`. Không ước
  đoán cho đủ ô.
- Làn đánh số từ phải sang trái theo hướng xe chạy: làn 0 là làn ngoài cùng bên phải.
- `vclass`: `car` (ô tô con, taxi, xe bán tải) hoặc `moto` (xe máy, xe đạp điện). Xe buýt và xe tải
  nằm ngoài phạm vi: không đếm, nhưng nếu nhiều thì ghi tổng vào `notes`.
- Mã hướng: `s` đi thẳng, `r` rẽ phải, `l` rẽ trái được phép, `u` quay đầu, `illegal_l` rẽ trái ở
  nhánh cấm rẽ trái (HDT_N, HDT_S).

Tên nhánh theo `config/site.yaml`:

| Mã | Đường | Xe đi vào nút từ phía |
|---|---|---|
| `LVL_W` | Lê Văn Lương | Tố Hữu (tây nam) |
| `LVL_E` | Lê Văn Lương | Láng Hạ (đông bắc) |
| `HDT_N` | Hoàng Đạo Thúy | Hoàng Minh Giám (tây bắc), cấm rẽ trái |
| `HDT_S` | Hoàng Đạo Thúy | Nguyễn Tuân (đông nam), cấm rẽ trái |

## Thứ tự đếm và khối lượng

Mỗi lượt chỉ theo dõi một việc. Một video 5 phút xem ở tốc độ 0,5x mất khoảng 10 phút một lượt. Đếm
lưu lượng có nhiều xe máy thì nên dùng ứng dụng bấm đếm (tally counter) trên điện thoại, mỗi hướng một
nút.

| Thứ tự | Tệp | Số lượt xem mỗi video | Metric dùng |
|---|---|---|---|
| 0 | `site_survey.yaml` | đo trên Google Earth và một lần xem video | hình học mạng |
| 1 | `00_video.yaml`, `01_signal.yaml` | 1 | chu kỳ, pha đèn; M2 (xuất phát sớm), M3 (vượt đèn đỏ) |
| 2 | `02_turn_counts.yaml` | 2 mỗi nhánh thấy được (ô tô, rồi xe máy) | dựng demand, cổng G0 (GEH lưu lượng) |
| 3 | `03_queue_at_green.yaml` | 1, dừng hình ở mỗi lần chuyển xanh | M4 (xe máy dừng vượt vạch), M5 (hàng chờ), M9 (chặn làn rẽ phải), M10 (vỉa hè) |
| 4 | `04_red_crossings.yaml` | 1 mỗi nhóm đèn | M2, M3 |
| 5 | `05_illegal_left_box.yaml` | 1 | M7 (rẽ trái trái phép chờ giữa nút) |
| 6 | `06_space_seeking.yaml` | 1 cho nhánh F2 | M9, M10, xác suất chọn khoảng trống theo hàng chờ |
| 7 | `07_wrong_lane.yaml` | 1 mỗi nhánh thấy mốc 30 m | M8 (đi sai làn) |
| 8 | `08_discharge.yaml` | tùy chọn, xem từng khung hình | M1 (giãn cách xả hàng) |
| 9 | `09_travel_time.yaml` | tùy chọn, mẫu 5 đến 10 xe mỗi hướng | M6 (thời gian và tốc độ qua nút) |

Việc 0 đến 2 là bắt buộc: thiếu chúng thì mô phỏng không chạy được trên số liệu thật. Việc 3 đến 7
cho các metric hành vi. Việc 8 và 9 làm nếu còn thời gian, vì đếm tay xe máy xả hàng với giãn cách
dưới 0,5 s rất dễ sai.

## Giới hạn của 2 x 5 phút

- 5 phút chứa khoảng 2 đến 3 chu kỳ đèn, nên mỗi video chỉ cho 2 đến 3 lần quan sát mỗi nhánh cho các
  metric theo chu kỳ (M3, M5, M7). Phân phối dựng từ ít điểm như vậy rất rộng, và luận văn phải ghi rõ
  số chu kỳ đã quan sát.
- Lưu lượng 5 phút được quy ra xe/giờ (nhân 12) và giả định không đổi trong cửa sổ mô phỏng. Đây là
  giả định của mô hình demand, không phải số đo; script chuyển đổi sẽ ghi nó vào `manifest.json`.
- Nếu V1 và V2 quay ở hai ngày khác nhau, có thể dùng chúng làm hai ngày quan sát để tính sàn nhiễu
  giữa ngày (PLAN §5.3). Nếu cùng ngày, chúng chỉ là hai mẫu của một ngày. Ghi rõ ngày trong
  `00_video.yaml`.
- Hàng chờ ghi theo mốc mỗi 10 s (`06_space_seeking.yaml`). PLAN §5.1 ghi mỗi 2 đến 5 s; 10 s là mức
  đếm tay làm được.
