from flask import Blueprint, request, jsonify
from app import db
from app.models import WAFLogs

logs_bp = Blueprint('logs', __name__)

@logs_bp.route("/store_logs", methods=["POST"])
def store_logs():
    # 1. Xác thực
    if request.headers.get("X-API-KEY") != "your-secret-key":
        return jsonify({"message": "Unauthorized"}), 401

    # 2. Lấy payload
    data = request.get_json() or {}
    domain   = data.get("domain")
    log_text = data.get("log_text")

    if not domain or not log_text:
        return jsonify({"message": "Invalid data"}), 400

    # 3. Lưu vào database qua SQLAlchemy
    try:
        entry = WAFLogs(domain=domain, log_text=log_text)
        db.session.add(entry)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"DB error: {e}"}), 500

    return jsonify({"message": "Log stored successfully"}), 200
