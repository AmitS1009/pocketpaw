"""Open Interpreter agent wrapper."""

import asyncio
import logging
from typing import AsyncIterator, Optional

from pocketclaw.config import Settings

logger = logging.getLogger(__name__)


class OpenInterpreterAgent:
    """Wraps Open Interpreter for autonomous task execution."""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self._interpreter = None
        self._stop_flag = False
        self._initialize()
    
    def _initialize(self) -> None:
        """Initialize the Open Interpreter instance."""
        try:
            from interpreter import interpreter
            
            # Configure interpreter
            interpreter.auto_run = True  # Don't ask for confirmation
            interpreter.loop = True      # Allow multi-step execution
            
            # Set LLM based on settings
            provider = self.settings.llm_provider
            
            # Explicit provider selection
            if provider == "anthropic" and self.settings.anthropic_api_key:
                interpreter.llm.model = self.settings.anthropic_model
                interpreter.llm.api_key = self.settings.anthropic_api_key
                logger.info(f"🤖 Using Anthropic: {self.settings.anthropic_model}")
            elif provider == "openai" and self.settings.openai_api_key:
                interpreter.llm.model = self.settings.openai_model
                interpreter.llm.api_key = self.settings.openai_api_key
                logger.info(f"🤖 Using OpenAI: {self.settings.openai_model}")
            elif provider == "ollama":
                interpreter.llm.model = f"ollama/{self.settings.ollama_model}"
                interpreter.llm.api_base = self.settings.ollama_host
                logger.info(f"🤖 Using Ollama: {self.settings.ollama_model}")
            # Auto mode: prioritize cloud APIs, fallback to Ollama
            elif provider == "auto":
                if self.settings.anthropic_api_key:
                    interpreter.llm.model = self.settings.anthropic_model
                    interpreter.llm.api_key = self.settings.anthropic_api_key
                    logger.info(f"🤖 Auto-selected Anthropic: {self.settings.anthropic_model}")
                elif self.settings.openai_api_key:
                    interpreter.llm.model = self.settings.openai_model
                    interpreter.llm.api_key = self.settings.openai_api_key
                    logger.info(f"🤖 Auto-selected OpenAI: {self.settings.openai_model}")
                else:
                    interpreter.llm.model = f"ollama/{self.settings.ollama_model}"
                    interpreter.llm.api_base = self.settings.ollama_host
                    logger.info(f"🤖 Auto-selected Ollama: {self.settings.ollama_model}")
            
            # Safety settings
            interpreter.safe_mode = "ask"  # Will still ask before dangerous ops
            
            self._interpreter = interpreter
            logger.info("✅ Open Interpreter initialized")
            
        except ImportError:
            logger.error("❌ Open Interpreter not installed. Run: pip install open-interpreter")
            self._interpreter = None
        except Exception as e:
            logger.error(f"❌ Failed to initialize Open Interpreter: {e}")
            self._interpreter = None
    
    async def run(self, message: str) -> AsyncIterator[dict]:
        """Run a message through Open Interpreter with real-time streaming."""
        if not self._interpreter:
            yield {
                "type": "message",
                "content": "❌ Open Interpreter not available. Install with: `pip install open-interpreter`"
            }
            return
        
        self._stop_flag = False
        
        # Use a queue to stream chunks from the sync thread to the async generator
        chunk_queue: asyncio.Queue = asyncio.Queue()
        
        def run_sync():
            """Run interpreter in a thread, push chunks to queue."""
            current_message = []
            
            try:
                for chunk in self._interpreter.chat(message, stream=True):
                    if self._stop_flag:
                        break
                    
                    if isinstance(chunk, dict):
                        chunk_type = chunk.get("type", "")
                        content = chunk.get("content", "")
                        
                        if chunk_type == "code":
                            # Flush any pending message first
                            if current_message:
                                asyncio.run_coroutine_threadsafe(
                                    chunk_queue.put({"type": "message", "content": "".join(current_message)}),
                                    loop
                                )
                                current_message = []
                            # Send code block
                            asyncio.run_coroutine_threadsafe(
                                chunk_queue.put({"type": "code", "content": content}),
                                loop
                            )
                        elif chunk_type == "message" and content:
                            current_message.append(content)
                            # Stream partial messages every ~100 chars
                            if len("".join(current_message)) > 100:
                                asyncio.run_coroutine_threadsafe(
                                    chunk_queue.put({"type": "message", "content": "".join(current_message)}),
                                    loop
                                )
                                current_message = []
                    elif isinstance(chunk, str) and chunk:
                        current_message.append(chunk)
                
                # Flush remaining message
                if current_message:
                    asyncio.run_coroutine_threadsafe(
                        chunk_queue.put({"type": "message", "content": "".join(current_message)}),
                        loop
                    )
            except Exception as e:
                asyncio.run_coroutine_threadsafe(
                    chunk_queue.put({"type": "error", "content": f"Agent error: {str(e)}"}),
                    loop
                )
            finally:
                # Signal completion
                asyncio.run_coroutine_threadsafe(chunk_queue.put(None), loop)
        
        try:
            loop = asyncio.get_event_loop()
            
            # Start the sync function in a thread
            executor_future = loop.run_in_executor(None, run_sync)
            
            # Yield chunks as they arrive
            while True:
                try:
                    chunk = await asyncio.wait_for(chunk_queue.get(), timeout=60.0)
                    if chunk is None:  # End signal
                        break
                    yield chunk
                except asyncio.TimeoutError:
                    yield {"type": "message", "content": "⏳ Still processing..."}
            
            # Wait for executor to finish
            await executor_future
            
        except Exception as e:
            logger.error(f"Open Interpreter error: {e}")
            yield {"type": "error", "content": f"❌ Agent error: {str(e)}"}
    
    async def stop(self) -> None:
        """Stop the agent execution."""
        self._stop_flag = True
        if self._interpreter:
            try:
                self._interpreter.reset()
            except Exception:
                pass

