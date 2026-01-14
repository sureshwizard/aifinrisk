import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import random

scope = ["https://spreadsheets.google.com/feeds","https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("creds.json", scope)
client = gspread.authorize(creds)
wb = client.open("Student_Risk_Platform")

students = wb.worksheet("student_master").get_all_records()
risk_sheet = wb.worksheet("ai_risk_score")

# Clear old data but keep header
risk_sheet.resize(1)

rows = []

for s in students:
    att = random.randint(40, 100)
    acad = random.randint(40, 100)
    fin = random.randint(40, 100)
    beh = random.randint(40, 100)
    eng = random.randint(40, 100)
    well = random.randint(40, 100)

    overall = round((att + acad + fin + beh + eng + well) / 6)

    if overall >= 75:
        risk = "HIGH"
    elif overall >= 55:
        risk = "MEDIUM"
    else:
        risk = "LOW"

    rows.append([
        s["student_id"], att, acad, fin, beh, eng, well,
        overall, risk, datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ])

risk_sheet.append_rows(rows)

print("AI Risk Scores generated for", len(rows), "students")

