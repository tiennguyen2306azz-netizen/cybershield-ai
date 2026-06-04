import os
import re
import ssl
import socket
import urllib.parse
import math
import base64
import ipaddress
from datetime import datetime, timezone
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from dotenv import load_dotenv
from openai import OpenAI

# Tải cấu hình từ .env
load_dotenv()

base_dir = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__, 
            template_folder=os.path.join(base_dir, "templates"), 
            static_folder=os.path.join(base_dir, "static"))
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
    # Global Services & Platforms
    "google.com", "youtube.com", "facebook.com", "instagram.com", "twitter.com",
    "x.com", "tiktok.com", "linkedin.com", "reddit.com", "wikipedia.org",
    "github.com", "stackoverflow.com", "microsoft.com", "apple.com",
    "amazon.com", "netflix.com", "spotify.com", "discord.com", "telegram.org",
    "paypal.com", "shopify.com", "cloudflare.com", "adobe.com", "zoom.us",
    "slack.com", "notion.so", "twitch.tv", "pinterest.com", "ebay.com",
    "yahoo.com", "bing.com", "baidu.com", "whatsapp.com", "viber.com",
    "skype.com", "figma.com", "canva.com", "dropbox.com", "openai.com",
    "nvidia.com", "gitlab.com", "npmjs.com", "pypi.org", "w3schools.com",
    "mozilla.org", "medium.com", "git-scm.com", "docker.com",
    # Vietnamese Governmental, Public Services & Press
    "gov.vn", "edu.vn", "chinhphu.vn", "baochinhphu.vn", "bocongan.gov.vn",
    "vtv.vn", "vnexpress.net", "tuoitre.vn", "thanhnien.vn", "dantri.com.vn",
    "vietnamnet.vn", "nhandan.vn", "chinhphu.vn", "mic.gov.vn", "ais.gov.vn",
    "chongluadao.vn", "tinnhiemmang.vn", "khonggianmang.vn", "ncsc.gov.vn",
    # Vietnamese Banks & Payment gateways
    "vietcombank.com.vn", "techcombank.com.vn", "bidv.com.vn", "mbbank.com.vn",
    "acb.com.vn", "sacombank.com.vn", "agribank.com.vn", "vnpay.vn",
    "zalopay.vn", "vietinbank.vn", "vpbank.com.vn", "shb.com.vn", "vib.com.vn",
    "eximbank.com.vn", "lienvietpostbank.com.vn", "kbank.com", "lottepay.com.vn",
    "momo.vn", "zalopay.vn",
    # Vietnamese E-Commerce & Shipping
    "shopee.vn", "lazada.vn", "tiki.vn", "sendo.vn", "viettel.vn", "fpt.vn",
    "vingroup.net", "garena.vn", "vng.com.vn", "vnpost.vn", "viettelpost.com.vn",
    "giaohangnhanh.vn", "ghn.vn", "ems.com.vn", "grab.com", "be.com.vn",
    "thegioididong.com", "dienmayxanh.com", "fptshop.com.vn", "tgdd.vn"
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

# Chữ ký lừa đảo chuyên biệt tại Việt Nam (Local Threat Signatures)
VIETNAMESE_PHISHING_SIGNATURES = [
    # Giả mạo cơ quan pháp luật
    "bocongan", "chinhphu", "congan", "dichvucong", "cucthuchihanhanh", "lenhbat",
    # Giả mạo dịch vụ vận chuyển
    "giaohangnhanh", "viettelpost", "vnpost", "ghn", "ems-vn",
    # Giả mạo ngân hàng & ví điện tử bổ sung
    "vietinbank", "vpbank", "shb", "vib", "exim", "lienviet", "kbank", "lottepay",
    # Chiêu dụ đầu tư/Quà tặng
    "nhanqua-vtv", "quatangvtv", "shopee-trunghuong", "game-garena-nhanqua"
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


def calculate_shannon_entropy(s):
    """Tính toán Shannon Entropy của một chuỗi để phát hiện độ ngẫu nhiên (DGA)"""
    if not s:
        return 0.0
    entropy = 0.0
    length = len(s)
    char_counts = {}
    for c in s:
        char_counts[c] = char_counts.get(c, 0) + 1
    for count in char_counts.values():
        p = count / length
        entropy -= p * math.log2(p)
    return round(entropy, 2)


def is_ssrf_ip(url):
    """Xác định xem địa chỉ URL có chỉ tới địa chỉ IP nội bộ, loopback hoặc riêng tư nguy hại hay không (Chống SSRF)"""
    try:
        # Chuẩn hóa URL
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
            
        parsed = urllib.parse.urlparse(url)
        hostname = parsed.netloc.lower().split(":")[0]
        
        # 1. Chặn hostname trực tiếp nếu là local
        if hostname in ["localhost", "127.0.0.1", "[::1]", "0.0.0.0"]:
            return True
            
        # 2. Giải phân giải DNS để lấy IP thực tế
        ips = socket.getaddrinfo(hostname, None)
        for ip_info in ips:
            ip_str = ip_info[4][0]
            # Xử lý dải IPv6 nếu có
            if ":" in ip_str and not ip_str.startswith("["):
                # Thử chuyển đổi thành ip address object
                try:
                    ip_obj = ipaddress.ip_address(ip_str)
                except ValueError:
                    continue
            else:
                ip_obj = ipaddress.ip_address(ip_str)
                
            # Kiểm tra xem IP có thuộc dải private, loopback, link_local hay multicast không
            if ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_link_local or ip_obj.is_multicast or ip_obj.is_unspecified:
                return True
    except Exception:
        pass
    return False


def analyze_html_content(html, host_domain):
    """Phân tích mã nguồn HTML để phát hiện form OTP/Password nhạy cảm, đạo nhái giao diện và đánh cắp thương hiệu"""
    results = {
        "warnings": [],
        "risk_score": 0,
        "is_phishing_form": False,
        "asset_leeching_ratio": 0.0,
        "impersonated_brand": None,
        "copyright_theft": False
    }
    
    if not html:
        return results
        
    html_lower = html.lower()
    
    # 1. Quét nhạy cảm: Form mật khẩu / OTP
    has_password_input = 'type="password"' in html_lower or "type='password'" in html_lower
    has_otp_input = any(kw in html_lower for kw in ["otp", "mã xác minh", "maxacminh", "mã otp", "ma otp", "card pin", "mật khẩu", "matkhau"])
    
    if has_password_input or (has_otp_input and ("<input" in html_lower or "<form" in html_lower)):
        results["is_phishing_form"] = True
        results["warnings"].append("🚨 **PHÁT HIỆN BIỂU MẪU THU THẬP THÔNG TIN NHẠY CẢM**: Trang web chứa ô nhập mật khẩu hoặc mã xác thực OTP. Tuyệt đối không nhập thông tin cá nhân tại đây trừ khi bạn chắc chắn đây là trang web chính thức.")
        results["risk_score"] += 35

    # 2. Phát hiện Đạo nhái tài nguyên (Asset Leeching)
    total_assets = 0
    leech_counts = {}
    
    asset_urls = re.findall(r'src=["\'](https?://[^"\']+)["\']|href=["\'](https?://[^"\']+)["\']', html)
    flattened_urls = []
    for t in asset_urls:
        if t[0]: flattened_urls.append(t[0])
        elif t[1]: flattened_urls.append(t[1])
        
    for url in flattened_urls:
        try:
            parsed_asset = urllib.parse.urlparse(url)
            asset_domain = parsed_asset.netloc.lower()
            if ":" in asset_domain:
                asset_domain = asset_domain.split(":")[0]
                
            if asset_domain == host_domain or host_domain.endswith("." + asset_domain) or asset_domain.endswith("." + host_domain):
                continue
                
            total_assets += 1
            for brand_key, brand_domain in POPULAR_BRANDS.items():
                if asset_domain == brand_domain or asset_domain.endswith("." + brand_domain):
                    leech_counts[brand_domain] = leech_counts.get(brand_domain, 0) + 1
                    break
        except Exception:
            continue
            
    if total_assets >= 3:
        for brand_domain, count in leech_counts.items():
            ratio = count / total_assets
            if ratio >= 0.25:
                results["asset_leeching_ratio"] = round(ratio * 100, 2)
                results["impersonated_brand"] = brand_domain
                results["warnings"].append(f"🚨 **PHÁT HIỆN CLONE GIAO DIỆN (ASSET LEECHING)**: Trang web này đang tải trực tiếp **{results['asset_leeching_ratio']}% tài nguyên** (ảnh, scripts) từ tên miền chính hãng `{brand_domain}`. Đây là dấu hiệu rõ ràng của việc làm giả giao diện để lừa đảo người dùng!")
                results["risk_score"] += 45
                break

    # 3. Phát hiện Bản quyền thương hiệu giả mạo (Copyright Theft)
    for brand_key, brand_domain in POPULAR_BRANDS.items():
        if host_domain != brand_domain and not host_domain.endswith("." + brand_domain):
            title_match = re.search(r'<title>[^<]*' + re.escape(brand_key) + r'[^<]*</title>', html_lower)
            copyright_match = re.search(r'(copyright|©|&copy;)[^<]*' + re.escape(brand_key), html_lower)
            
            if title_match or copyright_match:
                results["copyright_theft"] = True
                results["impersonated_brand"] = brand_domain
                results["warnings"].append(f"🚨 **ĐÁNH CẮP BẢN QUYỀN THƯƠNG HIỆU**: Phát hiện thông tin bản quyền hoặc tiêu đề trang nhắc tới thương hiệu chính hãng **`{brand_key}`** (`{brand_domain}`) trên tên miền không được ủy quyền `{host_domain}`. Dấu hiệu mạo danh cực kỳ cao!")
                results["risk_score"] += 35
                break

    # 4. Phát hiện Chuyển hướng ngầm Meta Refresh
    meta_refresh = re.search(r'<meta[^>]*http-equiv=["\']refresh["\'][^>]*content=["\'][^"\']*url=([^"\']+)["\']', html, re.IGNORECASE)
    if meta_refresh:
        redirect_target = meta_refresh.group(1).strip()
        results["warnings"].append(f"🚨 **CHUYỂN HƯỚNG BẰNG META REFRESH**: Phát hiện thẻ meta tự động chuyển hướng người dùng sang trang khác (`{redirect_target}`). Đây là kỹ thuật né tránh quét bảo mật.")
        results["risk_score"] += 30

    # 5. Phát hiện iframe ẩn (Hidden Iframe Drive-by)
    hidden_iframes = re.findall(r'<iframe[^>]*width=["\'](?:0|1px?)["\'][^>]*height=["\'](?:0|1px?)["\']', html_lower)
    if not hidden_iframes:
        hidden_iframes = re.findall(r'<iframe[^>]*style=["\'][^"\']*(?:display:\s*none|visibility:\s*hidden|width:\s*0|height:\s*0)[^"\']*["\']', html_lower)
    if hidden_iframes:
        results["warnings"].append("🚨 **IFRAME CHẠY NGẦM ẨN**: Phát hiện thẻ iframe có kích thước bằng 0 hoặc ẩn (`display:none`). Đây là kỹ thuật lén tải mã độc hoặc tăng truy cập ảo cực kỳ đáng ngờ.")
        results["risk_score"] += 25
                
    return results


def check_dns_records(domain):
    """Kiểm tra bản ghi DNS của tên miền (đặc biệt là MX mail server)"""
    result = {"warnings": [], "risk_score": 0, "has_mx": False, "mx_servers": []}
    try:
        import dns.resolver
        try:
            answers = dns.resolver.resolve(domain, 'MX')
            result["has_mx"] = True
            for rdata in answers:
                result["mx_servers"].append(str(rdata.exchange).rstrip('.'))
        except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN, dns.resolver.NoNameservers, Exception):
            result["has_mx"] = False
    except ImportError:
        pass
        
    return result


def check_virustotal(url):
    """Kiểm tra URL trên VirusTotal API v3 để lấy phản hồi từ 70+ security vendors"""
    result = {"available": False, "malicious_count": 0, "total_vendors": 0, "warnings": [], "risk_score": 0}
    api_key = os.getenv("VIRUSTOTAL_API_KEY")
    if not api_key:
        return result
        
    try:
        import requests
        url_id = base64.urlsafe_b64encode(url.encode()).decode().strip("=")
        headers = {
            "x-apikey": api_key,
            "accept": "application/json"
        }
        api_url = f"https://www.virustotal.com/api/v3/urls/{url_id}"
        resp = requests.get(api_url, headers=headers, timeout=6)
        
        if resp.status_code == 200:
            data = resp.json()
            stats = data.get("data", {}).get("attributes", {}).get("last_analysis_stats", {})
            malicious = stats.get("malicious", 0)
            suspicious = stats.get("suspicious", 0)
            harmless = stats.get("harmless", 0)
            undetected = stats.get("undetected", 0)
            
            result["available"] = True
            result["malicious_count"] = malicious
            result["total_vendors"] = malicious + suspicious + harmless + undetected
            
            if malicious > 0:
                result["warnings"].append(f"🚨 **CẢNH BÁO TỪ VIRUSTOTAL**: Có **{malicious}/{result['total_vendors']} động cơ bảo mật** trên thế giới (như Kaspersky, Sophos...) đã liệt kê liên kết này vào danh sách đen độc hại!")
                result["risk_score"] += min(malicious * 15, 60)
            elif suspicious > 0:
                result["warnings"].append(f"⚠️ **CẢNH BÁO TỪ VIRUSTOTAL**: Có **{suspicious} công cụ bảo mật** đánh dấu liên kết này là đáng ngờ.")
                result["risk_score"] += 15
    except Exception:
        pass
        
    return result


def deobfuscate_query_parameters(url):
    """Phát hiện và giải mã các tham số truy vấn được mã hóa bằng Base64 hoặc Hex để phát hiện theo dõi nạn nhân"""
    results = {
        "has_encoded_params": False,
        "decoded_params": {},
        "warnings": [],
        "risk_score": 0
    }
    try:
        parsed = urllib.parse.urlparse(url)
        # Thay thế các ký tự an toàn dạng URL-safe
        query_str = parsed.query
        queries = urllib.parse.parse_qs(query_str)
        
        for key, values in queries.items():
            for val in values:
                decoded_val = None
                method = None
                
                # Thử giải mã Base64
                if len(val) >= 4 and re.match(r'^[a-zA-Z0-9\-_=]+$', val):
                    try:
                        # Thêm đệm '=' nếu thiếu để giải mã đúng
                        padded_val = val + '=' * (-len(val) % 4)
                        # Thay thế ký tự URL safe
                        padded_val = padded_val.replace('-', '+').replace('_', '/')
                        decoded_bytes = base64.b64decode(padded_val, validate=True)
                        decoded_str = decoded_bytes.decode('utf-8')
                        if all(32 <= ord(c) < 127 or ord(c) > 160 or c in '\r\n\t' for c in decoded_str):
                            decoded_val = decoded_str
                            method = "Base64"
                    except Exception:
                        pass
                
                # Nếu chưa giải mã được, thử giải mã Hex
                if not decoded_val and len(val) >= 4 and re.match(r'^[0-9a-fA-F]+$', val) and len(val) % 2 == 0:
                    try:
                        decoded_bytes = bytes.fromhex(val)
                        decoded_str = decoded_bytes.decode('utf-8')
                        if all(32 <= ord(c) < 127 or ord(c) > 160 or c in '\r\n\t' for c in decoded_str):
                            decoded_val = decoded_str
                            method = "Hex"
                    except Exception:
                        pass
                        
                if decoded_val:
                    results["has_encoded_params"] = True
                    results["decoded_params"][f"{key} ({method})"] = decoded_val
                    results["warnings"].append(f"🚨 **BÓC GỠ THAM SỐ THEO DÕI ({method})**: Phát hiện tham số truy vấn `{key}` chứa dữ liệu mã hóa ẩn. Sau khi giải mã: **`{decoded_val}`**. Kẻ xấu đang âm thầm theo dõi hoặc định danh thiết bị của bạn qua tham số này!")
                    results["risk_score"] += 15
                    
    except Exception:
        pass
        
    return results


def analyze_javascript_behavior(html):
    """Phân tích tĩnh các thẻ script trong HTML để phát hiện hành vi độc hại, chống dịch ngược, chặn chuột phải, keylogging"""
    results = {
        "has_suspicious_js": False,
        "warnings": [],
        "risk_score": 0,
        "details": {
            "anti_devtools": False,
            "right_click_blocking": False,
            "keylogging": False,
            "stealth_redirect": False,
            "exfiltration": False
        }
    }
    
    if not html:
        return results
        
    try:
        scripts = re.findall(r'<script[^>]*>(.*?)</script>', html, re.DOTALL | re.IGNORECASE)
        combined_script = " ".join(scripts).lower()
        
        # 1. Phát hiện Anti-DevTools / Chống dịch ngược
        anti_dt_patterns = ["debugger", "devtools", "window.addeventlistener('resize'", "element.onclick = function()", "anti-devtools"]
        if any(p in combined_script for p in anti_dt_patterns) or "function debugger" in combined_script:
            results["details"]["anti_devtools"] = True
            results["warnings"].append("🚨 **CHỐNG DỊCH NGƯỢC (ANTI-DEVTOOLS)**: Phát hiện mã lệnh cố ý theo dõi hoặc làm gián đoạn bảng điều khiển Developer Tools (như dùng lệnh `debugger`). Đây là chiêu trò che giấu mã độc của các trang lừa đảo.")
            results["risk_score"] += 25
            
        # 2. Phát hiện Chặn chuột phải / Chặn phím tắt F12
        if ("contextmenu" in combined_script or "oncontextmenu" in combined_script) and ("preventdefault" in combined_script or "return false" in combined_script):
            results["details"]["right_click_blocking"] = True
            results["warnings"].append("⚠️ **CHẶN CHUỘT PHẢI / ANTI-COPY**: Phát hiện script chặn click chuột phải hoặc chặn phím sao chép nhằm mục đích ngăn cản nạn nhân phân tích liên kết hoặc sao chép mã nguồn.")
            results["risk_score"] += 15
            
        # 3. Phát hiện Keylogger / Trộm ký tự bàn phím
        kl_patterns = ["keyup", "keypress", "keydown"]
        if any(p in combined_script for p in kl_patterns) and ("addeventlistener" in combined_script or "window.on" in combined_script):
            if "document.addeventlistener" in combined_script or "window.addeventlistener" in combined_script:
                results["details"]["keylogging"] = True
                results["warnings"].append("🚨 **NGHI NGỜ KEYLOGGER**: Phát hiện mã lắng nghe sự kiện gõ bàn phím trên quy mô toàn trang web. Có nguy cơ cao trang web đang âm thầm ghi lại mật khẩu hoặc thông tin thẻ của bạn khi gõ phím!")
                results["risk_score"] += 35

        # 4. Phát hiện Chuyển hướng động ẩn (Stealth Dynamic Redirect)
        redirect_patterns = ["location.replace", "location.href", "location.assign", "window.location="]
        obfuscated_patterns = ["eval(", "unescape(", "atob(", "string.fromcharcode"]
        if any(p in combined_script for p in redirect_patterns) and any(o in combined_script for o in obfuscated_patterns):
            results["details"]["stealth_redirect"] = True
            results["warnings"].append("🚨 **CHUYỂN HƯỚNG ĐỘNG ẨN**: Phát hiện tập lệnh chứa các hàm chuyển hướng tự động kết hợp với kỹ thuật làm rối mã nguồn (`eval`, `atob`). Đây là kỹ thuật né tránh các bộ lọc bảo mật để đưa người dùng đến trang lừa đảo thực sự.")
            results["risk_score"] += 30

        # 5. Phát hiện Gửi dữ liệu lén lút (Exfiltration)
        if "navigator.sendbeacon" in combined_script:
            results["details"]["exfiltration"] = True
            results["warnings"].append("⚠️ **GỬI DỮ LIỆU CHẠY NỀN**: Phát hiện sử dụng `navigator.sendBeacon` để truyền dữ liệu chạy nền về máy chủ kẻ tấn công ngay cả khi người dùng đóng trang web.")
            results["risk_score"] += 15

        # 6. Phát hiện các kỹ thuật mã hóa/làm rối JS nâng cao (Obfuscation Detection)
        combined_script_raw = " ".join(scripts)
        
        # JSFuck Detection (Chỉ sử dụng 6 ký tự: [ ] ( ) ! +)
        if re.search(r'([\[\]\(\)\!\+]{20,})', combined_script_raw):
            results["warnings"].append("🚨 **MÃ HÓA JSFUCK PHÁT HIỆN**: Tập lệnh sử dụng kỹ thuật JSFuck (chỉ gồm các ký tự `[]()!+`) nhằm ẩn giấu hoàn toàn hành vi độc hại khỏi các tường lửa quét tĩnh!")
            results["risk_score"] += 40
            
        # JJEncode / AAEncode (Mã hóa biểu tượng cảm xúc Nhật Bản)
        if "$~[]" in combined_script_raw or "精" in combined_script_raw or "ﾟωﾟﾉ" in combined_script_raw:
            results["warnings"].append("🚨 **MÃ HÓA MẶT CƯỜI (AAENCODE/JJENCODE)**: Script sử dụng ký tự đặc biệt hoặc biểu tượng mặt cười Nhật Bản để mã hóa mã độc, nhằm trốn tránh bộ quét tĩnh.")
            results["risk_score"] += 35
            
        # Obfuscator.io (Hex variables _0x)
        if re.search(r'var _0x[a-f0-9]+', combined_script_raw) or re.search(r'function _0x[a-f0-9]+', combined_script_raw):
            results["warnings"].append("🚨 **TRÌNH LÀM RỐI OBFUSCATOR.IO**: Phát hiện mã nguồn được làm rối bằng Hex variables kiểu `_0x4f12`. Đây là kỹ thuật chuyên nghiệp thường bị hacker lợi dụng để giấu các script keylogger đánh cắp tài khoản.")
            results["risk_score"] += 30
            
        # Packed script (eval(function(p,a,c,k,e,r)))
        if "eval(function(p,a,c,k,e," in combined_script_raw.replace(" ", ""):
            results["warnings"].append("⚠️ **TẬP LỆNH ĐƯỢC NÉN (PACKED SCRIPT)**: Phát hiện sử dụng thuật toán nén Dean Edwards Packer `eval(function(p,a,c,k...` để mã hóa và nén script chạy ngầm.")
            results["risk_score"] += 20

        if results["risk_score"] > 0:
            results["has_suspicious_js"] = True

    except Exception:
        pass
        
    return results


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

        # --- CHECK 6.5: Giải mã Punycode & Phát hiện Homograph nâng cao ---
        if domain.startswith("xn--"):
            try:
                decoded_domain = domain.encode("utf-8").decode("idna")
                results["warnings"].append(f"🚨 **PHÁT HIỆN TÊN MIỀN QUỐC TẾ MÃ HÓA (PUNYCODE HOMOGRAPH)**: Tên miền gốc là `{domain}`, khi hiển thị thực tế trên trình duyệt sẽ biến đổi thành: **`{decoded_domain}`**. Đây là thủ thuật đánh lừa thị giác (Homograph Attack) để mạo danh các thương hiệu lớn cực kỳ tinh vi!")
                results["risk_score"] += 50
                results["status"] = "DANGEROUS"
                results["details"]["decoded_punycode"] = decoded_domain
            except Exception:
                pass

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

        # --- CHECK 11: Tính toán Shannon Entropy để phát hiện tên miền ngẫu nhiên (DGA) ---
        domain_parts = domain.split(".")
        main_part = domain_parts[0] if domain_parts else ""
        if len(main_part) >= 8:
            entropy = calculate_shannon_entropy(main_part)
            results["details"]["entropy"] = entropy
            if entropy > 3.9:
                results["warnings"].append(f"⚠️ Tên miền `{domain}` có **chỉ số hỗn loạn ký tự (Entropy) rất cao ({entropy})**. Đây là đặc trưng phổ biến của các tên miền phụ sinh tự động bằng máy (DGA) hoặc tên miền rác phân phối phần mềm độc hại.")
                results["risk_score"] += 15
                if results["status"] == "SAFE":
                    results["status"] = "SUSPICIOUS"

        # --- CHECK 12: Chữ ký lừa đảo chuyên biệt tại Việt Nam (Local Threat Signatures) ---
        found_vn_signatures = []
        for sig in VIETNAMESE_PHISHING_SIGNATURES:
            if sig in domain or sig in path or sig in query:
                # Tránh cảnh báo nhầm đối với các cơ quan chính phủ chính thống hoặc các dịch vụ thực tế
                if not (domain.endswith("gov.vn") or domain.endswith("chinhphu.vn") or domain.endswith("vnpost.vn") or domain.endswith("viettelpost.com.vn") or domain.endswith("vietinbank.vn") or domain.endswith("vpbank.com.vn")):
                    found_vn_signatures.append(sig)
        if found_vn_signatures:
            sig_list = ", ".join([f"`{s}`" for s in found_vn_signatures])
            results["warnings"].append(f"🚨 **PHÁT HIỆN CHỮ KÝ LỪA ĐẢO CHUYÊN BIỆT TẠI VIỆT NAM**: URL chứa từ khóa nhạy cảm {sig_list} mạo danh các cơ quan công an, dịch vụ vận chuyển hoặc ngân hàng tại Việt Nam. Nguy cơ lừa đảo chiếm đoạt tài sản cực kỳ cao!")
            results["risk_score"] += 45
            results["status"] = "DANGEROUS"

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
        result["html"] = resp.text
        headers = resp.headers
        result["data"]["status_code"] = resp.status_code
        result["data"]["final_url"] = resp.url
        result["data"]["server"] = headers.get("Server", "Ẩn")

        # Theo dõi chi tiết từng nút chuyển hướng (Hop-by-Hop Redirect Chain Tracker)
        hops_detail = []
        if resp.history:
            for i, r in enumerate(resp.history):
                hop_parsed = urllib.parse.urlparse(r.url)
                hop_domain = hop_parsed.netloc.lower().split(":")[0]
                hops_detail.append({
                    "hop_number": i + 1,
                    "url": r.url,
                    "domain": hop_domain,
                    "status_code": r.status_code
                })
        
        # Thêm hop cuối cùng (đích đến)
        final_parsed = urllib.parse.urlparse(resp.url)
        final_domain = final_parsed.netloc.lower().split(":")[0]
        hops_detail.append({
            "hop_number": len(hops_detail) + 1,
            "url": resp.url,
            "domain": final_domain,
            "status_code": resp.status_code
        })
        
        result["data"]["hops_detail"] = hops_detail

        # Phân tích tích lũy trên chuỗi chuyển hướng
        if len(hops_detail) > 1:
            redirect_chain = [h["url"] for h in hops_detail[:-1]]
            result["data"]["redirect_chain"] = redirect_chain
            
            # Cảnh báo nếu chuỗi quá dài
            if len(hops_detail) - 1 >= 3:
                result["warnings"].append(f"⚠️ URL trải qua **{len(hops_detail) - 1} lần chuyển hướng (redirect)** trước khi đến đích thực. Chuỗi redirect dài là chiêu trò phổ biến để che giấu nguồn gốc link lừa đảo.")
                result["risk_score"] += 15
                
            # Duyệt qua từng hop trung gian để phát hiện rủi ro ẩn giấu
            suspicious_hops = []
            for hop in hops_detail[:-1]: # chỉ audit các hop trung gian
                h_dom = hop["domain"]
                h_url = hop["url"]
                
                # Check 1: Chứa từ khóa nguy hiểm hoặc chữ ký Việt Nam trong hop trung gian
                found_sig = [s for s in VIETNAMESE_PHISHING_SIGNATURES if s in h_url]
                if found_sig:
                    suspicious_hops.append(f"Hop {hop['hop_number']} (`{h_dom}`) chứa chữ ký lừa đảo `{found_sig[0]}`")
                    result["risk_score"] += 25
                    
                # Check 2: Tên miền ngẫu nhiên rác (DGA) trong hop trung gian
                if len(h_dom.split(".")[0]) >= 8:
                    h_entropy = calculate_shannon_entropy(h_dom.split(".")[0])
                    if h_entropy > 4.0:
                        suspicious_hops.append(f"Hop {hop['hop_number']} (`{h_dom}`) có Entropy cao ({h_entropy})")
                        result["risk_score"] += 20
                        
                # Check 3: Sử dụng TLD rác trong hop trung gian
                is_bad_tld = any(h_dom.endswith(tld) for tld in SUSPICIOUS_TLDS)
                if is_bad_tld:
                    suspicious_hops.append(f"Hop {hop['hop_number']} (`{h_dom}`) sử dụng TLD rác `{h_dom.split('.')[-1]}`")
                    result["risk_score"] += 15
                    
            if suspicious_hops:
                sig_hops = "; ".join(suspicious_hops)
                result["warnings"].append(f"🚨 **PHÁT HIỆN RỦI RO TRONG CHUỖI CHUYỂN HƯỚNG**: Các bước chuyển hướng trung gian chứa hành vi đáng ngờ: {sig_hops}. Đây là hành vi tinh vi nhằm trốn tránh các hệ thống bảo mật firewall!")

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

def get_ai_link_analysis(url, heuristic_data, whois_data, ssl_data, header_data, html_results=None, dns_data=None, vt_data=None, js_data=None):
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

    # Dữ liệu HTTP Headers & Redirection Chain
    header_text = "  Không có dữ liệu HTTP."
    if header_data["available"]:
        header_lines = [
            f"  - HTTP Status: {header_data['data'].get('status_code', 'N/A')}",
            f"  - Server: {header_data['data'].get('server', 'N/A')}",
        ]
        if "hops_detail" in header_data["data"]:
            hops_str = " → ".join([f"Hop {h['hop_number']}: {h['domain']} ({h['status_code']})" for h in header_data["data"]["hops_detail"]])
            header_lines.append(f"  - Chuỗi chuyển hướng chi tiết (Hop-by-Hop): {hops_str}")
        elif "redirect_chain" in header_data["data"]:
            header_lines.append(f"  - Chuỗi Redirect: {' → '.join(header_data['data']['redirect_chain'][:3])}")
        if "missing_headers" in header_data["data"]:
            header_lines.append(f"  - Header bảo mật thiếu: {', '.join(header_data['data']['missing_headers'])}")
        if "present_headers" in header_data["data"]:
            header_lines.append(f"  - Header bảo mật có: {', '.join(header_data['data']['present_headers'])}")
        if header_data["warnings"]:
            for w in header_data["warnings"]:
                header_lines.append(f"  - CẢNH BÁO: {w}")
        header_text = "\n".join(header_lines)

    # Chuẩn bị dữ liệu bổ sung nếu có
    additional_text = ""
    if dns_data:
        additional_text += f"\n[MODULE BỔ SUNG - PHÂN TÍCH DNS INTEGRITY]:\n"
        additional_text += f"  - Có Mail Server (MX): {dns_data.get('has_mx', False)}\n"
        if dns_data.get("mx_servers"):
            additional_text += f"  - Máy chủ nhận thư: {', '.join(dns_data['mx_servers'])}\n"
            
    if html_results:
        additional_text += f"\n[MODULE BỔ SUNG - HTML CLONING AUDIT]:\n"
        additional_text += f"  - Có biểu mẫu đăng nhập nhạy cảm (Password/OTP): {html_results.get('is_phishing_form', False)}\n"
        if html_results.get("asset_leeching_ratio", 0) > 0:
            additional_text += f"  - Tỷ lệ Leeching tài nguyên: {html_results['asset_leeching_ratio']}% tải từ tên miền `{html_results.get('impersonated_brand')}`\n"
        if html_results.get("copyright_theft", False):
            additional_text += f"  - Đánh cắp bản quyền thương hiệu: Phát hiện nhắc tới thương hiệu `{html_results.get('impersonated_brand')}` trong mã nguồn\n"

    if js_data and js_data.get("has_suspicious_js", False):
        additional_text += f"\n[MODULE BỔ SUNG - ĐỘNG CƠ QUÉT TĨNH JS HÀNH VI (JS BEHAVIORAL SCAN)]:\n"
        additional_text += f"  - Phát hiện hành vi JavaScript nguy hại: Có\n"
        for w in js_data["warnings"]:
            additional_text += f"  - CẢNH BÁO JS: {w}\n"
            
    if vt_data and vt_data.get("available", False):
        additional_text += f"\n[MODULE BỔ SUNG - THREAT INTEL VIRUSTOTAL]:\n"
        additional_text += f"  - Số công cụ diệt virus gắn cờ độc hại: {vt_data.get('malicious_count', 0)}/{vt_data.get('total_vendors', 0)}\n"

    if html_results and html_results.get("deobfuscator") and html_results["deobfuscator"].get("has_encoded_params"):
        decoded = html_results["deobfuscator"]["decoded_params"]
        additional_text += f"\n[MODULE BỔ SUNG - QUERY PARAM DEOBFUSCATOR]:\n"
        for k, v in decoded.items():
            additional_text += f"  - Tham số {k} -> Dữ liệu giải mã: {v}\n"

    system_prompt = (
        "Bạn là 'CyberShield Agent Threat Intel' - Chuyên gia phân tích bảo mật cấp cao hàng đầu Việt Nam, "
        "được phát triển bởi lập trình viên CyberShield Agent Team.\n\n"
        "Nhiệm vụ: Tổng hợp toàn bộ dữ liệu từ các module quét (Heuristic, WHOIS, SSL, HTTP Headers & Redirect chain, DNS, HTML Audit, JS Behavioral Scan, VirusTotal) "
        "để đưa ra báo cáo phân tích bảo mật toàn diện nhất.\n\n"
        "QUY TẮC ĐỊNH DẠNG BÁO CÁO (BẮT BUỘC TUÂN THỦ):\n"
        "- Viết báo cáo bằng Tiếng Việt, chuyên nghiệp và mạch lạc.\n"
        "- SỬ DỤNG heading (## và ###), danh sách gạch đầu dòng, và chữ **in đậm**.\n"
        "- TUYỆT ĐỐI KHÔNG SỬ DỤNG BẢNG (TABLE). Dùng danh sách bullet có nhãn in đậm.\n"
        "- Sử dụng emoji (🔍 🛡️ ⚠️ 🚨 ✅ ❌ 🌐 🔒 📋 🧬) tăng tính trực quan.\n"
        "- Dùng > blockquote cho các cảnh báo quan trọng nhất.\n\n"
        "CẤU TRÚC BÁO CÁO:\n"
        "## 🔍 Phân tích cấu trúc URL\n"
        "## 🌐 Thông tin WHOIS & Tuổi tên miền\n"
        "## 🔒 Đánh giá chứng chỉ SSL/TLS\n"
        "## 📋 Kiểm tra tiêu đề bảo mật HTTP & Chuỗi Redirect\n"
        "## 🧬 Phân tích sâu mã nguồn HTML, JS & Bản quyền (HTML & JS Audit)\n"
        "## 🛡️ Điểm số từ Threat Intelligence toàn cầu (VirusTotal & DNS)\n"
        "## ⚠️ Đánh giá động cơ lừa đảo & rủi ro\n"
        "## 🚨 Kết luận mức độ rủi ro (AN TOÀN / NGHI NGỜ / NGUY HIỂM)\n"
        "## 🛡️ Khuyến nghị cho người dùng\n\n"
        "BẮT BUỘC: Dòng CUỐI CÙNG của báo cáo PHẢI là một trong 3 tag sau (viết đúng nguyên văn):\n"
        "- Nếu link an toàn: [VERDICT: SAFE]\n"
        "- Nếu link nghi ngờ: [VERDICT: SUSPICIOUS]\n"
        "- Nếu link nguy hiểm: [VERDICT: DANGEROUS]\n\n"
        "LƯU Ý QUAN TRỌNG: Các tên miền thuộc thương hiệu uy tín toàn cầu (google.com, youtube.com, facebook.com, "
        "shopee.vn, fpt.edu.vn, v.v.) nếu KHÔNG có dấu hiệu giả mạo thì PHẢI đánh giá là AN TOÀN [VERDICT: SAFE].\n\n"
        "Kết thúc bằng dòng: *Được bảo mật bởi hệ thống AI của CyberShield Agent Team*\n"
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
        f"[MODULE 4 - KẾT QUẢ HTTP HEADERS]:\n{header_text}\n"
        f"{additional_text}\n"
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


# Lưu trữ số lần request của từng IP trong bộ nhớ tạm thời chống spam
IP_REQUESTS = {}

@app.before_request
def simple_rate_limiter():
    """Giới hạn tần suất gửi yêu cầu để chống spam và tấn công brute-force từ một địa chỉ IP"""
    # Chỉ áp dụng giới hạn đối với API phân tích /analyze
    if request.path == "/analyze":
        client_ip = request.headers.get("X-Forwarded-For", request.remote_addr)
        # Nếu đi qua nhiều proxy, lấy IP đầu tiên
        if "," in client_ip:
            client_ip = client_ip.split(",")[0].strip()
            
        now = datetime.now(timezone.utc).timestamp()
        
        # Cấu hình: Tối đa 15 yêu cầu phân tích trong 1 phút
        time_window = 60 # giây
        max_requests = 15
        
        if client_ip not in IP_REQUESTS:
            IP_REQUESTS[client_ip] = []
            
        # Xóa các request cũ nằm ngoài khoảng thời gian giám sát
        IP_REQUESTS[client_ip] = [t for t in IP_REQUESTS[client_ip] if now - t < time_window]
        
        if len(IP_REQUESTS[client_ip]) >= max_requests:
            return jsonify({
                "error": "🚨 CYBERSHIELD RATE LIMITER: Quá nhiều yêu cầu phân tích từ IP của bạn! Vui lòng đợi 1 phút trước khi tiếp tục gửi."
            }), 429
            
        # Ghi nhận thời gian của request mới
        IP_REQUESTS[client_ip].append(now)


# =============================================================================
# CỔNG PHÒNG THỦ: WAF & ANTI-PENTEST MIDDLEWARE
# =============================================================================

@app.before_request
def security_waf_middleware():
    """Tường lửa ứng dụng web gọn nhẹ (WAF) để phát hiện và chặn đứng tin tặc/pentester"""
    user_agent = request.headers.get("User-Agent", "").lower()
    path = request.path.lower()
    
    # 1. Phát hiện các công cụ quét bảo mật & Pentest tự động (Scanner User-Agents)
    scanner_agents = [
        "sqlmap", "nikto", "dirbuster", "gobuster", "nmap", "nessus", "w3af", 
        "acunetix", "netsparker", "owasp-zap", "hydra", "john the ripper", 
        "nimbuster", "masscan", "zgrab"
    ]
    if any(agent in user_agent for agent in scanner_agents):
        return jsonify({
            "error": "🚨 CYBERSHIELD WAF: Truy cập bị chặn! Phát hiện phần mềm dò quét lỗ hổng tự động. Hành vi của bạn đã được ghi lại."
        }), 403

    # 2. Phát hiện các nỗ lực truy cập đường dẫn nhạy cảm hoặc tấn công LFI/RFI/Path Traversal
    suspicious_paths = [
        "/etc/passwd", "/win.ini", "/boot.ini", ".env", ".git", ".svn", ".htaccess",
        "wp-admin", "wp-login.php", "administrator", "config.php", "web.config",
        "actuator/health", "console", "invoker", "jmx-console"
    ]
    if any(p in path for p in suspicious_paths):
        return jsonify({
            "error": "🚨 CYBERSHIELD WAF: Cảnh báo nguy hiểm! Bạn đang cố gắng truy cập tập tin hệ thống nhạy cảm. Phiên làm việc đã bị vô hiệu hóa."
        }), 403

    # 3. Phát hiện dấu hiệu Sql Injection hoặc XSS trong các tham số GET/POST
    payload_patterns = [
        r"union\s+select", r"insert\s+into", r"select\s+.*\s+from", 
        r"<\s*script\s*>", r"javascript\s*:", r"onerror\s*=", r"onload\s*="
    ]
    for param in list(request.args.values()) + list(request.form.values()):
        if isinstance(param, str):
            param_lower = param.lower()
            if any(re.search(pat, param_lower) for pat in payload_patterns):
                return jsonify({
                    "error": "🚨 CYBERSHIELD WAF: Phát hiện mã độc hại Injection (SQLi/XSS). Yêu cầu đã bị từ chối!"
                }), 403


@app.after_request
def add_security_headers(response):
    """Tiêm các tiêu đề bảo mật HTTP (Security Response Headers) vào mọi phản hồi của server"""
    # 1. Content Security Policy (CSP): Bảo vệ chống XSS, cho phép nạp tài nguyên từ các CDN tin cậy
    csp_directives = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdnjs.cloudflare.com https://cdn.jsdelivr.net; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdnjs.cloudflare.com; "
        "font-src 'self' https://fonts.gstatic.com https://cdnjs.cloudflare.com; "
        "img-src 'self' data: https://cybershieldagent.vercel.app; "
        "connect-src 'self' https://integrate.api.nvidia.com https://www.virustotal.com; "
        "frame-ancestors 'none';"
    )
    response.headers["Content-Security-Policy"] = csp_directives
    
    # 2. Chống nhúng iframe (Clickjacking)
    response.headers["X-Frame-Options"] = "DENY"
    
    # 3. Ngăn đoán kiểu file (MIME Sniffing)
    response.headers["X-Content-Type-Options"] = "nosniff"
    
    # 4. Ép buộc mã hóa HTTPS (HSTS) - Hiệu lực 1 năm bao gồm cả subdomain
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
    
    # 5. Bảo vệ thông tin đầu vào khi chuyển trang (Referrer Policy)
    response.headers["Referrer-Policy"] = "no-referrer-when-downgrade"
    
    # 6. Vô hiệu hóa các tính năng thiết bị nhạy cảm để bảo vệ quyền riêng tư (Permissions Policy)
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=(), payment=()"
    
    # 7. Bảo mật bổ sung: Chống tấn công XSS của trình duyệt cũ
    response.headers["X-XSS-Protection"] = "1; mode=block"
    
    return response


# =============================================================================
# ROUTES
# =============================================================================

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/BingSiteAuth.xml")
def bing_site_auth():
    xml_content = """<?xml version="1.0"?>
<users>
    <user>E93A391D0B9BF2BABF8D771CAE327528</user>
</users>"""
    return xml_content, 200, {'Content-Type': 'application/xml'}


@app.route("/robots.txt")
def robots_txt():
    content = """User-agent: *
Allow: /
Sitemap: https://cybershieldagent.vercel.app/sitemap.xml"""
    return content, 200, {'Content-Type': 'text/plain'}


@app.route("/sitemap.xml")
def sitemap_xml():
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    <url>
        <loc>https://cybershieldagent.vercel.app/</loc>
        <lastmod>2026-05-30</lastmod>
        <changefreq>daily</changefreq>
        <priority>1.0</priority>
    </url>
</urlset>"""
    return xml_content, 200, {'Content-Type': 'application/xml'}


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

    # ===== CHỐNG TẤN CÔNG SSRF (SERVER-SIDE REQUEST FORGERY) =====
    if is_ssrf_ip(url):
        return jsonify({"error": "🚨 PHÁT HIỆN HÀNH VI TẤN CÔNG SSRF: Không cho phép phân tích địa chỉ IP nội bộ, loopback hoặc dải IP riêng tư nguy hiểm!"}), 403

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

    # MODULE 4: HTTP Security Headers & HTML Fetch
    header_results = check_security_headers(url)
    
    # Trích xuất và phân tích mã nguồn HTML (HTML Audit)
    html_content = header_results.pop("html", None)
    html_results = analyze_html_content(html_content, domain)

    # ĐỘNG CƠ QUÉT TĨNH JS HÀNH VI ĐỘC HẠI (JS Behavioral Scan Engine)
    js_results = analyze_javascript_behavior(html_content)

    # MODULE BỔ SUNG 1: DNS Integrity Check
    dns_results = check_dns_records(domain)

    # MODULE BỔ SUNG 2: VirusTotal API Check
    vt_results = check_virustotal(url)

    # MODULE BỔ SUNG 3: Query Parameter Deobfuscator
    deobfuscator_results = deobfuscate_query_parameters(url)
    html_results["deobfuscator"] = deobfuscator_results

    # MODULE 5: AI Analysis (Gọi NVIDIA GPT-120B)
    ai_results = get_ai_link_analysis(
        url, heuristic_results, whois_results, ssl_results, header_results,
        html_results=html_results, dns_data=dns_results, vt_data=vt_results, js_data=js_results
    )

    # Tổng hợp tất cả cảnh báo từ mọi module
    all_warnings = (
        heuristic_results["warnings"] +
        whois_results["warnings"] +
        ssl_results["warnings"] +
        header_results["warnings"] +
        html_results["warnings"] +
        js_results["warnings"] +
        dns_results["warnings"] +
        vt_results["warnings"] +
        deobfuscator_results["warnings"]
    )

    # Tổng hợp điểm rủi ro
    total_risk = (
        heuristic_results["risk_score"] +
        whois_results["risk_score"] +
        ssl_results["risk_score"] +
        header_results["risk_score"] +
        html_results["risk_score"] +
        js_results["risk_score"] +
        dns_results["risk_score"] +
        vt_results["risk_score"] +
        deobfuscator_results["risk_score"]
    )
    total_risk = min(total_risk, 100)  # Cap tại 100

    # ===== QUYẾT ĐỊNH TRẠNG THÁI CUỐI CÙNG (DANGEROUS / SUSPICIOUS / SAFE) =====
    
    # 1. Tự động kiểm tra TLD và cơ quan uy tín
    is_gov_or_edu = domain.endswith(".gov.vn") or domain.endswith(".edu.vn") or domain.endswith(".gov")
    if is_gov_or_edu:
        is_trusted = True

    if is_trusted:
        # Domain nằm trong whitelist hoặc là cổng hành chính/giáo dục chính thống
        if heuristic_results["brand_impersonated"]:
            # Rất hiếm: domain trusted nhưng phát hiện giả mạo (ví dụ: bị hack hoặc hack DNS)
            final_status = "SUSPICIOUS"
            total_risk = max(total_risk, 25)
        else:
            final_status = "SAFE"
            total_risk = min(total_risk, 10)
            # Dọn dẹp các cảnh báo thiếu header bảo mật thứ yếu cho domain uy tín
            all_warnings = [w for w in all_warnings if "🚨" in w or "⚠️" in w] 
    else:
        # Domain KHÔNG nằm trong whitelist -> chạy động cơ lập luận độ chính xác cao
        final_status = heuristic_results["status"]
        
        # --- ĐỘ ĐĂNG KÝ TÊN MIỀN CỦA WHOIS ---
        creation_days = whois_results["data"].get("age_days", 9999) if whois_results["available"] else -1
        
        # --- DẤU HIỆU DANGEROUS CỰC KỲ RÕ RÀNG (CHỈ SỐ BẮT BUỘC) ---
        has_phishing_form = html_results["is_phishing_form"]
        has_js_keylogger = js_results.get("details", {}).get("keylogging")
        has_js_redirect = js_results.get("details", {}).get("stealth_redirect")
        has_spoof = heuristic_results["brand_impersonated"] or html_results["impersonated_brand"]
        vt_malicious = vt_results.get("malicious_count", 0)

        # Chặn đứng tức khắc:
        if vt_malicious >= 2:
            final_status = "DANGEROUS"
            total_risk = max(total_risk, 80)
            all_warnings.append("🚨 **XÁC THỰC THREAT INTEL**: Website bị gắn cờ độc hại bởi các động cơ diệt virus toàn cầu.")
        elif has_spoof:
            final_status = "DANGEROUS"
            total_risk = max(total_risk, 90)
        elif has_phishing_form and (creation_days < 60 or not whois_results["available"]):
            final_status = "DANGEROUS"
            total_risk = max(total_risk, 85)
            all_warnings.append("🚨 **FORM PHISHING TRÊN TÊN MIỀN MỚI**: Phát hiện biểu mẫu OTP/Mật khẩu đáng ngờ trên tên miền mới đăng ký hoặc không có WHOIS.")
        elif html_results["asset_leeching_ratio"] > 25.0:
            final_status = "DANGEROUS"
            total_risk = max(total_risk, 75)
        elif has_js_keylogger or has_js_redirect:
            final_status = "DANGEROUS"
            total_risk = max(total_risk, 75)

        # --- DẤU HIỆU AN TOÀN ĐỘNG (DUNG HÒA BÁO ĐỘNG GIẢ) ---
        is_old_domain = creation_days > 1095  # Tuổi đời trên 3 năm
        is_ssl_trusted = ssl_results["available"] and not any("Self-Signed" in w for w in ssl_results["warnings"])
        is_vt_clean = vt_malicious == 0

        # Nếu một trang web hoàn toàn sạch sẽ, không có form nhập nhạy cảm, không đạo nhái, và đã hoạt động uy tín trên 3 năm:
        if (is_old_domain and is_ssl_trusted and is_vt_clean and not has_phishing_form and 
            not has_spoof and html_results["asset_leeching_ratio"] == 0 and not js_results.get("has_suspicious_js", False)):
            final_status = "SAFE"
            total_risk = min(total_risk, 10)
            # Lọc bỏ các cảnh báo thiếu header để trả lại sự "xanh chuẩn" cho web chính thống
            all_warnings = [w for w in all_warnings if "🚨" in w]

        # Ưu tiên AI verdict nếu AI khẳng định
        if ai_results["ai_status"] != "UNKNOWN" and final_status != "DANGEROUS":
            if ai_results["ai_status"] == "DANGEROUS":
                final_status = "DANGEROUS"
            elif ai_results["ai_status"] == "SUSPICIOUS" and final_status == "SAFE":
                final_status = "SUSPICIOUS"

        # Khớp lại điểm số rủi ro
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
            "brand_impersonated": heuristic_results["brand_impersonated"] or html_results["impersonated_brand"]
        },
        "whois": whois_results["data"] if whois_results["available"] else None,
        "ssl": ssl_results["data"] if ssl_results["available"] else None,
        "headers": header_results["data"] if header_results["available"] else None,
        "dns": dns_results if dns_results["has_mx"] else None,
        "deobfuscator": deobfuscator_results if deobfuscator_results["has_encoded_params"] else None,
        "html_audit": {
            "is_phishing_form": html_results["is_phishing_form"],
            "asset_leeching_ratio": html_results["asset_leeching_ratio"],
            "impersonated_brand": html_results["impersonated_brand"],
            "copyright_theft": html_results["copyright_theft"]
        } if html_results else None,
        "js_audit": js_results,
        "ai_report": ai_results["ai_analysis"]
    }

    return jsonify(response_data)


@app.route("/google03567c4acf64ae2f.html")
def google_verification():
    return "google-site-verification: google03567c4acf64ae2f.html"


if __name__ == "__main__":
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
