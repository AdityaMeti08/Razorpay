import sqlite3
import razorpay
import smtplib
from datetime import datetime as dt
from flask import Flask, redirect, request, render_template, url_for

# Initialize the database
def initialize_database():
    # Connect to SQLite database (or create it if it doesn't exist)
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    # Create the 'user' table if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            amount INTEGER NOT NULL,
            email TEXT NOT NULL,
            contact INTEGER NOT NULL,
            timestamp TEXT NOT NULL
        );
    ''')

    conn.commit()
    conn.close()

# Call initialize_database function to set up the database
initialize_database()

# Your Flask application setup
app = Flask(__name__, template_folder="templates", static_folder="static")

@app.route('/')
def home():
    return render_template("index.html")

@app.route('/form', methods=['GET', 'POST'])
def get_details():
    if request.method == 'POST' and request.form.get("username") != "" and request.form.get("amount") != 0 and request.form.get("email") != "" and len(request.form.get("contact")) == 10:
        username = request.form.get("username")
        email = request.form.get("email")
        contact = request.form.get("contact")
        amount = int(request.form.get("amount"))
        return redirect(url_for("checkout", amount=amount, username=username, contact=contact, email=email))
    return render_template("form1.html")

@app.route('/checkout/<int:amount>/<username>/<int:contact>/<email>', methods=['GET', 'POST'])
def checkout(amount, username, contact, email):
    # Razorpay API integration
    key_id = "rzp_test_GZg5qvJjZA6Zik"
    key_secret = "u7fUg81zTqF9Cjr4m5uNr5BU"
    client = razorpay.Client(auth=(key_id, key_secret))
    
    param = {
        "amount": amount * 100,
        "currency": "INR",
        "receipt": "donation",
        "partial_payment": False
    }
    
    conn = sqlite3.connect("database.db")
    id = conn.execute("SELECT id FROM user ORDER BY id DESC LIMIT 1;").fetchone()
    new_id = id[0] + 1 if id else 1  # Start from 1 if no records exist

    # Insert new user data
    conn.execute(f"INSERT INTO user (id, name, amount, email, contact, timestamp) VALUES ({new_id}, '{username}', {amount}, '{email}', {contact}, '{dt.now()}');")
    conn.commit()
    conn.close()
    
    # Create Razorpay order
    order = client.order.create(data=param)
    return render_template("pay1.html", order=order, username=username, contact=contact, email=email)

@app.route('/success', methods=['GET', 'POST'])
def success():
    conn = sqlite3.connect("database.db")
    receiver_email = conn.execute("SELECT email FROM user ORDER BY id DESC LIMIT 1; ").fetchone()[0]
    amount = conn.execute("SELECT amount FROM user ORDER BY id DESC LIMIT 1;").fetchone()[0]
    name = conn.execute("SELECT name FROM user ORDER BY id DESC LIMIT 1;").fetchone()[0]
    conn.commit()
    conn.close()

    # Send email for the payment completion
    password = "your_app_password"
    email = "your_email"
    connection = smtplib.SMTP("smtp.gmail.com")
    connection.starttls()
    connection.login(user=email, password=password)
    connection.sendmail(from_addr=email, to_addrs=receiver_email, msg=f"Subject:Invoice\n\nThank you for completing the payment. Invoice details:\nName: {name}\nAmount: Rs. {amount}\nTransaction ID: 1234567890")
    connection.close()

    return render_template("success.html", amount=amount)

# Run the Flask app
if __name__ == "__main__":
    app.run(debug=True)
