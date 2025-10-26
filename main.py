import asyncio
import logging
import random
import os
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, FSInputFile
from aiogram.filters import Command

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Telegram Bot Token ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN not found. Set it as an environment variable in Render.")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# --- Game setup ---
CASE_VALUES = [1, 5, 10, 25, 50, 75, 100, 250, 500, 1000]
user_games = {}


def get_case_keyboard(opened_cases):
    """Create inline keyboard with unopened cases."""
    buttons = []
    for i in range(1, 11):
        if i not in opened_cases:
            buttons.append(InlineKeyboardButton(f"💼 {i}", callback_data=f"case_{i}"))
    rows = [buttons[i:i + 5] for i in range(0, len(buttons), 5)]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_moon_dust_keyboard():
    """Keyboard for Moon / Dust choice."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("🌕 Moon", callback_data="moon"),
         InlineKeyboardButton("🌫️ Dust", callback_data="dust")]
    ])


def load_image(filename):
    """Safely load image if available."""
    path = os.path.join("images", filename)
    return FSInputFile(path) if os.path.exists(path) else None


@dp.message(Command("start"))
async def start_game(message: types.Message):
    img = load_image("briefcase.png")
    text = (
        "🎮 *Welcome to Moon or Dust: Whale Edition!*\n\n"
        "Pick your lucky briefcase (1–10) to begin:"
    )
    if img:
        await message.answer_photo(img, caption=text, parse_mode="Markdown", reply_markup=get_case_keyboard([]))
    else:
        await message.answer(text, parse_mode="Markdown", reply_markup=get_case_keyboard([]))


@dp.callback_query(lambda c: c.data.startswith("case_"))
async def choose_case(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    case_num = int(callback.data.split("_")[1])

    # Initialize new game for user
    values = random.sample(CASE_VALUES, len(CASE_VALUES))
    user_games[user_id] = {
        "chosen_case": case_num,
        "case_values": values,
        "opened_cases": [],
    }

    text = f"🎁 You picked case #{case_num}.\n\nNow open 3 other cases!"
    await callback.message.edit_caption(caption=text, reply_markup=get_case_keyboard([case_num]))
    await callback.answer()


@dp.callback_query(lambda c: c.data.startswith("open_") or c.data.startswith("case_"))
async def open_case(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    if user_id not in user_games:
        await callback.answer("Start a new game with /start", show_alert=True)
        return

    game = user_games[user_id]
    case_num = int(callback.data.split("_")[1])

    if case_num in game["opened_cases"] or case_num == game["chosen_case"]:
        await callback.answer("You already opened that case.")
        return

    game["opened_cases"].append(case_num)
    value = game["case_values"][case_num - 1]

    remaining = [v for i, v in enumerate(game["case_values"], 1)
                 if i not in game["opened_cases"] and i != game["chosen_case"]]

    msg = f"💼 You opened case #{case_num} — it had *{value} points!*"

    # Every 3 opens or near end → Whale offers
    if len(game["opened_cases"]) % 3 == 0 or len(remaining) <= 2:
        offer = int(sum(remaining) / len(remaining))
        game["offer"] = offer
        msg += f"\n\n🐋 *The Whale offers you {offer} points!*\nWould you like to **Moon** or **Dust**?"
        whale_img = load_image("whale.png")
        if whale_img:
            await callback.message.answer_photo(whale_img, caption=msg, parse_mode="Markdown",
                                                reply_markup=get_moon_dust_keyboard())
        else:
            await callback.message.answer(msg, parse_mode="Markdown", reply_markup=get_moon_dust_keyboard())
    else:
        msg += "\n\nPick another case:"
        await callback.message.edit_caption(
            caption=msg,
            parse_mode="Markdown",
            reply_markup=get_case_keyboard(game["opened_cases"] + [game["chosen_case"]])
        )

    await callback.answer()


@dp.callback_query(lambda c: c.data in ["moon", "dust"])
async def handle_choice(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    game = user_games.get(user_id)

    if not game:
        await callback.answer("Start a new game with /start", show_alert=True)
        return

    if callback.data == "moon":
        msg = f"🌕 You chose to *Moon!* — taking {game['offer']} points!"
        img = load_image("moon.png")
    else:
        msg = "🌫️ You chose *Dust!* — let’s keep opening cases!"
        img = load_image("dust.png")

    remaining = [i for i in range(1, 11)
                 if i not in game["opened_cases"] and i != game["chosen_case"]]

    if not remaining:
        final_value = game["case_values"][game["chosen_case"] - 1]
        end_msg = f"🎉 Final reveal!\nYour case #{game['chosen_case']} had *{final_value} points!*"
        if img:
            await callback.message.answer_photo(img, caption=end_msg, parse_mode="Markdown")
        else:
            await callback.message.answer(end_msg, parse_mode="Markdown")
        user_games.pop(user_id, None)
        await callback.answer()
        return

    if img:
        await callback.message.answer_photo(img, caption=msg, parse_mode="Markdown",
                                            reply_markup=get_case_keyboard(game["opened_cases"] + [game["chosen_case"]]))
    else:
        await callback.message.answer(msg, parse_mode="Markdown",
                                      reply_markup=get_case_keyboard(game["opened_cases"] + [game["chosen_case"]]))
    await callback.answer()


async def main():
    logger.info("Bot is running (Moon or Dust — Whale Edition)...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
