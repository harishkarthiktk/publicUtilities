import http.server
import socketserver
import threading
import time
import requests
import json
from urllib.parse import urlencode, urlparse, parse_qs
import webbrowser
import argparse
import os
import ssl
import subprocess

# Fixed URLs
AUTH_URL = 'https://accounts.zoho.com/oauth/v2/auth'
TOKEN_URL = 'https://accounts.zoho.com/oauth/v2/token'

CONFIG_FILE = 'config.json'

def load_config():
    """Load configuration from config.json."""
    default_config = {
        "CLIENT_ID": "your_client_id_here",
        "CLIENT_SECRET": "your_client_secret_here",
        "REDIRECT_URI": "http://localhost:3000/callback",
        "SCOPE": "SDPOnDemand.requests.READ",
        "API_DOMAIN": "sdpondemand.manageengine.com",
        "PORTAL": "your_portal_id",
        "TOKENS_FILE": "oauth_tokens.json"
    }
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
            # Merge with defaults to ensure all keys are present
            default_config.update(config)
    else:
        # Create default config file
        with open(CONFIG_FILE, 'w') as f:
            json.dump(default_config, f, indent=2)
        print(f"Created {CONFIG_FILE} with default values. Please update it with your actual values.")
    return default_config

config = load_config()
CLIENT_ID = config['CLIENT_ID']
CLIENT_SECRET = config['CLIENT_SECRET']
REDIRECT_URI = config['REDIRECT_URI']
SCOPE = config['SCOPE']
API_DOMAIN = config['API_DOMAIN']
PORTAL = config['PORTAL']
TOKENS_FILE = config['TOKENS_FILE']

def get_auth_url():
    """Generate the authorization URL."""
    params = {
        'response_type': 'code',
        'client_id': CLIENT_ID,
        'scope': SCOPE,
        'redirect_uri': REDIRECT_URI,
        'access_type': 'offline',
        'prompt': 'consent'
    }
    return f"{AUTH_URL}?{urlencode(params)}"

def generate_self_signed_cert(host='localhost', port=8000):
    """Generate self-signed certificate and key for local HTTPS server if they don't exist."""
    cert_file = f"{host}_{port}_cert.pem"
    key_file = f"{host}_{port}_key.pem"

    if os.path.exists(cert_file) and os.path.exists(key_file):
        print(f"Using existing certificate {cert_file} and key {key_file}.")
        return cert_file, key_file

    print("Generating self-signed certificate for local HTTPS server...")
    try:
        # Use openssl to generate self-signed cert (assumes openssl is installed on macOS)
        subject = f"/C=US/ST=State/L=City/O=Org/CN={host}"
        subprocess.check_call([
            'openssl', 'req', '-x509', '-newkey', 'rsa:4096', '-keyout', key_file,
            '-out', cert_file, '-days', '365', '-nodes', '-subj', subject
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"Generated {cert_file} and {key_file}.")
        return cert_file, key_file
    except subprocess.CalledProcessError:
        raise RuntimeError("Failed to generate self-signed certificate. Ensure openssl is installed (e.g., via Homebrew: brew install openssl).")


class OAuthCallbackHandler(http.server.BaseHTTPRequestHandler):
    """Custom handler for OAuth callback. Extracts code from query params on /callback GET."""
    code = None
    error = None

    def do_GET(self):
        # Security: Only accept requests from localhost
        if self.client_address[0] not in ['127.0.0.1', '::1']:
            self.send_response(403)
            self.end_headers()
            self.wfile.write(b'Access denied.')
            return

        if self.path.startswith('/callback'):
            parsed = urlparse(f"http://dummy{self.path}")
            query_params = parse_qs(parsed.query)
            if 'code' in query_params:
                OAuthCallbackHandler.code = query_params['code'][0]
                print(f"DEBUG: Code received: {OAuthCallbackHandler.code}")  # Debug print; remove after testing
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(b'<html><body>Authorization successful! You can close this window and return to the terminal.</body></html>')
            elif 'error' in query_params:
                OAuthCallbackHandler.error = query_params['error'][0]
                print(f"DEBUG: Error received: {OAuthCallbackHandler.error}")  # Debug print; remove after testing
                self.send_response(400)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(b'<html><body>Authorization failed: ' + OAuthCallbackHandler.error.encode() + b'. Please try again.</body></html>')
            else:
                print("DEBUG: No code or error in query params")  # Debug print; remove after testing
                self.send_response(404)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(b'<html><body>Invalid callback path or missing parameters.</body></html>')
        else:
            print(f"DEBUG: Invalid path: {self.path}")  # Debug print; remove after testing
            self.send_response(404)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b'<html><body>Path not found.</body></html>')

    def log_message(self, format, *args):
        # Suppress server logs for cleaner output
        pass


def authorize():
    """Open browser for authorization and automatically retrieve the code via local server (HTTP/HTTPS).
    Starts a temporary server on the port and protocol specified in REDIRECT_URI to handle the OAuth callback."""
    # Parse redirect URI to get scheme, host, port, path
    parsed_uri = urlparse(REDIRECT_URI)
    scheme = parsed_uri.scheme
    host = parsed_uri.hostname
    port = parsed_uri.port or (443 if scheme == 'https' else 80)
    callback_path = parsed_uri.path or '/callback'  # Default to /callback if no path

    if host != 'localhost':
        raise ValueError("Redirect URI must use 'localhost' for local server handling.")

    if port == 80 or port == 443:
        print("Warning: Using privileged port. May require elevated permissions.")

    is_https = scheme == 'https'

    if is_https:
        cert_file, key_file = generate_self_signed_cert(host, port)
        protocol_msg = "HTTPS"
    else:
        cert_file = key_file = None
        protocol_msg = "HTTP"

    auth_url = get_auth_url()
    print(f"Starting local {protocol_msg} server on {scheme}://{host}:{port}...")
    print(f"Listening for callback at {REDIRECT_URI}")
    print(f"Opening browser for authorization: {auth_url}")

    # Note: Browser may show security warning for self-signed cert; user must proceed.

    # Reset class variables
    OAuthCallbackHandler.code = None
    OAuthCallbackHandler.error = None

    # Create server
    httpd = socketserver.TCPServer((host, port), OAuthCallbackHandler)

    if is_https:
        # Use SSLContext for better compatibility
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(certfile=cert_file, keyfile=key_file)
        httpd.socket = context.wrap_socket(httpd.socket, server_side=True)
        print("Warning: Browser may show 'Your connection is not private' warning. Click 'Advanced' > 'Proceed to localhost (unsafe)' to continue.")

    # Start server in thread
    server_thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    server_thread.start()

    # Open browser
    webbrowser.open(auth_url)

    # Wait for code, error, or timeout
    start_time = time.time()
    timeout = 120  # 2 minutes timeout

    while time.time() - start_time < timeout:
        if OAuthCallbackHandler.code:
            httpd.shutdown()
            server_thread.join(timeout=1)
            print("Authorization successful! Code received.")
            return OAuthCallbackHandler.code
        elif OAuthCallbackHandler.error:
            httpd.shutdown()
            server_thread.join(timeout=1)
            raise ValueError(f"Authorization error: {OAuthCallbackHandler.error}")
        time.sleep(0.5)

    # Timeout
    httpd.shutdown()
    server_thread.join(timeout=1)
    raise TimeoutError(f"Authorization request timed out after {timeout} seconds. Please check the browser and try again.")

def get_tokens(code):
    """Exchange authorization code for access and refresh tokens."""
    data = {
        'code': code,
        'grant_type': 'authorization_code',
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'redirect_uri': REDIRECT_URI
    }
    response = requests.post(TOKEN_URL, data=data)
    response.raise_for_status()
    return response.json()

def refresh_access_token(refresh_token):
    """Refresh the access token using the refresh token."""
    data = {
        'refresh_token': refresh_token,
        'grant_type': 'refresh_token',
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'redirect_uri': REDIRECT_URI
    }
    response = requests.post(TOKEN_URL, data=data)
    response.raise_for_status()
    return response.json()

def load_tokens():
    """Load tokens from file."""
    try:
        with open(TOKENS_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return None

def save_tokens(tokens):
    """Save tokens to file."""
    with open(TOKENS_FILE, 'w') as f:
        json.dump(tokens, f, indent=2)

def get_valid_access_token():
    """Get a valid access token, authorizing or refreshing as needed."""
    tokens = load_tokens()
    if not tokens:
        print("No tokens found. Starting authorization flow.")
        code = authorize()
        tokens = get_tokens(code)
        save_tokens(tokens)
        return tokens['access_token'], tokens['refresh_token']

    access_token = tokens['access_token']
    refresh_token = tokens['refresh_token']

    # For simplicity, we'll refresh on API failure rather than tracking expiry
    return access_token, refresh_token

def make_api_request(endpoint, access_token, refresh_token=None, api_base=None):
    """Make a GET request to the API, refreshing token if necessary."""
    if api_base is None:
        api_base = f'https://{API_DOMAIN}/app/{PORTAL}/api/v3'
    headers = {
        'Authorization': f"Zoho-oauthtoken {access_token}",
        'Accept': 'application/vnd.manageengine.sdp.v3+json'
    }
    url = f"{api_base}/{endpoint}"
    response = requests.get(url, headers=headers)
    
    if response.status_code == 401:
        if not refresh_token:
            tokens = load_tokens()
            refresh_token = tokens['refresh_token']
        print("Access token expired. Refreshing...")
        new_tokens = refresh_access_token(refresh_token)
        save_tokens(new_tokens)
        access_token = new_tokens['access_token']
        headers['Authorization'] = f"Zoho-oauthtoken {access_token}"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
    
    response.raise_for_status()
    return response.json()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='OAuth Client for ServiceDesk Plus OnDemand')
    parser.add_argument('-p', '--portal', help='Portal ID to override config')
    parser.add_argument('-r', '--requestid', help='Specific Request ID to fetch (otherwise fetches list)')
    args = parser.parse_args()
    
    # Override portal if provided
    current_portal = args.portal if args.portal else PORTAL
    api_base = f'https://{API_DOMAIN}/app/{current_portal}/api/v3'
    
    # Determine endpoint
    endpoint = 'requests'
    if args.requestid:
        endpoint = f'requests/{args.requestid}'
    
    # Get valid access token
    access_token, refresh_token = get_valid_access_token()
    
    # Make API request
    try:
        requests_data = make_api_request(endpoint, access_token, refresh_token, api_base)
        print("API Response:")
        print(json.dumps(requests_data, indent=2))
    except requests.exceptions.RequestException as e:
        print(f"Error making API request: {e}")