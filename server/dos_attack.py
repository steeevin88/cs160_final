import threading
import requests
import time

TARGET_URL = "http://localhost:8000/limited"
NUM_THREADS = 100

def attack():
    try:
        response = requests.get(TARGET_URL)
        print(f"Status Code: {response.status_code}, Response: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")

threads = []
for i in range(NUM_THREADS):
    thread = threading.Thread(target=attack)
    threads.append(thread)
    thread.start()
    time.sleep(0.01) # stagger requests

for thread in threads:
    thread.join()