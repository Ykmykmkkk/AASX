#!/usr/bin/env python3
"""
Goal 3 Simple Test - AAS 서버가 데이터를 찾지 못해도 기본 데이터로 작동하는지 확인
"""
import requests
import json

def test_goal3_with_fallback():
    print("=" * 60)
    print("🧪 Goal 3: Production Time Prediction - Fallback Test")
    print("=" * 60)
    
    # API endpoint
    url = "http://localhost:80/execute-goal"
    
    # Test data
    payload = {
        "goal": "predict_first_completion_time",
        "product_id": "P1", 
        "quantity": 100
    }
    
    print(f"\n📤 Request:")
    print(json.dumps(payload, indent=2))
    
    try:
        # Send request
        response = requests.post(url, json=payload, timeout=30)
        
        print(f"\n📥 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("\n✅ SUCCESS! API responded with:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            
            # Check if result contains expected fields
            if "result" in result:
                res = result["result"]
                if isinstance(res, dict):
                    if "predicted_completion_time" in res:
                        print(f"\n🎯 Predicted Time: {res['predicted_completion_time']}")
                        print(f"📊 Confidence: {res.get('confidence', 'N/A')}")
                        print(f"🏭 Simulator: {res.get('simulator_type', 'N/A')}")
                        print("\n✅ Goal 3 is working with fallback data!")
                    else:
                        print("\n⚠️ Result doesn't contain predicted_completion_time")
                else:
                    print(f"\n⚠️ Result is not a dict: {type(res)}")
        elif response.status_code == 502:
            print("\n❌ 502 Error - AAS Server Communication Failed")
            print("This is expected if process_specification:all doesn't exist")
            print("But the system should use fallback data...")
            print(f"\nError details: {response.json()}")
        else:
            print(f"\n❌ Unexpected status code: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.Timeout:
        print("\n⏱️ Request timed out (30s) - simulator may be running")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    test_goal3_with_fallback()