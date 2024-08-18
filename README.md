# Panduan Setup Bot Telegram

1. Instalasi Kebutuhan

Pertama, instal semua ketergantungan yang dibutuhkan menggunakan `pip`:
pip install -r requirements.txt

2. Ganti Token API
Buka file bot.py dan ganti placeholder TOKEN_BOT dengan token API bot Telegram Anda yang sebenarnya dari BotFather:

python
TOKEN_BOT = "your_api_token_here"

3. Atur Akses Admin
Konfigurasikan akses admin di file access.json dengan menambahkan chat_id dan username admin. Struktur file access.json adalah sebagai berikut:

json
{
    "OWNER_ID": your_owner_id,
    "OWNER_USERNAME": "your_username",
    "ALLOWED_USER": {
        "-1001234567890": {
            "own": [],
            "user": []
        }
    }
}

4. Tambah Akses Pengguna
Untuk menambah akses pengguna ke bot, gunakan perintah berikut di chat dengan bot:

Untuk menambah pengguna selama 1 hari:
/add chatid 1day

Untuk menambah pengguna secara permanen:
/add chatid forever
Ganti chatid dengan ID chat pengguna yang sebenarnya.

5. Jalankan Bot
Setelah semuanya dikonfigurasi, Anda dapat memulai bot dengan perintah berikut:

python3 bot.py
