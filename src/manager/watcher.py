import os
import time
import asyncio
from typing import Dict, List, Set

# The directory to watch
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
SRC_DIR = os.path.join(PROJECT_ROOT, "src")

# We keep a simple state of file modification times
_file_mtimes: Dict[str, float] = {}

def get_module_name(filepath: str) -> str:
    """Converts a filepath like src/core/engine.py to 'core.engine'"""
    rel_path = os.path.relpath(filepath, SRC_DIR)
    if rel_path.endswith(".py"):
        rel_path = rel_path[:-3]
    return rel_path.replace(os.sep, ".")

def find_dependents(target_module_name: str) -> List[str]:
    """
    Scans all .py files in SRC_DIR to see if they import 'target_module_name'.
    Provides a simple AST/text blast-radius detection.
    """
    dependents = []
    
    # Just the tail name like 'engine' might be imported directly
    short_name = target_module_name.split('.')[-1]
    
    for root, _, files in os.walk(SRC_DIR):
        for file in files:
            if not file.endswith(".py"):
                continue
            filepath = os.path.join(root, file)
            # Avoid self-referencing check
            if get_module_name(filepath) == target_module_name:
                continue
                
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Very simple dependency parsing. 
                # (For production 10x systems, we use the literal python ast.parse)
                if f"import {target_module_name}" in content \
                   or f"from {target_module_name}" in content \
                   or f"import {short_name}" in content \
                   or f"from {short_name}" in content:
                    dependents.append(get_module_name(filepath))
            except Exception:
                pass
                
    return dependents

async def watcher_loop(bot):
    """
    The background clairvoyant loop.
    Checks file modifications every 5 seconds.
    """
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not chat_id:
        print("⚠️ Watcher disabled: TELEGRAM_CHAT_ID not set.")
        return

    print("👁️ Predictive Watcher (Clairvoyance) is now ACTIVE.")
    
    # Initial indexing
    for root, _, files in os.walk(SRC_DIR):
        for file in files:
            if file.endswith(".py") or file.endswith(".md"):
                filepath = os.path.join(root, file)
                try:
                    _file_mtimes[filepath] = os.stat(filepath).st_mtime
                except Exception:
                    pass

    while True:
        await asyncio.sleep(5.0)
        
        changed_files = []
        for root, _, files in os.walk(SRC_DIR):
            for file in files:
                if not (file.endswith(".py") or file.endswith(".md")):
                    continue
                    
                filepath = os.path.join(root, file)
                try:
                    current_mtime = os.stat(filepath).st_mtime
                    old_mtime = _file_mtimes.get(filepath)
                    
                    if old_mtime is not None and current_mtime > old_mtime:
                        changed_files.append((filepath, current_mtime))
                except Exception:
                    pass
        
        # Process changes
        for filepath, new_mtime in changed_files:
            _file_mtimes[filepath] = new_mtime
            
            # If it's a python file, analyze Blast Radius
            if filepath.endswith(".py"):
                mod_name = get_module_name(filepath)
                impacted = find_dependents(mod_name)
                
                filename = os.path.basename(filepath)
                
                if impacted:
                    impact_str = ", ".join([f"`{i}`" for i in impacted])
                    msg = (
                        f"🚨 **Predictive Watcher Alert**\n\n"
                        f"يا برو، أنا اكتشفت إنك معدل في ملف `{filename}` 📝.\n\n"
                        f"⚠️ **انتبه:** التعديل ده ممكن يضرب أو يأثر على المكونات دي (Blast Radius):\n"
                        f"{impact_str}\n\n"
                        f"تحب أعمل Re-index على الكود كله والميليشيا تراجع التعديلات دي قبل ما تضرب حاجة؟ 🕵️‍♂️"
                    )
                else:
                    msg = (
                        f"📡 **Predictive Watcher Alert**\n\n"
                        f"ملف `{filename}` اتعدل. الملف ده كأنه Standalone مفيش حاجة تانية بتعتمد عليه حالياً، "
                        f"بس لو تحبني أراجعه، ابعتلي. 👍"
                    )
                
                try:
                    await bot.send_message(chat_id=chat_id, text=msg, parse_mode="Markdown")
                    print(f"📡 Sent proactive alert for {filename}")
                except Exception as e:
                    print(f"❌ Failed to send Telegram alert: {e}")
                    
def start_watcher(bot):
    """
    Registers the watcher non-blocking in the current asyncio loop.
    """
    loop = asyncio.get_running_loop()
    loop.create_task(watcher_loop(bot))
