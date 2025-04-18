from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models import Domain
import re
import ipaddress
import logging

domains_bp = Blueprint('domains', __name__, url_prefix='/domains')

# Cấu hình logging
logging.basicConfig(filename='domains.log', level=logging.INFO, format='%(asctime)s - %(message)s')

def validate_domain_name(domain_name):
    """Kiểm tra định dạng tên domain hợp lệ."""
    domain_regex = r'^(?!-)[A-Za-z0-9-]{1,63}(?<!-)\.(?!-)[A-Za-z0-9-]{1,63}(?<!-)$'
    return re.match(domain_regex, domain_name)

def validate_ip_address(ip_address):
    """Kiểm tra địa chỉ IP hợp lệ."""
    try:
        ipaddress.ip_address(ip_address)
        return True
    except ValueError:
        return False

@domains_bp.route('/add-domain', methods=['GET', 'POST'])
@login_required
def add_domain():
    if request.method == 'POST':
        domain_name = request.form.get('domain_name')
        backend_ip = request.form.get('backend_ip')

        logging.info(f"User {current_user.email} is attempting to add domain {domain_name} with backend IP {backend_ip}.")

        # Kiểm tra dữ liệu hợp lệ
        if not domain_name or not backend_ip:
            flash("Tên domain và Backend IP không được để trống.", "danger")
            return render_template('add_domain.html')

        if not validate_domain_name(domain_name):
            flash("Tên domain không hợp lệ. Vui lòng nhập lại.", "danger")
            return render_template('add_domain.html')

        if not validate_ip_address(backend_ip):
            flash("Địa chỉ IP không hợp lệ. Vui lòng nhập lại.", "danger")
            return render_template('add_domain.html')

        # Kiểm tra domain đã tồn tại cho người dùng hiện tại
        existing_domain = Domain.query.filter_by(domain_name=domain_name, user_id=current_user.id).first()
        if existing_domain:
            flash("Domain này đã tồn tại trong tài khoản của bạn. Vui lòng chọn tên khác.", "warning")
            return render_template('add_domain.html')

        # Thêm domain mới
        new_domain = Domain(domain_name=domain_name, backend_ip=backend_ip, user_id=current_user.id)
        try:
            db.session.add(new_domain)
            db.session.commit()
            flash("Domain đã được thêm thành công.", "success")
            logging.info(f"Domain {domain_name} thêm thành công bởi {current_user.email}.")
            return redirect(url_for('dashboard.index'))
        except Exception as e:
            db.session.rollback()
            logging.error(f"Lỗi khi thêm domain {domain_name} bởi {current_user.email}: {e}")
            flash("Đã xảy ra lỗi khi thêm domain. Vui lòng thử lại.", "danger")

    return render_template('add_domain.html')


@domains_bp.route('/delete', methods=['POST'])
@login_required
def delete_domain():
    domain_id = request.form.get('domain_id')

    # Kiểm tra xem domain có tồn tại không
    domain = Domain.query.filter_by(id=domain_id, user_id=current_user.id).first()
    if not domain:
        flash("Domain không tồn tại hoặc bạn không có quyền xóa.", "danger")
        return redirect(url_for('dashboard.index'))

    # Xóa domain
    try:
        db.session.delete(domain)
        db.session.commit()
        flash("Domain đã được xóa thành công.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Đã xảy ra lỗi khi xóa domain: {e}", "danger")

    return redirect(url_for('dashboard.index'))