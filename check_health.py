import httpx

response = httpx.get("http://localhost:8765/health")
print(response.json())
