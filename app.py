from flask import Flask, render_template, request, redirect, jsonify
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import os
from openai import OpenAI

app = Flask(__name__, static_folder="static")

# -------------------------
# GOOGLE SHEETS
# -------------------------
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

creds = ServiceAccountCredentials.from_json_keyfile_name("creds.json", scope)
client = gspread.authorize(creds)

# ✅ REAL FINANCE SHEET
wb = client.open("finance_risk_ai")

# -------------------------
# OPENAI
# -------------------------
OPENAI_KEY = os.getenv("OPENAI_KEY")
client_ai = OpenAI(api_key=OPENAI_KEY)

# -------------------------
# TABLES (REAL)
# -------------------------
TABLES = [
    "borrowers",
    "loans",
    "credit_risk",
    "fraud_risk",
    "esg_risk",
    "cashflow_risk",
    "liquidity_risk",
    "market_risk",
    "interest_rate_risk",
    "collateral_risk",
    "income_risk",
    "leverage_risk",
    "sector_risk",
    "geographic_risk",
    "climate_risk",
    "compliance_risk",
    "operational_risk",
    "reputation_risk",
    "recovery_risk",
    "restructuring_risk",
    "concentration_risk",
    "stress_risk",
    "early_warning_risk",
    "master_loan_risk"
]

# -------------------------
# HOME
# -------------------------
@app.route("/")
def home():
    return redirect("/dashboard")

# -------------------------
# DASHBOARD
# -------------------------
@app.route("/dashboard")
def dashboard():
    borrowers = wb.worksheet("borrowers").get_all_records()
    loans = wb.worksheet("loans").get_all_records()
    risk = wb.worksheet("master_loan_risk").get_all_records()

    merged = []

    for r in risk:
        for l in loans:
            if str(r.get("loan_id")) == str(l.get("loan_id")):
                for b in borrowers:
                    if str(l.get("borrower_id")) == str(b.get("borrower_id")):
                        merged.append({
                            "loan_id": r.get("loan_id"),
                            "name": b.get("borrower_name"),
                            "risk": r.get("risk_band"),
                            "score": float(r.get("final_risk_score", 0))
                        })

    top = sorted(merged, key=lambda x: x["score"], reverse=True)[:10]

    high = sum(1 for x in merged if x["risk"] == "HIGH")
    medium = sum(1 for x in merged if x["risk"] == "MEDIUM")
    low = sum(1 for x in merged if x["risk"] == "LOW")

    return render_template(
        "dashboard.html",
        top=top,
        high=high,
        medium=medium,
        low=low,
        tables=TABLES
    )

# -------------------------
# TABLE VIEW
# -------------------------
@app.route("/table/<name>")
def table(name):
    sheet = wb.worksheet(name)
    data = sheet.get_all_values()
    return render_template("list.html", table=name, headers=data[0], rows=data[1:], tables=TABLES)

# -------------------------
# ADD RECORD
# -------------------------
@app.route("/add/<name>", methods=["GET", "POST"])
def add(name):
    sheet = wb.worksheet(name)
    headers = sheet.row_values(1)

    if request.method == "POST":
        row = []
        for h in headers:
            if "date" in h.lower() or "updated" in h.lower():
                row.append(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            else:
                row.append(request.form.get(h, ""))
        sheet.append_row(row)
        return redirect(f"/table/{name}")

    return render_template("form.html", table=name, headers=headers, tables=TABLES)

# -------------------------
# 🔥 AI FINANCE BRAIN
# -------------------------
@app.route("/ask", methods=["GET", "POST"])
def ask():
    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        q = data.get("question", "").strip()
    else:
        q = request.args.get("q", "").strip()

    if not q:
        return jsonify({"answer": "Please ask a finance risk question."})

    rows = wb.worksheet("master_loan_risk").get_all_records()

    dataset = ""
    for r in rows:
        dataset += f"{r}\n"

    system = """
You are AI FIN RISK.
You analyze loan default, fraud, ESG, market, liquidity and compliance risk.
You must answer ONLY from the dataset.
"""

    prompt = f"""
{system}

DATA:
{dataset}

Question: {q}
"""

    try:
        res = client_ai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )
        answer = res.choices[0].message.content
    except Exception as e:
        answer = "AI error: " + str(e)

    return jsonify({"answer": answer})

# -------------------------
# START
# -------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=4091)

