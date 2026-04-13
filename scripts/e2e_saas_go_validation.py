import asyncio
import os
import sys

# Ensure AlphaEdge source is in path
sys.path.append(os.getcwd())

from src.core.meta_manager import MetaManager


async def run_e2e_go_factory_test():
    """
    Triggers a real E2E build for 'SpeechToPost_AI' using Go/Gin and Self-Evolution.
    This validation now asserts template selection, scaffold generation, CI/CD, smoke tests,
    and deploy rollback behavior.
    """
    print("\n🏗️ [E2E GO FACTORY] Initializing Sovereign Build Cycle...")

    # Load environment
    from dotenv import load_dotenv

    load_dotenv()

    meta = MetaManager()

    project_name = "SpeechToPost_AI"
    description = "A powerful AI that converts voice notes into SEO-optimized blog posts using Go and Gin."
    price = "$19/mo"

    print("📡 Handing over task to SaaS Manager...")

    # 1. Initialize State with explicit product type template
    project = meta.saas.load_project(project_name)
    project.config.update(
        {
            "description": description,
            "price": price,
            "product_type": "api",
        }
    )
    meta.saas.save_project(project)

    # 2. RUN P0 (Cognition + scaffold generation)
    print("\n🧠 [PHASE 0] Architecture, template selection, and scaffold generation...")
    report_p0 = await meta.saas.advance_project(project_name)
    print(f"Result: {report_p0}")

    project = meta.saas.load_project(project_name)
    print(f"Template selected: {project.artifacts.get('template_type')}")
    print(f"Scaffold root: {project.artifacts.get('scaffold_dir')}")
    print(f"CI/CD pipeline: {project.artifacts.get('ci_cd_pipeline')}")
    print(f"Smoke tests: {project.artifacts.get('smoke_tests')}")

    # 3. RUN P1 (Infra - Neon DB)
    print("\n🔌 [PHASE 1] Infrastructure & Neon DB Provisioning...")
    report_p1 = await meta.saas.advance_project(project_name)
    print(f"Result: {report_p1}")

    # 4. RUN P2 (Dev) + Refinement
    print("\n🛠️ [PHASE 2] Development & Self-Evolution...")
    report_p2 = await meta.saas.advance_project(project_name)
    print(f"Result: {report_p2}")

    print("\n🧬 [EVOLUTION PULSE] Jules is self-correcting the Go code...")
    report_refine = await meta.saas.advance_project(project_name)
    print(f"Result: {report_refine}")

    # 5. RUN QA
    print("\n🧪 [PHASE 3] QA smoke test registration...")
    report_p3 = await meta.saas.advance_project(project_name)
    print(f"Result: {report_p3}")

    # 6. RUN Deploy with forced failure to validate rollback gate
    project = meta.saas.load_project(project_name)
    project.config["force_unhealthy_deploy"] = True
    meta.saas.save_project(project)

    print("\n🚨 [PHASE 4] Deploy with forced unhealthy checks to validate rollback...")
    report_p4 = await meta.saas.advance_project(project_name)
    print(f"Result: {report_p4}")

    project = meta.saas.load_project(project_name)
    print(f"Deploy status: {project.artifacts.get('deploy_status')}")
    print(f"Rollback status: {project.artifacts.get('rollback_status')}")
    print(f"Health report: {project.artifacts.get('last_deploy_health_report')}")

    print("\n🏆 E2E GO VALIDATION COMPLETE.")
    print(f"State stored in: data/projects/{project_name.lower()}_ai.json")


if __name__ == "__main__":
    asyncio.run(run_e2e_go_factory_test())
