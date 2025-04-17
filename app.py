from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import os


app = Flask(__name__)

# Kết nối tới RDS MySQL
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://admin:yourpassword@<RDS-PRIVATE-ENDPOINT>:3306/dbsaas'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Model người dùng
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)

# Model domain khách hàng
class Domain(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    domain_name = db.Column(db.String(255), nullable=False)

@app.route("/register", methods=["POST"])
def register():
    data = request.json
    user = User(email=data["email"])
    db.session.add(user)
    db.session.commit()
    return jsonify({"message": "User registered", "user_id": user.id})

@app.route("/add-domain", methods=["POST"])
def add_domain():
    data = request.json
    domain = Domain(user_id=data["user_id"], domain_name=data["domain"])
    db.session.add(domain)
    db.session.commit()
    return jsonify({"message": "Domain added"})

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
