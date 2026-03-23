from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Any
import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")  # anon key
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", SUPABASE_KEY)  # service role key
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "Iloveyouprim214")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
# Admin client uses service role key — bypasses RLS
supabase_admin: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

app = FastAPI(title="Cammy Digitals API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# ── Auth helper ──────────────────────────────────────────
def verify_admin(x_admin_token: str = Header(None)):
    if not x_admin_token or x_admin_token != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return True

# ── Pydantic models ──────────────────────────────────────
class Product(BaseModel):
    id: Optional[str] = None
    name: str
    cat: str
    subcat: Optional[str] = None
    price: float
    stock: int = 0
    desc: Optional[str] = None
    fb: Optional[str] = None
    tg: Optional[str] = None
    avail: bool = True

class Boost(BaseModel):
    id: Optional[str] = None
    name: str
    platform: str
    type: str
    price: float
    slots: int = 0
    desc: Optional[str] = None
    fb: Optional[str] = None
    tg: Optional[str] = None
    avail: bool = True

class Load(BaseModel):
    id: Optional[str] = None
    telco: str
    promo: str
    amount: float
    orig: float
    price: float
    validity: int = 1
    slots: int = 0
    desc: Optional[str] = None
    fb: Optional[str] = None
    tg: Optional[str] = None
    avail: bool = True

class User(BaseModel):
    username: str
    name: Optional[str] = None
    pass_hash: Optional[str] = None
    joined: Optional[str] = None

class Config(BaseModel):
    fb: Optional[str] = None
    tg: Optional[str] = None
    banner: Optional[str] = None
    store_open: bool = True
    closed_msg: Optional[str] = None
    theme: Optional[str] = "terracotta"

# ── PRODUCTS ─────────────────────────────────────────────
@app.get("/api/products")
def get_products():
    res = supabase.table("products").select("*").order("created_at").execute()
    return res.data

@app.post("/api/products")
def create_product(p: Product, admin=Depends(verify_admin)):
    import time
    p.id = p.id or "p" + str(int(time.time() * 1000))
    res = supabase.table("products").insert(p.dict()).execute()
    return res.data[0]

@app.put("/api/products/{pid}")
def update_product(pid: str, p: Product, admin=Depends(verify_admin)):
    data = {k: v for k, v in p.dict().items() if k != 'created_at'}
    data["id"] = pid
    res = supabase.table("products").upsert(data).execute()
    return res.data[0]

@app.delete("/api/products/{pid}")
def delete_product(pid: str, admin=Depends(verify_admin)):
    supabase.table("products").delete().eq("id", pid).execute()
    return {"ok": True}

# ── BOOSTS ───────────────────────────────────────────────
@app.get("/api/boosts")
def get_boosts():
    res = supabase.table("boosts").select("*").order("created_at").execute()
    return res.data

@app.post("/api/boosts")
def create_boost(b: Boost, admin=Depends(verify_admin)):
    import time
    b.id = b.id or "b" + str(int(time.time() * 1000))
    res = supabase.table("boosts").insert(b.dict()).execute()
    return res.data[0]

@app.put("/api/boosts/{bid}")
def update_boost(bid: str, b: Boost, admin=Depends(verify_admin)):
    data = {k: v for k, v in b.dict().items() if k != 'created_at'}
    data["id"] = bid
    res = supabase.table("boosts").upsert(data).execute()
    return res.data[0]

@app.delete("/api/boosts/{bid}")
def delete_boost(bid: str, admin=Depends(verify_admin)):
    supabase.table("boosts").delete().eq("id", bid).execute()
    return {"ok": True}

# ── LOADS ────────────────────────────────────────────────
@app.get("/api/loads")
def get_loads():
    res = supabase.table("loads").select("*").order("created_at").execute()
    return res.data

@app.post("/api/loads")
def create_load(l: Load, admin=Depends(verify_admin)):
    import time
    l.id = l.id or "l" + str(int(time.time() * 1000))
    res = supabase.table("loads").insert(l.dict()).execute()
    return res.data[0]

@app.put("/api/loads/{lid}")
def update_load(lid: str, l: Load, admin=Depends(verify_admin)):
    data = {k: v for k, v in l.dict().items() if k != 'created_at'}
    data["id"] = lid
    res = supabase.table("loads").upsert(data).execute()
    return res.data[0]

@app.delete("/api/loads/{lid}")
def delete_load(lid: str, admin=Depends(verify_admin)):
    supabase.table("loads").delete().eq("id", lid).execute()
    return {"ok": True}

# ── USERS ────────────────────────────────────────────────
@app.get("/api/users")
def get_users():
    res = supabase_admin.table("users").select("id,username,name,joined,login_count,last_login").execute()
    return res.data

@app.post("/api/users/register")
def register_user(body: dict):
    username = body.get("username","").strip()
    password = body.get("password","")
    if not username or not password:
        raise HTTPException(status_code=400, detail="Username and password required")
    # Check existing
    existing = supabase_admin.table("users").select("id").eq("username", username).execute()
    if existing.data:
        raise HTTPException(status_code=409, detail="Username already taken")
    import hashlib, time
    pass_hash = hashlib.sha256(password.encode()).hexdigest()
    from datetime import date
    user = {
        "username": username,
        "name": username,
        "pass_hash": pass_hash,
        "joined": str(date.today()),
        "login_count": 0
    }
    res = supabase_admin.table("users").insert(user).execute()
    u = res.data[0]
    return {"ok": True, "user": {"username": u["username"], "name": u["name"], "joined": u["joined"]}}

@app.post("/api/users/login")
def login_user(body: dict):
    username = body.get("username","").strip()
    password = body.get("password","")
    import hashlib
    pass_hash = hashlib.sha256(password.encode()).hexdigest()
    res = supabase_admin.table("users").select("*").eq("username", username).eq("pass_hash", pass_hash).execute()
    if not res.data:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    u = res.data[0]
    from datetime import datetime
    supabase_admin.table("users").update({
        "login_count": (u.get("login_count") or 0) + 1,
        "last_login": str(datetime.now())
    }).eq("id", u["id"]).execute()
    return {"ok": True, "user": {"username": u["username"], "name": u["name"], "joined": u["joined"]}}

@app.put("/api/users/{username}/password")
def change_password(username: str, body: dict):
    old_pw = body.get("old_password","")
    new_pw = body.get("new_password","")
    import hashlib
    new_hash = hashlib.sha256(new_pw.encode()).hexdigest()
    # Allow reset flow (old_password == '__reset__') — skip old password check
    if old_pw != '__reset__':
        old_hash = hashlib.sha256(old_pw.encode()).hexdigest()
        res = supabase_admin.table("users").select("id").eq("username", username).eq("pass_hash", old_hash).execute()
        if not res.data:
            raise HTTPException(status_code=401, detail="Current password is incorrect")
    supabase_admin.table("users").update({"pass_hash": new_hash}).eq("username", username).execute()
    return {"ok": True}

@app.delete("/api/users/{username}")
def delete_user(username: str, admin=Depends(verify_admin)):
    supabase_admin.table("users").delete().eq("username", username).execute()
    return {"ok": True}

# ── CONFIG ───────────────────────────────────────────────
@app.get("/api/config")
def get_config():
    res = supabase.table("config").select("*").eq("id", 1).execute()
    if res.data:
        return res.data[0]
    return {"id": 1, "fb": "", "tg": "", "banner": "", "store_open": True, "closed_msg": "", "theme": "terracotta"}

@app.put("/api/config")
def update_config(cfg: dict, admin=Depends(verify_admin)):
    existing = supabase.table("config").select("id").eq("id", 1).execute()
    if existing.data:
        res = supabase.table("config").update(cfg).eq("id", 1).execute()
    else:
        cfg["id"] = 1
        res = supabase.table("config").insert(cfg).execute()
    return res.data[0]

# Public endpoint — no admin auth needed, only updates theme
@app.put("/api/config/theme")
def update_theme(body: dict):
    theme = body.get("theme", "terracotta")
    existing = supabase.table("config").select("id").eq("id", 1).execute()
    if existing.data:
        res = supabase.table("config").update({"theme": theme}).eq("id", 1).execute()
    else:
        res = supabase.table("config").insert({"id": 1, "theme": theme}).execute()
    return res.data[0]

# ── WISHLIST ─────────────────────────────────────────────
@app.get("/api/wishlist/{username}")
def get_wishlist(username: str):
    res = supabase.table("wishlists").select("items").eq("username", username).execute()
    if res.data:
        return res.data[0].get("items", [])
    return []

@app.put("/api/wishlist/{username}")
def save_wishlist(username: str, body: dict):
    items = body.get("items", [])
    existing = supabase.table("wishlists").select("id").eq("username", username).execute()
    if existing.data:
        supabase.table("wishlists").update({"items": items}).eq("username", username).execute()
    else:
        supabase.table("wishlists").insert({"username": username, "items": items}).execute()
    return {"ok": True}

# ── SERVE FRONTEND ───────────────────────────────────────
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def serve_index():
    return FileResponse("static/index.html")

@app.get("/{full_path:path}")
def catch_all(full_path: str):
    return FileResponse("static/index.html")
