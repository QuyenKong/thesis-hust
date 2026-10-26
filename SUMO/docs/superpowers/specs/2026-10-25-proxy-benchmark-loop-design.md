# Thiết kế: chạy thông toàn bộ flow với dữ liệu proxy từ tài liệu (3 vòng LLM)

Ngày: 2026-10-25 · Tác giả: Claude (theo yêu cầu của Viktor) · Trạng thái: chờ duyệt

## 1. Mục đích và lý do

Viktor chưa quay được video nên chưa có dữ liệu quan sát. Viktor muốn **thấy methodology hoạt động từ đầu
đến cuối** (xác định chỉ số → LLM sinh luật → biên dịch vào SUMO → chạy thực nghiệm → phân tích vì sao lệch →
gửi lại LLM → sinh lại) trước khi đầu tư quay video. Số liệu thật sẽ thay vào sau, nên mọi thứ phải được
thiết kế để **thay dữ liệu proxy bằng dữ liệu thật chỉ bằng cách thay file**, không sửa code.

Thành công = sau đúng **3 vòng** tinh chỉnh, có một báo cáo cho Viktor đọc: sau 3 vòng cải thiện được gì
(theo từng chỉ số, so với SUMO mặc định), còn vướng mắc gì (kỹ thuật, dữ liệu, methodology).

## 2. Mục tiêu, phi mục tiêu, phản mục tiêu

**Mục tiêu**
- Làm hết PLAN Phase 1 → 7 ở mức "chạy thông", trên dữ liệu proxy.
- Dữ liệu proxy dựa trên số liệu giao thông Việt Nam/Hà Nội đã công bố, có trích nguồn từng con số.
- Vòng LLM chạy đúng 3 iteration, rồi benchmark và báo cáo.
- Một file tracking (`docs/PROGRESS.md`) ghi liên tục mọi việc đã làm để Viktor theo dõi.

**Phi mục tiêu**
- Không cần kết quả có giá trị khoa học; đây là chạy thử methodology.
- Không tối ưu chọn LLM (để sau). Không cần đạt R ≤ 1 trên mọi chỉ số.
- Không xử lý video.

**Phản mục tiêu (dù chạy được vẫn coi là hỏng)**
- Số proxy lẫn vào `config/site.yaml` hoặc bị trình bày như số đo thực địa.
- Thay dữ liệu thật vào sau phải sửa code.
- Báo cáo che giấu chỉ số xấu đi, teleport, can thiệp TraCI không được thực thi, hay việc LLM không cải thiện.
- Đoán tên tham số SUMO thay vì kiểm tra `--help`/docs (quy tắc CLAUDE.md vẫn áp dụng đầy đủ).

## 3. Ràng buộc

- Toàn bộ quy tắc trong `CLAUDE.md` và PLAN §1 vẫn giữ, **trừ** hai ngoại lệ Viktor đã cho phép:
  1. Được dùng số liệu tạm từ tài liệu nghiên cứu cho các giá trị chưa đo (xem §4.2 về cách cô lập).
  2. Làm liên tục, không dừng chờ xác nhận ở cuối mỗi phase, kể cả Phase 3 và cuối Phase 5. Quyết định
     tại các điểm dừng đó được ghi vào `docs/PROGRESS.md` kèm lý do để Viktor xem lại.
- Máy: i5-13400F, 32 GB RAM, RTX 4060 8 GB, ổ C còn ~17 GB (mọi thứ nặng để ở D).
- SUMO 1.27.0, libsumo cho chạy hàng loạt, traci cho sumo-gui.

## 4. Những phần đã quyết định

### 4.1 LLM cục bộ (Viktor: "tự cài", điều chỉnh sau)
- Ollama 0.40.10 (đã cài bằng winget), model lưu ở `D:\ollama\models` (biến môi trường user `OLLAMA_MODELS`).
- Model tạm: `qwen3.5:9b` (Q4, ~6 GB, vừa VRAM 8 GB). Model đích theo PLAN là `qwen3.8:27b`; đổi chỉ bằng
  `config/llm.yaml`. Code chỉ gọi API tương thích OpenAI (`http://localhost:11434/v1`), structured output
  theo JSON Schema, validate + retry tối đa 3 lần nếu runtime không ép được schema.

### 4.2 Dữ liệu proxy (Viktor: "tự nghiên cứu số liệu giao thông VN để chọn số tạm")
- Nghiên cứu tài liệu cho: chu kỳ/pha đèn điển hình nút lớn Hà Nội, bề rộng làn, lưu lượng giờ cao điểm và
  tỷ lệ xe máy/ô tô, headway xả hàng xe máy và ô tô, tỷ lệ vượt đỏ và xuất phát sớm, phân bố vị trí ngang
  xe máy, chiều dài hàng chờ/mật độ, số xe chờ rẽ trái giữa nút, PET.
- Cô lập:
  - Thông số hình học/đèn proxy: `config/site.proxy.yaml` (cùng cấu trúc `site.yaml`), mỗi giá trị kèm
    `source:` (URL/trích dẫn) và nhãn `LITERATURE_PROXY`. `site.yaml` vẫn giữ `null # TODO_MEASURE`.
    Code đọc site qua một hàm duy nhất có cờ `--site config/site.proxy.yaml`; khi dùng proxy thì mọi
    manifest và báo cáo đều in rõ `site_source: LITERATURE_PROXY`.
  - Dữ liệu quan sát proxy: `data/observed/PROXY_D1 … PROXY_D5/`, đúng schema Phase 5.1, sinh bằng một
    script có seed cố định từ `data/proxy/targets.yaml` (bảng chỉ tiêu + nguồn + biến động giữa ngày).
  - Chia ngày: D1–D3 hiệu chỉnh, D4–D5 kiểm chứng (ghi vào `experiment.yaml`).
- Biến động giữa ngày được đặt từ tài liệu nếu có; nếu không có, giả định ±10–15% và ghi rõ là giả định.
- `data/observed/SYNTHETIC/` (Phase 2) vẫn chỉ để test pipeline, khác với PROXY.

### 4.3 Flow mỗi vòng (Viktor mô tả)
`chỉ số mục tiêu → LLM sinh luật → biên dịch & đưa vào SUMO → chạy thực nghiệm → đánh giá → phân tích
nguyên nhân lệch → gửi lại LLM → sinh lại`. Chạy **3 vòng rồi dừng**, kết quả mỗi vòng import ngược vào vòng
sau. Sau 3 vòng: benchmark và báo cáo.

### 4.4 Đội agent (Viktor chỉ định)
| Vai trò | Model | Việc |
|---|---|---|
| Điều phối | Opus 5.5 | Chia việc theo phase, quyết định tại các điểm dừng cũ, phân tích nguyên nhân lệch mỗi vòng |
| Thực thi/code | Opus | Viết code Phase 1–7, test |
| Thao tác/test/SUMO | Sonnet | Chạy pytest, chạy SUMO, mở sumo-gui (backend traci) để kiểm tra trực quan, báo lỗi |
| Ghi chép | Sonnet | Duy trì `docs/PROGRESS.md` |

## 5. Các lựa chọn của Claude (Viktor chưa duyệt, đọc kỹ)

1. **"LLM gen code" được hiểu là LLM sinh *rule spec JSON*** (archetype vType + tham số luật TraCI) đúng
   PLAN Phase 4, rồi compiler biến thành `vtypes.add.xml` + `traci_rules.json`. LLM **không** viết Python
   chạy trong SUMO. Lý do: giữ validator/tái lập/kiểm toán như methodology đã viết. "Cấu trúc luật" (P2)
   = LLM chọn bật/tắt rule_type, số archetype, tỷ trọng, tham số.
2. **Phân tích nguyên nhân lệch** có hai lớp: (a) `feedback.md` sinh tự động (khoảng cách từng chỉ số, R,
   hướng lệch sim > obs hay <, lỗi validator, log can thiệp TraCI) — đây là cái gửi cho LLM local;
   (b) agent điều phối viết ghi chú chẩn đoán vào `PROGRESS.md` (người đọc là Viktor). Ghi chú (b) **không**
   đưa vào prompt, để vòng lặp vẫn tái lập được mà không phụ thuộc Claude.
3. Mỗi vòng: `n_samples = 4` spec, `n_seeds = 3` → ≤ 12 lượt SUMO/vòng, 36 lượt cho 3 vòng. Optuna (B2)
   nhận cùng 36 lượt. Benchmark cuối: B0, B1, B2, P (spec tốt nhất sau vòng 3) trên D4–D5, 20 seed.
   Nếu một lượt 3600 s quá chậm (> ~5 phút) thì giảm thời lượng mô phỏng hiệu chỉnh xuống 1800 s và ghi lại.
4. Phase 3: chạy thí nghiệm sức chứa vùng chờ; nếu native chứa được ≥ số xe chờ proxy thì chọn (a), không thì (b).
5. Morris sensitivity, ablation và kịch bản chính sách 0/50/100% là phần làm *nếu còn thời gian*; báo cáo nêu
   rõ cái nào đã làm, cái nào chưa.
6. Kết quả benchmark P1/H của E1/E2 (doc methodology) có thể rút gọn: tối thiểu B0, B1, B2, P2.

7. **R** = `d_sim_obs / d_day_day` theo PLAN §5.3 và doc methodology; "đạt" khi R ≤ 1. Trên dữ liệu proxy,
   `d_day_day` phụ thuộc biến động giữa ngày do mình giả định, nên báo cáo ghi rõ R **chỉ mang tính minh họa**.
8. **Sinh dữ liệu quan sát proxy theo từng sự kiện**: mỗi chỉ số lấy mẫu từ một họ phân phối có tham số
   (ví dụ lognormal cho headway, Poisson/âm nhị thức cho số vi phạm/chu kỳ), khớp trung bình và độ phân tán
   theo tài liệu. **Tuyệt đối độc lập với output SUMO** (không fit theo B0). Mỗi chỉ tiêu trong
   `targets.yaml` có `evidence: literature | assumed`. Giữ đủ M1–M8 (M7 là kịch bản trọng tâm). Chỉ tiêu
   `assumed` vẫn tính điểm, nhưng báo cáo tách riêng kết quả nhóm `literature` và nhóm `assumed`.
9. **Hình học**: dùng đúng mạng OSM của nút LVL × HĐT (Phase 1). Proxy chỉ điền bề rộng làn, chương trình đèn,
   nhánh cấm rẽ trái/có rẽ trái trái phép. Mạng proxy sinh ra `scenario/net/site.proxy.net.xml`, đặt cạnh
   `site.net.xml`, không ghi đè. Nhánh cấm rẽ trái/có vi phạm: nếu tài liệu/ảnh đường phố không xác nhận được
   thì chọn một nhánh chính trên Lê Văn Lương và ghi `evidence: assumed`.
10. **Ngày kiểm chứng**: D1–D5 dùng seed sinh độc lập cho từng ngày. Báo cáo nói rõ, vì cùng một generator,
    kiểm chứng trên proxy yếu hơn so với dữ liệu thật.
11. **Ngân sách tính theo số lượt SUMO** (1 spec × 1 seed = 1 lượt), dùng một bộ đếm chung. Spec không hợp lệ
    không tốn lượt (validator chặn trước). Optuna 36 lượt = 12 trial × 3 seed. Spec tốt nhất chọn **trên toàn
    bộ các vòng** theo điểm S trung bình seed trên D1–D3.
12. **Model**: tag `qwen3.5:9b` có trên Ollama (đang tải). Nếu không chạy được structured output qua `/v1`
    thì gọi API gốc `/api/chat` với `format` = schema; fallback model `qwen3:8b`.
13. **Tổ chức công việc**: các phase đầu làm tuần tự (mạng → demand → runner → metric → rule → LLM). Agent code
    (Opus) viết, agent thao tác (Sonnet) chạy/kiểm tra sau từng phase, agent ghi chép (Sonnet) cập nhật
    `PROGRESS.md`, agent điều phối (Opus 5.5) giữ thứ tự và chẩn đoán ở mỗi vòng LLM.

## 6. Báo cáo cuối

`docs/reports/2026-10-proxy-run-report.md` (và publish một trang để Viktor xem), gồm:
- Bảng chỉ số × phương pháp (B0, B1, B2, P sau vòng 1/2/3): khoảng cách, R, đạt/không.
- Đường hội tụ theo số lượt SUMO (LLM vs Optuna).
- Chất lượng luật: tỷ lệ spec hợp lệ, số lần retry, tỷ lệ can thiệp TraCI được thực thi.
- Sau 3 vòng cải thiện được gì; chỉ số nào không cải thiện và nguyên nhân phỏng đoán.
- Vướng mắc: giới hạn SUMO, LLM 9B, dữ liệu proxy, các TODO_MEASURE còn lại, việc cần làm khi có video.

## 7. Để lại cho người làm

Kiến trúc module trong `src/thesis_sumo/` theo PLAN §2; định dạng file tracking; cách sinh proxy data cụ thể
(phân phối nào cho từng chỉ số); chi tiết prompt v001; xử lý lỗi khi LLM trả JSON hỏng.
