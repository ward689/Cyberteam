import asyncio
import json
import os
import re
import socket
import subprocess
import hashlib
import base64
import urllib.parse
from datetime import datetime
from typing import List, Dict, Any
import aiohttp
import whois
import dns.resolver
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

# ===== НАСТРОЙКИ =====
BOT_TOKEN = "ТВОЙ_ТОКЕН_СЮДА"
ADMIN_ID = 123456789  # Твой Telegram ID

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

DATA_FILE = "data.json"

# ===== РАБОТА С ДАННЫМИ =====
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "users": {},
        "monitors": {},
        "history": {}
    }

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_user(data, user_id):
    uid = str(user_id)
    if uid not in data["users"]:
        data["users"][uid] = {
            "history": [],
            "monitors": []
        }
    return data["users"][uid]

# ===== КОМАНДЫ =====

# 1. СТАРТ
@dp.message(Command("start"))
async def cmd_start(message: Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔍 OSINT", callback_data="menu_osint"),
         InlineKeyboardButton(text="🛡️ Безопасность", callback_data="menu_security")],
        [InlineKeyboardButton(text="📊 Анализ", callback_data="menu_analysis"),
         InlineKeyboardButton(text="🔑 Инструменты", callback_data="menu_tools")],
        [InlineKeyboardButton(text="📱 Мониторинг", callback_data="menu_monitor"),
         InlineKeyboardButton(text="📋 Отчет", callback_data="menu_report")]
    ])
    
    await message.answer(
        "🦾 *Кибер-Комбайн V1.0*\n\n"
        "Мой инструментарий для кибербезопасности:\n\n"
        "🔍 */domain* — разведка по домену\n"
        "🔍 */ip* — информация по IP\n"
        "🔍 */email* — проверка в утечках\n\n"
        "🛡️ */check* — проверка ссылки\n"
        "🛡️ */hash* — проверка хэша\n"
        "🛡️ */ssl* — проверка SSL\n\n"
        "📊 */log* — анализ логов\n"
        "📊 */scan* — сканирование портов\n"
        "📊 */decode* — декодирование\n\n"
        "🔑 */passgen* — генератор паролей\n"
        "🔑 */exif* — метаданные фото\n\n"
        "📱 */monitor* — мониторинг хостов\n"
        "📋 */report* — отчет по проверкам\n\n"
        "Используй кнопки для быстрого доступа! 🚀",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

# ===== 1. OSINT =====

@dp.message(Command("domain"))
async def cmd_domain(message: Message):
    args = message.text.split()
    if len(args) < 2:
        await message.answer("❌ Укажи домен: `/domain google.com`")
        return
    
    domain = args[1].strip()
    
    await message.answer(f"🔍 Анализирую домен `{domain}`...")
    
    try:
        # WHOIS
        w = whois.whois(domain)
        whois_info = f"📋 *WHOIS*\nРегистратор: {w.registrar}\nСоздан: {w.creation_date}\nИстекает: {w.expiration_date}"
        
        # DNS
        dns_info = "🌐 *DNS записи*\n"
        for record in ['A', 'AAAA', 'MX', 'TXT', 'NS']:
            try:
                answers = dns.resolver.resolve(domain, record)
                dns_info += f"{record}: {', '.join(str(r) for r in answers[:3])}\n"
            except:
                dns_info += f"{record}: -\n"
        
        # IP
        ip = socket.gethostbyname(domain)
        ip_info = f"📍 *IP*\n{ip}"
        
        await message.answer(
            f"{whois_info}\n\n{dns_info}\n\n{ip_info}",
            parse_mode="Markdown"
        )
        
    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)}")

@dp.message(Command("ip"))
async def cmd_ip(message: Message):
    args = message.text.split()
    if len(args) < 2:
        await message.answer("❌ Укажи IP: `/ip 8.8.8.8`")
        return
    
    ip = args[1].strip()
    
    async with aiohttp.ClientSession() as session:
        try:
            # Геолокация (через бесплатный API)
            async with session.get(f"http://ip-api.com/json/{ip}") as resp:
                data = await resp.json()
                
            if data['status'] == 'success':
                text = f"📍 *Информация об IP* `{ip}`\n\n"
                text += f"🌍 Страна: {data['country']}\n"
                text += f"🏙️ Город: {data['city']}\n"
                text += f"📮 Регион: {data['regionName']}\n"
                text += f"📡 Провайдер: {data['isp']}\n"
                text += f"🗺️ Координаты: {data['lat']}, {data['lon']}\n"
                text += f"🔢 Организация: {data.get('org', 'N/A')}"
                
                await message.answer(text, parse_mode="Markdown")
            else:
                await message.answer("❌ IP не найден")
                
        except Exception as e:
            await message.answer(f"❌ Ошибка: {str(e)}")

@dp.message(Command("email"))
async def cmd_email(message: Message):
    args = message.text.split()
    if len(args) < 2:
        await message.answer("❌ Укажи email: `/email test@example.com`")
        return
    
    email = args[1].strip()
    
    await message.answer(f"🔍 Проверяю email `{email}` в утечках...")
    
    # HIBP проверка (бесплатный API)
    async with aiohttp.ClientSession() as session:
        try:
            headers = {"hibp-api-key": "YOUR_HIBP_KEY"}  # Зарегистрируйся на haveibeenpwned.com
            async with session.get(f"https://haveibeenpwned.com/api/v3/breachedaccount/{email}") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    text = f"🚨 *Email* `{email}` *НАЙДЕН В УТЕЧКАХ!*\n\n"
                    for breach in data[:5]:
                        text += f"📛 {breach['Name']} ({breach['BreachDate']})\n"
                    await message.answer(text, parse_mode="Markdown")
                elif resp.status == 404:
                    await message.answer(f"✅ Email `{email}` не найден в утечках", parse_mode="Markdown")
                else:
                    await message.answer("⚠️ Ошибка API, попробуй позже")
        except Exception as e:
            await message.answer(f"❌ Ошибка: {str(e)}")

# ===== 2. БЕЗОПАСНОСТЬ =====

@dp.message(Command("check"))
async def cmd_check(message: Message):
    args = message.text.split()
    if len(args) < 2:
        await message.answer("❌ Укажи ссылку: `/check https://example.com`")
        return
    
    url = args[1].strip()
    await message.answer(f"🛡️ Проверяю ссылку: {url}")
    
    # Простая проверка SSL и заголовков
    try:
        import ssl
        import urllib.request
        
        # SSL сертификат
        host = url.replace("https://", "").replace("http://", "").split("/")[0]
        ctx = ssl.create_default_context()
        with socket.create_connection((host, 443), timeout=10) as sock:
            with ctx.wrap_socket(sock, server_hostname=host) as ssock:
                cert = ssock.getpeercert()
                
        text = f"🔐 *Проверка ссылки* `{url}`\n\n"
        text += f"📅 Сертификат действителен до: {cert['notAfter']}\n"
        text += f"🔑 Выдан: {cert['issuer'][0][0][1]}\n"
        text += f"🌐 Домен: {cert['subject'][0][0][1]}\n"
        
        await message.answer(text, parse_mode="Markdown")
        
    except Exception as e:
        await message.answer(f"⚠️ Не удалось проверить SSL: {str(e)}")

@dp.message(Command("hash"))
async def cmd_hash(message: Message):
    # Если прикреплен файл
    if message.document:
        file = await bot.get_file(message.document.file_id)
        file_path = file.file_path
        downloaded_file = await bot.download_file(file_path)
        
        # Считаем хэши
        md5 = hashlib.md5(downloaded_file.read()).hexdigest()
        downloaded_file.seek(0)
        sha256 = hashlib.sha256(downloaded_file.read()).hexdigest()
        
        text = f"🔐 *Хэши файла* `{message.document.file_name}`\n\n"
        text += f"MD5: `{md5}`\n"
        text += f"SHA256: `{sha256}`\n"
        
        # Проверка в VirusTotal
        # (нужен API ключ)
        
        await message.answer(text, parse_mode="Markdown")
    else:
        await message.answer("❌ Прикрепи файл для проверки")

@dp.message(Command("ssl"))
async def cmd_ssl(message: Message):
    args = message.text.split()
    if len(args) < 2:
        await message.answer("❌ Укажи домен: `/ssl google.com`")
        return
    
    domain = args[1].strip()
    
    try:
        import ssl
        import socket
        from datetime import datetime
        
        ctx = ssl.create_default_context()
        with socket.create_connection((domain, 443), timeout=10) as sock:
            with ctx.wrap_socket(sock, server_hostname=domain) as ssock:
                cert = ssock.getpeercert()
        
        text = f"🔐 *SSL сертификат* `{domain}`\n\n"
        text += f"📅 Выдан: {cert['notBefore']}\n"
        text += f"📅 Истекает: {cert['notAfter']}\n"
        text += f"🔑 Издатель: {cert['issuer'][0][0][1]}\n"
        text += f"🌐 Домен: {cert['subject'][0][0][1]}\n"
        text += f"🔢 Версия: {cert.get('version', 'N/A')}"
        
        await message.answer(text, parse_mode="Markdown")
        
    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)}")

# ===== 3. АНАЛИЗ =====

@dp.message(Command("scan"))
async def cmd_scan(message: Message):
    args = message.text.split()
    if len(args) < 2:
        await message.answer("❌ Укажи IP: `/scan 127.0.0.1`")
        return
    
    ip = args[1].strip()
    await message.answer(f"🔍 Сканирую порты {ip}... (TOP 20)")
    
    # TOP 20 портов
    ports = [21, 22, 23, 25, 53, 80, 110, 111, 135, 139, 143, 443, 445, 993, 995, 1723, 3306, 3389, 5432, 8080]
    open_ports = []
    
    for port in ports:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex((ip, port))
            if result == 0:
                open_ports.append(port)
            sock.close()
        except:
            pass
    
    if open_ports:
        text = f"✅ *Открытые порты* `{ip}`:\n"
        for port in open_ports:
            text += f"🔓 {port}"
            if port == 80: text += " (HTTP)"
            elif port == 443: text += " (HTTPS)"
            elif port == 22: text += " (SSH)"
            elif port == 3306: text += " (MySQL)"
            elif port == 3389: text += " (RDP)"
            text += "\n"
        await message.answer(text, parse_mode="Markdown")
    else:
        await message.answer(f"❌ Открытые порты не найдены на {ip}")

@dp.message(Command("log"))
async def cmd_log(message: Message):
    if not message.document:
        await message.answer("❌ Прикрепи лог-файл для анализа")
        return
    
    file = await bot.get_file(message.document.file_id)
    file_path = file.file_path
    downloaded_file = await bot.download_file(file_path)
    
    content = downloaded_file.read().decode('utf-8', errors='ignore')
    lines = content.split('\n')
    
    # Поиск аномалий
    anomalies = []
    ip_pattern = re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}\b')
    emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', content)
    ips = ip_pattern.findall(content)
    
    # Ищем подозрительные паттерны
    for line in lines:
        if 'failed' in line.lower() or 'error' in line.lower() or 'warning' in line.lower():
            anomalies.append(line[:200])
        if 'sql' in line.lower() or 'script' in line.lower():
            anomalies.append(line[:200])
    
    text = f"📊 *Анализ лога*\n\n"
    text += f"📄 Строк: {len(lines)}\n"
    text += f"📧 Email: {len(emails)}\n"
    text += f"🌐 IP: {len(set(ips))} уникальных\n"
    text += f"⚠️ Аномалий: {len(anomalies)}\n\n"
    
    if anomalies:
        text += "🚨 *Найденные аномалии:*\n"
        for a in anomalies[:10]:
            text += f"`{a}`\n"
    
    await message.answer(text, parse_mode="Markdown")

@dp.message(Command("decode"))
async def cmd_decode(message: Message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("❌ Напиши текст для декодирования:\n`/decode SGVsbG8=`")
        return
    
    text = args[1].strip()
    
    result = "📊 *Результаты декодирования:*\n\n"
    
    # Base64
    try:
        decoded = base64.b64decode(text).decode('utf-8')
        result += f"🔐 Base64: `{decoded}`\n"
    except:
        result += "🔐 Base64: ❌\n"
    
    # URL decode
    try:
        decoded = urllib.parse.unquote(text)
        result += f"🔗 URL: `{decoded}`\n"
    except:
        result += "🔗 URL: ❌\n"
    
    # Hex
    try:
        decoded = bytes.fromhex(text).decode('utf-8')
        result += f"🔢 Hex: `{decoded}`\n"
    except:
        result += "🔢 Hex: ❌\n"
    
    await message.answer(result, parse_mode="Markdown")

# ===== 4. ИНСТРУМЕНТЫ =====

@dp.message(Command("passgen"))
async def cmd_passgen(message: Message):
    args = message.text.split()
    length = 16
    if len(args) > 1 and args[1].isdigit():
        length = int(args[1])
    
    import random
    import string
    
    chars = string.ascii_letters + string.digits + "!@#$%^&*()_+-="
    password = ''.join(random.choice(chars) for _ in range(length))
    
    # Энтропия
    entropy = length * (len(chars).bit_length())
    
    text = f"🔑 *Сгенерирован пароль*\n\n"
    text += f"`{password}`\n\n"
    text += f"📊 Длина: {length} символов\n"
    text += f"🔐 Энтропия: {entropy} бит\n"
    
    if entropy > 80:
        text += "✅ Супер-безопасный пароль\n"
    elif entropy > 60:
        text += "⚠️ Средняя защита\n"
    else:
        text += "❌ Слабый пароль\n"
    
    await message.answer(text, parse_mode="Markdown")

@dp.message(Command("exif"))
async def cmd_exif(message: Message):
    if not message.photo:
        await message.answer("❌ Пришли фото для анализа")
        return
    
    # Получаем файл
    photo = message.photo[-1]
    file = await bot.get_file(photo.file_id)
    file_path = file.file_path
    
    await message.answer("📸 Анализирую метаданные фото...")
    
    # Базовый анализ (без библиотек)
    text = "📸 *Метаданные фото*\n\n"
    text += f"📏 Размер: {photo.width}x{photo.height}\n"
    text += f"📁 ID файла: {photo.file_id[:20]}...\n"
    text += f"📅 Дата загрузки: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n"
    text += "⚠️ Для полного EXIF нужна библиотека PIL\n"
    text += "Установи: `pip install pillow`\n"
    
    await message.answer(text, parse_mode="Markdown")

# ===== 5. МОНИТОРИНГ =====

@dp.message(Command("monitor"))
async def cmd_monitor(message: Message):
    args = message.text.split()
    if len(args) < 2:
        await message.answer(
            "📱 *Мониторинг хостов*\n\n"
            "Добавить: `/monitor add google.com`\n"
            "Список: `/monitor list`\n"
            "Статус: `/monitor status`",
            parse_mode="Markdown"
        )
        return
    
    action = args[1]
    data = load_data()
    user = get_user(data, message.from_user.id)
    
    if action == "add" and len(args) > 2:
        host = args[2]
        user["monitors"].append(host)
        save_data(data)
        await message.answer(f"✅ Хост `{host}` добавлен в мониторинг", parse_mode="Markdown")
    
    elif action == "list":
        if user["monitors"]:
            text = "📱 *Мониторинг хостов:*\n\n"
            for host in user["monitors"]:
                text += f"🌐 {host}\n"
            await message.answer(text, parse_mode="Markdown")
        else:
            await message.answer("❌ Нет хостов в мониторинге")
    
    elif action == "status":
        if not user["monitors"]:
            await message.answer("❌ Нет хостов для проверки")
            return
        
        text = "📊 *Статус хостов:*\n\n"
        for host in user["monitors"]:
            try:
                socket.gethostbyname(host)
                text += f"✅ {host} — доступен\n"
            except:
                text += f"❌ {host} — НЕДОСТУПЕН\n"
        
        await message.answer(text, parse_mode="Markdown")

# ===== 6. ОТЧЕТЫ =====

@dp.message(Command("report"))
async def cmd_report(message: Message):
    data = load_data()
    user = get_user(data, message.from_user.id)
    
    text = "📋 *Отчет по безопасности*\n\n"
    text += f"📅 Дата: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n"
    text += f"👤 Пользователь: {message.from_user.username or 'Неизвестно'}\n\n"
    
    # Проверки
    if user["monitors"]:
        text += "🌐 *Мониторинг хостов:*\n"
        for host in user["monitors"]:
            try:
                socket.gethostbyname(host)
                text += f"✅ {host} — OK\n"
            except:
                text += f"❌ {host} — ПРОБЛЕМА\n"
        text += "\n"
    
    if len(user["history"]) > 0:
        text += "📊 *Последние действия:*\n"
        for h in user["history"][-5:]:
            text += f"• {h}\n"
    
    await message.answer(text, parse_mode="Markdown")

# ===== КНОПКИ =====

@dp.callback_query()
async def callback_handler(callback: types.CallbackQuery):
    data = callback.data
    
    responses = {
        "menu_osint": "🔍 *OSINT команды:*\n\n/domain — информация по домену\n/ip — информация по IP\n/email — проверка в утечках",
        "menu_security": "🛡️ *Безопасность:*\n\n/check — проверка ссылки\n/hash — проверка хэша файла\n/ssl — проверка SSL сертификата",
        "menu_analysis": "📊 *Анализ:*\n\n/scan — сканирование портов\n/log — анализ логов\n/decode — декодирование текста",
        "menu_tools": "🔑 *Инструменты:*\n\n/passgen — генератор паролей\n/exif — метаданные фото",
        "menu_monitor": "📱 *Мониторинг:*\n\n/monitor add — добавить хост\n/monitor list — список хостов\n/monitor status — статус",
        "menu_report": "📋 *Отчет:*\n\n/report — сгенерировать отчет"
    }
    
    await callback.message.answer(responses.get(data, "❌ Неизвестная команда"), parse_mode="Markdown")
    await callback.answer()

# ===== ЗАПУСК =====

async def main():
    print("🦾 Кибер-Комбайн запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())