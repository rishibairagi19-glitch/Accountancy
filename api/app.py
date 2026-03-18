from flask import Flask, request, jsonify
from flask_cors import CORS
from supabase import create_client, Client
import os
from dotenv import load_dotenv

app = Flask(__name__)
CORS(app)

# ---------------- SUPABASE CONFIG ----------------
# Dashboard se copy karke yahan apni sahi details dalein

# Load environment variables from a .env file for security
load_dotenv() 

# Get Supabase URL and Key from environment variables (recommended practice)
URL = os.getenv("SUPABASE_URL")
KEY = os.getenv("SUPABASE_KEY")

print(f"URL : {URL}")
      
# Client initialization
supabase: Client = create_client(URL, KEY)

# ---------------- DEFAULT USER ----------------
DEFAULT_EMAIL = "admin@rick.com"
DEFAULT_PASSWORD = "YWRtaW4xMjM="  # base64 of admin123

def create_default_user():
    try:
        # Step 1: Check if user exists
        res = supabase.table("users").select("*").eq("email", DEFAULT_EMAIL).execute()

        if not res.data:
            # Step 2: If not, Insert default user
            supabase.table("users").insert({
                "email": DEFAULT_EMAIL,
                "password": DEFAULT_PASSWORD,
                "verified": True,
                "ledger_data": [],
                "notes": [],
                "reminders": []
            }).execute()
            print("--- Default user created successfully ---")
        else:
            print("--- Default user already exists ---")

    except Exception as e:
        # Note: Startup function mein print hi use karein
        print(f"--- Supabase Connection/Auth Error: {str(e)} ---")

# App start hone par default user check karega
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

        # Check existing
        existing = supabase.table("users").select("*").eq("email", email).execute()

        if existing.data:
            return jsonify({"message": "User already exists-Rick"}), 400

        # Insert new user
        supabase.table("users").insert({
            "email": email,
            "password": password,
            "verified": False,
            "ledger_data": [],
            "notes": [],
            "reminders": []
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

        # 1. Check user by email
        user_res = supabase.table("users") \
            .select("*") \
            .eq("email", email) \
            .execute()

        if not user_res.data:
            return jsonify({"message": "Wrong User Name"}), 400

        user = user_res.data[0]

        # 2. Check password for that user only
        if user["password"] != password:
            return jsonify({"message": "Wrong Password"}), 401

        # 3. Success login
        return jsonify({
            "email": user["email"],
            "verified": user["verified"],
            "ledger_data": user["ledger_data"],
            "notes": user.get("notes", []),
            "reminders": user.get("reminders", [])
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500
        

@app.route("/api/check_verified", methods=["POST"])
def check_verified():
    try:
        data = request.json
        email = data.get("email")

        res = supabase.table("users") \
            .select("verified") \
            .eq("email", email) \
            .execute()

        return jsonify({
            "verified": res.data[0]["verified"]
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ---------------- SYNC LEDGER ----------------
@app.route("/api/sync", methods=["POST"])
def sync():
    try:
        data = request.json
        email = data.get("email")
        ledger = data.get("ledger_data")

        supabase.table("users") \
            .update({"ledger_data": ledger}) \
            .eq("email", email) \
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
                item["n"] = data.get("n") # Name
                item["a"] = float(data.get("a")) # Amount
                item["d"] = data.get("d") # Description/Date
                item["t"] = data.get("t") # Type

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
    return jsonify({
        "status": "Online",
        "message": "Rick Accountancy API is running on Supabase"
    })

# ---------------- UPDATE NOTES ----------------
@app.route("/api/updateNotes", methods=["POST"])
def update_notes():
    try:
        data = request.json
        email = data.get("email")
        notes = data.get("notes")

        supabase.table("users") \
            .update({"notes": notes}) \
            .eq("email", email) \
            .execute()

        return jsonify({"status": "ok"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---------------- UPDATE REMINDERS ----------------
@app.route("/api/updateReminders", methods=["POST"])
def update_reminders():
    try:
        data = request.json
        email = data.get("email")
        reminders = data.get("reminders")

        supabase.table("users") \
            .update({"reminders": reminders}) \
            .eq("email", email) \
            .execute()

        return jsonify({"status": "ok"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---------------- GET USER ----------------
@app.route("/api/getUser", methods=["GET"])
def get_user():
    try:
        email = request.args.get("email")

        res = supabase.table("users") \
            .select("*") \
            .eq("email", email) \
            .execute()

        if not res.data:
            return jsonify({"error": "User not found"}), 404

        return jsonify(res.data[0])

    except Exception as e:
        return jsonify({"error": str(e)}), 500

