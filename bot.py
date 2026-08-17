import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ConversationHandler,
    filters,
    ContextTypes,
)

from config import BOT_TOKEN, WELCOME_MESSAGE, QUICK_GUIDE_MESSAGE, ABOUT_MESSAGE
from converter import convert_units, parse_inline_query, UNIT_LABELS, CATEGORY_UNITS

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ---------- Conversation States ----------
SELECT_CATEGORY, SELECT_FROM_UNIT, SELECT_TO_UNIT, ENTER_VALUE = range(4)

# ---------- Inline Keyboards ----------
def main_menu_keyboard():
    """Return the main menu inline keyboard."""
    keyboard = [
        [
            InlineKeyboardButton("📏 Length Converter", callback_data="cat_length"),
            InlineKeyboardButton("⚖️ Weight Converter", callback_data="cat_weight"),
        ],
        [InlineKeyboardButton("🌡️ Temperature Converter", callback_data="cat_temperature")],
        [
            InlineKeyboardButton("📖 Quick Guide", callback_data="quick_guide"),
            InlineKeyboardButton("ℹ️ About & Privacy", callback_data="about"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)

def back_to_main_button():
    """Return an inline keyboard with just a 'Back to Main Menu' button."""
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton("🔙 Back to Main Menu", callback_data="main_menu")]]
    )

def unit_buttons(category: str):
    """Return an inline keyboard with the units of the given category."""
    units = list(CATEGORY_UNITS[category].keys()) if category in CATEGORY_UNITS else []
    # Sort for consistency (optional)
    units.sort()
    buttons = []
    row = []
    for unit in units:
        label = UNIT_LABELS.get(unit, unit.capitalize())
        row.append(InlineKeyboardButton(label, callback_data=f"unit_{unit}"))
        if len(row) == 3:  # 3 per row for better layout
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton("🔙 Back to Main Menu", callback_data="main_menu")])
    return InlineKeyboardMarkup(buttons)

# ---------- Handlers ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Send welcome message and show main menu."""
    await update.message.reply_text(
        WELCOME_MESSAGE,
        reply_markup=main_menu_keyboard(),
        parse_mode="Markdown",
    )
    return SELECT_CATEGORY

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Send quick guide and show main menu."""
    await update.message.reply_text(
        QUICK_GUIDE_MESSAGE,
        reply_markup=main_menu_keyboard(),
        parse_mode="Markdown",
    )
    return SELECT_CATEGORY

async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send about/privacy info with a back button."""
    await update.message.reply_text(
        ABOUT_MESSAGE,
        reply_markup=back_to_main_button(),
        parse_mode="Markdown",
    )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle all button presses."""
    query = update.callback_query
    await query.answer()
    data = query.data

    # ---------- Navigation and Info ----------
    if data == "main_menu":
        await query.edit_message_text(
            WELCOME_MESSAGE,
            reply_markup=main_menu_keyboard(),
            parse_mode="Markdown",
        )
        return SELECT_CATEGORY

    if data == "quick_guide":
        await query.edit_message_text(
            QUICK_GUIDE_MESSAGE,
            reply_markup=main_menu_keyboard(),
            parse_mode="Markdown",
        )
        return SELECT_CATEGORY

    if data == "about":
        await query.edit_message_text(
            ABOUT_MESSAGE,
            reply_markup=back_to_main_button(),
            parse_mode="Markdown",
        )
        # We stay in the main menu state conceptually, but we return SELECT_CATEGORY
        # so that pressing a category later works.
        return SELECT_CATEGORY

    # ---------- Category Selection ----------
    if data.startswith("cat_"):
        category = data.split("_")[1]  # "length", "weight", "temperature"
        context.user_data["category"] = category
        context.user_data["state"] = "select_from"
        await query.edit_message_text(
            f"📐 **{category.capitalize()} Conversion**\n\n"
            "Select the unit you want to convert **FROM**:",
            reply_markup=unit_buttons(category),
            parse_mode="Markdown",
        )
        return SELECT_FROM_UNIT

    # ---------- Unit Selection ----------
    if data.startswith("unit_"):
        unit = data.split("_")[1]
        if context.user_data.get("state") == "select_from":
            context.user_data["from_unit"] = unit
            context.user_data["state"] = "select_to"
            category = context.user_data["category"]
            await query.edit_message_text(
                f"From: **{UNIT_LABELS.get(unit, unit.capitalize())}**\n"
                "Now select the unit you want to convert **TO**:",
                reply_markup=unit_buttons(category),
                parse_mode="Markdown",
            )
            return SELECT_TO_UNIT
        else:  # state == "select_to" (or fallback)
            context.user_data["to_unit"] = unit
            context.user_data["state"] = "enter_value"
            from_unit = context.user_data["from_unit"]
            await query.edit_message_text(
                f"From: **{UNIT_LABELS.get(from_unit, from_unit.capitalize())}**\n"
                f"To: **{UNIT_LABELS.get(unit, unit.capitalize())}**\n\n"
                "Now enter the value you want to convert (e.g., `25`):",
                reply_markup=back_to_main_button(),
                parse_mode="Markdown",
            )
            return ENTER_VALUE

    # Fallback
    return SELECT_CATEGORY

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process user message: either a direct conversion or numeric value for a pending conversion."""
    text = update.message.text.strip()

    # First, try to parse as a direct command (e.g., "10 km to miles")
    parsed = parse_inline_query(text)
    if parsed:
        value, src, dst = parsed
        try:
            result = convert_units(value, src, dst)
            # Format result nicely
            if dst in ("celsius", "fahrenheit", "kelvin"):
                result_str = f"{result:.2f}"
            else:
                result_str = f"{result:.4f}".rstrip("0").rstrip(".")
            await update.message.reply_text(
                f"✅ **{value} {UNIT_LABELS.get(src, src.capitalize())} = "
                f"{result_str} {UNIT_LABELS.get(dst, dst.capitalize())}**",
                parse_mode="Markdown",
                reply_markup=main_menu_keyboard(),
            )
            context.user_data.clear()
            return SELECT_CATEGORY
        except Exception as e:
            logger.error(f"Conversion error: {e}")
            await update.message.reply_text(
                "⚠️ Sorry, I couldn't convert that. Please check the units and try again.",
                reply_markup=main_menu_keyboard(),
                parse_mode="Markdown",
            )
            context.user_data.clear()
            return SELECT_CATEGORY

    # If we are not in a pending conversion state, treat as unknown
    if "from_unit" not in context.user_data or "to_unit" not in context.user_data:
        await update.message.reply_text(
            "⚠️ I didn't understand that. Please use the menu below or type something like:\n"
            "`10 km to miles`",
            reply_markup=main_menu_keyboard(),
            parse_mode="Markdown",
        )
        return SELECT_CATEGORY

    # Otherwise, we expect a numeric value for the ongoing interactive conversion
    try:
        value = float(text)
    except ValueError:
        await update.message.reply_text(
            "⚠️ Please enter a valid number (e.g., `25` or `3.14`).",
            reply_markup=back_to_main_button(),
            parse_mode="Markdown",
        )
        return ENTER_VALUE

    from_unit = context.user_data["from_unit"]
    to_unit = context.user_data["to_unit"]
    try:
        result = convert_units(value, from_unit, to_unit)
        if to_unit in ("celsius", "fahrenheit", "kelvin"):
            result_str = f"{result:.2f}"
        else:
            result_str = f"{result:.4f}".rstrip("0").rstrip(".")
        await update.message.reply_text(
            f"✅ **{value} {UNIT_LABELS.get(from_unit, from_unit.capitalize())} = "
            f"{result_str} {UNIT_LABELS.get(to_unit, to_unit.capitalize())}**",
            parse_mode="Markdown",
            reply_markup=main_menu_keyboard(),
        )
        context.user_data.clear()
        return SELECT_CATEGORY
    except Exception as e:
        logger.error(f"Conversion error: {e}")
        await update.message.reply_text(
            "⚠️ Sorry, an error occurred during conversion. Please try again.",
            reply_markup=main_menu_keyboard(),
        )
        context.user_data.clear()
        return SELECT_CATEGORY

async def fallback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Catch-all for any message not handled by the conversation flow."""
    text = update.message.text
    parsed = parse_inline_query(text)
    if parsed:
        value, src, dst = parsed
        try:
            result = convert_units(value, src, dst)
            if dst in ("celsius", "fahrenheit", "kelvin"):
                result_str = f"{result:.2f}"
            else:
                result_str = f"{result:.4f}".rstrip("0").rstrip(".")
            await update.message.reply_text(
                f"✅ **{value} {UNIT_LABELS.get(src, src.capitalize())} = "
                f"{result_str} {UNIT_LABELS.get(dst, dst.capitalize())}**",
                parse_mode="Markdown",
                reply_markup=main_menu_keyboard(),
            )
            context.user_data.clear()
            return SELECT_CATEGORY
        except Exception:
            pass

    await update.message.reply_text(
        "⚠️ I didn't understand that. Please use the menu or type a direct conversion "
        "like `10 km to miles`.",
        reply_markup=main_menu_keyboard(),
        parse_mode="Markdown",
    )
    context.user_data.clear()
    return SELECT_CATEGORY

# ---------- Conversation Handler ----------
conv_handler = ConversationHandler(
    entry_points=[
        CommandHandler("start", start),
        CommandHandler("help", help_command),
        CommandHandler("settings", settings_command),
        CallbackQueryHandler(button_callback, pattern="^(main_menu|quick_guide|about|cat_|unit_)"),
    ],
    states={
        SELECT_CATEGORY: [
            CallbackQueryHandler(button_callback, pattern="^(main_menu|quick_guide|about|cat_|unit_)"),
            MessageHandler(filters.TEXT & ~filters.COMMAND, fallback),
        ],
        SELECT_FROM_UNIT: [
            CallbackQueryHandler(button_callback, pattern="^(unit_|main_menu)"),
            MessageHandler(filters.TEXT & ~filters.COMMAND, fallback),
        ],
        SELECT_TO_UNIT: [
            CallbackQueryHandler(button_callback, pattern="^(unit_|main_menu)"),
            MessageHandler(filters.TEXT & ~filters.COMMAND, fallback),
        ],
        ENTER_VALUE: [
            CallbackQueryHandler(button_callback, pattern="^main_menu$"),
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message),
        ],
    },
    fallbacks=[
        CommandHandler("start", start),
        CommandHandler("help", help_command),
        CommandHandler("settings", settings_command),
        CallbackQueryHandler(button_callback, pattern="^main_menu$"),
    ],
)

# ---------- Main ----------
def main():
    """Start the bot."""
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(conv_handler)

    logger.info("Bot started polling...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
