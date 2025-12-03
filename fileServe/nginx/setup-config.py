#!/usr/bin/env python3
"""
setup-config.py: Generate nginx/nginx.conf from template with dynamic paths.
Place in /nginx folder. Run: cd nginx && python setup-config.py (or python nginx/setup-config.py from root).
Supports macOS/Linux/Windows. Requires nginx in PATH for detection; exits if not found.
Assumes nginx/nginx.conf.template exists with placeholders like {SERVE_FOLDER}, {ACCESS_LOG}, {ERROR_LOG}.
Add nginx/nginx.conf to .gitignore.

Testing the generated conf standalone (without moving to Nginx install dir):
- Ensure mime.types is available: Copy from your Nginx etc/ dir (e.g., cp /opt/homebrew/etc/nginx/mime.types nginx/) if 'include mime.types;' fails.
- Syntax test: nginx -t -c nginx/nginx.conf
- Syntax: nginx -V would tell if there is a path hardcoded for .conf, and if the file exists there, the validation would pass.
- Start Nginx with this conf: nginx -c nginx/nginx.conf (binds to port 8000, proxies to 8002).
- Access http://localhost:8000 to verify.
- Stop: nginx -s quit or pkill nginx.
For full deployment, copy to detected Nginx conf dir.
"""

import os
import re
import subprocess
import sys
import platform

def detect_nginx_paths():
    """Run 'nginx -V' to detect prefix, conf-path, pid-path, mime-types-path, and log dir. Cross-platform."""
    try:
        # Use 'nginx' on Unix/macOS/Linux; on Windows, assume 'nginx' in PATH (common with Chocolatey install)
        cmd = ['nginx', '-V']
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        output = result.stdout

        # Parse --prefix (e.g., /usr/local/nginx)
        prefix_match = re.search(r'--prefix=([^\s]+)', output)
        prefix = prefix_match.group(1) if prefix_match else '/usr/local/nginx'

        # Parse --conf-path (e.g., /usr/local/etc/nginx/nginx.conf)
        conf_match = re.search(r'--conf-path=([^\s]+)', output)
        conf_path = conf_match.group(1) if conf_match else os.path.join(prefix, 'conf/nginx.conf')

        # Parse --pid-path (e.g., /usr/local/var/run/nginx.pid)
        pid_match = re.search(r'--pid-path=([^\s]+)', output)
        pid_path = pid_match.group(1) if pid_match else None

        # Parse --mime-types-path (e.g., /usr/local/etc/nginx/mime.types)
        mime_match = re.search(r'--mime-types-path=([^\s]+)', output)
        mime_types_path = mime_match.group(1) if mime_match else None

        # Derive conf dir
        conf_dir = os.path.dirname(conf_path)
        log_dir = os.path.join(prefix, 'logs')  # Standard log location

        return conf_dir, log_dir, pid_path, mime_types_path
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        # On Windows, if 'nginx' fails, try 'nginx.exe'
        if platform.system() == 'Windows':
            try:
                cmd = ['nginx.exe', '-V']
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                output = result.stdout
                # Repeat parsing logic here for simplicity, or refactor to a function
                prefix_match = re.search(r'--prefix=([^\s]+)', output)
                prefix = prefix_match.group(1) if prefix_match else r'C:\nginx'
                conf_match = re.search(r'--conf-path=([^\s]+)', output)
                conf_path = conf_match.group(1) if conf_match else os.path.join(prefix, 'conf\\nginx.conf')
                pid_match = re.search(r'--pid-path=([^\s]+)', output)
                pid_path = pid_match.group(1) if pid_match else None
                mime_match = re.search(r'--mime-types-path=([^\s]+)', output)
                mime_types_path = mime_match.group(1) if mime_match else None
                conf_dir = os.path.dirname(conf_path)
                log_dir = os.path.join(prefix, 'logs')
                return conf_dir, log_dir, pid_path, mime_types_path
            except (subprocess.CalledProcessError, FileNotFoundError):
                pass
        raise RuntimeError(f"Nginx not found in PATH. Install Nginx and ensure 'nginx -V' (or 'nginx.exe -V' on Windows) works before generating conf. Error: {e}")

def main():
    import shutil  # For copying mime.types

    # Get project root (script is in /nginx, so go up one level)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)

    # Resolve paths (cross-platform: join and normpath, then use / for Nginx conf)
    serve_folder = os.path.normpath(os.path.join(project_root, 'serveFolder'))
    serve_folder_conf = serve_folder.replace(os.sep, '/') + '/'  # Nginx uses /

    logs_dir = os.path.normpath(os.path.join(project_root, 'logs'))
    os.makedirs(logs_dir, exist_ok=True)
    project_access_log = os.path.normpath(os.path.join(logs_dir, 'file-serve.access.log'))
    project_access_log_conf = project_access_log.replace(os.sep, '/')
    project_error_log = os.path.normpath(os.path.join(logs_dir, 'file-serve.error.log'))
    project_error_log_conf = project_error_log.replace(os.sep, '/')

    # Detect Nginx paths (exits if fails)
    try:
        nginx_conf_dir, nginx_log_dir, detected_pid_path, detected_mime_types_path = detect_nginx_paths()
    except RuntimeError as e:
        print(e)
        sys.exit(1)

    # Handle PID path with fallback to project-local
    if detected_pid_path:
        pid_path = os.path.normpath(detected_pid_path)
    else:
        pid_path = os.path.normpath(os.path.join(logs_dir, 'nginx.pid'))
        print(f"Warning: PID path not detected; using project-local fallback: {pid_path}")
    pid_path_conf = pid_path.replace(os.sep, '/')

    # Handle mime.types: Copy from detected path if possible
    mime_local_path = os.path.join(script_dir, 'mime.types')
    if not os.path.exists(mime_local_path) and detected_mime_types_path and os.path.exists(detected_mime_types_path):
        try:
            shutil.copy(detected_mime_types_path, mime_local_path)
            print(f"Copied mime.types from {detected_mime_types_path} to {mime_local_path}")
        except (OSError, shutil.Error) as e:
            print(f"Warning: Could not copy mime.types from detected path. Please copy manually from {detected_mime_types_path}. Error: {e}")
    elif not os.path.exists(mime_local_path):
        print(f"Warning: mime.types not found locally. Please copy from your Nginx installation (e.g., /usr/local/etc/nginx/mime.types on macOS/Linux, C:\\nginx\\conf\\mime.types on Windows).")

    # Template and output paths
    template_path = os.path.join(script_dir, 'nginx.conf.template')
    output_path = os.path.join(script_dir, 'nginx.conf')

    if not os.path.exists(template_path):
        print(f"Error: Template not found at {template_path}. Create it first with placeholders.")
        sys.exit(1)

    # Read template
    with open(template_path, 'r') as f:
        template = f.read()

    # Substitute placeholders
    conf_content = template.format(
        SERVE_FOLDER=serve_folder_conf,
        ACCESS_LOG=project_access_log_conf,
        ERROR_LOG=project_error_log_conf,
        PID_PATH=pid_path_conf,
    )

    # Write output (only if detection succeeded)
    with open(output_path, 'w') as f:
        f.write(conf_content)

    # OS-specific notes
    is_windows = platform.system() == 'Windows'
    is_linux = platform.system() == 'Linux'
    print(f"Generated {output_path}")
    print(f"  - Serve folder: {serve_folder}")
    print(f"  - Logs: {project_access_log} and {project_error_log}")
    print(f"  - PID path: {pid_path}")
    print(f"  - Nginx conf dir (for deployment): {nginx_conf_dir}")
    print(f"  - Nginx log dir (system): {nginx_log_dir}")
    if is_windows:
        print("  - Windows note: Paths normalized with / for Nginx; ensure Nginx service runs with appropriate privileges for PID/logs.")
    elif is_linux:
        print("  - Linux note: Ensure Nginx user has access to serveFolder and logs dir.")
    print(f"\nStandalone testing:")
    print(f"  - Ensure mime.types exists in the same folder as {output_path} (copied automatically if detected; otherwise, copy manually from your Nginx installation).")
    nginx_cmd = 'nginx.exe' if is_windows else 'nginx'
    print(f"  - Syntax test: {nginx_cmd} -t -c {output_path} (fails if mime.types missing)")
    print(f"  - Start Nginx: {nginx_cmd} -c {output_path} (requires app running on port 8002)")
    print(f"  - Verify: Open http://localhost:8000 in browser")
    print(f"  - Stop: {nginx_cmd} -s quit (or pkill {nginx_cmd} on Unix/macOS/Linux)")
    print(f"For deployment, copy to {nginx_conf_dir}/nginx.d/file-serve.conf (or include it in main nginx.conf)")

if __name__ == '__main__':
    main()