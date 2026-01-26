const login = require("fca-unofficial");
const fs = require("fs");
const express = require("express");
const app = express();

// Giữ bot online 24/7 trên Render
app.get("/", (req, res) => res.send("Bot đang chạy..."));
app.listen(process.env.PORT || 3000);

const pathAppState = "./appstate.json";

// Cơ chế kiểm tra file AppState giống Mirai
if (!fs.existsSync(pathAppState) || fs.readFileSync(pathAppState).length == 0) {
    console.error("LỖI: File appstate.json trống. Hãy dán mã JSON vào trước!");
    process.exit(0);
}

const appState = JSON.parse(fs.readFileSync(pathAppState, "utf8"));

const loginConfig = { appState };

login(loginConfig, (err, api) => {
    if (err) {
        console.error("Đăng nhập thất bại. Có thể do AppState hết hạn hoặc Facebook chặn IP Render.");
        return console.error(err);
    }

    // Tự động cập nhật AppState giống Mirai
    fs.writeFileSync(pathAppState, JSON.stringify(api.getAppState(), null, 2));
    console.log("ĐĂNG NHẬP THÀNH CÔNG! Đã cập nhật lại file appstate.json.");

    api.setOptions({
        listenEvents: true,
        selfListen: false,
        forceLogin: true,
        online: true,
        autoMarkDelivery: true // Đánh dấu đã chuyển tin nhắn
    });

    api.listenMqtt((err, event) => {
        if (err) return console.error("Lỗi nhận tin nhắn:", err);
        
        // Phần xử lý lệnh (Prefix giống Mirai thường là "!")
        if (event.type === "message" && event.body && event.body.startsWith("!")) {
            const body = event.body.slice(1).trim(); // Bỏ dấu !
            if (body === "check") {
                api.sendMessage("✅ Bot Mirai-style đã online!", event.threadID);
            }
        }
    });
});
