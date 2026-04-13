import pytest
"""
End-to-End Test: Manager Workflow + Telegram Report Delivery
Tests: Groq connection, Gemini init, Report generation, Telegram message delivery.
"""
import os
import sys
import asyncio
import requests

# Inject Root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
load_dotenv(env_path, override=True)

from src.manager.intelligence import AlphaManagerAI

def test_env_vars():
    """Step 1: Verify all critical env vars are present."""
    print("=" * 60)
    print("🔍 [TEST 1] Environment Variables Check")
    print("=" * 60)
    
    required = ["GROQ_API_KEY", "GEMINI_API_KEY", "TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID"]
    all_ok = True
    for var in required:
        val = os.getenv(var)
        if val:
            print(f"  ✅ {var} = {val[:8]}...{val[-4:]}")
        else:
            print(f"  ❌ {var} = MISSING!")
            all_ok = False
    return all_ok

def test_groq_connection():
    """Step 2: Test Groq API connectivity."""
    print("\n" + "=" * 60)
    print("🧠 [TEST 2] Groq API (Llama 3.3 70B)")
    print("=" * 60)
    
    try:
        manager = AlphaManagerAI()
        response = manager.process_request("Hello, respond with exactly: GROQ_ALIVE", use_tools=False)
        print(f"  Response: {response[:200]}")
        print("  ✅ Groq connection PASSED")
        return manager
    except Exception as e:
        print(f"  ❌ Groq FAILED: {e}")
        return None

@pytest.fixture
def manager():
    from src.manager.intelligence import AlphaManagerAI
    return AlphaManagerAI()

def test_report_generation(manager):
    """Step 3: Generate the project status report."""
    print("\n" + "=" * 60)
    print("📊 [TEST 3] Project Status Report Generation")
    print("=" * 60)
    
    try:
        report = manager.generate_daily_report()
        print(f"  Report length: {len(report)} chars")
        print(f"  Preview: {report[:300]}...")
        print("  ✅ Report generation PASSED")
        return report
    except Exception as e:
        print(f"  ❌ Report generation FAILED: {e}")
        return None

@pytest.fixture
def report():
    return 'test report'

def test_telegram_delivery(report):
    """Step 4: Send the report directly to Telegram (raw API, bypasses bot framework)."""
    print("\n" + "=" * 60)
    print("📱 [TEST 4] Telegram Direct Delivery")
    print("=" * 60)
    
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    
    if not token or not chat_id:
        print("  ❌ Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID")
        return False
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    
    # Truncate to Telegram's 4096 limit and strip problematic formatting
    safe_report = report.replace("```", "").replace("**", "")[:3900]
    
    payload = {
        "chat_id": chat_id,
        "text": f"📊 AlphaEdge Project Status Report\n{'='*40}\n\n{safe_report}",
    }
    
    try:
        resp = requests.post(url, json=payload, timeout=10)
        data = resp.json()
        if data.get("ok"):
            print(f"  ✅ Message delivered to chat {chat_id}!")
            print(f"  Message ID: {data['result']['message_id']}")
            return True
        else:
            print(f"  ❌ Telegram API error: {data.get('description', 'Unknown')}")
            return False
    except Exception as e:
        print(f"  ❌ Network error: {e}")
        return False

def test_meta_loop_routing(manager):
    """Step 5: Test the Meta-Loop routing (tool-calling)."""
    print("\n" + "=" * 60)
    print("🔄 [TEST 5] Meta-Loop Tool Routing")
    print("=" * 60)
    
    try:
        response = manager.process_request(
            "Read the file src/core/engine.py and tell me what model it loads.",
            use_tools=True
        )
        print(f"  Response: {response[:300]}...")
        print("  ✅ Tool routing PASSED")
        return True
    except Exception as e:
        print(f"  ❌ Tool routing FAILED: {e}")
        return False

def run_all_tests():
    print("\n🚀 ALPHAEDGE MANAGER E2E TEST SUITE\n")
    
    # Test 1: Env
    env_ok = test_env_vars()
    if not env_ok:
        print("\n⚠️ Fix missing env vars before continuing!\n")
    
    # Test 2: Groq
    manager = test_groq_connection()
    if not manager:
        print("\n💀 Cannot continue without Groq. Aborting.")
        return
    
    # Test 3: Report
    report = test_report_generation(manager)
    
    # Test 4: Telegram
    if report:
        test_telegram_delivery(report)
    
    # Test 5: Meta-Loop
    test_meta_loop_routing(manager)
    
    print("\n" + "=" * 60)
    print("🏁 ALL TESTS COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    run_all_tests()
