# Phương pháp nghiên cứu của luận văn: giải thích từng bước và kiến thức nền tảng

Tài liệu tự học, viết ngày 22/11/2026 từ `PLAN.md`, các chương 3 đến 6 trong `Latex_SOICT/Chapter/` và mã nguồn trong
`SUMO/src/thesis_sumo/`. Mỗi bước được trình bày theo bốn ý: mục đích, kỹ thuật được dùng, nền tảng lý thuyết cần nắm,
và vị trí trong mã. Cuối tài liệu có bảng kiến thức nền tảng kèm tài liệu đọc thêm và danh sách câu hỏi tự kiểm tra.

Mọi con số về nút giao và dữ liệu mục tiêu trong tài liệu này là giá trị tạm thời (cấu hình đại diện và dữ liệu
PROXY), chưa phải số đo hiện trường.

## 1. Bài toán và cách đặt vấn đề

### 1.1. Phát biểu bài toán

Cho một nút giao có đèn với dòng xe hỗn hợp ô tô và xe máy, mật độ cao, có hành vi không tuân thủ (nút Lê Văn Lương
x Hoàng Đạo Thúy, cao điểm sáng 07:30 đến 09:00). Cần tìm một bộ luật hành vi người lái sao cho trình mô phỏng SUMO
chạy với bộ luật đó tái hiện các hành vi quan sát được tại nút càng giống càng tốt. Bộ luật phải kiểm tra được bằng
máy, chạy được trong SUMO và tái lập được với cùng seed.

### 1.2. Bài toán dưới góc nhìn hình thức

Về bản chất đây là bài toán **hiệu chỉnh mô hình mô phỏng** (simulation model calibration), một dạng bài toán ngược:
biết đầu ra quan sát, tìm đầu vào của mô hình. Ký hiệu một bộ luật là $\theta = (s, \varphi)$, trong đó $s$ là
**cấu trúc** (có những nguyên mẫu tài xế nào, luật có điều kiện nào áp cho nguyên mẫu nào) và $\varphi$ là **tham số**
(giá trị số trong cấu trúc đó). Bài toán là

$$
\theta^\* = \arg\min_{\theta \in \Theta} \; S\big(\mathrm{sim}(\theta, \text{nhu cầu}, \text{seed}),\ \text{quan sát}\big)
\quad \text{với ràng buộc: lần chạy đủ điều kiện,}
$$

trong đó $S$ là điểm tổng khoảng cách giữa mô phỏng và quan sát (mục 13), và tổng số lần chạy SUMO bị giới hạn bởi
một ngân sách cố định.

Ba đặc điểm làm bài toán khó và quyết định thiết kế phương pháp:

1. Hàm mục tiêu là **hộp đen, ngẫu nhiên và đắt**: không có đạo hàm, mỗi lần đánh giá là một lần chạy SUMO 1800 s mô
   phỏng, và kết quả thay đổi theo seed.
2. **Cấu trúc $s$ chưa biết trước.** Với dòng xe tuân thủ, cấu trúc đã có sẵn (bám xe, chuyển làn, nhường đường), chỉ
   cần chỉnh $\varphi$. Với dòng xe Việt Nam, câu hỏi "cần luật nào" là một phần của bài toán. Bộ tối ưu số như
   Optuna chỉ tìm được $\varphi$ khi $s$ đã cho; nó không đề xuất được cấu trúc.
3. **Dữ liệu đo rời rạc**: nhiều đại lượng hành vi tại nút giao Việt Nam chưa được công bố.

### 1.3. Ý tưởng chính: tách sinh luật khỏi thực thi luật

Phương pháp chia làm hai giai đoạn thời gian:

- **Giai đoạn ngoại tuyến (sinh luật)**: một LLM chạy cục bộ đề xuất đặc tả luật (cả $s$ và $\varphi$) dưới dạng
  văn bản JSON có cấu trúc. Đây là chỗ duy nhất LLM tham gia.
- **Giai đoạn trực tuyến (thực thi luật)**: đặc tả được kiểm tra hợp lệ, biên dịch, rồi một bộ điều khiển viết bằng
  mã xác định thực thi nó trong lúc SUMO chạy. Không có lời gọi LLM nào trong lúc mô phỏng.

Kết quả mô phỏng được đổi về cùng lược đồ với dữ liệu quan sát, tính chỉ số, và chỉ số trở thành phản hồi cho lần
sinh luật kế tiếp. Vòng lặp: sinh luật, kiểm tra hợp lệ, biên dịch, mô phỏng, tính chỉ số, phản hồi.

Lý do tách: gọi LLM cho từng xe ở từng bước 0,1 s với hàng trăm xe là không khả thi về thời gian và không tái lập
được; còn đặc tả sinh một lần rồi thực thi bằng mã thì mỗi lần chạy lặp lại được với cùng seed. Ngoài ra, phần thực thi
áp các nguyên tắc an toàn như nhau cho mọi nguồn đặc tả (người viết, LLM, Optuna), nên so sánh giữa các nguồn công bằng.

Khái niệm nền tảng để đọc thêm: hiệu chỉnh mô hình vi mô (calibration of microscopic traffic simulation), tối ưu hộp
đen (black-box optimization), suy luận dựa trên mô phỏng (simulation-based inference), trong đó gần nhất là
Approximate Bayesian Computation (ABC) và phương pháp mô-men mô phỏng (method of simulated moments): cả hai đều so mô
phỏng với quan sát qua các thống kê tóm tắt và một hàm khoảng cách, đúng như cách luận văn dùng M1 đến M10. Về vai trò
của LLM, khái niệm gần nhất là "LLM như bộ tối ưu" (OPRO, Yang và cộng sự) và tìm kiếm chương trình có LLM dẫn hướng
(FunSearch, Romera-Paredes và cộng sự).

## 2. Bước 1: Xác định các hành vi cần mô hình hóa

**Mục đích.** Quyết định mô hình phải tái hiện những gì trước khi quyết định tái hiện bằng cách nào.

**Kỹ thuật.** Tổng hợp tài liệu đã công bố và bổ sung từ quan sát hiện trường. Kết quả là 11 hành vi, chia theo
**cơ chế** thành ba nhóm:

| Nhóm | Cơ chế chung | Hành vi |
|---|---|---|
| F1: không tuân thủ tín hiệu | Quyết định đi khi đèn không cho phép, phụ thuộc trạng thái đèn và người xung quanh | 1 vượt đèn đỏ theo ngưỡng kiên nhẫn; 2 vượt đỏ theo đoàn; 3 xuất phát sớm |
| F2: tìm khoảng trống khi ùn | Hàng chờ dài thì tìm không gian khác để lên đầu hàng | 4 khoảng cách ngang nhỏ, lấn, luồn lách; 5 đi sai làn rồi cắt về; 6 chặn làn rẽ phải liên tục; 7 đi trên vỉa hè; 8 đi ngược chiều (hoãn) |
| F3: tương tác trong nút | Các dòng xe cắt nhau bên trong nút | 9 chấp nhận khoảng trống nhỏ, tạt đầu; 10 rẽ trái trái phép chờ giữa nút; 11 xe máy đi chậm giữa làn |

Cơ sở tài liệu chính: Mai và cộng sự (2019) đo tỷ lệ vượt đèn đỏ 9,64 đến 11,06% và xuất phát sớm 13,55 đến 15,82%
của xe máy tại hai nút ở Hà Nội; Saval và cộng sự (2023, PLOS ONE) có mô hình tác tử GAMA cho Hà Nội với xác suất dừng
đèn đỏ 0,5; Phuengprachuab và cộng sự (2023) và Gao và cộng sự (2020) cho thấy vượt đỏ có tính lây lan xã hội; Chu Cong
Minh và cộng sự (2005) đo khoảng cách ngang xe máy 1,10 m; Hsu và cộng sự (2024) đo PET trung bình 2,15 s. Các hành vi
5, 6, 7, 11 và luật vượt xe quay đầu đến từ quan sát và khảo sát hiện trường, chưa có số đếm.

Cách chia theo cơ chế quyết định cách biểu diễn: mỗi nhóm dùng một hoặc vài loại luật chung điều kiện kích hoạt, thay
vì mỗi hành vi một luật riêng. Ví dụ hành vi 5, 6, 7 dùng chung luật `queue_space_seeking`.

Hai quyết định phạm vi cần nhớ khi bảo vệ: rẽ phải khi đèn đỏ **không** phải vi phạm (mọi nhánh có làn rẽ phải liên
tục), và hành vi 8 bị hoãn vì các cách biểu diễn đã thử làm SUMO không còn tính xung đột với dòng ngược chiều thật.

**Nền tảng cần nắm.** Phân biệt hành vi liên tục (biểu diễn bằng tham số tĩnh) và hành vi tình huống (biểu diễn bằng
luật có điều kiện). Khái niệm dị biệt người lái (driver heterogeneity). Khái niệm chỉ số an toàn thay thế (surrogate
safety measure), đặc biệt PET (post-encroachment time): khoảng thời gian từ lúc xe thứ nhất rời vùng xung đột đến lúc xe
thứ hai vào vùng đó.

## 3. Bước 2: Dựng kịch bản và mạng mô phỏng

**Mục đích.** Có một mạng SUMO của nút giao, dựng lại được từ đầu bằng một lệnh, có sẵn các không gian mà chỉ xe vi
phạm được dùng.

**Kỹ thuật.**

1. **Cắt mạng từ OpenStreetMap** bằng `netconvert`: giữ bán kính 300 m quanh tâm nút, chỉ giữ cạnh cho `passenger`
   và `motorcycle`, đèn kiểu tĩnh (static), bỏ nút và đèn phụ trên các nhánh (`src/thesis_sumo/net/build_net.py`).
2. **Bản vá plain XML** (`*.edg.xml`, `*.con.xml`, `*.tll.xml`) sinh từ `config/site.yaml`, áp bằng
   `netconvert -s base.net.xml -e ... -x ... -i ...` (`net/apply_patches.py`). Không ai sửa tay `.net.xml`; mọi thay
   đổi đều nằm trong tệp vá có lịch sử git.
3. **Lớp vi phạm** bằng vClass riêng: `custom1` là xe máy vi phạm, `custom2` là ô tô vi phạm. Quyền dùng làn và
   connection trong SUMO được khai báo theo vClass (`allow`/`disallow`), nên một không gian mở cho `custom1` thì xe
   tuân thủ không vào được. Nếu không tách lớp, mở vỉa hè cho hành vi vi phạm đồng nghĩa với mở cho mọi xe.
4. **Bốn bản vá cho hành vi cần không gian riêng**: connection rẽ trái chỉ cho `custom1` ở hai nhánh Hoàng Đạo Thúy
   (cấm rẽ trái); làn rẽ phải liên tục ở lane 0 trong 30 m cuối, link rẽ phải mang trạng thái `g` ở mọi pha; tách
   mỗi nhánh thành đoạn thượng nguồn và đoạn 30 m sát vạch dừng; làn vỉa hè chỉ cho `custom1` dài 170 m ở hai nhánh
   Lê Văn Lương.
5. **Điểm chờ giữa nút** cho hành vi 10 dùng internal junction sẵn có của SUMO, chọn sau thí nghiệm khả thi 3D đo số
   xe máy cùng dừng chờ được trên link rẽ trái trong nút.
6. **Chương trình đèn** ba pha, chu kỳ 120 s (giá trị tạm thời từ TCCS 24:2018 và số đo của Mai và cộng sự tại nút
   Láng Hạ x Láng): các trạng thái 42/4/2/16/4/2/44/4/2 s.

**Thí nghiệm khả thi (Phase 3).** Trước khi đưa một hành vi cần không gian riêng vào mô hình, nó được thử trên kịch
bản nhỏ để trả lời bốn câu hỏi: SUMO có tự tạo ra hành vi không; cấu trúc mạng nào cho phép nó; xe tuân thủ chịu chi
phí gì; SUMO còn tính xung đột giữa xe vi phạm và dòng xe thật không. Hành vi không qua câu hỏi cuối thì không đưa vào,
vì khi đó mô phỏng cho năng lực thông qua và mức an toàn ảo. Đây là lý do hành vi 8 bị hoãn.

**Nền tảng cần nắm.** Mô hình mạng của SUMO: edge, lane, connection, internal lane, junction, logic quyền ưu tiên, và
trạng thái link của đèn (`G` xanh ưu tiên, `g` xanh phải nhường, `y`, `r`). Định dạng plain XML của `netconvert`. Khái
niệm vClass và quyền dùng làn theo vClass. Tham khảo: tài liệu SUMO (sumo.dlr.de/docs) các trang "Networks/PlainXML",
"Simulation/Traffic Lights", "Definition of Vehicles, Vehicle Types, and Routes"; Lopez và cộng sự (2018) giới thiệu
SUMO.

## 4. Bước 3: Dựng nhu cầu giao thông từ số đếm rẽ

**Mục đích.** Sinh tệp tuyến (`.rou.xml`) có số xe theo từng hướng rẽ, loại xe và ô 15 phút khớp với số đếm quan sát.

**Kỹ thuật** (`src/thesis_sumo/demand/build_demand.py`):

1. Sinh `candidate_routes.rou.xml` gồm mọi tuyến hợp lệ đi qua nút (vào, ra).
2. Đọc `turn_counts.csv` theo lược đồ quan sát, chạy công cụ `routeSampler.py` của SUMO cho từng loại xe
   (`--turn-files`, `--turn-attribute <type>`, `--seed`). routeSampler chọn tổ hợp tuyến ứng viên sao cho số xe qua
   từng cặp cạnh (edgeRelation) khớp số đếm. Mỗi loại xe dùng seed riêng (`seed + k*1000`) để không chung luồng ngẫu
   nhiên.
3. Tệp tuyến tham chiếu tên phân phối `car`, `moto`, `moto_violator`. Vì tên cố định, mọi đặc tả luật dùng chung một
   tệp nhu cầu: đổi đặc tả không đổi số xe hay hướng đi, chỉ đổi cách các xe đó hành xử. Đây là điều kiện để so sánh
   các đặc tả với nhau.

**Nền tảng cần nắm.** Ước lượng ma trận OD hoặc tuyến từ số đếm (OD estimation from traffic counts), công cụ
routeSampler (tài liệu SUMO "Tools/Turns"). Tắt định tuyến lại (`device.rerouting`) để tuyến không đổi trong lúc chạy.

## 5. Bước 4: Mô hình hành vi nền của SUMO và nguyên mẫu tài xế

**Mục đích.** Hiểu chính xác lớp tham số tĩnh: luật của luận văn đặt lên trên các mô hình này, nên phải biết chúng
làm gì trước khi biết luật sửa gì.

**Kỹ thuật.**

- **Mô hình bám xe Krauss** (mặc định của SUMO): mỗi bước, xe chọn tốc độ an toàn sao cho nếu xe trước phanh gấp thì
  xe sau vẫn dừng được trước khi va chạm, với thời gian phản ứng `tau`, giới hạn bởi `accel`, `decel`, tốc độ tối
  đa, và trừ đi một nhiễu ngẫu nhiên điều khiển bởi `sigma` (mức không hoàn hảo của người lái). Tham số khác:
  `minGap`, `speedFactor`, `speedDev`.
- **Mô hình làn con (sublane) và mô hình chuyển làn SL2015**: mỗi làn chia thành các dải ngang rộng
  `lateral-resolution` (luận văn dùng 0,4 m); xe hẹp như xe máy có thể đứng cạnh nhau trong một làn và di chuyển
  ngang liên tục. Tham số: `minGapLat`, `maxSpeedLat`, `latAlignment`, `lcSublane`, `lcPushy`, `lcPushyGap`,
  `lcAssertive`, `lcImpatience`, `lcAccelLat`, ... Semrau và Erdmann (2016) dùng mô hình này cho dòng xe kiểu châu Á.
- **Mô hình nút (junction model)**: các tham số `jm*` (ví dụ `jmDriveAfterRedTime`, `jmTimegapMinor`) và
  `impatience` điều khiển việc xe vào nút, chấp nhận khoảng trống, đi khi đèn vừa đỏ.
- **Nguyên mẫu tài xế** (driver archetype): mỗi loại phương tiện được chia thành một hỗn hợp các nguyên mẫu, mỗi nguyên
  mẫu có tỷ trọng và tập tham số tĩnh riêng. Trong SUMO đây là `vTypeDistribution`: khi một xe được sinh, SUMO rút
  một vType theo tỷ trọng và xe giữ vType đó suốt hành trình. Về mặt thống kê đây là mô hình hỗn hợp hữu hạn (finite
  mixture) hay mô hình lớp ẩn (latent class) cho dị biệt người lái.

**Nền tảng cần nắm.** Krauss (1998) cho mô hình bám xe; Erdmann (2015) cho mô hình chuyển làn của SUMO; Semrau và
Erdmann (2016) cho mô hình làn con. Khái niệm mô hình bám xe không va chạm (collision-free car-following). Nắm sự khác
nhau giữa Krauss và IDM: chính sự khác nhau này gây ra phát hiện ở mục 18 (`accel` 1,1 m/s² chuyển từ IDM của Saval
sang Krauss làm xe máy xả hàng quá chậm).

## 6. Bước 5: Biểu diễn luật (đặc tả luật)

**Mục đích.** Có một dạng biểu diễn chung cho mọi nguồn sinh luật, kiểm tra được bằng máy.

**Kỹ thuật.**

- **Đặc tả luật** là một tệp JSON theo lược đồ JSON Schema draft 2020-12 (`rules/schema/rule_spec.schema.json`), gồm:
  định danh và nguồn (`manual`, `llm`, `optuna`); truy vết (`provenance`: mô hình, phiên bản prompt, vòng lặp, chỉ số
  mẫu); danh sách nguyên mẫu tài xế (vClass cơ sở, phân phối, tỷ trọng, tham số, lý do); danh sách luật có điều kiện
  (loại luật, nguyên mẫu áp dụng, tham số, lý do).
- **Tệp miền giá trị** `rules/bounds/param_bounds.yaml`: mỗi tham số có tên, đơn vị, cận dưới, cận trên, mặc định,
  nhóm hành vi, các chỉ số ràng buộc được nó, nguồn URL và nhãn bằng chứng (tài liệu SUMO, tài liệu khoa học, chuyển
  giao, quyết định thiết kế, giả định). Mọi tên tham số được kiểm tra với tài liệu SUMO trước khi đưa vào.
- **Hai quy tắc thu nhỏ không gian tìm kiếm.** Tham số không có chỉ số nào ràng buộc được bị cố định ở mặc định, vì
  không hiệu chỉnh được từ dữ liệu (đây là vấn đề **khả nhận dạng**, identifiability). Tham số cho phép xe bỏ qua xe
  xung đột có quyền ưu tiên (`jmIgnoreFoeProb` và tương tự) bị loại hẳn, vì theo thiết kế nó tạo va chạm thật.
- LLM và Optuna dùng **cùng một tệp miền giá trị**, nên hai bên tìm trên đúng cùng một tập. Đây là điều kiện cần cho
  so sánh công bằng ở thí nghiệm E1.

**Nền tảng cần nắm.** JSON Schema (đặc biệt `oneOf`, `required`, `enum`, `minimum`/`maximum`). Khái niệm khả nhận
dạng tham số trong hiệu chỉnh mô hình: hai bộ tham số khác nhau cho cùng đầu ra thì dữ liệu không phân biệt được chúng.

## 7. Bước 6: Cơ chế của từng loại luật có điều kiện

**Mục đích.** Mỗi hành vi tình huống được mô tả bằng điều kiện kích hoạt, hành động, tham số hành vi và **biến đệm**.
Biến đệm là một điều kiện hoặc giới hạn đặt giữa kích hoạt và hành động; nó không tạo ra hành vi mà ngăn hành vi gây
ra hậu quả mô phỏng mà thực tế không có. Khi trình bày, luôn nêu biến đệm kèm hậu quả nếu thiếu nó.

### 7.1. `swarm_red_running` (hành vi 1, 2)

Khi xe tới vạch dừng lúc đèn đỏ, xác suất quyết định vượt là

$$ p = \min(p_0 + k\,n,\ p_{\max}) $$

với $p_0$ là xác suất nền (ngưỡng kiên nhẫn), $n$ là số xe đã vượt đỏ trên cùng nhánh trong $\Delta t$ giây gần nhất,
$k$ là mức tăng trên mỗi xe vừa vượt (hiệu ứng bầy đàn). Quyết định rút **một lần** khi xe tới vạch.

- Biến $n$ làm các lượt vượt đỏ phụ thuộc nhau. Hệ quả kiểm tra được: số xe vượt đỏ mỗi chu kỳ có phương sai lớn hơn
  trung bình (quá phân tán, overdispersion), đo bằng tỷ số phương sai trên trung bình trong M3. Nếu các lượt độc lập
  với cùng xác suất, số vượt mỗi chu kỳ gần phân phối nhị thức hoặc Poisson, tỷ số này không vượt 1 đáng kể.
- Biến đệm 1: trần $p_{\max}$. Thiếu nó thì chuỗi vượt đỏ tự khuếch đại tới $p = 1$.
- Biến đệm 2: **điều kiện nút thông**: xe đã quyết định vượt chỉ vào nút khi làn ra còn chỗ, không có xe trên làn nội
  bộ cắt ngang và không có xe đứng trên làn nội bộ của chính link. Thiếu nó thì xe vượt đỏ dừng giữa dòng đang xanh
  và gây khóa nút (gridlock).

### 7.2. `early_start` (hành vi 3)

Trong $t_{\text{before}}$ giây cuối pha đỏ, xe đầu hàng nhích qua vạch với xác suất $p$. Biến đệm là tốc độ tối đa
$v_{\max}$: thiếu nó xe tăng tốc như khi xanh và lao vào luồng cắt ngang chưa xả hết.

### 7.3. `queue_space_seeking` (hành vi 5, 6, 7)

Mỗi xe thuộc nguyên mẫu áp dụng được rút ngẫu nhiên **đúng một lần**, tại thời điểm đầu tiên một trong ba điều kiện
thỏa: hàng chờ ở làn đúng dài ít nhất $q$ mét; xe đã dừng ít nhất $t_w$ giây; hoặc $t_g$ giây trước lượt xanh kế tiếp,
xe ước lượng mình không qua kịp vạch trong lượt xanh đó. Kết quả rút là một trong các lựa chọn `wrong_lane` (đi làn
sai rồi cắt về), `right_lane` (dừng trên làn rẽ phải liên tục), `sidewalk` (lên vỉa hè), hoặc không làm gì, với xác
suất $p_{\text{wrong\_lane}}, p_{\text{right\_lane}}, p_{\text{sidewalk}}$.

- Biến đệm "rút một lần": nếu rút lại ở mỗi bước với xác suất nhỏ $p$, xác suất làm hành vi sau $N$ bước là
  $1 - (1-p)^N \to 1$ khi chờ lâu, và tham số mất ý nghĩa. Đây là lập luận về hàm nguy cơ (hazard) cộng dồn.
- Biến đệm sai số ước lượng $\sigma$: thời gian cần để qua vạch được nhân với một sai số ngẫu nhiên, để các xe cùng
  vị trí trong hàng không quyết định giống hệt nhau.
- Biến đệm vùng nhập lại và $v_{\text{creep}}$: xe đi sai làn phải cắt về làn đúng trong đoạn 30 m cuối bằng
  `changeLane` (lane change mode bit 9 đến 8 bằng 01, `lcPushy` bằng 1, trả lại sau vạch); chưa nhập được thì đứng ở
  cuối làn sai, chặn xe sau.
- Khi một lựa chọn không có không gian tại nút (ví dụ phương án chính sách chặn vỉa hè), xác suất của nó được chia
  lại theo tỷ lệ cho các lựa chọn còn lại. Đây là cơ chế "dồn hành vi", dự kiến dùng khi đánh giá phương án tổ chức giao
  thông.

### 7.4. `illegal_left_box` (hành vi 10)

Xe vào giữa nút trong pha xanh đi thẳng của nhánh mình, dừng ở điểm chờ trong nút (internal junction), rồi rẽ khi
dòng đi thẳng đối diện ngớt. Việc rời điểm chờ dùng cơ chế nhường đường của chính SUMO (tham số khoảng trống chấp nhận
của lớp vi phạm). Luật chỉ thêm độ trễ giải phóng $\Delta_{\text{release}}$. Biến đệm là nguyên tắc **chỉ giữ, không
đẩy**: luật chỉ được giữ xe lâu hơn, không được ép xe đi xuyên dòng xung đột. Cách "ép" đã được thử và cho số va chạm
gấp nhiều lần khi bật kiểm tra va chạm trong nút.

### 7.5. `slow_lane_center` (hành vi 11) và `uturn_bypass` (bổ sung)

`slow_lane_center` giữ xe máy chậm ở vị trí ngang lệch $\delta$ so với tim làn. `uturn_bypass`: xe đứng sau một xe chờ
quay đầu khi đèn của chính nó xanh, sau $t_{\text{wait}}$ giây được rút một lần mỗi cặp với xác suất $p$; nếu trúng
thì lách ngang hoặc đổi sang làn kề. Biến đệm là $t_{\text{wait}}$ và quy tắc rút một lần mỗi cặp.

**Nền tảng cần nắm.** Quá trình Bernoulli và phân phối nhị thức; quá phân tán và phân phối nhị thức âm (negative
binomial); hàm nguy cơ trong phân tích sống sót (để hiểu vì sao phải rút một lần); mô hình lây lan xã hội tuyến tính.

## 8. Bước 7: Sinh luật bằng LLM

**Mục đích.** Dùng LLM làm "người lập mô hình": đề xuất cấu trúc luật, chọn tham số và sửa đề xuất theo sai lệch định
lượng giữa mô phỏng và quan sát.

**Kỹ thuật** (`src/thesis_sumo/llm/`):

1. **Giao diện tương thích OpenAI** (`client.py`), để mã không phụ thuộc runtime (Ollama, vLLM, LM Studio). LLM cục
   bộ là `qwen3.5:9b`, lượng tử hóa Q4_K_M, chạy bằng Ollama trên GPU RTX 4060 8 GB, cửa sổ ngữ cảnh 32.768 token,
   `max_tokens` 7000, nhiệt độ 0,7, seed 42 (mẫu thứ $j$ dùng seed $42+j$ để bốn mẫu một vòng khác nhau).
2. **Đầu ra có cấu trúc** (structured output): gửi một lược đồ JSON cho máy chủ, máy chủ ràng buộc quá trình giải mã để
   đầu ra luôn đúng cú pháp lược đồ (constrained decoding). Lược đồ gửi đi là tập con an toàn với bộ giải mã (liệt kê
   rõ thuộc tính, không dùng cấu trúc điều kiện); lược đồ đầy đủ vẫn dùng để kiểm tra hợp lệ. Nếu máy chủ từ chối lược
   đồ, trình khách lùi về JSON thường rồi kiểm tra.
3. **Prompt có phiên bản** (`prompts/v001` đến `v005`), khóa theo chiến dịch. Prompt gồm: vai trò và ràng buộc; bối
   cảnh nút giao kèm từ điển tham số sinh tự động từ `param_bounds.yaml` và giá trị mục tiêu của các ngày hiệu chỉnh;
   với mỗi vòng trước, các đặc tả và phản hồi định lượng. Phản hồi gồm khoảng cách và tỷ số $R$ theo từng chỉ số kèm
   giá trị quan sát và mô phỏng (mục 13), tỷ lệ ô qua cổng G0, số và vị trí teleport kẹt, lỗi của bộ kiểm tra hợp lệ,
   và tóm tắt nhật ký can thiệp (số lần mỗi luật kích hoạt và số lần SUMO thi hành). Vòng gần nhất gửi đầy đủ, vòng
   cũ chỉ còn vài dòng tóm tắt ($S$, tính đủ điều kiện, nguyên mẫu, luật) để không vượt cửa sổ ngữ cảnh. Phản hồi chỉ
   dùng các ngày hiệu chỉnh (mục 15).
4. **Tự sửa lỗi theo phản hồi của bộ kiểm tra** (validate-and-retry): đặc tả không hợp lệ được gửi lại cho LLM kèm
   danh sách lỗi, tối đa 3 lần thử mỗi mẫu. Đặc tả không hợp lệ không tốn lần chạy SUMO.
5. **Nhịp vòng lặp** (`loop.py`): mỗi vòng sinh 4 mẫu; mỗi mẫu hợp lệ được biên dịch và chạy trên 3 ngày hiệu chỉnh;
   giữ đặc tả tốt nhất; dừng khi hết ngân sách số lần chạy SUMO (tối đa 5 vòng).
6. **Hai chế độ** để tách hai vai trò của LLM:
   - `params_only` (phương án P1): khóa cấu trúc của B1, LLM chỉ đổi giá trị; mọi thay đổi cấu trúc bị lỗi
     `structure_locked`. Ở chế độ này LLM làm đúng việc của Optuna.
   - `full` (phương án P2): LLM sinh cả cấu trúc và tham số. Từ prompt `v005` có ràng buộc **phủ luật** (coverage):
     phải dùng đủ 6 luật TraCI và bật mỗi luật ở ít nhất một nguyên mẫu. Lý do: chiến dịch P2 ngày 08/11 đạt $S$
     thấp nhất bằng cách bỏ `queue_space_seeking`, `uturn_bypass`, `slow_lane_center`, tức bỏ bớt hành vi mà mô hình
     phải tái hiện. Hiện tượng này trong học máy gọi là "lách đặc tả" (specification gaming, reward hacking).
7. **Tái lập**: mọi yêu cầu và câu trả lời lưu nguyên văn trong `experiments/llm_logs/`; chạy lại với cùng tin nhắn và
   cùng định danh mô hình thì câu trả lời được phát lại từ đĩa, không gọi lại LLM.
8. **Chế độ suy nghĩ tắt** (`reasoning_effort: none`) cho P1, P2 ngày 08/11, vì khi bật, phần suy nghĩ dài 18.554 và
   28.585 ký tự chiếm hết giới hạn token trước khi tới JSON.

**Nền tảng cần nắm.** Kiến trúc Transformer và sinh văn bản tự hồi quy; nhiệt độ lấy mẫu; giải mã có ràng buộc theo
ngữ pháp hoặc lược đồ (grammar-constrained decoding); lượng tử hóa trọng số (quantization, định dạng GGUF, Q4_K_M);
học trong ngữ cảnh (in-context learning); "LLM như bộ tối ưu" (Yang và cộng sự, OPRO); lách đặc tả. Các công trình dùng
LLM với SUMO mà luận văn trích: AgentSUMO (Jeong và cộng sự, 2025), ChatSUMO (Li và cộng sự, 2026).

## 9. Bước 8: Kiểm tra hợp lệ trước khi chạy

**Mục đích.** Chặn mọi đặc tả sai trước khi tốn lần chạy SUMO, và trả lỗi đủ cụ thể để LLM sửa được.

**Kỹ thuật** (`src/thesis_sumo/rules/validator.py`), năm nhóm kiểm tra:

1. Đối chiếu với JSON Schema.
2. Tên tham số có trong tệp miền giá trị; giá trị trong khoảng; tổng tỷ trọng mỗi phân phối bằng 1; tham số đúng cho
   từng loại luật.
3. Mâu thuẫn logic phụ thuộc nút: `minGapLat` lớn hơn bề rộng làn nhỏ nhất; $p_0 > p_{\max}$; luật áp cho loại
   phương tiện không phù hợp; lựa chọn đi sai làn trên nhánh không có làn tương ứng; khai báo đồng thời hai tham số
   mà SUMO chỉ dùng một. Các kiểm tra này đọc từ `site.yaml` và mạng đã dựng.
4. Chỉ ở `params_only`: cấu trúc phải khớp B1.
5. Chỉ ở `full` từ `v005`: đủ 6 luật (mã lỗi `coverage`).

Kết quả là **cả danh sách lỗi**, mỗi lỗi có đường dẫn tới phần tử sai, mã lỗi và thông điệp nêu khoảng hoặc tên được
phép. Tỷ lệ đặc tả hợp lệ được ghi cho từng câu trả lời và là một chỉ số của vòng LLM. Số liệu đã có: P1 có 12/27 câu
trả lời hợp lệ, P2 có 14/36; lỗi thường gặp nhất của P2 là mã nguyên mẫu trùng tên phân phối (19 lần) và tổng tỷ trọng
khác 1 (15 lần); 14/15 lần thử hỏng của P1 là lỗi tổng tỷ trọng ở phân phối `moto_violator` chỉ có một nguyên mẫu.

## 10. Bước 9: Biên dịch và thực thi luật trong SUMO

**Mục đích.** Biến đặc tả thành hành vi của xe mà không làm hỏng các cơ chế an toàn của SUMO.

**Kỹ thuật.**

1. **Biên dịch** (`rules/compiler.py`): đặc tả thành hai tệp, `vtypes.add.xml` (lớp tham số tĩnh, các
   `vTypeDistribution`) và `traci_rules.json` (lớp luật có điều kiện). Bộ biên dịch ghi mọi tham số tường minh, kể cả
   giá trị mặc định, và nạp thử tệp với kiểm tra lược đồ XML của SUMO, vì SUMO có thể bỏ qua âm thầm một tên tham số
   sai.
2. **Bộ điều khiển TraCI** (`runtime/controller.py`, `runtime/rules/*.py`): mỗi loại luật là một lớp có `on_step`,
   đăng ký theo mẫu registry. Mỗi bước 0,1 s, bộ điều khiển đọc trạng thái các xe trong bán kính quanh nút bằng
   **subscription** (đăng ký nhận dữ liệu, thay vì hỏi từng xe), đánh giá điều kiện và ra lệnh. Chạy được qua `traci`
   (socket, dùng được với sumo-gui) và `libsumo` (cùng tiến trình, nhanh hơn); `tests/test_backends.py` kiểm tra hai
   đường cho kết quả giống hệt.
3. **Năm nguyên tắc can thiệp an toàn**:
   - Chỉ gỡ đúng ràng buộc cần gỡ. Ví dụ luật vượt đỏ chỉ xóa bit 4 của speed mode (dừng khi đèn đỏ), giữ bit 3
     (nhường quyền ưu tiên trong nút) và các bit khác. Ràng buộc nào cần gỡ được xác định bằng thí nghiệm trên nút nhỏ.
     Nếu gỡ hết, bộ luật có thể "khớp" dữ liệu nhờ va chạm và chồng lấn vật lý, và vòng tối ưu sẽ khai thác lỗ hổng đó.
   - Chỉ giữ, không đẩy (mục 7.4).
   - Mỗi xe một can thiệp tại một thời điểm, để lệnh ghi đè không chồng nhau và mỗi hành vi có đúng một nguyên nhân.
   - Khôi phục và đọc lại: mọi thay đổi được hoàn tác khi can thiệp kết thúc; sau mỗi lần đặt và khôi phục, bộ điều
     khiển đọc lại giá trị từ SUMO và dừng lần chạy nếu không khớp.
   - Chỉ xét vùng nút; trạng thái đèn của mỗi xe lấy theo đúng link mà xe sẽ đi, để xe rẽ theo mũi tên riêng không bị
     coi là vượt đỏ.
4. **Ghi nhận can thiệp**: mỗi can thiệp là một bản ghi bảy trường (thời điểm, mã xe, luật, hành động, cờ thực thi,
   lý do không thực thi, thời điểm xác định kết quả). Cờ thực thi phân biệt "luật vô tác dụng" với "luật chưa từng
   kích hoạt". Mỗi can thiệp mở một **cửa sổ can thiệp** kéo dài tới khi xe ra khỏi nút; va chạm có ít nhất một xe
   trong cửa sổ được tính là liên quan can thiệp.
5. **Tất định**: mỗi luật có bộ sinh số ngẫu nhiên riêng khởi tạo từ seed của lần chạy, xe được duyệt theo thứ tự mã.
   Cùng đặc tả, cùng nhu cầu, cùng seed thì cùng chuỗi quyết định.

**Nền tảng cần nắm.** Giao diện TraCI (mô hình client-server, lệnh `setSpeedMode`, `setLaneChangeMode`, `changeLane`,
`slowDown`, subscription); bảng bit của speed mode và lane change mode trong tài liệu SUMO ("TraCI/Change Vehicle
State"); mô phỏng ngẫu nhiên có seed và bộ sinh số giả ngẫu nhiên độc lập theo luồng.

## 11. Bước 10: Chạy mô phỏng và thu đầu ra

**Kỹ thuật** (`sim/runner.py`, `sim/sumocfg.py`, `config/experiment.yaml`):

- SUMO 1.27.0, bước 0,1 s, độ phân giải làn con 0,4 m, SL2015, tắt định tuyến lại, bật
  `collision.check-junctions`, gộp cảnh báo sau 20 dòng.
- Thời lượng đầy đủ 3600 s; vòng hiệu chỉnh và đánh giá dùng 1800 s đầu (07:30 đến 08:00); chỉ số tính trên cửa sổ
  [300, 1800) s, 300 s đầu là giai đoạn khởi động (warm-up) để mạng đạt trạng thái có tải.
- Đầu ra: `tripinfo`, trạng thái đèn, vòng cảm ứng tức thời tại vạch dừng và vạch ra, `fcd` lọc trong bán kính 220 m
  có vị trí ngang, `lanechange-output`; thiết bị SSM đo PET chỉ bật ở tập chẩn đoán của đánh giá cuối.
- Mỗi lần chạy ghi `manifest.json`: mã commit, phiên bản SUMO, giá trị băm của đặc tả và mạng, seed, cấu hình, số
  teleport, số va chạm tách theo trên làn, trong nút và liên quan can thiệp, số xe chờ chèn lúc kết thúc.

**Nền tảng cần nắm.** Phân tích đầu ra mô phỏng ngẫu nhiên: lần lặp độc lập (replication), giai đoạn khởi động, số
seed cần thiết. Việc mọi đặc tả được chạy với cùng ngày nhu cầu và cùng seed gần với ý tưởng số ngẫu nhiên chung
(common random numbers) để giảm phương sai khi so sánh; tuy vậy luồng ngẫu nhiên không đồng bộ hoàn toàn khi hành vi
xe khác nhau. Khái niệm teleport của SUMO (xe kẹt quá `time-to-teleport` bị nhấc khỏi mạng) và vì sao không được giấu
nó bằng tùy chọn.

## 12. Bước 11: Lược đồ dữ liệu chung và hệ thống chỉ số

**Mục đích.** Đo mô phỏng giống quan sát đến đâu, bằng cùng một bộ hàm cho cả hai nguồn.

**Lược đồ chung.** Mười bảng (`schema_observed.py`, PLAN mục 5.1): số đếm rẽ 15 phút, sự kiện đèn, lượt qua vạch
dừng, ảnh chụp hàng chờ, vị trí ngang, hàng chờ giữa nút, lượt đi qua nút, chuỗi thời gian hàng chờ, sự kiện tìm khoảng
trống, độ trễ xe rẽ phải. Đầu ra mô phỏng được đổi sang đúng lược đồ này (`sim/outputs.py`), nên sai lệch không thể đến
từ việc hai bên tính chỉ số khác nhau. Các bảng của nhóm F2 chỉ suy từ quỹ đạo và tuyến, không đọc nhật ký can thiệp,
để định nghĩa áp dụng được cho video.

**Các chỉ số** (`src/thesis_sumo/metrics/`):

| Mã | Ý nghĩa | Hành vi đo |
|---|---|---|
| G0 (cổng GEH) | Cổng lọc, không tính điểm: tỷ lệ ô (15 phút x nhánh x hướng x loại xe) có GEH < 5 phải đạt ít nhất 0,85 | Nhu cầu |
| M1 (khoảng thời gian xả hàng) | Phân phối headway xả hàng sau khi xanh, theo loại xe | Năng lực thông qua |
| M2 (xuất phát sớm) | Tỷ lệ xe qua vạch trong 10 s cuối pha đỏ; độ trễ từ lúc xanh tới xe đầu tiên | 3 |
| M3 (vượt đèn đỏ) | Số vượt đỏ mỗi chu kỳ, tỷ số phương sai trên trung bình, tỷ lệ vượt đỏ | 1, 2 |
| M4 (vị trí ngang khi dừng) | Vị trí ngang của xe máy đang dừng lúc chuyển xanh; tỷ lệ và độ sâu dừng quá vạch | 4 |
| M5 (hàng chờ) | Chiều dài hàng chờ và mật độ xe máy lúc chuyển xanh | 4 |
| M6 (thời gian qua nút) | Thời gian qua nút và qua nhánh vào, theo hướng x loại xe | Toàn bộ |
| M7 (chờ giữa nút) | M7a số xe chờ giữa nút; M7b độ trễ giải phóng vùng chờ; M7c độ dốc tổn thất khởi động của hướng giao cắt theo số xe chờ | 10 |
| M8 (đi sai làn) | Tỷ lệ xe rẽ ở làn không có hướng ra, đọc tại đầu đoạn 30 m (trước khi xe có thể cắt về) | 5 |
| M9 (chặn làn rẽ phải liên tục) | M9a số xe không rẽ phải đứng chờ đỏ trên lane 0; M9b độ trễ và tỷ lệ xe rẽ phải bị chặn | 6 |
| M10 (đi trên vỉa hè) | Số xe máy trên vỉa hè mỗi chu kỳ | 7 |

Công thức GEH: $\mathrm{GEH} = \sqrt{2(m-c)^2/(m+c)}$, với $m$ là số đếm mô phỏng, $c$ là số đếm quan sát; ngưỡng 5
và tỷ lệ 85% theo hướng dẫn TAG M3.1 của Bộ Giao thông Anh.

**Nền tảng cần nắm.** Thống kê GEH trong hiệu chỉnh mô hình giao thông; headway bão hòa và lưu lượng bão hòa; tổn thất
khởi động (start-up lost time) theo lý thuyết dòng xe tại nút có đèn (Highway Capacity Manual); thống kê tóm tắt
(summary statistics) theo nghĩa của ABC.

## 13. Bước 12: Hàm khoảng cách, sàn nhiễu và điểm tổng

**Kỹ thuật** (`metrics/distance.py`):

- Chỉ số dạng **phân phối**: khoảng cách Wasserstein bậc 1 chia cho IQR của dữ liệu quan sát. Với hai phân phối một
  chiều, $W_1(F, G) = \int |F(x) - G(x)|\,dx$, tức diện tích giữa hai hàm phân phối tích lũy; nó có cùng đơn vị với
  biến, nên chia IQR để chuẩn hóa về không thứ nguyên. Nếu IQR bằng 0, mẫu số lùi về độ lệch chuẩn, trị tuyệt đối của
  trung bình, rồi 1.
- Chỉ số **vô hướng**: sai số tương đối $|x_{\text{sim}} - x_{\text{obs}}| / |x_{\text{obs}}|$.
- Biến đệm $D_{\text{empty}} = 2$: mọi khoảng cách theo ngày bị chặn trên ở 2, và khi một phía không có sự kiện nào thì
  khoảng cách bằng đúng 2. Thiếu quy tắc này, triệt tiêu một hành vi hiếm có thể rẻ hơn tái hiện nó sai mức. Hạn chế
  còn mở (câu hỏi cho GVHD trong chương 5): với tỷ lệ rất nhỏ, mô phỏng bằng 0 cho khoảng cách 1, còn mô phỏng gấp hơn
  hai lần quan sát cho 2, nên ép hành vi về 0 vẫn rẻ hơn.
- **Sàn nhiễu**: cùng khoảng cách tính giữa các ngày quan sát với nhau cho $d_{\text{day-day}}$ (sàn dưới 0,05). Mỗi chỉ
  số báo cáo bằng $R = d_{\text{sim-obs}} / d_{\text{day-day}}$. $R \approx 1$ nghĩa là mô phỏng lệch khỏi quan sát
  không nhiều hơn hai ngày quan sát lệch nhau. Đây là cách tách sai lệch của mô hình khỏi biến động tự nhiên.
- **Điểm tổng** $S$: trung bình có trọng số các khoảng cách; trọng số chia đều cho các nhóm M1 đến M10 có mặt, trong
  nhóm chia đều cho chỉ số con, rồi cho các khóa. $S = S_{\text{sourced}} + S_{\text{assumed}}$, tách phần từ mục tiêu
  có nguồn và phần từ mục tiêu giả định.

**Nền tảng cần nắm.** Khoảng cách Wasserstein và lý thuyết vận chuyển tối ưu (Villani, 2009); so sánh với khoảng cách
Kolmogorov-Smirnov; chuẩn hóa thang đo bằng thống kê bền vững (IQR); tối ưu đa mục tiêu và vô hướng hóa bằng tổng có
trọng số (weighted-sum scalarization), cùng nhược điểm của nó.

## 14. Bước 13: Tiêu chí đủ điều kiện

**Mục đích.** $S$ thấp chưa đủ: một lần chạy có thể có $S$ thấp vì xe bị loại do kẹt hoặc vì xe vi phạm va chạm nhau.

**Kỹ thuật** (`sim/runner.is_eligible`). Một lần chạy đủ điều kiện khi thỏa cả năm điều kiện: (i) không có teleport
nào không do va chạm; (ii) không còn xe chờ chèn vào mạng khi kết thúc; (iii) qua cổng G0; (iv) va chạm trên làn không
quá 4/h và va chạm trong nút không quá 142/h; (v) tối đa 1 va chạm liên quan can thiệp. Hai ngưỡng va chạm là
$\max(2, \lceil p_{90} \rceil)$ của B0 trên PROXY_D1 đến D3 x seed 1 đến 3, **đóng băng ngày 27/10/2026 trước vòng LLM
đầu tiên** và không đổi sau khi thấy kết quả LLM. Ý tưởng: bộ luật không được làm mô phỏng kém an toàn hơn chính mô hình
chuẩn. Một đặc tả đủ điều kiện khi mọi lần chạy của nó đủ điều kiện; nếu không có đặc tả nào đủ điều kiện, chọn theo số
xe kẹt trung bình mỗi giờ rồi theo $S$.

**Nền tảng cần nắm.** Tối ưu có ràng buộc và quy tắc chọn từ điển thứ tự (lexicographic); nguyên tắc đóng băng ngưỡng
trước khi thấy kết quả, tương tự đăng ký trước (preregistration), để tránh chỉnh ngưỡng theo kết quả.

## 15. Bước 14: Dữ liệu mục tiêu đại diện (PROXY) và chia dữ liệu

**Mục đích.** Kiểm thử toàn bộ quy trình khi chưa có video tại nút.

**Kỹ thuật** (`src/thesis_sumo/proxy/generate.py`, `data/proxy/targets.yaml`):

- Năm "ngày đại diện" PROXY_D1 đến D5 sinh theo **từng sự kiện phương tiện** từ bảng giá trị mục tiêu tổng hợp từ tài
  liệu. Mỗi giá trị mang nhãn bằng chứng: lấy từ tài liệu, chuyển giao từ bối cảnh khác (CG), hoặc giả định (GĐ). Ví
  dụ: lưu lượng tổng chuyển giao từ Mai và cộng sự (2019), chia nhánh giả định; tỷ lệ xe máy 0,865; headway bão hòa xe
  máy 0,254 s (Vu, 2015); các mục tiêu F2 đều giả định.
- Mô hình sinh: lượt đến theo **quá trình Poisson** theo loại xe x hướng x ô 15 phút; số xe vượt đỏ, xuất phát sớm, rẽ
  trái trái phép mỗi chu kỳ theo **phân phối nhị thức âm** (để có quá phân tán); headway xả hàng bằng headway bão hòa
  nhân hệ số khởi động theo vị trí và nhiễu lognormal; biến động giữa ngày bằng **hệ số ngày lognormal**, chuẩn hóa để
  trung bình năm ngày bằng giá trị danh nghĩa. Bộ sinh không đọc đầu ra SUMO.
- **Chia dữ liệu**: PROXY_D1 đến D3 để hiệu chỉnh; PROXY_D4, D5 chỉ để đánh giá cuối. LLM và Optuna không bao giờ thấy
  thống kê của D4, D5; mã báo lỗi nếu tên một ngày đánh giá xuất hiện trong văn bản phản hồi.

**Giới hạn phải nói rõ khi bảo vệ.** Dữ liệu PROXY không phải quan sát thực. Kết quả hiệu chỉnh trên các ngày này chỉ
cho biết quy trình vận hành được và mô phỏng khác mô hình chuẩn ở đâu, không cho biết mô phỏng giống giao thông thực
đến đâu.

**Nền tảng cần nắm.** Quá trình Poisson; phân phối nhị thức âm như hỗn hợp Poisson-Gamma; phân phối lognormal; tách
tập hiệu chỉnh và tập kiểm định (holdout), quá khớp (overfitting) và rò rỉ dữ liệu (data leakage).

## 16. Bước 15: Thiết kế so sánh

**Các phương án.** Mọi phương án qua cùng bộ kiểm tra, cùng bộ thực thi, cùng hàm đánh giá, cùng quy tắc chọn và cùng
ngân sách:

| Mã | Cấu trúc | Tham số |
|---|---|---|
| B0 | Mặc định SUMO, không luật có điều kiện | Mặc định |
| B1 | Viết tay, chuyển từ Saval và cộng sự (2023) | Viết tay |
| B2 | Cố định = B1 | Optuna |
| P1 | Cố định = B1 | LLM (`params_only`) |
| P2 | LLM sinh | LLM (`full`) |
| H | Cấu trúc tốt nhất của P2 | Optuna |

**Hai thí nghiệm.** E1 so sánh P1 với B2 trên cùng cấu trúc: LLM như một bộ tối ưu tham số. E2 so sánh B2, H, P2: giá
trị của cấu trúc do LLM sinh. Nếu H tốt hơn B2, cấu trúc của LLM có giá trị dù tham số do Optuna chọn. Thiết kế này cô
lập hai yếu tố (nguồn cấu trúc, nguồn tham số) theo kiểu thí nghiệm giai thừa không đầy đủ.

**Ngân sách bằng nhau.** 36 lần chạy SUMO mỗi phương án = 12 đặc tả x 3 ngày hiệu chỉnh x seed 1. Với LLM là 3 vòng x 4
mẫu; với Optuna là 12 thử nghiệm. Ngân sách lưu trên đĩa theo chiến dịch, nên chạy lại hay bị ngắt không làm vượt.

**Optuna** (`baselines/optuna_search.py`): bộ lấy mẫu TPE (Tree-structured Parzen Estimator), seed 0, 4 thử nghiệm
khởi đầu ngẫu nhiên thay cho mặc định 10 (với 12 thử nghiệm, mặc định để TPE chỉ còn 2 thử nghiệm có mô hình). Không
gian được **tham số hóa lại** để mọi thử nghiệm đều hợp lệ: `lcPushyGap` là tỷ lệ của `minGapLat`; $p_{\max} = p_0 +
u(1-p_0)$ với $u \in [0, 1]$; tỷ trọng các nguyên mẫu lấy trên đơn hình bằng **bẻ que** (stick-breaking). TPE mô hình
hóa $p(x \mid y)$ bằng hai mật độ, $\ell(x)$ cho các thử nghiệm tốt và $g(x)$ cho các thử nghiệm còn lại, rồi chọn điểm
tiếp theo cực đại tỷ số $\ell(x)/g(x)$, tương đương cực đại kỳ vọng cải thiện (expected improvement).

**Đánh giá cuối (dự kiến).** Chạy B0, B1, B2, P1, P2, H trên PROXY_D4, D5 với ít nhất 20 seed. Mỗi cặp so bằng kiểm
định **Mann-Whitney U** (phi tham số, không giả định phân phối chuẩn), hiệu chỉnh **Holm** cho so sánh bội, và kích
thước hiệu ứng **Cliff's delta** $\delta = P(X > Y) - P(X < Y)$. Kèm phân tích loại bỏ (ablation): tắt lần lượt từng
luật hoặc nhóm tham số. Nếu còn thời gian: đánh giá phương án tổ chức giao thông với B0 và mô hình đã hiệu chỉnh, so thứ
hạng bằng **Kendall tau**, ghi rõ là ngoại suy.

**So sánh trực quan với SUMO mặc định.** Đặt cạnh nhau quỹ đạo trong cùng một chu kỳ đèn ở ba nguồn (video, B0, bộ
luật đề xuất) và các số đếm trực tiếp (vượt đỏ, xuất phát sớm, xe chờ giữa nút, xe trên vỉa hè, xe qua vạch mỗi giờ).
Kỳ vọng là mô phỏng với bộ luật có các hành vi vi phạm mà B0 không có, ở mức gần số đếm thực tế hơn B0.

**Nền tảng cần nắm.** Tối ưu Bayes và TPE (Bergstra và cộng sự, 2011); Optuna (Akiba và cộng sự, 2019); tham số hóa
lại đơn hình; kiểm định Mann-Whitney (Mann và Whitney, 1947); hiệu chỉnh Holm (Holm, 1979); Cliff's delta (Cliff,
1993); Kendall tau (Kendall, 1938); thiết kế thí nghiệm với ngân sách tính toán bằng nhau.

## 17. Tái lập và kiểm thử phần mềm

Các kỹ thuật bảo đảm tái lập, cần nêu trong phần phương pháp:

- Mạng sinh từ script cộng tệp vá; `scenario_raw/` bất biến.
- Seed cố định ở mọi tầng: routeSampler, SUMO, bộ sinh số của từng luật, LLM, Optuna.
- `manifest.json` cho mỗi lần chạy với giá trị băm của đặc tả và mạng.
- Nhật ký LLM phát lại được; trạng thái vòng lặp và ngân sách lưu trên đĩa.
- Không bịa số liệu hiện trường: giá trị chưa đo để `null  # TODO_MEASURE`, mã báo lỗi khi gặp `null` bắt buộc.
- Kiểm thử `pytest` trên dữ liệu tổng hợp nhỏ cho bộ kiểm tra, bộ biên dịch, chỉ số; mỗi luật TraCI có một kịch bản
  chứng minh nó kích hoạt và được thực thi; kiểm tra `traci` và `libsumo` cho cùng kết quả.

## 18. Hiện trạng và các hạn chế đã biết (tính đến 22/11/2026)

- Chưa có số đo hiện trường và dữ liệu video. Mọi kết quả tính trên cấu hình đại diện và PROXY_D1 đến D5.
- Ba chiến dịch ngày 08/11 trên mạng 04/11 (B2, P1, P2 với `qwen3.5:9b`, prompt `v004`) **không có đặc tả nào đủ
  điều kiện**. $S$ nhỏ nhất: B2 1,1438; P1 1,2386; P2 1,1680. $S$ thấp hơn của P2 đến từ đặc tả bỏ bớt luật.
- Ở PROXY_D1 mọi đặc tả dựa trên B1 còn xe chờ chèn. Phân tích loại bỏ cho thấy nguyên nhân chính là `accel` 1,1 m/s²
  của xe máy trong B1, chuyển từ gia tốc cực đại của IDM trong Saval và cộng sự sang `accel` của Krauss (mặc định SUMO
  cho xe máy là 6 m/s²). Quyết định sửa B1 hay giữ nguyên chưa được đưa ra.
- Chưa chạy: P2 với prompt `v005`, phương án H, đánh giá cuối 20 seed trên D4, D5, đánh giá phương án tổ chức giao
  thông.
- Hạn chế của hàm khoảng cách với tỷ lệ rất nhỏ (mục 13) còn mở.
- Hai mục tiêu của M9 (chặn làn rẽ phải liên tục) chưa định nghĩa lại theo mô hình làn 30 m.

## 19. Bảng kiến thức nền tảng và tài liệu đọc thêm

| Chủ đề | Mục liên quan | Đọc gì | Xem trong dự án |
|---|---|---|---|
| Mô phỏng vi mô, SUMO | 3, 10, 11 | Lopez và cộng sự (2018), "Microscopic traffic simulation using SUMO"; sumo.dlr.de/docs | `scenario/`, `sim/` |
| Mô hình bám xe Krauss | 5 | Krauss (1998), luận án tiến sĩ, DLR/Đại học Köln | `param_bounds.yaml` nhóm carFollow |
| Chuyển làn và làn con | 5 | Erdmann (2015), "SUMO's lane-changing model"; Semrau và Erdmann (2016) | nhóm LC, sublane |
| Mạng SUMO, plain XML, đèn | 3 | Tài liệu SUMO: Networks/PlainXML, Traffic Lights, netconvert | `net/` |
| Nhu cầu từ số đếm | 4 | Tài liệu SUMO: Tools/Turns (routeSampler) | `demand/build_demand.py` |
| TraCI, speed mode, lane change mode | 10 | Tài liệu SUMO: TraCI, Change Vehicle State | `runtime/` |
| Mô hình tác tử cho Hà Nội | 2, 16 | Saval và cộng sự (2023), PLOS ONE | `rules/specs/B1_*.json`, Phụ lục B1 |
| Số liệu hành vi xe máy | 2, 15 | Mai và cộng sự (2019); Chu Cong Minh và cộng sự (2005); Zulkiffli và cộng sự (2023); Hsu và cộng sự (2024) | `data/proxy/targets.yaml` |
| Chỉ số an toàn thay thế, PET | 2, 12 | Allen và cộng sự (1978), Transportation Research Record 667 | M7b, thiết bị SSM |
| GEH | 12 | DfT, TAG Unit M3.1 | `metrics/g0_geh.py` |
| Wasserstein, vận chuyển tối ưu | 13 | Villani (2009), "Optimal Transport: Old and New" | `metrics/distance.py` |
| Suy luận dựa trên mô phỏng | 1, 13 | Beaumont, Zhang và Balding (2002) về ABC; McFadden (1989) về phương pháp mô-men mô phỏng | Toàn bộ vòng hiệu chỉnh |
| Tối ưu Bayes, TPE, Optuna | 16 | Bergstra và cộng sự (2011); Akiba và cộng sự (2019) | `baselines/optuna_search.py` |
| LLM như bộ tối ưu, tìm kiếm chương trình | 8 | Yang và cộng sự, "Large Language Models as Optimizers" (OPRO); Romera-Paredes và cộng sự (2024), FunSearch | `llm/loop.py` |
| Đầu ra có cấu trúc, JSON Schema | 6, 8 | json-schema.org; tài liệu Ollama về structured outputs | `rules/schema/`, `llm/client.py` |
| Thống kê phi tham số | 16 | Mann và Whitney (1947); Holm (1979); Cliff (1993); Kendall (1938) | `evaluate.py` |
| Phân phối đếm | 7, 15 | Giáo trình thống kê về Poisson, nhị thức âm, quá phân tán | `proxy/generate.py`, M3 |

## 20. Câu hỏi tự kiểm tra

Trả lời được các câu dưới đây thì đủ để bảo vệ phần phương pháp.

1. Vì sao bài toán này không giải được chỉ bằng Optuna? Phần nào của $\theta$ Optuna không tìm được?
2. Vì sao LLM không được gọi trong lúc mô phỏng? Nêu hai lý do.
3. Khác nhau giữa tham số tĩnh và luật có điều kiện là gì? Cho một ví dụ mỗi loại trong luận văn.
4. Biến đệm là gì? Nêu biến đệm của `swarm_red_running` và hậu quả nếu thiếu từng biến.
5. Vì sao `queue_space_seeking` phải rút một lần cho mỗi xe? Viết biểu thức xác suất nếu rút ở mỗi bước.
6. Tỷ số phương sai trên trung bình trong M3 đo điều gì, và vì sao nó liên quan tới tham số $k$?
7. Tại sao phải tách lớp vi phạm bằng `custom1`, `custom2` thay vì chỉ đổi tham số vType?
8. Speed mode bit 3 và bit 4 làm gì? Vì sao luật vượt đỏ chỉ xóa bit 4?
9. Nguyên tắc "chỉ giữ, không đẩy" giới hạn luật `illegal_left_box` ở đâu? Cái giá của nguyên tắc này là gì?
10. Vì sao chia Wasserstein-1 cho IQR? $R = d_{\text{sim-obs}}/d_{\text{day-day}}$ bằng 1 có nghĩa gì?
11. $D_{\text{empty}}$ ngăn được kiểu "gian lận" nào của bộ tối ưu, và còn hở trường hợp nào?
12. Vì sao ngưỡng va chạm phải đóng băng trước vòng LLM đầu tiên?
13. Năm điều kiện đủ điều kiện là gì? Vì sao $S$ thấp chưa đủ để chấp nhận một đặc tả?
14. Dữ liệu PROXY được sinh thế nào? Kết luận nào được rút ra từ nó và kết luận nào không?
15. E1 và E2 trả lời câu hỏi nào? Vì sao cần phương án H?
16. Vì sao ngân sách phải bằng nhau giữa LLM và Optuna, và vì sao đặc tả không hợp lệ không tính vào ngân sách?
17. TPE chọn điểm tiếp theo như thế nào? Vì sao đổi số thử nghiệm khởi đầu từ 10 xuống 4?
18. Vì sao dùng Mann-Whitney thay cho t-test, và Holm sửa vấn đề gì?
19. Ràng buộc phủ luật ở prompt `v005` sửa vấn đề gì đã quan sát được ở P2?
20. Vì sao `accel` 1,1 m/s² của Saval làm xe máy trong SUMO xả hàng quá chậm? Liên hệ khác nhau giữa IDM và Krauss.
