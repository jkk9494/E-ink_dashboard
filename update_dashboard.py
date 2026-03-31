import psycopg2
import os
from datetime import datetime

def fetch_db_data():
    conn = psycopg2.connect(
        host=os.getenv('DB_HOST'),
        database=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASS'),
        port=os.getenv('DB_PORT')
    )
    cur = conn.cursor()

    # D-Day (시험)
    cur.execute("SELECT title, target_date FROM d_days WHERE category='EXAM' ORDER BY target_date ASC LIMIT 1")
    exam = cur.fetchone() or ("일정 없음", datetime.now())
    exam_val = f"D-{(exam[1] - datetime.now().date()).days}"

    # D-Day (생일)
    cur.execute("SELECT title, target_date FROM d_days WHERE category='BIRTHDAY' ORDER BY target_date ASC LIMIT 1")
    bday = cur.fetchone() or ("생일 없음", datetime.now())
    bday_val = bday[1].strftime('%m.%d')

    # 오늘 루틴 리스트
    cur.execute("""
        SELECT m.task_name, COALESCE(l.is_completed, FALSE)
        FROM routine_master m
        LEFT JOIN routine_logs l ON m.id = l.routine_id AND l.completed_date = CURRENT_DATE
        ORDER BY m.display_order
    """)
    routines = cur.fetchall()
    routine_html = "".join([f'<div class="todo-item {"done" if r[1] else ""}">{r[0]}</div>' for r in routines])

    # 캘린더 점 찍을 날짜 리스트
    cur.execute("SELECT DISTINCT completed_date FROM routine_logs WHERE is_completed = TRUE")
    completed_dates = [d[0].strftime('%Y-%m-%d') for d in cur.fetchall()]

    cur.close()
    conn.close()
    return exam, exam_val, bday, bday_val, routine_html, completed_dates

def main():
    exam, exam_val, bday, bday_val, routine_html, completed_dates = fetch_db_data()
    
    with open('index.html', 'r', encoding='utf-8') as f:
        content = f.read()

    # 자리표시자 치환
    content = content.replace('{{D_DAY_TITLE}}', exam[0])
    content = content.replace('{{D_DAY_VAL}}', exam_val)
    content = content.replace('{{BDAY_TITLE}}', bday[0])
    content = content.replace('{{BDAY_VAL}}', bday_val)
    content = content.replace('{{ROUTINE_LIST}}', routine_html)
    content = content.replace('{{COMPLETED_DATES}}', str(completed_dates))

    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(content)

if __name__ == "__main__":
    main()
