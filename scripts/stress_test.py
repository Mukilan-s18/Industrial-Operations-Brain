"""
Day 7: Stress Test
Rapidly sends 20 concurrent queries to the FastAPI backend to ensure ChromaDB thread safety.
Make sure `uvicorn app:app` is running before executing this.
"""
import asyncio
import httpx
import time

async def fetch_query(client, idx):
    payload = {"query": "What is the pressure limit?", "mode": "brief"}
    try:
        response = await client.post("http://127.0.0.1:8000/chat", json=payload, timeout=30.0)
        return response.status_code == 200
    except Exception as e:
        print(f"Request {idx} failed: {e}")
        return False

async def main():
    print("Starting Day 7 Stress Test (20 rapid queries)...")
    start = time.time()
    
    async with httpx.AsyncClient() as client:
        tasks = [fetch_query(client, i) for i in range(20)]
        results = await asyncio.gather(*tasks)
        
    success_count = sum(results)
    print(f"Test completed in {time.time() - start:.2f} seconds.")
    print(f"Successful requests: {success_count}/20")
    
    if success_count == 20:
        print("PASS: System is stable under load.")
    else:
        print("FAIL: Some requests failed.")

if __name__ == "__main__":
    asyncio.run(main())
