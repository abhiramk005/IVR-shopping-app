from flask import Flask, render_template, request, redirect
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Gather
from db import get_db
from config import *

app = Flask(__name__)
client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# ---------------- HOME ----------------
@app.route("/")
def home():
    return redirect("/add-user")


# ---------------- ADD USER ----------------
@app.route("/add-user", methods=["GET", "POST"])
def add_user():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        phone = request.form["phone"]

        db = get_db()
        cur = db.cursor()
        cur.execute(
            "INSERT INTO users (name,email,phone) VALUES (%s,%s,%s)",
            (name, email, phone)
        )
        db.commit()
        db.close()

    return render_template("add_user.html")


# ---------------- BROADCAST CALL ----------------
@app.route("/broadcast", methods=["GET", "POST"])
def broadcast():
    if request.method == "POST":
        message = request.form["message"]

        db = get_db()
        cur = db.cursor()
        cur.execute("SELECT phone FROM users")
        phones = cur.fetchall()
        db.close()

        for p in phones:
            client.calls.create(
                to=p[0],
                from_=TWILIO_PHONE,
                url=f"https://roselyn-overturnable-fernando.ngrok-free.dev/voice?msg={message}"
            )

    return render_template("broadcast.html")


# ---------------- IVR VOICE ----------------
@app.route("/voice", methods=["POST"])
def voice():
    msg = request.args.get("msg", "Hello from admin.")
    vr = VoiceResponse()

    gather = Gather(num_digits=1, action="/menu", method="POST")
    gather.say(
        f"{msg}. "
        "Press 1 to place order. "
        "Press 2 to remove items. "
        "Press 3 to exit."
    )

    vr.append(gather)
    vr.redirect("/voice")
    return str(vr)


# ---------------- MENU ----------------
@app.route("/menu", methods=["POST"])
def menu():
    digit = request.values.get("Digits")
    vr = VoiceResponse()

    if digit == "1":
        gather = Gather(num_digits=2, action="/order", method="POST")
        gather.say("Enter order quantity")
        vr.append(gather)

    elif digit == "2":
        vr.say("Items removed successfully")
        vr.hangup()

    else:
        vr.say("Thank you. Goodbye")
        vr.hangup()

    return str(vr)


# ---------------- SAVE ORDER ----------------
@app.route("/order", methods=["POST"])
def order():
    qty = request.values.get("Digits")
    phone = request.values.get("From")

    db = get_db()
    cur = db.cursor()
    cur.execute(
        "INSERT INTO orders (phone, quantity) VALUES (%s,%s)",
        (phone, qty)
    )
    db.commit()
    db.close()

    vr = VoiceResponse()
    vr.say(f"Order of {qty} items confirmed")
    vr.hangup()
    return str(vr)


# ---------------- VIEW ORDERS ----------------
@app.route("/orders")
def orders():
    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("SELECT * FROM orders ORDER BY order_time DESC")
    data = cur.fetchall()
    db.close()

    return render_template("orders.html", orders=data)


if __name__ == "__main__":
    app.run(debug=True)
