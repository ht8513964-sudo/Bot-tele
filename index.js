const login = require("fca-unofficial");
const express = require("express");
const fs = require("fs-extra");
const app = express();

// 1. Web duy trì hoạt động
app.get('/', (req, res) => res.send('Bot đang chạy!'));
app.listen(process.env.PORT || 3000);

// 2. Đọc file cấu hình và AppState
const config = fs.readJsonSync("./config.json");
const appState = fs.readJsonSync("./appstate.json");
const DATA_FILE = "./points.json";

if (!fs.existsSync(DATA_FILE)) fs.writeJsonSync(DATA_FILE, {});
let dataFF = fs.readJsonSync(DATA_FILE);

// 3. Khởi chạy Bot
login({ appState }, (err, api) => {
    if (err) return console.error("Lỗi đăng nhập: Kiểm tra file appstate.json");

    api.setOptions({ listenEvents: true, selfListen: false });
    console.log(`${config.BOT_NAME} đã sẵn sàng!`);

    api.listenMqtt((err, event) => {
        if (err || !event.body) return;

        const args = event.body.trim().split(/\s+/);
        const cmd = args[0].toLowerCase();
        const senderID = event.senderID;

        // Lệnh xem BXH (Công khai)
        if (cmd === `${config.PREFIX}bxh`) {
            let bxh = "🏆 BXH FREE FIRE 🏆\n\n";
            const sorted = Object.entries(dataFF).sort((a, b) => b[1] - a[1]);
            if (sorted.length == 0) return api.sendMessage("Chưa có dữ liệu.", event.threadID);
            sorted.forEach(([t, p], i) => bxh += `${i + 1}. ${t}: ${p}đ\n`);
            api.sendMessage(bxh, event.threadID);
        }

        // Lệnh Quản trị (Chỉ ADMIN_ID trong config.json dùng được)
        if (cmd === `${config.PREFIX}ff`) {
            if (senderID !== config.ADMIN_ID) return api.sendMessage("⚠️ Bạn không có quyền Admin!", event.threadID);

            const action = args[1];
            if (action === "add") {
                const team = args[2], rank = parseInt(args[3]), kills = parseInt(args[4]);
                if (!team || isNaN(rank)) return api.sendMessage("Cú pháp: !ff add [Team] [Hạng] [Kill]", event.threadID);
                
                const points = { 1: 12, 2: 9, 3: 8, 4: 7, 5: 6, 6: 5, 7: 4, 8: 3, 9: 2, 10: 1 }[rank] || 0;
                const total = points + kills;
                dataFF[team] = (dataFF[team] || 0) + total;
                fs.writeJsonSync(DATA_FILE, dataFF);
                api.sendMessage(`✅ Admin đã cộng ${total}đ cho ${team}`, event.threadID);
            }
            if (action === "reset") {
                dataFF = {};
                fs.writeJsonSync(DATA_FILE, dataFF);
                api.sendMessage("🧹 Đã xóa toàn bộ điểm.", event.threadID);
            }
        }
    });
});
