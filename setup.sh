#!/data/data/com.termux/files/usr/bin/bash

echo ""
echo "╔══════════════════════════════════════╗"
echo "║    SIKU TAGALL BOT SETUP            ║"
echo "║    For Termux Android               ║"
echo "╚══════════════════════════════════════╝"
echo ""

echo "[1/5] 📦 Updating Termux packages..."
pkg update -y
pkg upgrade -y

echo "[2/5] 🔧 Installing required system packages..."
pkg install python -y
pkg install python-pip -y
pkg install git -y
pkg install clang -y
pkg install libxml2 -y
pkg install libxslt -y
pkg install libjpeg-turbo -y
pkg install zlib -y
pkg install libffi -y
pkg install openssl -y

echo "[3/5] ⬆️  Upgrading pip..."
pip install --upgrade pip

echo "[4/5] 📚 Installing Python dependencies..."
pip install telethon==1.34.0
pip install colorama==0.4.6
pip install pyaes==1.6.1
pip install rsa==4.9

echo "[5/5] ✅ Setup complete!"
echo ""
echo "════════════════════════════════════════"
echo "🎉 Installation Successful!"
echo "════════════════════════════════════════"
echo ""
echo "📝 Next steps:"
echo "1. Create main.py file with the bot code"
echo "2. Edit main.py and add your:"
echo "   • Phone number (with country code)"
echo ""
echo "3. Run the bot:"
echo "   python main.py"
echo ""
echo "4. First run will ask for:"
echo "   • Verification code from Telegram"
echo ""
echo "🔑 Owner ID: 7862393998"
echo "🔧 Commands available after authorization"
echo ""
echo "📱 Bot Features:"
echo "• /siku gm - Good Morning tagging"
echo "• /siku gn - Good Night tagging"
echo "• /siku [message] - Custom message"
echo "• /authsiku - Authorize users"
echo "• /sudosiku - Manage sudo users"
echo ""
echo "⚠️  Important: Keep your API credentials secure!"
echo ""
