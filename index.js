const login = require("fca-unofficial");
const fs = require("fs");
const express = require("express");
const app = express();

// Tạo server để Render không bị tắt (Giữ bot online)
app.get("/", (req, res) => res.send("Bot Free Fire đang chạy..."));
app.listen(process.env.PORT || 3000);

// Cấu hình đăng nhập
const appState = JSON.parse(fs.readFileSync('appstate.json', 'utf8'));

login({appState}, (err, api) => {
    if(err) return console.error("Lỗi đăng nhập:", err);

    api.setOptions({listenEvents: true, selfListen: false});

    console.log("Bot đã đăng nhập thành công!");

    api.listenMqtt((err, event) => {
        if (err) return console.error("Lỗi nhận tin nhắn:", err);

        if (event.type === "message" && event.body) {
            const message = event.body.trim();
            
            // Lệnh đăng ký: !reg [Tên đội] [ID]
            if (message.startsWith("!reg")) {
                const args = message.split(" ");
                if (args.length < 3) {
                    return api.sendMessage("Sai cú pháp! Ví dụ: !reg TeamA 12345678", event.threadID);
                }
                const teamName = args[1];
                const playerID = args[2];
                api.sendMessage(`✅ Đã đăng ký thành công cho đội ${teamName} (ID: ${playerID})`, event.threadID);
            }

            // Lệnh tính điểm: !diem [Thứ hạng] [Số Kill]
            if (message.startsWith("!diem")) {
                const args = message.split(" ");
                const rank = parseInt(args[1]);
                const kills = parseInt(args[2]);
                
                if (isNaN(rank) || isNaN(kills)) {
                    return api.sendMessage("Nhập đúng: !diem [Hạng] [Kills]", event.threadID);
                }

                // Ví dụ cách tính: Top 1 = 12đ, mỗi kill = 1đ
                const rankPoints = [0, 12, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0, 0];
                const total = (rankPoints[rank] || 0) + kills;

                api.sendMessage(`📊 Kết quả: Hạng ${rank} (${rankPoints[rank] || 0}đ) + ${kills} kill (${kills}đ) = Tổng ${total} điểm.`, event.threadID);
            }
        }
    });
});
