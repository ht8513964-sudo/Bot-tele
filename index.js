const login = require("fca-unofficial");
const fs = require("fs");
const express = require("express");
const app = express();

// --- PHẦN 1: GIỮ BOT ONLINE TRÊN RENDER ---
app.get("/", (req, res) => res.send("Bot Free Fire đang hoạt động..."));
const port = process.env.PORT || 3000;
app.listen(port, () => console.log(`[SERVER] Đang chạy tại port: ${port}`));

// --- PHẦN 2: HÀM KHỞI CHẠY BOT ---
function startBot() {
    // Kiểm tra và đọc file appstate.json
    let appState;
    try {
        appState = JSON.parse(fs.readFileSync('appstate.json', 'utf8'));
    } catch (err) {
        return console.error("[LỖI] Không thể đọc file appstate.json. Hãy kiểm tra lại file trên GitHub!");
    }

    login({appState}, (err, api) => {
        if (err) {
            console.error("[LỖI ĐĂNG NHẬP] Có thể mã AppState đã hết hạn hoặc bị Facebook chặn.");
            console.error("Chi tiết lỗi:", err);
            return;
        }

        // Cấu hình bot
        api.setOptions({
            listenEvents: true, 
            selfListen: false, 
            forceLogin: true, 
            online: true
        });

        // TỰ ĐỘNG CẬP NHẬT APPSTATE MỚI ĐỂ TRÁNH BỊ VĂNG
        const newAppState = api.getAppState();
        fs.writeFileSync('appstate.json', JSON.stringify(newAppState, null, 2));
        console.log("[HỆ THỐNG] Đăng nhập thành công và đã cập nhật AppState mới!");

        // --- PHẦN 3: XỬ LÝ TIN NHẮN ---
        api.listenMqtt((err, event) => {
            if (err) return console.error("[LỖI MQTT]:", err);

            if (event.type === "message" && event.body) {
                const body = event.body.trim();
                const args = body.split(/\s+/);
                const command = args.shift().toLowerCase();

                // Lệnh kiểm tra bot
                if (command === "!check") {
                    return api.sendMessage("✅ Bot đang online và hoạt động tốt!", event.threadID);
                }

                // Lệnh đăng ký (Ví dụ: !reg TeamA 123456)
                if (command === "!reg") {
                    if (args.length < 2) return api.sendMessage("⚠️ Sai cú pháp! Ví dụ: !reg [Tên Đội] [ID]", event.threadID);
                    return api.sendMessage(`📝 Đã ghi nhận đội: ${args[0]} - ID: ${args[1]}`, event.threadID);
                }
                
                // Bạn có thể thêm các lệnh tính điểm Free Fire khác ở đây
            }
        });
    });
}

startBot();
