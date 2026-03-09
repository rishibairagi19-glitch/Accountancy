from flask import Flask, request, jsonify
from flask_cors import CORS
from supabase import create_client, Client
import os

app = Flask(__name__)
CORS(app)

# ---------------- SUPABASE CONFIG ----------------
# Dashboard se copy karke yahan apni sahi details dalein
URL = "https://eshvdtfkafsxgmenmlxh.supabase.co"
KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImVzaHZkdGZrYWZzeGdtZW5tbHhoIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzIzMzg3MzcsImV4cCI6MjA4NzkxNDczN30.vR70DchpYEYwF_tid9Ocbj7KAm8Roan9Jo-Ble4YG5g" 

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
                "ledger_data": []
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

         # Check existing
        existingu = supabase.table("users").select("*").eq("email", email).execute()
        existingp = supabase.table("users").select("*").eq("passwird", password).execute()
        
        if not existingu.data:
            return jsonify({"message": "Wrong User Name"}), 400
        if not existingp.data:
            return jsonify({"message": "Wrong Password"}), 401

        if res.data and len(res.data) > 0:
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

# ---------------- RUN SERVER ----------------
if __name__ == "__main__":
    # Render/Railway automatically sets PORT
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
