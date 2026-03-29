from flask import Flask, render_template, request, redirect, session
from pymongo import MongoClient
from bson.objectid import ObjectId

app = Flask(__name__)
app.secret_key = "secret123"

# -------------------- DATABASE --------------------
client = MongoClient("mongodb://localhost:27017/")
db = client["eventDB"]

users = db["users"]
events = db["events"]
bookings = db["bookings"]

# -------------------- HOME --------------------
@app.route("/")
def home():
    return redirect("/login")


# -------------------- REGISTER --------------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        if not email or not password:
            return "Please fill all fields"

        users.insert_one({
            "email": email,
            "password": password,
            "role": "user"
        })

        return redirect("/login")

    return render_template("register.html")


# -------------------- LOGIN (FIXED) --------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":

        email = request.form.get("email")
        password = request.form.get("password")

        if not email or not password:
            return "Enter email and password"

        user = users.find_one({
            "email": email,
            "password": password
        })

        if user:
            session["user"] = user["email"]
            session["role"] = user.get("role", "user")
            return redirect("/dashboard")
        else:
            return "Invalid Email or Password"

    return render_template("login.html")


# -------------------- LOGOUT --------------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


# -------------------- DASHBOARD --------------------
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/login")

    return render_template("dashboard.html", user=session["user"], role=session["role"])


# -------------------- CREATE EVENT --------------------
@app.route("/create_event", methods=["GET", "POST"])
def create_event():
    if "user" not in session or session["role"] != "admin":
        return redirect("/login")

    if request.method == "POST":
        title = request.form.get("title")
        date = request.form.get("date")
        location = request.form.get("location")
        price = request.form.get("price")

        if not title or not date or not location or not price:
            return "Fill all fields"

        event = {
            "title": title,
            "date": date,
            "location": location,
            "price": float(price)
        }

        events.insert_one(event)

        return redirect("/events")

    return render_template("create_event.html")


# -------------------- VIEW EVENTS --------------------
@app.route("/events")
def view_events():
    if "user" not in session:
        return redirect("/login")

    all_events = list(events.find())

    return render_template("events.html", events=all_events, role=session["role"])


# -------------------- BOOK + PAYMENT --------------------
@app.route("/book/<event_id>", methods=["GET", "POST"])
def book_event(event_id):
    if "user" not in session:
        return redirect("/login")

    event = events.find_one({"_id": ObjectId(event_id)})

    if request.method == "POST":
        booking = {
            "user": session["user"],
            "event_id": event_id,
            "event_name": event["title"],
            "price": float(event["price"]),
            "status": "booked"
        }

        bookings.insert_one(booking)

        return render_template("receipt.html", booking=booking)

    return render_template("payment.html", event=event)


# -------------------- MY BOOKINGS --------------------
@app.route("/my_bookings")
def my_bookings():
    if "user" not in session:
        return redirect("/login")

    user_bookings = list(bookings.find({"user": session["user"]}))

    return render_template("my_bookings.html", bookings=user_bookings)


# -------------------- ALL BOOKINGS (ADMIN) --------------------
@app.route("/all_bookings")
def all_bookings():
    if "user" not in session or session["role"] != "admin":
        return redirect("/login")

    all_data = list(bookings.find())

    return render_template("all_bookings.html", bookings=all_data)


# -------------------- CANCEL BOOKING --------------------
@app.route("/cancel_booking/<booking_id>")
def cancel_booking(booking_id):
    booking = bookings.find_one({"_id": ObjectId(booking_id)})

    if booking:
        price = float(booking.get("price", 0))

        refund = price * 0.8  # 80% refund

        bookings.update_one(
            {"_id": ObjectId(booking_id)},
            {
                "$set": {
                    "status": "cancelled",
                    "refund": refund
                }
            }
        )

    return redirect("/my_bookings")


# -------------------- RUN --------------------
if __name__ == "__main__":
    app.run(debug=True)