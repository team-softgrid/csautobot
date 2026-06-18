import subprocess
import time
import sys
import os
import requests
from pathlib import Path

# Setup python path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

def test_servers():
    sys.stdout.reconfigure(encoding='utf-8')
    print("=== Starting API and Frontend Servers for Verification ===")
    
    # 1. Start FastAPI backend (port 8000)
    print("Launching FastAPI backend server...")
    backend_proc = subprocess.Popen(
        [sys.executable, "csautobot/main.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd=str(HERE.parent)
    )
    
    # 2. Start Streamlit frontend (port 8501)
    print("Launching Streamlit frontend server...")
    # Add flags to run headlessly and bypass telemetry
    streamlit_proc = subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", "csautobot/streamlit_app.py", 
         "--server.port", "8501", "--server.headless", "true", "--browser.gatherUsageStats", "false"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd=str(HERE.parent)
    )
    
    # Give the servers time to boot up
    print("Waiting 6 seconds for servers to start and bind ports...")
    time.sleep(6)
    
    success = True
    try:
        # Test 1: Verify FastAPI server is online
        print("\n--- Test 1: Verifying FastAPI Root Endpoint ---")
        res_root = requests.get("http://localhost:8000/", timeout=5)
        print(f"Status Code: {res_root.status_code}")
        print(f"Response JSON: {res_root.json()}")
        assert res_root.status_code == 200, "FastAPI backend root failed"
        
        # Test 2: Verify AI Quotation API Draft Endpoint
        print("\n--- Test 2: Verifying AI Quotation Generation API Endpoint ---")
        payload = {
            "query": "급속 충전기 케이블 꽂자마자 충전 완료 뜸",
            "charger_type": "급속"
        }
        res_draft = requests.post("http://localhost:8000/api/v1/quotation/draft", json=payload, timeout=15)
        print(f"Status Code: {res_draft.status_code}")
        draft_json = res_draft.json()
        print("Response JSON Preview:")
        print(f"  - 증상 요약: {draft_json.get('symptom_summary')}")
        print(f"  - 예상 원인: {draft_json.get('likely_cause')}")
        print(f"  - 부품 수: {len(draft_json.get('parts', []))}")
        for p in draft_json.get('parts', []):
            print(f"    * {p['part_name']} ({p['spec']}) - 단가: {p['unit_price']:,} 원, 수량: {p['qty']}")
        print(f"  - 공급가액: {draft_json.get('supply_value'):,} 원")
        print(f"  - 부가세: {draft_json.get('vat'):,} 원")
        print(f"  - 합계금액: {draft_json.get('total_amount'):,} 원")
        
        assert res_draft.status_code == 200, "AI Quotation API failed"
        assert draft_json.get("supply_value") > 0, "Quotation should have non-zero value"
        
        # Test 3: Verify Streamlit HTML rendering
        print("\n--- Test 3: Verifying Streamlit Web Server HTML rendering ---")
        res_st = requests.get("http://localhost:8501/", timeout=5)
        print(f"Status Code: {res_st.status_code}")
        html_sample = res_st.text[:200].replace("\n", " ").strip()
        print(f"HTML Response Head: {html_sample}...")
        assert res_st.status_code == 200, "Streamlit web server failed"
        assert "<html" in res_st.text.lower() or "doctype html" in res_st.text.lower(), "Response is not HTML"
        
        print("\n🎉 All server rendering and HTTP verification tests passed successfully!")
        
    except Exception as e:
        print(f"\n❌ Verification Test Failed: {e}")
        success = False
    finally:
        # Clean up background processes
        print("\nTerminating background servers...")
        backend_proc.terminate()
        streamlit_proc.terminate()
        try:
            backend_proc.wait(timeout=3)
            streamlit_proc.wait(timeout=3)
            print("Background servers terminated successfully.")
        except subprocess.TimeoutExpired:
            print("Force killing servers...")
            backend_proc.kill()
            streamlit_proc.kill()
            
    if not success:
        sys.exit(1)

if __name__ == '__main__':
    test_servers()
