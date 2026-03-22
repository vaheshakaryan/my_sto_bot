import asyncio
import gspread
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from oauth2client.service_account import ServiceAccountCredentials

# Ներմուծում ենք գաղտնի տվյալները config.py ֆայլից
import config 

TOKEN = config.BOT_TOKEN
ADMIN_ID = config.ADMIN_ID
SHEET_NAME = config.SHEET_NAME

# Մնացած կոդը մնում է նույնը...
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("creds.json", scope)
client = gspread.authorize(creds)
sheet = client.open(SHEET_NAME).sheet1

bot = Bot(token=TOKEN)
dp = Dispatcher()

# ... (շարունակությունը նույնն է, ինչ նախորդ անգամ ուղարկածս կոդը)

# Состояния анкеты (FSM)
class OrderState(StatesGroup):
    item_name = State()
    quantity = State()
    truck_number = State()

# Команда /start
@dp.message(Command("start"))
async def start_handler(message: types.Message, state: FSMContext):
    await message.answer("Привет, Механик! Введите название запчасти (расходника):")
    await state.set_state(OrderState.item_name)

# Получаем название запчасти
@dp.message(OrderState.item_name)
async def process_item(message: types.Message, state: FSMContext):
    await state.update_data(item_name=message.text)
    await message.answer("Введите количество (например: 2 шт или 5 литров):")
    await state.set_state(OrderState.quantity)

# Получаем количество
@dp.message(OrderState.quantity)
async def process_qty(message: types.Message, state: FSMContext):
    await state.update_data(quantity=message.text)
    await message.answer("Введите госномер машины:")
    await state.set_state(OrderState.truck_number)

# Получаем номер машины и сохраняем всё
@dp.message(OrderState.truck_number)
async def process_truck(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    item = user_data['item_name']
    qty = user_data['quantity']
    truck = message.text
    user_name = message.from_user.full_name
    
    # Форматируем дату для таблицы
    date_now = message.date.strftime("%d.%m.%Y %H:%M")

    # Сохранение данных в Google Sheets
    try:
        # Добавляем строку: Дата, Механик, Запчасть, Количество, Номер машины
        sheet.append_row([date_now, user_name, item, qty, truck])
        
        # Сообщение администратору (вам)
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
    
    # Очищаем состояние
    await state.clear()

async def main():
    print("Бот запущен...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())