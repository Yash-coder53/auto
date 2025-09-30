import os
import re
import asyncio
import random
import time
import json
import logging
from collections import defaultdict
from telethon import TelegramClient, events
from telethon.tl.types import Channel, Chat, User
from telethon.tl.functions.messages import GetParticipantsRequest
from telethon.tl.types import ChannelParticipantsSearch
from telethon.errors import FloodWaitError, ChatAdminRequiredError

# ========= CONFIGURATION =========
API_ID = int(os.getenv("API_ID", "24633463"))
API_HASH = os.getenv("API_HASH", "a2f7cd31e5017cf4fb84dd6ca2f27809")

SESSION_FILES = [
    os.getenv("BQGuXKQAhQiWxB92vpZ3o6wPj_Jth60YBFPEC7lOcL58MsSg-HfAPt7E4mhMq51Jxb9O-5poYJ0MznBZ2ysVpDJk0DLQ5FxQG7j6ngFq4R7z2KrqKrRe4svrgFgbUKs7srZTp7vhahKaqqu7uRVkVFn5-1CfG2_5M861Rt811yLg5mfFTD92-VDlc3xm9CWenKaUGN5V2qUsQ1C-wwpphMSfIEENVqK1Gi-xkxWTK-2POj4zuzPRjSXabJGFFTb4-VOLtOiarAtNk3SqwtrFFzAc4GM7YPdk0_zKOSerND4BAjvBR5R5so32bvR4Dxx4C-Rqzn1jmv6NpqTRXfoBZF0eRx5KngAAAAGxMMFeAA", "user1"),
    os.getenv("SESSION2", "user2"), 
    os.getenv("SESSION3", "user3"),
]

# Enhanced message database
AUTO_REPLY_MESSAGES = [
    "Hello! Thanks for your message! 👋",
    "Hi there! I'll get back to you soon. ⏳",
    "Thanks for reaching out! I'm currently busy. 📱",
    "Hello! Your message has been received. ✅",
    "Hey! I'll respond properly when I'm free. 🕒"
]

TAG_ALL_MESSAGES = [
    "📢 **Attention Everyone!** \n\n",
    "👋 **Hey everyone!** \n\n",
    "🚨 **Important Notice!** \n\n",
    "📣 **Announcement!** \n\n"
]

class EnhancedBotState:
    def __init__(self):
        self.selected = set()
        self.running = set()
        self.copy_mode = set()
        self.auto_reply_mode = set()
        self.tag_all_mode = set()
        self.last_send = defaultdict(float)
        self.recent_stickers = defaultdict(list)
        self.target = {}
        self.raid_tasks = {}
        self.user_cooldowns = defaultdict(float)
        self.group_cooldowns = defaultdict(float)
        
        # Enhanced settings
        self.auto_reply_delay = 2
        self.max_tag_members = 100
        self.cooldown_time = 30  # seconds

def is_sticker(msg):
    return getattr(getattr(msg, "sticker", None), "id", None) is not None

def get_auto_reply():
    return random.choice(AUTO_REPLY_MESSAGES)

def get_tag_all_prefix():
    return random.choice(TAG_ALL_MESSAGES)

async def type_and_send(client: TelegramClient, state: EnhancedBotState, event, text, typing_ms=600):
    """Enhanced typing with better error handling"""
    try:
        async with client.action(event.chat_id, 'typing'):
            await asyncio.sleep(typing_ms/1000)
        await send_throttled(state, event, text)
    except Exception as e:
        logging.error(f"Typing error: {e}")
        await send_throttled(state, event, text)

async def send_throttled(state: EnhancedBotState, event, text):
    """Enhanced throttling with cooldown management"""
    now = time.time()
    cid = event.chat_id
    
    # Check cooldown
    if now - state.group_cooldowns[cid] < state.cooldown_time:
        return
    
    gap = 1.0 + random.uniform(0.2, 0.5)
    wait = (state.last_send[cid] + gap) - now
    if wait > 0:
        await asyncio.sleep(wait)
    
    try:
        await event.reply(text)
        state.last_send[cid] = time.time()
        state.group_cooldowns[cid] = now
    except FloodWaitError as e:
        wait_time = int(getattr(e, "seconds", 3))
        logging.warning(f"Flood wait: {wait_time}s")
        await asyncio.sleep(wait_time)
        await event.reply(text)
        state.last_send[cid] = time.time()

async def resolve_target(client, event):
    """Enhanced target resolution"""
    r = await event.get_reply_message()
    if r and r.sender_id:
        s = r.sender or await r.get_sender()
        name = getattr(s, "first_name", None) or getattr(s, "username", "user")
        return r.sender_id, name
    
    ents = getattr(event.message, "entities", None) or []
    for e in ents or []:
        if getattr(e, "__class__", None).__name__ == "MessageEntityMentionName":
            return e.user_id, "user"
        if getattr(e, "__class__", None).__name__ == "MessageEntityMention":
            off, ln = e.offset, e.length
            username = (event.raw_text or "")[off:off+ln].lstrip("@")
            try:
                ent = await client.get_entity(username)
                return ent.id, getattr(ent, "first_name", None) or username
            except Exception:
                pass
    return None, None

async def tag_all_members(client: TelegramClient, state: EnhancedBotState, event):
    """Enhanced tag all members functionality"""
    try:
        chat = await event.get_chat()
        
        # Check if it's a group/channel
        if not isinstance(chat, (Channel, Chat)):
            await event.reply("❌ Tag all works only in groups and channels!")
            return
        
        # Check cooldown
        now = time.time()
        if now - state.group_cooldowns[event.chat_id] < 300:  # 5 min cooldown for tag all
            await event.reply("⏳ Please wait 5 minutes before using tag all again!")
            return
        
        await event.reply("🔄 Collecting members...")
        
        participants = []
        tag_message = get_tag_all_prefix()
        
        # Get participants with error handling
        try:
            async for user in client.iter_participants(chat):
                if not user.bot and not user.deleted and not user.is_self:
                    participants.append(user)
                    if len(participants) >= state.max_tag_members:
                        break
        except ChatAdminRequiredError:
            await event.reply("❌ I need admin rights to see all members!")
            return
        except Exception as e:
            logging.error(f"Error getting participants: {e}")
            await event.reply("❌ Error accessing member list!")
            return
        
        if not participants:
            await event.reply("❌ No members found to tag!")
            return
        
        # Build tag message with better formatting
        tagged_count = 0
        for i, user in enumerate(participants):
            if user.username:
                tag_message += f"@{user.username} "
                tagged_count += 1
            else:
                tag_message += f"[{user.first_name or 'User'}](tg://user?id={user.id}) "
                tagged_count += 1
            
            # Split into multiple messages if too many users
            if (i + 1) % 10 == 0:
                tag_message += "\n"
        
        tag_message += f"\n\n✅ **Tagged {tagged_count} members!**"
        
        # Send the tag message
        await event.reply(tag_message)
        state.group_cooldowns[event.chat_id] = time.time()
        
        logging.info(f"Tagged {tagged_count} members in {chat.title}")
        
    except Exception as e:
        logging.error(f"Tag all error: {e}")
        await event.reply("❌ Error tagging members!")

async def raid_runner(client: TelegramClient, state: EnhancedBotState, event, tag, n):
    """Enhanced raid runner with better safety"""
    cid = event.chat_id
    try:
        for i in range(n):
            if i % 5 == 0 and i > 0:  # Add delay every 5 messages
                await asyncio.sleep(2)
            await type_and_send(client, state, event, f"{tag} {get_auto_reply()}", typing_ms=300)
    except asyncio.CancelledError:
        pass
    finally:
        t = state.raid_tasks.get(cid)
        if t is asyncio.current_task():
            state.raid_tasks.pop(cid, None)

def attach_enhanced_handlers(client: TelegramClient, state: EnhancedBotState):
    """Attach all event handlers with enhanced functionality"""
    
    @client.on(events.NewMessage(incoming=True))
    async def enhanced_auto_handler(event):
        """Enhanced auto-reply handler"""
        try:
            sender = await event.get_sender()
            if getattr(sender, "bot", False) or getattr(sender, "is_self", False):
                return
            
            chat = await event.get_chat()
            cid = event.chat_id
            
            # Handle auto-reply in selected chats
            if cid in state.selected and cid in state.running and cid in state.auto_reply_mode:
                await handle_auto_reply(client, state, event, chat, sender)
            
            # Handle tag all command
            if event.message.text and any(cmd in event.message.text.lower() for cmd in ['!tagall', '/tagall', '@all']):
                await handle_tag_all_command(client, state, event, chat)
                
        except Exception as e:
            logging.error(f"Auto handler error: {e}")

    async def handle_auto_reply(client, state, event, chat, sender):
        """Handle automatic replies"""
        now = time.time()
        
        # User cooldown check
        if now - state.user_cooldowns[sender.id] < state.auto_reply_delay:
            return
        
        # Add random delay to avoid detection
        await asyncio.sleep(random.uniform(1, 3))
        
        reply_text = get_auto_reply()
        
        # Personalize DM replies
        if isinstance(chat, User):
            reply_text = f"Hi {sender.first_name}! {reply_text}"
        
        await event.reply(reply_text)
        state.user_cooldowns[sender.id] = now
        logging.info(f"Auto-replied to {sender.first_name}")

    async def handle_tag_all_command(client, state, event, chat):
        """Handle tag all commands"""
        if isinstance(chat, (Channel, Chat)):
            await tag_all_members(client, state, event)
        else:
            await event.reply("ℹ️ Tag all works only in groups and channels!")

    @client.on(events.NewMessage(outgoing=True, pattern=r'\.(allow|remove|start|stop|copy|tagall|autoreply)'))
    async def enhanced_commands(event):
        """Enhanced command handler"""
        try:
            command = event.pattern_match.group(1)
            cid = event.chat_id
            text = (event.raw_text or "").strip().lower()
            
            if command == "allow":
                state.selected.add(cid)
                reply_msg = "✅ Chat selected! Use .start to enable features."
                await event.reply(reply_msg)
                await event.delete()

            elif command == "remove":
                state.selected.discard(cid)
                state.running.discard(cid)
                state.auto_reply_mode.discard(cid)
                state.tag_all_mode.discard(cid)
                state.target.pop(cid, None)
                task = state.raid_tasks.pop(cid, None)
                if task and not task.done(): 
                    task.cancel()
                await event.reply("❌ Chat removed from bot control.")
                await event.delete()

            elif command == "start":
                if cid in state.selected:
                    state.running.add(cid)
                    state.auto_reply_mode.add(cid)
                    state.tag_all_mode.add(cid)
                    await event.reply("🚀 All features activated! Auto-reply and Tag-all enabled.")
                else:
                    await event.reply("❌ Use .allow first to select this chat.")
                await event.delete()

            elif command == "stop":
                state.running.discard(cid)
                state.auto_reply_mode.discard(cid)
                task = state.raid_tasks.pop(cid, None)
                if task and not task.done(): 
                    task.cancel()
                await event.reply("⏸️ Features stopped. Use .start to resume.")
                await event.delete()

            elif command == "copy":
                if cid in state.selected:
                    state.copy_mode.add(cid)
                    await event.reply("📝 Copy mode ON")
                else:
                    await event.reply("❌ Use .allow first")
                await event.delete()

            elif command == "tagall":
                if cid in state.selected and cid in state.running:
                    await tag_all_members(client, state, event)
                else:
                    await event.reply("❌ Use .allow and .start first")
                await event.delete()

            elif command == "autoreply":
                if "off" in text:
                    state.auto_reply_mode.discard(cid)
                    await event.reply("🔕 Auto-reply OFF")
                else:
                    state.auto_reply_mode.add(cid)
                    await event.reply("🔔 Auto-reply ON")
                await event.delete()

        except Exception as e:
            logging.error(f"Command error: {e}")

    @client.on(events.NewMessage(outgoing=True, pattern=r'^\.raids+(\d+)$'))
    async def raid_command(event):
        """Enhanced raid command"""
        try:
            n = int(event.pattern_match.group(1))
            n = max(1, min(n, 50))  # Limit to 50 for safety
            
            cid = event.chat_id
            tid, name = await resolve_target(client, event)
            
            if not tid:
                await event.reply("❌ Reply to or mention a user to target!")
                await event.delete()
                return
            
            tag = f"[{name or 'user'}](tg://user?id={tid})"
            old_task = state.raid_tasks.pop(cid, None)
            if old_task and not old_task.done(): 
                old_task.cancel()
            
            task = asyncio.create_task(raid_runner(client, state, event, tag, n))
            state.raid_tasks[cid] = task
            await event.reply(f"🎯 Raid started: {n} messages")
            await event.delete()
            
        except Exception as e:
            logging.error(f"Raid command error: {e}")

async def run_enhanced_client(session_name):
    """Run enhanced client with better error handling"""
    client = TelegramClient(session_name, API_ID, API_HASH)
    state = EnhancedBotState()
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format=f'%(asctime)s - {session_name} - %(levelname)s - %(message)s'
    )
    
    try:
        attach_enhanced_handlers(client, state)
        await client.start()
        me = await client.get_me()
        logging.info(f"Started as {me.first_name} (@{me.username})")
        
        # Print available commands
        print(f"\n🤖 {session_name} is running!")
        print("Available Commands:")
        print(".allow - Select current chat")
        print(".remove - Remove current chat") 
        print(".start - Enable all features")
        print(".stop - Disable features")
        print(".tagall - Tag all members")
        print(".autoreply - Toggle auto-reply")
        print(".copy - Enable copy mode")
        print(".raid N - Raid target user")
        print(".stopraid - Stop raid\n")
        
        await client.run_until_disconnected()
    except Exception as e:
        logging.error(f"Client error: {e}")

async def main():
    """Main function with enhanced session management"""
    print("🚀 Enhanced Telegram Bot Starting...")
    print("=" * 50)
    
    tasks = []
    for session in SESSION_FILES:
        task = asyncio.create_task(run_enhanced_client(session))
        tasks.append(task)
        await asyncio.sleep(2)  # Stagger startup
    
    await asyncio.gather(*tasks, return_exceptions=True)

def create_config_files():
    """Create configuration files if they don't exist"""
    if not os.path.exists('config.json'):
        config = {
            "api_id": "28362425",
            "api_hash": "5e58ea069d62ec34cbd90f275f68f124",
            "sessions": ["user1", "user2", "user3"],
            "auto_reply_messages": AUTO_REPLY_MESSAGES,
            "tag_all_messages": TAG_ALL_MESSAGES,
            "settings": {
                "max_tag_members": 100,
                "auto_reply_delay": 2,
                "cooldown_time": 30
            }
        }
        with open('config.json', 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        print("✅ Created config.json")

if __name__ == "__main__":
    create_config_files()
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Bot stopped by user")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
