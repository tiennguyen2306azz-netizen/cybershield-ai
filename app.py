import os
import re
import ssl
import socket
import urllib.parse
from datetime import datetime, timezone
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from dotenv import load_dotenv
from openai import OpenAI

# Tải cấu hình từ .env
load_dotenv()

app = Flask(__name__, template_folder="templates", static_folder="static")
CORS(app)

# Cấu hình API NVIDIA từ Env
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY")
NVIDIA_BASE_URL = os.getenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "openai/gpt-oss-120b")

# =============================================================================
# CƠ SỞ DỮ LIỆU TĨNH: Các pattern lừa đảo phổ biến tại Việt Nam
# =============================================================================

# Danh sách các thương hiệu phổ biến thường bị giả mạo ở Việt Nam
POPULAR_BRANDS = {
    "facebook": "facebook.com", "google": "google.com", "shopee": "shopee.vn",
    "momo": "momo.vn", "vietcombank": "vietcombank.com.vn", "garena": "garena.vn",
    "techcombank": "techcombank.com.vn", "bidv": "bidv.com.vn", "tiki": "tiki.vn",
    "lazada": "lazada.vn", "netflix": "netflix.com", "telegram": "telegram.org",
    "zalo": "zalo.me", "vng": "vng.com.vn", "mbbank": "mbbank.com.vn",
    "acb": "acb.com.vn", "sacombank": "sacombank.com.vn", "agribank": "agribank.com.vn",
    "apple": "apple.com", "microsoft": "microsoft.com", "paypal": "paypal.com",
    "instagram": "instagram.com", "tiktok": "tiktok.com", "twitter": "twitter.com",
    "vnpay": "vnpay.vn", "zalopay": "zalopay.vn", "viettel": "viettel.vn",
    "vingroup": "vingroup.net", "fpt": "fpt.vn", "grab": "grab.com",
    "shopify": "shopify.com", "amazon": "amazon.com"
}

# Danh sách trắng: các tên miền uy tín KHÔNG BAO GIỜ bị đánh dấu nguy hiểm
TRUSTED_DOMAINS = [
    "google.com", "youtube.com", "facebook.com", "instagram.com", "twitter.com",
    "x.com", "tiktok.com", "linkedin.com", "reddit.com", "wikipedia.org",
    "github.com", "stackoverflow.com", "microsoft.com", "apple.com",
    "amazon.com", "netflix.com", "spotify.com", "discord.com", "telegram.org",
    "shopee.vn", "lazada.vn", "tiki.vn", "momo.vn", "grab.com",
    "vietcombank.com.vn", "techcombank.com.vn", "bidv.com.vn", "mbbank.com.vn",
    "acb.com.vn", "sacombank.com.vn", "agribank.com.vn", "vnpay.vn",
    "zalopay.vn", "zalo.me", "viettel.vn", "fpt.vn", "fpt.edu.vn",
    "vingroup.net", "garena.vn", "vng.com.vn", "paypal.com", "shopify.com",
    "cloudflare.com", "adobe.com", "zoom.us", "slack.com", "notion.so",
    "twitch.tv", "pinterest.com", "ebay.com", "yahoo.com", "bing.com",
    "baidu.com", "whatsapp.com", "viber.com", "skype.com",
    "gov.vn", "edu.vn", "chinhphu.vn"
]

# TLD (Top Level Domain) thường bị lạm dụng bởi kẻ lừa đảo
SUSPICIOUS_TLDS = [
    ".xyz", ".top", ".club", ".online", ".site", ".icu", ".buzz", ".tk",
    ".ml", ".ga", ".cf", ".gq", ".work", ".click", ".link", ".info",
    ".cam", ".rest", ".monster", ".sbs", ".cfd", ".quest"
]

# Dịch vụ rút gọn URL (thường dùng để che giấu link gốc)
URL_SHORTENERS = [
    "bit.ly", "tinyurl.com", "t.co", "goo.gl", "ow.ly", "is.gd",
    "buff.ly", "adf.ly", "bc.vc", "j.mp", "rb.gy", "shorturl.at",
    "cutt.ly", "s.id", "shorten.asia", "rebrand.ly", "t.ly"
]

# Từ khóa đáng ngờ trong đường dẫn URL (thường liên quan đến lừa đảo)
SUSPICIOUS_KEYWORDS = [
    "login", "signin", "verify", "update", "secure", "account", "confirm",
    "banking", "wallet", "password", "credential", "authenticate", "suspend",
    "unlock", "restore", "recover", "otp", "prize", "winner", "gift",
    "reward", "bonus", "free", "claim", "urgent", "limited", "offer",
    "naptien", "napthe", "khuyenmai", "quatang", "trunghuong", "dangky",
    "xacminh", "taikhoan", "matkhau", "chuyentien", "nhanqua"
]

# Ký tự Homograph (Unicode giả dạng ký tự Latin - rất nguy hiểm!)
HOMOGRAPH_MAP = {
    'а': 'a', 'е': 'e', 'і': 'i', 'о': 'o', 'р': 'p', 'с': 'c',
    'у': 'y', 'х': 'x', 'ѕ': 's', 'ԁ': 'd', 'ɡ': 'g', 'ɑ': 'a',
    'ο': 'o', 'τ': 't', 'ν': 'v', 'к': 'k', 'н': 'h', 'т': 't'
}


def get_levenshtein_distance(s1, s2):
    """Tính khoảng cách Levenshtein giữa hai chuỗi để phát hiện giả mạo tên miền"""
    if len(s1) < len(s2):
        return get_levenshtein_distance(s2, s1)
    if len(s2) == 0:
        return len(s1)
    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    return previous_row[-1]


# =============================================================================
# MODULE 1: PHÂN TÍCH HEURISTIC NÂNG CAO (Quét tĩnh cấu trúc URL)
# =============================================================================

def analyze_domain_heuristics(url):
    """Phân tích tĩnh nâng cao các đặc trưng của URL"""
    results = {
        "status": "SAFE",
        "warnings": [],
        "risk_score": 0,
        "brand_impersonated": None,
        "details": {}
    }

    try:
        # Chuẩn hóa URL
        original_url = url
        if not url.startswith(("http://", "https://")):
            url = "https://" + url

        parsed = urllib.parse.urlparse(url)
        domain = parsed.netloc.lower()
        path = parsed.path.lower()
        query = parsed.query.lower()
        full_url_lower = url.lower()

        # Xóa cổng nếu có
        if ":" in domain:
            domain = domain.split(":")[0]

        results["details"]["protocol"] = parsed.scheme
        results["details"]["domain"] = domain
        results["details"]["path"] = parsed.path
        results["details"]["query"] = parsed.query

        # --- CHECK 1: Sử dụng IP trực tiếp ---
        ip_pattern = re.compile(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$")
        if ip_pattern.match(domain):
            results["warnings"].append("🚨 Đường dẫn sử dụng **địa chỉ IP trực tiếp** thay vì tên miền chuẩn. Đây là kỹ thuật phổ biến để tránh bị truy vết và thường gặp ở các link phát tán mã độc.")
            results["risk_score"] += 40
            results["status"] = "SUSPICIOUS"

        # --- CHECK 2: Quá nhiều Subdomain ---
        subdomains = domain.split(".")
        if len(subdomains) > 4:
            results["warnings"].append(f"⚠️ Tên miền chứa **{len(subdomains)} tầng subdomain** (bất thường). Kỹ thuật này thường dùng để nhúng từ khóa giả mạo ở đầu, ví dụ: `facebook.login.evil-site.com`.")
            results["risk_score"] += 20
            results["status"] = "SUSPICIOUS"

        # --- CHECK 3: Ký tự '@' trong URL ---
        if "@" in parsed.netloc:
            results["warnings"].append("🚨 URL chứa ký tự **'@'** trong phần tên miền. Đây là kỹ thuật che giấu tên miền thật (phần trước @ bị trình duyệt bỏ qua, phần sau mới là đích thực).")
            results["risk_score"] += 35
            results["status"] = "DANGEROUS"

        # --- CHECK 4: Phát hiện URL Shortener ---
        for shortener in URL_SHORTENERS:
            if domain == shortener or domain.endswith("." + shortener):
                results["warnings"].append(f"⚠️ Đường dẫn sử dụng **dịch vụ rút gọn URL ({shortener})**. Link rút gọn che giấu hoàn toàn đích đến thực sự, thường bị kẻ xấu lợi dụng để phát tán link lừa đảo.")
                results["risk_score"] += 25
                results["status"] = "SUSPICIOUS"
                break

        # --- CHECK 5: TLD đáng ngờ ---
        for tld in SUSPICIOUS_TLDS:
            if domain.endswith(tld):
                results["warnings"].append(f"⚠️ Tên miền sử dụng đuôi **`{tld}`** — đây là loại TLD rẻ tiền, thường xuyên bị lạm dụng để tạo trang lừa đảo do chi phí đăng ký gần bằng 0.")
                results["risk_score"] += 15
                results["status"] = "SUSPICIOUS"
                break

        # --- CHECK 6: Phát hiện tấn công Homograph (Unicode giả dạng) ---
        homograph_found = []
        for char in domain:
            if char in HOMOGRAPH_MAP:
                homograph_found.append(f"'{char}' → '{HOMOGRAPH_MAP[char]}'")
        if homograph_found:
            results["warnings"].append(f"🚨 **PHÁT HIỆN TẤN CÔNG HOMOGRAPH!** Tên miền chứa ký tự Unicode giả dạng chữ Latin: {', '.join(homograph_found)}. Đây là kỹ thuật lừa đảo cực kỳ tinh vi, khiến tên miền giả trông giống hệt tên miền thật dưới mắt thường.")
            results["risk_score"] += 50
            results["status"] = "DANGEROUS"

        # --- CHECK 7: Từ khóa đáng ngờ trong URL ---
        found_keywords = []
        for keyword in SUSPICIOUS_KEYWORDS:
            if keyword in domain or keyword in path or keyword in query:
                found_keywords.append(keyword)
        if found_keywords:
            kw_list = ", ".join([f"`{k}`" for k in found_keywords[:5]])
            results["warnings"].append(f"⚠️ URL chứa các **từ khóa nhạy cảm**: {kw_list}. Các từ khóa này thường xuất hiện trong các trang lừa đảo thu thập thông tin đăng nhập hoặc dụ dỗ nhận thưởng.")
            results["risk_score"] += len(found_keywords) * 5
            if results["status"] == "SAFE":
                results["status"] = "SUSPICIOUS"

        # --- CHECK 8: Giao thức HTTP (không mã hóa) ---
        if parsed.scheme == "http":
            results["warnings"].append("⚠️ Đường dẫn sử dụng giao thức **HTTP** (không mã hóa). Mọi dữ liệu bạn nhập (mật khẩu, thẻ tín dụng) sẽ bị truyền đi dưới dạng bản rõ, có thể bị đọc trộm bởi hacker trên cùng mạng.")
            results["risk_score"] += 15

        # --- CHECK 9: Độ dài URL bất thường ---
        if len(url) > 150:
            results["warnings"].append(f"⚠️ Độ dài URL bất thường (**{len(url)} ký tự**). Các URL dài bất thường thường chứa tham số mã hóa để theo dõi nạn nhân hoặc nhúng payload tấn công.")
            results["risk_score"] += 10

        # --- CHECK 10: Giả mạo thương hiệu (Typo-squatting) ---
        domain_clean = re.sub(r'[^a-z]', '', domain.split(".")[0])
        for brand_key, brand_domain in POPULAR_BRANDS.items():
            # Nếu khớp chính xác thương hiệu thì bỏ qua
            if domain == brand_domain or domain.endswith("." + brand_domain):
                continue
            # Kiểm tra nếu tên thương hiệu xuất hiện trong domain nhưng domain không phải chính hãng
            if brand_key in domain and domain != brand_domain:
                results["warnings"].append(f"🚨 Tên miền `{domain}` **chứa từ khóa thương hiệu '{brand_key}'** nhưng KHÔNG phải là trang chính thức `{brand_domain}`. Có dấu hiệu giả mạo thương hiệu để lừa đảo!")
                results["brand_impersonated"] = brand_domain
                results["risk_score"] += 45
                results["status"] = "DANGEROUS"
                break
            # Tính khoảng cách Levenshtein
            dist = get_levenshtein_distance(domain_clean, brand_key)
            if 0 < dist <= 2 and len(domain_clean) >= len(brand_key) - 1:
                results["warnings"].append(f"🚨 Tên miền `{domain}` có cấu trúc **rất giống** thương hiệu chính thức `{brand_domain}` (chỉ khác {dist} ký tự). Nghi ngờ cao là giả mạo tên miền (Typo-squatting)!")
                results["brand_impersonated"] = brand_domain
                results["risk_score"] += 45
                results["status"] = "DANGEROUS"
                break

        # Cập nhật trạng thái cuối
        if results["risk_score"] >= 50:
            results["status"] = "DANGEROUS"
        elif results["risk_score"] >= 20:
            results["status"] = "SUSPICIOUS"

    except Exception as e:
        results["warnings"].append(f"❌ Lỗi phân tích tĩnh: {str(e)}")

    return results


# =============================================================================
# MODULE 2: KIỂM TRA WHOIS - TUỔI TÊN MIỀN
# =============================================================================

def check_whois(domain):
    """Kiểm tra thông tin WHOIS để xác định tuổi tên miền"""
    result = {"available": False, "data": {}, "warnings": [], "risk_score": 0}
    try:
        import whois
        # Loại bỏ subdomain, chỉ lấy domain chính
        parts = domain.split(".")
        if len(parts) > 2:
            # Xử lý TLD có 2 phần (ví dụ: .com.vn)
            if parts[-2] in ["com", "co", "org", "net", "edu", "gov"]:
                main_domain = ".".join(parts[-3:])
            else:
                main_domain = ".".join(parts[-2:])
        else:
            main_domain = domain

        w = whois.whois(main_domain)

        if w and w.domain_name:
            result["available"] = True
            
            # Lấy ngày đăng ký
            creation_date = w.creation_date
            if isinstance(creation_date, list):
                creation_date = creation_date[0]

            expiration_date = w.expiration_date
            if isinstance(expiration_date, list):
                expiration_date = expiration_date[0]

            registrar = w.registrar if w.registrar else "Không rõ"
            country = w.country if w.country else "Không rõ"

            result["data"]["registrar"] = registrar
            result["data"]["country"] = country

            if creation_date:
                result["data"]["creation_date"] = str(creation_date)
                # Tính tuổi tên miền
                now = datetime.now()
                if hasattr(creation_date, 'date'):
                    age_days = (now - creation_date.replace(tzinfo=None)).days
                else:
                    age_days = -1

                result["data"]["age_days"] = age_days

                if 0 <= age_days <= 30:
                    result["warnings"].append(f"🚨 Tên miền **mới đăng ký chỉ {age_days} ngày trước**! Đây là dấu hiệu cực kỳ đáng ngờ — phần lớn các trang lừa đảo được tạo mới và tồn tại rất ngắn (dưới 30 ngày).")
                    result["risk_score"] += 40
                elif 0 <= age_days <= 90:
                    result["warnings"].append(f"⚠️ Tên miền khá mới, chỉ mới **{age_days} ngày tuổi** (dưới 3 tháng). Các trang web uy tín thường có tuổi đời lâu hơn.")
                    result["risk_score"] += 20
                elif age_days > 365:
                    result["data"]["age_note"] = f"Tên miền đã tồn tại {age_days // 365} năm — tín hiệu tích cực."

            if expiration_date:
                result["data"]["expiration_date"] = str(expiration_date)

    except Exception as e:
        result["data"]["error"] = f"Không thể truy xuất WHOIS: {str(e)}"

    return result


# =============================================================================
# MODULE 3: KIỂM TRA CHỨNG CHỈ SSL/TLS
# =============================================================================

def check_ssl_certificate(domain):
    """Kiểm tra chứng chỉ SSL/TLS của tên miền"""
    result = {"available": False, "data": {}, "warnings": [], "risk_score": 0}
    try:
        # Loại bỏ port nếu có
        hostname = domain.split(":")[0]

        context = ssl.create_default_context()
        with socket.create_connection((hostname, 443), timeout=5) as sock:
            with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                cert = ssock.getpeercert()
                result["available"] = True

                # Lấy thông tin issuer
                issuer_dict = dict(x[0] for x in cert.get("issuer", []))
                subject_dict = dict(x[0] for x in cert.get("subject", []))
                
                issuer_org = issuer_dict.get("organizationName", "Không rõ")
                issuer_cn = issuer_dict.get("commonName", "Không rõ")
                subject_cn = subject_dict.get("commonName", "Không rõ")

                result["data"]["issuer"] = issuer_org
                result["data"]["issuer_cn"] = issuer_cn
                result["data"]["subject"] = subject_cn
                result["data"]["not_before"] = cert.get("notBefore", "")
                result["data"]["not_after"] = cert.get("notAfter", "")

                # Kiểm tra chứng chỉ tự ký (Self-signed)
                if issuer_org == subject_cn or "self" in issuer_org.lower():
                    result["warnings"].append("🚨 Chứng chỉ SSL **tự ký (Self-Signed)**! Đây không phải chứng chỉ từ tổ chức uy tín. Các trang lừa đảo thường dùng SSL tự ký để giả vờ 'an toàn'.")
                    result["risk_score"] += 25

                # Kiểm tra chứng chỉ miễn phí (Let's Encrypt) - không hẳn xấu nhưng đáng lưu ý
                if "let's encrypt" in issuer_org.lower() or "r3" == issuer_cn.lower() or "r10" == issuer_cn.lower() or "r11" == issuer_cn.lower():
                    result["data"]["cert_type"] = "Let's Encrypt (Miễn phí)"
                else:
                    result["data"]["cert_type"] = f"{issuer_org}"

    except ssl.SSLCertVerificationError as e:
        result["warnings"].append(f"🚨 **Chứng chỉ SSL KHÔNG HỢP LỆ**: {str(e)[:100]}. Trình duyệt sẽ cảnh báo nguy hiểm khi truy cập trang này!")
        result["risk_score"] += 40
    except (socket.timeout, ConnectionRefusedError, OSError):
        result["data"]["error"] = "Không thể kết nối tới máy chủ hoặc máy chủ không hỗ trợ HTTPS."
    except Exception as e:
        result["data"]["error"] = f"Lỗi kiểm tra SSL: {str(e)[:100]}"

    return result


# =============================================================================
# MODULE 4: KIỂM TRA HTTP SECURITY HEADERS
# =============================================================================

def check_security_headers(url):
    """Kiểm tra các tiêu đề bảo mật HTTP của trang web"""
    result = {"available": False, "data": {}, "warnings": [], "risk_score": 0}
    try:
        import requests
        if not url.startswith(("http://", "https://")):
            url = "https://" + url

        resp = requests.get(url, timeout=8, allow_redirects=True, verify=False,
                           headers={"User-Agent": "CyberShield AI/1.0 SecurityAuditor"})

        result["available"] = True
        headers = resp.headers
        result["data"]["status_code"] = resp.status_code
        result["data"]["final_url"] = resp.url
        result["data"]["server"] = headers.get("Server", "Ẩn")

        # Kiểm tra Redirect chain (chuỗi chuyển hướng)
        if resp.history:
            redirect_chain = [r.url for r in resp.history]
            result["data"]["redirect_chain"] = redirect_chain
            if len(redirect_chain) >= 3:
                result["warnings"].append(f"⚠️ URL trải qua **{len(redirect_chain)} lần chuyển hướng (redirect)** trước khi đến đích thực. Chuỗi redirect dài là chiêu trò phổ biến để che giấu nguồn gốc link lừa đảo.")
                result["risk_score"] += 15

        # Kiểm tra các header bảo mật quan trọng
        security_headers = {
            "Content-Security-Policy": "Chính sách bảo mật nội dung (CSP) — ngăn chặn tấn công XSS",
            "X-Frame-Options": "Chống nhúng iframe — ngăn chặn tấn công Clickjacking",
            "X-Content-Type-Options": "Ngăn trình duyệt đoán sai loại nội dung (MIME Sniffing)",
            "Strict-Transport-Security": "Ép buộc kết nối HTTPS (HSTS)",
            "X-XSS-Protection": "Bộ lọc tấn công XSS tích hợp trình duyệt",
        }

        missing_headers = []
        present_headers = []
        for header, description in security_headers.items():
            if header.lower() in {k.lower(): v for k, v in headers.items()}:
                present_headers.append(header)
            else:
                missing_headers.append(header)

        result["data"]["present_headers"] = present_headers
        result["data"]["missing_headers"] = missing_headers

        if len(missing_headers) >= 3:
            result["warnings"].append(f"⚠️ Trang web **thiếu {len(missing_headers)}/{len(security_headers)} tiêu đề bảo mật quan trọng** ({', '.join(missing_headers[:3])}...). Các trang web chuyên nghiệp luôn cấu hình đầy đủ các header này.")
            result["risk_score"] += 10

    except Exception as e:
        result["data"]["error"] = f"Không thể kết nối: {str(e)[:100]}"

    return result


# =============================================================================
# MODULE 5: PHÂN TÍCH AI NVIDIA GPT-120B (Bộ não trung tâm)
# =============================================================================

def get_ai_link_analysis(url, heuristic_data, whois_data, ssl_data, header_data):
    """Gọi API NVIDIA GPT-120B để thực hiện phân tích tổng hợp chuyên sâu"""
    if not NVIDIA_API_KEY:
        return {
            "ai_analysis": "⚠️ Không tìm thấy `NVIDIA_API_KEY` trong cấu hình `.env`. AI Engine không khả dụng.",
            "ai_status": "UNKNOWN"
        }

    client = OpenAI(base_url=NVIDIA_BASE_URL, api_key=NVIDIA_API_KEY)

    # Chuẩn bị dữ liệu ngữ cảnh từ tất cả các module quét
    warnings_text = "\n".join([f"  {w}" for w in heuristic_data["warnings"]]) if heuristic_data["warnings"] else "  Không phát hiện dấu hiệu bất thường."
    brand_text = f"  Nghi ngờ giả mạo: {heuristic_data['brand_impersonated']}" if heuristic_data["brand_impersonated"] else "  Không phát hiện giả mạo thương hiệu."

    # Dữ liệu WHOIS
    whois_text = "  Không có dữ liệu WHOIS."
    if whois_data["available"]:
        whois_lines = []
        if "creation_date" in whois_data["data"]:
            whois_lines.append(f"  - Ngày đăng ký: {whois_data['data']['creation_date']}")
        if "age_days" in whois_data["data"]:
            whois_lines.append(f"  - Tuổi tên miền: {whois_data['data']['age_days']} ngày")
        if "registrar" in whois_data["data"]:
            whois_lines.append(f"  - Nhà đăng ký: {whois_data['data']['registrar']}")
        if "country" in whois_data["data"]:
            whois_lines.append(f"  - Quốc gia: {whois_data['data']['country']}")
        if whois_data["warnings"]:
            for w in whois_data["warnings"]:
                whois_lines.append(f"  - CẢNH BÁO: {w}")
        whois_text = "\n".join(whois_lines) if whois_lines else whois_text

    # Dữ liệu SSL
    ssl_text = "  Không có dữ liệu SSL."
    if ssl_data["available"]:
        ssl_lines = [
            f"  - Tổ chức cấp: {ssl_data['data'].get('issuer', 'N/A')}",
            f"  - Loại chứng chỉ: {ssl_data['data'].get('cert_type', 'N/A')}",
            f"  - Hiệu lực: {ssl_data['data'].get('not_before', '')} → {ssl_data['data'].get('not_after', '')}"
        ]
        if ssl_data["warnings"]:
            for w in ssl_data["warnings"]:
                ssl_lines.append(f"  - CẢNH BÁO: {w}")
        ssl_text = "\n".join(ssl_lines)

    # Dữ liệu HTTP Headers
    header_text = "  Không có dữ liệu HTTP."
    if header_data["available"]:
        header_lines = [
            f"  - HTTP Status: {header_data['data'].get('status_code', 'N/A')}",
            f"  - Server: {header_data['data'].get('server', 'N/A')}",
        ]
        if "redirect_chain" in header_data["data"]:
            header_lines.append(f"  - Chuỗi Redirect: {' → '.join(header_data['data']['redirect_chain'][:3])}")
        if "missing_headers" in header_data["data"]:
            header_lines.append(f"  - Header bảo mật thiếu: {', '.join(header_data['data']['missing_headers'])}")
        if "present_headers" in header_data["data"]:
            header_lines.append(f"  - Header bảo mật có: {', '.join(header_data['data']['present_headers'])}")
        if header_data["warnings"]:
            for w in header_data["warnings"]:
                header_lines.append(f"  - CẢNH BÁO: {w}")
        header_text = "\n".join(header_lines)

    system_prompt = (
        "Bạn là 'CyberShield AI Threat Intel' - Chuyên gia phân tích bảo mật cấp cao hàng đầu Việt Nam, "
        "được phát triển bởi lập trình viên CyberShield AI Team.\n\n"
        "Nhiệm vụ: Tổng hợp toàn bộ dữ liệu từ 4 module quét (Heuristic, WHOIS, SSL, HTTP Headers) "
        "để đưa ra báo cáo phân tích bảo mật toàn diện nhất.\n\n"
        "QUY TẮC ĐỊNH DẠNG BÁO CÁO (BẮT BUỘC TUÂN THỦ):\n"
        "- Viết báo cáo bằng Tiếng Việt, chuyên nghiệp và mạch lạc.\n"
        "- SỬ DỤNG heading (## và ###), danh sách gạch đầu dòng, và chữ **in đậm**.\n"
        "- TUYỆT ĐỐI KHÔNG SỬ DỤNG BẢNG (TABLE). Dùng danh sách bullet có nhãn in đậm.\n"
        "- Sử dụng emoji (🔍 🛡️ ⚠️ 🚨 ✅ ❌ 🌐 🔒 📋) tăng tính trực quan.\n"
        "- Dùng > blockquote cho các cảnh báo quan trọng nhất.\n\n"
        "CẤU TRÚC BÁO CÁO:\n"
        "## 🔍 Phân tích cấu trúc URL\n"
        "## 🌐 Thông tin WHOIS & Tuổi tên miền\n"
        "## 🔒 Đánh giá chứng chỉ SSL/TLS\n"
        "## 📋 Kiểm tra tiêu đề bảo mật HTTP\n"
        "## ⚠️ Đánh giá động cơ lừa đảo & rủi ro\n"
        "## 🚨 Kết luận mức độ rủi ro (AN TOÀN / NGHI NGỜ / NGUY HIỂM)\n"
        "## 🛡️ Khuyến nghị cho người dùng\n\n"
        "BẮT BUỘC: Dòng CUỐI CÙNG của báo cáo PHẢI là một trong 3 tag sau (viết đúng nguyên văn):\n"
        "- Nếu link an toàn: [VERDICT: SAFE]\n"
        "- Nếu link nghi ngờ: [VERDICT: SUSPICIOUS]\n"
        "- Nếu link nguy hiểm: [VERDICT: DANGEROUS]\n\n"
        "LƯU Ý QUAN TRỌNG: Các tên miền thuộc thương hiệu uy tín toàn cầu (google.com, youtube.com, facebook.com, "
        "shopee.vn, fpt.edu.vn, v.v.) nếu KHÔNG có dấu hiệu giả mạo thì PHẢI đánh giá là AN TOÀN [VERDICT: SAFE].\n\n"
        "Kết thúc bằng dòng: *Được bảo mật bởi hệ thống AI của CyberShield AI Team*\n"
        "Rồi xuống dòng và ghi tag VERDICT."
    )

    user_message = (
        f"Hãy phân tích toàn diện đường link sau:\n"
        f"URL: {url}\n\n"
        f"[MODULE 1 - KẾT QUẢ QUÉT HEURISTIC]:\n"
        f"- Trạng thái: {heuristic_data['status']}\n"
        f"- Điểm rủi ro: {heuristic_data['risk_score']}/100\n"
        f"- Cảnh báo:\n{warnings_text}\n"
        f"- {brand_text}\n\n"
        f"[MODULE 2 - KẾT QUẢ WHOIS]:\n{whois_text}\n\n"
        f"[MODULE 3 - KẾT QUẢ SSL/TLS]:\n{ssl_text}\n\n"
        f"[MODULE 4 - KẾT QUẢ HTTP HEADERS]:\n{header_text}\n\n"
        f"Hãy tổng hợp tất cả dữ liệu trên để đưa ra báo cáo đánh giá an toàn chi tiết nhất."
    )

    try:
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=0.2,
            max_tokens=2500
        )

        ai_response = completion.choices[0].message.content

        # Phân loại trạng thái dựa trên tag [VERDICT] mà AI trả về
        ai_status = "SAFE"
        if "[VERDICT: DANGEROUS]" in ai_response:
            ai_status = "DANGEROUS"
        elif "[VERDICT: SUSPICIOUS]" in ai_response:
            ai_status = "SUSPICIOUS"
        elif "[VERDICT: SAFE]" in ai_response:
            ai_status = "SAFE"

        # Xóa tag VERDICT khỏi báo cáo hiển thị cho người dùng
        clean_response = ai_response.replace("[VERDICT: DANGEROUS]", "").replace("[VERDICT: SUSPICIOUS]", "").replace("[VERDICT: SAFE]", "").strip()

        return {"ai_analysis": clean_response, "ai_status": ai_status}

    except Exception as e:
        return {
            "ai_analysis": f"❌ Lỗi kết nối với API NVIDIA AI: {str(e)}",
            "ai_status": "UNKNOWN"
        }


# =============================================================================
# ROUTES
# =============================================================================

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/analyze", methods=["POST"])
def analyze():
    data = request.json
    if not data or "url" not in data:
        return jsonify({"error": "Vui lòng cung cấp đường link cần phân tích"}), 400

    url = data["url"].strip()
    if not url:
        return jsonify({"error": "Đường link không được để trống"}), 400

    # Chuẩn hóa domain
    temp_url = url if url.startswith(("http://", "https://")) else "https://" + url
    parsed = urllib.parse.urlparse(temp_url)
    domain = parsed.netloc.lower().split(":")[0]

    # ===== KIỂM TRA WHITELIST DOMAIN UY TÍN =====
    is_trusted = False
    for trusted in TRUSTED_DOMAINS:
        # Khớp chính xác hoặc subdomain (vd: www.youtube.com khớp youtube.com)
        if domain == trusted or domain.endswith("." + trusted):
            is_trusted = True
            break

    # MODULE 1: Heuristic Analysis (Quét tĩnh nâng cao)
    heuristic_results = analyze_domain_heuristics(url)

    # MODULE 2: WHOIS Lookup (Kiểm tra tuổi tên miền)
    whois_results = check_whois(domain)

    # MODULE 3: SSL Certificate Check
    ssl_results = check_ssl_certificate(domain)

    # MODULE 4: HTTP Security Headers
    header_results = check_security_headers(url)

    # MODULE 5: AI Analysis (Gọi NVIDIA GPT-120B)
    ai_results = get_ai_link_analysis(url, heuristic_results, whois_results, ssl_results, header_results)

    # Tổng hợp tất cả cảnh báo từ mọi module
    all_warnings = (
        heuristic_results["warnings"] +
        whois_results["warnings"] +
        ssl_results["warnings"] +
        header_results["warnings"]
    )

    # Tổng hợp điểm rủi ro
    total_risk = (
        heuristic_results["risk_score"] +
        whois_results["risk_score"] +
        ssl_results["risk_score"] +
        header_results["risk_score"]
    )
    total_risk = min(total_risk, 100)  # Cap tại 100

    # ===== QUYẾT ĐỊNH TRẠNG THÁI CUỐI CÙNG =====
    if is_trusted:
        # Domain nằm trong whitelist → LUÔN AN TOÀN (trừ khi heuristic phát hiện giả mạo)
        if heuristic_results["brand_impersonated"]:
            # Trường hợp hiếm: domain trusted nhưng heuristic vẫn phát hiện vấn đề
            final_status = "SUSPICIOUS"
            total_risk = max(total_risk, 25)
        else:
            final_status = "SAFE"
            total_risk = min(total_risk, 10)
            # Xóa các cảnh báo không liên quan (HTTP headers missing) cho trusted domain
            all_warnings = [w for w in all_warnings if "🚨" in w]  # Chỉ giữ cảnh báo nghiêm trọng
    else:
        # Domain KHÔNG nằm trong whitelist → logic đánh giá bình thường
        final_status = heuristic_results["status"]

        # Ưu tiên AI verdict
        if ai_results["ai_status"] != "UNKNOWN":
            if ai_results["ai_status"] == "DANGEROUS":
                final_status = "DANGEROUS"
            elif ai_results["ai_status"] == "SUSPICIOUS" and final_status == "SAFE":
                final_status = "SUSPICIOUS"

        # Override bằng risk score tổng hợp
        if total_risk >= 50:
            final_status = "DANGEROUS"
        elif total_risk >= 25 and final_status == "SAFE":
            final_status = "SUSPICIOUS"

        # Chuẩn hóa lại risk score theo final status
        if final_status == "DANGEROUS":
            total_risk = max(total_risk, 70)
        elif final_status == "SUSPICIOUS":
            total_risk = max(total_risk, 30)
        else:
            total_risk = min(total_risk, 15)

    response_data = {
        "url": url,
        "status": final_status,
        "risk_score": total_risk,
        "heuristics": {
            "warnings": all_warnings,
            "brand_impersonated": heuristic_results["brand_impersonated"]
        },
        "whois": whois_results["data"] if whois_results["available"] else None,
        "ssl": ssl_results["data"] if ssl_results["available"] else None,
        "headers": header_results["data"] if header_results["available"] else None,
        "ai_report": ai_results["ai_analysis"]
    }

    return jsonify(response_data)


if __name__ == "__main__":
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
