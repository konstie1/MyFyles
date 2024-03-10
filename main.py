import hashlib
from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher, FSMContext
from aiogram.utils import executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher.filters import BoundFilter
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from string import ascii_letters, digits
import configparser
import randoms
import os
import sqlite3
import asyncio
import cv2
from datetime import datetime, timedelta
import numpy as np
import requests
from PIL import Image, ImageDraw, ImageFont
import os
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
import base64
import random

config = configparser.ConfigParser()
config.read('config.ini')

ADMIN_ID = config['Bot']['admin_id']
TOKEN = config['Bot']['token']

def hash_password(password):
    sha256 = hashlib.sha256()

    sha256.update(password.encode())

    hashed_password = sha256.hexdigest()

    return hashed_password
def generate_key(password):
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        salt=b'salt_value',
        iterations=100000,
        length=16,
        backend=default_backend()
    )
    key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
    return key

def encrypt_file_info(file_info, password):
    key = generate_key(password)

    iv = os.urandom(16)
    cipher = Cipher(algorithms.AES(key), modes.CFB8(iv), backend=default_backend())
    encryptor = cipher.encryptor()

    encrypted_data = encryptor.update(','.join(file_info.values()).encode()) + encryptor.finalize()

    return base64.urlsafe_b64encode(iv + encrypted_data).decode()

def decrypt_file_info(encrypted_data, password):
    key = generate_key(password)

    if isinstance(encrypted_data, tuple):
        encrypted_data = encrypted_data[0]

    iv_and_data = base64.urlsafe_b64decode(encrypted_data[:32])
    iv = iv_and_data[:16]
    encrypted_data = iv_and_data[16:]

    if len(iv) != 16:
        raise ValueError(f'Invalid IV size ({len(iv)}) for CFB8.')

    cipher = Cipher(algorithms.AES(key), modes.CFB8(iv), backend=default_backend())
    decryptor = cipher.decryptor()

    decrypted_data = decryptor.update(encrypted_data) + decryptor.finalize()

    return decrypted_data.decode().split(',')


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


current_date = datetime.now()


def user_exist(user_id):
    db = sqlite3.connect("data.db", check_same_thread=False)
    cursor = db.cursor()
    cursor.execute("SELECT user_id FROM users WHERE user_id=?", (user_id,))

    if cursor.fetchone() is None:
        return False
    else:
        return True


def add_user_to_db(user_id):
    db = sqlite3.connect("data.db", check_same_thread=False)
    cursor = db.cursor()
    user = [user_id]
    cursor.execute(f"""INSERT INTO users(user_id) VALUES(?)""", user)
    db.commit()


def add_new_file(user_id, type, code, file_id, file_name, file_date):
    db = sqlite3.connect("data.db", check_same_thread=False)
    cursor = db.cursor()
    data = [user_id, type, code, file_id, file_name, file_date, None]
    cursor.execute(
        "INSERT INTO files(user_id, type, code, file_id, file_name, file_date, fire_date) VALUES(?,?,?,?,?,?,?)", data)
    db.commit()


def add_new_pass_file(user_id, type, code, file_id, password, file_name, file_date):
    db = sqlite3.connect("data.db", check_same_thread=False)
    cursor = db.cursor()
    data = [user_id, type, code, file_id, password, file_name, file_date, None] 
    cursor.execute(
        "INSERT INTO files(user_id, type, code, file_id, password, file_name, file_date, fire_date) VALUES(?,?,?,?,?,?,?,?)",
        data)
    db.commit()


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
    blur_intensity = 60
    image = cv2.imread(image_path)
    if image is None:
        return None

    small_image = cv2.resize(image, (0, 0), fx=0.009, fy=0.009)

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


class IsPrivate(BoundFilter):
    async def check(self, message: types.Message):
        return message.chat.type == types.ChatType.PRIVATE


class action(StatesGroup):
    alert = State()
    main_fire_date_button = State()
    upload_file = State()
    upload_file_password = State()
    main_delete_button = State()
    check_password = State()
    fire_date = State()


bot = Bot(token=TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())


def main_menu_buttons():
    button1 = KeyboardButton('📩 Завантажити файл')
    button2 = KeyboardButton('🗃️ Особисті файли')
    main_menu_buttons = ReplyKeyboardMarkup(resize_keyboard=True)
    main_menu_buttons.add(button1)
    main_menu_buttons.add(button2)
    return main_menu_buttons


def back_button():
    button1 = KeyboardButton('Отмена')
    back_button1 = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    back_button1.add(button1)
    return back_button1


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
        return round(size_in_bytes / (1024 ** 3), 3)

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


@dp.message_handler(IsPrivate(), commands=["start"], state="*")
async def start_command(message: types.Message, state: FSMContext):
    args = message.get_args()
    bot_data = await bot.get_me()
    bot_name = bot_data["username"]

    if user_exist(message.chat.id) == False:
        add_user_to_db(message.chat.id)

    if not args:
        await bot.send_message(
            chat_id=message.chat.id,
            text=f"Вітаю тебе на нашому файлообміннику! 🌐Мене звуть {bot_name}, і я тут, щоб полегшити твій досвід обміну файлами. Безпечно, зручно та ефективно - це те, що я пропоную.",
            reply_markup=main_menu_buttons(),
        )

    else:
        type_file, fileID, views, password, file_name, file_date = get_file(args)
        if type_file is None and fileID is None:
            await bot.send_message(
                chat_id=message.chat.id,
                text="Файл втрачено...",
                reply_markup=main_menu_buttons(),
            )

        else:
            if password == (None,):
                view_updater(args)

                if type_file[0] == "photo":
                    await bot.send_photo(
                        chat_id=message.chat.id,
                        photo=fileID[0],
                        caption=f"👁 Перегляди: {int(views[0]) + 1}",
                        reply_markup=main_menu_buttons(),
                    )

                elif type_file[0] == "video":

                    await bot.send_video(
                        chat_id=message.chat.id,
                        video=fileID[0],
                        caption=f"👁 Перегляди: {int(views[0]) + 1}",
                        reply_markup=main_menu_buttons(),
                    )

                elif type_file[0] == "voice":
                    await bot.send_voice(
                        chat_id=message.chat.id,
                        voice=fileID[0],
                        caption=f"👁 Перегляди: {int(views[0]) + 1}",
                        reply_markup=main_menu_buttons(),
                    )

                elif type_file[0] == "document":
                    await bot.send_document(
                        chat_id=message.chat.id,
                        document=fileID[0],
                        caption=f"👁 Перегляди: {int(views[0]) + 1}",
                        reply_markup=main_menu_buttons(),
                    )

            else:
                file_info = await bot.get_file(fileID[0])
                file_path = file_info.file_path

                if (type_file[0] == "photo"):
                    file_save_path = f"assets/temp/{fileID[0]}.png"
                    os.makedirs(os.path.dirname(file_save_path), exist_ok=True)

                    await bot.send_message(message.chat.id, text="Предперегляд:")

                    await bot.download_file(file_path, file_save_path)

                    await blur_image(file_save_path)

                    with open(file_save_path, "rb") as photo:
                        await bot.send_photo(message.chat.id, photo=photo)

                    os.remove(file_save_path)

                elif type_file[0] == "document":
                    await bot.send_message(message.chat.id, text="Предперегляд:")
                    # os.makedirs(f"assets/temp/{fileID[0]}")
                    # await bot.download_file(
                    #     file_path, f"assets/temp/{fileID[0]}/{file_name[0]}"
                    # )
                    # print(file_name, fileID)
                    #
                    # if file_name and fileID:
                    #     base_name, *_, extension = file_name[0].rpartition(".")
                    #     if base_name and extension:
                    #         file_path = f"assets/temp/{fileID[0]}/{file_name[0]}"
                    #         file_size = get_file_size(file_path)
                    #         virus_check = virus_total_check(file_path)
                    #
                    #         message_text = (
                    #             f"Название файла: {base_name}\n"
                    #             f"Тип файла: {extension}\n"
                    #             f"Вес файла: {file_size}GB\n"
                    #             f"VirusTotal: {virus_check}"
                    #         )
                    #         await bot.send_message(message.chat.id, text=message_text)
                    #     else:
                    #         await bot.send_message(
                    #             message.chat.id,
                    #             text="Ошибка: неверный формат имени файла.",
                    #         )
                    # else:
                    #     await bot.send_message(
                    #         message.chat.id, text="Ошибка: отсутствуют данные о файле."
                    #     )
                    #
                    # os.remove(f"assets/temp/{fileID[0]}/{file_name[0]}")
                    # os.removedirs(f"assets/temp/{fileID[0]}")

                await bot.send_message(
                    message.chat.id,
                    text="Файл захищений паролем🔒, для доступу до файлу введіть пароль:",
                    reply_markup=back_button(),
                )
                await state.update_data(
                    check_password=args
                )
                await action.check_password.set()


@dp.message_handler(state=action.check_password, content_types=types.ContentTypes.ANY)
async def upload_file(message: types.Message, state: FSMContext):
    if message.text:

        if message.text.lower() == 'отмена':
            await bot.send_message(chat_id=message.chat.id, text='Ви повернулися в головне меню.🏠',
                                   reply_markup=main_menu_buttons())
            await state.finish()

        else:
            user_data = await state.get_data()
            code = user_data['check_password']
            type_file, fileID, views, password, file_name, file_date = get_file(code)
            password_hash = hash_password(message.text)
            if password_hash == password[0]:
                view_updater(code)

                if type_file[0] == 'photo':
                    await bot.send_photo(chat_id=message.chat.id, photo=fileID[0],
                                         caption=f'👁 Перегляди: {int(views[0]) + 1}', reply_markup=main_menu_buttons())

                elif type_file[0] == 'video':
                    await bot.send_video(chat_id=message.chat.id, video=fileID[0],
                                         caption=f'👁 Перегляди: {int(views[0]) + 1}', reply_markup=main_menu_buttons())

                elif type_file[0] == 'voice':
                    await bot.send_voice(chat_id=message.chat.id, voice=fileID[0],
                                         caption=f'👁 Перегляди: {int(views[0]) + 1}', reply_markup=main_menu_buttons())

                elif type_file[0] == 'document':
                    file_info = await bot.get_file(fileID[0])
                    file_path = file_info.file_path
                    file_name = decrypt_file_info(file_name, password_hash)
                    await bot.send_message(message.chat.id, text="Предперегляд:")
                    os.makedirs(f"assets/temp/{fileID[0]}")
                    await bot.download_file(
                        file_path, f"assets/temp/{fileID[0]}/{file_name[0]}"
                    )

                    
                    base_name, *_, extension = file_name[0].rpartition(".")
                    if base_name and extension:
                        file_path = f"assets/temp/{fileID[0]}/{file_name[0]}"
                        file_size = get_file_size(file_path)
                        virus_check = virus_total_check(file_path)

                        message_text = (
                            f"Название файла: {base_name}\n"
                            f"Тип файла: {extension}\n"
                            f"Вес файла: {file_size}GB\n"
                            f"VirusTotal: {virus_check}"
                        )
                        await bot.send_message(message.chat.id, text=message_text)
                    await bot.send_document(chat_id=message.chat.id, document=fileID[0],
                                            caption=f'👁 Перегляди: {int(views[0]) + 1}',
                                            reply_markup=main_menu_buttons())
                await state.finish()

            else:
                await bot.send_message(chat_id=message.chat.id, text='😔Упс, це не вірний пароль, спробуй ще раз:',
                                       reply_markup=back_button())

    else:
        await bot.send_message(chat_id=message.chat.id, text='😔Упс, це не вірний пароль, спробуй ще раз:',
                               reply_markup=back_button())


@dp.message_handler(text="📩 Завантажити файл")
async def create_post(message: types.Message):
    if user_exist(message.chat.id) == True:
        await bot.send_message(chat_id=message.chat.id, text='Надішли мені файл.', reply_markup=back_button())
        await action.upload_file.set()


@dp.message_handler(text="🗃️ Особисті файли")
async def create_post(message: types.Message):
    if user_exist(message.chat.id) == True:
        bot_data = await bot.get_me()
        bot_name = bot_data['username']
        all_types, all_ids, all_views, passwords, file_name, file_date, fire_date = get_files(message.from_user.id)

        if not all_types:
            await bot.send_message(chat_id=message.chat.id,
                                   text='У вас немає завантажених файлів, щоб завантажити файли натисніть "📩 Завантажити файл"',
                                   reply_markup=main_menu_buttons())

        else:
            file_message = ""
            for i, id_file in enumerate(all_ids):
                if(passwords[i][0] == None):
                    passwd = False
                else: 
                    passwd = True

                file_message += (
                    f"{i + 1} | https://t.me/{bot_name}?start={id_file[0]} | \n"
                    f"📁 {file_name[i][0]} | 👁 {all_views[i][0]} |⏲{fire_date[i][0]} |🔒{passwd}\n"
                )

            await bot.send_message(chat_id=message.chat.id, text=file_message, reply_markup=main_delete_button())


@dp.message_handler(state=action.upload_file_password, content_types=types.ContentTypes.TEXT)
async def upload_file(message: types.Message, state: FSMContext):
    bot_data = await bot.get_me()
    bot_name = bot_data['username']
    user_data = await state.get_data()
    file_data = user_data['upload_file_password']

    if message.text == '-':

        if file_data.split('|')[1] == 'photo':
            code = file_data.split('|')[2]
            add_new_file(file_data.split('|')[0], 'photo', file_data.split('|')[2], file_data.split('|')[3],
                         file_data.split('|')[4], file_data.split('|')[5])

            await bot.send_message(chat_id=message.chat.id,
                                   text=f'📁Файл було успішно завантажено.\n\n🔗Щоб поділитися ним відправ це посилання: https://t.me/{bot_name}?start={code}',
                                   reply_markup=main_menu_buttons())
            await state.finish()

        elif file_data.split('|')[1] == 'video':
            code = file_data.split('|')[2]
            add_new_file(file_data.split('|')[0], 'video', file_data.split('|')[2], file_data.split('|')[3],
                         file_data.split('|')[4], file_data.split('|')[5])
            await bot.send_message(chat_id=message.chat.id,
                                   text=f'📁Файл було успішно завантажено.\n\n🔗Щоб поділитися ним відправ це посилання: https://t.me/{bot_name}?start={code}',
                                   reply_markup=main_menu_buttons())
            await state.finish()

        elif file_data.split('|')[1] == 'voice':
            code = file_data.split('|')[2]
            add_new_file(file_data.split('|')[0], 'voice', file_data.split('|')[2], file_data.split('|')[3],
                         file_data.split('|')[4], file_data.split('|')[5])
            await bot.send_message(chat_id=message.chat.id,
                                   text=f'📁Файл було успішно завантажено.\n\n🔗Щоб поділитися ним відправ це посилання: https://t.me/{bot_name}?start={code}',
                                   reply_markup=main_menu_buttons())
            await state.finish()

        elif file_data.split('|')[1] == 'document':
            code = file_data.split('|')[2]
            add_new_file(file_data.split('|')[0], 'document', file_data.split('|')[2], file_data.split('|')[3],
                         file_data.split('|')[4], file_data.split('|')[5])
            await bot.send_message(chat_id=message.chat.id,
                                   text=f'📁Файл було успішно завантажено.\n\n🔗Щоб поділитися ним відправ це посилання: https://t.me/{bot_name}?start={code}',
                                   reply_markup=main_menu_buttons())
            await state.finish()

    elif message.text.lower() == 'отмена':
        await bot.send_message(chat_id=message.chat.id, text='Ви повернулися в головне меню.🏠',
                               reply_markup=main_menu_buttons())
        await state.finish()

    else:
        password = message.text
        password = hash_password(password)


        if file_data.split('|')[1] == 'photo':
            code = file_data.split('|')[2]
            file_info = {"file_name": file_data.split('|')[4]}
            encrypted_data = encrypt_file_info(file_info, password)
            add_new_pass_file(file_data.split('|')[0], 'photo', file_data.split('|')[2], file_data.split('|')[3],
                                  password, encrypted_data, file_data.split('|')[5])


            await bot.send_message(chat_id=message.chat.id,
                                   text=f'📁Файл було успішно завантажено.\n\n🔒Пароль: {message.text}\n\n🔗Щоб поділитися ним відправ це посилання: https://t.me/{bot_name}?start={code}',
                                   reply_markup=main_menu_buttons())
            await state.finish()

        elif file_data.split('|')[1] == 'video':
            code = file_data.split('|')[2]
            file_info = {"file_name": file_data.split('|')[4]}
            encrypted_data = encrypt_file_info(file_info, password)
            add_new_pass_file(file_data.split('|')[0], 'video', file_data.split('|')[2], file_data.split('|')[3],
                              password, encrypted_data, file_data.split('|')[5])
            await bot.send_message(chat_id=message.chat.id,
                                   text=f'📁Файл було успішно завантажено.\n\n🔒Пароль: {message.text}\n\n🔗Щоб поділитися ним відправ це посилання: https://t.me/{bot_name}?start={code}',
                                   reply_markup=main_menu_buttons())
            await state.finish()

        elif file_data.split('|')[1] == 'voice':
            code = file_data.split('|')[2]
            file_info = {"file_name": file_data.split('|')[4]}
            encrypted_data = encrypt_file_info(file_info, password)
            add_new_pass_file(file_data.split('|')[0], 'voice', file_data.split('|')[2], file_data.split('|')[3],
                              password, encrypted_data, file_data.split('|')[5])
            await bot.send_message(chat_id=message.chat.id,
                                   text=f'📁Файл було успішно завантажено.\n\n🔒Пароль: {message.text}\n\n🔗Щоб поділитися ним відправ це посилання: https://t.me/{bot_name}?start={code}',
                                   reply_markup=main_menu_buttons())
            await state.finish()

        elif file_data.split('|')[1] == 'document':
            code = file_data.split('|')[2]
            file_info = {"file_name": file_data.split('|')[4]}
            encrypted_data = encrypt_file_info(file_info, password)
            add_new_pass_file(file_data.split('|')[0], 'document', file_data.split('|')[2], file_data.split('|')[3],
                              password, encrypted_data, file_data.split('|')[5])
            await bot.send_message(chat_id=message.chat.id,
                                   text=f'📁Файл було успішно завантажено.\n\n🔒Пароль: {message.text}\n\n🔗Щоб поділитися ним відправ це посилання: https://t.me/{bot_name}?start={code}',
                                   reply_markup=main_menu_buttons())
            await state.finish()


@dp.message_handler(state=action.upload_file, content_types=types.ContentTypes.ANY)
async def upload_file(message: types.Message, state: FSMContext):
    file_name = message.document.file_name if message.document else 'media'
    file_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    if message.photo:
        fileID = message.photo[-1].file_id
        code = ''.join(random.sample(ascii_letters + digits, random.randint(33, 40)))
        await state.update_data(
            upload_file_password=f'{message.from_user.id}|photo|{code}|{fileID}|{file_name}|{file_date}')
        await bot.send_message(chat_id=message.chat.id, text='Введи пароль🔒 для файлу. Якщо не хочеш, то напиши "-".',
                               reply_markup=back_button())
        await action.upload_file_password.set()

    elif message.text:

        if message.text.lower() == 'отмена':
            await bot.send_message(chat_id=message.chat.id, text='Ти повернувся назад.🔙',
                                   reply_markup=main_menu_buttons())
            await state.finish()

        else:
            await bot.send_message(chat_id=message.chat.id, text='Надішли мені файл.', reply_markup=back_button())

    elif message.voice:
        fileID = message.voice.file_id
        code = ''.join(random.sample(ascii_letters + digits, random.randint(33, 40)))
        await state.update_data(
            upload_file_password=f'{message.from_user.id}|voice|{code}|{fileID}|{file_name}|{file_date}')
        await bot.send_message(chat_id=message.chat.id, text='Введи пароль🔒 для файлу. Якщо не хочеш, то напиши "-".',
                               reply_markup=back_button())
        await action.upload_file_password.set()

    elif message.video:
        fileID = message.video.file_id
        code = ''.join(random.sample(ascii_letters + digits, random.randint(33, 40)))
        await state.update_data(
            upload_file_password=f'{message.from_user.id}|video|{code}|{fileID}|{file_name}|{file_date}')
        await bot.send_message(chat_id=message.chat.id, text='Введи пароль🔒 для файлу. Якщо не хочеш, то напиши "-".',
                               reply_markup=back_button())
        await action.upload_file_password.set()

    elif message.document:
        fileID = message.document.file_id
        code = ''.join(random.sample(ascii_letters + digits, random.randint(33, 40)))
        await state.update_data(
            upload_file_password=f'{message.from_user.id}|document|{code}|{fileID}|{file_name}|{file_date}')
        await bot.send_message(chat_id=message.chat.id, text='Введи пароль🔒 для файлу. Якщо не хочеш, то напиши "-".',
                               reply_markup=back_button())
        await action.upload_file_password.set()


@dp.message_handler(state=action.main_delete_button, content_types=types.ContentTypes.TEXT)
async def del_file(message: types.Message, state: FSMContext):
    try:
        number = int(message.text)
        user_data = await state.get_data()
        mess_id = user_data['main_delete_button']
        all_types, all_ids, all_views, passwords, file_name, file_date, fire_date = get_files(message.from_user.id)

        if number > len(all_ids):
            await bot.send_message(chat_id=message.chat.id, text='Такого файлу не існує. Введи номер файлу:',
                                   reply_markup=back_delete_button())

        else:
            delete_file(all_ids[(number - 1)][0])
            await bot.delete_message(message.chat.id, mess_id)
            await bot.send_message(chat_id=message.chat.id, text='Ви успішно видалили файл!',
                                   reply_markup=main_menu_buttons())
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
            await bot.send_message(chat_id=message.chat.id, text='Такого файлу не існує. Введи номер файлу:',
                                   reply_markup=back_delete_button())

        else:
            file_id = all_ids[number - 1][0]
            await main_fire_date_button(file_id, time)
            await bot.delete_message(message.chat.id, mess_id)
            await bot.send_message(chat_id=message.chat.id, text='Дата видалення файлу успішно оновлена',
                                   reply_markup=main_menu_buttons())
            await state.finish()

    except ValueError:
        await bot.send_message(chat_id=message.chat.id, text='Введи номер файлу:', reply_markup=back_delete_button())


@dp.callback_query_handler(state='*')
async def handler_call(call: types.CallbackQuery, state: FSMContext):
    bot_data = await bot.get_me()
    bot_name = bot_data['username']
    chat_id = call.from_user.id

    if call.data == 'main_delete_button':
        all_types, all_ids, all_views, passwords, file_name, file_date, fire_date = get_files(chat_id)

        if all_ids == []:
            await bot.delete_message(chat_id, call.message.message_id)
            await bot.send_message(chat_id=chat_id,
                                   text='У вас немає завантажених файлів, щоб завантажити файли натисніть "📩 Завантажити файл"',
                                   reply_markup=main_menu_buttons())

        else:
            text = 'Який файл видаляемо?: \n\n'

            for i, id_file in enumerate(all_ids):
                text += f'{i + 1}. https://t.me/{str(bot_name)}?start={id_file[0]} | {file_name[i][0]}\n\n'

            text += 'Введи номер файлу, який ти хочеш видалити.'
            await bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text=text,
                                        reply_markup=back_delete_button())
            await state.update_data(main_delete_button=call.message.message_id)
            await action.main_delete_button.set()

    if call.data == 'main_fire_date_button':
        all_types, all_ids, all_views, passwords, file_name, file_date, fire_date = get_files(chat_id)

        if all_ids == []:
            await bot.delete_message(chat_id, call.message.message_id)
            await bot.send_message(chat_id=chat_id,
                                   text='У вас немає завантажених файлів, щоб завантажити файли натисніть "📩 Завантажити файл"',
                                   reply_markup=main_menu_buttons())

        else:
            text = 'Який файл?: \n\n'
            for i, id_file in enumerate(all_ids):
                text += f'{i + 1}. https://t.me/{str(bot_name)}?start={id_file[0]} | {file_name[i][0]}\n\n'
            text += 'Введіть номер файлу для створення таймера, Та час\nФормат НомерФайлу/ЧасУГодинах'
            await bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text=text,
                                        reply_markup=back_delete_button())
            await state.update_data(main_fire_date_button=call.message.message_id)
            await action.main_fire_date_button.set()

    if call.data == 'back_delete_button':
        await state.finish()
        all_types, all_ids, all_views, passwords, file_name, file_date, fire_date = get_files(chat_id)

        if all_ids == []:
            await bot.delete_message(chat_id, call.message.message_id)
            await bot.send_message(chat_id=chat_id,
                                   text='У вас немає завантажених файлів, щоб завантажити файли натисніть "📩 Завантажити файл"',
                                   reply_markup=main_menu_buttons())

        else:

            for i, id_file in enumerate(all_ids):
                if(passwords[i][0] == None):
                    passwd = False
                else: passwd = True

                file_message += (
                    f"{i + 1} | https://t.me/{bot_name}?start={id_file[0]} | \n"
                    f"📁 {file_name[i][0]} | 👁 {all_views[i][0]} |⏲{fire_date[i][0]} |🔒{passwd}\n"
                )

            await bot.send_message(chat_id=chat_id, text=file_message, reply_markup=main_delete_button())


def ADMIN_KB():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(types.InlineKeyboardButton(text="Рассылка"))
    kb.add(types.InlineKeyboardButton(text="Статистика"))

    return kb


@dp.message_handler(commands=['admin'])
async def start(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        await message.answer('Що накажете робити, хазяїне?', reply_markup=ADMIN_KB())

    else:
        await message.answer('Ти не мій хазяїн!')


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
        cursor.execute(f'''SELECT user_id FROM users''')
        alert_base = cursor.fetchall()

        for i in range(len(alert_base)):
            await bot.send_message(alert_base[i][0], message.text)
            await state.finish()
        await message.answer('Рассылка завершена', reply_markup=ADMIN_KB())


@dp.message_handler(content_types=['text'], text='Статистика')
async def hfandler(message: types.Message, state: FSMContext):
    db = sqlite3.connect("data.db", check_same_thread=False)
    cursor = db.cursor()
    cursor.execute('''select * from users''')
    results_user = cursor.fetchall()
    cursor.execute('''select * from files''')
    result_files = cursor.fetchall()
    await message.answer(f'Кількість користувачів: {len(results_user)}\nКількість файлів: {len(result_files)}')


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
