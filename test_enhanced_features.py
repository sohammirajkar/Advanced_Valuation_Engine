#!/usr/bin/env python3
"""
Comprehensive test script for the enhanced valuation engine
Tests all new features including models, API endpoints, and caching
"""

import requests
import json
import time
import sys
from typing import Dict, Any, Optional

API_BASE = "http://localhost:8000"

def test_api_endpoint(endpoint: str, method: str = "GET", data: Optional[Dict] = None, params: Optional[Dict] = None) -> Dict[str, Any]:
    """Test an API endpoint and return results"""
    try:
        if method.upper() == "GET":
            response = requests.get(f"{API_BASE}{endpoint}", params=params)
        elif method.upper() == "POST":
            response = requests.post(f"{API_BASE}{endpoint}", json=data, params=params)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        response.raise_for_status()
        return {"success": True, "data": response.json(), "status_code": response.status_code}
    except Exception as e:
        status_code = None
        # Check if it's a requests exception with a response
        if hasattr(e, 'response') and getattr(e, 'response', None) is not None:
            response = getattr(e, 'response')
            if hasattr(response, 'status_code'):
                status_code = response.status_code
        return {"success": False, "error": str(e), "status_code": status_code}


def run_comprehensive_tests():
    """Run comprehensive tests of all new features"""
    print("🚀 Starting Enhanced Valuation Engine Tests")
    print("=" * 60)
    
    test_results = []
    
    # Test 1: Basic NPV calculation
    print("\n📊 Test 1: Basic NPV Calculation")
    result = test_api_endpoint("/valuation/npv", "POST", {
        "cash_flows": [100, 200, 300, 400, 500],
        "discount_rate": 0.1
    })
    test_results.append(("NPV Calculation", result["success"]))
    if result["success"]:
        print(f"✅ NPV = ${result['data']['npv']:.2f}")
    else:
        print(f"❌ Error: {result['error']}")
    
    # Test 2: Black-Scholes Option Pricing
    print("\n🎯 Test 2: Black-Scholes Option Pricing")
    result = test_api_endpoint("/valuation/black-scholes", "POST", {
        "S": 100, "K": 100, "T": 1.0, "r": 0.05, "sigma": 0.2, "option_type": "call"
    })
    test_results.append(("Black-Scholes Pricing", result["success"]))
    if result["success"]:
        data = result['data']
        print(f"✅ Call Option Price = ${data['option_price']:.4f}")
        print(f"   Delta = {data['greeks']['delta']:.4f}")
        print(f"   Gamma = {data['greeks']['gamma']:.4f}")
    else:
        print(f"❌ Error: {result['error']}")
    
    # Test 3: Binomial Tree Pricing
    print("\n🌳 Test 3: Binomial Tree Pricing")
    result = test_api_endpoint("/valuation/binomial-tree", "POST", {
        "S": 100, "K": 100, "T": 1.0, "r": 0.05, "sigma": 0.2, 
        "option_type": "call", "steps": 100, "american": True
    })
    test_results.append(("Binomial Tree Pricing", result["success"]))
    if result["success"]:
        print(f"✅ American Call Option Price = ${result['data']['option_price']:.4f}")
    else:
        print(f"❌ Error: {result['error']}")
    
    # Test 4: Asian Option Pricing
    print("\n🌊 Test 4: Asian Option Pricing")
    result = test_api_endpoint("/valuation/exotic-options", "POST", {
        "option_class": "asian",
        "S": 100, "K": 100, "T": 1.0, "r": 0.05, "sigma": 0.2,
        "option_type": "call", "average_type": "arithmetic",
        "num_paths": 5000, "steps": 100
    })
    test_results.append(("Asian Option Pricing", result["success"]))
    if result["success"]:
        data = result['data']
        print(f"✅ Asian Call Option Price = ${data['price']:.4f}")
        print(f"   Standard Error = {data['std_error']:.6f}")
    else:
        print(f"❌ Error: {result['error']}")
    
    # Test 5: Barrier Option Pricing
    print("\n🚧 Test 5: Barrier Option Pricing")
    result = test_api_endpoint("/valuation/exotic-options", "POST", {
        "option_class": "barrier",
        "S": 100, "K": 100, "T": 1.0, "r": 0.05, "sigma": 0.2,
        "option_type": "call", "barrier": 90, "barrier_type": "down_and_out",
        "num_paths": 5000, "steps": 100
    })
    test_results.append(("Barrier Option Pricing", result["success"]))
    if result["success"]:
        data = result['data']
        print(f"✅ Down-and-Out Barrier Call = ${data['price']:.4f}")
    else:
        print(f"❌ Error: {result['error']}")
    
    # Test 6: Bond Pricing
    print("\n📜 Test 6: Bond Pricing")
    result = test_api_endpoint("/valuation/bond-pricing", "POST", {
        "face_value": 1000,
        "coupon_rate": 0.05,
        "years_to_maturity": 10,
        "yield_to_maturity": 0.06,
        "frequency": 2
    })
    test_results.append(("Bond Pricing", result["success"]))
    if result["success"]:
        data = result['data']
        print(f"✅ Bond Price = ${data['bond_price']:.2f}")
        print(f"   Macaulay Duration = {data['macaulay_duration']:.2f} years")
        print(f"   Modified Duration = {data['modified_duration']:.2f}")
    else:
        print(f"❌ Error: {result['error']}")
    
    # Test 7: Implied Volatility
    print("\n🔍 Test 7: Implied Volatility Calculation")
    result = test_api_endpoint("/valuation/implied-volatility", "POST", {
        "option_price": 10.0,
        "S": 100, "K": 100, "T": 0.25, "r": 0.05, "option_type": "call"
    })
    test_results.append(("Implied Volatility", result["success"]))
    if result["success"]:
        data = result['data']
        print(f"✅ Implied Volatility = {data['implied_volatility']:.2%}")
        print(f"   Market Price = ${data['market_price']:.4f}")
        print(f"   Model Price = ${data['model_price']:.4f}")
    else:
        print(f"❌ Error: {result['error']}")
    
    # Test 8: Option Chain Generation
    print("\n🔗 Test 8: Option Chain Generation")
    result = test_api_endpoint("/valuation/option-chain", "GET", params={
        "S": 100, "T": 0.25, "r": 0.05, "sigma": 0.2,
        "K_min": 90, "K_max": 110, "K_step": 5
    })
    test_results.append(("Option Chain", result["success"]))
    if result["success"]:
        chain = result['data']['option_chain']
        print(f"✅ Generated option chain with {len(chain)} strikes")
        print("   Sample strikes and call prices:")
        for i, option in enumerate(chain[:3]):
            print(f"   K=${option['strike']:.0f}: Call=${option['call_price']:.4f}")
    else:
        print(f"❌ Error: {result['error']}")
    
    # Test 9: Async Monte Carlo Task
    print("\n⚡ Test 9: Async Monte Carlo Simulation")
    result = test_api_endpoint("/tasks/montecarlo", "POST", params={
        "trials": 5000, "S0": 100, "r": 0.05, "sigma": 0.2,
        "T": 1.0, "K": 100, "option_type": "call"
    })
    test_results.append(("Async Monte Carlo", result["success"]))
    if result["success"]:
        task_id = result['data']['task_id']
        print(f"✅ Monte Carlo task submitted: {task_id}")
        
        # Poll for completion
        print("   Waiting for completion...", end="")
        for _ in range(30):  # Wait up to 30 seconds
            time.sleep(1)
            print(".", end="", flush=True)
            
            status_result = test_api_endpoint(f"/tasks/status/{task_id}")
            if status_result["success"] and status_result['data']['status'] == 'completed':
                print(" ✅ Completed!")
                mc_result = status_result['data']['result']
                print(f"   Option Price = ${mc_result['option_price']:.4f}")
                print(f"   Computation Time = {mc_result['computation_time_seconds']:.2f}s")
                break
        else:
            print(" ⏳ Still running...")
    else:
        print(f"❌ Error: {result['error']}")
    
    # Test 10: Cache Stats
    print("\n💾 Test 10: Cache Statistics")
    result = test_api_endpoint("/tasks/cache-stats")
    test_results.append(("Cache Stats", result["success"]))
    if result["success"]:
        stats = result['data']
        print(f"✅ Cache Stats Retrieved:")
        print(f"   Used Memory: {stats.get('used_memory', 'N/A')}")
        print(f"   Keys: {stats.get('keys', 0)}")
        print(f"   Hit Rate: {stats.get('hit_rate', 0):.2%}")
    else:
        print(f"❌ Error: {result['error']}")
    
    # Test 11: Volatility Surface
    print("\n🌊 Test 11: Volatility Surface Generation")
    result = test_api_endpoint("/valuation/volatility-surface", "GET", params={
        "S": 100, "r": 0.05, "base_vol": 0.2, "K_range": 0.4, "T_max": 2.0
    })
    test_results.append(("Volatility Surface", result["success"]))
    if result["success"]:
        surface = result['data']['volatility_surface']
        print(f"✅ Generated volatility surface with {len(surface)} data points")
        # Show sample data point
        sample = surface[0]
        print(f"   Sample: K=${sample['strike']:.2f}, T={sample['time_to_expiry']:.2f}, Vol={sample['volatility']:.2%}")
    else:
        print(f"❌ Error: {result['error']}")
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, success in test_results if success)
    total = len(test_results)
    
    for test_name, success in test_results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 All tests passed! Your enhanced valuation engine is working perfectly!")
    else:
        print("⚠️  Some tests failed. Check the API server and dependencies.")
    
    return passed == total


def check_dependencies():
    """Check if the API server is running"""
    print("🔍 Checking API server connectivity...")
    try:
        response = requests.get(f"{API_BASE}/")
        if response.status_code == 200:
            print("✅ API server is running")
            return True
        else:
            print(f"❌ API server returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to API server: {e}")
        print("Please make sure the FastAPI server is running on http://localhost:8000")
        return False


if __name__ == "__main__":
    print("🧪 Enhanced Valuation Engine Test Suite")
    print("=" * 60)
    
    if not check_dependencies():
        print("\n💡 To start the API server, run:")
        print("   uvicorn app.main:app --reload --port 8000")
        sys.exit(1)
    
    success = run_comprehensive_tests()
    
    if success:
        print("\n🚀 Ready to start the Streamlit app!")
        print("   streamlit run streamlit_app.py")
    
    sys.exit(0 if success else 1)