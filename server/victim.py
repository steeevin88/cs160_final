from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.middleware import SlowAPIMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import requests
import threading
import time

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

TARGET_URL = "http://localhost:8000/limited"

def run_dos_attack(num_threads: int):
    def attack():
        try:
            response = requests.get(TARGET_URL)
            print(f"Status Code: {response.status_code}, Response: {response.text}")
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")

    threads = []
    for i in range(num_threads):
        thread = threading.Thread(target=attack)
        threads.append(thread)
        thread.start()
        time.sleep(0.01)  # stagger requests

    for thread in threads:
        thread.join()

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

@app.post("/configure")
async def configure_victim_settings(request: Request, background_tasks: BackgroundTasks):
    data = await request.json()
    num_threads = data.get("NUM_THREADS", 10)
    rate_limit_number = data.get("RATE_LIMIT", 5)
    rate_limit = f"{rate_limit_number}/minute"

    # Update server settings
    app.state.limiter = Limiter(key_func=get_remote_address, default_limits=[rate_limit])

    # Execute the DoS attack in the background
    background_tasks.add_task(run_dos_attack, num_threads)

    return {"message": "Configuration updated and DoS attack initiated", "num_threads": num_threads, "rate_limit": rate_limit}

if __name__ == "__main__":
    # Automatically start the server when running the script
    import uvicorn
    uvicorn.run('app:app', host="0.0.0.0", port=8000, reload=True)