
import asyncio
import aiohttp
import json

async def test_search():
    url = "http://localhost:8000/api/v1/agents/archivist/search"
    payload = {
        "query": "运维班组",
        "user_id": "user5220eb7ee134ad0d",
        "search_type": "hybrid"
    }
    
    print(f"Testing API: {url}")
    print(f"Payload: {json.dumps(payload, ensure_ascii=False)}")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, timeout=60) as response:
                print(f"Status: {response.status}")
                if response.status == 200:
                    data = await response.json()
                    print("Response:")
                    print(json.dumps(data, indent=2, ensure_ascii=False))
                else:
                    text = await response.text()
                    print(f"Error: {text}")
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    asyncio.run(test_search())
