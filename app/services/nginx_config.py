import os
import re
import ipaddress
import logging

# Cấu hình logging
logging.basicConfig(
    filename="nginx_config.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

CONFIG_PATH = "/usr/local/nginx/conf/"

def validate_domain_name(domain_name: str) -> bool:
    """
    Xác thực tên miền hợp lệ.
    """
    domain_regex = r'^([a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}$'
    return bool(re.match(domain_regex, domain_name))

def validate_ip_address(backend_ip: str) -> bool:
    """
    Xác thực địa chỉ IP hợp lệ.
    """
    try:
        ipaddress.ip_address(backend_ip)
        return True
    except ValueError:
        return False

def generate_nginx_config(domain_name: str, backend_ip: str) -> str:
    """
    Sinh server block cấu hình Nginx cho từng khách hàng.
    """
    if not validate_domain_name(domain_name):
        logging.error(f"Invalid domain name: {domain_name}")
        raise ValueError(f"Invalid domain name: {domain_name}")

    if not validate_ip_address(backend_ip):
        logging.error(f"Invalid backend IP: {backend_ip}")
        raise ValueError(f"Invalid backend IP: {backend_ip}")

    logging.info(f"Generating server block for domain: {domain_name}, backend IP: {backend_ip}")

    config = f"""
server {{
    listen 80;
    server_name {domain_name};
    
    access_log /var/log/nginx/{domain_name}_access.log;
    error_log /var/log/nginx/{domain_name}_error.log;
    
    # Trang 403 tùy chỉnh
    error_page 403 /403.html;
    location = /403.html {{
        internal;
        root /usr/share/nginx/html;
    }}

    # Proxy tới backend của khách hàng
    location / {{
        proxy_pass http://{backend_ip};
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }}

    # Trang lỗi 5xx
    error_page 500 502 503 504 /50x.html;
    location = /50x.html {{
        root /usr/share/nginx/html;
    }}
}}
"""
    return config


def save_nginx_config(domain_name: str, config_content: str) -> str:
    config_file_path = os.path.join(CONFIG_PATH, f"{domain_name}.conf")

    try:
        with open(config_file_path, "w") as config_file:
            config_file.write(config_content)

        # Kiểm tra nếu file tồn tại & có nội dung
        if os.path.exists(config_file_path) and os.path.getsize(config_file_path) > 0:
            logging.info(f"Saved server block for {domain_name} at {config_file_path}")
            return config_file_path
        else:
            logging.error(f"File {config_file_path} created but empty!")
            raise IOError("Failed to write config properly")
    except Exception as e:
        logging.error(f"Failed to save server block for {domain_name}: {e}")
        raise



