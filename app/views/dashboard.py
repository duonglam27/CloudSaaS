from flask import Blueprint, render_template, flash, redirect, url_for
from flask_login import login_required, current_user
import logging

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')

# Cấu hình logging
logging.basicConfig(filename='dashboard.log', level=logging.INFO, format='%(asctime)s - %(message)s')


@dashboard_bp.route('/')
@login_required
def index():
    # Ghi log khi người dùng truy cập dashboard
    logging.info(f"User {current_user.email} accessed the dashboard.")

    # Lấy danh sách domains hoặc xử lý lỗi nếu không lấy được
    domains = []
    if hasattr(current_user, 'domains'):
        try:
            domains = current_user.domains.all()
        except Exception as e:
            logging.error(f"Error retrieving domains for user {current_user.email}: {e}")
            flash("Không thể lấy danh sách domains. Vui lòng thử lại sau.", "danger")

    # Thêm thông báo nếu người dùng không có domain
    if not domains:
        domains = [{"domain_name": "Chưa có domain", "backend_ip": "N/A"}]

    # Dữ liệu dashboard
    dashboard_data = {
        "email": current_user.email,
        "domains": domains
    }

    return render_template('dashboard.html', user=dashboard_data)