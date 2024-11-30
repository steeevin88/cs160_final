from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.middleware import SlowAPIMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

app = FastAPI()
limiter = Limiter(key_func=get_remote_address)

# middleware
app.state.limiter = limiter
app.add_exception_handler(Exception, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# IP blacklist
blacklisted_ips = set()

class IPFilterMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        client_ip = get_remote_address(request)
        if client_ip in blacklisted_ips:
            return Response("Forbidden", status_code=403)
        response = await call_next(request)
        return response

app.add_middleware(IPFilterMiddleware)

@app.get("/limited")
@limiter.limit("5/minute")
async def limited_endpoint(request: Request):
    return {"message": "This endpoint is rate limited to 5 requests per minute."}

@app.get("/open")
async def open_endpoint(request: Request):
    return {"message": "This endpoint has no rate limiting."}

@app.post("/blacklist/{ip}")
async def blacklist_ip(ip: str, request: Request):
    blacklisted_ips.add(ip)
    return {"message": f"IP {ip} added to blacklist."}

@app.delete("/blacklist/{ip}")
async def remove_blacklist_ip(ip: str, request: Request):
    blacklisted_ips.discard(ip)
    return {"message": f"IP {ip} removed from blacklist."}