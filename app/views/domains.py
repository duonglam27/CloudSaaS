# app/views/domains.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models import Domain
import logging
from app.services.nginx_config import generate_nginx_config
from app.services.reload_waf import connect_ssh, reload_nginx, write_config_to_waf

# Cấu hình logging
logging.basicConfig(filename='domains.log', level=logging.INFO, format='%(asctime)s - %(message)s')

domains_bp = Blueprint('domains', __name__, url_prefix='/domains')

def validate_domain_name(domain_name):
    import re
    domain_regex = r'^[A-Za-z0-9-.]+$'
    return bool(re.match(domain_regex, domain_name))

def validate_ip_address(ip_address):
    import ipaddress
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

        if not domain_name or not backend_ip:
            flash("Tên domain và Backend IP không được để trống.", "danger")
            return render_template('add_domain.html')

        if not validate_domain_name(domain_name):
            flash("Tên domain không hợp lệ. Vui lòng nhập lại.", "danger")
            return render_template('add_domain.html')

        if not validate_ip_address(backend_ip):
            flash("Địa chỉ IP không hợp lệ. Vui lòng nhập lại.", "danger")
            return render_template('add_domain.html')

        existing_domain = Domain.query.filter_by(domain_name=domain_name, user_id=current_user.id).first()
        if existing_domain:
            flash("Domain này đã tồn tại trong tài khoản của bạn. Vui lòng chọn tên khác.", "warning")
            return render_template('add_domain.html')

        new_domain = Domain(domain_name=domain_name, backend_ip=backend_ip, user_id=current_user.id)
        try:
            db.session.add(new_domain)
            db.session.commit()
            flash("Domain đã được thêm thành công.", "success")
            logging.info(f"Domain {domain_name} thêm thành công bởi {current_user.email}.")

            try:
                config_content = generate_nginx_config(domain_name, backend_ip)
                deploy_config_to_waf(domain_name, config_content)
                logging.info(f"Đã ghi và triển khai cấu hình cho domain {domain_name} lên WAF.")
            except Exception as deploy_err:
                logging.error(f"Lỗi khi triển khai WAF cho domain {domain_name}: {deploy_err}")
                flash("Domain đã được thêm, nhưng không triển khai được lên WAF.", "warning")

            return redirect(url_for('dashboard.index'))
        except Exception as e:
            db.session.rollback()
            logging.error(f"Lỗi khi thêm domain {domain_name} bởi {current_user.email}: {e}")
            flash("Đã xảy ra lỗi khi thêm domain. Vui lòng thử lại.", "danger")

    return render_template('add_domain.html')

@domains_bp.route('/delete-domain/<int:domain_id>', methods=['POST'])
@login_required
def delete_domain(domain_id):
    domain = Domain.query.filter_by(id=domain_id, user_id=current_user.id).first()

    if not domain:
        flash("Domain không tồn tại hoặc bạn không có quyền xóa domain này.", "danger")
        logging.warning(f"User {current_user.email} tried to delete a non-existent or unauthorized domain (ID: {domain_id}).")
        return redirect(url_for('dashboard.index'))

    domain_name = domain.domain_name

    try:
        db.session.delete(domain)
        db.session.commit()
        flash(f"Domain {domain_name} đã được xóa thành công.", "success")
        logging.info(f"Domain {domain_name} (ID: {domain_id}) đã bị xóa bởi {current_user.email}.")

        try:
            remove_domain_from_waf(domain_name)
        except Exception as waf_err:
            logging.error(f"Lỗi khi xóa file cấu hình trên WAF cho domain {domain_name}: {waf_err}")
            flash(f"Domain {domain_name} đã bị xóa, nhưng gặp lỗi khi đồng bộ trên WAF.", "warning")

    except Exception as e:
        db.session.rollback()
        logging.error(f"Lỗi khi xóa domain {domain_name} (ID: {domain_id}) bởi {current_user.email}: {e}")
        flash(f"Đã xảy ra lỗi khi xóa domain {domain_name}. Vui lòng thử lại.", "danger")

    return redirect(url_for('dashboard.index'))

def deploy_config_to_waf(domain_name, config_content):
    import os
    ssh_host = os.getenv('WAF_SSH_HOST', '52.54.100.111')
    ssh_username = os.getenv('WAF_SSH_USER', 'nginx')
    ssh_key_path = os.getenv('WAF_SSH_KEY', '/home/ubuntu/keys/keyEC2WAF.pem')
    remote_file_path = f"/usr/local/nginx/conf/{domain_name}.conf"

    if not os.path.exists(ssh_key_path):
        raise FileNotFoundError(f"Private key không tồn tại tại {ssh_key_path}")

    try:
        write_config_to_waf(ssh_host, ssh_username, ssh_key_path, remote_file_path, config_content)
    except Exception as e:
        raise RuntimeError(f"Lỗi khi ghi file cấu hình lên WAF: {e}")

def remove_domain_from_waf(domain_name):
    import os
    ssh_host = os.getenv('WAF_SSH_HOST', '52.54.100.111')
    ssh_username = os.getenv('WAF_SSH_USER', 'nginx')
    ssh_key_path = os.getenv('WAF_SSH_KEY', '/home/ubuntu/keys/keyEC2WAF.pem')
    remote_file_path = f"/usr/local/nginx/conf/{domain_name}.conf"

    try:
        ssh = connect_ssh(ssh_host, ssh_username, ssh_key_path)
        remove_cmd = f"sudo rm -f {remote_file_path}"
        stdin, stdout, stderr = ssh.exec_command(remove_cmd, get_pty=True)
        err = stderr.read().decode().strip()
        if err:
            logging.error(f"Error while removing file {remote_file_path} on WAF: {err}")
            raise RuntimeError(f"Error while removing file on WAF: {err}")

        logging.info(f"File cấu hình {remote_file_path} đã được xóa trên WAF.")
        reload_nginx(ssh_host, ssh_username, ssh_key_path)
    except Exception as e:
        logging.error(f"Lỗi khi xóa domain {domain_name} trên WAF: {e}")
        raise
    finally:
        ssh.close()
        logging.info(f"SSH connection to {ssh_host} closed.")
