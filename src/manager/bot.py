import os
import sys
import json
import asyncio
import datetime
import tempfile

# Inject Project Root to PYTHONPATH native resolution
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from dotenv import load_dotenv, set_key

# CRITICAL: Load .env BEFORE importing intelligence (which uses os.getenv at module level)
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env')
load_dotenv(env_path, override=True)

from telegram import Update, BotCommand
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from src.manager.intelligence import AlphaManagerAI
from src.core.github_bridge import RepoManager
from src.manager.watcher import start_watcher

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

ai_manager = AlphaManagerAI()
github = RepoManager()


async def post_init(application):
    """Set bot commands and menu button after startup."""
    commands = [
        BotCommand("start", "Initialize Neural Link"),
        BotCommand("report", "Project Status Report"),
        BotCommand("skills", "List learned skills"),
        BotCommand("runskill", "Execute a skill: /runskill <name>"),
        BotCommand("repo", "Live GitHub repo status"),
        BotCommand("prs", "List open Pull Requests"),
        BotCommand("commits", "Recent commit history"),
        BotCommand("tree", "Browse repo: /tree [path]"),
        BotCommand("analyze", "Code search: /analyze <query>"),
        BotCommand("search", "Web search: /search <query>"),
        BotCommand("logs", "Read recent chat logs"),
    ]
    await application.bot.set_my_commands(commands)

    # Set menu button to open TMA (requires HTTPS URL configured via BotFather)
    tma_url = os.getenv("TMA_URL", "")
    if tma_url.startswith("https://"):
        from telegram import MenuButtonWebApp, WebAppInfo
        await application.bot.set_chat_menu_button(
            menu_button=MenuButtonWebApp(text="🔮 Hologram", web_app=WebAppInfo(url=tma_url))
        )
    else:
        from telegram import MenuButtonCommands
        await application.bot.set_chat_menu_button(
            menu_button=MenuButtonCommands()
        )
        
    # Launch predictive file watcher
    try:
        start_watcher(application.bot)
    except Exception as e:
        print(f"Failed to start Predictive Watcher: {e}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    current_chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if str(current_chat_id) != str(chat_id):
        set_key(env_path, "TELEGRAM_CHAT_ID", str(chat_id))
        os.environ["TELEGRAM_CHAT_ID"] = str(chat_id)

    await update.message.reply_text(
        f"✅ Neural Link established. Chat ID [{chat_id}] secured.\n\n"
        "I am AlphaManager, your 50% AI Co-Founder.\n\n"
        "Commands:\n"
        "/report - Project Status Report\n"
        "/skills - Learned AI skills\n"
        "/runskill [name] - Execute a skill\n"
        "/repo   - Live GitHub status\n"
        "/prs    - Open Pull Requests\n"
        "/commits - Recent commits\n"
        "/tree [path] - Browse repo\n"
        "/analyze [query] - Search codebase\n"
        "/search [query] - Search the web\n"
        "/logs - View recent AI memory\n\n"
        "You can also send voice messages or text."
    )


async def handle_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = await update.message.reply_text("🧠 Generating Project Status Report...")
    try:
        report = ai_manager.generate_daily_report()
        await _safe_send(msg, update, report)
    except Exception as e:
        await msg.edit_text(f"⚠️ Report Error: {e}")


async def handle_skills(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        from src.skills import list_skills
        skills = list_skills()
        if skills:
            text = "🛠️ Learned Skills:\n" + "\n".join(f"  • {s}" for s in skills)
        else:
            text = "📭 No skills learned yet."
        await update.message.reply_text(text)
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")


async def handle_repo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    info = github.get_repo_info()
    git_status = github.get_git_status()
    await update.message.reply_text(f"{info}\n\n{git_status}")


async def handle_prs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prs = github.list_open_prs()
    await update.message.reply_text(prs)


async def handle_commits(update: Update, context: ContextTypes.DEFAULT_TYPE):
    commits = github.get_git_log()
    await update.message.reply_text(commits)


async def handle_tree(update: Update, context: ContextTypes.DEFAULT_TYPE):
    path = " ".join(context.args) if context.args else ""
    tree = github.get_file_tree(path)
    await update.message.reply_text(tree)


async def handle_runskill(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /runskill <skill_name>")
        return
    msg = await update.message.reply_text(f"⚙️ Running skill: {context.args[0]}...")
    # Wrap sync call via process_request
    resp = ai_manager.process_request(f'execute the skill named "{context.args[0]}"')
    await _safe_send(msg, update, resp)


async def handle_analyze(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /analyze <query or filepath>")
        return
    query = " ".join(context.args)
    msg = await update.message.reply_text(f"🟩 Scanning Code Matrix for: {query}...")
    resp = ai_manager.process_request(f'search my codebase for "{query}"')
    await _safe_send(msg, update, resp)


async def handle_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /search <query>")
        return
    query = " ".join(context.args)
    msg = await update.message.reply_text(f"🌐 Searching Web for: {query}...")
    resp = ai_manager.process_request(f'search the web for "{query}"')
    await _safe_send(msg, update, resp)


async def handle_logs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = await update.message.reply_text("📜 Reading memory logs...")
    resp = ai_manager.process_request("read the chat logs")
    await _safe_send(msg, update, resp)


# ---------------------------------------------------------
# HEARTBEAT LOOP (Autonomous Background Routine)
# ---------------------------------------------------------
async def heartbeat_routine(context: ContextTypes.DEFAULT_TYPE):
    """
    Runs periodically. Reads heartbeat.md and triggers AlphaManagerAI to act.
    """
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not chat_id:
        return
        
    heartbeat_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "heartbeat.md")
    
    if not os.path.exists(heartbeat_path):
        return
        
    try:
        with open(heartbeat_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        if not content.strip():
            return
            
        print("🫀 Executing Heartbeat Loop...")
        directive = f"HEARTBEAT BACKGROUND DIRECTIVE:\n\n{content}\n\nExecute the next logical phase autonomously."
        
        # We don't log this to chat history to avoid cluttering human chat logs
        response = ai_manager.process_request(directive)
        
        # Alert the user that the background agent did something
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"🫀 **Background Heartbeat Executed**\n\n{response[:3500]}",
            parse_mode="Markdown"
        )
    except Exception as e:
        print(f"⚠️ Heartbeat Error: {e}")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    msg = await update.message.reply_text("🧠 Routing through Meta-Loop...")

    try:
        # Log user query
        _log_chat("user", user_text)
        
        response = ai_manager.process_request(user_text)
        
        # Log AI response
        _log_chat("assistant", response)
        
        await _safe_send(msg, update, response)
    except Exception as e:
        await msg.edit_text(f"⚠️ Error: {e}")


async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle native Telegram voice messages (fallback when TMA mic is blocked)."""
    msg = await update.message.reply_text("🎙️ Processing voice message...")

    try:
        voice = update.message.voice or update.message.audio
        file = await context.bot.get_file(voice.file_id)

        # Download to temp file
        with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as tmp:
            await file.download_to_drive(tmp.name)
            tmp_path = tmp.name

        # Transcribe with whisper if available, otherwise note limitation
        transcription = await _transcribe_audio(tmp_path)

        if transcription:
            await msg.edit_text(f"🎙️ Heard: \"{transcription}\"\n\n🧠 Processing...")
            _log_chat("user", f"[Voice] {transcription}")
            
            response = ai_manager.process_request(transcription)
            
            _log_chat("assistant", response)
            await _safe_send(msg, update, response)
        else:
            await msg.edit_text("⚠️ Could not transcribe. Whisper/STT not available locally.")

        # Cleanup
        os.unlink(tmp_path)

    except Exception as e:
        await msg.edit_text(f"⚠️ Voice processing error: {e}")


async def _transcribe_audio(file_path: str) -> str:
    """Attempt to transcribe audio. Uses Groq Whisper API as primary."""
    try:
        from groq import Groq
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        with open(file_path, "rb") as audio_file:
            transcription = client.audio.transcriptions.create(
                model="whisper-large-v3",
                file=audio_file,
            )
        return transcription.text
    except Exception as e:
        print(f"Whisper transcription failed: {e}")
        return None


async def auto_daily_report(context: ContextTypes.DEFAULT_TYPE):
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not chat_id:
        return
    try:
        report = ai_manager.generate_daily_report()
        safe_report = report.replace("```", "").replace("**", "")
        if len(safe_report) > 4000:
            for i in range(0, len(safe_report), 4000):
                await context.bot.send_message(chat_id=chat_id, text=safe_report[i:i+4000])
        else:
            await context.bot.send_message(chat_id=chat_id, text=safe_report)
    except Exception as e:
        await context.bot.send_message(chat_id=chat_id, text=f"⚠️ Auto-report failed: {e}")


async def _safe_send(msg, update, text: str):
    """Safely send text, stripping bad Markdown and chunking for Telegram 4096 limit."""
    safe = text.replace("```", "").replace("**", "").replace("__", "")
    if len(safe) > 4000:
        await msg.edit_text(safe[:4000])
        for i in range(4000, len(safe), 4000):
            await update.message.reply_text(safe[i:i+4000])
    else:
        await msg.edit_text(safe)


def _log_chat(role: str, text: str):
    """Appends to the local chat history log for AI self-analysis."""
    log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "logs")
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "chat_history.jsonl")
    
    entry = {
        "timestamp": datetime.datetime.now().isoformat(),
        "role": role,
        "content": text
    }
    try:
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    except:
        pass


def run_manager_daemon():
    if not BOT_TOKEN:
        print("[!] TELEGRAM_BOT_TOKEN missing in .env")
        return

    print(f"🔑 Token: {BOT_TOKEN[:10]}...{BOT_TOKEN[-5:]}")
    print(f"📨 Chat ID: {os.getenv('TELEGRAM_CHAT_ID')}")

    app = Application.builder().token(BOT_TOKEN).post_init(post_init).build()

    # Command handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("report", handle_report))
    app.add_handler(CommandHandler("skills", handle_skills))
    app.add_handler(CommandHandler("runskill", handle_runskill))
    app.add_handler(CommandHandler("repo", handle_repo))
    app.add_handler(CommandHandler("prs", handle_prs))
    app.add_handler(CommandHandler("commits", handle_commits))
    app.add_handler(CommandHandler("tree", handle_tree))
    app.add_handler(CommandHandler("analyze", handle_analyze))
    app.add_handler(CommandHandler("search", handle_search))
    app.add_handler(CommandHandler("logs", handle_logs))

    # Message handlers
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.VOICE | filters.AUDIO, handle_voice))

    # Schedule Daily Report & Heartbeat
    job_queue = app.job_queue
    if job_queue is not None:
        job_queue.run_daily(auto_daily_report, time=datetime.time(hour=9, minute=0))
        # Autonomously run the heartbeat routine every hour, starting 15 seconds after boot
        job_queue.run_repeating(heartbeat_routine, interval=3600, first=15)
        print("📊 Daily report scheduled for 09:00 AM.")
        print("🫀 Background Heartbeat (Cron) Loop Active.")
    else:
        print("⚠️ JobQueue unavailable. Heartbeat disabled.")

    print("🚀 AlphaManager ONLINE. Send /start to the bot.")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    run_manager_daemon()
