/* ==========================================================================
   Cyberpunk UI JS Controller
   Project: AI Phishing Link Analyzer (Tiến Shield AI)
   Author: Nguyễn Xuân Tiến
   ========================================================================== */

document.addEventListener("DOMContentLoaded", () => {
    // UI Elements
    const analyzeForm = document.getElementById("analyzeForm");
    const targetUrlInput = document.getElementById("targetUrl");
    const submitBtn = document.getElementById("submitBtn");
    const inputCard = document.getElementById("inputCard");
    const loadingCard = document.getElementById("loadingCard");
    const resultsArea = document.getElementById("resultsArea");
    const terminalLogs = document.getElementById("terminalLogs");
    const historyList = document.getElementById("historyList");
    
    // Result Elements
    const statusCard = document.getElementById("statusCard");
    const riskScoreText = document.getElementById("riskScore");
    const riskGauge = document.getElementById("riskGauge");
    const statusLabel = document.getElementById("statusLabel");
    const statusDesc = document.getElementById("statusDesc");
    const urlDisplay = document.getElementById("urlDisplay");
    const warningsList = document.getElementById("warningsList");
    const aiReportContent = document.getElementById("aiReportContent");
    
    // Action Buttons
    const resetBtn = document.getElementById("resetBtn");
    const copyReportBtn = document.getElementById("copyReportBtn");
    const exampleBtns = document.querySelectorAll(".example-btn");
    const clearHistoryBtn = document.getElementById("clearHistoryBtn");

    // Mobile Responsive Elements
    const mobileMenuBtn = document.getElementById("mobileMenuBtn");
    const appSidebar = document.getElementById("appSidebar");
    const closeSidebarBtn = document.getElementById("closeSidebarBtn");
    const sidebarBackdrop = document.getElementById("sidebarBackdrop");

    // Hàm mở/đóng Sidebar Drawer trên di động
    function openSidebar() {
        if (appSidebar) appSidebar.classList.add("active");
        if (sidebarBackdrop) sidebarBackdrop.classList.add("active");
    }

    function closeSidebar() {
        if (appSidebar) appSidebar.classList.remove("active");
        if (sidebarBackdrop) sidebarBackdrop.classList.remove("active");
    }

    // Gắn sự kiện điều khiển Sidebar di động
    if (mobileMenuBtn) {
        mobileMenuBtn.addEventListener("click", openSidebar);
    }
    if (closeSidebarBtn) {
        closeSidebarBtn.addEventListener("click", closeSidebar);
    }
    if (sidebarBackdrop) {
        sidebarBackdrop.addEventListener("click", closeSidebar);
    }

    // Lịch sử quét ảo
    let scanHistory = JSON.parse(localStorage.getItem("tienshield_history")) || [];

    // Khởi tạo Lịch sử
    renderHistory();

    // 1. Xử lý gửi Form Phân tích
    analyzeForm.addEventListener("submit", (e) => {
        e.preventDefault();
        const url = targetUrlInput.value.trim();
        if (url) {
            startAnalysis(url);
        }
    });

    // 2. Click các nút ví dụ
    exampleBtns.forEach(btn => {
        btn.addEventListener("click", () => {
            const url = btn.getAttribute("data-url");
            targetUrlInput.value = url;
            startAnalysis(url);
        });
    });

    // 3. Nút phân tích lại
    resetBtn.addEventListener("reset", resetUI);
    resetBtn.addEventListener("click", resetUI);

    // 3.5. Nút Xóa Lịch sử quét
    if (clearHistoryBtn) {
        clearHistoryBtn.addEventListener("click", () => {
            if (confirm("Bạn có chắc chắn muốn xóa toàn bộ lịch sử quét lưu trên máy này không?")) {
                scanHistory = [];
                localStorage.removeItem("tienshield_history");
                renderHistory();
            }
        });
    }

    // 4. Nút Sao chép Báo cáo
    copyReportBtn.addEventListener("click", () => {
        const textToCopy = aiReportContent.innerText;
        navigator.clipboard.writeText(textToCopy).then(() => {
            const originalText = copyReportBtn.innerHTML;
            copyReportBtn.innerHTML = `<i class="fa-solid fa-check"></i> Đã Sao Chép!`;
            setTimeout(() => {
                copyReportBtn.innerHTML = originalText;
            }, 2000);
        });
    });

    // 5. Hệ thống chuyển đổi Tab trong Diagnostics Terminal
    const tabBtns = document.querySelectorAll(".tab-btn");
    const tabContents = document.querySelectorAll(".tab-content");
    
    tabBtns.forEach(btn => {
        btn.addEventListener("click", () => {
            tabBtns.forEach(b => b.classList.remove("active"));
            tabContents.forEach(c => c.classList.remove("active"));
            
            btn.classList.add("active");
            const tabId = btn.getAttribute("data-tab");
            document.getElementById(`tab-${tabId}`).classList.add("active");
        });
    });

    // Hàm đặt lại giao diện
    function resetUI() {
        resultsArea.classList.add("hidden");
        loadingCard.classList.add("hidden");
        inputCard.classList.remove("hidden");
        targetUrlInput.value = "";
        targetUrlInput.focus();
    }

    // Tiến trình quét đường link
    async function startAnalysis(url) {
        // Chuyển giao diện sang Màn hình quét
        inputCard.classList.add("hidden");
        loadingCard.classList.remove("hidden");
        terminalLogs.innerHTML = ""; // Xóa console log cũ
        
        // Bắt đầu in log terminal mô phỏng (5 MODULE QUÉT)
        const logs = [
            { text: "> [SYS] Khởi động CyberShield AI Engine v2.0...", delay: 200, type: "info" },
            { text: `> [SYS] Nạp mục tiêu: ${url}`, delay: 400, type: "info" },
            { text: "> ─────────────────────────────────────────────────", delay: 600, type: "info" },
            { text: "> [MODULE 1/7] HEURISTIC SCANNER", delay: 800, type: "success" },
            { text: ">   ├─ Quét cấu trúc URL, giao thức, TLD...", delay: 1000, type: "info" },
            { text: ">   ├─ Phát hiện Typo-squatting (Levenshtein Distance)...", delay: 1200, type: "info" },
            { text: ">   ├─ Quét Homograph Attack (Unicode giả dạng)...", delay: 1400, type: "info" },
            { text: ">   └─ Tính toán Shannon Entropy (Mức hỗn loạn DGA)...", delay: 1600, type: "info" },
            { text: "> [MODULE 2/7] WHOIS DOMAIN LOOKUP", delay: 1800, type: "success" },
            { text: ">   ├─ Truy xuất thông tin đăng ký tên miền...", delay: 2000, type: "info" },
            { text: ">   └─ Phân tích tuổi tên miền & nhà đăng ký...", delay: 2200, type: "info" },
            { text: "> [MODULE 3/7] SSL/TLS CERTIFICATE CHECK", delay: 2400, type: "success" },
            { text: ">   ├─ Kết nối TLS tới máy chủ mục tiêu...", delay: 2600, type: "info" },
            { text: ">   └─ Xác minh chứng chỉ SSL & tổ chức cấp...", delay: 2800, type: "info" },
            { text: "> [MODULE 4/7] HTTP SECURITY HEADERS AUDIT", delay: 3000, type: "success" },
            { text: ">   ├─ Gửi yêu cầu HTTP & theo dõi Redirect chain...", delay: 3200, type: "info" },
            { text: ">   └─ Kiểm tra CSP, HSTS, X-Frame-Options...", delay: 3400, type: "info" },
            { text: "> [MODULE 5/7] HTML & ASSET CLONING AUDIT", delay: 3600, type: "success" },
            { text: ">   ├─ Tải mã nguồn HTML & Quét trường đăng nhập (OTP/Password)...", delay: 3800, type: "info" },
            { text: ">   └─ Kiểm tra tỷ lệ Asset Leeching & Copyright Theft...", delay: 4000, type: "info" },
            { text: "> [MODULE 6/7] DNS INTEGRITY AUDIT", delay: 4200, type: "success" },
            { text: ">   └─ Kiểm tra bản ghi MX Mail Server...", delay: 4400, type: "info" },
            { text: "> [MODULE 7/7] GLOBAL THREAT INTEL INTEGRATION (VIRUSTOTAL)", delay: 4600, type: "success" },
            { text: ">   └─ Truy xuất cơ sở dữ liệu mối đe dọa toàn cầu...", delay: 4800, type: "info" },
            { text: "> [MODULE AI] NVIDIA GPT-120B AI THREAT INTEL", delay: 5100, type: "success" },
            { text: ">   ├─ Đóng gói ngữ cảnh từ 7 module gửi tới AI...", delay: 5400, type: "info" },
            { text: ">   └─ Đang chờ AI phân tích hành vi lừa đảo...", delay: 5700, type: "info" },
            { text: "> ─────────────────────────────────────────────────", delay: 6500, type: "info" },
            { text: "> [SYS] Tổng hợp dữ liệu & chấm điểm rủi ro...", delay: 6800, type: "info" },
            { text: "> [SYS] ✓ HOÀN TẤT! Kết xuất Dashboard kết quả...", delay: 7000, type: "success" }
        ];

        // Chạy song song API Request thực tế
        const apiPromise = fetch("/analyze", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ url: url })
        }).then(res => {
            if (!res.ok) throw new Error("Lỗi máy chủ phân tích");
            return res.json();
        });

        // Hàm in log từng dòng theo delay mô phỏng
        for (const log of logs) {
            await new Promise(resolve => setTimeout(resolve, log.delay - (logs.indexOf(log) > 0 ? logs[logs.indexOf(log) - 1].delay : 0)));
            printTerminalLog(log.text, log.type);
        }

        try {
            // Chờ kết quả API thực tế (đảm bảo in xong log tối thiểu)
            const result = await apiPromise;
            
            // Hiển thị kết quả lên màn hình
            displayResults(result);
            
            // Lưu vào lịch sử
            saveToHistory(result);
            
        } catch (error) {
            printTerminalLog(`> [!] LỖI HỆ THỐNG: ${error.message}`, "danger");
            printTerminalLog(`> [!] Vui lòng đảm bảo Flask Server đang chạy và .env cấu hình đúng API Key.`, "warning");
            
            // Nút khôi phục lại
            setTimeout(() => {
                resetUI();
                alert(`Không thể phân tích: ${error.message}. Vui lòng thử lại.`);
            }, 3000);
        }
    }

    // In log vào Terminal ảo
    function printTerminalLog(text, type = "info") {
        const row = document.createElement("div");
        row.className = `log-row ${type}`;
        row.innerText = text;
        terminalLogs.appendChild(row);
        terminalLogs.scrollTop = terminalLogs.scrollHeight;
    }

    // Hiển thị kết quả phân tích
    function displayResults(data) {
        // 1. Ẩn loading, hiện màn hình kết quả
        loadingCard.classList.add("hidden");
        resultsArea.classList.remove("hidden");

        // 2. Thiết lập trạng thái màu sắc cho Status Card
        statusCard.className = "card status-card"; // reset classes
        let statusClass = "state-safe";
        let statusText = "✅ AN TOÀN";
        let statusDescription = "Đường dẫn thuộc tên miền uy tín, không phát hiện dấu hiệu giả mạo hay cấu trúc độc hại. Bạn có thể yên tâm truy cập.";
        let gaugeColor = "#39ff14"; // Neon Green
        
        if (data.status === "DANGEROUS") {
            statusClass = "state-dangerous";
            statusText = "🚨 NGUY HIỂM";
            statusDescription = "CẢNH BÁO KHẨN CẤP: Phát hiện dấu hiệu lừa đảo giả mạo hoặc liên kết thu thập thông tin độc hại. Tuyệt đối KHÔNG TRUY CẬP!";
            gaugeColor = "#ff0055"; // Neon Red
        } else if (data.status === "SUSPICIOUS") {
            statusClass = "state-suspicious";
            statusText = "⚠️ NGHI NGỜ";
            statusDescription = "Đường link có một số dấu hiệu bất thường. Cần xác minh kỹ trước khi nhấn vào hoặc nhập thông tin cá nhân.";
            gaugeColor = "#ffdf00"; // Neon Yellow
        }
        
        statusCard.classList.add(statusClass);
        statusLabel.innerText = statusText;
        statusDesc.innerText = statusDescription;
        urlDisplay.innerText = data.url;

        // 3. Animate Điểm số Rủi ro (Circular Gauge) với MÀU ĐÚNG
        let currentScore = 0;
        const targetScore = data.risk_score;
        const radius = 40;
        const circumference = 2 * Math.PI * radius; // ~251.2
        
        // Đặt dasharray ban đầu + màu gauge
        riskGauge.style.strokeDasharray = circumference;
        riskGauge.style.stroke = gaugeColor;
        riskGauge.style.filter = `drop-shadow(0 0 6px ${gaugeColor})`;
        
        const interval = setInterval(() => {
            if (currentScore >= targetScore) {
                clearInterval(interval);
            } else {
                currentScore++;
                riskScoreText.innerText = currentScore;
                
                // Tính offset lùi
                const offset = circumference - (circumference * currentScore) / 100;
                riskGauge.style.strokeDashoffset = offset;
            }
        }, 10);

        // 4. Điền danh sách cảnh báo quét tĩnh (Heuristics)
        warningsList.innerHTML = "";
        if (data.heuristics.warnings && data.heuristics.warnings.length > 0) {
            data.heuristics.warnings.forEach(warning => {
                const item = document.createElement("div");
                item.className = `warning-item ${data.status === "DANGEROUS" ? "danger-warn" : ""}`;
                item.innerHTML = `
                    <i class="fa-solid fa-circle-exclamation warning-icon"></i>
                    <div class="warning-text">${warning}</div>
                `;
                warningsList.appendChild(item);
            });
        } else {
            warningsList.innerHTML = `
                <div class="no-warnings">
                    <i class="fa-solid fa-circle-check"></i>
                    <span>Tuyệt vời! Không phát hiện dấu hiệu bất thường nào từ quét Heuristic tĩnh.</span>
                </div>
            `;
        }

        // 5. Render Báo cáo AI chuyên sâu bằng Marked.js
        if (window.marked) {
            aiReportContent.innerHTML = marked.parse(data.ai_report);
        } else {
            aiReportContent.innerText = data.ai_report;
        }

        // Kích hoạt highlight.js nếu có block code
        if (window.hljs) {
            document.querySelectorAll(".ai-report-content pre code").forEach((el) => {
                hljs.highlightElement(el);
            });
        }

        // 6. Điền động dữ liệu vào các Tab chẩn đoán nâng cao
        
        // --- TAB 3: HTML & DEOBFUSCATOR ---
        const htmlAuditDetails = document.getElementById("htmlAuditDetails");
        if (data.html_audit) {
            const audit = data.html_audit;
            let auditHtml = `<div class="diagnostic-item">
                <span class="diagnostic-label">Trường thu thập thông tin nhạy cảm (Password/OTP)</span>
                <span class="diagnostic-value ${audit.is_phishing_form ? 'red-alert' : 'green-ok'}">${audit.is_phishing_form ? '🚨 CÓ FORM NHẬP OTP/PASSWORD' : '✓ Không phát hiện'}</span>
            </div>`;
            if (audit.asset_leeching_ratio > 0) {
                auditHtml += `<div class="diagnostic-item">
                    <span class="diagnostic-label">Tỷ lệ đạo nhái giao diện (Asset Leeching)</span>
                    <span class="diagnostic-value red-alert">${audit.asset_leeching_ratio}%</span>
                </div>
                <div class="diagnostic-item">
                    <span class="diagnostic-label">Thương hiệu bị mạo danh</span>
                    <span class="diagnostic-value red-alert">${audit.impersonated_brand}</span>
                </div>`;
            } else {
                auditHtml += `<div class="diagnostic-item">
                    <span class="diagnostic-label">Đạo nhái tài nguyên thương hiệu</span>
                    <span class="diagnostic-value green-ok">✓ Không phát hiện</span>
                </div>`;
            }
            if (audit.copyright_theft) {
                auditHtml += `<div class="diagnostic-item">
                    <span class="diagnostic-label">Nhái bản quyền thương hiệu</span>
                    <span class="diagnostic-value red-alert">🚨 ĐÁNH CẮP BẢN QUYỀN (${audit.impersonated_brand})</span>
                </div>`;
            } else {
                auditHtml += `<div class="diagnostic-item">
                    <span class="diagnostic-label">Đánh cắp bản quyền thương hiệu</span>
                    <span class="diagnostic-value green-ok">✓ Không phát hiện</span>
                </div>`;
            }
            htmlAuditDetails.innerHTML = auditHtml;
        } else {
            htmlAuditDetails.innerHTML = "Không có thông tin quét HTML.";
        }

        const deobfuscatorDetails = document.getElementById("deobfuscatorDetails");
        if (data.deobfuscator && data.deobfuscator.has_encoded_params) {
            let deobHtml = `<p style="font-size:12px; color:rgba(255,255,255,0.5); margin-bottom:10px;">Phát hiện các tham số truy vấn được mã hóa. Đã giải mã thành công:</p>`;
            for (const [key, val] of Object.entries(data.deobfuscator.decoded_params)) {
                deobHtml += `<div class="diagnostic-item">
                    <span class="diagnostic-label" style="font-family:monospace; color:var(--neon-red); font-size:11px;">${key}</span>
                    <span class="diagnostic-value" style="font-family:monospace; color:#fff; background:rgba(255,0,85,0.15); padding:2px 6px; border-radius:3px; font-size:11px;">${val}</span>
                </div>`;
            }
            deobfuscatorDetails.innerHTML = deobHtml;
        } else {
            deobfuscatorDetails.innerHTML = `<div class="no-warnings" style="margin: 0; padding: 10px;">
                <i class="fa-solid fa-circle-check" style="color:var(--neon-green)"></i>
                <span style="color:rgba(255,255,255,0.6)">Không phát hiện bất kỳ tham số truy vấn mã hóa đáng ngờ nào (Base64/Hex).</span>
            </div>`;
        }

        const jsAuditDetails = document.getElementById("jsAuditDetails");
        if (data.js_audit) {
            const js = data.js_audit;
            if (js.has_suspicious_js) {
                let jsHtml = `<p style="font-size:12px; color:var(--neon-orange); margin-bottom:10px; font-weight:600;"><i class="fa-solid fa-triangle-exclamation"></i> Phát hiện hành vi script bất thường/độc hại:</p>`;
                js.warnings.forEach(warn => {
                    jsHtml += `<div class="diagnostic-item" style="border-left: 2px solid var(--neon-red); padding-left: 8px; margin-bottom: 8px; background: rgba(255, 0, 85, 0.05);">
                        <span class="diagnostic-value" style="text-align:left; color:#fff; font-size:12px; padding:0;">${warn}</span>
                    </div>`;
                });
                
                jsHtml += `<div style="margin-top:15px; border-top:1px solid rgba(255,255,255,0.05); padding-top:10px;">`;
                jsHtml += `<div class="diagnostic-item"><span class="diagnostic-label">Chống Debugger/DevTools</span><span class="diagnostic-value ${js.details.anti_devtools ? 'red-alert' : 'green-ok'}">${js.details.anti_devtools ? '🚨 PHÁT HIỆN' : '✓ Không có'}</span></div>`;
                jsHtml += `<div class="diagnostic-item"><span class="diagnostic-label">Chặn click chuột phải</span><span class="diagnostic-value ${js.details.right_click_blocking ? 'red-alert' : 'green-ok'}">${js.details.right_click_blocking ? '🚨 PHÁT HIỆN' : '✓ Không có'}</span></div>`;
                jsHtml += `<div class="diagnostic-item"><span class="diagnostic-label">Ghi nhận thao tác phím (Keylogger)</span><span class="diagnostic-value ${js.details.keylogging ? 'red-alert' : 'green-ok'}">${js.details.keylogging ? '🚨 PHÁT HIỆN' : '✓ Không có'}</span></div>`;
                jsHtml += `<div class="diagnostic-item"><span class="diagnostic-label">Chuyển hướng động ẩn (Stealth Redirect)</span><span class="diagnostic-value ${js.details.stealth_redirect ? 'red-alert' : 'green-ok'}">${js.details.stealth_redirect ? '🚨 PHÁT HIỆN' : '✓ Không có'}</span></div>`;
                jsHtml += `<div class="diagnostic-item"><span class="diagnostic-label">Truyền dữ liệu ngầm (Beacon Exfiltration)</span><span class="diagnostic-value ${js.details.exfiltration ? 'red-alert' : 'green-ok'}">${js.details.exfiltration ? '🚨 PHÁT HIỆN' : '✓ Không có'}</span></div>`;
                jsHtml += `</div>`;
                
                jsAuditDetails.innerHTML = jsHtml;
            } else {
                jsAuditDetails.innerHTML = `<div class="no-warnings" style="margin: 0; padding: 10px;">
                    <i class="fa-solid fa-circle-check" style="color:var(--neon-green)"></i>
                    <span style="color:rgba(255,255,255,0.6)">Không phát hiện hành vi JavaScript bất thường nào (Anti-DevTools, Keylogger, Redirect...).</span>
                </div>`;
            }
        } else {
            jsAuditDetails.innerHTML = `<div class="no-warnings" style="margin: 0; padding: 10px;">
                <i class="fa-solid fa-circle-check" style="color:var(--neon-green)"></i>
                <span style="color:rgba(255,255,255,0.6)">Không phát hiện tập lệnh JavaScript đáng ngờ nào trong mã nguồn HTML.</span>
            </div>`;
        }

        // --- TAB 4: WHOIS & DNS ---
        const whoisDetails = document.getElementById("whoisDetails");
        if (data.whois) {
            let whoisHtml = "";
            for (const [key, val] of Object.entries(data.whois)) {
                whoisHtml += `<div class="diagnostic-item">
                    <span class="diagnostic-label">${key}</span>
                    <span class="diagnostic-value">${val}</span>
                </div>`;
            }
            whoisDetails.innerHTML = whoisHtml || "Không có chi tiết.";
        } else {
            whoisDetails.innerHTML = `<div style="border-left:2px solid var(--neon-red); padding:10px; background:rgba(255,0,85,0.05); color:var(--neon-red); font-weight:600; font-family:'Orbitron', sans-serif; font-size:12px; border-radius:4px;">
                🚨 THIẾU THÔNG TIN WHOIS: Không có dữ liệu đăng ký WHOIS (Tên miền trôi nổi hoặc bị ẩn thông tin).
            </div>`;
        }

        const dnsDetails = document.getElementById("dnsDetails");
        if (data.dns && data.dns.has_mx) {
            let dnsHtml = `<div class="diagnostic-item">
                <span class="diagnostic-label">Có Mail Server (MX Record)</span>
                <span class="diagnostic-value green-ok">✓ ĐÃ CẤU HÌNH</span>
            </div>`;
            if (data.dns.mx_servers && data.dns.mx_servers.length > 0) {
                dnsHtml += `<div class="diagnostic-item">
                    <span class="diagnostic-label">Máy chủ nhận thư</span>
                    <span class="diagnostic-value">${data.dns.mx_servers.join(", ")}</span>
                </div>`;
            }
            dnsDetails.innerHTML = dnsHtml;
        } else {
            dnsDetails.innerHTML = `<div class="diagnostic-item" style="border-left:2px solid var(--neon-red); padding:10px; background:rgba(255,0,85,0.05); border-radius:4px; margin-bottom:8px;">
                <span class="diagnostic-label" style="color:var(--neon-red)">Cấu hình Mail Server (MX Record)</span>
                <span class="diagnostic-value red-alert" style="color:var(--neon-red); font-weight:800; text-shadow:0 0 5px rgba(255,0,85,0.3);">🚨 THIẾU MX RECORD</span>
            </div>
            <p style="font-size:11px; color:rgba(255,255,255,0.4); margin-top:8px;">Hầu hết các ngân hàng hoặc tổ chức lớn luôn cấu hình MX Record để nhận thư điện tử. Việc thiếu MX record là một dấu hiệu bất thường đối với các trang tuyên bố thuộc thương hiệu lớn.</p>`;
        }

        // --- TAB 5: SSL CERT ---
        const sslDetails = document.getElementById("sslDetails");
        if (data.ssl) {
            let sslHtml = "";
            for (const [key, val] of Object.entries(data.ssl)) {
                sslHtml += `<div class="diagnostic-item">
                    <span class="diagnostic-label">${key}</span>
                    <span class="diagnostic-value">${val}</span>
                </div>`;
            }
            sslDetails.innerHTML = sslHtml || "Không có chi tiết.";
        } else {
            sslDetails.innerHTML = `<div style="border-left:2px solid var(--neon-red); padding:10px; background:rgba(255,0,85,0.05); color:var(--neon-red); font-weight:600; font-family:'Orbitron', sans-serif; font-size:12px; border-radius:4px;">
                🚨 THIẾU BẢO MẬT SSL/TLS: Không truy cập được chứng chỉ bảo mật hoặc máy chủ không sử dụng giao thức bảo mật HTTPS!
            </div>`;
        }

        // --- TAB 6: HTTP HEADERS ---
        const headersDetails = document.getElementById("headersDetails");
        if (data.headers) {
            let headersHtml = `<div class="diagnostic-item">
                <span class="diagnostic-label">Trạng thái HTTP</span>
                <span class="diagnostic-value">${data.headers.status_code || "N/A"}</span>
            </div>
            <div class="diagnostic-item">
                <span class="diagnostic-label">Máy chủ dịch vụ (Server)</span>
                <span class="diagnostic-value">${data.headers.server || "N/A"}</span>
            </div>`;
            if (data.headers.present_headers && data.headers.present_headers.length > 0) {
                headersHtml += `<div class="diagnostic-item">
                    <span class="diagnostic-label" style="color:var(--neon-green)">Tiêu đề bảo mật đã thiết lập</span>
                    <span class="diagnostic-value green-ok" style="font-size:11px;">${data.headers.present_headers.join(", ")}</span>
                </div>`;
            }
            if (data.headers.missing_headers && data.headers.missing_headers.length > 0) {
                headersHtml += `<div class="diagnostic-item" style="border-left:2px solid var(--neon-red); padding:10px; background:rgba(255,0,85,0.05); border-radius:4px; margin-top:10px; flex-direction:column; align-items:flex-start; gap:8px;">
                    <span class="diagnostic-label" style="color:var(--neon-red); font-weight:700; font-family:'Orbitron', sans-serif; font-size:11px;">🚨 TIÊU ĐỀ BẢO MẬT CÒN THIẾU (MISSING SECURE HEADERS)</span>
                    <div style="display:flex; flex-wrap:wrap; gap:6px; margin-top:4px;">
                        ${data.headers.missing_headers.map(h => `<span style="color:#fff; background:rgba(255,0,85,0.25); border:1px solid var(--neon-red); padding:2px 6px; border-radius:4px; font-size:10px; font-family:monospace; font-weight:600; text-shadow:0 0 4px var(--neon-red);">${h}</span>`).join("")}
                    </div>
                </div>`;
            }
            headersDetails.innerHTML = headersHtml;
        } else {
            headersDetails.innerHTML = `<div style="border-left:2px solid var(--neon-red); padding:10px; background:rgba(255,0,85,0.05); color:var(--neon-red); font-weight:600; font-family:'Orbitron', sans-serif; font-size:12px; border-radius:4px;">
                🚨 THIẾU KẾT NỐI HEADERS: Không thể kiểm tra tiêu đề bảo mật HTTP (máy chủ mục tiêu chặn kết nối).
            </div>`;
        }

        // --- SƠ ĐỒ CHUỖI CHUYỂN HƯỚNG (REDIRECTION CHAIN MAP) ---
        const redirectChainMap = document.getElementById("redirectChainMap");
        if (data.headers && data.headers.hops_detail && data.headers.hops_detail.length > 0) {
            const hops = data.headers.hops_detail;
            let mapHtml = `<div style="display:flex; flex-direction:column; gap:12px; font-family:'JetBrains Mono', monospace; font-size:12px;">`;
            
            hops.forEach((hop, idx) => {
                const isLast = idx === hops.length - 1;
                let statusColor = "var(--neon-green)";
                let statusIcon = "✓";
                
                if (hop.status_code >= 300 && hop.status_code < 400) {
                    statusColor = "var(--neon-yellow)";
                    statusIcon = "➜ Redirect";
                } else if (hop.status_code >= 400) {
                    statusColor = "var(--neon-red)";
                    statusIcon = "✗ Lỗi";
                }
                
                mapHtml += `
                <div style="display:flex; align-items:center; gap:15px; background:rgba(255,255,255,0.02); border:1px solid rgba(255,255,255,0.05); padding:10px; border-radius:6px; position:relative;">
                    <div style="width:30px; height:30px; border-radius:50%; display:flex; align-items:center; justify-content:center; font-weight:800; background:rgba(0, 243, 255, 0.1); border:2px solid var(--neon-cyan); color:var(--neon-cyan); font-family:'Orbitron', sans-serif;">
                        ${hop.hop_number}
                    </div>
                    <div style="flex-grow:1;">
                        <div style="color:#fff; font-weight:600; font-size:13px; word-break:break-all;">${hop.domain}</div>
                        <div style="font-size:11px; color:rgba(255,255,255,0.4); margin-top:2px; word-break:break-all;">${hop.url}</div>
                    </div>
                    <div style="text-align:right;">
                        <span style="font-family:'Orbitron', sans-serif; font-weight:700; color:${statusColor}; border:1px solid ${statusColor}; padding:2px 8px; border-radius:4px; font-size:10px;">
                            ${hop.status_code}
                        </span>
                        <div style="font-size:10px; color:${statusColor}; margin-top:4px; font-weight:600;">${statusIcon}</div>
                    </div>
                </div>`;
                
                if (!isLast) {
                    mapHtml += `
                    <div style="display:flex; justify-content:center; margin:-6px 0; color:var(--neon-cyan); opacity:0.6; font-size:16px;">
                        <i class="fa-solid fa-arrow-down-long" style="filter: drop-shadow(0 0 5px var(--neon-cyan));"></i>
                    </div>`;
                }
            });
            
            mapHtml += `</div>`;
            redirectChainMap.innerHTML = mapHtml;
        } else {
            redirectChainMap.innerHTML = `<div class="no-warnings" style="margin: 0; padding: 10px;">
                <i class="fa-solid fa-circle-check" style="color:var(--neon-green)"></i>
                <span style="color:rgba(255,255,255,0.6)">Không phát hiện bất kỳ chuỗi chuyển hướng nào (Direct connection).</span>
            </div>`;
        }
    }

    // Lưu kết quả vào LocalStorage History
    function saveToHistory(scanResult) {
        // Tránh trùng lặp URL
        scanHistory = scanHistory.filter(item => item.url !== scanResult.url);
        
        const historyItem = {
            url: scanResult.url,
            status: scanResult.status,
            risk_score: scanResult.risk_score,
            time: new Date().toLocaleTimeString("vi-VN", { hour: '2-digit', minute: '2-digit' }),
            data: scanResult // Lưu toàn bộ kết quả phân tích để tải lại lập tức
        };

        scanHistory.unshift(historyItem);
        
        // Giới hạn lịch sử tối đa 8 mục
        if (scanHistory.length > 8) {
            scanHistory.pop();
        }

        localStorage.setItem("tienshield_history", JSON.stringify(scanHistory));
        renderHistory();
    }

    // Hiển thị danh sách lịch sử bên Sidebar
    function renderHistory() {
        historyList.innerHTML = "";
        
        if (scanHistory.length === 0) {
            historyList.innerHTML = `<div class="empty-history">Chưa quét link nào</div>`;
            return;
        }

        scanHistory.forEach(item => {
            const row = document.createElement("div");
            row.className = "history-item";
            
            let color = "var(--neon-green)";
            let badgeBg = "rgba(57, 255, 20, 0.2)";
            let badgeText = "AN TOÀN";

            if (item.status === "DANGEROUS") {
                color = "var(--neon-red)";
                badgeBg = "rgba(255, 0, 85, 0.2)";
                badgeText = "NGUY HIỂM";
            } else if (item.status === "SUSPICIOUS") {
                color = "var(--neon-yellow)";
                badgeBg = "rgba(255, 223, 0, 0.2)";
                badgeText = "NGHI NGỜ";
            }

            row.style.setProperty("--item-color", color);
            row.style.setProperty("--badge-bg", badgeBg);
            
            row.innerHTML = `
                <div class="history-url" title="${item.url}">${item.url}</div>
                <div class="history-meta">
                    <span class="history-badge" style="background: ${badgeBg}; color: ${color}">${badgeText}</span>
                    <span class="history-time">${item.time}</span>
                </div>
            `;

            // Click vào lịch sử sẽ tải lại kết quả ngay tức khắc (Không cần gọi API lại)
            row.addEventListener("click", () => {
                inputCard.classList.add("hidden");
                loadingCard.classList.add("hidden");
                resultsArea.classList.remove("hidden");
                displayResults(item.data);
                closeSidebar(); // Tự động đóng khay trượt trên mobile khi chọn mục lịch sử
            });

            historyList.appendChild(row);
        });
    }
});
