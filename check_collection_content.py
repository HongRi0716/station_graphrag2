import requests
import json

API_BASE_URL = "http://localhost:8000"
USER_ID = "user5220eb7ee134ad0d"
# 使用之前日志中看到的 collection_id
COLLECTION_IDS = ["cold307b13f7b870c13", "colc8b5993e9352a49e"]

def get_collection_documents(collection_id):
    print(f"Checking collection: {collection_id}")
    url = f"{API_BASE_URL}/api/v1/collections/{collection_id}/documents"
    headers = {
        "X-User-Id": USER_ID,
        "Content-Type": "application/json"
    }
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            print(f"Total documents: {data.get('total', 0)}")
            for item in data.get('items', [])[:5]:
                print(f" - {item.get('name')} (ID: {item.get('id')})")
        else:
            print(f"Failed to get documents: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    for col_id in COLLECTION_IDS:
        get_collection_documents(col_id)
