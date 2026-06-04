<div align="center">

# 🛡️ CYBERSHIELD AGENT

### Động Cơ Đánh Giá và Chẩn Đoán Link Độc Hại Bằng Trí Tuệ Nhân Tạo NVIDIA 120B

<img src="https://img.shields.io/badge/Python-3.9+-blue?style=for-the-badge&logo=python&logoColor=white" />
<img src="https://img.shields.io/badge/Flask-2.0+-green?style=for-the-badge&logo=flask&logoColor=white" />
<img src="https://img.shields.io/badge/NVIDIA_AI-GPT_120B-76B900?style=for-the-badge&logo=nvidia&logoColor=white" />
<img src="https://img.shields.io/badge/Vercel-Production-black?style=for-the-badge&logo=vercel&logoColor=white" />
<img src="https://img.shields.io/badge/UI_Style-Cyberpunk_Neon-00F2FE?style=for-the-badge" />

**Hệ thống phân tích, bóc tách mã độc và phát hiện liên kết lừa đảo (phishing) chuyên sâu toàn diện.**

[Xem Bản Live](https://cybershieldagent.vercel.app) · [Cài Đặt Chạy Máy Cục Bộ](#-cài-đặt-chạy-máy-cục-bộ) · [Hệ Thống 7 Module Quét](#-hệ-thống-7-module-quét-chuyên-nghiệp) · [Cấu Trúc Tường Lửa WAF](#-tường-lửa-ứng-dụng-web-waf--anti-pentest-middleware)

</div>

---

## 📋 Giới thiệu tổng quan

**CyberShield Agent** là một pháo đài bảo mật kỹ thuật số chuyên sâu, giúp người dùng phổ thông lẫn các kỹ sư an ninh mạng phân tích, phát hiện và bóc gỡ các hành vi ẩn giấu của liên kết lừa đảo trực tuyến (phishing/malicious links). 

Ứng dụng kết hợp sức mạnh của **7 Module quét tĩnh/động kỹ thuật**, tích hợp dữ liệu cơ sở dữ liệu mối đe dọa toàn cầu (VirusTotal) và kết xuất báo cáo phân tích thông minh dựa trên **Mô hình Trí tuệ Nhân tạo cao cấp NVIDIA 120B (GPT-OSS)**.

---

## 🛡️ Hệ thống 7 Module Quét Chuyên Nghiệp

| Module | Cơ Chế Phân Tích & Chẩn Đoán |
|---|---|
| 🔍 **Heuristic Static Scanner** | Phân tích cấu trúc URL, Homograph Attack (ký tự Unicode giả dạng), Typo-squatting (đo khoảng cách Levenshtein phát hiện nhái tên miền), Shannon Entropy (phát hiện tên miền rác sinh tự động bằng máy DGA) và bóc gỡ dịch vụ rút gọn link. |
| 🌐 **WHOIS Registry Tracker** | Truy xuất ngày đăng ký, nhà cung cấp, quốc gia tên miền. Cảnh báo nguy hiểm cấp độ đỏ cho các tên miền mới đăng ký dưới 30 ngày (đặc trưng của chiến dịch phishing nhanh). |
| 🔒 **SSL/TLS Certificate Validator** | Kết nối cổng 443 kiểm tra tính pháp lý của chứng chỉ số, cảnh báo tức thì nếu chứng chỉ hết hạn, không hợp lệ hoặc sử dụng chứng chỉ tự ký (Self-Signed SSL). |
| 📋 **HTTP Headers & Hop Tracker** | Gửi yêu cầu HTTP ngầm, bắt mã trạng thái và theo dõi chi tiết **Chuỗi chuyển hướng (Redirection Chain Map)** từng hop trung gian. Audit các tiêu đề an toàn bắt buộc (CSP, HSTS, X-Frame-Options...). |
| 🧬 **HTML Clone & Copyright Audit** | Tải mã nguồn HTML kiểm tra các ô thu thập thông tin nhạy cảm (Password/OTP), tỷ lệ đạo nhái tài nguyên (Asset Leeching), đánh cắp bản quyền thương hiệu và các kỹ thuật né tránh (Iframe ẩn, Meta Refresh). |
| ⚙️ **JS Behavioral & Decryption Engine** | Phát hiện các mã script theo dõi (Keylogger, Anti-Copy, chặn chuột phải), các hàm né tránh máy quét (chống DevTools/chống Debugger) và **bóc trần 4 loại mã hóa/làm rối JavaScript (JSFuck, AAEncode/JJEncode mặt cười, Obfuscator.io, Packed Script)**. |
| 📬 **DNS Mail Integrity Scanner** | Kiểm tra cấu hình bản ghi máy chủ nhận thư (DNS MX Records), hỗ trợ cảnh báo đỏ nguy cấp đối với các trang web mạo danh thương hiệu lớn nhưng thiếu MX Records nhận mail. |

---

## 🔒 Tường Lửa Ứng Dụng Web (WAF) & Anti-Pentest Middleware

Để đảm bảo an toàn tuyệt đối cho chính máy chủ ứng dụng trước các hacker và pentester chuyên nghiệp, **CyberShield Agent** tích hợp trực tiếp lớp middleware phòng thủ chủ động:

* **Chống Dò Quét Tự Động (Anti-Scanner):** Nhận dạng và cấm truy cập ngay lập tức các User-Agent của công cụ pentest tự động (`sqlmap`, `nikto`, `dirbuster`, `nmap`, `nessus`, `acunetix`...).
* **Chống Tấn Công Tập Tin Hệ Thống (LFI/RFI WAF):** Ngăn chặn các nỗ lực truy cập thư mục nhạy cảm (`/etc/passwd`, `.env`, `.git`, `wp-admin`...) và trả về phản hồi 403 Forbidden mang phong cách Cyberpunk độc đáo.
* **Chống Tấn Công Injection:** Bộ lọc RegExp phát hiện và vô hiệu hóa SQL Injection (`UNION SELECT`) và Cross-Site Scripting (`<script>`) truyền qua query/form.
* **SSRF Shield (Server-Side Request Forgery):** Cơ chế phân giải DNS địa chỉ IP mục tiêu trước khi gửi request. Chặn đứng tuyệt đối việc bắt máy chủ quét chính nó hoặc truy cập dải mạng nội bộ riêng tư (RFC 1918, Loopback `127.0.0.1`, Link-local `169.254.169.254`).

---

## 🎨 Giao Diện Cyberpunk Neon & Responsive Di Động Hoàn Hảo

* **Aesthetic Cyberpunk:** Thiết kế tối tân với hiệu ứng kính mờ (Glassmorphism), hạt chuyển động nền tinh tú, và hệ màu Tailored HSL phát sáng.
* **Responsive Drawer (Mobile):** Trên di động, phần Lịch sử quét chuyển đổi mượt mà thành một khay trượt drawer kính mờ từ cạnh trái sang có lớp nền phủ tối (`backdrop-filter: blur(8px)`).
* **Swipeable Horizontal Tabs:** Các tab chẩn đoán terminal (`AI REPORT`, `HEURISTICS`, `WHOIS & DNS`, `SSL CERT`...) trên di động được gom vào một dòng duy nhất hỗ trợ vuốt ngang cảm ứng mượt mà, không bị bẻ dòng.
* **Lịch Sử Riêng Tư 100%:** Lịch sử quét của người dùng được lưu trữ cục bộ trên trình duyệt cá nhân bằng `LocalStorage` (Không lưu trên database, bảo mật quyền riêng tư tuyệt đối).
* **Vòng đo Rủi ro (Circular Gauge):** Hoạt họa tăng điểm mượt mà theo 3 mức màu chỉ thị trực quan: 🟢 An toàn / 🟡 Nghi ngờ / 🔴 Nguy hiểm.

---

## 🚀 Cài Đặt Chạy Máy Cục Bộ

### Yêu cầu chuẩn bị
* Python 3.9 trở lên
* Tài khoản lấy API Key NVIDIA AI và VirusTotal (Tùy chọn)

### Bước 1: Tải mã nguồn về máy
```bash
git clone https://github.com/tiennguyen2306azz-netizen/cybershield-ai.git
cd cybershield-ai
```

### Bước 2: Cài đặt các thư viện Python
```bash
pip install -r requirements.txt
```

### Bước 3: Cấu hình khóa bảo mật API
Tạo tệp `.env` trong thư mục gốc của dự án:
```env
NVIDIA_API_KEY=your_nvidia_api_key_here
NVIDIA_BASE_URL=https://integrate.api.nvidia.com/v1
MODEL_NAME=openai/gpt-oss-120b
VIRUSTOTAL_API_KEY=your_virustotal_api_key_here
```
*(Lưu ý: Tệp `.env` đã được cấu hình trong `.gitignore` để không bao giờ bị đẩy lên GitHub, bảo vệ an toàn API key của bạn).*

### Bước 4: Khởi chạy Server
```bash
python app.py
```
Mở trình duyệt web của bạn và truy cập địa chỉ: `http://localhost:5000` 🎉

---

## 📁 Cấu Trúc Dự Án
```
cybershield-ai/
├── app.py                 # Flask Server tích hợp WAF, SSRF Shield & 7 Module Quét
├── requirements.txt       # Danh sách thư viện Python cần dùng
├── .env                   # Tệp lưu API Key bí mật (Cá nhân tự cấu hình)
├── .gitignore             # Danh sách loại trừ các tệp nhạy cảm
├── templates/
│   └── index.html         # Giao diện chính responsive di động, Mobile Top Bar
└── static/
    ├── style.css          # CSS thiết kế Cyberpunk Glassmorphism & Media Queries
    ├── app.js             # Logic JS điều khiển client-side, Drawer đóng mở tự động
    └── logo.png           # Biểu tượng CyberShield Agent chính thức
```

---

## 👨‍💻 Bản Quyền và Phát Triển
* Dự án được phát triển và tối ưu hóa bởi **CyberShield Agent Team**.
* Quyền riêng tư của người dùng là tối cao — Hệ thống không lưu trữ bất kỳ lịch sử duyệt/quét nào của bạn trên máy chủ trung gian.

---

<div align="center">

**⭐ Nếu thấy dự án này hữu ích, hãy cho mình một Star nhé! ⭐**

Made with ❤️ by CyberShield Agent Team

</div>
