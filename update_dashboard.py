import psycopg2
import os
import json
from datetime import datetime

def fetch_db_data():
    # DB 연결
    conn = psycopg2.connect(
        host=os.getenv('DB_HOST'),
        database=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASS'),
        port=os.getenv('DB_PORT')
    )
    cur = conn.cursor()

    # 1. D-Day (시험) 가져오기
    cur.execute("SELECT title, target_date FROM d_days WHERE category='EXAM' ORDER BY target_date ASC LIMIT 1")
    exam = cur.fetchone() or ("일정 없음", datetime.now().date())
    exam_val = f"D-{(exam[1] - datetime.now().date()).days}"

    # 2. D-Day (생일) 가져오기
    cur.execute("SELECT title, target_date FROM d_days WHERE category='BIRTHDAY' ORDER BY target_date ASC LIMIT 1")
    bday = cur.fetchone() or ("생일 없음", datetime.now().date())
    bday_val = bday[1].strftime('%m.%d')

    # 3. 오늘 루틴 리스트 가져오기 (m.id 추가됨)
    cur.execute("""
        SELECT m.id, m.task_name, COALESCE(l.is_completed, FALSE)
        FROM routine_master m
        LEFT JOIN routine_logs l ON m.id = l.routine_id AND l.completed_date = CURRENT_DATE
        ORDER BY m.display_order
    """)
    routines = cur.fetchall()
    
    # HTML 조각 생성 (r[0]=id, r[1]=name, r[2]=is_completed 로 인덱스 변경됨)
    routine_html = ""
    for r in routines:
        done_class = "done" if r[2] else ""
        # data-id 속성에 실제 DB의 id값을 넣음
        routine_html += f'<div class="todo-item {done_class}" data-id="{r[0]}"><svg class="icon" viewBox="0 0 24 24"><path d="M12 20h9"></path><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"></path></svg>{r[1]}</div>'

    # 4. 캘린더 점 찍을 날짜 리스트 가져오기
    cur.execute("SELECT DISTINCT completed_date FROM routine_logs WHERE is_completed = TRUE")
    completed_dates = [d[0].strftime('%Y-%m-%d') for d in cur.fetchall()]

    cur.close()
    conn.close()
    return exam, exam_val, bday, bday_val, routine_html, completed_dates

def main():
    # 데이터 호출
    exam, exam_val, bday, bday_val, routine_html, completed_dates = fetch_db_data()
    
    # index.html 읽기
    with open('index.html', 'r', encoding='utf-8') as f:
        content = f.read()

    # 데이터 주입 (JSON 형식으로 안전하게)
    completed_dates_json = json.dumps(completed_dates)

    content = content.replace('{{D_DAY_TITLE}}', str(exam[0]))
    content = content.replace('{{D_DAY_VAL}}', str(exam_val))
    content = content.replace('{{BDAY_TITLE}}', str(bday[0]))
    content = content.replace('{{BDAY_VAL}}', str(bday_val))
    content = content.replace('{{ROUTINE_LIST}}', routine_html)
    content = content.replace('{{COMPLETED_DATES}}', completed_dates_json)

    # 수정된 내용 저장
    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(content)

if __name__ == "__main__":
    main()
