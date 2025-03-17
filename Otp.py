from flask import Flask, request, jsonify
from flask_pymongo import PyMongo
import random
import datetime

app = Flask(__name__)

# Configure MongoDB connection
app.config["MONGO_URI"] = "mongodb://localhost:27017/Linu"
mongo = PyMongo(app)

# Collection references
users_collection = mongo.db.users
otp_collection = mongo.db.otp_codes


def generate_otp():
    """Generate a random 6-digit OTP."""
    return str(random.randint(100000, 999999))


def add_sample_users():
    """Insert 10 sample anime users if they don't already exist."""
    sample_users = [
        {"name": "Monkey D. Luffy", "email": "luffy@gmail.com"},
        {"name": "Naruto Uzumaki", "email": "naruto@gmail.com"},
        {"name": "Ichigo Kurosaki", "email": "ichigo@bleach.com"},
        {"name": "Goku", "email": "goku@dragonball.com"},
        {"name": "Levi Ackerman", "email": "levi@attackontitan.com"},
        {"name": "Light Yagami", "email": "light@deathnote.com"},
        {"name": "Edward Elric", "email": "edward@fma.com"},
        {"name": "Gojo Satoru", "email": "gojo@jujutsukaisen.com"},
        {"name": "Kakashi Hatake", "email": "kakashi@naruto.com"},
        {"name": "Roronoa Zoro", "email": "zoro@onepiece.com"},
    ]

    for user in sample_users:
        users_collection.update_one(
            {"email": user["email"]},
            {"$set": user},
            upsert=True
        )


@app.route('/send-otp', methods=['POST'])
def send_otp():
    data = request.json
    name = data.get('name')
    email = data.get('email')

    if not name or not email:
        return jsonify({"success": False, "message": "Name and email are required!"}), 400

    otp = generate_otp()
    expiry_time = datetime.datetime.utcnow() + datetime.timedelta(minutes=5)  # OTP valid for 5 minutes

    # Save OTP in the database (delete previous OTP for the same email)
    otp_collection.delete_many({"email": email})  # Remove old OTPs
    otp_collection.insert_one({"email": email, "otp": otp, "expiry": expiry_time})

    # Simulate sending OTP (in real-world, integrate with an email service)
    print(f"OTP for {email}: {otp}")

    return jsonify({"success": True, "message": "OTP sent successfully!"})


@app.route('/verify-otp', methods=['POST'])
def verify_otp():
    data = request.json
    email = data.get('email')
    entered_otp = data.get('otp')

    if not email or not entered_otp:
        return jsonify({"success": False, "message": "Email and OTP are required!"}), 400

    # Fetch OTP from database
    otp_record = otp_collection.find_one({"email": email})

    if not otp_record:
        return jsonify({"success": False, "message": "No OTP found. Please request a new one!"}), 400

    # Check if OTP is expired
    if otp_record["expiry"] < datetime.datetime.utcnow():
        otp_collection.delete_one({"email": email})  # Remove expired OTP
        return jsonify({"success": False, "message": "OTP expired. Please request a new one!"}), 400

    # Verify OTP
    if otp_record["otp"] == entered_otp:
        otp_collection.delete_one({"email": email})  # Remove used OTP

        # Store user details (optional: only if you want to keep track of logins)
        users_collection.update_one(
            {"email": email},
            {"$set": {"name": data.get('name'), "email": email, "last_login": datetime.datetime.utcnow()}},
            upsert=True
        )

        return jsonify({"success": True, "message": "OTP verified! Login successful."})

    return jsonify({"success": False, "message": "Invalid OTP. Please try again!"}), 400


if __name__ == '__main__':
    add_sample_users()  # Insert anime users when the server starts
    app.run(debug=True, port=3000)
