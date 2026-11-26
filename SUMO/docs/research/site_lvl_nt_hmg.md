# Published geometry of the junction Le Van Luong x Hoang Minh Giam x Nguyen Tuan

Research for `config/site.yaml` after the study junction moved from LVL x Hoang Dao Thuy to LVL x HMG x NT
(owner decision 2026-11-25). The owner asked that road dimensions come from published sources, not a site
survey (2026-11-26). Search run 2026-11-26 through the owner's Perplexity session; the sources marked
"opened" were read in full in the browser, the others only through the Perplexity summary.

Evidence labels follow `docs/research/proxy_targets.md`: `literature` = a published source states the value
for this junction; `standard` = a Vietnamese design standard, not a statement about this junction;
`assumed` = no source.

## 1. Values

| Item | Value | Label | Source |
|---|---|---|---|
| LVL inbound to the centre (LVL_W, from the Khuat Duy Tien underpass) | 3 mixed lanes + 1 BRT lane, since the widening of Dec 2025 – Jan 2026 | literature | [G1] opened |
| LVL_W right turn to Nguyen Tuan | continuous right turn, chevron marking, not signal controlled | literature | [G1] opened |
| LVL per direction (corridor, before or away from the junction) | 2 mixed lanes + 1 BRT lane | literature | [G2], [G3] |
| LVL total cross-section | about 40 m | literature | [G2], [G4] |
| LVL median | 3–7 m depending on the source and date | literature (sources disagree) | [G2], [G5] |
| HMG total cross-section | 17.5 m, no median, sidewalks 3–5 m | literature | [G5] |
| HMG at the junction | one lane added at the start of the street by cutting the sidewalk | literature | [G1] opened |
| NT near the junction (stop line to lane 162, about 400 m) | 4 lanes (2 per direction), widened about 20 years ago, not part of the 21 m project | literature | [G6] |
| Sidewalk cut at the junction | close to 2 m | literature | [G1] (related article title) |
| Lane width | 3.5 m for a secondary arterial (phố chính thứ yếu, 50–70 km/h); range 2.75–3.75 m in steps of 0.25 m | standard | [G7] TCXDVN 104:2007 Table 10, [G8] TCVN 13592:2022 |

No source gives the lane width of any of the three streets at this junction. `lane_widths_m` in `site.yaml`
therefore uses the standard value 3.5 m with the label `standard`.

The Khuat Duy Tien underpass ramp of LVL starts about 212 m south-west of the junction (OSM ways 899919254 /
899919255). Through traffic in the underpass does not reach the study junction's stop line from a different
lane, but the ramp nodes fall inside the 300 m cut radius used for the old junction.

## 2. Open points

- LVL_E (the arm from the Lang Ha side, heading away from the centre): [G1] describes only the inbound
  side, so the lane count of LVL_E at the stop line is not published.
- HMG and NT lane counts at the stop line after the 2025–2026 widening are not published.
- The BRT lane: buses are out of scope (PLAN §1). Whether the BRT lane is modelled as a bus-only lane or left
  out is a modelling decision (`TODO_DECIDE`).

## 3. Sources

- [G1] VTC News, 16/01/2026, "Sau gần 1 tháng xén vỉa hè, 'điểm đen' ùn tắc Lê Văn Lương thay đổi ra sao?",
  https://vtcnews.vn/sau-gan-1-thang-xen-via-he-diem-den-un-tac-le-van-luong-thay-doi-ra-sao-ar998603.html (opened 2026-11-26)
- [G2] Dân trí, 19/05/2026, "Hiện trạng ùn tắc 2 tuyến đường Hà Nội đang nghiên cứu phân luồng đảo chiều",
  https://dantri.com.vn/thoi-su/hien-trang-un-tac-2-tuyen-duong-ha-noi-dang-nghien-cuu-phan-luong-dao-chieu-20260519221131995.htm
- [G3] VietnamPlus, "Hiện trạng hai tuyến đường dự kiến tổ chức giao thông đảo chiều ở Hà Nội",
  https://www.vietnamplus.vn/hien-trang-hai-tuyen-duong-du-kien-to-chuc-giao-thong-dao-chieu-o-ha-noi-post1121751.vnp
- [G4] VnEconomy, 08/10/2010, "Thông xe đường Lê Văn Lương kéo dài", https://vneconomy.vn/thong-xe-duong-le-van-luong-keo-dai.htm
- [G5] VTC News, 24/08/2024, "Nhìn từ trên cao 7 tuyến đường sắp bị xén vỉa hè, dải phân cách ở Hà Nội",
  https://vtcnews.vn/nhin-tu-tren-cao-7-tuyen-duong-sap-bi-xen-via-he-dai-phan-cach-o-ha-noi-ar891193.html
- [G6] Lao Động, 15/08/2024, "Dồn lực triển khai mở rộng đường nổi tiếng ùn tắc ở Hà Nội",
  https://laodong.vn/giao-thong/don-luc-trien-khai-mo-rong-duong-noi-tieng-un-tac-o-ha-noi-1379112.ldo
- [G7] TCXDVN 104:2007 Đường đô thị – Yêu cầu thiết kế, Table 10 (via the reprint at
  https://giaphaco.com/tieu-chuan-xay-dung-viet-nam-tcxdvn-1042007-ve-yeu-cau-thiet-ke-duong-do-thi/), TODO_CITE: check the original text
- [G8] TCVN 13592:2022 Đường đô thị – Yêu cầu thiết kế (via https://luatvietnam.vn/xay-dung/tieu-chuan-tcvn-13592-2022-duong-do-thi-yeu-cau-thiet-ke-253652-d3.html), TODO_CITE: check the original text
