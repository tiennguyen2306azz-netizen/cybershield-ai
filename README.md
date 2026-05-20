<div align="center">

# 🛡️ CYBERSHIELD AI

### AI-Powered Phishing Link Analyzer

<img src="https://img.shields.io/badge/Python-3.9+-blue?style=for-the-badge&logo=python&logoColor=white" />
<img src="https://img.shields.io/badge/Flask-2.0+-green?style=for-the-badge&logo=flask&logoColor=white" />
<img src="https://img.shields.io/badge/NVIDIA_AI-GPT_120B-76B900?style=for-the-badge&logo=nvidia&logoColor=white" />
<img src="https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge" />

**Hệ thống phân tích và phát hiện link phishing (lừa đảo) bằng Trí tuệ Nhân tạo**

[Demo trực tiếp](#demo) · [Cài đặt](#cài-đặt) · [Tính năng](#tính-năng) · [Tác giả](#tác-giả)

</div>

---

## 📋 Giới thiệu

**CyberShield AI** là ứng dụng web giúp người dùng kiểm tra tính an toàn của bất kỳ đường link nào trước khi truy cập. Hệ thống kết hợp **5 module quét song song** và **AI NVIDIA GPT-120B** để đưa ra đánh giá toàn diện.

### 🎯 Vấn đề giải quyết
- Việt Nam có **hơn 15 triệu** nạn nhân lừa đảo qua mạng (BKAV 2024)
- Phần lớn bắt đầu từ **link giả mạo** gửi qua Zalo, Messenger, SMS
- Người dùng thường không có kiến thức kỹ thuật để nhận biết

---

## ✨ Tính năng

| Module | Mô tả |
|--------|-------|
| 🔍 **Heuristic Scanner** | Phân tích cấu trúc URL, Typo-squatting (Levenshtein Distance), Homograph Attack, URL Shortener, Suspicious TLD |
| 🌐 **WHOIS Lookup** | Kiểm tra tuổi tên miền, nhà đăng ký, quốc gia. Cảnh báo domain mới < 30 ngày |
| 🔒 **SSL/TLS Check** | Xác minh chứng chỉ SSL, phát hiện Self-Signed Certificate |
| 📋 **HTTP Headers Audit** | Kiểm tra CSP, HSTS, X-Frame-Options, X-Content-Type-Options, X-XSS-Protection |
| 🧠 **AI NVIDIA GPT-120B** | Tổng hợp dữ liệu từ 4 module, phân tích chuyên sâu bằng LLM 120 tỷ tham số |

### 🎨 Giao diện
- **Cyberpunk UI** với hiệu ứng neon, glassmorphism
- **3 trạng thái màu**: 🟢 An toàn / 🟡 Nghi ngờ / 🔴 Nguy hiểm
- **Radar animation** khi quét
- **Terminal log** mô phỏng tiến trình quét
- **Lịch sử quét** lưu trên LocalStorage

---

## 🚀 Cài đặt

### Yêu cầu
- Python 3.9+

### Bước 1: Clone repository
```bash
git clone https://github.com/YOUR_USERNAME/cybershield-ai.git
cd cybershield-ai
```

### Bước 2: Cài đặt thư viện
```bash
pip install -r requirements.txt
```

### Bước 3: Cấu hình API Key
Tạo file `.env` trong thư mục gốc:
```env
NVIDIA_API_KEY=your_nvidia_api_key_here
NVIDIA_BASE_URL=https://integrate.api.nvidia.com/v1
MODEL_NAME=openai/gpt-oss-120b
```

### Bước 4: Chạy ứng dụng
```bash
python app.py
```

Mở trình duyệt tại `http://localhost:5000` 🎉

### Chia sẻ qua Internet (Ngrok)
```bash
ngrok http 5000
```

---

## 🛠️ Công nghệ sử dụng

| Thành phần | Công nghệ |
|------------|-----------|
| Backend | Python Flask |
| Frontend | HTML5, CSS3, JavaScript |
| AI Engine | NVIDIA AI API (GPT-OSS 120B) |
| UI Style | Cyberpunk Glassmorphism |
| Libraries | python-whois, OpenAI SDK, requests |
| Font | Orbitron, Plus Jakarta Sans, JetBrains Mono |

---

## 📁 Cấu trúc dự án

```
cybershield-ai/
├── app.py                 # Flask server + 5 module quét
├── requirements.txt       # Thư viện Python
├── .env                   # API Key (không push lên Git)
├── .gitignore             # Loại trừ file nhạy cảm
├── templates/
│   └── index.html         # Giao diện chính
└── static/
    ├── style.css          # Cyberpunk CSS
    └── app.js             # Client-side logic
```

---

## 📸 Screenshots

> *Thêm screenshots vào đây*

---

## 👨‍💻 Tác giả

**CyberShield AI Team**
- 🎓 Sinh viên An toàn Thông tin
- 💻 AI Developer
- 📧 Email: tiennguyen2306azz@gmail.com

---

## 📄 License

Dự án này được phân phối dưới giấy phép [MIT License](LICENSE).

---

<div align="center">

**⭐ Nếu thấy hữu ích, hãy cho mình một Star nhé! ⭐**

Made with ❤️ by CyberShield AI Team

</div>
