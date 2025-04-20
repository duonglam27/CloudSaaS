# app/services/reload_waf.py
import paramiko
import logging
from paramiko.ssh_exception import SSHException, AuthenticationException

# Cấu hình logging
logging.basicConfig(
    filename="reload_waf.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

REMOTE_DIR = "/usr/local/nginx/conf"

def connect_ssh(host: str, username: str, ssh_key_path: str = None, port: int = 22):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(host, port=port, username=username, key_filename=ssh_key_path)
        logging.info(f"Successfully connected to {host} as {username}.")
        return ssh
    except AuthenticationException:
        logging.error(f"Authentication failed for {username}@{host}.")
        raise
    except SSHException as e:
        logging.error(f"SSH error while connecting to {host}: {e}")
        raise

def write_config_to_waf(
    host: str,
    username: str,
    ssh_key_path: str,
    remote_path: str,
    config_content: str,
    port: int = 22
):
    try:
        ssh = connect_ssh(host, username, ssh_key_path, port)

        # Tạo thư mục nếu chưa tồn tại
        mkdir_cmd = f"sudo mkdir -p {REMOTE_DIR} && sudo chown -R ubuntu:ubuntu {REMOTE_DIR}"
        ssh.exec_command(mkdir_cmd, get_pty=True)

        # Ghi file cấu hình
        sftp = ssh.open_sftp()
        with sftp.file(remote_path, "w") as remote_file:
            remote_file.write(config_content)
        sftp.chmod(remote_path, 0o644)
        sftp.close()
        logging.info(f"Uploaded config to {host}:{remote_path}")

        # Test và reload Nginx
        test_nginx_config(host, username, ssh_key_path, port)
        reload_nginx(host, username, ssh_key_path, port)

    except Exception as e:
        logging.error(f"Error in write_config_to_waf: {e}")
        raise
    finally:
        ssh.close()


def reload_nginx(host: str, username: str, ssh_key_path: str = None, port: int = 22, command: str = "sudo nginx -s reload"):
    try:
        ssh = connect_ssh(host, username, ssh_key_path, port)
        stdin, stdout, stderr = ssh.exec_command(command, get_pty=True)
        err = stderr.read().decode().strip()
        out = stdout.read().decode().strip()

        if err:
            logging.error(f"Reload stderr: {err}")
            raise RuntimeError(f"Error during Nginx reload: {err}")
        logging.info(f"Reload stdout: {out}")
    except Exception as e:
        logging.error(f"Error while reloading Nginx on {host}: {e}")
        raise
    finally:
        ssh.close()
        logging.info(f"SSH connection to {host} closed.")

def test_nginx_config(host: str, username: str, ssh_key_path: str = None, port: int = 22, command: str = "sudo nginx -t"):
    try:
        ssh = connect_ssh(host, username, ssh_key_path, port)
        stdin, stdout, stderr = ssh.exec_command(command, get_pty=True)
        err = stderr.read().decode().strip()
        out = stdout.read().decode().strip()

        if err:
            logging.error(f"Nginx test stderr: {err}")
            raise RuntimeError(f"Error during Nginx config test: {err}")
        logging.info(f"Nginx test stdout: {out}")
    except Exception as e:
        logging.error(f"Error while testing Nginx config on {host}: {e}")
        raise
    finally:
        ssh.close()
        logging.info(f"SSH connection to {host} closed.")
