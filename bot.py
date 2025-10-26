import random
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command

TOKEN = "BOT_TOKEN"  # Replace with your bot token
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Start game
async def start_game(user_id: int):
    # 10 briefcases with random values
    briefcases = [1, 5, 10, 25, 50, 100, 250, 500, 750, 1000]
    random.shuffle(briefcases)

    # Player picks one case
    player_case = random.choice(briefcases)
    briefcases.remove(player_case)

    await bot.send_message(user_id,
                           f"🌙 Welcome to Moon-or-Dust! 💨\n\n"
                           f"You picked a secret case.\nYour case is hidden until the end.")

    await continue_game(user_id, player_case, briefcases)

# Helper: generate inline keyboard for remaining briefcases
def briefcase_keyboard(briefcases):
    kb = InlineKeyboardMarkup(row_width=5)
    for case in briefcases:
        kb.insert(InlineKeyboardButton(text=f"{case}", callback_data="ignore"))
    return kb

# Continue game rounds
async def continue_game(user_id: int, player_case: int, briefcases: list):
    round_num = 1
    while briefcases:
        opened_case = briefcases.pop(0)
        await bot.send_message(user_id,
                               f"Round {round_num}: A briefcase was opened revealing {opened_case} Dust!",
                               reply_markup=briefcase_keyboard(briefcases))
        round_num += 1

        if briefcases:
            # Whale offer
            offer = int(sum(briefcases) / len(briefcases))
            kb = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(text="Moon 🌙", callback_data=f"accept:{offer}:{player_case}:{','.join(map(str, briefcases))}"),
                        InlineKeyboardButton(text="Dust 💨", callback_data=f"decline:{offer}:{player_case}:{','.join(map(str, briefcases))}")
                    ]
                ]
            )
            await bot.send_message(user_id,
                                   f"The Whale offers you {offer} Dust.\nWould you like to Moon or Dust?",
                                   reply_markup=kb)
            break
        else:
            await bot.send_message(user_id, f"No more offers! Your case contained {player_case} Dust. 🌟")
            break

# Handle offers
async def handle_offer(callback: types.CallbackQuery):
    action, offer, player_case, remaining = callback.data.split(":")
    offer = int(offer)
    player_case = int(player_case)
    remaining_cases = list(map(int, remaining.split(",")))

    if action == "accept":
        await callback.message.edit_text(f"🌙 You chose to Moon! You win {offer} Dust! 🎉\nYour case contained {player_case} Dust.")
        await callback.answer()
    else:
        await callback.message.edit_text(f"💨 You chose Dust! The game continues...")
        await callback.answer()
        await continue_game(callback.from_user.id, player_case, remaining_cases)

# Command: /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await start_game(message.from_user.id)

# Callback handler
@dp.callback_query(lambda c: c.data.startswith(("accept:", "decline:")))
async def cb_handler(callback: types.CallbackQuery):
    await handle_offer(callback)

# Ignore click on visual briefcases
@dp.callback_query(lambda c: c.data == "ignore")
async def ignore_case(callback: types.CallbackQuery):
    await callback.answer("This is a remaining briefcase!", show_alert=True)

# Run bot
async def main():
    print("Bot started...")
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
