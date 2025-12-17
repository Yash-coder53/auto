#!/usr/bin/env python3
import asyncio
import sys
import time
import json
import os
from telethon import TelegramClient, events
from telethon.errors import FloodWaitError
from telethon.tl.functions.channels import GetParticipantRequest
from telethon.tl.types import ChannelParticipantAdmin, ChannelParticipantCreator
import logging
from colorama import init, Fore, Style

# Initialize colorama for colored output
init(autoreset=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format=f'{Fore.CYAN}[%(asctime)s]{Style.RESET_ALL} {Fore.GREEN}%(levelname)s{Style.RESET_ALL}: %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

# Configuration - Your credentials
API_ID = 24633463  # Your API ID
API_HASH = 'a2f7cd31e5017cf4fb84dd6ca2f27809'  # Your API Hash
PHONE_NUMBER = '+1234567890'  # Your phone number with country code
SESSION_NAME = 'tagall_bot'

# Owner ID - Only this user can use owner commands
OWNER_ID = 7862393998

# Files
ALLOWED_CHATS_FILE = 'allowed_chats.json'
SETTINGS_FILE = 'bot_settings.json'
AUTHORIZED_USERS_FILE = 'authorized_users.json'
SUDO_USERS_FILE = 'sudo_users.json'

# Default values
DEFAULT_TAG_LIMIT = 0  # 0 means no limit (tag all)
DEFAULT_DELAY_SECONDS = 2  # Default delay between messages

# Messages dictionary with emojis
MESSAGES = {
    'gm': "🌅 Good Morning {mention}! ☀️ Have a great day! 🌞✨",
    'gn': "🌙 Good Night {mention}! 🌜 Take care and sweet dreams! 💫🛏️",
    'siku': "{mention} "  # Custom message prefix
}

# Global variables
stop_flags = {}
allowed_chats = set()
bot_settings = {}
authorized_users = {}  # chat_id -> set of user_ids
sudo_users = set()  # Global sudo users

def load_allowed_chats():
    """Load allowed chats from file"""
    global allowed_chats
    try:
        if os.path.exists(ALLOWED_CHATS_FILE):
            with open(ALLOWED_CHATS_FILE, 'r') as f:
                data = json.load(f)
                allowed_chats = set(data.get('allowed_chats', []))
                logger.info(f"Loaded {len(allowed_chats)} allowed chats")
    except Exception as e:
        logger.error(f"Error loading allowed chats: {e}")
        allowed_chats = set()

def save_allowed_chats():
    """Save allowed chats to file"""
    try:
        data = {'allowed_chats': list(allowed_chats)}
        with open(ALLOWED_CHATS_FILE, 'w') as f:
            json.dump(data, f)
        logger.info(f"Saved {len(allowed_chats)} allowed chats")
    except Exception as e:
        logger.error(f"Error saving allowed chats: {e}")

def load_authorized_users():
    """Load authorized users from file"""
    global authorized_users
    try:
        if os.path.exists(AUTHORIZED_USERS_FILE):
            with open(AUTHORIZED_USERS_FILE, 'r') as f:
                data = json.load(f)
                # Convert lists back to sets
                authorized_users = {}
                for chat_id_str, user_list in data.items():
                    authorized_users[int(chat_id_str)] = set(user_list)
                logger.info(f"Loaded authorized users for {len(authorized_users)} chats")
    except Exception as e:
        logger.error(f"Error loading authorized users: {e}")
        authorized_users = {}

def save_authorized_users():
    """Save authorized users to file"""
    try:
        # Convert sets to lists for JSON serialization
        data = {}
        for chat_id, user_set in authorized_users.items():
            data[str(chat_id)] = list(user_set)
        
        with open(AUTHORIZED_USERS_FILE, 'w') as f:
            json.dump(data, f)
        logger.info(f"Saved authorized users for {len(authorized_users)} chats")
    except Exception as e:
        logger.error(f"Error saving authorized users: {e}")

def load_sudo_users():
    """Load sudo users from file"""
    global sudo_users
    try:
        if os.path.exists(SUDO_USERS_FILE):
            with open(SUDO_USERS_FILE, 'r') as f:
                data = json.load(f)
                sudo_users = set(data.get('sudo_users', []))
                logger.info(f"Loaded {len(sudo_users)} sudo users")
    except Exception as e:
        logger.error(f"Error loading sudo users: {e}")
        sudo_users = set()

def save_sudo_users():
    """Save sudo users to file"""
    try:
        data = {'sudo_users': list(sudo_users)}
        with open(SUDO_USERS_FILE, 'w') as f:
            json.dump(data, f)
        logger.info(f"Saved {len(sudo_users)} sudo users")
    except Exception as e:
        logger.error(f"Error saving sudo users: {e}")

def load_settings():
    """Load bot settings from file"""
    global bot_settings
    try:
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, 'r') as f:
                bot_settings = json.load(f)
                logger.info(f"Loaded settings: {bot_settings}")
        else:
            # Default settings
            bot_settings = {
                'tag_limit': DEFAULT_TAG_LIMIT,
                'delay_seconds': DEFAULT_DELAY_SECONDS
            }
            save_settings()
    except Exception as e:
        logger.error(f"Error loading settings: {e}")
        bot_settings = {
            'tag_limit': DEFAULT_TAG_LIMIT,
            'delay_seconds': DEFAULT_DELAY_SECONDS
        }

def save_settings():
    """Save bot settings to file"""
    try:
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(bot_settings, f, indent=2)
        logger.info(f"Saved settings: {bot_settings}")
    except Exception as e:
        logger.error(f"Error saving settings: {e}")

def get_chat_setting(chat_id, setting_key, default_value=None):
    """Get setting for a specific chat"""
    chat_key = str(chat_id)
    if 'chat_settings' in bot_settings and chat_key in bot_settings['chat_settings']:
        return bot_settings['chat_settings'][chat_key].get(setting_key, default_value)
    return default_value

def set_chat_setting(chat_id, setting_key, value):
    """Set setting for a specific chat"""
    chat_key = str(chat_id)
    if 'chat_settings' not in bot_settings:
        bot_settings['chat_settings'] = {}
    if chat_key not in bot_settings['chat_settings']:
        bot_settings['chat_settings'][chat_key] = {}
    bot_settings['chat_settings'][chat_key][setting_key] = value
    save_settings()

async def is_owner(event):
    """Check if the user is the owner"""
    try:
        return event.sender_id == OWNER_ID
    except:
        return False

async def is_sudo_user(user_id):
    """Check if user is a sudo user"""
    return user_id in sudo_users

async def is_chat_allowed(chat_id):
    """Check if chat is allowed to use the bot"""
    return chat_id in allowed_chats

async def is_user_authorized(chat_id, user_id):
    """Check if user is authorized to use tagging commands in this chat"""
    # Owner and sudo users are always authorized
    if user_id == OWNER_ID or user_id in sudo_users:
        return True
    
    # Check if user is in authorized list for this chat
    if chat_id in authorized_users:
        return user_id in authorized_users[chat_id]
    
    return False

async def is_admin_or_creator(client, chat_id, user_id):
    """Check if user is admin or creator in the chat"""
    try:
        participant = await client(GetParticipantRequest(chat_id, user_id))
        if isinstance(participant.participant, (ChannelParticipantAdmin, ChannelParticipantCreator)):
            return True
    except Exception as e:
        logger.error(f"Error checking admin status: {e}")
    return False

async def authorize_user(chat_id, user_id):
    """Authorize a user to use tagging commands in a chat"""
    if chat_id not in authorized_users:
        authorized_users[chat_id] = set()
    authorized_users[chat_id].add(user_id)
    save_authorized_users()

async def unauthorize_user(chat_id, user_id):
    """Remove authorization from a user"""
    if chat_id in authorized_users and user_id in authorized_users[chat_id]:
        authorized_users[chat_id].remove(user_id)
        if not authorized_users[chat_id]:  # If empty, remove the chat entry
            del authorized_users[chat_id]
        save_authorized_users()
        return True
    return False

async def add_sudo_user(user_id):
    """Add a user to sudo users"""
    sudo_users.add(user_id)
    save_sudo_users()

async def remove_sudo_user(user_id):
    """Remove a user from sudo users"""
    if user_id in sudo_users:
        sudo_users.remove(user_id)
        save_sudo_users()
        return True
    return False

async def get_all_participants(client, chat):
    """Get all participants from a chat/channel"""
    participants = []
    
    try:
        logger.info(f"Fetching participants from chat...")
        
        # Get chat entity
        chat_entity = await client.get_entity(chat)
        
        # Fetch participants
        async for user in client.iter_participants(chat_entity):
            if not user.bot and not user.deleted and not user.is_self:
                participants.append(user)
                
        logger.info(f"Found {len(participants)} active members")
        return participants
        
    except Exception as e:
        logger.error(f"Error getting participants: {e}")
        return []

async def tag_one_by_one(client, chat_id, message_type, custom_message=""):
    """Tag all members one by one in separate messages"""
    chat = await client.get_entity(chat_id)
    chat_title = chat.title if hasattr(chat, 'title') else "Unknown Chat"
    
    task_id = f"{chat_id}_{time.time()}"
    stop_flags[task_id] = False
    
    try:
        participants = await get_all_participants(client, chat_id)
        
        if not participants:
            await client.send_message(chat_id, "❌ No active members found to tag.")
            return False, 0, 0
        
        total = len(participants)
        success_count = 0
        fail_count = 0
        
        # Get tag limit for this chat
        tag_limit = get_chat_setting(chat_id, 'tag_limit', bot_settings['tag_limit'])
        delay_seconds = get_chat_setting(chat_id, 'delay_seconds', bot_settings['delay_seconds'])
        
        # Apply limit if set
        if tag_limit > 0:
            participants = participants[:tag_limit]
            total = len(participants)
        
        # Send starting message
        start_msg_text = f"🚀 Starting to tag {total} members one by one...\n"
        start_msg_text += f"Type: {message_type.upper()}\n"
        start_msg_text += f"Delay: {delay_seconds} seconds\n"
        
        if tag_limit > 0:
            start_msg_text += f"Limit: {tag_limit} members\n"
        
        start_msg_text += "Use /stopsiku to stop"
        
        start_msg = await client.send_message(chat_id, start_msg_text)
        
        # Process each participant
        for index, user in enumerate(participants, 1):
            # Check if stop flag is set
            if stop_flags.get(task_id, False):
                logger.info(f"{Fore.YELLOW}Tagging stopped by user")
                await client.send_message(chat_id, "⏹️ Tagging stopped by user command!")
                break
            
            try:
                # Create mention
                if user.username:
                    mention = f"@{user.username}"
                    mention_for_message = f"@{user.username}"
                else:
                    name = f"{user.first_name or ''} {user.last_name or ''}".strip()
                    mention = f"[{name}](tg://user?id={user.id})"
                    mention_for_message = f"[{name}](tg://user?id={user.id})"
                
                # Create message based on type
                if message_type == 'siku' and custom_message:
                    # Custom message
                    message = f"{custom_message} {mention_for_message}!"
                elif message_type in MESSAGES:
                    # GM or GN message with emojis
                    message = MESSAGES[message_type].format(mention=mention_for_message)
                else:
                    message = f"👋 {mention_for_message}!"
                
                # Send individual message
                await client.send_message(
                    chat_id,
                    message,
                    parse_mode='md'
                )
                
                success_count += 1
                logger.info(f"{Fore.GREEN}[{index}/{total}] Tagged: {mention}")
                
                # Update status every 10 members
                if index % 10 == 0:
                    status_msg = await client.send_message(
                        chat_id,
                        f"📊 Progress: {index}/{total} members tagged\n"
                        f"✅ Success: {success_count} | ❌ Failed: {fail_count}"
                    )
                    await asyncio.sleep(1)
                    try:
                        await status_msg.delete()
                    except:
                        pass
                
                # Delay between messages
                await asyncio.sleep(delay_seconds)
                    
            except FloodWaitError as e:
                wait_time = e.seconds
                logger.warning(f"{Fore.YELLOW}Flood wait: Sleeping for {wait_time} seconds")
                wait_msg = await client.send_message(chat_id, f"⏸️ Pausing for {wait_time} seconds due to rate limit...")
                await asyncio.sleep(wait_time)
                try:
                    await wait_msg.delete()
                except:
                    pass
                
            except Exception as e:
                fail_count += 1
                logger.error(f"{Fore.RED}Failed to tag user {index}: {e}")
                await asyncio.sleep(delay_seconds * 2)  # Longer delay on error
        
        # Delete start message
        try:
            await start_msg.delete()
        except:
            pass
        
        # Send completion message if not stopped
        if not stop_flags.get(task_id, False):
            completion_msg = f"✅ Tagging Complete!\n\n"
            completion_msg += f"📊 Statistics:\n"
            completion_msg += f"• Total Members: {total}\n"
            completion_msg += f"• Successfully Tagged: {success_count}\n"
            completion_msg += f"• Failed: {fail_count}\n"
            completion_msg += f"• Type: {message_type.upper()}\n"
            completion_msg += f"• Delay: {delay_seconds} seconds\n"
            
            if tag_limit > 0:
                completion_msg += f"• Limit: {tag_limit} members\n"
            
            completion_msg += f"\n🎯 All members tagged individually!"
            
            await client.send_message(chat_id, completion_msg)
        
        # Cleanup
        if task_id in stop_flags:
            del stop_flags[task_id]
            
        return True, success_count, fail_count
        
    except Exception as e:
        logger.error(f"Error in tag_one_by_one: {e}")
        await client.send_message(chat_id, f"❌ Error: {str(e)}")
        
        # Cleanup
        if task_id in stop_flags:
            del stop_flags[task_id]
            
        return False, 0, 0

@events.register(events.NewMessage(pattern='/authsiku'))
async def authsiku_handler(event):
    """Handle /authsiku command - Admin can authorize users (with username or reply)"""
    try:
        # Check if command is in a group/channel
        if not event.is_group and not event.is_channel:
            await event.reply("❌ This command only works in groups and channels!")
            return
        
        # Check if chat is allowed
        if not await is_chat_allowed(event.chat_id):
            await event.reply("❌ This chat is not authorized to use the bot!")
            return
        
        # Check if user is admin, creator, owner, or sudo
        is_admin = await is_admin_or_creator(event.client, event.chat_id, event.sender_id)
        is_sudo = await is_sudo_user(event.sender_id)
        is_owner_user = await is_owner(event)
        
        if not is_admin and not is_sudo and not is_owner_user:
            await event.reply("❌ Only admins, sudo users, and the owner can use this command!")
            return
        
        # Check if replying to a message
        if event.is_reply:
            try:
                replied_msg = await event.get_reply_message()
                user_id = replied_msg.sender_id
                user = await event.client.get_entity(user_id)
                
                await authorize_user(event.chat_id, user_id)
                
                await event.reply(f"✅ User Authorized Successfully!\n\n"
                                f"📝 User Info:\n"
                                f"• Username: @{user.username if user.username else 'N/A'}\n"
                                f"• Name: {user.first_name or ''} {user.last_name or ''}\n"
                                f"• ID: {user.id}\n\n"
                                f"🔓 Now this user can use /siku commands in this chat.")
                
                logger.info(f"Authorized user {user.id} (via reply) in chat {event.chat_id}")
                return
                
            except Exception as e:
                await event.reply(f"❌ Error authorizing replied user: {str(e)}")
                return
        
        # Parse command
        command_text = event.message.text.split()
        
        if len(command_text) == 1:
            # Show authorized users for this chat
            chat_id = event.chat_id
            if chat_id in authorized_users and authorized_users[chat_id]:
                user_list = []
                for user_id in list(authorized_users[chat_id])[:10]:  # Limit to 10 users
                    try:
                        user = await event.client.get_entity(user_id)
                        username = f"@{user.username}" if user.username else user.first_name or "Unknown"
                        user_list.append(f"• {username} (ID: {user_id})")
                    except:
                        user_list.append(f"• Unknown User (ID: {user_id})")
                
                response = f"✅ Authorized Users in this chat ({len(authorized_users[chat_id])}):\n\n"
                response += f"{chr(10).join(user_list)}\n\n"
                response += "📝 Commands:\n"
                response += "/authsiku @username - Authorize user\n"
                response += "/authsiku (reply to user) - Authorize replied user\n"
                response += "/unauthsiku @username - Remove authorization\n"
                response += "/authsiku all - Authorize all current members"
                
                if len(authorized_users[chat_id]) > 10:
                    response += f"\n\n... and {len(authorized_users[chat_id]) - 10} more users"
            else:
                response = "📭 No users are currently authorized in this chat.\n\n"
                response += "📝 Commands:\n"
                response += "/authsiku @username - Authorize user\n"
                response += "/authsiku (reply to user) - Authorize replied user\n"
                response += "/unauthsiku @username - Remove authorization\n"
                response += "/authsiku all - Authorize all current members"
            
            await event.reply(response)
            return
        
        if len(command_text) >= 2:
            if command_text[1].lower() == 'all':
                # Authorize all current members
                try:
                    participants = await get_all_participants(event.client, event.chat_id)
                    count = 0
                    
                    for user in participants:
                        await authorize_user(event.chat_id, user.id)
                        count += 1
                    
                    await event.reply(f"✅ Authorized All Members Successfully!\n\n"
                                    f"📊 Statistics:\n"
                                    f"• Total Members Authorized: {count}\n"
                                    f"• Now they can use /siku commands\n\n"
                                    f"⚠️ Note: This only authorizes current members.\n"
                                    f"New members need separate authorization.")
                    
                    logger.info(f"Authorized {count} users in chat {event.chat_id}")
                    
                except Exception as e:
                    await event.reply(f"❌ Error: {str(e)}")
                    
            elif command_text[1].startswith('@'):
                # Authorize by username
                username = command_text[1][1:]  # Remove @
                try:
                    # Get user by username
                    user = await event.client.get_entity(username)
                    await authorize_user(event.chat_id, user.id)
                    
                    await event.reply(f"✅ User Authorized Successfully!\n\n"
                                    f"📝 User Info:\n"
                                    f"• Username: @{user.username if user.username else 'N/A'}\n"
                                    f"• Name: {user.first_name or ''} {user.last_name or ''}\n"
                                    f"• ID: {user.id}\n\n"
                                    f"🔓 Now @{username} can use /siku commands in this chat.")
                    
                    logger.info(f"Authorized user {user.id} (@{username}) in chat {event.chat_id}")
                    
                except Exception as e:
                    await event.reply(f"❌ User not found or error: {str(e)}")
            
            elif command_text[1].isdigit():
                # Authorize by user ID
                user_id = int(command_text[1])
                try:
                    user = await event.client.get_entity(user_id)
                    await authorize_user(event.chat_id, user.id)
                    
                    await event.reply(f"✅ User Authorized Successfully!\n\n"
                                    f"📝 User Info:\n"
                                    f"• Username: @{user.username if user.username else 'N/A'}\n"
                                    f"• Name: {user.first_name or ''} {user.last_name or ''}\n"
                                    f"• ID: {user.id}\n\n"
                                    f"🔓 Now this user can use /siku commands in this chat.")
                    
                    logger.info(f"Authorized user {user_id} in chat {event.chat_id}")
                    
                except Exception as e:
                    await event.reply(f"❌ User not found or error: {str(e)}")
            
            else:
                await event.reply("❌ Usage: /authsiku @username OR /authsiku user_id OR /authsiku all\n"
                                "OR reply to a user's message with /authsiku")
        
    except Exception as e:
        await event.reply(f"❌ Error: {str(e)}")
        logger.error(f"Error in authsiku_handler: {e}")

@events.register(events.NewMessage(pattern='/unauthsiku'))
async def unauthsiku_handler(event):
    """Handle /unauthsiku command - Admin can remove user authorization"""
    try:
        # Check if command is in a group/channel
        if not event.is_group and not event.is_channel:
            await event.reply("❌ This command only works in groups and channels!")
            return
        
        # Check if chat is allowed
        if not await is_chat_allowed(event.chat_id):
            await event.reply("❌ This chat is not authorized to use the bot!")
            return
        
        # Check if user is admin, creator, owner, or sudo
        is_admin = await is_admin_or_creator(event.client, event.chat_id, event.sender_id)
        is_sudo = await is_sudo_user(event.sender_id)
        is_owner_user = await is_owner(event)
        
        if not is_admin and not is_sudo and not is_owner_user:
            await event.reply("❌ Only admins, sudo users, and the owner can use this command!")
            return
        
        # Check if replying to a message
        if event.is_reply:
            try:
                replied_msg = await event.get_reply_message()
                user_id = replied_msg.sender_id
                user = await event.client.get_entity(user_id)
                
                if await unauthorize_user(event.chat_id, user_id):
                    await event.reply(f"❌ User Authorization Removed!\n\n"
                                    f"📝 User Info:\n"
                                    f"• Username: @{user.username if user.username else 'N/A'}\n"
                                    f"• Name: {user.first_name or ''} {user.last_name or ''}\n"
                                    f"• ID: {user.id}\n\n"
                                    f"🔒 This user can no longer use /siku commands in this chat.")
                else:
                    await event.reply(f"❌ This user is not authorized in this chat.")
                    
                return
                
            except Exception as e:
                await event.reply(f"❌ Error: {str(e)}")
                return
        
        # Parse command
        command_text = event.message.text.split()
        
        if len(command_text) < 2:
            await event.reply("❌ Usage: /unauthsiku @username OR /unauthsiku user_id\n"
                            "OR reply to a user's message with /unauthsiku")
            return
        
        if command_text[1].startswith('@'):
            # Unauth by username
            username = command_text[1][1:]  # Remove @
            try:
                user = await event.client.get_entity(username)
                if await unauthorize_user(event.chat_id, user.id):
                    await event.reply(f"❌ User Authorization Removed!\n\n"
                                    f"📝 User Info:\n"
                                    f"• Username: @{user.username if user.username else 'N/A'}\n"
                                    f"• Name: {user.first_name or ''} {user.last_name or ''}\n"
                                    f"• ID: {user.id}\n\n"
                                    f"🔒 @{username} can no longer use /siku commands in this chat.")
                else:
                    await event.reply(f"❌ User @{username} is not authorized in this chat.")
                    
            except Exception as e:
                await event.reply(f"❌ User not found or error: {str(e)}")
        
        elif command_text[1].isdigit():
            # Unauth by user ID
            user_id = int(command_text[1])
            try:
                user = await event.client.get_entity(user_id)
                if await unauthorize_user(event.chat_id, user.id):
                    await event.reply(f"❌ User Authorization Removed!\n\n"
                                    f"📝 User Info:\n"
                                    f"• Username: @{user.username if user.username else 'N/A'}\n"
                                    f"• Name: {user.first_name or ''} {user.last_name or ''}\n"
                                    f"• ID: {user.id}\n\n"
                                    f"🔒 This user can no longer use /siku commands in this chat.")
                else:
                    await event.reply(f"❌ User with ID {user_id} is not authorized in this chat.")
                    
            except Exception as e:
                await event.reply(f"❌ User not found or error: {str(e)}")
        
        else:
            await event.reply("❌ Usage: /unauthsiku @username OR /unauthsiku user_id\n"
                            "OR reply to a user's message with /unauthsiku")
        
    except Exception as e:
        await event.reply(f"❌ Error: {str(e)}")
        logger.error(f"Error in unauthsiku_handler: {e}")

@events.register(events.NewMessage(pattern='/sudosiku'))
async def sudosiku_handler(event):
    """Handle /sudosiku command - Owner can manage sudo users"""
    try:
        # Check if user is owner
        if not await is_owner(event):
            await event.reply("❌ This command is only available for the owner!")
            return
        
        # Parse command
        command_text = event.message.text.split()
        
        if len(command_text) == 1:
            # Show sudo users
            if sudo_users:
                user_list = []
                for user_id in list(sudo_users)[:20]:  # Limit to 20 users
                    try:
                        user = await event.client.get_entity(user_id)
                        username = f"@{user.username}" if user.username else user.first_name or "Unknown"
                        user_list.append(f"• {username} (ID: {user_id})")
                    except:
                        user_list.append(f"• Unknown User (ID: {user_id})")
                
                response = f"👑 Sudo Users ({len(sudo_users)}):\n\n"
                response += f"{chr(10).join(user_list)}\n\n"
                response += "📝 Commands:\n"
                response += "/sudosiku @username - Add sudo user\n"
                response += "/sudosiku (reply to user) - Add replied user as sudo\n"
                response += "/sudosiku remove @username - Remove sudo user\n"
                response += "/sudosiku remove (reply) - Remove replied user from sudo"
                
                if len(sudo_users) > 20:
                    response += f"\n\n... and {len(sudo_users) - 20} more users"
            else:
                response = "📭 No sudo users currently.\n\n"
                response += "📝 Commands:\n"
                response += "/sudosiku @username - Add sudo user\n"
                response += "/sudosiku (reply to user) - Add replied user as sudo\n"
                response += "/sudosiku remove @username - Remove sudo user\n"
                response += "/sudosiku remove (reply) - Remove replied user from sudo"
            
            await event.reply(response)
            return
        
        # Check if replying to a message
        if event.is_reply:
            try:
                replied_msg = await event.get_reply_message()
                user_id = replied_msg.sender_id
                user = await event.client.get_entity(user_id)
                
                # Check if remove command
                if len(command_text) >= 2 and command_text[1].lower() == 'remove':
                    if await remove_sudo_user(user_id):
                        await event.reply(f"❌ User Removed from Sudo!\n\n"
                                        f"📝 User Info:\n"
                                        f"• Username: @{user.username if user.username else 'N/A'}\n"
                                        f"• Name: {user.first_name or ''} {user.last_name or ''}\n"
                                        f"• ID: {user.id}\n\n"
                                        f"🔒 This user is no longer a sudo user.")
                    else:
                        await event.reply(f"❌ This user is not a sudo user.")
                else:
                    await add_sudo_user(user_id)
                    await event.reply(f"✅ User Added as Sudo!\n\n"
                                    f"📝 User Info:\n"
                                    f"• Username: @{user.username if user.username else 'N/A'}\n"
                                    f"• Name: {user.first_name or ''} {user.last_name or ''}\n"
                                    f"• ID: {user.id}\n\n"
                                    f"👑 This user now has sudo privileges.")
                
                return
                
            except Exception as e:
                await event.reply(f"❌ Error: {str(e)}")
                return
        
        # Handle regular command
        if len(command_text) >= 2:
            if command_text[1].lower() == 'remove' and len(command_text) >= 3:
                # Remove sudo user by username or ID
                target = command_text[2]
                if target.startswith('@'):
                    username = target[1:]
                    try:
                        user = await event.client.get_entity(username)
                        if await remove_sudo_user(user.id):
                            await event.reply(f"❌ User Removed from Sudo!\n\n"
                                            f"📝 User Info:\n"
                                            f"• Username: @{user.username if user.username else 'N/A'}\n"
                                            f"• Name: {user.first_name or ''} {user.last_name or ''}\n"
                                            f"• ID: {user.id}\n\n"
                                            f"🔒 @{username} is no longer a sudo user.")
                        else:
                            await event.reply(f"❌ User @{username} is not a sudo user.")
                    except Exception as e:
                        await event.reply(f"❌ User not found or error: {str(e)}")
                elif target.isdigit():
                    user_id = int(target)
                    try:
                        user = await event.client.get_entity(user_id)
                        if await remove_sudo_user(user_id):
                            await event.reply(f"❌ User Removed from Sudo!\n\n"
                                            f"📝 User Info:\n"
                                            f"• Username: @{user.username if user.username else 'N/A'}\n"
                                            f"• Name: {user.first_name or ''} {user.last_name or ''}\n"
                                            f"• ID: {user.id}\n\n"
                                            f"🔒 This user is no longer a sudo user.")
                        else:
                            await event.reply(f"❌ User with ID {user_id} is not a sudo user.")
                    except Exception as e:
                        await event.reply(f"❌ User not found or error: {str(e)}")
                else:
                    await event.reply("❌ Usage: /sudosiku remove @username OR /sudosiku remove user_id")
            
            elif command_text[1].startswith('@'):
                # Add sudo user by username
                username = command_text[1][1:]
                try:
                    user = await event.client.get_entity(username)
                    await add_sudo_user(user.id)
                    
                    await event.reply(f"✅ User Added as Sudo!\n\n"
                                    f"📝 User Info:\n"
                                    f"• Username: @{user.username if user.username else 'N/A'}\n"
                                    f"• Name: {user.first_name or ''} {user.last_name or ''}\n"
                                    f"• ID: {user.id}\n\n"
                                    f"👑 @{username} now has sudo privileges.")
                    
                except Exception as e:
                    await event.reply(f"❌ User not found or error: {str(e)}")
            
            elif command_text[1].isdigit():
                # Add sudo user by ID
                user_id = int(command_text[1])
                try:
                    user = await event.client.get_entity(user_id)
                    await add_sudo_user(user_id)
                    
                    await event.reply(f"✅ User Added as Sudo!\n\n"
                                    f"📝 User Info:\n"
                                    f"• Username: @{user.username if user.username else 'N/A'}\n"
                                    f"• Name: {user.first_name or ''} {user.last_name or ''}\n"
                                    f"• ID: {user.id}\n\n"
                                    f"👑 This user now has sudo privileges.")
                    
                except Exception as e:
                    await event.reply(f"❌ User not found or error: {str(e)}")
            
            else:
                await event.reply("❌ Usage: /sudosiku @username OR /sudosiku user_id OR /sudosiku (reply)\n"
                                "OR /sudosiku remove @username OR /sudosiku remove user_id")
        
    except Exception as e:
        await event.reply(f"❌ Error: {str(e)}")
        logger.error(f"Error in sudosiku_handler: {e}")

@events.register(events.NewMessage(pattern='^/siku'))
async def siku_handler(event):
    """Handle /siku commands for tagging"""
    try:
        # Check if command is in a group/channel
        if not event.is_group and not event.is_channel:
            await event.reply("❌ This command only works in groups and channels!")
            return
        
        # Check if chat is allowed
        if not await is_chat_allowed(event.chat_id):
            await event.reply("❌ This chat is not authorized to use the bot!\n\n"
                            "👑 Owner/Sudo command:\n"
                            "Use /allow in this chat to authorize it.\n\n"
                            "🔒 Contact the bot owner or sudo user to get access.")
            return
        
        # Check if user is authorized (owner, sudo, or authorized user)
        if not await is_user_authorized(event.chat_id, event.sender_id):
            await event.reply("❌ You are not authorized to use tagging commands!\n\n"
                            "👮 Admin/Sudo Command:\n"
                            "Ask an admin or sudo user to authorize you using:\n"
                            "/authsiku @your_username\n\n"
                            "📝 Only authorized users can use /siku commands.")
            return
        
        # Parse command
        full_text = event.message.text.strip()
        
        # Check if it's just /siku without arguments
        if full_text == '/siku':
            await event.reply("📝 Usage: /siku [type] OR /siku [your message]\n\n"
                            "📌 Types:\n"
                            "• gm - 🌅 Good Morning (with emojis)\n"
                            "• gn - 🌙 Good Night (with emojis)\n\n"
                            "📌 Examples:\n"
                            "/siku gm - Tag with Good Morning\n"
                            "/siku gn - Tag with Good Night\n"
                            "/siku Hello everyone - Tag with custom message")
            return
        
        # Extract the part after /siku
        if ' ' in full_text:
            command_parts = full_text.split(' ', 1)
            argument = command_parts[1].strip()
        else:
            argument = ""
        
        if not argument:
            await event.reply("❌ Please specify a message type or custom message!\n"
                            "Examples: /siku gm, /siku gn, /siku Hello everyone")
            return
        
        # Check if it's gm or gn command
        if argument.lower() in ['gm', 'gn']:
            message_type = argument.lower()
            
            # Handle gm/gn commands
            # Get current settings
            current_limit = get_chat_setting(event.chat_id, 'tag_limit', bot_settings['tag_limit'])
            current_delay = get_chat_setting(event.chat_id, 'delay_seconds', bot_settings['delay_seconds'])
            
            limit_text = f" (Limit: {current_limit} members)" if current_limit > 0 else ""
            delay_text = f" (Delay: {current_delay}s)"
            
            # Get message preview
            if message_type == 'gm':
                preview = "🌅 Good Morning {mention}! ☀️ Have a great day! 🌞✨"
            else:
                preview = "🌙 Good Night {mention}! 🌜 Take care and sweet dreams! 💫🛏️"
            
            # Send confirmation
            confirm_msg = await event.reply(f"🚀 Starting tagging process...\n\n"
                                          f"Type: {message_type.upper()}{limit_text}{delay_text}\n\n"
                                          f"📝 Message Format:\n"
                                          f"{preview}\n\n"
                                          f"⏳ Please wait, this may take some time...")
            
            # Delete the command message
            try:
                await event.delete()
            except:
                pass
            
            # Start tagging process
            asyncio.create_task(tag_one_by_one(event.client, event.chat_id, message_type))
            
            # Delete confirmation after 5 seconds
            await asyncio.sleep(5)
            try:
                await confirm_msg.delete()
            except:
                pass
            
        else:
            # Handle custom message (/siku your message)
            custom_message = argument
            
            # Get current settings
            current_limit = get_chat_setting(event.chat_id, 'tag_limit', bot_settings['tag_limit'])
            current_delay = get_chat_setting(event.chat_id, 'delay_seconds', bot_settings['delay_seconds'])
            
            limit_text = f" (Limit: {current_limit} members)" if current_limit > 0 else ""
            delay_text = f" (Delay: {current_delay}s)"
            
            # Send confirmation
            confirm_msg = await event.reply(f"🚀 Starting tagging process...\n\n"
                                          f"Message: {custom_message[:50]}...{limit_text}{delay_text}\n\n"
                                          f"📝 Format: {custom_message[:30]}... {{mention}}!\n\n"
                                          f"⏳ Please wait, this may take some time...")
            
            # Delete the command message
            try:
                await event.delete()
            except:
                pass
            
            # Start tagging process with custom message
            asyncio.create_task(tag_one_by_one(event.client, event.chat_id, 'siku', custom_message))
            
            # Delete confirmation after 5 seconds
            await asyncio.sleep(5)
            try:
                await confirm_msg.delete()
            except:
                pass
        
    except Exception as e:
        logger.error(f"Error in siku_handler: {e}")

@events.register(events.NewMessage(pattern='/stopsiku'))
async def stopsiku_handler(event):
    """Handle /stopsiku command to stop current tagging"""
    try:
        # Check if command is in a group/channel
        if not event.is_group and not event.is_channel:
            await event.reply("❌ This command only works in groups and channels!")
            return
        
        # Check if chat is allowed
        if not await is_chat_allowed(event.chat_id):
            await event.reply("❌ This chat is not authorized to use the bot!")
            return
        
        # Check if user is authorized
        if not await is_user_authorized(event.chat_id, event.sender_id):
            await event.reply("❌ You are not authorized to use tagging commands!")
            return
        
        chat_id = event.chat_id
        
        # Check if any tagging is active in this chat
        chat_tasks = [tid for tid in stop_flags.keys() if str(chat_id) in tid]
        
        if not chat_tasks:
            await event.reply("❌ No active tagging process found in this chat!")
            return
        
        # Set stop flag for all tasks in this chat
        for task_id in chat_tasks:
            stop_flags[task_id] = True
        
        # Delete the command message
        try:
            await event.delete()
        except:
            pass
        
        # Send stop confirmation
        stop_msg = await event.reply("🛑 Stopping tagging process...")
        await asyncio.sleep(2)
        try:
            await stop_msg.delete()
        except:
            pass
        
    except Exception as e:
        logger.error(f"Error in stopsiku_handler: {e}")

@events.register(events.NewMessage(pattern='/limit'))
async def limit_handler(event):
    """Handle /limit command - Set tag limit for this chat"""
    try:
        # Check if user is admin, creator, owner, or sudo
        is_admin = await is_admin_or_creator(event.client, event.chat_id, event.sender_id)
        is_sudo = await is_sudo_user(event.sender_id)
        is_owner_user = await is_owner(event)
        
        if not is_admin and not is_sudo and not is_owner_user:
            await event.reply("❌ Only admins, sudo users, and the owner can use this command!")
            return
        
        # Check if command is in a group/channel
        if not event.is_group and not event.is_channel:
            await event.reply("❌ This command only works in groups and channels!")
            return
        
        # Parse command
        command_text = event.message.text.split()
        
        if len(command_text) == 1:
            # Show current limit
            current_limit = get_chat_setting(event.chat_id, 'tag_limit', bot_settings['tag_limit'])
            current_delay = get_chat_setting(event.chat_id, 'delay_seconds', bot_settings['delay_seconds'])
            
            await event.reply(f"📊 Current Settings for this Chat:\n\n"
                            f"• Tag Limit: {current_limit if current_limit > 0 else 'No limit (tag all)'}\n"
                            f"• Delay: {current_delay} seconds between messages\n\n"
                            f"📝 Usage:\n"
                            f"/limit [number] - Set max members to tag (0 for no limit)\n"
                            f"/limit delay [seconds] - Set delay between messages")
            return
        
        if len(command_text) >= 2:
            if command_text[1].lower() == 'delay':
                # Set delay
                if len(command_text) >= 3:
                    try:
                        delay = int(command_text[2])
                        if delay < 1 or delay > 10:
                            await event.reply("❌ Delay must be between 1 and 10 seconds!")
                            return
                        
                        set_chat_setting(event.chat_id, 'delay_seconds', delay)
                        
                        # Get chat info
                        chat = await event.client.get_entity(event.chat_id)
                        chat_title = chat.title if hasattr(chat, 'title') else "Private Chat"
                        
                        await event.reply(f"✅ Delay Updated Successfully!\n\n"
                                        f"📝 Chat: {chat_title}\n"
                                        f"🕐 New Delay: {delay} seconds\n"
                                        f"⏰ Between each message\n\n"
                                        f"⚠️ Note: Too short delay may trigger flood limits!")
                        
                        logger.info(f"Set delay to {delay} seconds for chat {event.chat_id}")
                        
                    except ValueError:
                        await event.reply("❌ Invalid delay value! Please enter a number between 1-10.")
                else:
                    await event.reply("❌ Usage: /limit delay [seconds]")
            else:
                # Set tag limit
                try:
                    limit = int(command_text[1])
                    if limit < 0 or limit > 1000:
                        await event.reply("❌ Limit must be between 0 and 1000! (0 = no limit)")
                        return
                    
                    set_chat_setting(event.chat_id, 'tag_limit', limit)
                    
                    # Get chat info
                    chat = await event.client.get_entity(event.chat_id)
                    chat_title = chat.title if hasattr(chat, 'title') else "Private Chat"
                    
                    if limit == 0:
                        limit_text = "No limit (will tag all members)"
                    else:
                        limit_text = f"Max {limit} members"
                    
                    await event.reply(f"✅ Tag Limit Updated Successfully!\n\n"
                                    f"📝 Chat: {chat_title}\n"
                                    f"🎯 New Limit: {limit_text}\n"
                                    f"⏰ Delay: {get_chat_setting(event.chat_id, 'delay_seconds', bot_settings['delay_seconds'])} seconds\n\n"
                                    f"⚠️ Note: This only affects future tagging commands.")
                    
                    logger.info(f"Set tag limit to {limit} for chat {event.chat_id}")
                    
                except ValueError:
                    await event.reply("❌ Invalid limit value! Please enter a number between 0-1000.")
        
    except Exception as e:
        await event.reply(f"❌ Error: {str(e)}")
        logger.error(f"Error in limit_handler: {e}")

@events.register(events.NewMessage(pattern='/allow'))
async def allow_handler(event):
    """Handle /allow command - Only owner and sudo can use"""
    try:
        # Check if user is owner or sudo
        if not await is_owner(event) and not await is_sudo_user(event.sender_id):
            await event.reply("❌ This command is only available for the owner and sudo users!")
            return
        
        # Check if command is in a group/channel
        if not event.is_group and not event.is_channel:
            await event.reply("❌ This command only works in groups and channels!")
            return
        
        # Add chat to allowed list
        chat_id = event.chat_id
        allowed_chats.add(chat_id)
        save_allowed_chats()
        
        # Get chat info
        chat = await event.client.get_entity(chat_id)
        chat_title = chat.title if hasattr(chat, 'title') else "Private Chat"
        
        # Get current settings for this chat
        current_limit = get_chat_setting(chat_id, 'tag_limit', bot_settings['tag_limit'])
        current_delay = get_chat_setting(chat_id, 'delay_seconds', bot_settings['delay_seconds'])
        
        limit_text = f"{current_limit} members" if current_limit > 0 else "No limit (tag all)"
        
        await event.reply(f"✅ Chat Added Successfully!\n\n"
                        f"📝 Chat Info:\n"
                        f"• Title: {chat_title}\n"
                        f"• ID: {chat_id}\n"
                        f"• Allowed: ✅\n\n"
                        f"⚙️ Current Settings:\n"
                        f"• Tag Limit: {limit_text}\n"
                        f"• Delay: {current_delay} seconds\n\n"
                        f"👮 Admin/Sudo Commands:\n"
                        f"• /authsiku @username - Authorize user for /siku\n"
                        f"• /unauthsiku @username - Remove authorization\n"
                        f"• /limit [number] - Set tag limit\n"
                        f"• /limit delay [seconds] - Set delay\n\n"
                        f"🤖 User Commands (after authorization):\n"
                        f"• /siku gm - 🌅 Good Morning tagging\n"
                        f"• /siku gn - 🌙 Good Night tagging\n"
                        f"• /siku [message] - 📢 Custom message\n"
                        f"• /stopsiku - 🛑 Stop tagging")
        
        logger.info(f"Added chat {chat_id} ({chat_title}) to allowed list")
        
    except Exception as e:
        await event.reply(f"❌ Error: {str(e)}")
        logger.error(f"Error in allow_handler: {e}")

@events.register(events.NewMessage(pattern='/disallow'))
async def disallow_handler(event):
    """Handle /disallow command - Only owner and sudo can use"""
    try:
        # Check if user is owner or sudo
        if not await is_owner(event) and not await is_sudo_user(event.sender_id):
            await event.reply("❌ This command is only available for the owner and sudo users!")
            return
        
        # Check if command is in a group/channel
        if not event.is_group and not event.is_channel:
            await event.reply("❌ This command only works in groups and channels!")
            return
        
        # Remove chat from allowed list
        chat_id = event.chat_id
        if chat_id in allowed_chats:
            allowed_chats.remove(chat_id)
            save_allowed_chats()
            
            # Get chat info
            chat = await event.client.get_entity(chat_id)
            chat_title = chat.title if hasattr(chat, 'title') else "Private Chat"
            
            await event.reply(f"❌ Chat Removed Successfully!\n\n"
                            f"📝 Chat Info:\n"
                            f"• Title: {chat_title}\n"
                            f"• ID: {chat_id}\n"
                            f"• Allowed: ❌\n\n"
                            f"This chat can no longer use the bot.")
            
            logger.info(f"Removed chat {chat_id} ({chat_title}) from allowed list")
        else:
            await event.reply("❌ This chat is not in the allowed list!")
            
    except Exception as e:
        await event.reply(f"❌ Error: {str(e)}")
        logger.error(f"Error in disallow_handler: {e}")

@events.register(events.NewMessage(pattern='/sikustatus'))
async def sikustatus_handler(event):
    """Show siku bot status and help"""
    try:
        # Check if chat is allowed
        is_allowed = await is_chat_allowed(event.chat_id)
        is_owner_user = await is_owner(event)
        is_sudo = await is_sudo_user(event.sender_id)
        is_admin = await is_admin_or_creator(event.client, event.chat_id, event.sender_id)
        is_authorized = await is_user_authorized(event.chat_id, event.sender_id)
        
        user_type = "Regular User"
        if is_owner_user:
            user_type = "👑 Owner"
        elif is_sudo:
            user_type = "👑 Sudo User"
        elif is_admin:
            user_type = "👮 Admin"
        elif is_authorized:
            user_type = "✅ Authorized User"
        
        if is_owner_user or is_sudo:
            help_text = f"🤖 Siku TagAll Bot - One by One Tagging\n\n" \
                       f"👑 Owner/Sudo Commands:\n" \
                       f"• /allow - Authorize this chat\n" \
                       f"• /disallow - Remove authorization\n" \
                       f"• /allowed - List authorized chats\n" \
                       f"• /sudosiku - Manage sudo users\n" \
                       f"• /limit [number] - Set tag limit for this chat\n" \
                       f"• /limit delay [seconds] - Set delay for this chat\n\n" \
                       f"👮 Admin/Sudo Commands (in allowed chats):\n" \
                       f"• /authsiku @username - Authorize user for /siku\n" \
                       f"• /unauthsiku @username - Remove authorization\n" \
                       f"• /authsiku all - Authorize all current members\n" \
                       f"• /limit - Set tag limit/delay\n\n" \
                       f"🤖 User Commands (after authorization):\n" \
                       f"• /siku gm - 🌅 Good Morning tagging\n" \
                       f"• /siku gn - 🌙 Good Night tagging\n" \
                       f"• /siku [message] - 📢 Custom message tagging\n" \
                       f"• /stopsiku - 🛑 Stop current tagging process\n" \
                       f"• /sikustatus - Show this help\n\n" \
                       f"⚙️ Current Chat Status:\n" \
                       f"• Chat Authorized: {'✅' if is_allowed else '❌'}\n" \
                       f"• Your Status: {user_type}\n" \
                       f"• You are Authorized: {'✅' if is_authorized else '❌'}\n" \
                       f"• Tag Limit: {get_chat_setting(event.chat_id, 'tag_limit', bot_settings['tag_limit']) if get_chat_setting(event.chat_id, 'tag_limit', bot_settings['tag_limit']) > 0 else 'No limit'}\n" \
                       f"• Delay: {get_chat_setting(event.chat_id, 'delay_seconds', bot_settings['delay_seconds'])} seconds\n\n" \
                       f"📝 Message Formats:\n" \
                       f"• GM: 🌅 Good Morning {{mention}}! ☀️ Have a great day! 🌞✨\n" \
                       f"• GN: 🌙 Good Night {{mention}}! 🌜 Take care and sweet dreams! 💫🛏️\n\n" \
                       f"⚠️ Note: Use responsibly! Too frequent use may trigger Telegram limits."
        elif is_admin and is_allowed:
            help_text = f"🤖 Siku TagAll Bot - One by One Tagging\n\n" \
                       f"👮 Admin Commands:\n" \
                       f"• /authsiku @username - Authorize user for /siku\n" \
                       f"• /unauthsiku @username - Remove authorization\n" \
                       f"• /authsiku all - Authorize all current members\n" \
                       f"• /limit [number] - Set tag limit\n" \
                       f"• /limit delay [seconds] - Set delay\n\n" \
                       f"🤖 User Commands (after authorization):\n" \
                       f"• /siku gm - 🌅 Good Morning tagging\n" \
                       f"• /siku gn - 🌙 Good Night tagging\n" \
                       f"• /siku [message] - 📢 Custom message tagging\n" \
                       f"• /stopsiku - 🛑 Stop current tagging process\n" \
                       f"• /sikustatus - Show this help\n\n" \
                       f"⚙️ Current Chat Status:\n" \
                       f"• Chat Authorized: ✅\n" \
                       f"• Your Status: {user_type}\n" \
                       f"• You are Authorized: {'✅' if is_authorized else '❌ (Ask another admin to /authsiku you)'}\n" \
                       f"• Tag Limit: {get_chat_setting(event.chat_id, 'tag_limit', bot_settings['tag_limit']) if get_chat_setting(event.chat_id, 'tag_limit', bot_settings['tag_limit']) > 0 else 'No limit'}\n" \
                       f"• Delay: {get_chat_setting(event.chat_id, 'delay_seconds', bot_settings['delay_seconds'])} seconds\n\n" \
                       f"📝 Message Formats:\n" \
                       f"• GM: 🌅 Good Morning {{mention}}! ☀️ Have a great day! 🌞✨\n" \
                       f"• GN: 🌙 Good Night {{mention}}! 🌜 Take care and sweet dreams! 💫🛏️\n\n" \
                       f"⚠️ Note: Use responsibly! Too frequent use may trigger Telegram limits."
        elif is_authorized:
            current_limit = get_chat_setting(event.chat_id, 'tag_limit', bot_settings['tag_limit'])
            current_delay = get_chat_setting(event.chat_id, 'delay_seconds', bot_settings['delay_seconds'])
            
            help_text = f"🤖 Siku TagAll Bot - One by One Tagging\n\n" \
                       f"📋 Your Commands:\n" \
                       f"• /siku gm - 🌅 Good Morning tagging\n" \
                       f"• /siku gn - 🌙 Good Night tagging\n" \
                       f"• /siku [message] - 📢 Custom message tagging\n" \
                       f"• /stopsiku - 🛑 Stop current tagging process\n" \
                       f"• /sikustatus - Show this help\n\n" \
                       f"⚙️ Current Settings:\n" \
                       f"• Tag Limit: {current_limit if current_limit > 0 else 'No limit (tag all)'}\n" \
                       f"• Delay: {current_delay} seconds between messages\n\n" \
                       f"📝 Message Formats:\n" \
                       f"• GM: 🌅 Good Morning {{mention}}! ☀️ Have a great day! 🌞✨\n" \
                       f"• GN: 🌙 Good Night {{mention}}! 🌜 Take care and sweet dreams! 💫🛏️\n\n" \
                       f"🎯 Features:\n" \
                       f"• Tags members one by one in separate messages\n" \
                       f"• Custom messages with /siku command\n" \
                       f"• Stop tagging anytime with /stopsiku\n" \
                       f"• Smart rate limiting\n\n" \
                       f"⚠️ Note: Use responsibly! Too frequent use may trigger Telegram limits."
        elif is_allowed:
            help_text = f"🤖 Siku TagAll Bot - One by One Tagging\n\n" \
                       f"❌ You are not authorized to use /siku commands!\n\n" \
                       f"👮 Ask an admin or sudo user to authorize you using:\n" \
                       f"/authsiku @your_username\n\n" \
                       f"📋 Commands for authorized users:\n" \
                       f"• /siku gm - 🌅 Good Morning tagging\n" \
                       f"• /siku gn - 🌙 Good Night tagging\n" \
                       f"• /siku [message] - 📢 Custom message\n" \
                       f"• /stopsiku - 🛑 Stop tagging\n" \
                       f"• /sikustatus - Show help"
        else:
            help_text = f"🤖 Siku TagAll Bot - One by One Tagging\n\n" \
                       f"❌ This chat is not authorized to use the bot!\n\n" \
                       f"👑 Owner ID: {OWNER_ID}\n\n" \
                       f"🔒 To use this bot in your group:\n" \
                       f"1. Add me to your group\n" \
                       f"2. Ask the owner or sudo user to use /allow in your group\n" \
                       f"3. Admins/sudo can then authorize users with /authsiku\n" \
                       f"4. Authorized users can use /siku commands"
        
        await event.reply(help_text)
        
    except Exception as e:
        logger.error(f"Error in sikustatus_handler: {e}")

@events.register(events.NewMessage(pattern='/start'))
async def start_handler(event):
    """Handle /start command"""
    try:
        # Check user status
        is_owner_user = await is_owner(event)
        is_sudo = await is_sudo_user(event.sender_id)
        
        if is_owner_user:
            welcome_msg = f"👑 Welcome Owner!\n\n" \
                         f"Your ID: {OWNER_ID}\n" \
                         f"Authorized Chats: {len(allowed_chats)}\n" \
                         f"Sudo Users: {len(sudo_users)}\n\n" \
                         f"📋 Owner Commands:\n" \
                         f"• /allow - Authorize current chat\n" \
                         f"• /disallow - Remove authorization\n" \
                         f"• /allowed - List authorized chats\n" \
                         f"• /sudosiku - Manage sudo users\n" \
                         f"• /limit [number] - Set tag limit\n" \
                         f"• /limit delay [seconds] - Set delay\n\n" \
                         f"🤖 User Commands (after authorization):\n" \
                         f"• /siku gm - 🌅 Good Morning tagging\n" \
                         f"• /siku gn - 🌙 Good Night tagging\n" \
                         f"• /siku [message] - 📢 Custom message\n" \
                         f"• /stopsiku - 🛑 Stop tagging\n" \
                         f"• /sikustatus - Show help\n\n" \
                         f"📝 Message Formats:\n" \
                         f"• GM: 🌅 Good Morning {{mention}}! ☀️ Have a great day! 🌞✨\n" \
                         f"• GN: 🌙 Good Night {{mention}}! 🌜 Take care and sweet dreams! 💫🛏️"
        elif is_sudo:
            welcome_msg = f"👑 Welcome Sudo User!\n\n" \
                         f"Your ID: {event.sender_id}\n" \
                         f"Authorized Chats: {len(allowed_chats)}\n\n" \
                         f"📋 Sudo Commands:\n" \
                         f"• /allow - Authorize current chat\n" \
                         f"• /disallow - Remove authorization\n" \
                         f"• /authsiku - Authorize users for /siku\n" \
                         f"• /limit [number] - Set tag limit\n" \
                         f"• /limit delay [seconds] - Set delay\n\n" \
                         f"🤖 User Commands (after authorization):\n" \
                         f"• /siku gm - 🌅 Good Morning tagging\n" \
                         f"• /siku gn - 🌙 Good Night tagging\n" \
                         f"• /siku [message] - 📢 Custom message\n" \
                         f"• /stopsiku - 🛑 Stop tagging\n" \
                         f"• /sikustatus - Show help\n\n" \
                         f"📝 Message Formats:\n" \
                         f"• GM: 🌅 Good Morning {{mention}}! ☀️ Have a great day! 🌞✨\n" \
                         f"• GN: 🌙 Good Night {{mention}}! 🌜 Take care and sweet dreams! 💫🛏️"
        else:
            welcome_msg = f"🤖 Welcome to Siku TagAll Bot!\n\n" \
                         f"This bot tags all members one by one in separate messages with beautiful emojis! ✨\n\n" \
                         f"👑 Owner ID: {OWNER_ID}\n\n" \
                         f"🔒 To use this bot in your group:\n" \
                         f"1. Add me to your group\n" \
                         f"2. Ask the owner or sudo user to use /allow in your group\n" \
                         f"3. Admins/sudo can authorize users with /authsiku\n" \
                         f"4. Authorized users can use /siku commands\n\n" \
                         f"📋 Commands for authorized users:\n" \
                         f"• /siku gm - 🌅 Good Morning tagging\n" \
                         f"• /siku gn - 🌙 Good Night tagging\n" \
                         f"• /siku [message] - 📢 Custom message\n" \
                         f"• /stopsiku - 🛑 Stop tagging\n" \
                         f"• /sikustatus - Show help\n\n" \
                         f"📝 Message Formats:\n" \
                         f"• GM: 🌅 Good Morning {{mention}}! ☀️ Have a great day! 🌞✨\n" \
                         f"• GN: 🌙 Good Night {{mention}}! 🌜 Take care and sweet dreams! 💫🛏️"
        
        await event.reply(welcome_msg)
        
    except Exception as e:
        logger.error(f"Error in start_handler: {e}")

@events.register(events.NewMessage(pattern='/allowed'))
async def allowed_handler(event):
    """Show list of allowed chats - Only owner and sudo can use"""
    try:
        # Check if user is owner or sudo
        if not await is_owner(event) and not await is_sudo_user(event.sender_id):
            await event.reply("❌ This command is only available for the owner and sudo users!")
            return
        
        if not allowed_chats:
            await event.reply("📭 No chats are currently allowed.")
            return
        
        # Get chat info for each allowed chat
        chat_list = []
        for chat_id in list(allowed_chats)[:20]:  # Limit to 20 chats
            try:
                chat = await event.client.get_entity(chat_id)
                title = chat.title if hasattr(chat, 'title') else f"Private Chat ({chat_id})"
                
                # Get settings for this chat
                limit = get_chat_setting(chat_id, 'tag_limit', bot_settings['tag_limit'])
                delay = get_chat_setting(chat_id, 'delay_seconds', bot_settings['delay_seconds'])
                
                # Get authorized users count
                auth_count = len(authorized_users.get(chat_id, set()))
                
                limit_text = f"L:{limit}" if limit > 0 else "L:∞"
                chat_list.append(f"• {title} (ID: {chat_id}) [{limit_text}, D:{delay}s, Auth:{auth_count}]")
            except:
                chat_list.append(f"• Unknown Chat (ID: {chat_id})")
        
        response = f"✅ Allowed Chats ({len(allowed_chats)}):\n\n"
        response += f"{chr(10).join(chat_list)}\n\n"
        response += "📝 Legend: L=Limit, D=Delay(s), ∞=No limit, Auth=Authorized users"
        
        if len(allowed_chats) > 20:
            response += f"\n\n... and {len(allowed_chats) - 20} more chats"
        
        await event.reply(response)
        
    except Exception as e:
        await event.reply(f"❌ Error: {str(e)}")
        logger.error(f"Error in allowed_handler: {e}")

@events.register(events.NewMessage(pattern='/clear'))
async def clear_handler(event):
    """Clear allowed chats list - Only owner can use"""
    try:
        # Check if user is owner
        if not await is_owner(event):
            await event.reply("❌ This command is only available for the owner!")
            return
        
        global allowed_chats
        count = len(allowed_chats)
        allowed_chats.clear()
        save_allowed_chats()
        
        await event.reply(f"🗑️ Cleared All Authorized Chats\n\n"
                        f"✅ Removed {count} chats from allowed list.\n\n"
                        f"All chats are now unauthorized.\n"
                        f"Use /allow to authorize chats again.")
        
        logger.info(f"Cleared {count} allowed chats")
        
    except Exception as e:
        await event.reply(f"❌ Error: {str(e)}")
        logger.error(f"Error in clear_handler: {e}")

async def main():
    """Main function to run the client"""
    # Load allowed chats
    load_allowed_chats()
    
    # Load authorized users
    load_authorized_users()
    
    # Load sudo users
    load_sudo_users()
    
    # Load settings
    load_settings()
    
    print(f"""{Fore.CYAN}
╔══════════════════════════════════════╗
║        SIKU TAGALL BOT               ║
║     Complete All-in-One Solution     ║
║         Owner ID: {OWNER_ID}          ║
║      API ID: {API_ID}                 ║
╚══════════════════════════════════════╝
{Style.RESET_ALL}""")
    
    client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
    
    # Register event handlers
    client.add_event_handler(start_handler)
    client.add_event_handler(allow_handler)
    client.add_event_handler(disallow_handler)
    client.add_event_handler(allowed_handler)
    client.add_event_handler(siku_handler)
    client.add_event_handler(stopsiku_handler)
    client.add_event_handler(sikustatus_handler)
    client.add_event_handler(limit_handler)
    client.add_event_handler(authsiku_handler)
    client.add_event_handler(unauthsiku_handler)
    client.add_event_handler(sudosiku_handler)
    client.add_event_handler(clear_handler)
    
    try:
        # Connect and start
        await client.start(phone=PHONE_NUMBER)
        
        # Get user info
        me = await client.get_me()
        print(f"\n{Fore.GREEN}✓ Logged in as: {me.first_name} (@{me.username})")
        print(f"{Fore.YELLOW}⚠ Owner ID: {OWNER_ID}")
        print(f"{Fore.BLUE}📊 Authorized Chats: {len(allowed_chats)}")
        print(f"{Fore.MAGENTA}👑 Sudo Users: {len(sudo_users)}")
        print(f"{Fore.CYAN}⚙️ Default Delay: {bot_settings['delay_seconds']} seconds")
        print(f"{Fore.CYAN}🎯 Default Limit: {bot_settings['tag_limit'] if bot_settings['tag_limit'] > 0 else 'No limit'}")
        
        # Show message formats
        print(f"\n{Fore.MAGENTA}📝 Message Formats:")
        print(f"  {Fore.GREEN}GM: {MESSAGES['gm']}")
        print(f"  {Fore.BLUE}GN: {MESSAGES['gn']}")
        
        # Show owner commands
        print(f"\n{Fore.CYAN}👑 Owner Commands:")
        print(f"  {Fore.GREEN}/allow       {Fore.WHITE}- Authorize current chat")
        print(f"  {Fore.RED}/disallow    {Fore.WHITE}- Remove authorization")
        print(f"  {Fore.CYAN}/allowed     {Fore.WHITE}- List authorized chats")
        print(f"  {Fore.YELLOW}/sudosiku    {Fore.WHITE}- Manage sudo users")
        print(f"  {Fore.YELLOW}/clear       {Fore.WHITE}- Clear all authorized chats")
        
        # Show admin/sudo commands
        print(f"\n{Fore.YELLOW}👮 Admin/Sudo Commands (in allowed chats):")
        print(f"  {Fore.GREEN}/authsiku    {Fore.WHITE}- Authorize user (username or reply)")
        print(f"  {Fore.RED}/unauthsiku  {Fore.WHITE}- Remove authorization")
        print(f"  {Fore.GREEN}/limit       {Fore.WHITE}- Set tag limit/delay")
        
        # Show user commands
        print(f"\n{Fore.CYAN}🤖 User Commands (after authorization):")
        print(f"  {Fore.GREEN}/siku gm     {Fore.WHITE}- 🌅 Good Morning tagging")
        print(f"  {Fore.GREEN}/siku gn     {Fore.WHITE}- 🌙 Good Night tagging")
        print(f"  {Fore.GREEN}/siku [msg]  {Fore.WHITE}- 📢 Custom message tagging")
        print(f"  {Fore.RED}/stopsiku    {Fore.WHITE}- 🛑 Stop current tagging")
        print(f"  {Fore.CYAN}/sikustatus  {Fore.WHITE}- Show help")
        
        print(f"\n{Fore.MAGENTA}⏰ Default delay: {bot_settings['delay_seconds']} seconds between messages")
        print(f"{Fore.YELLOW}🔒 Three-level authorization: Owner → Sudo → Admin → Users")
        
        # Keep running
        print(f"\n{Fore.GREEN}✅ Bot is running! Press Ctrl+C to stop.")
        await client.run_until_disconnected()
        
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}⚠ Bot stopped by user")
    except Exception as e:
        print(f"\n{Fore.RED}✗ Error: {e}")
    finally:
        # Cleanup
        stop_flags.clear()
        save_allowed_chats()
        save_authorized_users()
        save_sudo_users()
        await client.disconnect()
        print(f"{Fore.CYAN}👋 Goodbye!")

if __name__ == '__main__':
    asyncio.run(main())
