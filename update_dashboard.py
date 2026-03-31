import psycopg2
import os
from datetime import datetime

def fetch_data():
    conn = psycopg2.connect(
        host=os.getenv('DB_HOST'),
        database=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASS'),
        port=os.getenv('DB_PORT')
    )
    cur = conn.cursor()

    # 1. D-Day 가져오기 (가장 가까운 2개)
    cur.execute("SELECT title, target_date FROM d_days WHERE is_active = TRUE ORDER BY target_date ASC LIMIT 2")
    d_days = cur.fetchall()

    # 2. 오늘 루틴 상태 가져오기
    cur.execute("""
        SELECT m.task_name, COALESCE(l.is_completed, FALSE)
        FROM routine_master m
        LEFT JOIN routine_logs l ON m.id = l.routine_id AND l.completed_date = CURRENT_DATE
        ORDER BY m.display_order
    """)
    routines = cur.fetchall()

    # 3. 이번 달 달성 기록 (캘린더 점 표시용)
    cur.execute("""
        SELECT DISTINCT completed_date FROM routine_logs 
        WHERE is_completed = TRUE 
        AND date_trunc('month', completed_date) = date_trunc('month', CURRENT_DATE)
    """)
    completed_dates = [d[0].strftime('%Y-%m-%d') for d in cur.fetchall()]

    cur.close()
    conn.close()
    return d_days, routines, completed_dates

def update_html(d_days, routines, completed_dates):
    with open('index.html', 'r', encoding='utf-8') as f:
        html = f.read()

    # 데이터 주입 (간단한 문자열 치환 방식)
    # D-Day 예시 (첫 번째 위젯)
    if len(d_days) > 0:
        html = html.replace('{{D_DAY_TITLE_1}}', d_days[0][0])
        html = html.replace('{{D_DAY_DATE_1}}', d_days[0][1].strftime('%m.%d'))
    
    # 루틴 리스트 생성 (HTML 조각 생성)
    routine_html = ""
    for name, is_done in routines:
        done_class = "done" if is_done else ""
        routine_html += f'<div class="todo-item {done_class}">{name}</div>'
    html = html.replace('{{ROUTINE_LIST}}', routine_html)

    # 캘린더 기록 데이터 주입 (JS 변수로 전달)
    html = html.replace('{{COMPLETED_DATES}}', str(completed_dates))

    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(html)

if __name__ == "__main__":
    d_days, routines, completed_dates = fetch_data()
    update_html(d_days, routines, completed_dates)
