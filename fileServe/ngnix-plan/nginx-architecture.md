# Nginx + Flask Architecture for File Server

This diagram illustrates the request flow for a file download in the Flask File Server project, integrating Nginx as a reverse proxy with X-Accel-Redirect for efficient large-file serving on high-speed LANs. Authentication is handled by Flask's Basic Auth (from `core_auth.py` using YAML/env users), while Nginx offloads the actual file transfer from `serveFolder`.

Key Components:
- **Client**: Browser or curl with Basic Auth credentials.
- **Nginx**: Front-end proxy; handles static serving via internal location `/internal-files/`.
- **Flask App**: Runs on Gunicorn (e.g., port 8000); uses `routes.py` for endpoints like `/files/<filename>`, `core_auth.py` for auth validation.
- **serveFolder**: Disk storage for files (e.g., large MKVs); aliased in Nginx.

## Sequence Diagram: Authenticated File Download Flow

```mermaid
sequenceDiagram
    participant C as Client (Browser/cURL)
    participant N as Nginx (Proxy + Static Serve)
    participant F as Flask App (routes.py + core_auth.py)
    participant D as Disk (serveFolder)

    Note over C,N: Request: GET /files/largefile.mkv<br/>with Authorization: Basic creds

    C->>+N: HTTP Request + Auth Header
    N->>+F: Proxy to http://127.0.0.1:8000/files/largefile.mkv<br/>(passes Auth header)
    
    F->>F: @auth.login_required (core_auth.py)<br/>Validate YAML/env users
    alt Invalid Credentials
        F-->>N: 401 Unauthorized
        N-->>C: 401 (re-prompt auth)
        Note over C: Retry with valid creds
    else Valid Auth
        F->>F: Path validation (routes.py: serve_file)<br/>Resolve filepath in serveFolder
        alt Invalid Path/File
            F-->>N: 403/404/500 Error
            N-->>C: Error Response
        else Valid Path
            F-->>N: 200 OK + X-Accel-Redirect: /internal-files/largefile.mkv<br/>+ Content-Type/Disposition/Length headers
            N->>+D: Direct read (sendfile on, alias to serveFolder)
            D-->>-N: File stream (optimized I/O)
            N-->>C: File stream + Flask headers<br/>(high-speed LAN transfer)
        end
    end
    deactivate F
    deactivate N
    
    Note over N,D: Nginx bypasses Flask for data<br/>Flask only handles logic/auth
```

## High-Level Architecture Diagram

```mermaid
graph TD
    subgraph Client["Client Side"]
        C["Client<br/>- Browser<br/>- cURL/wget"]
    end
    
    subgraph Nginx["Nginx Layer (Port 80/8000)"]
        N["Reverse Proxy<br/>- Proxy / to Flask<br/>- Internal /internal-files/<br/>- sendfile on<br/>- tcp_nopush/nodelay"]
    end
    
    subgraph Flask["Flask App Layer (Gunicorn, Port 8000)"]
        FA["Flask App (app.py)<br/>- Blueprint: routes.py<br/>- Auth: core_auth.py (YAML/env)<br/>- Templates: browser.html<br/>- Config: serveFolder, temp_zips"]
    end
    
    subgraph Storage["Storage Layer"]
        D["Disk: serveFolder<br/>- Files (MKVs, images)<br/>- Uploads via /upload<br/>- Zips via /download-folder"]
        T["temp_zips<br/>- Temporary ZIPs for folders"]
    end
    
    C --> N
    N --> FA
    FA --> N
    N --> D
    FA -.-> T
    FA -.-> D
    
    style N fill:#f9f,stroke:#333,stroke-width:2px
    style FA fill:#bbf,stroke:#333,stroke-width:2px
    style D fill:#dfd,stroke:#333,stroke-width:2px
```

## Explanation
- **Entry Point**: All traffic hits Nginx first (for load balancing, SSL termination if added).
- **Dynamic Routes** (e.g., `/` listing, `/upload`): Proxied to Flask; auth enforced there.
- **File Download Routes** (e.g., `/files/<path>`): Proxied to Flask for auth/path checks; Flask redirects to Nginx internal path.
- **Static Serving**: Nginx directly reads from `serveFolder` (no Python overhead for large files).
- **Security**: Internal paths are protected (`internal;` directive); auth via Flask ensures only valid users trigger serving.
- **Performance**: On LAN, expect >100MB/s for large files (vs. <10MB/s pure Flask) due to Nginx's kernel sendfile.
- **Deployment**: Use Gunicorn for Flask concurrency; Nginx config as provided earlier.

This setup preserves your project's modularity (`routes.py`, `core_auth.py`) while optimizing for speed. For implementation, switch to code mode to apply changes.
