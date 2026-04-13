import os
import sys
import subprocess

# Inject Root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.engine import CognitiveEngine
from src.agents.generator import Generator
from src.agents.challenger import Challenger

def run_arena(target_file: str):
    print("="*60)
    print("⚔️ WELCOME TO THE ALPHAEDGE AUTONOMOUS TDD ARENA ⚔️")
    print("="*60)
    
    # 1. Initialize Edge VRAM Engine
    engine = CognitiveEngine()
    challenger = Challenger(engine)
    generator = Generator(engine)
    
    with open(target_file, 'r') as f:
        source_code = f.read()

    print(f"\n[1] 🧪 Challenger: Analyzing {target_file} to design ruthless Pytest...")
    
    # Hijack Challenger to become Extreme QA
    challenger.hijack_prompt(
        "You are an extreme QA Software Engineer. Write a Python `pytest` test file "
        "that tests the logical boundaries of the provided code. "
        "OUTPUT EXCLUSIVELY VALID PYTHON CODE. DO NOT output markdown ticks or explanations. Just pure import pytest code."
    )
    
    test_code = challenger.critique(user_query="Write complete pytest file", generator_draft=source_code)
    
    # Clean up output to ensure pure python execution (Removing markdown blocks if leaked)
    test_code = test_code.replace("```python", "").replace("```", "").strip()
    
    test_file_path = target_file.replace(".py", "_test.py")
    with open(test_file_path, 'w') as f:
        f.write(test_code)
        
    print(f"✅ Challenger wrote tests -> saved to {test_file_path}")
    
    max_loops = 3
    for loop in range(max_loops):
        print(f"\n[Loop {loop+1}/{max_loops}] 💥 Executing test suite via subprocess...")
        
        result = subprocess.run(["pytest", test_file_path], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("🏆 GENERATOR WINS! The code passes all tests perfectly.")
            break
            
        print("❌ Test Failed! Passing traceback to Generator for patching...\n")
        traceback = result.stdout[-1500:] # Last 1500 chars of traceback
        
        generator.hijack_prompt(
            "You are an Elite 10x Developer. Your code failed the tests. "
            "Read the original code and the PyTest Traceback error. "
            "OUTPUT ONLY THE FIXED COMPLETE SOURCE CODE FILE. Do not explain anything. Just pure valid Python code."
        )
        
        fixed_code = generator.generate(
            f"Traceback:\n{traceback}", 
            context_memories=[source_code]
        )
        
        fixed_code = fixed_code.replace("```python", "").replace("```", "").strip()
        print("🛠️ Generator produced a patch! Saving to file...")
        
        # Save patch
        with open(target_file, 'w') as f:
            f.write(fixed_code)
            
        # Update source code context for next loop
        source_code = fixed_code
        
    print("\n🏁 Arena Execution Terminated.")

if __name__ == "__main__":
    test_target = os.path.join(os.path.dirname(os.path.dirname(__file__)), "tests", "playground.py")
    run_arena(test_target)
