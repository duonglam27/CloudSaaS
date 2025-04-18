from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, login_required, logout_user
from app import db
from app.models import User
from werkzeug.security import generate_password_hash, check_password_hash
import logging
import re  # Thư viện để kiểm tra định dạng email

auth_bp = Blueprint('auth', __name__)

# Cấu hình logging
logging.basicConfig(filename='auth.log', level=logging.INFO, format='%(asctime)s - %(message)s')

def validate_email(email):
    """Kiểm tra định dạng email hợp lệ."""
    email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z]{2,}$'
    return re.match(email_regex, email)

def validate_password(password):
    """Kiểm tra độ mạnh của mật khẩu."""
    if len(password) < 8:
        return False
    if not any(char.isdigit() for char in password):
        return False
    if not any(char.islower() for char in password):
        return False
    if not any(char.isupper() for char in password):
        return False
    return True

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password_hash, password):
            remember = 'remember' in request.form
            login_user(user, remember=remember)
            logging.info(f"User {email} logged in successfully.")
            flash("Đăng nhập thành công!", "success")
            return redirect(url_for('dashboard.index'))
        else:
            logging.warning(f"Failed login attempt for email {email}.")
            flash("Email hoặc mật khẩu không chính xác. Vui lòng thử lại.", "danger")
    return render_template('login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    user = request.form.get('email')  # Optional: log the user being logged out
    logout_user()
    logging.info(f"User logged out.")
    flash("Bạn đã đăng xuất.", "info")
    return redirect(url_for('auth.login'))

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        if not validate_email(email):
            flash("Email không hợp lệ. Vui lòng nhập lại.", "danger")
            return render_template('register.html')

        if not validate_password(password):
            flash("Mật khẩu phải có ít nhất 8 ký tự, bao gồm chữ hoa, chữ thường, và số.", "danger")
            return render_template('register.html')

        if User.query.filter_by(email=email).first():
            flash("Email đã được sử dụng. Vui lòng chọn email khác.", "danger")
            return render_template('register.html')

        hashed_password = generate_password_hash(password, method='sha256')
        new_user = User(email=email, password_hash=hashed_password)

        try:
            db.session.add(new_user)
            db.session.commit()
            logging.info(f"User {email} registered successfully.")
            flash("Đăng ký thành công! Bạn có thể đăng nhập ngay bây giờ.", "success")
            return redirect(url_for('auth.login'))
        except Exception as e:
            logging.error(f"Error adding user {email} to database: {e}")
            flash("Đã xảy ra lỗi. Vui lòng thử lại.", "danger")

    return render_template('register.html')