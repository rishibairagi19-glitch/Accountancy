from flask import Flask, request, jsonify
from flask_cors import CORS
from supabase import create_client
import os

app = Flask(__name__)
CORS(app)

# ---------------- SUPABASE CONFIG ----------------
SUPABASE_URL = os.environ.get("https://eshvdtfkafsxgmenmlxh.supabase.co")
SUPABASE_KEY = os.environ.get("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImVzaHZkdGZrYWZzeGdtZW5tbHhoIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MjMzODczNywiZXhwIjoyMDg3OTE0NzM3fQ.KHOmVF46wf4B0QJaSAU9yfNSYW3YNnccPB32A3CHlKo")
#SUPABASE_KEY = os.environ.get("sb_publishable_KNkUFe4TJZe4M6IRl8_QHQ_MLJUb7vO")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ---------------- DEFAULT USER ----------------
DEFAULT_EMAIL = "admin@rick.com"
DEFAULT_PASSWORD = "YWRtaW4xMjM="  # base64 of admin123

def create_default_user():
    try:
        res = supabase.table("users").select("*").eq("email", DEFAULT_EMAIL).execute()

        if not res.data:
            supabase.table("users").insert({
                "email": DEFAULT_EMAIL,
                "password": DEFAULT_PASSWORD,
                "ledger_data": []
            }).execute()
            print("Default user created")
            
    except Exception as e:
        print("Error creating default user:", e)      

create_default_user()

# ---------------- REGISTER ----------------
@app.route("/api/register", methods=["POST"])
def register():
    try:
        data = request.json
        email = data.get("email")
        password = data.get("password")

        if not email or not password:
            return jsonify({"message": "Missing fields"}), 400

        existing = supabase.table("users").select("*").eq("email", email).execute()

        if existing.data:
            return jsonify({"message": "User already exists"}), 400

        supabase.table("users").insert({
            "email": email,
            "password": password,
            "ledger_data": []
        }).execute()

        return jsonify({
            "email": email,
            "ledger_data": []
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ---------------- LOGIN ----------------
@app.route("/api/login", methods=["POST"])
def login():
    try:
        data = request.json
        email = data.get("email")
        password = data.get("password")

        res = supabase.table("users") \
            .select("*") \
            .eq("email", email) \
            .eq("password", password) \
            .execute()

        if res.data:
            return jsonify({
                "email": res.data[0]["email"],
                "ledger_data": res.data[0]["ledger_data"]
            })

        return jsonify({"error": "Invalid credentials"}), 401

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ---------------- SYNC LEDGER ----------------
@app.route("/api/sync", methods=["POST"])
def sync():
    try:
        data = request.json

        supabase.table("users") \
            .update({"ledger_data": data["ledger_data"]}) \
            .eq("email", data["email"]) \
            .execute()

        return jsonify({"message": "Synced"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ---------------- DELETE ----------------
@app.route("/api/delete", methods=["POST"])
def delete():
    try:
        data = request.json
        email = data.get("email")
        record_id = str(data.get("id"))

        user = supabase.table("users").select("ledger_data").eq("email", email).execute()

        if not user.data:
            return jsonify({"error": "User not found"}), 404

        ledger = user.data[0]["ledger_data"]

        new_data = [i for i in ledger if str(i.get("id")) != record_id]

        supabase.table("users") \
            .update({"ledger_data": new_data}) \
            .eq("email", email) \
            .execute()

        return jsonify({"new_data": new_data})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ---------------- EDIT ----------------
@app.route("/api/edit", methods=["POST"])
def edit():
    try:
        data = request.json
        email = data.get("email")
        record_id = str(data.get("id"))

        user = supabase.table("users").select("ledger_data").eq("email", email).execute()

        if not user.data:
            return jsonify({"error": "User not found"}), 404

        ledger = user.data[0]["ledger_data"]

        for item in ledger:
            if str(item.get("id")) == record_id:
                item["n"] = data.get("n")
                item["a"] = float(data.get("a"))
                item["d"] = data.get("d")
                item["t"] = data.get("t")

        supabase.table("users") \
            .update({"ledger_data": ledger}) \
            .eq("email", email) \
            .execute()

        return jsonify({"new_data": ledger})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ---------------- HOME ----------------
@app.route("/")
def home():
    return jsonify({"message": "Rick Accountancy API Running"})

# ---------------- RUN SERVER ----------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
