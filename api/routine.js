const { Client } = require('pg');

// Vercel이 100% 이해하는 안정적인 문법 (module.exports)
module.exports = async function handler(req, res) {
    // 1. 무조건 맨 처음에 CORS 헤더부터 박아넣기 (가짜 에러 방지)
    res.setHeader('Access-Control-Allow-Credentials', true);
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'OPTIONS, POST');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

    // 2. 브라우저가 "보내도 돼?" 하고 찔러보기(OPTIONS) 요청을 하면 바로 "ㅇㅇ 됨" 하고 끊어버림
    if (req.method === 'OPTIONS') {
        return res.status(200).end();
    }

    // POST 요청이 아니면 차단
    if (req.method !== 'POST') {
        return res.status(405).json({ message: 'POST 요청만 받습니다.' });
    }

    const { routine_id, is_completed, date } = req.body;

    // DB 연결 설정
    const client = new Client({
        host: process.env.DB_HOST,
        database: process.env.DB_NAME,
        user: process.env.DB_USER,
        password: process.env.DB_PASS,
        port: process.env.DB_PORT,
        ssl: false
    });

    try {
        await client.connect();
        
        if (is_completed) {
            // 체크 완료 (INSERT 또는 UPDATE)
            await client.query(`
                INSERT INTO routine_logs (routine_id, completed_date, is_completed)
                VALUES ($1, $2, TRUE)
                ON CONFLICT (routine_id, completed_date) DO UPDATE SET is_completed = TRUE
            `, [routine_id, date]);
        } else {
            // 체크 해제
            await client.query(`
                UPDATE routine_logs SET is_completed = FALSE
                WHERE routine_id = $1 AND completed_date = $2
            `, [routine_id, date]);
        }
        
        // 성공 응답!
        res.status(200).json({ success: true, message: "DB 저장 완벽해 형!" });
        
    } catch (error) {
        // DB 에러가 나도 서버가 뻗지 않고 에러 내용을 브라우저로 보내줌
        console.error("DB 접속 에러:", error);
        res.status(500).json({ error: 'Database error', details: error.message });
    } finally {
        await client.end();
    }
};
