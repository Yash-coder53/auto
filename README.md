# 🤖 Siku TagAll Bot - Telegram Member Tagging Tool

A powerful Telegram bot that tags all members one by one in separate messages with beautiful emoji formatting. Perfect for group announcements, greetings, and notifications.

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Telethon](https://img.shields.io/badge/Telethon-1.34.0-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)
![Platform](https://img.shields.io/badge/Platform-Termux-purple.svg)

## ✨ Features

- **One-by-One Tagging**: Each member receives a separate personalized message
- **Beautiful Emoji Messages**: Pre-formatted GM/GN messages with emojis
- **Custom Messages**: Tag with your own custom text
- **Multi-Level Authorization**: Owner → Sudo → Admin → Authorized Users
- **Rate Limit Protection**: Built-in delays to avoid Telegram bans
- **Stop Command**: Stop tagging process anytime
- **Statistics**: Detailed tagging statistics after completion
- **Chat Management**: Control which chats can use the bot
- **User Authorization**: Grant specific users tagging permissions

## 📋 Commands

### 👑 Owner Commands
- `/allow` - Authorize current chat
- `/disallow` - Remove chat authorization
- `/allowed` - List authorized chats
- `/sudosiku` - Manage sudo users
- `/clear` - Clear all authorized chats

### 👮 Admin/Sudo Commands
- `/authsiku @username` - Authorize user (or reply to user)
- `/unauthsiku @username` - Remove user authorization
- `/authsiku all` - Authorize all current members
- `/limit [number]` - Set maximum members to tag
- `/limit delay [seconds]` - Set delay between messages

### 🤖 User Commands (After Authorization)
- `/siku gm` - 🌅 Good Morning tagging
- `/siku gn` - 🌙 Good Night tagging
- `/siku [message]` - 📢 Custom message tagging
- `/stopsiku` - 🛑 Stop current tagging process
- `/sikustatus` - Show bot status and help

## 📝 Message Formats

### Good Morning
```
🌅 Good Morning @username! ☀️ Have a great day! 🌞✨
```

### Good Night
```
🌙 Good Night @username! 🌜 Take care and sweet dreams! 💫🛏️
```

### Custom Messages
```
[Your Message] @username!
```

## 🚀 Installation

### Prerequisites
- Termux app installed on Android
- Telegram account
- API credentials from [my.telegram.org](https://my.telegram.org)

### Quick Setup (Termux)

1. **Clone or create the files:**
```bash
# Create project directory
mkdir ~/siku-bot
cd ~/siku-bot

# Create setup.sh and requirements.txt from above
# Create main.py with the bot code
```

2. **Run setup script:**
```bash
chmod +x setup.sh
./setup.sh
```

3. **Configure the bot:**
Edit `main.py` and update:
```python
API_ID = 24633463  # Your API ID
API_HASH = 'a2f7cd31e5017cf4fb84dd6ca2f27809'  # Your API Hash
PHONE_NUMBER = '+1234567890'  # Your phone number with country code
OWNER_ID = 7862393998  # Your Telegram user ID
```

4. **Run the bot:**
```bash
python main.py
```

5. **First-time setup:**
- Enter your phone number when prompted
- Enter verification code from Telegram
- Bot will create session files automatically

## 🔧 Configuration Files

The bot creates these JSON files automatically:

| File | Purpose |
|------|---------|
| `allowed_chats.json` | Stores authorized chat IDs |
| `authorized_users.json` | Stores authorized user IDs per chat |
| `sudo_users.json` | Stores sudo user IDs |
| `bot_settings.json` | Stores bot settings and limits |

## 🛡️ Security Features

### 4-Level Permission System
1. **Owner** (`7862393998`): Full control over everything
2. **Sudo Users**: Can manage chats and authorize users
3. **Group Admins**: Can authorize users in their groups
4. **Authorized Users**: Can use `/siku` commands only
5. **Regular Users**: No access to tagging commands

### Protection Mechanisms
- Flood wait handling with automatic delays
- Message splitting for large groups
- Stop command to halt tagging anytime
- Chat authorization required before use
- User authorization required for tagging

## ⚙️ Settings Management

### Tag Limits
```bash
# Set maximum members to tag
/limit 50  # Tag only 50 members
/limit 0   # No limit (tag all members)

# Set delay between messages
/limit delay 2  # 2 seconds between messages
/limit delay 3  # 3 seconds between messages
```

### Default Values
- **Tag Limit**: 0 (no limit)
- **Delay**: 2 seconds between messages
- **Max Limit**: 1000 members
- **Max Delay**: 10 seconds

## 📊 Usage Examples

### Basic Tagging
```bash
# Good Morning tagging
/siku gm

# Good Night tagging
/siku gn

# Custom message
/siku Meeting at 5 PM today!
```

### Admin Operations
```bash
# Authorize a user
/authsiku @username
/authsiku (reply to user)

# Authorize all members
/authsiku all

# Set limits
/limit 100
/limit delay 3
```

### Owner Operations
```bash
# Add sudo user
/sudosiku @username

# Authorize chat
/allow

# List authorized chats
/allowed
```

## 🐛 Troubleshooting

### Common Issues

1. **"Bot not starting"**
   ```bash
   # Check Python installation
   python --version
   
   # Check dependencies
   pip list | grep telethon
   ```

2. **"Flood wait" errors**
   - Bot automatically handles these with delays
   - Increase delay with `/limit delay [seconds]`
   - Don't spam commands

3. **"Chat not authorized"**
   ```bash
   # Owner or sudo must authorize the chat first
   /allow
   ```

4. **"User not authorized"**
   ```bash
   # Admin or sudo must authorize the user
   /authsiku @username
   ```

### Logs and Monitoring
- Check terminal output for real-time logs
- Errors are logged with timestamps
- Progress is shown during tagging

## 🔄 Updates

To update the bot:
1. Backup your JSON files
2. Replace `main.py` with new code
3. Restart the bot
4. Your settings and authorizations are preserved

## 📁 Project Structure
```
siku-bot/
├── main.py              # Main bot code
├── requirements.txt     # Python dependencies
├── setup.sh            # Setup script for Termux
├── README.md           # This file
├── allowed_chats.json      # Auto-generated
├── authorized_users.json   # Auto-generated
├── sudo_users.json         # Auto-generated
└── bot_settings.json       # Auto-generated
```

## ⚠️ Important Notes

### Do:
- ✅ Use responsibly in groups
- ✅ Ask for permission before tagging
- ✅ Monitor bot activity
- ✅ Keep API credentials secure
- ✅ Backup JSON files regularly

### Don't:
- ❌ Spam tagging commands
- ❌ Use in unauthorized chats
- ❌ Share your session files
- ❌ Modify JSON files manually
- ❌ Use for harassment or spam

## 🆘 Support

### Need Help?
1. Check the troubleshooting section
2. Verify your API credentials
3. Ensure proper installation
4. Check bot logs for errors

### Reporting Issues
When reporting issues, include:
- Error messages from logs
- Steps to reproduce
- Your configuration (without sensitive data)
- Screenshots if applicable

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Credits

- Built with [Telethon](https://github.com/LonamiWebs/Telethon)
- Emoji messages for better engagement
- Designed for Termux Android environment

## 🎯 Quick Start Summary

```bash
# 1. Install Termux from F-Droid
# 2. Open Termux and run:
pkg update && pkg upgrade
pkg install python git
pip install telethon colorama

# 3. Create main.py with bot code
# 4. Configure API credentials
# 5. Run: python main.py
# 6. Authorize your chat: /allow
# 7. Authorize users: /authsiku @username
# 8. Start tagging: /siku gm
```

---

**Happy Tagging!** 🌟 If you find this bot useful, consider sharing it with other group admins!
