const login = require("fca-unofficial");
const axios = require("axios");
const fs = require("fs-extra");
const express = require("express");

const app = express();
app.get("/", (req, res) => res.send("Bot Free Fire đang online!"));
app.listen(process.env.PORT || 3000);

// Load cấu hình
const config = fs.readJsonSync("./config.json");
const PLAYER_FILE = "./players.json";
const DATA_FILE = "./points.json";
const rankTable = { 1: 12, 2: 9, 3: 8, 4: 7, 5: 6, 6: 5, 7: 4, 8: 3, 9: 2, 10: 1 };

if (!fs.existsSync(PLAYER_FILE)) fs.writeJsonSync(PLAYER_FILE, {});
if (!fs.existsSync(DATA_FILE)) fs.writeJsonSync(DATA_FILE, {});

const appState = fs.readJsonSync("./appstate.json");

login({ appState }, (err, api) => {
    if (err) return console.error("Lỗi AppState! Hãy kiểm tra lại.");

    api.listenMqtt(async (err, event) => {
        if (!event || !event.body || !event.body.startsWith(config.PREFIX)) return;
        
        const args = event.body.slice(config.PREFIX.length).trim().split(/\s+/);
        const cmd = args.shift().toLowerCase();

        // 1. Đăng ký ID cầu thủ
        if (cmd === "reg") {
            const team = args[0], id = args[1];
            if (!team || !id) return api.sendMessage(`⚠️ Cú pháp: ${config.PREFIX}reg [TênTeam] [ID]`, event.threadID);
            let players = fs.readJsonSync(PLAYER_FILE);
            players[id] = team;
            fs.writeJsonSync(PLAYER_FILE, players);
            api.sendMessage(`✅ Đã lưu: ${team} (ID: ${id})`, event.threadID);
        }

        // 2. Lệnh tính điểm tự động (Cơ chế vmnghia)
        if (cmd === "room") {
            const roomID = args[0];
            if (!roomID) return api.sendMessage("⚠️ Nhập ID phòng!", event.threadID);
            api.sendMessage(`⏳ Đang truy vấn lịch sử đấu cho phòng ${roomID}...`, event.threadID);

            let players = fs.readJsonSync(PLAYER_FILE);
            let results = [];
            let now = Date.now();

            for (const [id, team] of Object.entries(players)) {
                try {
                    const res = await axios.get(`https://congdong.ff.garena.vn/api/match/history?id=${id}`);
                    const match = res.data.data[0];

                    if (match && Math.abs(match.time_end - now) < config.TIME_LIMIT) {
                        results.push({ team, rank: match.rank, kill: match.kill });
                    }
                } catch (e) { console.log(`Lỗi ID ${id}`); }
            }

            if (results.length === 0) return api.sendMessage("❌ Không tìm thấy trận đấu mới hợp lệ!", event.threadID);

            let bxh = `📊 PHÒNG: ${roomID}\n`;
            let data = fs.readJsonSync(DATA_FILE);
            results.forEach(res => {
                let pts = (rankTable[res.rank] || 0) + res.kill;
                data[res.team] = (data[res.team] || 0) + pts;
                bxh += `🔹 ${res.team}: Top ${res.rank} (+${pts}đ)\n`;
            });
            fs.writeJsonSync(DATA_FILE, data);
            api.sendMessage(bxh + "✅ Đã cộng điểm vào BXH!", event.threadID);
        }

        // 3. Xem BXH tổng
        if (cmd === "bxh") {
            let data = fs.readJsonSync(DATA_FILE);
            let sorted = Object.entries(data).sort((a,b) => b[1] - a[1]);
            let msg = "🏆 BXH TỔNG GIẢI ĐẤU 🏆\n";
            sorted.forEach(([t, p], i) => msg += `${i+1}. ${t}: ${p}đ\n`);
            api.sendMessage(msg || "Chưa có điểm.", event.threadID);
        }
    });
});
