import os
from app import create_app, db
from app.models import User, Domain

app = create_app()

if __name__ == "__main__":
    with app.app_context():
        # Tạo các bảng trực tiếp trong cơ sở dữ liệu
        db.create_all()

        # Thêm dữ liệu mẫu nếu chưa có
        if not User.query.filter_by(email='admin@example.com').first():
            # Tạo admin user
            admin_user = User(email='admin@example.com')
            admin_user.set_password('admin123')
            db.session.add(admin_user)
            db.session.commit()

            # Tạo các domain mẫu
            domain1 = Domain(domain_name='example.com', backend_ip='192.168.1.100', user_id=admin_user.id)
            domain2 = Domain(domain_name='testsite.com', backend_ip='192.168.1.101', user_id=admin_user.id)
            db.session.add_all([domain1, domain2])
            db.session.commit()

            print("Sample admin user and domains created!")
        else:
            print("Sample data already exists.")

    # Đọc chế độ debug từ biến môi trường (mặc định là True)
    debug_mode = os.getenv("FLASK_DEBUG", "True").lower() == "true"
    app.run(debug=debug_mode)