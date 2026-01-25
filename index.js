const login = require("fca-unofficial");
const express = require("express");
const fs = require("fs-extra");
const app = express();

// 1. Web duy trì hoạt động trên Render
app.get('/', (req, res) => res.send('Bot FF & Welcome đang chạy!'));
app.listen(process.env.PORT || 3000);

// 2. Đọc file cấu hình
const config = fs.readJsonSync("./config.json");
const appState = fs.readJsonSync("./appstate.json");
const DATA_FILE = "./points.json";

if (!fs.existsSync(DATA_FILE)) fs.writeJsonSync(DATA_FILE, {});
let dataFF = fs.readJsonSync(DATA_FILE);

// 3. Khởi chạy Bot
login({ appState }, (err, api) => {
    if (err) return console.error("Lỗi đăng nhập: Kiểm tra file appstate.json");

    api.setOptions({ listenEvents: true, selfListen: false });
    console.log(`${config.BOT_NAME} đã sẵn sàng trong nhóm!`);

    api.listenMqtt(async (err, event) => {
        if (err) return;

        // --- TÍNH NĂNG 1: CHÀO THÀNH VIÊN MỚI ---
        if (event.logMessageType === "log:subscribe") {
            const { threadID } = event;
            // Lấy thông tin người được thêm vào
            const addedParticipants = event.logMessageData.addedParticipants;
            
            for (let participant of addedParticipants) {
                const name = participant.fullName;
                const msg = `🌟 Chào mừng ${name} đã gia nhập nhóm!\n🔥 Chúc bạn bắn Free Fire thật cháy và tuân thủ quy định nhóm nhé!`;
                api.sendMessage(msg, threadID);
            }
        }

        // --- TÍNH NĂNG 2: LỆNH CHAT (BXH & TÍNH ĐIỂM) ---
        if (event.body) {
            const args = event.body.trim().split(/\s+/);
            const cmd = args[0].toLowerCase();
            const senderID = event.senderID;

            // Xem BXH
            if (cmd === `${config.PREFIX}bxh`) {
                let bxh = "🏆 BXH GIẢI ĐẤU FREE FIRE 🏆\n" + "━".repeat(15) + "\n";
                const sorted = Object.entries(dataFF).sort((a, b) => b[1] - a[1]);
                if (sorted.length == 0) return api.sendMessage("Chưa có dữ liệu điểm.", event.threadID);
                sorted.forEach(([t, p], i) => bxh += `${i + 1}. ${t.toUpperCase()}: ${p}đ\n`);
                api.sendMessage(bxh, event.threadID);
            }

            // Lệnh Admin
            if (cmd === `${config.PREFIX}ff`) {
                if (senderID !== config.ADMIN_ID) return api.sendMessage("⚠️ Bạn không có quyền Admin!", event.threadID);

                const action = args[1];
                if (action === "add") {
                    const team = args[2], rank = parseInt(args[3]), kills = parseInt(args[4]);
                    if (!team || isNaN(rank)) return api.sendMessage("Cú pháp: !ff add [Team] [Hạng] [Kill]", event.threadID);
                    
                    const points = { 1: 12, 2: 9, 3: 8, 4: 7, 5: 6, 6: 5, 7: 4, 8: 3, 9: 2, 10: 1 }[rank] || 0;
                    const total = points + (isNaN(kills) ? 0 : kills);
                    dataFF[team] = (dataFF[team] || 0) + total;
                    fs.writeJsonSync(DATA_FILE, dataFF);
                    api.sendMessage(`✅ Đã cộng ${total}đ cho Team ${team}`, event.threadID);
                }
                
                if (action === "reset") {
                    dataFF = {};
                    fs.writeJsonSync(DATA_FILE, dataFF);
                    api.sendMessage("🧹 Đã xóa toàn bộ điểm giải đấu.", event.threadID);
                }
            }
        }
    });
});
