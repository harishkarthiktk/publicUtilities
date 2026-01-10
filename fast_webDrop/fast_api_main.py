from fastapi import FastAPI, Request, UploadFile, File, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, Response
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from datetime import datetime
from pydantic import BaseModel
import json
import os
import csv
import base64
from io import StringIO
from authService import AuthManager, AuthConfig
from authService.logger import setup_logger, AuthLogger

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Create logs directory if it doesn't exist
LOGS_DIR = "logs"
if not os.path.exists(LOGS_DIR):
    os.makedirs(LOGS_DIR)

# Initialize authentication with file logging
logger = setup_logger(
    name="AuthManager",
    log_file=os.path.join(LOGS_DIR, "auth.log"),
    level="INFO",
    max_bytes=5242880,  # 5MB
    backup_count=5
)
auth_logger = AuthLogger(logger)
auth_config = AuthConfig(yaml_file='users.yaml', use_env_vars=False)
auth_manager = AuthManager(auth_config, logger=auth_logger)

# Simple file-based storage
LINKS_FILE = "links.json"

def load_links():
    if os.path.exists(LINKS_FILE):
        with open(LINKS_FILE, 'r') as f:
            return json.load(f)
    return []

def save_links(links):
    with open(LINKS_FILE, 'w') as f:
        json.dump(links, f)

class Link(BaseModel):
    url: str

class DeleteLink(BaseModel):
    url: str

class UpdateCategory(BaseModel):
    url: str
    category: str

async def verify_auth(request: Request):
    """Verify HTTP Basic Auth credentials using authService."""
    auth_header = request.headers.get('Authorization', '')

    if not auth_header:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )

    result = auth_manager.verify_basic_auth_header(
        auth_header,
        ip_address=request.client.host
    )
    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=result.message
        )
    return result.user

@app.get("/favicon.svg")
async def favicon():
    svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
        <rect width="100" height="100" fill="#4A9FD8" rx="20"/>
        <path d="M50 20 L65 55 L50 55 L70 80 L30 50 L50 50 Z" fill="white"/>
    </svg>"""
    return Response(content=svg, media_type="image/svg+xml")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    links = load_links()
    return templates.TemplateResponse("index.html", {
        "request": request,
        "links": links
    })

@app.post("/add-link")
async def add_link(request: Request, link: Link, user = Depends(verify_auth)):
    links = load_links()
    client_ip = request.client.host
    timestamp = datetime.now().isoformat()
    # Check for duplicate
    if any(l["url"] == link.url for l in links):
        return {"status": "duplicate"}
    links.append({"url": link.url, "ip": client_ip, "timestamp": timestamp, "category": "working"})
    save_links(links)
    return {"status": "success"}

@app.post("/delete-link")
async def delete_link(link: DeleteLink, user = Depends(verify_auth)):
    links = load_links()
    links = [l for l in links if l["url"] != link.url]
    save_links(links)
    return {"status": "success"}

@app.post("/update-category")
async def update_category(data: UpdateCategory, user = Depends(verify_auth)):
    links = load_links()
    for link in links:
        if link["url"] == data.url:
            link["category"] = data.category
            break
    save_links(links)
    return {"status": "success"}

@app.get("/export-json")
async def export_json(user = Depends(verify_auth)):
    links = load_links()
    content = json.dumps(links, indent=2)
    return Response(content=content, media_type="application/json", headers={"Content-Disposition": f"attachment; filename=links.json"})

@app.get("/export-csv")
async def export_csv(user = Depends(verify_auth)):
    links = load_links()
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["url", "timestamp", "ip", "category"])
    for link in links:
        writer.writerow([link["url"], link["timestamp"], link["ip"], link.get("category", "working")])
    return Response(content=output.getvalue(), media_type="text/csv", headers={"Content-Disposition": f"attachment; filename=links.csv"})

@app.get("/export-html")
async def export_html(user = Depends(verify_auth)):
    links = load_links()
    html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Exported Links</title>
</head>
<body>
    <h1>FastWebDrop Links</h1>
    <ul>"""
    for link in links:
        html += f"<li><a href='{link['url']}' target='_blank'>{link['url']}</a></li>"
    html += """    </ul>
</body>
</html>"""
    return Response(content=html, media_type="text/html", headers={"Content-Disposition": f"attachment; filename=links.html"})

@app.post("/import-links")
async def import_links(file: UploadFile = File(...), user = Depends(verify_auth)):
    if not file.filename:
        return {"status": "error", "message": "No file provided"}
    
    content = await file.read()
    content_str = content.decode('utf-8')
    links = load_links()
    added = 0
    
    try:
        if file.filename.endswith('.json'):
            new_links = json.loads(content_str)
            for nl in new_links:
                if "url" in nl and nl["url"] not in [l["url"] for l in links]:
                    nl["timestamp"] = nl.get("timestamp", datetime.now().isoformat())
                    nl["ip"] = nl.get("ip", "imported")
                    nl["category"] = nl.get("category", "working")
                    links.append(nl)
                    added += 1
        elif file.filename.endswith('.csv'):
            reader = csv.DictReader(StringIO(content_str))
            for row in reader:
                url = row.get("url", "").strip()
                if url and url not in [l["url"] for l in links]:
                    timestamp = row.get("timestamp", datetime.now().isoformat())
                    ip = row.get("ip", "imported")
                    category = row.get("category", "working")
                    links.append({"url": url, "timestamp": timestamp, "ip": ip, "category": category})
                    added += 1
        else:
            return {"status": "error", "message": "Unsupported file format. Use JSON or CSV."}
        
        save_links(links)
        return {"status": "success", "added": added}
    except Exception as e:
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
