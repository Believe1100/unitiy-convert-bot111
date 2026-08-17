import os
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env (if present)

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable is not set.")

# ------------------- UI Text Constants -------------------
WELCOME_MESSAGE = (
    "👋 **Welcome to Unity Convert Bot!** (@unit_convertutility_bot)\n\n"
    "Your lightweight, instant measurement converter right inside Telegram. "
    "Whether you're traveling, cooking, studying, or working, convert everyday "
    "units in seconds without leaving your chat.\n\n"
    "✨ **What I Can Do:**\n"
    "📏 **Length:** Kilometers, Meters, Centimeters, Miles, Feet, Inches\n"
    "⚖️ **Weight:** Kilograms, Grams, Pounds, Ounces\n"
    "🌡️ **Temperature:** Celsius, Fahrenheit, Kelvin\n\n"
    "Tap a category below or press **Quick Guide** to learn how to convert "
    "numbers directly!"
)

QUICK_GUIDE_MESSAGE = (
    "📖 **How to Use Unity Convert Bot**\n\n"
    "**Method 1: Interactive Menu (Recommended)**\n"
    "1. Select a category below (Length, Weight, or Temp).\n"
    "2. Choose your starting unit and target unit.\n"
    "3. Type the number you wish to convert.\n\n"
    "**Method 2: Quick Command Syntax**\n"
    "You can also type direct conversions anytime:\n"
    "• `10 km to miles`\n"
    "• `70 kg to lbs`\n"
    "• `100 c to f`\n\n"
    "Press any button below to start converting!"
)

ABOUT_MESSAGE = (
    "ℹ️ **About Unity Convert Bot**\n\n"
    "Unity Convert Bot is a free utility tool designed for fast unit calculations.\n"
    "• **Version:** 1.0.0\n"
    "• **Data Privacy:** We do not store or track your personal conversation "
    "history or conversion inputs.\n"
    "• **Support:** Free and open for public utility.\n\n"
    "Tap below to return to the main menu."
)
