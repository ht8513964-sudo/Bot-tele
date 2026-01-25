const login = require("fca-unofficial");
const axios = require("axios");
const fs = require("fs-extra");
const express = require("express");

const app = express();
app.get("/", (req, res) => res.send("Bot Free Fire đang online!"));
app.listen(process.env.PORT || 3000);

const PLAYER_FILE = "./players.json";
const DATA_FILE = "./points.json";
const rankTable = { 1: 12, 2: 9, 3: 8, 4: 7, 5: 6, 6: 5, 7: 4, 8: 3, 9: 2, 10: 1 };

if (!fs.existsSync(PLAYER_FILE)) fs.writeJsonSync(PLAYER_FILE, {});
if (!fs.existsSync(DATA_FILE)) fs.writeJsonSync(DATA_FILE, {});

const appState = fs.readJsonSync("./appstate.json");

login({ appState }, (err, api) => {
    if (err) return console.error("Lỗi AppState! Hãy kiểm tra lại file appstate.json");

    api.listenMqtt(async (err, event) => {
        if (!event || !event.body) return;
        const args = event.body.trim().split(/\s+/);
        const cmd = args[0].toLowerCase();

        // Lệnh 1: Đăng ký ID người chơi (Làm 1 lần trước giải)
        if (cmd === "!reg") {
            const team = args[1], id = args[2];
            if (!team || !id) return api.sendMessage("⚠️ Cú pháp: !reg [TênTeam] [ID]", event.threadID);
            let players = fs.readJsonSync(PLAYER_FILE);
            players[id] = team;
            fs.writeJsonSync(PLAYER_FILE, players);
            api.sendMessage(`✅ Đã đăng ký: ${team} (ID: ${id})`, event.threadID);
        }

        // Lệnh 2: Quét trận đấu (Sau khi trận đấu kết thúc 2 phút)
        if (cmd === "!room") {
            const roomID = args[1];
            if (!roomID) return api.sendMessage("⚠️ Nhập ID phòng!", event.threadID);
            api.sendMessage(`⏳ Đang quét dữ liệu lịch sử đấu cho phòng ${roomID}...`, event.threadID);

            let players = fs.readJsonSync(PLAYER_FILE);
            let results = [];
            let now = Date.now();

            for (const [id, team] of Object.entries(players)) {
                try {
                    // API lấy lịch sử đấu của Garena
                    const res = await axios.get(`https://congdong.ff.garena.vn/api/match/history?id=${id}`);
                    const match = res.data.data[0];

                    // So khớp thời gian kết thúc trận trong vòng 20 phút qua
                    if (match && Math.abs(match.time_end - now) < 1200000) {
                        results.push({ team, rank: match.rank, kill: match.kill });
                    }
                } catch (e) { console.log(`Lỗi quét ID ${id}`); }
            }

            if (results.length === 0) return api.sendMessage("❌ Không tìm thấy trận đấu mới nào hợp lệ!", event.threadID);

            let bxh = `📊 KẾT QUẢ PHÒNG: ${roomID}\n━━━━━━━━━━━━━━\n`;
            let data = fs.readJsonSync(DATA_FILE);
            results.forEach(res => {
                let pts = (rankTable[res.rank] || 0) + res.kill;
                data[res.team] = (data[res.team] || 0) + pts;
                bxh += `🔹 ${res.team}: Hạng ${res.rank} | +${pts}đ\n`;
            });
            fs.writeJsonSync(DATA_FILE, data);
            api.sendMessage(bxh + "━━━━━━━━━━━━━━\n✅ Đã cập nhật BXH tổng!", event.threadID);
        }

        // Lệnh 3: Xem bảng điểm tổng
        if (cmd === "!bxh") {
            let data = fs.readJsonSync(DATA_FILE);
            let sorted = Object.entries(data).sort((a,b) => b[1] - a[1]);
            if (sorted.length == 0) return api.sendMessage("Chưa có dữ liệu!", event.threadID);
            let msg = "🏆 BXH TỔNG GIẢI ĐẤU 🏆\n";
            sorted.forEach(([t, p], i) => msg += `${i+1}. ${t}: ${p}đ\n`);
            api.sendMessage(msg, event.threadID);
        }
    });
});
