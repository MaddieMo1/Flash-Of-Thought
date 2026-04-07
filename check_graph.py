
import requests
import json
import time

print("Checking graph API...")
try:
    res = requests.get("http://localhost:8000/api/v1/graph", timeout=5)
    print(f"Status Code: {res.status_code}")
    if res.status_code == 200:
        data = res.json()
        nodes = data.get("nodes", [])
        
        print(f"Total nodes: {len(nodes)}")
        
        found_idea = False
        for n in nodes:
            if n.get("group") == "core_idea":
                found_idea = True
                print(f"Idea Node: ID={n['id']}")
                print(f"  Label: {n['label']}")
                print(f"  Title: {n.get('title', 'N/A')}")
                print(f"  Color: {n.get('color')}")
                
                # Verification logic
                if len(n['label']) <= 13: # 10 chars + "..."
                     print("  [PASS] Label truncated correctly (or short enough)")
                else:
                     print("  [FAIL] Label not truncated")
                     
                if n.get('title') and len(n['title']) >= len(n['label']):
                     print("  [PASS] Title (full text) is present")
                else:
                     print("  [WARN] Title might be missing or shorter than label")
                     
                if n.get('color') == "#90E0EF":
                     print("  [PASS] Color is correct")
                else:
                     print(f"  [FAIL] Color is {n.get('color')}")
                
                break # Check one is enough
        
        if not found_idea:
            print("No Idea Nodes found. Graph might be empty or only have tags/notes.")
            
    else:
        print(f"Error: {res.status_code} - {res.text}")
except Exception as e:
    print(f"Connection failed: {e}")
