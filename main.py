# Привіт читач, це пародiя на мого старого бота Scarl3t, повністю весь функціонал я не перенесу, 
# бо писав його я близько 2 тижнів, а на цей у мене відсили кілька днів разом з оформленням тз, тезами і всілякою фігнею,
# якщо цікаво, що за скарлет, ось посилання: https://github.com/konstie1/Scarl3t-file-sharing-service
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
import asyncio
import cv2
from datetime import datetime, timedelta
import numpy as np
import requests
from PIL import Image, ImageDraw, ImageFont
import os
#import json
#import speech_recognition as sr
# Я буду супроводжувати тебе весь код, тож давай знайомитися

ADMIN_ID = 6100695964

# Я ваня або Konstie, а це токен або token

TOKEN = "6557090734:AAEoJgWr0tciJ6MX_svl3cw0sikkVFVycl4"

# А тут простая проверка БД нечего особенного..

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
		"CREATE TABLE files(user_id INT, type TEXT, code TEXT, file_id TEXT, views INT DEFAULT (0), password TEXT, file_name TEXT, file_date TEXT, fire_date TEXT)"
		)

	db.commit()

current_date = datetime.now() # Час я думаю потрiбен

# Взагалі я коменти пишу під час написання коду, але оскільки я себе знаю, код буду 100 разів рефакторити, тож усе ж таки коментарі буду якось структурувати у кінці, щоб ми разом ішли згори донизу по коду)
def user_exist(user_id):
    db = sqlite3.connect("data.db", check_same_thread=False)
    cursor = db.cursor()
    cursor.execute("SELECT user_id FROM users WHERE user_id=?", (user_id,))

    if cursor.fetchone() is None:
        return False
    else:
        return True

 # Тут мала бути обробка БД для тимчасових файлів

# def add_new_file_with_fire_date(user_id, file_type, file_id, file_size, file_name, password, expiration_date):

#     conn = sqlite3.connect('data.db') # Мені чомусь не подобається ця частина коду
#     cursor = conn.cursor()

#     query = """
#     INSERT INTO files (user_id, file_type, file_id, file_size, file_name, password, expiration_date)
#     VALUES (?, ?, ?, ?, ?, ?, ?)
#     ON CONFLICT(file_id) DO UPDATE SET
#         user_id = excluded.user_id,
#         file_type = excluded.file_type,
#         file_size = excluded.file_size,
#         file_name = excluded.file_name,
#         password = excluded.password,
#         expiration_date = excluded.expiration_date;
#     """

#     cursor.execute(query, (user_id, file_type, file_id, file_size, file_name, password, expiration_date))

#     conn.commit()
#     conn.close()


# 17.1.2024

# До речі, я довго думав, як краще зробити базу даних, зрештою вирішив зробити sqlite3 хоча в минулих схожих проектах використовував json
def add_user_to_db(user_id):
    db = sqlite3.connect("data.db", check_same_thread=False)
    cursor = db.cursor()
    user = [user_id]
    cursor.execute(f"""INSERT INTO users(user_id) VALUES(?)""", user)
    db.commit()

# Але для конкурсу sqlite3 має більш потужніший вигляд, та й у json потрібно париться зі збереженнями, backup і всякою такою шнягою
def add_new_file(user_id, type, code, file_id, file_name, file_date):
    db = sqlite3.connect("data.db", check_same_thread=False)
    cursor = db.cursor()
    data = [user_id, type, code, file_id, file_name, file_date, None]  
    cursor.execute("INSERT INTO files(user_id, type, code, file_id, file_name, file_date, fire_date) VALUES(?,?,?,?,?,?,?)", data)
    db.commit()


# def audio_to_text(audio_file):
#     recognizer = sr.Recognizer()

#     with sr.AudioFile(audio_file) as source:
#         audio_data = recognizer.record(source)

#     try:
#         text = recognizer.recognize_google(audio_data, language='ru-RU')
#         return text
#     except sr.UnknownValueError:
#         return "Не удалось распознать аудио"
#     except sr.RequestError:
#         return "Ошибка запроса; проверьте подключение к интернету"


# Я так і не придумав нормально як зробити паролі, в результаті вийшла, друга функцiя
def add_new_pass_file(user_id, type, code, file_id, password, file_name, file_date):
    db = sqlite3.connect("data.db", check_same_thread=False)
    cursor = db.cursor()
    data = [user_id, type, code, file_id, password, file_name, file_date, None]  # Include 'None' for 'fire_date'
    cursor.execute("INSERT INTO files(user_id, type, code, file_id, password, file_name, file_date, fire_date) VALUES(?,?,?,?,?,?,?,?)", data)
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
	cursor.execute("SELECT file_name FROM files WHERE code=?", (code,))
	file_name = cursor.fetchone()
	cursor.execute("SELECT file_date FROM files WHERE code=?", (code,))
	file_date = cursor.fetchone()
	return type_file, fileID, views, password, file_name, file_date

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

	cursor.execute("SELECT file_name FROM files WHERE user_id=?", (user_id,))
	file_names = cursor.fetchall()

	cursor.execute("SELECT file_date FROM files WHERE user_id=?", (user_id,))
	file_date = cursor.fetchall()

	cursor.execute("SELECT fire_date FROM files WHERE user_id=?", (user_id,))
	fire_date = cursor.fetchall()

	return types_my_file, fileIDs, views, passwords, file_names, file_date, fire_date



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

async def blur_image(image_path):
	blur_intensity=60
	image = cv2.imread(image_path)
	if image is None:
		return None

	small_image = cv2.resize(image, (0,0), fx=0.009, fy=0.009)

	resized_image = cv2.resize(small_image, (image.shape[1], image.shape[0]))

	bot_data = await bot.get_me()
	bot_name = bot_data['username']
	blurred_image = cv2.blur(resized_image, (blur_intensity, blur_intensity))

	font = cv2.FONT_HERSHEY_SIMPLEX
	font_scale = 1
	font_color = (255, 255, 255) 
	font_thickness = 2
	text_size = cv2.getTextSize(f'@{bot_name}', font, font_scale, font_thickness)[0]
	text_x = (blurred_image.shape[1] - text_size[0]) // 2
	text_y = (blurred_image.shape[0] + text_size[1]) // 2

	cv2.putText(blurred_image, f'@{bot_name}', (text_x, text_y), font, font_scale, font_color, font_thickness)




	cv2.imwrite(image_path, blurred_image)

	return image_path

# І побачив те, що в інших немає лічильника скачувань, я думаю, можна щось подібне реалізувати
def delete_file(code):
	db = sqlite3.connect("data.db", check_same_thread=False)
	cursor = db.cursor()
	cursor.execute("DELETE FROM files WHERE code = ?", (code,))
	db.commit()

async def main_fire_date_button(code, fire_date_hours):
    db = sqlite3.connect("data.db", check_same_thread=False)
    cursor = db.cursor()

    fire_date = datetime.now() + timedelta(hours=fire_date_hours)

    try:
        fire_date_str = fire_date.strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""UPDATE files SET fire_date = ? WHERE code = ?""", (fire_date_str, code))
        db.commit()
    except sqlite3.Error as e:
        print(f"Помилка при оновленні fire_date: {e}")
    finally:
        db.close()

# Я бачив різне розв'язання проблеми те що tgAPI не дає для конкретного юзера програми обробляти конкретним алгоритмом 
class IsPrivate(BoundFilter):
    async def check(self, message: types.Message):
        return message.chat.type == types.ChatType.PRIVATE
# Мені здається моє рішення має місце бути, я зроблю так, щоб користувачеві прив'язувався статус запиту
class action(StatesGroup):
	alert = State() 
	# Смішна ідея є зробити блок юзера не через ЧС
	# А через статус))
	main_fire_date_button = State()
	upload_file = State()
	upload_file_password = State()
	main_delete_button = State()
	check_password = State()
	fire_date = State()
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


# # def preview_button(): # Вирішив додати попередній перегляд для запоролених файлів
# # 	InlineKeyboardButton('👀Предперегляд')
	
# def preview_button(): 
# 	button1 = InlineKeyboardButton('👀Предперегляд', callback_data='preview_button')
# 	return InlineKeyboardMarkup().add(button1)
	


def main_delete_button():
	markup = InlineKeyboardMarkup()
	btn2 = InlineKeyboardButton(text='🧺Видалити файл', callback_data=f'main_delete_button')
	markup.add(btn2)
	btn3 = InlineKeyboardButton(text='⏲Таймер файлу', callback_data=f'main_fire_date_button')
	markup.add(btn3)
	return markup

	
def get_file_size(file_path):
    try:
        size_in_bytes = os.path.getsize(file_path)
        return round(size_in_bytes / (1024 ** 3), 3)  # Convert bytes to gigabytes
	
    except OSError as e:
        print(f"Error: {e}")
        return None
	
def virus_total_check(file_path, api_key='68174e55354b900b581848997b2b66d5e948b20c9c10a834b11f1fabc79da76f'):
    url = 'https://www.virustotal.com/vtapi/v2/file/scan'
    params = {'apikey': api_key}

    files = {'file': (file_path, open(file_path, 'rb'))}
    response = requests.post(url, files=files, params=params)

    if response.status_code != 200:
        return "Ошибка при сканировании файла"

    json_response = response.json()
    resource = json_response.get('resource')

    url_report = 'https://www.virustotal.com/vtapi/v2/file/report'
    params_report = {'apikey': api_key, 'resource': resource}

    report_response = requests.get(url_report, params=params_report)

    if report_response.status_code != 200:
        return "Ошибка при получении отчета"

    report_json = report_response.json()
    detections = report_json.get('positives')
    total = report_json.get('total')

    return f"{detections}/{total}"

# Зробив додаткову кнопку для повернення, мені це дуже не подобається
def back_delete_button():
	markup = InlineKeyboardMarkup()
	btn2 = InlineKeyboardButton(text='Отмена', callback_data=f'back_delete_button')
	markup.add(btn2)
	return markup

def write_on_image(fileid, format_file, file_name, file_size, virus_total, image_path):

    img = Image.open(image_path)

    draw = ImageDraw.Draw(img)


    font = ImageFont.truetype('assets/Roboto-Black.ttf', size=20)

    positions = {

        "format_file": (100, 30),

        "file_name": (100, 100), 

        "file_size": (100, 170), 

        "virus_total": (400, 170) 

    }
    draw.text(positions["format_file"], format_file, font=font, fill="black")

    draw.text(positions["file_name"], file_name, font=font, fill="black")

    draw.text(positions["file_size"], file_size, font=font, fill="black")

    draw.text(positions["virus_total"], virus_total, font=font, fill="black")
	
    output_path = os.path.join('assets/temp', f'{fileid}.png')

    img.save(output_path)

    return output_path


# До речі ідеї зі станом активності я придумав коли писав свого першого бота
@dp.message_handler(IsPrivate(), commands=['start'], state='*')
async def start_command(message: types.Message, state: FSMContext):
	args = message.get_args()
	bot_data = await bot.get_me()
	bot_name = bot_data['username']

	if user_exist(message.chat.id) == False:
		add_user_to_db(message.chat.id)

	if not args:
		await bot.send_message(chat_id=message.chat.id, text=f'Вітаю тебе на нашому файлообміннику! 🌐Мене звуть {bot_name}, і я тут, щоб полегшити твій досвід обміну файлами. Безпечно, зручно та ефективно - це те, що я пропоную.', reply_markup = main_menu_buttons())
	
	else:
		type_file, fileID, views, password, file_name, file_date = get_file(args)
		if type_file is None and fileID is None:
			await bot.send_message(chat_id=message.chat.id, text='Файл втрачено...', reply_markup = main_menu_buttons())
			
		else:
#			await bot.get_file(fileID[0])
			# file = await bot.get_file(fileID[0])
			# await bot.download_file(file.file_path, 'file')

			if password == (None,): # Зробив лічильник відкриття файлу
				view_updater(args)

				if type_file[0] == 'photo': # Назвав його "перегляди"
					await bot.send_photo(chat_id=message.chat.id, photo=fileID[0], caption=f'👁 Перегляди: {int(views[0])+1}', reply_markup = main_menu_buttons())
				
				elif type_file[0] == 'video':

					await bot.send_video(chat_id=message.chat.id, video=fileID[0], caption=f'👁 Перегляди: {int(views[0])+1}', reply_markup = main_menu_buttons())
				
				elif type_file[0] == 'voice':
					await bot.send_voice(chat_id=message.chat.id, voice=fileID[0], caption=f'👁 Перегляди: {int(views[0])+1}', reply_markup = main_menu_buttons())
				
				elif type_file[0] == 'document':
					await bot.send_document(chat_id=message.chat.id, document=fileID[0], caption=f'👁 Перегляди: {int(views[0])+1}', reply_markup = main_menu_buttons())
		
			else:# Ще не зробив захист файлу паролем, але заздалегідь зроблю виняток
#				await bot.send_message(chat_id=message.chat.id, text='Тицьніть для попереднього перегляду файлу', reply_markup = KeyboardButton.preview_button())
#				all_types, all_ids, all_views, passwords, file_name = get_files(message.from_user.id)
				file_info = await bot.get_file(fileID[0])
				file_path = file_info.file_path

				if type_file[0] == 'photo': # 15.1.2025 22:26 вирішив зробити попередній перегляд файлу
					# почав із фото, зроблю просто цензуру фотографії
					file_save_path = f'assets/temp/{fileID[0]}.png'
					os.makedirs(os.path.dirname(file_save_path), exist_ok=True)

					await bot.send_message(message.chat.id, text='Предперегляд:')  

					await bot.download_file(file_path, file_save_path)

					await blur_image(file_save_path)

					with open(file_save_path, 'rb') as photo:
						await bot.send_photo(message.chat.id, photo=photo)

					os.remove(file_save_path)



				# elif type_file[0] == 'video': # була ідея брати перший кадр, але поки що краще зроблю щось інше
				# 	pass

				# elif type_file[0] == 'voice':
				#	pass

				elif type_file[0] == 'document':
					await bot.send_message(message.chat.id, text='Предперегляд:')
					os.makedirs(f'assets/temp/{fileID[0]}')
					await bot.download_file(file_path, f'assets/temp/{fileID[0]}/{file_name[0]}')
#					write_on_image(fileid=fileID[0], format_file=file_name[0].spilt('.')[0], file_name=file_name[0].spilt('.')[-1], file_size=get_file_size(f'assets/temp/{fileID[0]}/{file_name[0]}'), virus_total=virus_total_check('assets/temp/{fileID[0]}/{file_name[0]}'), image_path='assets/temp/{fileID[0]}/{file_name[0]}')
#					print(f'{fileID[0]}, {file_name[0].split('.')[0]}, {file_name[0].split('.')[-1]}, {get_file_size(f'assets/temp/{fileID[0]}/{file_name[0]}')}, {virus_total_check(f'assets/temp/{fileID[0]}/{file_name[0]}')},')
					if file_name and fileID:  
					    base_name, *_, extension = file_name[0].rpartition('.')
					    if base_name and extension:  
					        file_path = f'assets/temp/{fileID[0]}/{file_name[0]}'
					        file_size = get_file_size(file_path)
					        virus_check = virus_total_check(file_path)
					        
					        message_text = (
					            f'Название файла: {base_name}\n'
					            f'Тип файла: {extension}\n'
					            f'Вес файла: {file_size}GB\n'
					            f'VirusTotal: {virus_check}'
					        )
					        await bot.send_message(message.chat.id, text=message_text)
					    else:
					        await bot.send_message(message.chat.id, text="Ошибка: неверный формат имени файла.")
					else:
					    await bot.send_message(message.chat.id, text="Ошибка: отсутствуют данные о файле.")

					os.remove(f'assets/temp/{fileID[0]}/{file_name[0]}')
					os.removedirs(f'assets/temp/{fileID[0]}')

				await bot.send_message(message.chat.id, text='Файл захищений паролем🔒, для доступу до файлу введіть пароль:', reply_markup = back_button())# Скористаюся тим, що поле пароля не порожнє поле, і не буду паритися, все таки залишу, НЕ БАГ А ФІЧА
				await state.update_data(check_password=args) # Ось, до речі, приклад статусу активності 
				await action.check_password.set() 

		# if not args: # Уже шкодую, що на python пишу, через те що відвик до табуляції
		# 	await bot.send_message(chat_id=message.chat.id, text=f'Вітаю тебе на нашому файлообміннику! 🌐Мене звуть {bot_name}, і я тут, щоб полегшити твій досвід обміну файлами. Безпечно, зручно та ефективно - це те, що я пропоную.', reply_markup = main_menu_buttons())
		# else:
		# 	type_file, fileID, views, password = get_file(args)
		# 	if type_file is None and fileID is None:
		# 		await bot.send_message(chat_id=message.chat.id, text='Файл втрачено...', reply_markup = main_menu_buttons())
		# 	else:
		# 		if password == (None,):
		# 			view_updater(args) # Не люблю повторювати код, але придумувати щось із цим мені ліньки
		# 			if type_file[0] == 'photo':
		# 				await bot.send_photo(chat_id=message.chat.id, photo=fileID[0], caption=f'👁 Перегляди: {int(views[0])+1}', reply_markup = main_menu_buttons())
		# 			elif type_file[0] == 'video':
		# 				await bot.send_video(chat_id=message.chat.id, video=fileID[0], caption=f'👁 Перегляди: {int(views[0])+1}', reply_markup = main_menu_buttons())
		# 			elif type_file[0] == 'voice':
		# 				await bot.send_voice(chat_id=message.chat.id, voice=fileID[0], caption=f'👁 Перегляди: {int(views[0])+1}', reply_markup = main_menu_buttons())
		# 			elif type_file[0] == 'document':
		# 				await bot.send_document(chat_id=message.chat.id, document=fileID[0], caption=f'👁 Перегляди: {int(views[0])+1}', reply_markup = main_menu_buttons())
		# 		else: # Чому бог не додав Case до python..
		# 			await bot.send_message(chat_id=message.chat.id, text='Файл захищений паролем🔒, для доступу до файлу введіть пароль:', reply_markup = back_button())
		# 			await state.update_data(check_password=args)
		# 			await action.check_password.set()

@dp.message_handler(state=action.check_password, content_types=types.ContentTypes.ANY) # До речі про статуси , мій перший бот, де я використовував статуси, був на js і у 2021 року
async def upload_file(message: types.Message, state: FSMContext):

	if message.text: 

		if message.text.lower() == 'отмена':
			await bot.send_message(chat_id=message.chat.id, text='Ви повернулися в головне меню.🏠', reply_markup=main_menu_buttons())
			await state.finish()

		else:
			user_data = await state.get_data()
			code = user_data['check_password']
			type_file, fileID, views, password, file_name, file_date = get_file(code) # Писав я його на замовлення від знайомого, який робив свій бізнес із перепродажу

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
		await action.upload_file.set()

@dp.message_handler(text="🗃️ Особисті файли")
async def create_post(message: types.Message):
    if user_exist(message.chat.id) == True:
        bot_data = await bot.get_me()
        bot_name = bot_data['username']
        all_types, all_ids, all_views, passwords, file_name, file_date, fire_date = get_files(message.from_user.id)

        if not all_types:
            await bot.send_message(chat_id=message.chat.id, text='У вас немає завантажених файлів, щоб завантажити файли натисніть "📩 Завантажити файл"', reply_markup=main_menu_buttons())     
        
        else:
            file_message = ""
            for i, id_file in enumerate(all_ids):
                file_message += (
                    f"{i + 1} | https://t.me/{bot_name}?start={id_file[0]} | \n"
                    f"📁 {file_name[i][0]} | 👁 {all_views[i][0]} |⏲{fire_date[i][0]} |🔒{passwords[i][0]}\n"
                )

            await bot.send_message(chat_id=message.chat.id, text=file_message, reply_markup=main_delete_button())

@dp.message_handler(state=action.upload_file_password, content_types=types.ContentTypes.TEXT) # Не пам'ятаю що там із таймаутами в TG але сподіваюся обійдуся без всякого
async def upload_file(message: types.Message, state: FSMContext):
	bot_data = await bot.get_me()
	bot_name = bot_data['username']
	user_data = await state.get_data()
	file_data = user_data['upload_file_password']

	if message.text == '-': # Думав, може, варто зробити кнопкою, а то мене бісить, що треба відкривати клавіатуру

		if file_data.split('|')[1] == 'photo':
			code = file_data.split('|')[2]
			add_new_file(file_data.split('|')[0], 'photo', file_data.split('|')[2], file_data.split('|')[3], file_data.split('|')[4], file_data.split('|')[5])

			await bot.send_message(chat_id=message.chat.id, text=f'📁Файл було успішно завантажено.\n\n🔗Щоб поділитися ним відправ це посилання: https://t.me/{bot_name}?start={code}', reply_markup=main_menu_buttons())
			await state.finish()
	
		elif file_data.split('|')[1] == 'video':
			code = file_data.split('|')[2]
			add_new_file(file_data.split('|')[0], 'video', file_data.split('|')[2], file_data.split('|')[3], file_data.split('|')[4], file_data.split('|')[5])
			await bot.send_message(chat_id=message.chat.id, text=f'📁Файл було успішно завантажено.\n\n🔗Щоб поділитися ним відправ це посилання: https://t.me/{bot_name}?start={code}', reply_markup=main_menu_buttons())
			await state.finish()
	
		elif file_data.split('|')[1] == 'voice':
			code = file_data.split('|')[2]
			add_new_file(file_data.split('|')[0], 'voice', file_data.split('|')[2], file_data.split('|')[3], file_data.split('|')[4], file_data.split('|')[5])
			await bot.send_message(chat_id=message.chat.id, text=f'📁Файл було успішно завантажено.\n\n🔗Щоб поділитися ним відправ це посилання: https://t.me/{bot_name}?start={code}', reply_markup=main_menu_buttons())
			await state.finish()
	
		elif file_data.split('|')[1] == 'document':
			code = file_data.split('|')[2]
			add_new_file(file_data.split('|')[0], 'document', file_data.split('|')[2], file_data.split('|')[3], file_data.split('|')[4], file_data.split('|')[5])
			await bot.send_message(chat_id=message.chat.id, text=f'📁Файл було успішно завантажено.\n\n🔗Щоб поділитися ним відправ це посилання: https://t.me/{bot_name}?start={code}', reply_markup=main_menu_buttons())
			await state.finish()
	
	elif message.text.lower() == 'отмена':
		await bot.send_message(chat_id=message.chat.id, text='Ви повернулися в головне меню.🏠', reply_markup=main_menu_buttons())
		await state.finish() # Шкода що мені не заплатять за це, бо тієї атмосфери за яку я люблю проограмування не має(
	
	else:
		
		if file_data.split('|')[1] == 'photo':
			code = file_data.split('|')[2]
			add_new_pass_file(file_data.split('|')[0], 'photo', file_data.split('|')[2], file_data.split('|')[3], message.text, file_data.split('|')[4], file_data.split('|')[5])
			await bot.send_message(chat_id=message.chat.id, text=f'📁Файл було успішно завантажено.\n\n🔒Пароль: {message.text}\n\n🔗Щоб поділитися ним відправ це посилання: https://t.me/{bot_name}?start={code}', reply_markup=main_menu_buttons())
			await state.finish()
		
		elif file_data.split('|')[1] == 'video': # Я ентузіаст у програмуванні, але тільки тоді, коли є особливий вайб
			code = file_data.split('|')[2]
			add_new_pass_file(file_data.split('|')[0], 'video', file_data.split('|')[2], file_data.split('|')[3], message.text, file_data.split('|')[4], file_data.split('|')[5])
			await bot.send_message(chat_id=message.chat.id, text=f'📁Файл було успішно завантажено.\n\n🔒Пароль: {message.text}\n\n🔗Щоб поділитися ним відправ це посилання: https://t.me/{bot_name}?start={code}', reply_markup=main_menu_buttons())
			await state.finish()
		
		elif file_data.split('|')[1] == 'voice':
			code = file_data.split('|')[2]
			add_new_pass_file(file_data.split('|')[0], 'voice', file_data.split('|')[2], file_data.split('|')[3], message.text, file_data.split('|')[4], file_data.split('|')[5])
			await bot.send_message(chat_id=message.chat.id, text=f'📁Файл було успішно завантажено.\n\n🔒Пароль: {message.text}\n\n🔗Щоб поділитися ним відправ це посилання: https://t.me/{bot_name}?start={code}', reply_markup=main_menu_buttons())
			await state.finish()
		
		elif file_data.split('|')[1] == 'document':
			code = file_data.split('|')[2]
			add_new_pass_file(file_data.split('|')[0], 'document', file_data.split('|')[2], file_data.split('|')[3], message.text, file_data.split('|')[4], file_data.split('|')[5])
			await bot.send_message(chat_id=message.chat.id, text=f'📁Файл було успішно завантажено.\n\n🔒Пароль: {message.text}\n\n🔗Щоб поділитися ним відправ це посилання: https://t.me/{bot_name}?start={code}', reply_markup=main_menu_buttons())
			await state.finish()
	# await action.fire_date.set()
	# await message.answer("Please enter the lifespan of the file in hours:")

# @dp.message_handler(state=action.fire_date)
# async def fire_date_handler(message: types.Message, state: FSMContext):
#     fire_date_input = message.text

#     try:
#         hours = int(fire_date_input)
#         if hours <= 0:
#             raise ValueError("...")


#         expiration_date = datetime.now() + timedelta(hours=hours)


#         user_data = await state.get_data()
#         file_data = user_data['upload_file_password']

#         file_action = file_data.split('|') # Для різнобарвності зроблю по іншому
#         user_id = file_action[0]
#         file_type = file_action[1]
#         file_id = file_action[2]
#         file_size = file_action[3]
#         file_name = file_action[4]

#         password = file_action[5] if len(file_action) > 5 else None


#         add_new_file_with_fire_date(user_id, file_type, file_id, file_size, file_name, password, expiration_date) # На цьому етапі майже готовий код видалення файлу в певний час
# 		#Залишилося написати функцію add_new_file_with_fire_date
#         await message.answer(f"📁Файл було успішно завантажено і буде доступний до {expiration_date.strftime('%Y-%m-%d %H:%M:%S')}")

#     except ValueError:

#         await message.reply("Введіть коректну кількість годин. Спробуйте ще раз:")
#         return  
#     await state.finish()


# )))))))))))))))))))))))))))))))))

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


@dp.message_handler(state=action.upload_file, content_types=types.ContentTypes.ANY)
async def upload_file(message: types.Message, state: FSMContext):
	file_name = message.document.file_name if message.document else 'media'
	file_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
	
	if message.photo: # Який жах у телеграма з цими типами файлів чому ФОТО це не файл через це я змушений повторюватися 
		fileID = message.photo[-1].file_id
		code = ''.join(random.sample(ascii_letters + digits, random.randint(33, 40)))
		await state.update_data(upload_file_password=f'{message.from_user.id}|photo|{code}|{fileID}|{file_name}|{file_date}')
		await bot.send_message(chat_id=message.chat.id, text='Введи пароль🔒 для файлу. Якщо не хочеш, то напиши "-".', reply_markup=back_button())
		await action.upload_file_password.set()
	
	elif message.text: # Який жах у телеграма з цими типами файлів чому ФОТО це не файл через це я змушений повторюватися 
	
		if message.text.lower() == 'отмена':
			await bot.send_message(chat_id=message.chat.id, text='Ти повернувся назад.🔙', reply_markup=main_menu_buttons())
			await state.finish()
	
		else:
			await bot.send_message(chat_id=message.chat.id, text='Надішли мені файл.', reply_markup=back_button())
	
	elif message.voice: # Який жах у телеграма з цими типами файлів чому ФОТО це не файл через це я змушений повторюватися 
		fileID = message.voice.file_id
		code = ''.join(random.sample(ascii_letters + digits, random.randint(33, 40)))
		await state.update_data(upload_file_password=f'{message.from_user.id}|voice|{code}|{fileID}|{file_name}|{file_date}')
		await bot.send_message(chat_id=message.chat.id, text='Введи пароль🔒 для файлу. Якщо не хочеш, то напиши "-".', reply_markup=back_button())
		await action.upload_file_password.set()
	
	elif message.video: # Який жах у телеграма з цими типами файлів чому ФОТО це не файл через це я змушений повторюватися 
		fileID = message.video.file_id
		code = ''.join(random.sample(ascii_letters + digits, random.randint(33, 40)))
		await state.update_data(upload_file_password=f'{message.from_user.id}|video|{code}|{fileID}|{file_name}|{file_date}')
		await bot.send_message(chat_id=message.chat.id, text='Введи пароль🔒 для файлу. Якщо не хочеш, то напиши "-".', reply_markup=back_button())
		await action.upload_file_password.set()
	
	elif message.document: # Який жах у телеграма з цими типами файлів чому ФОТО це не файл через це я змушений повторюватися 
		fileID = message.document.file_id
		code = ''.join(random.sample(ascii_letters + digits, random.randint(33, 40)))
		await state.update_data(upload_file_password=f'{message.from_user.id}|document|{code}|{fileID}|{file_name}|{file_date}')
		await bot.send_message(chat_id=message.chat.id, text='Введи пароль🔒 для файлу. Якщо не хочеш, то напиши "-".', reply_markup=back_button())
		await action.upload_file_password.set()

@dp.message_handler(state=action.main_delete_button, content_types=types.ContentTypes.TEXT)
async def del_file(message: types.Message, state: FSMContext):
	
	try:
		number = int(message.text)
		user_data = await state.get_data()
		mess_id = user_data['main_delete_button'] # Все таки роблю окрему кнопку, не зміг придумати як зробити це однією кнопкою
		all_types, all_ids, all_views, passwords, file_name,file_date, fire_date = get_files(message.from_user.id)

		if number > len(all_ids):
			await bot.send_message(chat_id=message.chat.id, text='Такого файлу не існує. Введи номер файлу:', reply_markup=back_delete_button())
	
		else:
			delete_file(all_ids[(number-1)][0]) # У мене з'явилася проблема з id файлу і видаленням файла
			await bot.delete_message(message.chat.id, mess_id) # Після видалення лічильник id не хоче скидатися 
			await bot.send_message(chat_id=message.chat.id, text='Ви успішно видалили файл!', reply_markup=main_menu_buttons())
			await state.finish()
	
	except ValueError:
		await bot.send_message(chat_id=message.chat.id, text='Введи номер файлу:', reply_markup=back_delete_button())


@dp.message_handler(state=action.main_fire_date_button, content_types=types.ContentTypes.TEXT)
async def main_fire_date(message: types.Message, state: FSMContext):
	
	try:
		number, time = map(int, message.text.split('/'))
		user_data = await state.get_data()
		mess_id = user_data.get('main_fire_date_button')

		all_types, all_ids, all_views, passwords, file_name, file_date, fire_date = get_files(message.from_user.id)

		if number > len(all_ids):
			await bot.send_message(chat_id=message.chat.id, text='Такого файлу не існує. Введи номер файлу:', reply_markup=back_delete_button())
	
		else:
			file_id = all_ids[number - 1][0]
			await main_fire_date_button(file_id, time)
			await bot.delete_message(message.chat.id, mess_id) 
			await bot.send_message(chat_id=message.chat.id, text='Дата видалення файлу успішно оновлена', reply_markup=main_menu_buttons())
			await state.finish()
	
	except ValueError:
		await bot.send_message(chat_id=message.chat.id, text='Введи номер файлу:', reply_markup=back_delete_button())



@dp.callback_query_handler(state='*')
async def handler_call(call: types.CallbackQuery, state: FSMContext):
	bot_data = await bot.get_me()
	bot_name = bot_data['username']
	chat_id = call.from_user.id
	
	if call.data == 'main_delete_button': # Підтвердження видалення файлу я думаю не буде зайвим
		all_types, all_ids, all_views, passwords, file_name, file_date, fire_date = get_files(chat_id)
	
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
			await action.main_delete_button.set()
	


	if call.data == 'main_fire_date_button':
		all_types, all_ids, all_views, passwords, file_name, file_date, fire_date = get_files(chat_id)
	
		if all_ids == []:
			await bot.delete_message(chat_id, call.message.message_id)
			await bot.send_message(chat_id=chat_id, text='У вас немає завантажених файлів, щоб завантажити файли натисніть "📩 Завантажити файл"', reply_markup = main_menu_buttons())
	
		else:
			text='Який файл?: \n\n'
			for i, id_file in enumerate(all_ids):
				text+=f'{i+1}. https://t.me/{str(bot_name)}?start={id_file[0]} | {file_name[i][0]}\n\n'
			text+='Введіть номер файлу для створення таймера, Та час\nФормат НомерФайлу/ЧасУГодинах'
			await bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text=text, reply_markup=back_delete_button())
			await state.update_data(main_fire_date_button=call.message.message_id)
			await action.main_fire_date_button.set()


	if call.data == 'back_delete_button':
		await state.finish()
		all_types, all_ids, all_views, passwords, file_name, file_date, fire_date = get_files(chat_id)
	
		if all_ids == []: # Взагалі те що я тут написав у цьому рядку маячня, і так краще не робити
			await bot.delete_message(chat_id, call.message.message_id)
			await bot.send_message(chat_id=chat_id, text='У вас немає завантажених файлів, щоб завантажити файли натисніть "📩 Завантажити файл"', reply_markup = main_menu_buttons())
	
		else:

			for i, id_file in enumerate(all_ids):

				file_message = (
					f"{i + 1} | https://t.me/{str(bot_name)}?start={id_file[0]} \n"
					f"📁 {file_name[i][0]}👁 {all_views[i][0]} | 🔒{passwords[i][0]}"
				) # За ідеєю я повинен був зробити цю частину коду через try але мені тааааак не хочеться 

			await bot.send_message(chat_id=chat_id, text=file_message, reply_markup=main_delete_button()) # 4:50 12.01.2024 я зробив основну частину, хочу ще зробити панель адміністратора
			# 7:34 12.01.2024 з'явилася ідея зробити файл, який зникає в певну годину, вирешив записати

# 8:49 14.01.2024 другий захід на програмування цеi штуки
# Видалення файлу за часом не працює так як хотілося б
# Я поки що відволічуся і займуся адмінпанеллю
# Хочу зробити можливість сповіщення всіх користувачів бота
# I якщо придумаю якось, блокування і статистику

def ADMIN_KB(): # Винесу меню адміна окремо, хочу так!
	kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
	kb.add(types.InlineKeyboardButton(text="Рассылка"))
	kb.add(types.InlineKeyboardButton(text="Статистика"))
#	kb.add(types.InlineKeyboardButton(text="/start")) # Мені здається чому б і не додати для зручності
	# Я забув що у тг бота можна зробити меню команд...
	return kb
# Якби не ctrl+f я б не знайшов клас станів...
@dp.message_handler(commands=['admin'])
async def start(message: types.Message):
	
	if message.from_user.id == ADMIN_ID:
		await message.answer('Що накажете робити, хазяїне?', reply_markup=ADMIN_KB()) # Мені здається прикольно, а чому б і ні))
	
	else:
		await message.answer('Ти не мій хазяїн!') # Мій код, і я вирішую як він буде мене звати!

@dp.message_handler(content_types=['text'], text='Рассылка')
async def alert(message: types.Message):
  await action.alert.set()
  await message.answer('Надішли текст розсилки:')

@dp.message_handler(state=action.alert)
async def start_alert(message: types.Message, state: FSMContext):
	
	if message.text == '-':
		await message.answer('Адмiн меню', reply_markup=ADMIN_KB())
		await state.finish()
	
	else:
		db = sqlite3.connect("data.db", check_same_thread=False)
		cursor = db.cursor()
		cursor.execute(f'''SELECT user_id FROM users''') # Це жах, я перерив документацію. гуглив, питав у chatGPT 
		alert_base = cursor.fetchall()					 # Як зробити щоб розмітка зберігалася??/?/??
		
		for i in range(len(alert_base)):
			await bot.send_message(alert_base[i][0], message.text) # Уже 10.44 14.1.2024 Я так і не вирішив проблему з розміткою
			await state.finish()
		await message.answer('Рассылка завершена', reply_markup=ADMIN_KB()) # Цікаво а чи буде хтось взагалі це читати..

@dp.message_handler(content_types=['text'], text='Статистика')
async def hfandler(message: types.Message, state: FSMContext):
	db = sqlite3.connect("data.db", check_same_thread=False)
	cursor = db.cursor()
	cursor.execute('''select * from users''')
	results_user = cursor.fetchall()
	cursor.execute('''select * from files''')
	result_files = cursor.fetchall() # Хоча може варто додати кількість учасників за 24 години
	await message.answer(f'Кількість користувачів: {len(results_user)}\nКількість файлів: {len(result_files)}') # Я думаю, не варто робити динамічну статистику

async def delete_expired_files():
    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT file_id FROM files WHERE fire_date < ? AND fire_date IS NOT NULL", 
                       (datetime.now().strftime('%Y-%m-%d %H:%M:%S'),))
        expired_files = cursor.fetchall()
		
        for file in expired_files:
            cursor.execute("DELETE FROM files WHERE file_id = ?", (file[0],))

        conn.commit()
    except sqlite3.OperationalError as e:
        print("Ошибка при работе с базой данных:", e)
    finally:
        conn.close()

async def on_startup(dp):
    asyncio.create_task(delete_expired_files_periodic())

async def delete_expired_files_periodic():
    while True:
        await delete_expired_files()
        await asyncio.sleep(3)  
if __name__ == "__main__":
    verif_db()
    executor.start_polling(dp, on_startup=on_startup, skip_updates=True)
