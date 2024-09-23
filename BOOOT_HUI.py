from aiogram import Bot, Dispatcher, types
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram import Router
from aiogram import F, Dispatcher

bot = Bot(token='7910646214:AAG-ku8Zjt2xi88017Vj3RyXW4Agv2ZijQM')
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
router = Router()


@router.message(F.text == "/start")
async def start_handler(message: types.Message):
    """

    :param message:
    """
    await message.answer('Привет! ☕ Добро пожаловать в нашу кофейню! Мы рады предложить вам ароматный кофе, вкусные десерты и уютную атмосферу. Как мы можем помочь вам сегодня?')

@router.message()
async def info(message: types.Message):
    murkup= types.InlineKeyboardMarkup(row_wight = 2):
    murkup.add(types.InlineKeyboardButton('Menu', callback_data=Menu))

dp.include_router(router)


async def main():
    await dp.start_polling(bot)


if __name__ == '__main__':
    import asyncio

    asyncio.run(main())
