const express = require('express');
const cors = require('cors');
const jwt = require('jsonwebtoken');
const { DateTime } = require('luxon');
const randomstring = require('randomstring');
const csv = require('csv-parser');
const fs = require('fs');
const { LotteryTicket, AdminUser } = require('./models');

const app = express();
const PORT = process.env.PORT || 8000;
const SECRET_KEY = "your_secret_key"; // Replace with a secure key
const ACCESS_TOKEN_EXPIRE_MINUTES = 30;

app.use(cors());

app.use(express.json());

app.post("/api/savePhoneNumber/", async (req, res) => {
    const phoneNumber = req.body.phoneNumber;
    if (!phoneNumber) {
        return res.status(400).json({ message: 'Phone number is required' });
    }

    let exists = false;
    fs.createReadStream('data.csv')
        .pipe(csv())
        .on('data', (row) => {
            if (phoneNumber === row[0]) {
                exists = true;
            }
        })
        .on('end', async () => {
            if (exists) {
                return res.status(400).json({ message: 'Phone number already exists' });
            }

            try {
                fs.appendFileSync('data.csv', `${phoneNumber}\n`);
                return res.status(200).json({ message: 'Phone number saved successfully' });
            } catch (error) {
                console.error('Error saving phone number:', error);
                return res.status(500).json({ message: 'Failed to save phone number' });
            }
        });
});

app.post("/api/token", async (req, res) => {
    const { username, password } = req.body;
    const user = await AdminUser.findOne({ username });

    if (!user || !user.verifyPassword(password)) {
        return res.status(401).json({ message: 'Incorrect username or password' });
    }

    const accessToken = jwt.sign({ username: user.username }, SECRET_KEY, { expiresIn: ACCESS_TOKEN_EXPIRE_MINUTES * 60 });
    return res.status(200).json({ access_token: accessToken });
});

app.get("/api/tickets/", async (req, res) => {
    const tickets = await LotteryTicket.find();
    return res.status(200).json(tickets);
});

app.post("/api/generate_ticket/", async (req, res) => {
    const ticketCode = randomstring.generate({ length: 10, charset: 'alphanumeric' });
    const ticket = new LotteryTicket({ ticket_code: ticketCode });
    await ticket.save();
    return res.status(200).json({ ticket_code: ticketCode });
});

app.post("/api/submit_ticket/:ticket_code", async (req, res) => {
    const ticketCode = req.params.ticket_code;
    const ticket = await LotteryTicket.findOne({ ticket_code: ticketCode });

    if (!ticket) {
        return res.status(400).json({ message: 'Invalid ticket code' });
    }

    if (ticket.used) {
        return res.status(400).json({ message: 'Ticket already used' });
    }

    // Implement your logic here
});

app.get("/api/spin/:ticket_code", async (req, res) => {
    const ticketCode = req.params.ticket_code;
    const ticket = await LotteryTicket.findOne({ ticket_code: ticketCode });

    if (!ticket) {
        return res.status(400).json({ message: 'Invalid ticket code' });
    }

    if (ticket.used) {
        return res.status(400).json({ message: 'Ticket already used' });
    }

    const result = getRandomResult();
    ticket.result = result;
    ticket.used = true;
    await ticket.save();
    
    return res.status(200).json({ prize: result });
});

app.get("/api/ticket_prize/:ticket_code", async (req, res) => {
    const ticketCode = req.params.ticket_code;
    const ticket = await LotteryTicket.findOne({ ticket_code: ticketCode });

    if (!ticket) {
        return res.status(404).json({ message: 'Ticket not found' });
    }

    if (!ticket.result) {
        return res.status(404).json({ message: 'No prize assigned to this ticket yet' });
    }

    return res.status(200).json({ ticket_code: ticket.ticket_code, prize: ticket.result });
});

function getRandomResult() {
    const prizes = ["谢谢参与", "300", "600", "900", "1500", "3000", "8800", "再来一次"];
    const probabilities = [0.10, 0.36, 0.25, 0.10, 0.5, 0.03, 0.01, 0.10];
    const randomIndex = getRandomIndex(probabilities);
    return prizes[randomIndex];
}

function getRandomIndex(probabilities) {
    const rand = Math.random();
    let cumulativeProbability = 0;
    for (let i = 0; i < probabilities.length; i++) {
        cumulativeProbability += probabilities[i];
        if (rand < cumulativeProbability) {
            return i;
        }
    }
    return probabilities.length - 1; // Fallback to the last index
}

app.listen(PORT, () => {
    console.log(`Server is running on port ${PORT}`);
});
