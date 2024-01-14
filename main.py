# Привіт читач, це переробка мого старого проєкту Scarl3t, повністю весь функціонал я не перенесу, бо писав його я близько 2 тижнів, а на цей у мене відсили кілька днів разом з оформленням тез, тезами і всілякою фігнею, якщо цікаво, що за скарлет, ось посилання: https://github.com/konstie1/Scarl3t-file-sharing-service
from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher, FSMContext
from aiogram.utils import executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher.filters import BoundFilter
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from string import ascii_letters, digits
import random
import sqlite3
# Я буду супроводжувати тебе весь код, тож давай знайомитися

# Я ваня або Konstie, а це токен або token
TOKEN = ""

# А тут простая проверка БД нечего особенного..
import sqlite3

def verif_db():
    databaseFile = "data.db"
    db = sqlite3.connect(databaseFile, check_same_thread=False)
    cursor = db.cursor()

    try:
        cursor.execute("SELECT * FROM users")
    except sqlite3.OperationalError:
        cursor.execute(
            "CREATE TABLE users(id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INT)"
        )

    try:
        cursor.execute("SELECT * FROM files")
    except sqlite3.OperationalError:
        cursor.execute(
            "CREATE TABLE files(user_id INT, type TEXT, code TEXT, file_id TEXT, views INT DEFAULT (0), password TEXT)"
        )

    cursor.execute("PRAGMA table_info(files)")
    columns = [info[1] for info in cursor.fetchall()]
    if "file_name" not in columns:
        cursor.execute("ALTER TABLE files ADD COLUMN file_name TEXT")

    db.commit()


# Взагалі я коменти пишу під час написання коду, але оскільки я себе знаю, код буду 100 разів рефакторити, тож усе ж таки коментарі буду якось структурувати у кінці, щоб ми разом ішли згори донизу по коду)
def user_exist(user_id):
    db = sqlite3.connect("data.db", check_same_thread=False)
    cursor = db.cursor()
    cursor.execute("SELECT user_id FROM users WHERE user_id=?", (user_id,))
    if cursor.fetchone() is None:
        return False
    else:
        return True

# До речі, я довго думав, як краще зробити базу даних, зрештою вирішив зробити sqlite3 хоча в минулих схожих проектах використовував json
def add_user_to_db(user_id):
    db = sqlite3.connect("data.db", check_same_thread=False)
    cursor = db.cursor()
    user = [user_id]
    cursor.execute(f"""INSERT INTO users(user_id) VALUES(?)""", user)
    db.commit()

# Але для конкурсу sqlite3 має більш потужніший вигляд, та й у json потрібно париться зі збереженнями, backup і всякою такою шнягою
def add_new_file(user_id, type, code, file_id, file_name):
    db = sqlite3.connect("data.db", check_same_thread=False)
    cursor = db.cursor()
    data = [user_id, type, code, file_id, file_name]
    cursor.execute("INSERT INTO files(user_id, type, code, file_id, file_name) VALUES(?,?,?,?,?)", data)
    db.commit()

# Я так і не придумав нормально як зробити паролі, в результаті вийшло, що у відповідь приходить мерзенне null, коли немає пароля
def add_new_pass_file(user_id, type, code, file_id, password, file_name):
    db = sqlite3.connect("data.db", check_same_thread=False)
    cursor = db.cursor()
    data = [user_id, type, code, file_id, password, file_name]
    cursor.execute("INSERT INTO files(user_id, type, code, file_id, password, file_name) VALUES(?,?,?,?,?,?)", data)
    db.commit()

# Отримання файлу теж стандартне, хоча я мені здається щось перемудрив з return
def get_file(code):
    db = sqlite3.connect("data.db", check_same_thread=False)
    cursor = db.cursor()
    cursor.execute("SELECT file_id FROM files WHERE code=?", (code,))
    fileID = cursor.fetchone()
    cursor.execute("SELECT type FROM files WHERE code=?", (code,))
    type_file = cursor.fetchone()
    cursor.execute("SELECT views FROM files WHERE code=?", (code,))
    views = cursor.fetchone()
    cursor.execute("SELECT password FROM files WHERE code=?", (code,))
    password = cursor.fetchone()
    return type_file, fileID, views, password

# Зараз написано тільки третину того, що я хочу, якщо буде близько 200-300 рядків коду знайте, мені стало ліньки)
def get_files(user_id):
    db = sqlite3.connect("data.db", check_same_thread=False)
    cursor = db.cursor()

    cursor.execute("SELECT code FROM files WHERE user_id=?", (user_id,))
    fileIDs = cursor.fetchall()

    cursor.execute("SELECT type FROM files WHERE user_id=?", (user_id,))
    types_my_file = cursor.fetchall()

    cursor.execute("SELECT views FROM files WHERE user_id=?", (user_id,))
    views = cursor.fetchall()

    cursor.execute("SELECT password FROM files WHERE user_id=?", (user_id,))
    passwords = cursor.fetchall()

    # Добавляем запрос для извлечения имен файлов
    cursor.execute("SELECT file_name FROM files WHERE user_id=?", (user_id,))
    file_names = cursor.fetchall()

    return types_my_file, fileIDs, views, passwords, file_names


# У мене з'явилася прикольна ідея, я подивився схожі файлообмінники
def view_updater(code):
    db = sqlite3.connect("data.db", check_same_thread=False)
    cursor = db.cursor()
    cursor.execute("SELECT views FROM files WHERE code=?", (code,))
    views = cursor.fetchone()
    cursor.execute(
        """UPDATE files SET views = ? WHERE code = ?""", (int(views[0]) + 1, code)
    )
    db.commit()

# І побачив те, що в інших немає лічильника скачувань, я думаю, можна щось подібне реалізувати
def delete_file(code):
    db = sqlite3.connect("data.db", check_same_thread=False)
    cursor = db.cursor()
    cursor.execute("DELETE FROM files WHERE code = ?", (code,))
    db.commit()

# Я бачив різне розв'язання проблеми те що tgAPI не дає для конкретного юзера програми обробляти конкретним алгоритмом 
class IsPrivate(BoundFilter):
    async def check(self, message: types.Message):
        return message.chat.type == types.ChatType.PRIVATE
# Мені здається моє рішення має місце бути, я зроблю так, щоб користувачеві прив'язувався статус запиту
class Info(StatesGroup):
    upload_file = State()
    upload_file_password = State()
    main_delete_button = State()
    check_password = State()
# Уже зробив два статуси активності, статус очікування файлу, і статус очікування пароля файлу хоча я ще не придумав до кінця з паролями
bot = Bot(token=TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

# Вирішив цього разу винести меню в окремі функції, спочатку думав зробити клас, але напевно це занадто
def main_menu_buttons():
	button1 = KeyboardButton('📩 Завантажити файл')
	button2 = KeyboardButton('🗃️ Особисті файли')
	main_menu_buttons = ReplyKeyboardMarkup(resize_keyboard=True)
	main_menu_buttons.add(button1)
	main_menu_buttons.add(button2)
	return main_menu_buttons

# На жаль, я не придумав як об'єднати кнопку скасування для завантаження файлу і скасування видалення
def back_button():
	button1 = KeyboardButton('Отмена')
	back_button1 = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
	back_button1.add(button1)
	return back_button1


def main_delete_button():
	markup = InlineKeyboardMarkup()
	btn2 = InlineKeyboardButton(text='🧺Видалити файл', callback_data=f'main_delete_button')
	markup.add(btn2)
	return markup
	
# Зробив додаткову кнопку для повернення, мені це дуже не подобається
def back_delete_button():
	markup = InlineKeyboardMarkup()
	btn2 = InlineKeyboardButton(text='Отмена', callback_data=f'back_delete_button')
	markup.add(btn2)
	return markup

# До речі ідеї зі станом активності я придумав коли писав свого першого бота
@dp.message_handler(IsPrivate(), commands=['start'], state='*')
async def start_command(message: types.Message, state: FSMContext):
	args = message.get_args()
	bot_data = await bot.get_me()
	bot_name = bot_data['username']
	if user_exist(message.chat.id) == False:
		add_user_to_db(message.chat.id)
		if not args:
			await bot.send_message(chat_id=message.chat.id, text='Вітаю тебе на нашому файлообміннику! 🌐Мене звуть {bot_name}, і я тут, щоб полегшити твій досвід обміну файлами. Безпечно, зручно та ефективно - це те, що я пропоную.', reply_markup = main_menu_buttons())
		else:
			type_file, fileID, views, password = get_file(args)
			if type_file is None and fileID is None:
				await bot.send_message(chat_id=message.chat.id, text='Файл втрачено...', reply_markup = main_menu_buttons())
			else:
				if password == (None,): # Зробив лічильник відкриття файлу
					view_updater(args)
					if type_file[0] == 'photo': # Перейменував його в "перегляди"
						await bot.send_photo(chat_id=message.chat.id, photo=fileID[0], caption=f'👁 Перегляди: {int(views[0])+1}', reply_markup = main_menu_buttons())
					elif type_file[0] == 'video':
						await bot.send_video(chat_id=message.chat.id, video=fileID[0], caption=f'👁 Перегляди: {int(views[0])+1}', reply_markup = main_menu_buttons())
					elif type_file[0] == 'voice':
						await bot.send_voice(chat_id=message.chat.id, voice=fileID[0], caption=f'👁 Перегляди: {int(views[0])+1}', reply_markup = main_menu_buttons())
					elif type_file[0] == 'document':
						await bot.send_document(chat_id=message.chat.id, document=fileID[0], caption=f'👁 Перегляди: {int(views[0])+1}', reply_markup = main_menu_buttons())
				else:# Ще не зробив захист файлу паролем, але заздалегідь зроблю виняток
					await bot.send_message(chat_id=message.chat.id, text='Файл захищений паролем🔒, для доступу до файлу введіть пароль:', reply_markup = back_button())# Скористаюся тим, що поле пароля не порожнє поле, і не буду паритися, все таки залишу, НЕ БАГ А ФІЧА
					await state.update_data(check_password=args)
					await Info.check_password.set()
	else:
		if not args: # Уже шкодую, що на python пишу, через те що відвик до табуляції
			await bot.send_message(chat_id=message.chat.id, text='Вітаю тебе на нашому файлообміннику! 🌐Мене звуть MyFyles, і я тут, щоб полегшити твій досвід обміну файлами. Безпечно, зручно та ефективно - це те, що я пропоную.', reply_markup = main_menu_buttons())
		else:
			type_file, fileID, views, password = get_file(args)
			if type_file is None and fileID is None:
				await bot.send_message(chat_id=message.chat.id, text='Файл втрачено...', reply_markup = main_menu_buttons())
			else:
				if password == (None,):
					view_updater(args) # Не люблю повторювати код, але придумувати щось із цим мені ліньки
					if type_file[0] == 'photo':
						await bot.send_photo(chat_id=message.chat.id, photo=fileID[0], caption=f'👁 Перегляди: {int(views[0])+1}', reply_markup = main_menu_buttons())
					elif type_file[0] == 'video':
						await bot.send_video(chat_id=message.chat.id, video=fileID[0], caption=f'👁 Перегляди: {int(views[0])+1}', reply_markup = main_menu_buttons())
					elif type_file[0] == 'voice':
						await bot.send_voice(chat_id=message.chat.id, voice=fileID[0], caption=f'👁 Перегляди: {int(views[0])+1}', reply_markup = main_menu_buttons())
					elif type_file[0] == 'document':
						await bot.send_document(chat_id=message.chat.id, document=fileID[0], caption=f'👁 Перегляди: {int(views[0])+1}', reply_markup = main_menu_buttons())
				else: # Чому бог не додав Case до python..
					await bot.send_message(chat_id=message.chat.id, text='Файл захищений паролем🔒, для доступу до файлу введіть пароль:', reply_markup = back_button())
					await state.update_data(check_password=args)
					await Info.check_password.set()

@dp.message_handler(state=Info.check_password, content_types=types.ContentTypes.ANY) # До речі про статуси , мій перший бот, де я використовував статуси, був на js і у 2021 року
async def upload_file(message: types.Message, state: FSMContext):
	bot_data = await bot.get_me()
	bot_name = bot_data['username']
	if message.text: 
		if message.text.lower() == 'отмена':
			await bot.send_message(chat_id=message.chat.id, text='Ви повернулися в головне меню.🏠', reply_markup=main_menu_buttons())
			await state.finish()
		else:
			user_data = await state.get_data()
			code = user_data['check_password']
			type_file, fileID, views, password = get_file(code) # Писав я його на замовлення від знайомого, який робив свій бізнес із перепродажу

			if message.text == password[0]:
				view_updater(code)
				if type_file[0] == 'photo':
					await bot.send_photo(chat_id=message.chat.id, photo=fileID[0], caption=f'👁 Перегляди: {int(views[0])+1}', reply_markup = main_menu_buttons())
				elif type_file[0] == 'video':
					await bot.send_video(chat_id=message.chat.id, video=fileID[0], caption=f'👁 Перегляди: {int(views[0])+1}', reply_markup = main_menu_buttons())
				elif type_file[0] == 'voice':
					await bot.send_voice(chat_id=message.chat.id, voice=fileID[0], caption=f'👁 Перегляди: {int(views[0])+1}', reply_markup = main_menu_buttons())
				elif type_file[0] == 'document':
					await bot.send_document(chat_id=message.chat.id, document=fileID[0], caption=f'👁 Перегляди: {int(views[0])+1}', reply_markup = main_menu_buttons())
				await state.finish()
			else:
				await bot.send_message(chat_id=message.chat.id, text='😔Упс, це не вірний пароль, спробуй ще раз:', reply_markup = back_button())
	else:
		await bot.send_message(chat_id=message.chat.id, text='😔Упс, це не вірний пароль, спробуй ще раз:', reply_markup = back_button())


@dp.message_handler(text="📩 Завантажити файл") # Парився я зі стрічкою замовлень і управлінням цін дуже довго у першому боті
async def create_post(message: types.Message):
	if user_exist(message.chat.id) == True:
		await bot.send_message(chat_id=message.chat.id, text='Надішли мені файл.', reply_markup = back_button())
		await Info.upload_file.set()

@dp.message_handler(text="🗃️ Особисті файли")
async def create_post(message: types.Message):
    if user_exist(message.chat.id) == True:
        bot_data = await bot.get_me()
        bot_name = bot_data['username']
        all_types, all_ids, all_views, passwords, file_name = get_files(message.from_user.id)

        if not all_types:
            await bot.send_message(chat_id=message.chat.id, text='У вас немає завантажених файлів, щоб завантажити файли натисніть "📩 Завантажити файл"', reply_markup=main_menu_buttons())
        else:
            file_message = ""
            for i, id_file in enumerate(all_ids):
                file_message += (
                    f"{i + 1} | https://t.me/{bot_name}?start={id_file[0]} | \n"
                    f"📁 {file_name[i][0]} | 👁 {all_views[i][0]} | 🔒{passwords[i][0]}\n"
                )

            await bot.send_message(chat_id=message.chat.id, text=file_message, reply_markup=main_delete_button())

@dp.message_handler(state=Info.upload_file_password, content_types=types.ContentTypes.TEXT) # Не пам'ятаю що там із таймаутами в TG але сподіваюся обійдуся без всякого
async def upload_file(message: types.Message, state: FSMContext):
	bot_data = await bot.get_me()
	bot_name = bot_data['username']
	user_data = await state.get_data()
	file_data = user_data['upload_file_password']

	if message.text == '-': # Думав, може, варто зробити кнопкою, а то мене бісить, що треба відкривати клавіатуру
		if file_data.split('|')[1] == 'photo':
			code = file_data.split('|')[2]
			add_new_file(file_data.split('|')[0], 'photo', file_data.split('|')[2], file_data.split('|')[3], file_data.split('|')[4])

			await bot.send_message(chat_id=message.chat.id, text=f'📁Файл було успішно завантажено.\n\n🔗Щоб поділитися ним відправ це посилання: https://t.me/{bot_name}?start={code}', reply_markup=main_menu_buttons())
			await state.finish()
		elif file_data.split('|')[1] == 'video':
			code = file_data.split('|')[2]
			add_new_file(file_data.split('|')[0], 'video', file_data.split('|')[2], file_data.split('|')[3], file_data.split('|')[4])
			await bot.send_message(chat_id=message.chat.id, text=f'📁Файл було успішно завантажено.\n\n🔗Щоб поділитися ним відправ це посилання: https://t.me/{bot_name}?start={code}', reply_markup=main_menu_buttons())
			await state.finish()
		elif file_data.split('|')[1] == 'voice':
			code = file_data.split('|')[2]
			add_new_file(file_data.split('|')[0], 'voice', file_data.split('|')[2], file_data.split('|')[3], file_data.split('|')[4])
			await bot.send_message(chat_id=message.chat.id, text=f'📁Файл було успішно завантажено.\n\n🔗Щоб поділитися ним відправ це посилання: https://t.me/{bot_name}?start={code}', reply_markup=main_menu_buttons())
			await state.finish()
		elif file_data.split('|')[1] == 'document':
			code = file_data.split('|')[2]
			add_new_file(file_data.split('|')[0], 'document', file_data.split('|')[2], file_data.split('|')[3], file_data.split('|')[4])
			await bot.send_message(chat_id=message.chat.id, text=f'📁Файл було успішно завантажено.\n\n🔗Щоб поділитися ним відправ це посилання: https://t.me/{bot_name}?start={code}', reply_markup=main_menu_buttons())
			await state.finish()
	elif message.text.lower() == 'отмена':
		await bot.send_message(chat_id=message.chat.id, text='Ви повернулися в головне меню.🏠', reply_markup=main_menu_buttons())
		await state.finish() # Шкода що мені не заплатять за це, бо тієї атмосфери за яку я люблю проограмування не має(
	else:
		if file_data.split('|')[1] == 'photo':
			code = file_data.split('|')[2]
			add_new_pass_file(file_data.split('|')[0], 'photo', file_data.split('|')[2], file_data.split('|')[3], message.text, file_data.split('|')[4])
			await bot.send_message(chat_id=message.chat.id, text=f'📁Файл було успішно завантажено.\n\n🔒Пароль: {message.text}\n\n🔗Щоб поділитися ним відправ це посилання: https://t.me/{bot_name}?start={code}', reply_markup=main_menu_buttons())
			await state.finish()
		elif file_data.split('|')[1] == 'video': # Я ентузіаст у програмуванні, але тільки тоді, коли є особливий вайб
			code = file_data.split('|')[2]
			add_new_pass_file(file_data.split('|')[0], 'video', file_data.split('|')[2], file_data.split('|')[3], message.text, file_data.split('|')[4])
			await bot.send_message(chat_id=message.chat.id, text=f'📁Файл було успішно завантажено.\n\n🔒Пароль: {message.text}\n\n🔗Щоб поділитися ним відправ це посилання: https://t.me/{bot_name}?start={code}', reply_markup=main_menu_buttons())
			await state.finish()
		elif file_data.split('|')[1] == 'voice':
			code = file_data.split('|')[2]
			add_new_pass_file(file_data.split('|')[0], 'voice', file_data.split('|')[2], file_data.split('|')[3], message.text, file_data.split('|')[4])
			await bot.send_message(chat_id=message.chat.id, text=f'📁Файл було успішно завантажено.\n\n🔒Пароль: {message.text}\n\n🔗Щоб поділитися ним відправ це посилання: https://t.me/{bot_name}?start={code}', reply_markup=main_menu_buttons())
			await state.finish()
		elif file_data.split('|')[1] == 'document':
			code = file_data.split('|')[2]
			add_new_pass_file(file_data.split('|')[0], 'document', file_data.split('|')[2], file_data.split('|')[3], message.text, file_data.split('|')[4])
			await bot.send_message(chat_id=message.chat.id, text=f'📁Файл було успішно завантажено.\n\n🔒Пароль: {message.text}\n\n🔗Щоб поділитися ним відправ це посилання: https://t.me/{bot_name}?start={code}', reply_markup=main_menu_buttons())
			await state.finish()


# { 
# 	"special vibe": [
# 		"weather": "rain",
# 		"drink": [
# 			"drink type": "coffee",
# 			"sugar": "one teaspoon",
# 			"temperature": "mood-wise",
# 			"cup": "personal"
# 		]
# 		"Time": "late evening",
# 		"outfit": "soft sleepwear",
# 		"music": [
# 			"volum": "mild",
# 			"language": "ENG && UA",
# 		]
		
# 	]
# }


@dp.message_handler(state=Info.upload_file, content_types=types.ContentTypes.ANY)
async def upload_file(message: types.Message, state: FSMContext):
	bot_data = await bot.get_me()
	bot_name = bot_data['username']
	file_name = message.document.file_name if message.document else 'media'
	if message.photo: # Який жах у телеграма з цими типами файлів чому ФОТО це не файл через це я змушений повторюватися 
		fileID = message.photo[-1].file_id
		code = ''.join(random.sample(ascii_letters + digits, random.randint(33, 40)))
		await state.update_data(upload_file_password=f'{message.from_user.id}|photo|{code}|{fileID}|{file_name}')
		await bot.send_message(chat_id=message.chat.id, text='Введи пароль🔒 для файлу. Якщо не хочеш, то напиши "-".', reply_markup=back_button())
		await Info.upload_file_password.set()
	elif message.text: # Який жах у телеграма з цими типами файлів чому ФОТО це не файл через це я змушений повторюватися 
		if message.text.lower() == 'отмена':
			await bot.send_message(chat_id=message.chat.id, text='Ти повернувся назад.🔙', reply_markup=main_menu_buttons())
			await state.finish()
		else:
			await bot.send_message(chat_id=message.chat.id, text='Надішли мені файл.', reply_markup=back_button())
	elif message.voice: # Який жах у телеграма з цими типами файлів чому ФОТО це не файл через це я змушений повторюватися 
		fileID = message.voice.file_id
		code = ''.join(random.sample(ascii_letters + digits, random.randint(33, 40)))
		await state.update_data(upload_file_password=f'{message.from_user.id}|voice|{code}|{fileID}|{file_name}')
		await bot.send_message(chat_id=message.chat.id, text='Введи пароль🔒 для файлу. Якщо не хочеш, то напиши "-".', reply_markup=back_button())
		await Info.upload_file_password.set()
	elif message.video: # Який жах у телеграма з цими типами файлів чому ФОТО це не файл через це я змушений повторюватися 
		fileID = message.video.file_id
		code = ''.join(random.sample(ascii_letters + digits, random.randint(33, 40)))
		await state.update_data(upload_file_password=f'{message.from_user.id}|video|{code}|{fileID}|{file_name}')
		await bot.send_message(chat_id=message.chat.id, text='Введи пароль🔒 для файлу. Якщо не хочеш, то напиши "-".', reply_markup=back_button())
		await Info.upload_file_password.set()
	elif message.document: # Який жах у телеграма з цими типами файлів чому ФОТО це не файл через це я змушений повторюватися 
		fileID = message.document.file_id
		code = ''.join(random.sample(ascii_letters + digits, random.randint(33, 40)))
		await state.update_data(upload_file_password=f'{message.from_user.id}|document|{code}|{fileID}|{file_name}')
		await bot.send_message(chat_id=message.chat.id, text='Введи пароль🔒 для файлу. Якщо не хочеш, то напиши "-".', reply_markup=back_button())
		await Info.upload_file_password.set()

@dp.message_handler(state=Info.main_delete_button, content_types=types.ContentTypes.TEXT)
async def del_file(message: types.Message, state: FSMContext):
	try:
		number = int(message.text)
		user_data = await state.get_data()
		mess_id = user_data['main_delete_button'] # Все таки роблю окрему кнопку, не зміг придумати як зробити це однією кнопкою
		all_types, all_ids, all_views, passwords, file_name = get_files(message.from_user.id)
		if number > len(all_ids):
			await bot.send_message(chat_id=message.chat.id, text='Такого файлу не існує. Введи номер файлу:', reply_markup=back_delete_button())
		else:
			delete_file(all_ids[(number-1)][0]) # У мене з'явилася проблема з id файлу і видаленням файла
			await bot.delete_message(message.chat.id, mess_id) # Після видалення лічильник id не хоче скидатися 
			await bot.send_message(chat_id=message.chat.id, text='Ви успішно видалили файл!', reply_markup=main_menu_buttons())
			await state.finish()
	except ValueError:
		await bot.send_message(chat_id=message.chat.id, text='Введи номер файлу:', reply_markup=back_delete_button())


@dp.callback_query_handler(state='*')
async def handler_call(call: types.CallbackQuery, state: FSMContext):
	bot_data = await bot.get_me()
	bot_name = bot_data['username']
	chat_id = call.from_user.id
	if call.data == 'main_delete_button': # Підтвердження видалення файлу я думаю не буде зайвим
		all_types, all_ids, all_views, passwords, file_name = get_files(chat_id)
		if all_ids == []:
			await bot.delete_message(chat_id, call.message.message_id)
			await bot.send_message(chat_id=chat_id, text='У вас немає завантажених файлів, щоб завантажити файли натисніть "📩 Завантажити файл"', reply_markup = main_menu_buttons())
		else:
			text='Який файл видаляемо?: \n\n'
			for i, id_file in enumerate(all_ids):
				text+=f'{i+1}. https://t.me/{str(bot_name)}?start={id_file[0]} | {file_name[i][0]}\n\n'
			text+='Введи номер файлу, який ти хочеш видалити.'
			await bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text=text, reply_markup=back_delete_button())
			await state.update_data(main_delete_button=call.message.message_id)
			await Info.main_delete_button.set()
	if call.data == 'back_delete_button':
		await state.finish()
		all_types, all_ids, all_views, passwords, file_name = get_files(chat_id)
		if all_ids == []: # Взагалі те що я тут написав у цьому рядку маячня, і так краще не робити
			await bot.delete_message(chat_id, call.message.message_id)
			await bot.send_message(chat_id=chat_id, text='У вас немає завантажених файлів, щоб завантажити файли натисніть "📩 Завантажити файл"', reply_markup = main_menu_buttons())
		else:

			for i, id_file in enumerate(all_ids):

				file_message = (
					f"{i + 1} | https://t.me/{str(bot_name)}?start={id_file[0]} \n"
					f"📁 {file_name}👁 {all_views[i][0]} | 🔒{passwords[i][0]}"
				) # За ідеєю я повинен був зробити цю частину коду через try але мені тааааак не хочеться 

			await bot.send_message(chat_id=chat_id, text=file_message, reply_markup=main_delete_button()) # 4:50 12.01.2024 я зробив основну частину, хочу ще зробити панель адміністратора
			# 7:34 12.01.2024 з'явилася ідея зробити файл, який зникає в певну годину, вирешив записати

if __name__ == "__main__":
	verif_db()
	# Запускаем бота
	executor.start_polling(dp, skip_updates=True)