import telebot
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup
import vobject
import os
import json
import datetime

API_TOKEN = "7433767669:AAEhnO7t5UDgiGPuJyvWa4aQd81FNzb0C2c"
bot = telebot.TeleBot(API_TOKEN)

user_data = {}
active_mode = None
IMAGE_PATHS = {
    'cv': 'tampilan/cv.jpg',
    'split': 'tampilan/split.jpg',
    'string': 'tampilan/string.jpg'
}
LOG_FILE = 'log.json'
PRIVILEGE_FILE = 'access.json'

def load_privileges():
    try:
        if os.path.exists(PRIVILEGE_FILE):
            with open(PRIVILEGE_FILE, 'r') as f:
                return json.load(f)
    except Exception as e:
        print("Error saat membaca file privilege:", e)
    return {"accessed_user": [], "admin": []}

def save_privileges(privileges):
    try:
        with open(PRIVILEGE_FILE, 'w') as f:
            json.dump(privileges, f, indent=4)
    except Exception as e:
        print("Error saat menulis file privilege:", e)

privileges = load_privileges()
accessed_user = privileges.get('accessed_user', [])
admin = privileges.get('admin', [])

def load_admin():
    try:
        if os.path.exists(PRIVILEGE_FILE):
            with open(PRIVILEGE_FILE, 'r') as f:
                return json.load(f)
    except Exception as e:
        print("Error saat membaca file privilege:", e)
    return {"admin": []}

def send_message_to_all(message):
    try:
        for user in privileges['accessed_user']:
            bot.send_message(user['id'], message)
    except Exception as e:
        print("Error saat mengirim pesan:", e)

def has_access(chat_id):
    try:
        if check_access(chat_id):
            return True
        admin_data = load_admin()
        return chat_id in admin_data["admin"]
    except:
        pass

def add_user_with_duration(user_id, duration):
    expiry_date = None
    if duration != 'forever':
        try:
            unit = duration[-3:].lower()
            value = int(duration[:-3])
            if unit == 'day':
                expiry_date = datetime.datetime.now() + datetime.timedelta(days=value)
            elif unit == 'week':
                expiry_date = datetime.datetime.now() + datetime.timedelta(weeks=value)
            elif unit == 'month':
                expiry_date = datetime.datetime.now() + datetime.timedelta(days=value * 30)
        except:
            return "Format durasi tidak valid. Gunakan format seperti 1day, 1week, 1month, forever."

    accessed_user.append({"id": user_id, "expiry_date": expiry_date.isoformat() if expiry_date else "forever"})
    privileges['accessed_user'] = accessed_user
    save_privileges(privileges)
    return f"User dengan ID {user_id} berhasil ditambahkan dengan durasi {duration}."

def check_access(user_id):
    for user in accessed_user:
        if user["id"] == user_id:
            if user["expiry_date"] == "forever":
                return True
            expiry_date = datetime.datetime.fromisoformat(user["expiry_date"])
            if datetime.datetime.now() < expiry_date:
                return True
            else:
                accessed_user.remove(user)
                privileges['accessed_user'] = accessed_user
                save_privileges(privileges)
                log_data = read_log()
                log_data["chats"] = [chat for chat in log_data["chats"] if chat["chatid"] != str(user_id)]
                write_log(log_data)
    return False

def read_log():
    try:
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, 'r') as f:
                return json.load(f)
    except Exception as e:
        print("Error saat membaca file log:", e)
    return {"chats": []}

def write_log(log_data):
    try:
        with open(LOG_FILE, 'w') as f:
            json.dump(log_data, f, indent=4)
    except Exception as e:
        print("Error saat menulis file log:", e)

def update_log(chat_id, file_type, file_name):
    try:
        log_data = read_log()
        chat_entry = next((chat for chat in log_data["chats"] if chat["chatid"] == str(chat_id)), None)
        time = datetime.datetime.now()

        if not chat_entry:
            chat_entry = {
                "chatid": str(chat_id),
                "output_file": {"filename": []},
                "user_file": {"filename": []}
            }
            log_data["chats"].append(chat_entry)

        if file_type == 'output':
            output_with_time = f"{file_name} ({time.year}/{time.month}/{time.day} {time.hour}:{time.minute}:{time.second})"
            chat_entry["output_file"]["filename"].append(output_with_time)
        elif file_type == 'user':
            userfile_with_time = f"{file_name} ({time.year}/{time.month}/{time.day} {time.hour}:{time.minute}:{time.second})"
            chat_entry["user_file"]["filename"].append(userfile_with_time)

        write_log(log_data)
    except Exception as e:
        print("Terjadi kesalahan saat memperbarui log:", e)

def delete_file(file_path):
    try:
        os.remove(file_path)
        print(f"File {file_path} berhasil dihapus.")
    except Exception as e:
        print(f"Gagal menghapus file {file_path}: {e}")

def process_vcard_file(file_path):
    vcard_array = []
    with open(file_path, 'r') as file:
        vcard_buffer = ''
        for line in file:
            if line.strip() == "END:VCARD":
                vcard_buffer += line
                vcard_array.append(vcard_buffer)
                vcard_buffer = ''
            else:
                vcard_buffer += line
    return vcard_array

def save_vcards_vcf(vcards_lists, filename_template, limit):
    try:
        created_files = []
        num_files = (len(vcards_lists) + limit - 1) // limit

        for i in range(num_files):
            start_idx = i * limit
            end_idx = min((i + 1) * limit, len(vcards_lists))
            file_name, file_extension = os.path.splitext(filename_template)
            if file_extension == '.vcf':
                filename = f"{file_name} - {i + 1}{file_extension}"
            else:
                filename = f"{file_name} - {i + 1}.vcf"

            with open(filename, 'w') as f:
                for vcard in vcards_lists[start_idx:end_idx]:
                    f.write(vcard)
            created_files.append(filename)

        return created_files
    except Exception as e:
        print("An error occurred while saving vCards:", e)
        return None

def create(fn, name_file, limit):
    try:
        with open(name_file, "r") as read:
            contacts = read.readlines()
            i = 1
            vcard_lists = []
            vcard_list = []
            file_counter = 1
            current_name = fn
            previous_name = current_name

            for line in contacts:
                line = line.strip()
                if not line:
                    if current_name != fn:
                        current_name = fn
                        i = 1
                    continue
                if line.isalpha():
                    if current_name != line:
                        current_name = line
                        i = 1
                    continue
                if current_name != previous_name:
                    i = 1
                previous_name = current_name

                name_with_number = f"{current_name}-{i}" if current_name != fn else f"{current_name}{i}"

                if not line.startswith('+'):
                    line = '+' + line

                vcard = vobject.vCard()
                vcard.add('VERSION').value = '3.0'
                vcard.add('FN').value = name_with_number
                vcard.add('TEL;TYPE=CELL').value = line
                vcard_list.append(vcard)
                i += 1
                if len(vcard_list) == limit:
                    vcard_lists.append(vcard_list)
                    vcard_list = []
                    file_counter += 1
            if vcard_list:
                vcard_lists.append(vcard_list)
            return vcard_lists
    except Exception as e:
        print("Terjadi kesalahan saat membuat vCard:", e)
        return None

def create_vcard_from_text(text):
    try:
        contacts = text.strip().split("\n")
        i = 1
        vcard_lists = []
        vcard_list = []
        current_name = None
        previous_name = None  # Inisialisasi previous_name di sini
        fn = None
        limit = None
        file_counter = 1

        for line in contacts:
            line = line.strip()
            if not line:
                if current_name != fn:
                    current_name = fn
                    i = 1
                continue
            if line.isalpha():
                if current_name != line:
                    current_name = line
                    i = 1
                continue
            if current_name != previous_name:
                i = 1
            previous_name = current_name

            name_with_number = f"{current_name}-{i}" if current_name != fn else f"{current_name}{i}"

            if not line.startswith('+'):
                line = '+' + line

            vcard = vobject.vCard()
            vcard.add('VERSION').value = '3.0'
            vcard.add('FN').value = name_with_number
            vcard.add('TEL;TYPE=CELL').value = line
            vcard_list.append(vcard)
            i += 1
            if len(vcard_list) == limit:
                vcard_lists.append(vcard_list)
                vcard_list = []
                file_counter += 1
        if vcard_list:
            vcard_lists.append(vcard_list)
        return vcard_lists
    except Exception as e:
        print("Terjadi kesalahan saat membuat vCard:", e)
        return None


def save_vcards_txt(vcards_lists, filename_template, start):
    try:
        created_files = []
        single_file = len(vcards_lists) == 1
        for idx, vcard_list in enumerate(vcards_lists, start=1):
            file_name, file_extension = os.path.splitext(filename_template)
            if single_file:
                filename = f"{file_name}{file_extension}"
            else:
                filename = f"{file_name}{start + idx - 1}{file_extension}"
            
            if not filename.endswith('.vcf'):
                filename += '.vcf'
            
            with open(filename, 'w') as f:
                for vcard in vcard_list:
                    f.write(vcard.serialize() + '\n')
            created_files.append(filename)
        return created_files
    except Exception as e:
        print("Terjadi kesalahan saat menyimpan vCard:", e)
        return None

def save_vcards(vcards_lists, filename_template, start=1):
    try:
        created_files = []
        single_file = len(vcards_lists) == 1
        for idx, vcard_list in enumerate(vcards_lists, start=1):
            file_name, file_extension = os.path.splitext(filename_template)
            if single_file:
                filename = f"{file_name}{file_extension}"
            else:
                filename = f"{file_name}{start + idx - 1}{file_extension}"
            
            if not filename.endswith('.vcf'):
                filename += '.vcf'
                
            with open(filename, 'w') as f:
                for vcard in vcard_list:
                    f.write(vcard.serialize() + '\n')
            created_files.append(filename)
        return created_files
    except Exception as e:
        print("Terjadi kesalahan saat menyimpan vCard:", e)
        return None

def format_config(user_id):
    try:
        config = user_data.get(user_id, {})
        nama_kontak = config.get('nama_kontak', '')
        limit_kontak = config.get('limit_kontak', '')
        nama_output_kontak = config.get('nama_output_kontak', '')
        return (
            "=====================\n"
            "      🌟 FORMAT CV 🌟\n"
            "=====================\n"
            "Silakan pilih parameter untuk diisi atau tampilkan konfigurasi saat ini:\n"
            "---------------------\n"
            f"👤 Nama Kontak       : {nama_kontak}\n"
            f"🔢 Limit Kontak      : {limit_kontak}\n"
            f"📄 Nama Output File  : {nama_output_kontak}\n"
            "=====================\n"
        )
    except Exception as e:
        print("Terjadi kesalahan saat memformat konfigurasi:", e)
        return ""

def create_markup():
    try:
        markup = InlineKeyboardMarkup()
        markup.row_width = 2
        markup.add(
            InlineKeyboardButton("👤 Nama Kontak", callback_data='nama_kontak'),
            InlineKeyboardButton("🔢 Limit Kontak", callback_data='limit_kontak'),
            InlineKeyboardButton("📄 Nama Output File", callback_data='nama_output_kontak')
        )
        return markup
    except Exception as e:
        print("Terjadi kesalahan saat membuat markup:", e)
        return None

@bot.message_handler(commands=['chat'])
def chat_all_users(message):
    try:
        if message.chat.id not in privileges['admin']:
            bot.send_message(message.chat.id, "Maaf, Anda tidak memiliki izin untuk menggunakan perintah ini.")
            return
        parts = message.text.split(' ', 1)
        if len(parts) == 1:
            bot.send_message(message.chat.id, "Format perintah salah. Gunakan format: /chat [pesan yang ingin dikirim ke semua pengguna]")
            return
        send_message_to_all(parts[1])
    except Exception as e:
        bot.send_message(message.chat.id, f"Terjadi kesalahan: {e}")

@bot.message_handler(commands=['tampilan'])
def handle_tampilan(message):
    args = message.text.split()
    if len(args) > 1:
        option = args[1].lower()
        if option in IMAGE_PATHS:
            with open(IMAGE_PATHS[option], 'rb') as photo:
                bot.send_photo(message.chat.id, photo)
        else:
            bot.send_message(message.chat.id, "Opsi tidak valid. Gunakan salah satu dari berikut ini:\n/tampilan cv\n/tampilan split\n/tampilan string")
    else:
        bot.send_message(message.chat.id, "Silakan pilih salah satu opsi:\n/tampilan cv\n/tampilan split\n/tampilan string")

@bot.message_handler(commands=['help'])
def show_help(message):
    try:
        help_message = """Daftar Perintah:
/help   - Untuk menampilkan daftar perintah yang tersedia
/cv     - Untuk mengonversi format txt menjadi vcf
/split  - Untuk memecah file vcf menjadi beberapa bagian
/string - Untuk mengubah format chat pengguna menjadi VCF
"""
        bot.send_message(message.chat.id, help_message)
    except Exception as e:
        bot.send_message(message.chat.id, f"Terjadi kesalahan: {e}")


@bot.message_handler(commands=['dfile'])
def delete_files(message):
    try:
        if message.chat.id in admin:
            folder_path = os.getcwd()

            for filename in os.listdir(folder_path):
                if filename.endswith(".vcf") or filename.endswith(".txt"):
                    file_path = os.path.join(folder_path, filename)
                    os.remove(file_path)

            bot.send_message(message.chat.id, "Semua file .vcf dan .txt telah dihapus dari folder.")
    except Exception as e:
        bot.send_message(message.chat.id, f"Terjadi kesalahan saat menghapus file: {str(e)}")

@bot.message_handler(commands=['file'])
def list_files(message):
    try:
        if message.chat.id in admin:
            folder_path = os.getcwd()

            file_list = os.listdir(folder_path)
            if file_list:
                file_list_message = "\n".join(file_list)
                response_message = f"Daftar file dalam folder:\n\n{file_list_message}"
            else:
                response_message = "Tidak ada file dalam folder."

        bot.send_message(message.chat.id, response_message)
    except Exception as e:
        bot.send_message(message.chat.id, f"Terjadi kesalahan saat mengakses daftar file: {str(e)}")

@bot.message_handler(commands=['add'])
def add(message):
    try:
        if message.chat.id in admin:
            parts = message.text.split()
            if len(parts) != 3:
                bot.send_message(message.chat.id, "Format perintah salah. Gunakan format: /add <user_id> <duration>")
                return
            user_id = int(parts[1])
            duration = parts[2]
            response = add_user_with_duration(user_id, duration)
            bot.send_message(message.chat.id, response)
    except Exception as e:
        bot.send_message(message.chat.id, f"Telah terjadi error : {e}")

@bot.message_handler(commands=['delete'])
def delete(message):
    try:
        if message.chat.id in admin:
            index = int(message.text[8:]) - 1
            if 0 <= index < len(accessed_user):
                deleted_user = accessed_user.pop(index)
                privileges['accessed_user'] = accessed_user
                save_privileges(privileges)
                bot.send_message(message.chat.id, f"User dengan ID {deleted_user['id']} berhasil dihapus dari daftar akses.")
            else:
                bot.send_message(message.chat.id, "Indeks tidak valid.")
    except Exception as e:
        bot.send_message(message.chat.id, f"Telah terjadi error : {e}")

@bot.message_handler(commands=['show'])
def show(message):
    try:
        if message.chat.id in admin:
            accessed_users_list = "\n".join([f"{idx+1}. ID: {user['id']}, Expiry: {user['expiry_date']}" for idx, user in enumerate(accessed_user)])
            admin_list = "\n".join([f"{idx+1}. ID: {admin_id}" for idx, admin_id in enumerate(admin)])
            bot.send_message(message.chat.id, f"Accessed Users:\n{accessed_users_list}\n\nAdmins:\n{admin_list}")
    except Exception as e:
        bot.send_message(message.chat.id, f"Telah terjadi error : {e}")

@bot.message_handler(commands=['start'])
def welcome(message):
    try:
        if check_access(message.chat.id):
            bot.reply_to(message, '''Selamat datang di BOT CV Zyeta!\nKami senang Anda di sini untuk menggunakan layanan zyeta!''')
        else:
            bot.reply_to(message, "Hmmm. Maaf sepertinya anda belum memiliki akses untuk bot ini\nJika ingin membeli hubungi @zyetaaa")
    except Exception as e:
        print(f"Error saat memebalas pesan start: {str(e)}")

@bot.message_handler(commands=['split'])
def handle_split_command(message):
    markup = InlineKeyboardMarkup()
    markup.row_width = 1  
    user_data[message.chat.id] = user_data.get(message.chat.id, {})
    user_data[message.chat.id]['mode'] = 'split'

    if check_access(message.chat.id) or has_access(message.chat.id):
        if user_data[message.chat.id].get('split_count'):
            split_count = user_data[message.chat.id]['split_count']
            markup.add(InlineKeyboardButton(f"{split_count} ctc / file", callback_data=f"split_count_{split_count}"),
                    InlineKeyboardButton("Edit", callback_data="edit_split"))
        else:
            markup.add(InlineKeyboardButton("MASUKKAN JUMLAH PECAHAN", callback_data="input_split"))

        bot.send_message(message.chat.id, "Silakan pilih untuk melanjutkan:", reply_markup=markup)
    else:
        bot.send_message(message.chat.id, "Hmmm. Maaf sepertinya anda belum memiliki akses untuk bot ini\nJika ingin membeli hubungi @zyetaaa")

@bot.callback_query_handler(func=lambda call: call.data == 'input_split')
def ask_split_count(call):
    bot.send_message(call.message.chat.id, "Kamu ingin memecah berapa kontak? Masukkan jumlah kontak yang ingin kamu pecah:")
    bot.register_next_step_handler(call.message, process_split_count)

def process_split_count(message):
    try:
        split_count = int(message.text)
        if split_count <= 0:
            bot.send_message(message.chat.id, "Masukkan jumlah kontak yang valid (angka positif).")
            return
        
        user_data[message.chat.id] = user_data.get(message.chat.id, {})
        user_data[message.chat.id]['split_count'] = split_count

        markup = InlineKeyboardMarkup()
        markup.row_width = 1
        markup.add(InlineKeyboardButton(f"{split_count} ctc / file", callback_data=f"split_count_{split_count}"),
                   InlineKeyboardButton("Edit", callback_data="edit_split"))

        bot.send_message(message.chat.id, "Jumlah pecahan telah diatur. Silakan kirim file vCard (.vcf) yang ingin dipecah:", reply_markup=markup)

    except ValueError:
        bot.send_message(message.chat.id, "Masukkan jumlah kontak dalam bentuk angka.")

@bot.callback_query_handler(func=lambda call: call.data == 'edit_split')
def edit_split_count(call):
    bot.send_message(call.message.chat.id, "Silakan masukkan jumlah kontak baru untuk dipecah:")
    bot.register_next_step_handler(call.message, process_edit_split_count)

def process_edit_split_count(message):
    try:
        split_count = int(message.text)
        if split_count <= 0:
            bot.send_message(message.chat.id, "Masukkan jumlah kontak yang valid (angka positif).")
            return
        
        user_data[message.chat.id] = user_data.get(message.chat.id, {})
        user_data[message.chat.id]['split_count'] = split_count

        markup = InlineKeyboardMarkup()
        markup.row_width = 1
        markup.add(InlineKeyboardButton(f"{split_count} ctc / file", callback_data=f"split_count_{split_count}"),
                   InlineKeyboardButton("Edit", callback_data="edit_split"))

        bot.send_message(message.chat.id, "Jumlah pecahan telah diperbarui.", reply_markup=markup)

    except ValueError:
        bot.send_message(message.chat.id, "Masukkan jumlah kontak dalam bentuk angka.")

@bot.callback_query_handler(func=lambda call: call.data.startswith('split_count_'))
def handle_split_callback(call):
    split_count = int(call.data.split('_')[1])
    bot.send_message(call.message.chat.id, f"Anda memilih untuk memecah menjadi {split_count} kontak per file. Silakan kirim file vCard (.vcf) yang ingin dipecah.")

@bot.message_handler(content_types=['document'])
def handle_document(message):
    try:
        user_mode = user_data.get(message.chat.id, {}).get('mode')

        if user_mode == 'split':
            if message.document.mime_type in ['text/x-vcard', 'text/vcard'] and message.document.file_name.endswith('.vcf'):
                split_count = user_data.get(message.chat.id, {}).get('split_count')
                if not split_count:
                    bot.send_message(message.chat.id, "Silakan gunakan perintah /split dan tentukan jumlah pecahan sebelum mengirim file.")
                    return
                
                file_info = bot.get_file(message.document.file_id)
                downloaded_file = bot.download_file(file_info.file_path)

                temp_file_path = f"temp_{message.document.file_name}"
                with open(temp_file_path, 'wb') as new_file:
                    new_file.write(downloaded_file)

                vcard_array = process_vcard_file(temp_file_path)
                if vcard_array:
                    original_file_name = os.path.splitext(message.document.file_name)[0]
                    created_files = save_vcards_vcf(vcard_array, original_file_name, split_count)

                    for file in created_files:
                        with open(file, 'rb') as f:
                            bot.send_document(message.chat.id, f)
                        os.remove(file)

                    os.remove(temp_file_path)

                else:
                    bot.send_message(message.chat.id, "Gagal memproses file vCard.")
                
            else:
                bot.send_message(message.chat.id, "Mohon kirimkan file vCard dengan format .vcf.")

        elif user_mode == 'cv':
            if message.document.mime_type == 'text/plain':
                file_info = bot.get_file(message.document.file_id)
                downloaded_file = bot.download_file(file_info.file_path)

                with open(f"{message.document.file_name}", 'wb') as new_file:
                    new_file.write(downloaded_file)

                update_log(message.chat.id, 'user', message.document.file_name)

                if message.chat.id in user_data:
                    config = user_data[message.chat.id]
                    fn = config.get('nama_kontak', 'default')
                    limit = int(config.get('limit_kontak', 10))
                    name_file = message.document.file_name
                    vcard_lists = create(fn, name_file, limit)
                    if vcard_lists:
                        file_name, _ = os.path.splitext(message.document.file_name)
                        output_name = config.get('nama_output_kontak', f'{file_name} - .vcf')
                        created_files = save_vcards(vcard_lists, output_name, 1)
                        for files in created_files:
                            with open(files, 'rb') as f:
                                bot.send_document(message.chat.id, f)
                                update_log(message.chat.id, 'output', files)
                                os.remove(files)
                        os.remove(name_file)

                    else:
                        bot.send_message(message.chat.id, 'Terjadi kesalahan saat membuat vCard.')
                else:
                    bot.send_message(message.chat.id, 'Silakan gunakan /cv untuk memulai konfigurasi terlebih dahulu.')
            else:
                bot.send_message(message.chat.id, "File yang dikirimkan tidak sesuai format yang diharapkan.")
        else:
            bot.send_message(message.chat.id, 'Silakan gunakan /cv atau /split untuk memulai konfigurasi terlebih dahulu.')
    except Exception as e:
        bot.send_message(message.chat.id, f"Terjadi kesalahan: {str(e)}")

@bot.message_handler(commands=['cv'])
def setting(message):
    if check_access(message.chat.id) or has_access(message.chat.id):
        try:
            user_id = message.from_user.id
            user_data[user_id] = user_data.get(user_id, {})
            user_data[user_id]['mode'] = 'cv'

            initial_message = format_config(user_id)
            markup = create_markup()
            sent_message = bot.send_message(message.chat.id, initial_message, reply_markup=markup)
            user_data[user_id]['message_id'] = sent_message.message_id
        except Exception as e:
            print(f"Error saat membuat config : {str(e)}")
    else:
        bot.send_message(message.chat.id,  "Maaf, Anda tidak memiliki akses untuk fitur ini. Jika Anda ingin membeli, silakan hubungi @zyetaaa.")

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    try:
        user_id = call.from_user.id
        user_mode = user_data.get(user_id, {}).get('mode')

        if user_mode == 'cv' and call.data in ['nama_kontak', 'limit_kontak', 'nama_output_kontak']:
            param = call.data
            bot.send_message(call.message.chat.id, f'Masukkan {param.replace("_", " ").capitalize()}:')
            user_data[user_id]['param'] = param
    except Exception as e:
        print(f"Error saat menerima callback : {str(e)}")
        
@bot.message_handler(commands=['string'])
def handle_file_command(message):
    if check_access(message.chat.id):
        global nama_file
        nama_file = None
        chat_id = message.chat.id
        user_data[chat_id] = user_data.get(chat_id, {})
        user_data[chat_id]['mode'] = 'string'
        bot.send_message(chat_id, "Silakan kirimkan nama file untuk menyimpan vCard:")
        print(f"Mode diatur ke 'string' untuk chat_id: {chat_id}")  # Debug statement
    else:
        bot.send_message(message.chat.id, "Maaf, Anda tidak memiliki akses untuk fitur ini.")

@bot.message_handler(content_types=['text'])
def receive_input(message):
    try:
        user_id = message.from_user.id
        user_mode = user_data.get(user_id, {}).get('mode')
        print(f"Mode saat ini untuk user_id {user_id}: {user_mode}")  # Debug statement

        if user_mode == 'cv':
            param = user_data[user_id].get('param')
            if param:
                user_data[user_id][param] = message.text

                current_config = format_config(user_id)
                markup = create_markup()
                bot.edit_message_text(current_config, message.chat.id, user_data[user_id]['message_id'], reply_markup=markup)

                user_data[user_id]['param'] = None
            else:
                bot.send_message(message.chat.id, 'Silakan gunakan /cv untuk memulai konfigurasi.')
        elif user_mode == 'string':
            global nama_file

            if not nama_file:
                nama_file = message.text.strip()
                bot.send_message(message.chat.id, f"Nama file telah diatur ke: {nama_file}. Silakan kirimkan data untuk dikonversi menjadi vCard:")
            else:
                bot.send_chat_action(message.chat.id, 'typing')
                vcard_lists = create_vcard_from_text(message.text)  
                if vcard_lists:
                    saved_files = save_vcards_txt(vcard_lists, nama_file, 1) 
                    if saved_files:
                        for file_path in saved_files:
                            with open(file_path, 'rb') as f:
                                bot.send_document(message.chat.id, f)
                                delete_file(file_path)  
                        nama_file = None  
                else:
                    bot.send_message(message.chat.id, 'Terjadi kesalahan saat membuat vCard.')
        else:
            bot.send_message(message.chat.id, 'Silakan gunakan /cv atau /split untuk memulai konfigurasi terlebih dahulu.')
    except Exception as e:
        print(f"Error saat menerima pesan: {str(e)}")


bot.polling()
