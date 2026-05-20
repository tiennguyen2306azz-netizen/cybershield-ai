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
            { text: "> [SYS] Khởi động Tiến Shield AI Engine v2.0...", delay: 200, type: "info" },
            { text: `> [SYS] Nạp mục tiêu: ${url}`, delay: 400, type: "info" },
            { text: "> ─────────────────────────────────────────────────", delay: 600, type: "info" },
            { text: "> [MODULE 1/5] HEURISTIC SCANNER", delay: 800, type: "success" },
            { text: ">   ├─ Quét cấu trúc URL, giao thức, TLD...", delay: 1000, type: "info" },
            { text: ">   ├─ Phát hiện Typo-squatting (Levenshtein Distance)...", delay: 1300, type: "info" },
            { text: ">   ├─ Quét Homograph Attack (Unicode giả dạng)...", delay: 1500, type: "info" },
            { text: ">   └─ Đối chiếu URL Shortener & Suspicious TLD...", delay: 1700, type: "info" },
            { text: "> [MODULE 2/5] WHOIS DOMAIN LOOKUP", delay: 2000, type: "success" },
            { text: ">   ├─ Truy xuất thông tin đăng ký tên miền...", delay: 2300, type: "info" },
            { text: ">   └─ Phân tích tuổi tên miền & nhà đăng ký...", delay: 2600, type: "info" },
            { text: "> [MODULE 3/5] SSL/TLS CERTIFICATE CHECK", delay: 2900, type: "success" },
            { text: ">   ├─ Kết nối TLS tới máy chủ mục tiêu...", delay: 3200, type: "info" },
            { text: ">   └─ Xác minh chứng chỉ SSL & tổ chức cấp...", delay: 3500, type: "info" },
            { text: "> [MODULE 4/5] HTTP SECURITY HEADERS AUDIT", delay: 3800, type: "success" },
            { text: ">   ├─ Gửi yêu cầu HTTP & theo dõi Redirect chain...", delay: 4100, type: "info" },
            { text: ">   └─ Kiểm tra CSP, HSTS, X-Frame-Options...", delay: 4400, type: "info" },
            { text: "> [MODULE 5/5] NVIDIA GPT-120B AI THREAT INTEL", delay: 4700, type: "success" },
            { text: ">   ├─ Đóng gói ngữ cảnh từ 4 module gửi tới AI...", delay: 5000, type: "info" },
            { text: ">   └─ Đang chờ AI phân tích hành vi lừa đảo...", delay: 5300, type: "info" },
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
            });

            historyList.appendChild(row);
        });
    }
});
