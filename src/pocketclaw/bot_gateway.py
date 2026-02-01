"""Telegram bot gateway - the main interface."""

import logging
from typing import Optional

from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)
import httpx

from pocketclaw.config import Settings
from pocketclaw.tools import status, fetch, screenshot
from pocketclaw.llm.router import LLMRouter
from pocketclaw.agents.router import AgentRouter

logger = logging.getLogger(__name__)


# Persistent keyboard
MAIN_KEYBOARD = ReplyKeyboardMarkup(
    [
        ["🟢 Status", "📁 Fetch"],
        ["📸 Screenshot", "🛑 Panic"],
        ["🧠 Agent Mode", "⚙️ Settings"]
    ],
    resize_keyboard=True,
    is_persistent=True
)


class BotGateway:
    """Main Telegram bot gateway."""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.agent_active = False
        self.agent_router: Optional[AgentRouter] = None
        self.llm_router: Optional[LLMRouter] = None
        
    def is_authorized(self, user_id: int) -> bool:
        """Check if user is authorized."""
        return user_id == self.settings.allowed_user_id
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /start command."""
        user_id = update.effective_user.id
        
        # If this is first connection, save the user ID
        if not self.settings.allowed_user_id:
            self.settings.allowed_user_id = user_id
            self.settings.save()
            
            # Notify web server that pairing is complete
            try:
                async with httpx.AsyncClient() as client:
                    await client.post(
                        f"http://{self.settings.web_host}:{self.settings.web_port}/complete",
                        params={"user_id": user_id}
                    )
            except Exception:
                pass  # Web server might already be shut down
            
            await update.message.reply_text(
                "🦀 **PocketClaw Connected!**\n\n"
                "Your AI agent is now running on your machine.\n\n"
                "Use the buttons below to control it, or just type a message to chat.",
                parse_mode="Markdown",
                reply_markup=MAIN_KEYBOARD
            )
        elif self.is_authorized(user_id):
            await update.message.reply_text(
                "🦀 **Welcome back!**\n\nPocketClaw is ready.",
                parse_mode="Markdown",
                reply_markup=MAIN_KEYBOARD
            )
        else:
            await update.message.reply_text("⛔ Unauthorized. This bot is locked to another user.")
    
    async def handle_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle status request."""
        if not self.is_authorized(update.effective_user.id):
            return
        
        stats = status.get_system_status()
        await update.message.reply_text(stats, parse_mode="Markdown")
    
    async def handle_fetch(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle fetch request - show file browser."""
        if not self.is_authorized(update.effective_user.id):
            return
        
        keyboard = fetch.get_directory_keyboard(self.settings.file_jail_path)
        await update.message.reply_text(
            f"📁 **File Browser**\n`{self.settings.file_jail_path}`",
            parse_mode="Markdown",
            reply_markup=keyboard
        )
    
    async def handle_fetch_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle file browser navigation."""
        query = update.callback_query
        await query.answer()
        
        if not self.is_authorized(query.from_user.id):
            return
        
        data = query.data
        if data.startswith("fetch:"):
            path = data[6:]
            result = await fetch.handle_path(path, self.settings.file_jail_path)
            
            if result["type"] == "directory":
                await query.edit_message_text(
                    f"📁 **File Browser**\n`{path}`",
                    parse_mode="Markdown",
                    reply_markup=result["keyboard"]
                )
            elif result["type"] == "file":
                await query.message.reply_document(
                    document=open(path, "rb"),
                    filename=result["filename"]
                )
    
    async def handle_screenshot(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle screenshot request."""
        if not self.is_authorized(update.effective_user.id):
            return
        
        await update.message.reply_text("📸 Taking screenshot...")
        
        img_bytes = screenshot.take_screenshot()
        if img_bytes:
            await update.message.reply_photo(photo=img_bytes, caption="📸 Current screen")
        else:
            await update.message.reply_text("❌ Screenshot failed. Display might not be available.")
    
    async def handle_panic(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle panic button - kill all agent processes."""
        if not self.is_authorized(update.effective_user.id):
            return
        
        self.agent_active = False
        if self.agent_router:
            await self.agent_router.stop()
        
        await update.message.reply_text(
            "🛑 **PANIC ACTIVATED**\n\nAll agent processes stopped.",
            parse_mode="Markdown",
            reply_markup=MAIN_KEYBOARD
        )
    
    async def handle_agent_mode(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Toggle agent mode."""
        if not self.is_authorized(update.effective_user.id):
            return
        
        self.agent_active = not self.agent_active
        
        if self.agent_active:
            if not self.agent_router:
                self.agent_router = AgentRouter(self.settings)
            
            backend = self.settings.agent_backend
            await update.message.reply_text(
                f"🧠 **Agent Mode: ON**\n\n"
                f"Backend: `{backend}`\n\n"
                f"Type your requests naturally. The agent has access to your shell and files.\n\n"
                f"Tap 🛑 Panic to stop at any time.",
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text(
                "🧠 **Agent Mode: OFF**\n\nBack to tool-only mode.",
                parse_mode="Markdown",
                reply_markup=MAIN_KEYBOARD
            )
    
    async def handle_settings(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Show settings menu."""
        if not self.is_authorized(update.effective_user.id):
            return
        
        current_backend = self.settings.agent_backend
        current_llm = self.settings.llm_provider
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(
                f"{'✅' if current_backend == 'open_interpreter' else '⬜'} Open Interpreter",
                callback_data="settings:backend:open_interpreter"
            )],
            [InlineKeyboardButton(
                f"{'✅' if current_backend == 'claude_code' else '⬜'} Claude Code",
                callback_data="settings:backend:claude_code"
            )],
            [InlineKeyboardButton("──── LLM Provider ────", callback_data="noop")],
            [InlineKeyboardButton(
                f"{'✅' if current_llm == 'auto' else '⬜'} Auto (Ollama → OpenAI → Claude)",
                callback_data="settings:llm:auto"
            )],
            [InlineKeyboardButton(
                f"{'✅' if current_llm == 'ollama' else '⬜'} Ollama (Local)",
                callback_data="settings:llm:ollama"
            )],
            [InlineKeyboardButton(
                f"{'✅' if current_llm == 'openai' else '⬜'} OpenAI",
                callback_data="settings:llm:openai"
            )],
            [InlineKeyboardButton(
                f"{'✅' if current_llm == 'anthropic' else '⬜'} Anthropic (Claude)",
                callback_data="settings:llm:anthropic"
            )]
        ])
        
        await update.message.reply_text(
            "⚙️ **Settings**\n\nChoose your agent backend and LLM provider:",
            parse_mode="Markdown",
            reply_markup=keyboard
        )
    
    async def handle_settings_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle settings selection."""
        query = update.callback_query
        await query.answer()
        
        if not self.is_authorized(query.from_user.id):
            return
        
        data = query.data
        if data == "noop":
            return
        
        if data.startswith("settings:backend:"):
            backend = data.split(":")[-1]
            self.settings.agent_backend = backend
            self.settings.save()
            await query.edit_message_text(
                f"✅ Agent backend set to: **{backend}**",
                parse_mode="Markdown"
            )
        
        elif data.startswith("settings:llm:"):
            provider = data.split(":")[-1]
            self.settings.llm_provider = provider
            self.settings.save()
            await query.edit_message_text(
                f"✅ LLM provider set to: **{provider}**",
                parse_mode="Markdown"
            )
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle text messages."""
        if not self.is_authorized(update.effective_user.id):
            return
        
        text = update.message.text
        
        # Handle keyboard buttons
        if text == "🟢 Status":
            await self.handle_status(update, context)
        elif text == "📁 Fetch":
            await self.handle_fetch(update, context)
        elif text == "📸 Screenshot":
            await self.handle_screenshot(update, context)
        elif text == "🛑 Panic":
            await self.handle_panic(update, context)
        elif text == "🧠 Agent Mode":
            await self.handle_agent_mode(update, context)
        elif text == "⚙️ Settings":
            await self.handle_settings(update, context)
        elif self.agent_active and self.agent_router:
            # Send to agent
            await update.message.reply_text("🧠 Thinking...")
            
            async for chunk in self.agent_router.run(text):
                if chunk.get("type") == "message":
                    await update.message.reply_text(chunk["content"])
                elif chunk.get("type") == "code":
                    await update.message.reply_text(
                        f"```\n{chunk['content']}\n```",
                        parse_mode="Markdown"
                    )
        else:
            # Simple LLM chat when agent mode is off
            if not self.llm_router:
                self.llm_router = LLMRouter(self.settings)
            
            response = await self.llm_router.chat(text)
            await update.message.reply_text(response)


async def run_bot(settings: Settings) -> None:
    """Run the Telegram bot."""
    gateway = BotGateway(settings)
    
    app = Application.builder().token(settings.telegram_bot_token).build()
    
    # Command handlers
    app.add_handler(CommandHandler("start", gateway.start))
    
    # Callback handlers
    app.add_handler(CallbackQueryHandler(gateway.handle_fetch_callback, pattern="^fetch:"))
    app.add_handler(CallbackQueryHandler(gateway.handle_settings_callback, pattern="^settings:"))
    
    # Message handler
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, gateway.handle_message))
    
    # Start polling
    await app.initialize()
    await app.start()
    await app.updater.start_polling(drop_pending_updates=True)
    
    logger.info("🦀 PocketClaw is running! Send /start to your bot.")
    
    # Keep running until stopped
    try:
        while True:
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        pass
    finally:
        await app.updater.stop()
        await app.stop()
        await app.shutdown()


# Need to import asyncio for the sleep
import asyncio
