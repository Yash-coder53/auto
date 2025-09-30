"""
Message templates for Telegram Auto Reply & Tag All Bot
Organized by category and functionality
"""

# =============================================
# AUTO REPLY MESSAGES
# =============================================

AUTO_REPLY_MESSAGES = [
    # Friendly & Casual
    "Hello! Thanks for your message! 👋",
    "Hi there! I'll get back to you soon. ⏳",
    "Hey! Thanks for reaching out! 📱",
    "Hello! Your message has been received. ✅",
    "Hi! I'll respond properly when I'm free. 🕒",
    "Thanks for your message! I'll reply shortly. ✨",
    "Hey there! Got your message. Talk soon! 💬",
    
    # Professional
    "Thank you for your message. I will respond as soon as possible.",
    "Your message has been received. I'll get back to you shortly.",
    "Thanks for contacting me. I'll reply when available.",
    "Message received. I appreciate your patience.",
    
    # Fun & Creative
    "🎯 Message received! I'll shoot back a reply soon!",
    "🚀 Your message has launched! I'll orbit back with a response!",
    "📬 Message delivered! Preparing response...",
    "💫 Got your cosmic message! Sending reply soon!",
    "🎉 Thanks for the message! Celebration reply incoming!",
    
    # Emoji Focused
    "👋 😊 📱 ✅",
    "💬 ✨ ⏰ 🎯",
    "🚀 💫 🌟 📲",
    
    # Multi-language
    "Hola! Gracias por tu mensaje. 👋",
    "Bonjour! Merci pour votre message. 🇫🇷",
    "Hallo! Danke für deine Nachricht. 🇩🇪",
    "Ciao! Grazie per il tuo messaggio. 🇮🇹",
    "你好！谢谢你的消息。 🇨🇳",
]

# =============================================
# TAG ALL MESSAGES & PREFIXES
# =============================================

TAG_ALL_PREFIXES = [
    "📢 **Attention Everyone!** \n\n",
    "👋 **Hey everyone!** \n\n", 
    "🚨 **Important Notice!** \n\n",
    "📣 **Announcement!** \n\n",
    "🎯 **Attention All Members!** \n\n",
    "🌟 **Hello Friends!** \n\n",
    "⚡ **Quick Announcement!** \n\n",
    "🎉 **Hey Everyone!** \n\n",
    "📢 **Group Announcement!** \n\n",
    "👥 **Calling All Members!** \n\n",
]

TAG_ALL_SUFFIXES = [
    "\n\n✅ **Tagged {count} members!**",
    "\n\n👆 **Everyone has been notified!**",
    "\n\n🎯 **All members tagged successfully!**",
    "\n\n📢 **Message broadcasted to all!**",
    "\n\n🌟 **Spread the word!**",
    "\n\n💫 **Everyone has been mentioned!**",
]

# =============================================
# RAID & TARGET MESSAGES
# =============================================

RAID_MESSAGES = [
    "Hey! Just checking in! 👋",
    "Hello there! 👀",
    "What's up? 💬",
    "How are you doing? 😊",
    "Thinking of you! 💫",
    "Sending good vibes! 🌟",
    "Hope you're having a great day! ☀️",
    "Just wanted to say hi! 🎯",
    "You're awesome! 🚀",
    "Keep shining! ✨",
]

# =============================================
# COPY MODE MESSAGES
# =============================================

COPY_PREFIXES = [
    "👀 ",
    "📝 ",
    "🔁 ",
    "💬 ",
    "🎯 ",
    "👆 ",
    "👉 ",
]

# =============================================
# ERROR & SYSTEM MESSAGES
# =============================================

ERROR_MESSAGES = {
    "no_members": "❌ No members found to tag!",
    "no_permission": "❌ I need admin rights to see all members!",
    "not_group": "❌ Tag all works only in groups and channels!",
    "cooldown": "⏳ Please wait 5 minutes before using tag all again!",
    "generic_error": "❌ Error processing your request!",
    "flood_wait": "⏰ Flood limit exceeded. Please wait...",
}

SUCCESS_MESSAGES = {
    "tag_success": "✅ Successfully tagged {count} members!",
    "auto_reply_on": "🔔 Auto-reply activated!",
    "auto_reply_off": "🔕 Auto-reply deactivated!",
    "copy_on": "📝 Copy mode activated!",
    "copy_off": "📝 Copy mode deactivated!",
    "raid_start": "🎯 Raid started with {count} messages!",
    "raid_stop": "🛑 Raid stopped!",
}

# =============================================
# COMMAND RESPONSES
# =============================================

COMMAND_RESPONSES = {
    "allow": "✅ Chat selected! Use .start to enable features.",
    "remove": "❌ Chat removed from bot control.",
    "start": "🚀 All features activated! Auto-reply and Tag-all enabled.",
    "stop": "⏸️ Features stopped. Use .start to resume.",
    "copy_on": "📝 Copy mode ON",
    "copy_off": "📝 Copy mode OFF",
    "autoreply_on": "🔔 Auto-reply ON", 
    "autoreply_off": "🔕 Auto-reply OFF",
    "need_allow": "❌ Use .allow first to select this chat.",
}

# =============================================
# THEMED MESSAGE SETS
# =============================================

THEMED_MESSAGES = {
    "business": [
        "Thank you for your inquiry. We'll respond shortly.",
        "Your message has been received by our team.",
        "Thanks for contacting us. We'll get back to you soon.",
        "Message received. Our team will respond promptly.",
    ],
    
    "friendly": [
        "Hey! Thanks for the message! 😊",
        "Hi there! I'll reply as soon as I can! 👋",
        "Hello! Got your message - talk soon! 💬",
        "Hey! Appreciate you reaching out! ✨",
    ],
    
    "funny": [
        "Message received! My human is currently busy being awesome! 🦸",
        "Your message has entered the queue! Currently serving: awesomeness! 🎯",
        "Beep boop! Message logged! Human response incoming! 🤖",
        "Alert! A wild message appeared! Response being crafted! 🎮",
    ],
    
    "minimal": [
        "Got it.",
        "Thanks.",
        "Noted.",
        "Received.",
        "OK.",
    ]
}

# =============================================
# MULTI-LANGUAGE SUPPORT
# =============================================

MULTILINGUAL_MESSAGES = {
    "spanish": [
        "¡Hola! Gracias por tu mensaje. 👋",
        "¡Hola! Responderé pronto. ⏳",
        "Gracias por contactarme. 📱",
        "Mensaje recibido. ✅",
    ],
    
    "french": [
        "Bonjour ! Merci pour votre message. 👋",
        "Salut ! Je répondrai bientôt. ⏳", 
        "Merci de me contacter. 📱",
        "Message reçu. ✅",
    ],
    
    "german": [
        "Hallo! Danke für deine Nachricht. 👋",
        "Hallo! Ich werde bald antworten. ⏳",
        "Danke, dass du mich kontaktiert hast. 📱",
        "Nachricht erhalten. ✅",
    ],
    
    "arabic": [
        "مرحبا! شكرا على رسالتك. 👋",
        "أهلا! سأرد قريبا. ⏳",
        "شكرا لتواصلك معي. 📱",
        "تم استلام الرسالة. ✅",
    ]
}

# =============================================
# MESSAGE UTILITY FUNCTIONS
# =============================================

def get_auto_reply(theme="default"):
    """Get random auto-reply message based on theme"""
    if theme in THEMED_MESSAGES:
        return random.choice(THEMED_MESSAGES[theme])
    return random.choice(AUTO_REPLY_MESSAGES)

def get_tag_all_prefix():
    """Get random tag all prefix"""
    return random.choice(TAG_ALL_PREFIXES)

def get_tag_all_suffix(count):
    """Get tag all suffix with member count"""
    suffix = random.choice(TAG_ALL_SUFFIXES)
    return suffix.format(count=count)

def get_raid_message():
    """Get random raid message"""
    return random.choice(RAID_MESSAGES)

def get_copy_prefix():
    """Get random copy prefix"""
    return random.choice(COPY_PREFIXES)

def get_error_message(error_type):
    """Get error message by type"""
    return ERROR_MESSAGES.get(error_type, ERROR_MESSAGES["generic_error"])

def get_success_message(success_type, **kwargs):
    """Get success message by type with formatting"""
    message = SUCCESS_MESSAGES.get(success_type, "✅ Operation successful!")
    return message.format(**kwargs)

def get_command_response(command):
    """Get response for command"""
    return COMMAND_RESPONSES.get(command, "✅ Command executed!")

def get_multilingual_message(language):
    """Get message in specific language"""
    if language in MULTILINGUAL_MESSAGES:
        return random.choice(MULTILINGUAL_MESSAGES[language])
    return random.choice(AUTO_REPLY_MESSAGES)  # Fallback to English

# =============================================
# MESSAGE CONFIGURATION
# =============================================

class MessageConfig:
    """Configuration class for message settings"""
    
    def __init__(self):
        self.theme = "default"
        self.language = "english"
        self.use_emojis = True
        self.formal_tone = False
        
    def set_theme(self, theme):
        """Set message theme"""
        if theme in THEMED_MESSAGES:
            self.theme = theme
        else:
            self.theme = "default"
    
    def set_language(self, language):
        """Set message language"""
        if language in MULTILINGUAL_MESSAGES:
            self.language = language
        else:
            self.language = "english"
    
    def get_auto_reply(self):
        """Get auto-reply based on current config"""
        if self.language != "english":
            return get_multilingual_message(self.language)
        return get_auto_reply(self.theme)

# Create global message config instance
message_config = MessageConfig()

# =============================================
# MESSAGE VALIDATION & HELPERS
# =============================================

def validate_message_length(message, max_length=4000):
    """Validate message length for Telegram limits"""
    return len(message) <= max_length

def add_emojis(message, emoji_list):
    """Add emojis to message if enabled"""
    if message_config.use_emojis and emoji_list:
        return f"{message} {random.choice(emoji_list)}"
    return message

def format_user_mention(user_id, user_name):
    """Format user mention for tagging"""
    return f"[{user_name}](tg://user?id={user_id})"

# Import random for message selection
import random

# =============================================
# QUICK ACCESS FUNCTIONS
# =============================================

def quick_auto_reply():
    """Quick access to auto-reply message"""
    return message_config.get_auto_reply()

def quick_tag_prefix():
    """Quick access to tag prefix"""
    return get_tag_all_prefix()

def quick_raid_message():
    """Quick access to raid message"""
    return get_raid_message()

# Example usage:
if __name__ == "__main__":
    print("=== Message Library Demo ===")
    print("Auto-reply:", get_auto_reply())
    print("Tag prefix:", get_tag_all_prefix())
    print("Raid message:", get_raid_message())
    print("Error message:", get_error_message("no_permission"))
    print("Success message:", get_success_message("tag_success", count=50))
