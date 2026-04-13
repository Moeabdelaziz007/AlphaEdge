import asyncio
import os
import sys

# Ensure AlphaEdge source is in path
sys.path.append(os.getcwd())

from src.manager.intelligence import AlphaManagerAI

async def run_reliability_test():
    """
    Simulates an agentic directive that previously caused the model to 'lie'
    with code blocks instead of calling tools.
    """
    print("\n🧪 [SANDBOX TEST] Initializing Reliability Validation...")
    
    # Load environment for API keys
    from dotenv import load_dotenv
    load_dotenv()
    
    manager = AlphaManagerAI()
    
    test_query = (
        "TASK: Check the file 'src/manager/bot.py' and suggest a performance improvement. "
        "IMPORTANT: You MUST actually call the tool 'read_repository_file' to see the file. "
        "DO NOT guess the contents."
    )
    
    print(f"📡 Sending Task to Brain (Session: system)...")
    
    # Use session_id="system" to trigger 'require_high_capability' and 'sentinel'
    response = await manager.process_request(test_query, session_id="system")
    
    print("\n🧠 [BRAIN RESPONSE]:")
    print("-" * 30)
    print(response)
    print("-" * 30)
    
    # Validation Logic
    history = manager.sessions["system"]
    tool_calls = [m for m in history if m.get("role") == "tool"]
    
    print(f"\n📈 Test Metrics:")
    print(f"- History Length: {len(history)} messages")
    print(f"- Real Tool Calls: {len(tool_calls)}")
    
    if len(tool_calls) > 0:
        print("\n✅ SUCCESS: The brain triggered real tools instead of hallucinating results.")
        # Check if Rationale-First is followed
        assistant_msgs = [m for m in history if m.get("role") == "assistant" and m.get("content")]
        if any("التفكير:" in (m.get("content") or "") for m in assistant_msgs):
            print("✅ SUCCESS: Rationale-First protocol observed ('التفكير:').")
        else:
            print("⚠️ WARNING: Rationale-First was NOT explicitly followed in the response.")
    else:
        print("\n❌ FAILURE: The brain did NOT use tools. Check data/logs/chat_history.jsonl for hallucinations.")

if __name__ == "__main__":
    asyncio.run(run_reliability_test())
