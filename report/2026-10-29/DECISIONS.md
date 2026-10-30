# Quyết định ngày 29–30/10/2026

Các quyết định Claude tự đưa ra khi Viktor vắng mặt (từ 01:00 ngày 30/10), cùng các lựa chọn Viktor đã chốt trong ngày. Báo cáo đầy đủ ở `README.md` cùng thư mục. Chưa commit gì.

## Viktor đã chốt

| # | Nội dung | Ngày |
|---|---|---|
| V1 | Làn 0 chỉ là làn rẽ phải liên tục ở 30 m cuối trước vạch dừng, thượng nguồn vẫn là làn thường. Cạnh tiếp cận được tách tại (vạch dừng − 30 m). | 29/10 |
| V2 | Vi phạm (hành vi 6) là xe có hướng đi thẳng, rẽ trái hoặc quay đầu đứng chờ trên làn 0 trong 30 m cuối khi đèn của chính nó đỏ. Đứng lúc xanh, hoặc đứng ở thượng nguồn, không tính. | 29/10 |
| V3 | Thêm link rẽ trái từ làn 0 (chỉ LVL_W, LVL_E) và quay đầu từ làn 0, 1 (cả 4 nhánh), chỉ cho custom1/custom2, theo đèn rẽ trái. | 29/10 |
| V4 | Giữ đủ các hành vi: rẽ trái từ làn 1–2, rẽ trái từ làn 0 (ít), vượt đỏ để rẽ trái, quay đầu. Không bỏ link nào để giảm teleport. | 30/10 |
| V5 | Xe máy đi sau một xe quay đầu đang đứng chờ phần lớn sẽ lách qua; ô tô ít khi đổi làn để vượt. Đưa vào mô hình bằng một luật TraCI mới. | 30/10 |
| V6 | Video 2 dùng spec biến thể của B1 có thêm hành vi mới, cùng PROXY_D2, seed 1, để so trực tiếp với video 1. | 30/10 |
| V7 | Quay video theo cách cũ (chụp từng khung qua TraCI), không dùng Xbox Game Bar. | 30/10 |

## Claude tự quyết

| # | Quyết định | Lý do |
|---|---|---|
| C1 | Video 1: spec `B1_manual`, PROXY_D2, seed 1, giây 0–1500, chụp mỗi 3 bước (0,3 s). | Run này có lần nút khóa cứng lúc khoảng giây 1290 (42 teleport kẹt/nhường), nên thấy được cả hiện tượng quay đầu chặn xe sau lẫn kẹt nút. |
| C2 | Script quay video là bản Windows của `report/2026-10-28/scripts/record_video.py`, thêm watchdog của bản 26/10; encoder dùng font Segoe UI và ffmpeg của `imageio-ffmpeg` cài vào thư mục tạm (`pip install --target`), không cài vào `.venv`. | Máy Windows không có ffmpeg, Xvfb, DejaVu; không muốn đổi môi trường `.venv`. |
| C3 | Lần quay đầu tiên treo ở khung 2342 (giây 702,6) lúc 00:53; dừng và quay lại từ đầu khi máy rảnh hơn. | Watchdog không gỡ được; lúc đó 6 run `REF_n29s5` và pytest chạy cùng lúc. |
| C4 | Nhãn màu xanh lơ trong video đổi từ "Xe đi thẳng chặn làn rẽ phải" thành "Xe không rẽ phải trên làn 0 gần vạch dừng". | Theo V2, đứng trên làn 0 lúc xanh không còn là vi phạm, nên nhãn cũ sai nghĩa. |
| C5 | Luật mới tên `uturn_bypass`, tham số `p` (xác suất, một lần bốc mỗi cặp xe sau–xe quay đầu) và `t_wait` (giây đứng chờ trước khi bốc). Lách ngang trong làn nếu còn khe, không thì đổi sang làn kề có nối tới hướng đi của xe. Không đổi speed mode hay lane-change mode. | Giữ an toàn mặc định của SUMO, không thêm va chạm do luật gây ra. |
| C6 | Spec `rules/specs/B1_uturn_bypass.json` = `B1_manual` giữ nguyên + 2 mục `uturn_bypass`: xe máy `p` 0,8, ô tô `p` 0,1, `t_wait` 2 s. `B1_manual.json` không đổi. | Giá trị là giả định từ mô tả định tính của Viktor (V5), không có số đếm. |
| C7 | Chưa thêm `uturn_bypass` vào prompt LLM `v002` và vào cấu trúc khóa của P1/B2. | Cấu trúc P1/P2/B2 là quyết định của Viktor; mới có video minh họa. |
| C8 | Sửa prompt `v002` (mục 6, câu "Not violations") và `llm/feedback.py` cho đúng V1–V3. | Mô tả cũ nói đứng chờ trên làn 0 nói chung là vi phạm, không có 30 m và link vi phạm từ làn 0. |
| C9 | Sửa kỳ vọng của `tests/test_outputs_synthetic.py` (F2) theo V2 và thêm 3 trường hợp (đứng lúc đỏ, đứng ngoài 30 m, xe rẽ phải bị chặn lúc đỏ). | Test cũ coi đứng lúc xanh là vi phạm. |
| C10 | Sửa `tests/test_demand.py` (số cạnh của route: LVL 4, HDT 3) và sinh lại `routes_SYNTHETIC.rou.xml` (seed 1; 784 ô tô, 3413 xe máy, 101 xe vi phạm). | Mạng có thêm điểm tách 30 m; file route cũ không còn chạy được. |
| C11 | Không nới `test_short_run_on_new_net` (vẫn fail: 1 va chạm ở giây 77). | Va chạm này đến từ mạng mới (xem README mục 3.3), không phải lỗi test. |
| C13 | Luật qua 3 phiên bản trên PROXY_D1 seed 1 (README mục 4.1). Bản dùng cho video 2 (v3): khi can thiệp, laneChangeMode bit 9–8 = 01 ("avoid immediate collisions") và `lcPushy` = 1 đặt riêng cho xe qua `setParameter`, trả lại khi xong; lề ngang khi lách 0,1 m (Saval et al. 2023, Sec 4). Không dùng `lcPushyGap` (đọc lại ra giá trị âm, chưa hiểu). | v1 chỉ vượt 8/144 lần. Không đổi speed mode để không ép xe vào xe khác. |
| C14 | Dừng tinh chỉnh luật sau v3 và quay video 2, dù hiệu quả trên mạng proxy còn thấp (13/150 lần vượt). | Viktor yêu cầu 2 video. Hạn chế còn lại nằm ở hình học hàng xe máy (minGap 1,9 m của Saval, ba hàng ngang trên làn 3,5 m); sửa phần đó là quyết định của Viktor. |
| C12 | Không chạy campaign B2/P1/P2. Chỉ chạy B0/B1 tham chiếu (`REF_n29s5`, 5 seed) và các run chẩn đoán. | CLAUDE.md và chỉ dẫn trước đó. |
