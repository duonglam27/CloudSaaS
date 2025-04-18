import os
import subprocess
import re
import ipaddress
import logging

logging.basicConfig(filename="nginx_config.log", level=logging.ERROR, format="%(asctime)s - %(levelname)s - %(message)s")

def validate_domain_name(domain_name):
    """Kiểm tra domain name hợp lệ."""
    regex = r"^(?!-)[A-Za-z0-9-]{1,63}(?<!-)\.(?!-)[A-Za-z0-9-]{1,63}(?<!-)$"
    return re.match(regex, domain_name) is not None

def validate_ip_address(ip_address):
    """Kiểm tra IP hợp lệ (IPv4 hoặc IPv6)."""
    try:
        ipaddress.ip_address(ip_address)
        return True
    except ValueError:
        return False

def generate_nginx_config(domain_name, backend_ip, config_dir="/etc/nginx/sites-available", symlink_dir="/etc/nginx/sites-enabled"):
    try:
        # Validate inputs
        if not domain_name or not backend_ip:
            raise ValueError("Domain name and backend IP must be provided.")
        if not validate_domain_name(domain_name):
            raise ValueError(f"Invalid domain name: {domain_name}")
        if not validate_ip_address(backend_ip):
            raise ValueError(f"Invalid IP address: {backend_ip}")

        # Generate Nginx configuration content
        config_content = f"""
server {{
    listen 80;
    server_name {domain_name};

    location / {{
        proxy_pass http://{backend_ip};
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }}
}}
"""
        config_path = os.path.join(config_dir, f"{domain_name}.conf")
        symlink_path = os.path.join(symlink_dir, f"{domain_name}.conf")

        # Check if configuration already exists
        if os.path.exists(config_path):
            raise FileExistsError(f"Configuration file already exists: {config_path}")

        # Write config file
        with open(config_path, "w") as file:
            file.write(config_content)

        # Create symlink if it doesn't exist
        if not os.path.exists(symlink_path):
            os.symlink(config_path, symlink_path)
        else:
            print(f"Symlink already exists: {symlink_path}")

        # Reload Nginx to apply changes
        subprocess.run(["nginx", "-t"], check=True)  # Test the configuration
        subprocess.run(["systemctl", "reload", "nginx"], check=True)  # Reload Nginx
        print(f"Nginx configuration for {domain_name} created and enabled successfully.")

    except FileExistsError as e:
        logging.error(f"Error: {e}")
        print(f"Error: {e}")
    except subprocess.CalledProcessError as e:
        logging.error(f"Nginx configuration test or reload failed: {e}")
        print(f"Nginx configuration test or reload failed: {e}")
    except Exception as e:
        logging.error(f"Error generating Nginx config: {e}")
        print(f"Error generating Nginx config: {e}")

if __name__ == "__main__":
    domain_name = input("Enter the domain name: ")
    backend_ip = input("Enter the backend IP address: ")
    generate_nginx_config(domain_name, backend_ip)