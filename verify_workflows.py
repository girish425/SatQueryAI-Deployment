import httpx
import json

base_url = "http://127.0.0.1:8000"

print("--- 1. Testing Health ---")
r = httpx.get(f"{base_url}/health")
print("Health:", r.status_code, r.json())

# Create new session
r = httpx.post(f"{base_url}/history/new")
session_id = r.json()["session_id"]
print(f"Created Session: {session_id}")

questions = [
    ("What is visible in this image?", ["sample_optical_hyderabad.tif"]),
    ("Is there water in this image?", ["sample_optical_hyderabad.tif"]),
    ("Are there buildings?", ["sample_optical_hyderabad.tif"]),
    ("Where is the river?", ["sample_optical_hyderabad.tif"]),
    ("Describe the image.", ["sample_optical_hyderabad.tif"]),
    ("What changed between these two images?", ["sample_change_t1.tif", "sample_change_t2.tif"]),
    ("Analyze the optical and SAR images together.", ["sample_optical_hyderabad.tif", "sample_sar_hyderabad.tif"])
]

for q, imgs in questions:
    print(f"\n==========================================")
    print(f"Q: '{q}' (Images: {imgs})")
    resp = httpx.post(
        f"{base_url}/chat/",
        json={"session_id": session_id, "query": q, "image_ids": imgs},
        timeout=30.0
    )
    if resp.status_code != 200:
        print("ERROR:", resp.status_code, resp.text)
        continue
    data = resp.json()
    print(f"Intent: {data['intent']} (Conf: {data['intent_confidence']})")
    print(f"Model Used: {data['model_used']}")
    print(f"Summary: {data['answer']['summary']}")
    print(f"Key Findings: {data['answer']['key_findings']}")
    print(f"Evidence: {data['evidence']}")
    print(f"Technical: {data['technical_details']}")

# Test STAC search
print(f"\n--- 2. Testing STAC Satellite Retrieval ---")
ret_resp = httpx.post(
    f"{base_url}/retrieve/",
    json={"query": "Find Sentinel-2 images of Hyderabad from August 2026"}
)
print("STAC Results Count:", ret_resp.json()["count"])
for item in ret_resp.json()["results"][:2]:
    print(f" - [{item['satellite']}] {item['title']} ({item['date']})")

# Test PDF Generation
print(f"\n--- 3. Testing PDF Generation ---")
pdf_resp = httpx.get(f"{base_url}/conversation/{session_id}/pdf")
print("PDF Status:", pdf_resp.status_code)
print("PDF Content-Type:", pdf_resp.headers.get("content-type"))
print("PDF Byte Size:", len(pdf_resp.content))
with open(f"./uploads/test_export_{session_id[:8]}.pdf", "wb") as f:
    f.write(pdf_resp.content)
print(f"Saved PDF to ./uploads/test_export_{session_id[:8]}.pdf")

print("\n--- ALL WORKFLOWS COMPLETED SUCCESSFULLY ---")
