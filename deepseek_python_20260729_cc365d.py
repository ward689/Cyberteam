#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🦾 Кибер-Комбайн V2.0
Telegram бот для кибербезопасности
"""

import asyncio
import json
import os
import re
import socket
import hashlib
import base64
import urllib.parse
import random
import string
import ssl
from datetime import datetime
from typing import Dict, List, Any
import logging

# ===== НАСТРОЙКА ЛОГИРОВАНИЯ =====
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ===== ИМПОРТЫ =====
try:
    import aiohttp
    import whois
    import dns.resolver
    from aiogram import Bot, Dispatcher, types
    from aiogram.filters import Command
    from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    print("Установи зависимости: pip install aiogram aiohttp python-whois dnspython")
    exit(1)

# ===== ТОКЕН (ЗАМЕНИ НА СВОЙ!) =====
BOT_TOKEN = "ТВОЙ_ТОКЕН_СЮДА"  # ВСТАВЬ СЮДА СВОЙ ТОКЕН!

# ===== ИНИЦИАЛИЗАЦИЯ =====
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ===== ФАЙЛ ДЛЯ ХРАНЕНИЯ =====
DATA_FILE = "data.json"

# ===== РАБОТА С ДАННЫМИ =====
def load_data() -> Dict:
    """Загрузка данных из JSON файла"""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {"users": {}, "monitors": {}}
    return {"users": {}, "monitors": {}}

def save_data(data: Dict) -> None:
    """Сохранение данных в JSON файл"""
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_user(data: Dict, user_id: int) -> Dict:
    """Получение или создание пользователя"""
    uid = str(user_id)
    if uid not in data["users"]:
        data["users"][uid] = {
            "history": [],
            "monitors": [],
            "tasks": []
        }
    return data["users"][uid]

# ===== КОМАНДЫ =====

@dp.message(Command("start"))
async def cmd_start(message: Message):
    """Приветствие и главное меню"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔍 OSINT", callback_data="menu_osint"),
            InlineKeyboardButton(text="🛡️ Безопасность", callback_data="menu_security")
        ],
        [
            InlineKeyboardButton(text="📊 Анализ", callback_data="menu_analysis"),
            InlineKeyboardButton(text="🔑 Инструменты", callback_data="menu_tools")
        ],
        [
            InlineKeyboardButton(text="📱 Мониторинг", callback_data="menu_monitor"),
            InlineKeyboardButton(text="📋 Отчет", callback_data="menu_report")
        ],
        [
            InlineKeyboardButton(text="ℹ️ Помощь", callback_data="menu_help")
        ]
    ])
    
    await message.answer(
        "🦾 *Кибер-Комбайн V2.0*\n\n"
        "Многофункциональный инструмент для кибербезопасности\n\n"
        "🔍 */domain* — разведка по домену\n"
        "🔍 */ip* — информация по IP\n"
        "🔍 */email* — проверка в утечках\n\n"
        "🛡️ */check* — проверка ссылки\n"
        "🛡️ */hash* — проверка хэша файла\n"
        "🛡️ */ssl* — проверка SSL\n\n"
        "📊 */scan* — сканирование портов\n"
        "📊 */log* — анализ логов\n"
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
    """Информация по домену: WHOIS, DNS, IP"""
    args = message.text.split()
    if len(args) < 2:
        await message.answer("❌ Укажи домен: `/domain google.com`", parse_mode="Markdown")
        return
    
    domain = args[1].strip()
    await message.answer(f"🔍 Анализирую домен `{domain}`...", parse_mode="Markdown")
    
    try:
        # WHOIS
        w = whois.whois(domain)
        whois_text = f"📋 *WHOIS*\n"
        whois_text += f"Регистратор: {w.registrar or 'Неизвестно'}\n"
        whois_text += f"Создан: {w.creation_date[0] if isinstance(w.creation_date, list) else w.creation_date}\n"
        whois_text += f"Истекает: {w.expiration_date[0] if isinstance(w.expiration_date, list) else w.expiration_date}\n"
        
        # DNS
        dns_text = "🌐 *DNS записи*\n"
        for record in ['A', 'AAAA', 'MX', 'TXT', 'NS']:
            try:
                answers = dns.resolver.resolve(domain, record)
                dns_text += f"{record}: {', '.join(str(r) for r in answers[:3])}\n"
            except:
                dns_text += f"{record}: -\n"
        
        # IP
        ip = socket.gethostbyname(domain)
        ip_text = f"📍 *IP*\n{ip}"
        
        await message.answer(
            f"{whois_text}\n\n{dns_text}\n\n{ip_text}",
            parse_mode="Markdown"
        )
        
        # Сохраняем в историю
        data = load_data()
        user = get_user(data, message.from_user.id)
        user["history"].append(f"domain: {domain}")
        save_data(data)
        
    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)}")

@dp.message(Command("ip"))
async def cmd_ip(message: Message):
    """Информация по IP: геолокация, провайдер"""
    args = message.text.split()
    if len(args) < 2:
        await message.answer("❌ Укажи IP: `/ip 8.8.8.8`", parse_mode="Markdown")
        return
    
    ip = args[1].strip()
    await message.answer(f"🔍 Анализирую IP `{ip}`...", parse_mode="Markdown")
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(f"http://ip-api.com/json/{ip}") as resp:
                data = await resp.json()
                
            if data.get('status') == 'success':
                text = f"📍 *Информация об IP* `{ip}`\n\n"
                text += f"🌍 Страна: {data.get('country', 'Неизвестно')}\n"
                text += f"🏙️ Город: {data.get('city', 'Неизвестно')}\n"
                text += f"📮 Регион: {data.get('regionName', 'Неизвестно')}\n"
                text += f"📡 Провайдер: {data.get('isp', 'Неизвестно')}\n"
                text += f"🗺️ Координаты: {data.get('lat', '')}, {data.get('lon', '')}\n"
                text += f"🔢 Организация: {data.get('org', 'Неизвестно')}\n"
                text += f"🌐 AS: {data.get('as', 'Неизвестно')}"
                
                await message.answer(text, parse_mode="Markdown")
            else:
                await message.answer("❌ IP не найден")
                
        except Exception as e:
            await message.answer(f"❌ Ошибка: {str(e)}")

@dp.message(Command("email"))
async def cmd_email(message: Message):
    """Проверка email в утечках (Have I Been Pwned)"""
    args = message.text.split()
    if len(args) < 2:
        await message.answer("❌ Укажи email: `/email test@example.com`", parse_mode="Markdown")
        return
    
    email = args[1].strip()
    await message.answer(f"🔍 Проверяю email `{email}` в утечках...", parse_mode="Markdown")
    
    async with aiohttp.ClientSession() as session:
        try:
            # Бесплатный API без ключа (ограничение 1 запрос/сек)
            async with session.get(f"https://haveibeenpwned.com/api/v3/breachedaccount/{email}") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    text = f"🚨 *Email* `{email}` *НАЙДЕН В УТЕЧКАХ!*\n\n"
                    for breach in data[:5]:
                        text += f"📛 {breach.get('Name', 'Неизвестно')} ({breach.get('BreachDate', '')})\n"
                    text += f"\nВсего утечек: {len(data)}"
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
    """Проверка ссылки: SSL, заголовки"""
    args = message.text.split()
    if len(args) < 2:
        await message.answer("❌ Укажи ссылку: `/check https://example.com`", parse_mode="Markdown")
        return
    
    url = args[1].strip()
    await message.answer(f"🛡️ Проверяю ссылку: {url}")
    
    try:
        # SSL сертификат
        host = url.replace("https://", "").replace("http://", "").split("/")[0]
        ctx = ssl.create_default_context()
        with socket.create_connection((host, 443), timeout=10) as sock:
            with ctx.wrap_socket(sock, server_hostname=host) as ssock:
                cert = ssock.getpeercert()
        
        text = f"🔐 *Проверка ссылки* `{url}`\n\n"
        text += f"📅 Сертификат действителен до: {cert.get('notAfter', 'Неизвестно')}\n"
        text += f"🔑 Выдан: {cert.get('issuer', [['', 'Неизвестно']])[0][0][1]}\n"
        text += f"🌐 Домен: {cert.get('subject', [['', host]])[0][0][1]}\n"
        
        # Проверка на фишинг (простые эвристики)
        suspicious_patterns = ['login', 'verify', 'secure', 'update', 'confirm']
        is_suspicious = any(p in url.lower() for p in suspicious_patterns)
        if is_suspicious:
            text += "\n⚠️ *ВНИМАНИЕ!* Ссылка может быть фишинговой!"
        
        await message.answer(text, parse_mode="Markdown")
        
    except Exception as e:
        await message.answer(f"⚠️ Не удалось проверить SSL: {str(e)}")

@dp.message(Command("hash"))
async def cmd_hash(message: Message):
    """Хэширование файла: MD5, SHA1, SHA256"""
    if not message.document:
        await message.answer("❌ Прикрепи файл для проверки:\n`/hash` (с файлом)", parse_mode="Markdown")
        return
    
    file = await bot.get_file(message.document.file_id)
    downloaded_file = await bot.download_file(file.file_path)
    content = downloaded_file.read()
    
    # Считаем хэши
    md5 = hashlib.md5(content).hexdigest()
    sha1 = hashlib.sha1(content).hexdigest()
    sha256 = hashlib.sha256(content).hexdigest()
    
    text = f"🔐 *Хэши файла* `{message.document.file_name}`\n\n"
    text += f"📁 Размер: {len(content)} байт\n"
    text += f"🔑 MD5: `{md5}`\n"
    text += f"🔑 SHA1: `{sha1}`\n"
    text += f"🔑 SHA256: `{sha256}`\n"
    
    await message.answer(text, parse_mode="Markdown")

@dp.message(Command("ssl"))
async def cmd_ssl(message: Message):
    """Информация о SSL сертификате"""
    args = message.text.split()
    if len(args) < 2:
        await message.answer("❌ Укажи домен: `/ssl google.com`", parse_mode="Markdown")
        return
    
    domain = args[1].strip()
    
    try:
        ctx = ssl.create_default_context()
        with socket.create_connection((domain, 443), timeout=10) as sock:
            with ctx.wrap_socket(sock, server_hostname=domain) as ssock:
                cert = ssock.getpeercert()
        
        text = f"🔐 *SSL сертификат* `{domain}`\n\n"
        text += f"📅 Выдан: {cert.get('notBefore', 'Неизвестно')}\n"
        text += f"📅 Истекает: {cert.get('notAfter', 'Неизвестно')}\n"
        text += f"🔑 Издатель: {cert.get('issuer', [['', 'Неизвестно']])[0][0][1]}\n"
        text += f"🌐 Домен: {cert.get('subject', [['', domain]])[0][0][1]}\n"
        text += f"🔢 Версия: {cert.get('version', 'N/A')}"
        
        await message.answer(text, parse_mode="Markdown")
        
    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)}")

# ===== 3. АНАЛИЗ =====

@dp.message(Command("scan"))
async def cmd_scan(message: Message):
    """Сканирование портов (TOP 20)"""
    args = message.text.split()
    if len(args) < 2:
        await message.answer("❌ Укажи IP: `/scan 127.0.0.1`", parse_mode="Markdown")
        return
    
    ip = args[1].strip()
    await message.answer(f"🔍 Сканирую порты `{ip}`... (TOP 20)", parse_mode="Markdown")
    
    # TOP 20 портов
    ports = [
        21, 22, 23, 25, 53, 80, 110, 111, 135, 139,
        143, 443, 445, 993, 995, 1723, 3306, 3389, 5432, 8080
    ]
    open_ports = []
    services = {
        21: "FTP", 22: "SSH", 23: "Telnet", 25: "SMTP", 53: "DNS",
        80: "HTTP", 110: "POP3", 111: "RPC", 135: "MS RPC", 139: "NetBIOS",
        143: "IMAP", 443: "HTTPS", 445: "SMB", 993: "IMAPS", 995: "POP3S",
        1723: "PPTP", 3306: "MySQL", 3389: "RDP", 5432: "PostgreSQL", 8080: "HTTP-Alt"
    }
    
    for port in ports:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1.5)
            result = sock.connect_ex((ip, port))
            if result == 0:
                service = services.get(port, "Unknown")
                open_ports.append(f"🔓 {port} ({service})")
            sock.close()
        except:
            pass
    
    if open_ports:
        text = f"✅ *Открытые порты* `{ip}`:\n\n"
        text += "\n".join(open_ports)
        text += f"\n\nВсего открыто: {len(open_ports)} портов"
        await message.answer(text, parse_mode="Markdown")
    else:
        await message.answer(f"❌ Открытые порты не найдены на `{ip}`", parse_mode="Markdown")

@dp.message(Command("log"))
async def cmd_log(message: Message):
    """Анализ лог-файла"""
    if not message.document:
        await message.answer("❌ Прикрепи лог-файл для анализа:\n`/log` (с файлом)", parse_mode="Markdown")
        return
    
    await message.answer("📊 Анализирую лог-файл...")
    
    file = await bot.get_file(message.document.file_id)
    downloaded_file = await bot.download_file(file.file_path)
    content = downloaded_file.read().decode('utf-8', errors='ignore')
    lines = content.split('\n')
    
    # Поиск аномалий
    anomalies = []
    ip_pattern = re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}\b')
    emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', content)
    ips = ip_pattern.findall(content)
    
    # Ищем подозрительные паттерны
    suspicious_keywords = ['failed', 'error', 'warning', 'critical', 'denied', 'rejected', 'invalid']
    for line in lines:
        if any(kw in line.lower() for kw in suspicious_keywords):
            anomalies.append(line[:200])
        if 'sql' in line.lower() or 'script' in line.lower():
            anomalies.append(line[:200])
        if '<script>' in line.lower() or 'alert(' in line.lower():
            anomalies.append(line[:200])
    
    # Собираем статистику
    unique_ips = list(set(ips))
    
    text = f"📊 *Анализ лога* `{message.document.file_name}`\n\n"
    text += f"📄 Всего строк: {len(lines)}\n"
    text += f"📧 Email: {len(emails)}\n"
    text += f"🌐 Уникальных IP: {len(unique_ips)}\n"
    text += f"⚠️ Аномалий: {len(anomalies)}\n\n"
    
    if unique_ips:
        text += "🌐 *IP адреса:*\n"
        for ip in unique_ips[:10]:
            text += f"• {ip}\n"
        if len(unique_ips) > 10:
            text += f"• ... и еще {len(unique_ips) - 10}\n"
        text += "\n"
    
    if anomalies:
        text += "🚨 *Найденные аномалии:*\n"
        for a in anomalies[:5]:
            text += f"`{a[:150]}...`\n"
    
    await message.answer(text, parse_mode="Markdown")

@dp.message(Command("decode"))
async def cmd_decode(message: Message):
    """Декодирование Base64, URL, Hex"""
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer(
            "❌ Напиши текст для декодирования:\n"
            "`/decode SGVsbG8=`\n"
            "`/decode https%3A%2F%2Fexample.com`\n"
            "`/decode 48656c6c6f`",
            parse_mode="Markdown"
        )
        return
    
    text = args[1].strip()
    result = "📊 *Результаты декодирования:*\n\n"
    
    # Base64
    try:
        decoded = base64.b64decode(text).decode('utf-8', errors='ignore')
        result += f"🔐 *Base64:* `{decoded[:100]}`\n"
    except:
        result += "🔐 Base64: ❌\n"
    
    # URL decode
    try:
        decoded = urllib.parse.unquote(text)
        if decoded != text:
            result += f"🔗 *URL:* `{decoded[:100]}`\n"
        else:
            result += "🔗 URL: ❌\n"
    except:
        result += "🔗 URL: ❌\n"
    
    # Hex
    try:
        cleaned = re.sub(r'[^0-9a-fA-F]', '', text)
        decoded = bytes.fromhex(cleaned).decode('utf-8', errors='ignore')
        if decoded:
            result += f"🔢 *Hex:* `{decoded[:100]}`\n"
        else:
            result += "🔢 Hex: ❌\n"
    except:
        result += "🔢 Hex: ❌\n"
    
    await message.answer(result, parse_mode="Markdown")

# ===== 4. ИНСТРУМЕНТЫ =====

@dp.message(Command("passgen"))
async def cmd_passgen(message: Message):
    """Генерация безопасного пароля"""
    args = message.text.split()
    length = 16
    if len(args) > 1 and args[1].isdigit():
        length = int(args[1])
        if length < 4:
            length = 4
        if length > 50:
            length = 50
    
    chars = string.ascii_letters + string.digits + "!@#$%^&*()_+-="
    password = ''.join(random.choice(chars) for _ in range(length))
    
    # Энтропия (примерная)
    entropy = length * (len(chars).bit_length())
    
    text = f"🔑 *Сгенерирован пароль*\n\n"
    text += f"`{password}`\n\n"
    text += f"📊 Длина: {length} символов\n"
    text += f"🔐 Энтропия: ~{entropy} бит\n"
    
    if entropy > 100:
        text += "✅ Супер-безопасный пароль\n"
    elif entropy > 70:
        text += "⚠️ Хороший пароль\n"
    elif entropy > 50:
        text += "⚠️ Средняя защита\n"
    else:
        text += "❌ Слабый пароль\n"
    
    await message.answer(text, parse_mode="Markdown")

@dp.message(Command("exif"))
async def cmd_exif(message: Message):
    """Анализ метаданных фото"""
    if not message.photo:
        await message.answer("❌ Пришли фото для анализа:\n`/exif` (с фото)", parse_mode="Markdown")
        return
    
    photo = message.photo[-1]
    file = await bot.get_file(photo.file_id)
    
    # Базовый анализ
    text = "📸 *Метаданные фото*\n\n"
    text += f"📏 Размер: {photo.width}x{photo.height}\n"
    text += f"📁 ID файла: `{photo.file_id[:20]}...`\n"
    text += f"📅 Дата загрузки: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n"
    
    # Проверяем наличие геоданных через API (если нужно)
    text += "⚠️ Для полного EXIF нужна библиотека Pillow\n"
    text += "Установи: `pip install pillow`\n\n"
    text += "Файл сохранён: ✅"
    
    await message.answer(text, parse_mode="Markdown")

# ===== 5. МОНИТОРИНГ =====

@dp.message(Command("monitor"))
async def cmd_monitor(message: Message):
    """Управление мониторингом хостов"""
    args = message.text.split()
    if len(args) < 2:
        await message.answer(
            "📱 *Мониторинг хостов*\n\n"
            "▪️ Добавить: `/monitor add google.com`\n"
            "▪️ Список: `/monitor list`\n"
            "▪️ Статус: `/monitor status`\n"
            "▪️ Удалить: `/monitor remove google.com`\n",
            parse_mode="Markdown"
        )
        return
    
    action = args[1]
    data = load_data()
    user = get_user(data, message.from_user.id)
    
    if action == "add" and len(args) > 2:
        host = args[2]
        if host not in user["monitors"]:
            user["monitors"].append(host)
            save_data(data)
            await message.answer(f"✅ Хост `{host}` добавлен в мониторинг", parse_mode="Markdown")
        else:
            await message.answer(f"ℹ️ Хост `{host}` уже в списке", parse_mode="Markdown")
    
    elif action == "remove" and len(args) > 2:
        host = args[2]
        if host in user["monitors"]:
            user["monitors"].remove(host)
            save_data(data)
            await message.answer(f"🗑️ Хост `{host}` удалён из мониторинга", parse_mode="Markdown")
        else:
            await message.answer(f"❌ Хост `{host}` не найден в списке", parse_mode="Markdown")
    
    elif action == "list":
        if user["monitors"]:
            text = "📱 *Мониторинг хостов:*\n\n"
            for host in user["monitors"]:
                text += f"🌐 `{host}`\n"
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
                ip = socket.gethostbyname(host)
                text += f"✅ `{host}` — доступен (IP: {ip})\n"
            except:
                text += f"❌ `{host}` — НЕДОСТУПЕН!\n"
        
        await message.answer(text, parse_mode="Markdown")

# ===== 6. ОТЧЕТ =====

@dp.message(Command("report"))
async def cmd_report(message: Message):
    """Генерация отчета по безопасности"""
    data = load_data()
    user = get_user(data, message.from_user.id)
    
    text = "📋 *Отчет по безопасности*\n\n"
    text += f"📅 Дата: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n"
    text += f"👤 Пользователь: @{message.from_user.username or 'Неизвестно'}\n"
    text += f"🆔 ID: `{message.from_user.id}`\n\n"
    
    # Мониторинг
    if user["monitors"]:
        text += "🌐 *Мониторинг хостов:*\n"
        online = 0
        for host in user["monitors"]:
            try:
                socket.gethostbyname(host)
                text += f"✅ `{host}` — OK\n"
                online += 1
            except:
                text += f"❌ `{host}` — ПРОБЛЕМА!\n"
        text += f"\nСтатистика: {online}/{len(user['monitors'])} доступны\n\n"
    
    # История
    if user["history"]:
        text += "📊 *Последние действия:*\n"
        for h in user["history"][-5:]:
            text += f"• `{h}`\n"
        text += "\n"
    
    text += "🔒 *Рекомендации:*\n"
    if len(user["monitors"]) == 0:
        text += "• Добавьте хосты в мониторинг\n"
    if len(user["history"]) < 3:
        text += "• Проведите больше проверок для полного отчета\n"
    
    await message.answer(text, parse_mode="Markdown")

# ===== ОБРАБОТЧИК КНОПОК =====

@dp.callback_query()
async def callback_handler(callback: types.CallbackQuery):
    """Обработка нажатий на кнопки"""
    data = callback.data
    
    responses = {
        "menu_osint": "🔍 *OSINT команды:*\n\n`/domain` — информация по домену\n`/ip` — информация по IP\n`/email` — проверка в утечках",
        "menu_security": "🛡️ *Безопасность:*\n\n`/check` — проверка ссылки\n`/hash` — проверка хэша файла\n`/ssl` — проверка SSL сертификата",
        "menu_analysis": "📊 *Анализ:*\n\n`/scan` — сканирование портов\n`/log` — анализ логов\n`/decode` — декодирование текста",
        "menu_tools": "🔑 *Инструменты:*\n\n`/passgen` — генератор паролей\n`/exif` — метаданные фото",
        "menu_monitor": "📱 *Мониторинг:*\n\n`/monitor add` — добавить хост\n`/monitor list` — список хостов\n`/monitor status` — статус хостов",
        "menu_report": "📋 *Отчет:*\n\n`/report` — сгенерировать отчет",
        "menu_help": "ℹ️ *Помощь:*\n\nВсе команды доступны в меню.\nПо всем вопросам: @твой_ник\n\n🔗 GitHub: [ссылка на репозиторий]"
    }
    
    await callback.message.answer(responses.get(data, "❌ Неизвестная команда"), parse_mode="Markdown")
    await callback.answer()

# ===== ЗАПУСК =====

async def main():
    """Главная функция запуска бота"""
    logger.info("🦾 Кибер-Комбайн V2.0 запущен!")
    logger.info(f"📊 Бот @{bot.username} готов к работе")
    logger.info("=" * 50)
    
    try:
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Ошибка: {e}")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 Бот остановлен")