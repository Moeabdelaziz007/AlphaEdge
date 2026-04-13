import asyncio
import os
import sys

# Add project root to sys.path
sys.path.append(os.getcwd())

from src.core.meta_manager import MetaManager
from src.core.saas_manager import SaaSManager, SaaSProject

async def test_saas_loop():
    print("🏗️ Starting SaaS State Machine Sandbox Test...")
    
    # Initialize
    meta = MetaManager()
    orchestrator = meta.saas
    
    project_name = "TestSummarizer"
    description = "A tool that summarizes long videos for marketers."
    price = "$15/mo"
    
    # 1. Initialize Project
    print(f"🔹 Step 1: Initializing Project '{project_name}'...")
    project = orchestrator.load_project(project_name)
    project.config.update({"description": description, "price": price})
    orchestrator.save_project(project)
    
    # 2. Advance to P0 (Cognition)
    print(f"🔹 Step 2: Advancing to P0 (Architecture & Tickets)...")
    # Note: This will call Gemini and Jules. We check if files are created.
    result = await orchestrator.advance_project(project_name)
    print(f"   Result: {result}")
    
    # 3. Check State Persistence
    updated_project = orchestrator.load_project(project_name)
    print(f"🔹 Step 3: Checking Persistence...")
    print(f"   Current State: {updated_project.state}")
    print(f"   PRD Path: {updated_project.artifacts.get('prd_path')}")
    
    if updated_project.state == "infra":
        print("✅ P0 Transition Successful.")
    else:
        print("❌ P0 Transition Failed.")

if __name__ == "__main__":
    asyncio.run(test_saas_loop())
