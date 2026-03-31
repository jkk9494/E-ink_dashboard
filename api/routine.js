const { Client } = require('pg');

export default async function handler(req, res) {
    // CORS 설정 (깃허브 페이지에서 오는 요청을 허용)
    res.setHeader('Access-Control-Allow-Credentials', true);
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'OPTIONS,POST');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

    if (req.method === 'OPTIONS') return res.status(200).end();
    if (req.method !== 'POST') return res.status(405).json({ message: 'Method Not Allowed' });

    const { routine_id, is_completed, date } = req.body;

    const client = new Client({
        host: process.env.DB_HOST,
        database: process.env.DB_NAME,
        user: process.env.DB_USER,
        password: process.env.DB_PASS,
        port: process.env.DB_PORT,
        ssl: { rejectUnauthorized: false } // 대부분의 클라우드 DB는 필수
    });

    try {
        await client.connect();
        if (is_completed) {
            // 체크 완료 -> DB에 INSERT (이미 있으면 업데이트)
            await client.query(`
                INSERT INTO routine_logs (routine_id, completed_date, is_completed)
                VALUES ($1, $2, TRUE)
                ON CONFLICT (routine_id, completed_date) DO UPDATE SET is_completed = TRUE
            `, [routine_id, date]);
        } else {
            // 체크 해제 -> DB에서 FALSE로 업데이트
            await client.query(`
                UPDATE routine_logs SET is_completed = FALSE
                WHERE routine_id = $1 AND completed_date = $2
            `, [routine_id, date]);
        }
        res.status(200).json({ success: true });
    } catch (error) {
        console.error(error);
        res.status(500).json({ error: 'Database error' });
    } finally {
        await client.end();
    }
}
