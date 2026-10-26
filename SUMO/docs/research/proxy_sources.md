# Proxy site values: sources

Research for `config/site.proxy.yaml` (`site_source: LITERATURE_PROXY`), done 2026-10-25.
These numbers are **not field measurements**. `config/site.yaml` keeps `null # TODO_MEASURE`.
Evidence labels: `literature` = a published source states the value or a rule that fixes it;
`literature_transferred` (ruling R13) = from a source but transferred across site, denominator or country
(`<key>_transfer_note` says how); `assumed` = no source found, the value is a stated choice with the reasoning given.

No published source was found that gives the signal timing, lane widths, turn bans, volumes or
vehicle mix at **Le Van Luong x Hoang Dao Thuy** itself. The values below come from Vietnamese
design standards, from studies of other Hanoi junctions (one on the same corridor), and from the OSM
export.

## 1. Values used in `site.proxy.yaml`

| Key | Value | Evidence | Sources |
|---|---|---|---|
| `approaches[*].lane_widths_m` | `[3.5, 3.5, 3.5]` on all four approaches | literature | [S1], lane count [S3] [S4] |
| `exits[*].lane_widths_m` | `[3.5, 3.5, 3.5]` on all four outbound edges (ruling R21) | literature | [S1], lane count [S3] [S4] |
| `approaches[LVL_W].left_turn_banned` | `true` | assumed | [S3] [S9] [S10] |
| `approaches[LVL_E, HDT_N, HDT_S].left_turn_banned` | `false` | assumed | [S3] |
| `approaches[*].u_turn_banned` | `false` | assumed | [S3] |
| `signal.cycle_s` | `120` | literature_transferred (R13: other-junction measurement) | [S2] [S5] |
| `signal.phases` | 2 phases, 64/4/2 + 44/4/2 s | assumed (yellow from [S2]) | [S2] [S3] [S6] |
| `illegal_left.approaches` | `[LVL_W]` | assumed | [S5] |

### Lane widths: 3.5 m

- TCVN 13592:2022 (the urban road design standard that replaced TCXDVN 104:2007), clause 9.2.3:
  "Chiều rộng một làn xe thay đổi trong phạm vi từ 2,75 m đến 3,75 m". Table 10 gives 3.50 m
  for a secondary main street (*đường phố chính thứ yếu*) and 3.75 / 3.50 m for a primary main
  street (*chủ yếu*), and a note says a dedicated bus lane is at least 3.50 m wide [S1]. 3.50 m is
  the one width allowed for both main-street classes, so it is used for every lane. (The online
  copy of Table 10 has garbled columns, so the speed column for each width could not be read.)
- Table 11 [S1]: a left-turn lane next to the median must be ≥ 3.0 m, and a right-turn lane must be
  ≥ (adjacent lane − 0.25 m) and ≥ 3.0 m. These are not used yet because OSM has no separate turn lanes here.
- Lane count is 3 per approach. All four approach ways in the OSM export have `lanes=3`,
  `highway=primary`, `maxspeed=60`, `oneway=yes` (dual carriageways) [S3]. On Le Van Luong the
  leftmost lane is the BRT lane (`psv:lanes=designated|yes|yes`) [S3]. This matches the press
  report "Mỗi chiều có 3 làn lưu thông, gồm 2 làn hỗn hợp cho ô tô, xe máy và một làn riêng dành
  cho tuyến xe buýt nhanh BRT", with a cross-section of nearly 40 m [S4].
- Hoang Dao Thuy is treated as a main street because OSM tags it `primary` at 60 km/h [S3]. Its
  official class was not found, so this is a small assumption inside a `literature` value.
- OSM gives no `width` tags, and netconvert falls back to its 3.2 m default (PLAN Phase 1.3).
- The outbound edges (`exits`) get the same 3.5 m (ruling R21): netconvert gives every internal lane of a
  link the width of its outbound lane, so with the 3.2 m default on the exits the junction box was 0.3 m
  narrower per lane than the approaches, which caused most B0 collisions (Task 4 operator report).

### Turn bans

- OSM: there is no turn-restriction relation at this junction. The export contains 26
  `type=restriction` relations, but the nearest one has members ≥ 202 m from the junction centre
  [S3]. All four approaches have `l` and `t` connections (PLAN Phase 1.3).
- Press: no source found mentioning a left-turn or U-turn ban at LVL x HDT. The junction is
  described as a long-standing congestion point (Zing/VTC 2018: "Cảnh tiến thoái lưỡng nan tại nút
  giao Lê Văn Lương - Hoàng Đạo Thúy").
- Hanoi does ban left turns at comparable arterial junctions nearby:
  - Tố Hữu – Vũ Trọng Khánh: "thành phố cấm phương tiện rẽ trái từ Tố Hữu vào Vũ Trọng Khánh"
    (2022), with a U-turn 300 m downstream [S10].
  - Left turns from Khuất Duy Tiến into Tố Hữu / Lê Văn Lương were only allowed again by a pilot
    from 12/4/2025 [S9].
  - Many OSM restrictions in the bbox are `no_left_turn` with `except=motorcycle`, sometimes
    peak-hour conditional `@ (06:00-09:00,16:00-19:30)` [S3]. That is, Hanoi often bans left turns
    for cars only.
- **Choice (assumed):** `LVL_W` is the banned-left approach. It is meant to be the inbound
  (towards the city centre) Le Van Luong approach, which gets green priority in the AM peak [S6] and
  therefore has the largest volume that could turn left illegally. **Task 2 must check** that
  `LVL_W` really is the approach entering from the Tố Hữu (south-west) side. If it is not, the ban
  should move to whichever LVL approach is inbound.
- U-turns are kept allowed everywhere, as OSM has them. TCCS 24 cl. 6.3.3 recommends moving U-turns
  away from junctions on main roads [S2], but no ban at this site was found.

### Signal

- Cycle 120 s (`literature_transferred` since ruling R13: the 120 s choice rests on the 127 s measured at another junction):
  - TCCS 24:2018/TCĐBVN cl. 6.7.5: "Thời gian chu kỳ thông thường từ 60 s đến 90 s, một số
    trường hợp đặc biệt có thể lên đến giá trị 120 s" [S2].
  - Measured in Hanoi:
    - 127 s at Láng Hạ – Láng (3-lane major road, protected-left phase, on the same Láng Hạ / Lê
      Văn Lương corridor) [S5].
    - 70 s at the smaller Vũ Phạm Hàm – Nguyễn Khang [S5].
    - About 160–165 s at Ngã Tư Sở (8 directions) [S7].
  - HCMC Hàng Xanh runs fixed-time 90–120 s [S8].
  - A busy AM-peak arterial junction sits at the top of the TCCS range, so 120 s is used.
- 2 phases (structure `literature`, split `assumed`):
  - TCCS cl. 6.4.2 says a typical urban 3–4-arm junction needs at least 2 phases [S2].
  - The OSM/netconvert guess is also 2 phases (41 s / 4 s, PLAN 1.3).
  - Lefts and U-turns are permissive in the through phase. Vũ Phạm Hàm – Nguyễn Khang runs that
    way ("Permitted left turn") [S5].
- Yellow 4 s (`literature`): TCCS cl. 6.7.6 sets t_v = 3 s for V ≤ 50 km/h, 4 s for ≤ 60 km/h and
  5 s for ≤ 70 km/h [S2], and OSM maxspeed is 60 [S3]. Hanoi cycles are fixed per time-of-day band
  [S6]. (Press: an expert's speed-based yellow is > 5.27 s at 60 km/h and 3 s at 20 km/h [S12], so
  4 s is a middle value.)
- All-red 2 s (`assumed`):
  - TCCS computes intergreen from clearance and entry distances (cl. 6.7.1), which need the real
    geometry.
  - Its worked 2-phase example (Annex G) uses a total intergreen of 11 s per cycle, i.e. about
    5.5 s per change [S2].
  - With a 4 s yellow, that leaves about 1.5–2 s all-red, so 2 s is used.
  - TCCS also recommends a 1 s red-yellow (cl. 6.7.7), applied when there is no countdown
    display. It is not modelled because it does not change who may enter the junction. If it is
    wanted later, check the SUMO tlLogic state codes in the docs first.
- Green split 64 s (LVL) / 44 s (HDT) (`assumed`):
  - Total green = 120 − 2 × (4 + 2) = 108 s.
  - TCCS allocates green in proportion to the critical flow ratios b_i (Annex G.11) [S2]. No
    flows are known, so LVL gets about 60 %. LVL is the radial artery with BRT [S4], and Hanoi
    gives the inbound radial direction more green in the AM peak [S6].
  - Both greens exceed the TCCS minimum green of 10 s (cl. 6.7.9) [S2].
- Phase format: list of `{name, duration_s, green_movements, yellow_movements}`. A movement is
  written `<approach_id>:<dir>` with `dir` taken from SUMO's connection `dir` values
  (`r` right, `s` straight, `l` left, `t` turnaround). These values were checked at
  sumo.dlr.de/docs/Networks/SUMO_Road_Networks.html, which also lists `L` / `R` (partially
  left / right) and `invalid`. **Task 2 must map `L`→`l` and `R`→`r`** if the net has them.
  Unlisted movements are red.

### Illegal left

`illegal_left.approaches: [LVL_W]` follows the assumed ban. The behaviour itself is documented for
Hanoi:
- At Láng Hạ – Láng, "a large amount of motorcycle of minor flow runs into the middle of the
  intersection and wait for passing when time phase changes" [S5].
- Cars do the same occasionally [S5].

## 2. Values for later tasks (demand / observed proxy targets)

These are not keys of `site.yaml`. They are recorded here for `data/proxy/targets.yaml` (later task).

| Quantity | Value | Evidence | Source |
|---|---|---|---|
| AM peak period, Hanoi | 06:30–08:30 | literature | [S6] (CSGT Hà Nội, 2025) |
| Motorcycle share of vehicles, peak hours, Láng Hạ – Láng | 14148 / (14148 + 2204) = 86.5 % | literature | [S5] |
| Motorcycle share, Vũ Phạm Hàm – Nguyễn Khang | 4865 / (4865 + 1242) = 79.7 % | literature | [S5] |
| Motorcycle share of traffic, Hàng Xanh (HCMC) | 85–90 % | literature | [S8] |
| Motorcycles among registered vehicles, Hanoi | > 90 % | literature | [S11] |
| Volume, Láng Hạ – Láng (all approaches) | 16352 veh in 2 h video (7–8 am + 5–6 pm) ≈ 8200 veh/h | literature (other junction, same corridor) | [S5] |
| Volume, Vũ Phạm Hàm – Nguyễn Khang | 6107 veh in 2 h ≈ 3050 veh/h | literature | [S5] |
| Red-light passing, motorcycles | 11.06 % (site 1), 9.64 % (site 2) of MC volume | literature | [S5] Table 2 |
| Red-light passing, cars | 0.50 %, 0.96 % of car volume | literature | [S5] Table 2 |
| Early departure (> 5 s before green), motorcycles | 15.82 %, 13.55 % | literature | [S5] Table 2 |
| Early departure, cars | 0.68 %, 1.61 % | literature | [S5] Table 2 |
| MC red-run, minor stream, Láng Hạ – Láng | 36.25 % (early run 60.40 %) | literature | [S5] Table 3 |
| Motorcycle PCE at Hanoi signals | 0.24 | literature | [S13] (Minh & Sano 2003, cited) |
| Saturation headway, Hanoi | 2.11 s + 0.51 s per MC between cars | literature | [S13] |
| Start-up lost time, Hanoi | 3.3 s (no MC ahead) → 5.7 s (two MC rows) | literature | [S13] (Nakatsuji et al. 2001, cited) |
| Mean motorcycle speed, Hanoi urban driving | 20.49 km/h | literature | [S11] |

Notes on these values:
- The [S5] Table 2 rows are mis-aligned in the PDF text layer. They were re-paired by checking
  each percentage against its total (e.g. 2238 / 14148 = 15.82 %).
- No LVL × HDT turning-movement count was found. Demand volumes for this junction remain
  TODO_MEASURE.

## 3. Sources

- [S1] TCVN 13592:2022 *Đường đô thị – Yêu cầu thiết kế*, cl. 9.2.3 Table 10, cl. 9.2.4 Table 11.
  Text read at https://dulieuphapluat.vn/van-ban/xay-dung-van-ban/tieu-chuan-quoc-gia-tcvn-135922022-ve-duong-do-thi-yeu-cau-thiet-ke-1145327.html
  (official PDF mirror: https://sgtvt.hochiminhcity.gov.vn/Files/1032/ , which could not be
  downloaded). Supersedes TCXDVN 104:2007, whose full text was not accessible (thuvienphapluat
  403, vbpl.moj.gov.vn unreachable).
- [S2] TCCS 24:2018/TCĐBVN *Tiêu chuẩn thiết kế điều khiển giao thông đường bộ bằng đèn tín hiệu*,
  Tổng cục Đường bộ Việt Nam (based on the German RiLSA). See cl. 6.3.3, 6.4.2, 6.7.1, 6.7.5,
  6.7.6, 6.7.7, 6.7.9 and Annex G.
  https://drvn.gov.vn/upload/2006538/fck/admintcdb/TCCS%2024-2018-%20Tieu%20chuan%20dieu%20khien%20giao%20thong.pdf
  (cl. 6.7.6 read from the rendered page 49, because the formulas are images).
- [S3] OSM export `scenario_raw/2026-10-02-06-34-26/osm_bbox.osm.xml.gz`. Ways within 120 m of
  (105.8047, 21.0053) are 37871458, 208366047, 208366141, 219979442, 408823207, 1071601648 (HDT)
  and 37877893, 711526326, 711526328, 954885541, 1012665662, 1240408565 (LVL). Read with a
  throw-away script (ElementTree, gzip).
- [S4] Tiến Cường, "Khảo sát 2 tuyến đường sẽ phân làn giao thông đảo chiều theo giờ ở Hà Nội",
  VietnamFinance, 08/07/2026. https://vietnamfinance.vn/khao-sat-2-tuyen-duong-se-to-chuc-giao-thong-dao-chieu-o-ha-noi-d147175.html
- [S5] Mai V.H., Chu T.D., Vu H.Q. (2019), "Investigating Signal Violations in Mixed Traffic in Hanoi
  City", *Proc. Eastern Asia Society for Transportation Studies* 12. Video of 24/10/2018,
  7–8 am and 5–6 pm. https://easts.info/on-line/proceedings/vol.12/pdf/PP2454.pdf
- [S6] Hanoi traffic police (CSGT):
  - Peak hours and per-band cycles: lsvn.vn, 26/07/2025,
    https://lsvn.vn/nguoi-dan-ha-noi-luu-y-ve-dieu-chinh-den-tin-hieu-giao-thong-tai-cac-nut-giao-a160945.html
    ("cao điểm sáng từ 06 giờ 30 phút đến 08 giờ 30 phút").
  - Fixed cycles and inbound priority in the AM peak: Viettimes, 14/04/2023,
    https://viettimes.vn/bai-2-phong-canh-sat-giao-thong-ha-noi-noi-gi-ve-giai-phap-thay-doi-nhip-den-tranh-un-tac-post164915.html
    ("khung giờ cao điểm buổi sáng, hệ thống sẽ ưu tiên hướng di chuyển theo trục hướng tâm vào
    thành phố").
- [S7] Phi Long, "Để Ngã Tư Sở không trở lại là 'Ngã tư... khổ'", VOV, 14/11/2020.
  https://vov.vn/xa-hoi/de-nga-tu-so-khong-tro-lai-la-nga-tu-kho-817242.vov
- [S8] Nguyen H.K. (2026), "Projected Impacts of SURTRAC-Enabled Adaptive Signal Control … Ho Chi
  Minh City", *Mathematical Modelling of Engineering Problems* 13(5), 889–896,
  https://doi.org/10.18280/mmep.130509
- [S9] "Thí điểm điều chỉnh giao thông tại nút Lê Văn Lương – Khuất Duy Tiến từ 12/4", lsvn.vn,
  10/04/2025. https://lsvn.vn/thi-diem-dieu-chinh-giao-thong-tai-nut-le-van-luong-khuat-duy-tien-tu-12-4-a156168.html
- [S10] "Hà Nội phân luồng lại một số nút giao từ 18/6", 18/07/2022 (repost on VnReview).
  https://vnreview.vn/thread/ha-noi-phan-luong-lai-mot-so-nut-giao-tu-18-6.140737488533834
- [S11] Nguyen T.Y.L., Nguyen D.K., Cao M.Q., Than T.H.Y., Bui L.H.M. (2022), "A study on the
  determination of the real-world driving characteristics of motorcycles in Hanoi", *Transport and
  Communications Science Journal* 73(4), 412–426, https://doi.org/10.47869/tcsj.73.4.6
- [S12] N. Huyền, "Đèn giao thông rối loạn: rà soát, điều chỉnh phải lưu ý thời gian đèn vàng",
  Người Quan Sát (from VietNamNet), 27/02/2025.
  https://nguoiquansat.vn/den-giao-thong-roi-loan-ra-soat-dieu-chinh-phai-luu-y-thoi-gian-den-vang-201430.html
- [S13] Torquato R.M.N., Maciel M.S.C., Castro Neto M.M. (2020), "Estimation of the effect of
  motorcycles on the capacity of signalized intersections", *Transportes* 28(4). Literature review
  of Nakatsuji et al. (2001) and Minh & Sano (2003, J. EASTS).
  https://anpet.emnuvens.com.br/anpet/article/download/2229/865/11516

## 4. Still TODO_MEASURE (needs video / field survey)

- Real lane widths per lane (and whether the BRT lane is physically separated at the stop line).
- Actual cycle, phase sequence and splits for the AM peak, including whether there is a protected
  left phase as at Láng Hạ – Láng.
- Which approaches are actually left- or U-turn-banned, and where illegal lefts happen.
- Turning-movement counts by vehicle class, 07:30–09:00.
