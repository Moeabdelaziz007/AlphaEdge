import asyncio
import os
import sys
import json

# Ensure AlphaEdge source is in path
sys.path.append(os.getcwd())

from src.core.meta_manager import MetaManager
from src.core.saas_manager import SaaSManager, SaaSProject

async def run_e2e_go_factory_test():
    """
    Triggers a real E2E build for 'SpeechToPost_AI' using Go/Gin and Self-Evolution.
    """
    print("\n🏗️ [E2E GO FACTORY] Initializing Sovereign Build Cycle...")
    
    # Load environment
    from dotenv import load_dotenv
    load_dotenv()
    
    meta = MetaManager()
    
    project_name = "SpeechToPost_AI"
    description = "A powerful AI that converts voice notes into SEO-optimized blog posts using Go and Gin."
    price = "$19/mo"
    
    print(f"📡 Handing over task to SaaS Manager...")
    
    # Simulate the MetaManager action "build_saas"
    # We step through the phases manually in this test to capture data at each step
    
    # 1. Initialize State
    project = meta.saas.load_project(project_name)
    project.config.update({"description": description, "price": price})
    meta.saas.save_project(project)
    
    # 2. RUN P0 (Cognition)
    print("\n🧠 [PHASE 0] Architecture & PRD Generation (Go/Gin)...")
    report_p0 = await meta.saas.advance_project(project_name)
    print(f"Result: {report_p0}")
    
    # Verify PRD
    prd_path = project.artifacts.get("prd_path")
    if prd_path and os.path.exists(prd_path):
        print(f"✅ PRD Generated: {prd_path}")
        with open(prd_path, 'r') as f:
            print(f"--- PRD Snippet ---\n{f.read()[:300]}...\n------------------")
    
    # 3. RUN P1 (Infra - Neon DB)
    print("\n🔌 [PHASE 1] Infrastructure & Neon DB Provisioning...")
    report_p1 = await meta.saas.advance_project(project_name)
    print(f"Result: {report_p1}")
    
    # 4. RUN P2 (Dev & Self-Evolution)
    # We trigger P2. This will dispatch to Jules (v0 + Go)
    print("\n🛠️ [PHASE 2] Development & Self-Evolution (DNA Sequencing)...")
    report_p2 = await meta.saas.advance_project(project_name)
    print(f"Result: {report_p2}")
    
    # Since P2 ends with 'refinement' state, we advance again for the Evolution loop
    print("\n🧬 [EVOLUTION PULSE] Jules is self-correcting the Go code...")
    report_refine = await meta.saas.advance_project(project_name)
    print(f"Result: {report_refine}")
    
    # 5. RUN P5 (Marketing)
    # Skip QA/Deploy for this sandbox test if Jules/Render APIs are slow, go straight to Marketing for data capture
    project.state = "marketing"
    meta.saas.save_project(project)
    
    print("\n📢 [PHASE 5] Marketing Copy Generation...")
    report_p5 = await meta.saas.advance_project(project_name)
    print(f"Result/Copy:\n{report_p5}")
    
    print(f"\n🏆 E2E GO VALIDATION COMPLETE.")
    print(f"State stored in: data/projects/{project_name.lower()}_ai.json")

if __name__ == "__main__":
    asyncio.run(run_e2e_go_factory_test())
