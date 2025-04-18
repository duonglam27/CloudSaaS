import paramiko
import os
import logging
from getpass import getpass
from paramiko.ssh_exception import AuthenticationException, SSHException

# Cấu hình logging
logging.basicConfig(
    filename="reload_waf.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def reload_nginx(host, username, ssh_key_path=None, password=None, command="sudo nginx -s reload", port=22):
    """
    Kết nối SSH và thực thi lệnh trên máy chủ từ xa (mặc định là reload Nginx).

    Args:
        host (str): Địa chỉ IP hoặc hostname của máy chủ từ xa.
        username (str): Tên đăng nhập SSH.
        ssh_key_path (str, optional): Đường dẫn tới file SSH private key. Mặc định là None.
        password (str, optional): Mật khẩu SSH nếu không sử dụng SSH key. Mặc định là None.
        command (str, optional): Lệnh cần thực thi trên máy chủ từ xa. Mặc định là "sudo nginx -s reload".
        port (int, optional): Cổng SSH. Mặc định là 22.
    """
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        # Kết nối bằng SSH key hoặc mật khẩu
        if ssh_key_path:
            logging.info(f"Connecting to {host}:{port} as {username} using SSH key.")
            ssh.connect(host, port=port, username=username, key_filename=ssh_key_path)
        elif password:
            logging.info(f"Connecting to {host}:{port} as {username} using password.")
            ssh.connect(host, port=port, username=username, password=password)
        else:
            raise ValueError("Cần cung cấp SSH key hoặc mật khẩu để kết nối.")

        # Kiểm tra trạng thái kết nối
        if not ssh.get_transport().is_active():
            raise SSHException("SSH connection is not active.")

        # Thực thi lệnh
        logging.info(f"Executing command: {command} on {host}.")
        stdin, stdout, stderr = ssh.exec_command(command, get_pty=True)
        if password:
            stdin.write(password + '\n')
            stdin.flush()

        # Hiển thị kết quả
        stdout_output = stdout.read().decode().strip()
        stderr_output = stderr.read().decode().strip()
        if stdout_output:
            logging.info(f"Command output: {stdout_output}")
            print("[INFO] Lệnh thực hiện thành công:", stdout_output)
        if stderr_output:
            logging.error(f"Command error: {stderr_output}")
            print("[ERROR] Có lỗi xảy ra:", stderr_output)

    except AuthenticationException:
        logging.error(f"SSH Authentication failed for {username}@{host}.")
        print("[ERROR] Xác thực SSH không thành công. Vui lòng kiểm tra thông tin đăng nhập.")
    except SSHException as e:
        logging.error(f"SSH connection error: {e}")
        print(f"[ERROR] Lỗi kết nối SSH: {e}")
    except ValueError as ve:
        logging.error(f"Input error: {ve}")
        print(f"[ERROR] Lỗi đầu vào: {ve}")
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        print(f"[ERROR] Lỗi không xác định: {e}")
    finally:
        ssh.close()
        logging.info(f"Closed SSH connection to {host}.")
        print("[INFO] Đã đóng kết nối SSH.")

# Ví dụ sử dụng
if __name__ == "__main__":
    host = input("Enter the host (IP or hostname): ")
    username = input("Enter the SSH username: ")

    # Lựa chọn phương thức xác thực
    use_ssh_key = input("Use SSH key? (y/n): ").strip().lower() == 'y'
    ssh_key_path = None
    password = None

    if use_ssh_key:
        ssh_key_path = input("Enter the SSH key path (or leave empty for default): ").strip() or os.path.expanduser("~/.ssh/id_rsa")
    else:
        password = getpass("Enter the SSH password: ")

    port = int(input("Enter SSH port (default 22): ") or 22)

    reload_nginx(
        host=host,
        username=username,
        ssh_key_path=ssh_key_path,
        password=password,
        port=port
    )