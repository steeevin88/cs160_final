from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.middleware import SlowAPIMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response, JSONResponse
import requests
import threading
import time
import psutil
import logging
import json
from datetime import datetime
from typing import List, Dict
from collections import deque
import multiprocessing
import random

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

attack_processes: List[multiprocessing.Process] = []
metrics_history: deque[Dict[str, float]] = deque(maxlen=100)
logs_history: List[Dict[str, str]] = []  
blacklisted_ips: set[str] = set()
logged_blacklisted_ips: set[str] = set()
is_attacking = False

app = FastAPI()

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(SlowAPIMiddleware)

def log_event(event_type: str, message: str):
    log_entry = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "type": event_type,
        "message": message
    }
    logs_history.append(log_entry)
    logger.info(f"[{event_type}] {message}")

def clear_blacklist():
    global blacklisted_ips
    while True:
        time.sleep(10) # clear blacklist every 10 seconds...
        blacklisted_ips.clear()
        log_event("info", "Blacklist cleared")

def blacklist_ip(ip: str):
    global blacklisted_ips
    if ip not in blacklisted_ips:
        logger.info(f"Blacklisting IP: {ip}")
        blacklisted_ips.add(ip)

@app.get("/metrics")
async def get_metrics():
    return collect_metrics()

@app.get("/logs")
async def get_logs():
    return logs_history

@app.get("/limited")
@limiter.limit("5/minute")
async def limited_endpoint(request: Request):
    client_ip = get_remote_address(request)
    log_event("info", f"Rate-limited endpoint accessed successfully from {client_ip}")
    return {"message": "Request successful", "status": "success"}

@app.get("/open")
async def open_endpoint(request: Request):
    client_ip = get_remote_address(request)
    log_event("info", f"Open endpoint accessed from {client_ip}")
    return {"message": "This endpoint has no rate limiting."}

@app.post("/configure")
async def configure_attack(request: Request, background_tasks: BackgroundTasks):
    global is_attacking, attack_processes
    
    await stop_attack()
    
    try:
        data = await request.json()
        num_threads = data.get("NUM_THREADS", 10)
        rate_limit = data.get("RATE_LIMIT", 5)
        attack_mode = data.get("ATTACK_MODE", "single")
        target_endpoint = data.get("TARGET_ENDPOINT", "/limited")
        is_blacklisting = data.get("IS_BLACKLISTING", False)
        
        attack_metrics.reset()
        logging.debug(f"Debug: rate limiting rate: {rate_limit}/minute")
        
        is_attacking = True
        target_url = f"http://127.0.0.1:8000{target_endpoint}"
        
        log_event("info", f"Starting {attack_mode} attack with {num_threads} threads against {target_url}")
        
        if attack_mode == "single":
            for i in range(num_threads):
                thread = threading.Thread(
                    target=single_attack,
                    args=(target_url, is_blacklisting)
                )
                attack_processes.append(thread)
                thread.start()
                log_event("info", f"Started attack thread {i+1}/{num_threads}")
        else:
            attack_processes.extend(
                distributed_attack(target_url, num_threads, is_blacklisting)
            )
        
        metrics_thread = threading.Thread(target=update_metrics)
        metrics_thread.daemon = True
        metrics_thread.start()
        log_event("info", "Started metrics collection")
        
        return {
            "message": "Attack configured and started",
            "mode": attack_mode,
            "threads": num_threads,
            "rate_limit": rate_limit,
            "target_url": target_url
        }
    except Exception as e:
        log_event("error", f"Error configuring attack: {str(e)}")
        return JSONResponse(
            {"error": f"Failed to configure attack: {str(e)}"},
            status_code=500
        )

@app.post("/stop")
async def stop_attack():
    global is_attacking, attack_processes
    
    if is_attacking:
        is_attacking = False
        for thread in attack_processes:
            thread.join()
        attack_processes.clear()
        
        final_metrics = attack_metrics.get_metrics()
        log_event("info", f"Attack stopped. Final metrics: "
                        f"Success Rate: {final_metrics['successRate']:.1f}%, "
                        f"Rate Limited: {final_metrics['rateLimitedRate']:.1f}%, "
                        f"Failures: {final_metrics['failureRate']:.1f}%")
        
        attack_metrics.reset()
    
    return {"message": "Attack stopped"}

@app.exception_handler(Exception)
async def custom_rate_limit_exceeded_handler(request: Request, exc: Exception):
    if "Rate limit exceeded" in str(exc):
        path = request.url.path
        if path == "/metrics":
            return await get_metrics()
        elif path == "/logs":
            return await get_logs()
        return JSONResponse(
            {"error": "Rate limit exceeded"},
            status_code=429
        )
    raise exc

class AttackMetrics:
    def __init__(self):
        self.request_times = deque(maxlen=100)
        self.request_results = deque(maxlen=100)
        self.start_time = time.time()
        self.total_requests = 0
        self.successful_requests = 0
        self.rate_limited_requests = 0
        self.failed_requests = 0
        self.last_update = time.time()
        self.current_status = "running"  
        
    def record_request(self, response_time: float, status_code: int):
        current_time = time.time()
        self.request_times.append(response_time)
        self.request_results.append(status_code)
        self.total_requests += 1
        self.last_update = current_time
        
        if status_code == 200:
            self.successful_requests += 1
            self.current_status = "running"
        elif status_code == 429:
            self.rate_limited_requests += 1
            self.current_status = "rate_limited"
        else:
            self.failed_requests += 1
            
    def get_metrics(self):
        current_time = time.time()
        time_since_last = current_time - self.last_update
        
        if time_since_last > 1 and self.current_status == "rate_limited":
            self.record_request(1000, 429) 
            
        if not self.request_times:
            return {
                "avgResponseTime": 0,
                "successRate": 0,
                "rateLimitedRate": 0,
                "failureRate": 0,
                "requestsPerSecond": 0,
                "status": "stopped"
            }
        
        window_size = 10  
        window_start = current_time - window_size
        recent_total = 0
        recent_success = 0
        recent_rate_limited = 0
        recent_failed = 0
        
        for i, result in enumerate(self.request_results):
            if i >= len(self.request_times):
                break
            request_time = current_time - (len(self.request_results) - i) * 0.1 
            if request_time >= window_start:
                recent_total += 1
                if result == 200:
                    recent_success += 1
                elif result == 429:
                    recent_rate_limited += 1
                else:
                    recent_failed += 1
        
        recent_total = max(1, recent_total)  
        
        elapsed_time = min(window_size, current_time - self.start_time)
        requests_per_second = recent_total / elapsed_time
        
        recent_times = list(self.request_times)[-int(requests_per_second * 2 or 1):]
        avg_response_time = sum(recent_times) / len(recent_times) if recent_times else 0
            
        return {
            "avgResponseTime": avg_response_time,
            "successRate": (recent_success / recent_total) * 100,
            "rateLimitedRate": (recent_rate_limited / recent_total) * 100,
            "failureRate": (recent_failed / recent_total) * 100,
            "requestsPerSecond": requests_per_second,
            "status": self.current_status
        }
        
    def reset(self):
        self.__init__()

attack_metrics = AttackMetrics()

def collect_metrics() -> Dict:
    metrics = attack_metrics.get_metrics()
    return {
        "responseTime": metrics["avgResponseTime"],
        "successRate": metrics["successRate"],
        "cpuUsage": psutil.Process().cpu_percent(interval=0.5),
        "activeAttackers": len(attack_processes),
        "rateLimitedRate": metrics["rateLimitedRate"],
        "failureRate": metrics["failureRate"],
        "requestsPerSecond": metrics["requestsPerSecond"]
    }

def update_metrics():
    last_metrics_time = time.time()
    while is_attacking:
        try:
            current_time = time.time()
            if current_time - last_metrics_time >= 1.0:
                metrics = collect_metrics()
                metrics_history.append(metrics)
                last_metrics_time = current_time
        except Exception as e:
            log_event("error", f"Error updating metrics: {str(e)}")
        finally:
            time.sleep(0.1) 

def single_attack(target_url: str, is_blacklisting: bool = False):
    global blacklisted_ips

    logging.debug(f"Starting single attack thread against {target_url}")
    log_event("info", f"Starting single attack thread against {target_url}")
    consecutive_429s = 0
    ip = f"192.168.1.{random.randint(1, 255)}"
    
    while is_attacking:
        try:
            if is_blacklisting and ip in blacklisted_ips and ip not in logged_blacklisted_ips:
                logged_blacklisted_ips.add(ip)
                log_event("warning", f"Rate-limited IP {ip} has been blacklisted.")
                continue

            start_time = time.time()
            response = requests.get(
                    target_url,
                    headers={"X-Forwarded-For": ip}
                )
            response_time = (time.time() - start_time) * 1000  
            status = response.status_code
            
            attack_metrics.record_request(response_time, status)
            
            if status == 429:
                consecutive_429s += 1

                if is_blacklisting:
                    blacklist_ip(ip)

                backoff = min(consecutive_429s * 0.1, 1.0)  
                log_event("warning", 
                    f"Rate limited ({consecutive_429s} in a row) - "
                    f"Response: {response_time:.0f}ms, "
                    f"Backing off: {backoff:.1f}s"
                )
                time.sleep(backoff)
            else:
                logging.debug(f"Request successful {status}")
                consecutive_429s = 0
                if status == 200:
                    log_event("info", 
                        f"Request successful - "
                        f"Response: {response_time:.0f}ms"
                    )
                else:
                    log_event("error", 
                        f"Request failed ({status}) - "
                        f"Response: {response_time:.0f}ms"
                    )
                time.sleep(0.1)
                
        except requests.exceptions.RequestException as e:
            log_event("error", f"Request failed: {str(e)}")
            attack_metrics.record_request(1000, 500)
            time.sleep(0.5)

def distributed_attack(target_url: str, num_nodes: int, is_blacklisting: bool = False):
    global blacklisted_ips

    def node_attack():
        node_id = random.randint(1, 1000)
        while is_attacking:
            try:
                ip = f"192.168.1.{random.randint(1, 255)}"
                if is_blacklisting and ip in blacklisted_ips and ip not in logged_blacklisted_ips:
                    logged_blacklisted_ips.add(ip)
                    log_event("warning", f"Rate-limited IP {ip} has been blacklisted.")
                    continue

                start_time = time.time()
                response = requests.get(
                    target_url,
                    headers={"X-Forwarded-For": ip}
                )
                response_time = (time.time() - start_time) * 1000
                attack_metrics.record_request(response_time, response.status_code)

                if response.status_code == 429:
                    if is_blacklisting:
                        blacklist_ip(ip)
                    log_event("warning", f"Node {node_id} (IP: {ip}) hit rate limit")
                else:
                    log_event("info", f"Node {node_id} (IP: {ip}) request successful")
            except requests.exceptions.RequestException as e:
                log_event("error", f"Node {node_id} request failed: {str(e)}")
                attack_metrics.record_request(1000, 500)
            time.sleep(random.uniform(0.1, 1.0))

    threads = []
    for _ in range(num_nodes):
        thread = threading.Thread(target=node_attack)
        threads.append(thread)
        thread.start()
    return threads

if __name__ == "__main__":
    import uvicorn
    clear_thread = threading.Thread(target=clear_blacklist, daemon=True)
    clear_thread.start()
    uvicorn.run('app:app', host="0.0.0.0", port=8000, reload=True)