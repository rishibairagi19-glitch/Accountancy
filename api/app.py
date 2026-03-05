from flask import Flask, request, jsonify
from flask_cors import CORS
from supabase import create_client
import os

app = Flask(__name__)
CORS(app)

SUPABASE_URL = os.environ.get("https://eshvdtfkafsxgmenmlxh.supabase.co")
SUPABASE_KEY = os.environ.get("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImVzaHZkdGZrYWZzeGdtZW5tbHhoIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzIzMzg3MzcsImV4cCI6MjA4NzkxNDczN30.vR70DchpYEYwF_tid9Ocbj7KAm8Roan9Jo-Ble4YG5g")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ---------------- REGISTER ----------------
@app.route("/api/register", methods=["POST"])
def register():
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
    }), 200


# ---------------- LOGIN ----------------
@app.route("/api/login", methods=["POST"])
def login():
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


# ---------------- SYNC ----------------
@app.route("/api/sync", methods=["POST"])
def sync():
    data = request.json

    supabase.table("users") \
        .update({"ledger_data": data["ledger_data"]}) \
        .eq("email", data["email"]) \
        .execute()

    return jsonify({"message": "Synced"})


# ---------------- DELETE ----------------
@app.route("/api/delete", methods=["POST"])
def delete():
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


# ---------------- EDIT ----------------
@app.route("/api/edit", methods=["POST"])
def edit():
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


@app.route("/")
def home():
    return "API Running 🚀"