from flask import Blueprint, render_template, flash, redirect, url_for
from flask_login import login_required, current_user
import logging
from app import db
from app.models import Domain, WAFLogs

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')

# Cấu hình logging
logging.basicConfig(filename='dashboard.log', level=logging.INFO, format='%(asctime)s - %(message)s')

@dashboard_bp.route('/')
@login_required
def index():
    """
    Route để hiển thị dashboard của người dùng.
    """
    # Ghi log khi người dùng truy cập dashboard
    logging.info(f"User {current_user.email} accessed the dashboard.")

    # Lấy danh sách domains hoặc xử lý lỗi nếu không lấy được
    domains = []
    try:
        if hasattr(current_user, 'domains'):
            domains = current_user.domains.all()
    except Exception as e:
        logging.error(f"Error retrieving domains for user {current_user.email}: {e}")
        flash("Không thể lấy danh sách domains. Vui lòng thử lại sau.", "danger")

    # Thêm thông báo nếu người dùng không có domain nào
    if not domains:
        flash("Hiện tại bạn chưa có domain nào. Hãy thêm domain mới!", "info")

    # Dữ liệu dashboard
    dashboard_data = {
        "email": current_user.email,
        "domains": domains
    }

    return render_template('dashboard.html', user=dashboard_data)

@dashboard_bp.route('/logs/<domain_id>')
@login_required
def view_logs(domain_id):
    """
    Hiển thị log của một domain cụ thể cho người dùng.
    """
    # Xác thực domain này có thuộc về user không
    domain = Domain.query.get(domain_id)
    try:
        if not domain.user_id==current_user.id:
            flash("Bạn không có quyền xem log của domain này.", "danger")
            return redirect(url_for('dashboard.index'))
    except Exception as e:
        print(e)
        logging.error(f"Error checking domain ownership for user {current_user.email}: {e}")
        flash("Lỗi khi kiểm tra quyền truy cập domain.", "danger")
        return redirect(url_for('dashboard.index'))

    # Lấy log từ MySQL
    logs = []
    try:
        # Sử dụng context manager cho DB để tự động đóng connection
        with db.cursor() as cursor:
            cursor.execute(
                "SELECT timestamp, log_text FROM waf_logs WHERE domain = %s ORDER BY timestamp DESC LIMIT 100",
                (domain,)
            )
            logs = WAFLogs.query.filter_by(domain_id=domain_id).order_by(WAFLogs.timestamp.desc()).all()
    except Exception as e:
        logging.error(f"Error retrieving logs for domain {domain}: {e}")
        flash("Không thể lấy log. Vui lòng thử lại sau.", "danger")

    return render_template("view_log.html", domain=domain, access_log=logs)
