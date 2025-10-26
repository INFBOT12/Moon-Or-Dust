import asyncio
import logging
import os
import random
from aiogram import Bot, Dispatcher, types

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment variables
BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_CHAT_ID = os.environ.get("ADMIN_CHAT_ID")  # optional

# Initialize bot and dispatcher
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Keep track of user games (no saves, in-memory)
active_games = {}

# Function to simulate a round
def calculate_whale_offer(remaining_values):
    return round(sum(remaining_values) / len(remaining_values), 2)

# Start command
@dp.message()
async def start_game(message: types.Message):
    user_id = message.from_user.id
    if user_id in active_games:
        await message.answer("Game in progress! Finish your current round.")
        return

    # Create 10 mystery boxes with random values
    values = [10, 50, 100, 500, 1000, 5000, 10000, 50000, 100000, 500000]
    random.shuffle(values)
    active_games[user_id] = {
        "boxes": values,
        "chosen_box": None,
        "opened_boxes": []
    }
    box_buttons = [types.InlineKeyboardButton(text=f"Box {i+1}", callback_data=f"choose_{i}") for i in range(10)]
    keyboard = types.InlineKeyboardMarkup(row_width=5)
    keyboard.add(*box_buttons)
    await message.answer("Welcome to Moon or Dust!\nPick your mystery box:", reply_markup=keyboard)

# Callback for choosing and opening boxes
@dp.callback_query()
async def handle_box(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    data = callback.data
    game = active_games.get(user_id)
    if not game:
        await callback.answer("No active game. Use any message to /start again.")
        return

    if data.startswith("choose_"):
        index = int(data.split("_")[1])
        if game["chosen_box"] is None:
            # Player selects their box
            game["chosen_box"] = index
            await callback.message.edit_text(f"You chose Box {index+1}.\nNow start opening other boxes!")
        else:
            if index == game["chosen_box"] or index in game["opened_boxes"]:
                await callback.answer("Cannot open this box!")
                return
            # Open box
            value = game["boxes"][index]
            game["opened_boxes"].append(index)
            remaining_values = [v for i, v in enumerate(game["boxes"]) if i not in game["opened_boxes"] and i != game["chosen_box"]]
            whale_offer = calculate_whale_offer(remaining_values)
            keyboard = types.InlineKeyboardMarkup(row_width=2)
