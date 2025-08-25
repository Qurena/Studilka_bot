from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from pathlib import Path


API_TOKEN = '7879539811:AAFGpkfGrvlErG3-z-Pa4Cm6JjggIFTj1u4'

bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
BASE_DIR = Path(__file__).parent.parent
DB_DIR = BASE_DIR / "database"
DB_PATH = DB_DIR / "bot_db.sqlite"