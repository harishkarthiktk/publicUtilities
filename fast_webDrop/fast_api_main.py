from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi import Request
from fastapi.staticfiles import StaticFiles
from datetime import datetime
from pydantic import BaseModel
import json
import os

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

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


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    links = load_links()
    return templates.TemplateResponse("index.html", {
        "request": request,
        "links": links
    })

@app.post("/add-link")
async def add_link(request: Request, link: Link):
    links = load_links()
    client_ip = request.client.host
    timestamp = datetime.now().isoformat()
    links.append({"url": link.url, "ip": client_ip, "timestamp": timestamp})
    save_links(links)
    return {"status": "success"}

@app.post("/delete-link")
async def delete_link(link: DeleteLink):
    links = load_links()
    links = [l for l in links if l["url"] != link.url]
    save_links(links)
    return {"status": "success"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
