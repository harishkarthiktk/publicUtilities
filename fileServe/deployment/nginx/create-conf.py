#!/usr/bin/env python3
"""
create-conf.py: Generate nginx/nginx.conf from template with dynamic paths, OS detection, and client_max_body_size from config.yaml.
Supports macOS/Linux/Windows. See nginx/README.md for usage, testing, and deployment instructions.
Assumes nginx/nginx.conf.template exists with placeholders like {SERVE_FOLDER}, {ACCESS_LOG}, {ERROR_LOG}, {PID_PATH}, {CLIENT_MAX_BODY_SIZE}.
Add nginx/nginx.conf to .gitignore.
"""

import os
import re
import subprocess
import sys
import platform
import yaml

def detect_nginx_paths():
    """Return OS-specific default paths (no detection required). Cross-platform."""
    is_windows = platform.system() == 'Windows'
    
    if is_windows:
        conf_dir = r'C:\nginx\conf'
        log_dir = r'C:\nginx\logs'
        pid_comment = r'C:/nginx/logs/nginx.pid'  # For conf comment
    else:
        conf_dir = '/usr/local/etc/nginx'
        log_dir = '/usr/local/var/log/nginx'
        pid_comment = '/usr/local/var/run/nginx.pid'  # For conf comment
    
    # Simulate detection attempt for warning
    detected = False
    try:
        cmd = ['nginx', '-V']
        subprocess.run(cmd, capture_output=True, text=True, check=True)
        detected = True
    except (subprocess.CalledProcessError, FileNotFoundError):
        if is_windows:
            try:
                cmd = ['nginx.exe', '-V']
                subprocess.run(cmd, capture_output=True, text=True, check=True)
                detected = True
            except (subprocess.CalledProcessError, FileNotFoundError):
                pass
    
    if detected:
        print("Nginx detected successfully.")
    else:
        print("Warning: Nginx not in PATH. Using defaults for reference paths.")
        print(f"  - Manual copy target conf dir: {conf_dir}")
        print(f"  - System log dir (reference): {log_dir}")
        print("  - Install Nginx in PATH for validation.")
    
    return conf_dir, log_dir, pid_comment  # Return pid_comment for conf substitution

def main():
    # Get project root (script is in /nginx, so go up one level)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)

    # Load config.yaml for max_content_length
    config_path = os.path.join(project_root, 'config.yaml')
    default_max_length = 10 * 1024 * 1024  # 10MB default
    client_max_body_size_str = '10m'  # Default nginx string

    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        max_content_length = config.get('max_content_length', default_max_length)

        # Convert bytes to nginx size format
        if max_content_length >= 1024**3:
            size = max_content_length / 1024**3
            suffix = 'g'
        elif max_content_length >= 1024**2:
            size = max_content_length / 1024**2
            suffix = 'm'
        else:
            size = max_content_length / 1024
            suffix = 'k'

        if size.is_integer():
            client_max_body_size_str = f"{int(size)}{suffix}"
        else:
            client_max_body_size_str = f"{size:.1f}{suffix}"
    except (FileNotFoundError, yaml.YAMLError, KeyError) as e:
        print(f"Warning: Could not load max_content_length from {config_path}: {e}. Using default 10m.")

    # Resolve paths (cross-platform: join and normpath, then use / for Nginx conf)
    serve_folder = os.path.normpath(os.path.join(project_root, 'serveFolder'))
    serve_folder_conf = serve_folder.replace(os.sep, '/') + '/'  # Nginx uses /

    logs_dir = os.path.normpath(os.path.join(project_root, 'logs'))
    os.makedirs(logs_dir, exist_ok=True)
    project_access_log = os.path.normpath(os.path.join(logs_dir, 'file-serve.access.log'))
    project_access_log_conf = project_access_log.replace(os.sep, '/')
    project_error_log = os.path.normpath(os.path.join(logs_dir, 'file-serve.error.log'))
    project_error_log_conf = project_error_log.replace(os.sep, '/')

    # Detect/reference paths (always succeeds)
    nginx_conf_dir, nginx_log_dir, pid_comment = detect_nginx_paths()

    # PID always project-local
    pid_path = os.path.normpath(os.path.join(logs_dir, 'nginx.pid'))
    pid_path_conf = pid_path.replace(os.sep, '/')
    print(f"  - PID path: {pid_path} (edit conf for alternatives)")

    # Handle mime.types: Warn if missing
    mime_local_path = os.path.join(script_dir, 'mime.types')
    if not os.path.exists(mime_local_path):
        print(f"Warning: mime.types not found at {mime_local_path}. Copy manually from your Nginx install to this folder for 'include mime.types;'.")

    # Template and output paths
    template_path = os.path.join(script_dir, 'nginx.conf.template')
    output_path = os.path.join(script_dir, 'nginx.conf')

    if not os.path.exists(template_path):
        print(f"Error: Template not found at {template_path}. Create it first with placeholders.")
        sys.exit(1)

    # Read template
    with open(template_path, 'r') as f:
        template = f.read()

    # Substitute placeholders, add PID comment
    conf_content = template.format(
        SERVE_FOLDER=serve_folder_conf,
        ACCESS_LOG=project_access_log_conf,
        ERROR_LOG=project_error_log_conf,
        PID_PATH=f"{pid_path_conf}; # Alternative (system default): {pid_comment}",
        CLIENT_MAX_BODY_SIZE=client_max_body_size_str
    )

    # Write output
    with open(output_path, 'w') as f:
        f.write(conf_content)

    # OS-specific notes
    is_windows = platform.system() == 'Windows'
    print(f"Generated {output_path} (in nginx/ folder)")
    print(f"  - Serve folder: {serve_folder}")
    print(f"  - Logs: {project_access_log} and {project_error_log} (project-local)")
    print(f"  - PID: {pid_path} (with system alternative commented in conf)")
    print(f"  - Manual copy target: {nginx_conf_dir}/nginx.conf (or nginx.d/file-serve.conf)")
    print(f"  - System logs (reference): {nginx_log_dir}")
    if is_windows:
        print("  - Windows: Use forward slashes in conf; run as admin if needed.")
    else:
        print("  - Unix: Ensure permissions for logs/serveFolder.")
    print(f"\nStandalone testing (from nginx/):")
    print(f"  - Copy mime.types to {script_dir} if missing.")
    nginx_cmd = 'nginx.exe' if is_windows else 'nginx'
    print(f"  - Syntax: {nginx_cmd} -t -c {output_path}")
    print(f"  - Start: {nginx_cmd} -c {output_path}")
    print(f"  - Verify: http://localhost:8000")
    print(f"  - Stop: {nginx_cmd} -s quit")
    print(f"\nFor deployment: Edit {output_path} if needed (e.g., PID), then copy to {nginx_conf_dir}.")

if __name__ == '__main__':
    main()