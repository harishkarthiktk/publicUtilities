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
    """Run 'nginx -V' to detect prefix, conf-path, and log dir. Cross-platform."""
    try:
        # Use 'nginx' on Unix/macOS; 'nginx.exe' on Windows if needed, but assume 'nginx' in PATH
        cmd = ['nginx', '-V']
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        output = result.stdout

        # Parse --prefix (e.g., /usr/local/nginx)
        prefix_match = re.search(r'--prefix=([^\s]+)', output)
        prefix = prefix_match.group(1) if prefix_match else '/usr/local/nginx'

        # Parse --conf-path (e.g., /usr/local/etc/nginx/nginx.conf)
        conf_match = re.search(r'--conf-path=([^\s]+)', output)
        conf_path = conf_match.group(1) if conf_match else os.path.join(prefix, 'conf/nginx.conf')

        # Derive conf dir
        conf_dir = os.path.dirname(conf_path)
        log_dir = os.path.join(prefix, 'logs')  # Standard log location

        return conf_dir, log_dir
    except (subprocess.CalledProcessError, FileNotFoundError):
        raise RuntimeError("Nginx not found in PATH. Install Nginx and ensure 'nginx -V' works before generating conf.")

def main():
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
        nginx_conf_dir, nginx_log_dir = detect_nginx_paths()
    except RuntimeError as e:
        print(e)
        sys.exit(1)

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
    )

    # Write output (only if detection succeeded)
    with open(output_path, 'w') as f:
        f.write(conf_content)

    # OS-specific notes
    is_windows = platform.system() == 'Windows'
    print(f"Generated {output_path}")
    print(f"  - Serve folder: {serve_folder}")
    print(f"  - Logs: {project_access_log} and {project_error_log}")
    print(f"  - Nginx conf dir (for deployment): {nginx_conf_dir}")
    print(f"  - Nginx log dir (system): {nginx_log_dir}")
    if is_windows:
        print("  - Windows note: Ensure Nginx is in PATH; paths normalized for compatibility.")
    print(f"\nStandalone testing:")
    print(f"  - Copy mime.types to project (for include): cp /opt/homebrew/etc/nginx/mime.types {script_dir}/ (adjust path for your Nginx install, e.g., /usr/local/etc/nginx/mime.types)")
    print(f"  - Syntax test: nginx -t -c {output_path}")
    print(f"  - Start Nginx: nginx -c {output_path} (requires app running on port 8002)")
    print(f"  - Verify: Open http://localhost:8000 in browser")
    print(f"  - Stop: nginx -s quit (or pkill nginx)")
    print(f"For deployment, copy to {nginx_conf_dir}/nginx.d/file-serve.conf (or include it)")

if __name__ == '__main__':
    main()