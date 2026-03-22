import asyncio
import gspread
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from oauth2client.service_account import ServiceAccountCredentials

import config 

TOKEN = config.BOT_TOKEN
ADMIN_ID = config.ADMIN_ID
SHEET_NAME = config.SHEET_NAME

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("creds.json", scope)
client = gspread.authorize(creds)
sheet = client.open(SHEET_NAME).sheet1

bot = Bot(token=TOKEN)
dp = Dispatcher()


class OrderState(StatesGroup):
    item_name = State()
    quantity = State()
    truck_number = State()

@dp.message(Command("start"))
async def start_handler(message: types.Message, state: FSMContext):
    await message.answer("Привет, Механик! Введите название запчасти (расходника):")
    await state.set_state(OrderState.item_name)

@dp.message(OrderState.item_name)
async def process_item(message: types.Message, state: FSMContext):
    await state.update_data(item_name=message.text)
    await message.answer("Введите количество (например: 2 шт или 5 литров):")
    await state.set_state(OrderState.quantity)

@dp.message(OrderState.quantity)
async def process_qty(message: types.Message, state: FSMContext):
    await state.update_data(quantity=message.text)
    await message.answer("Введите госномер машины:")
    await state.set_state(OrderState.truck_number)

@dp.message(OrderState.truck_number)
async def process_truck(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    item = user_data['item_name']
    qty = user_data['quantity']
    truck = message.text
    user_name = message.from_user.full_name
    
    date_now = message.date.strftime("%d.%m.%Y %H:%M")

    try:
        sheet.append_row([date_now, user_name, item, qty, truck])
        
        report = (
            f"⚠️ **Новый расход!**\n\n"
            f"👤 **Механик:** {user_name}\n"
            f"🔧 **Запчасть:** {item}\n"
            f"🔢 **Количество:** {qty}\n"
            f"🚛 **Машина:** {truck}"
        )
        await bot.send_message(ADMIN_ID, report, parse_mode="Markdown")
        
        await message.answer("✅ Данные успешно записаны в таблицу!")
    except Exception as e:
        await message.answer("❌ Ошибка при записи в таблицу!")
        print(f"Error: {e}")
    
    await state.clear()

async def main():
    print("Бот запущен...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
