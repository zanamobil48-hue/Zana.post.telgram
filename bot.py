import asyncio, os, gspread, json, requests, re
from PIL import Image, ImageDraw, ImageFont
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from google.oauth2.service_account import Credentials

TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN', '')
GOOGLE_CREDS = os.environ.get('GOOGLE_CREDS', '')
PAT_TOKEN = os.environ.get('PAT_TOKEN', '')
REPO = os.environ.get('GITHUB_REPOSITORY', '')

# 🌟 گۆڕدرا بۆ چەناڵە تێستەکەت بۆ ئەوەی بە سەلامەتی تاقی بکەیتەوە
CHANNEL_ID = '@zanatest123'
SHEET_ID = '1RkGwtLZfZ_DaScAnFH9zKdDuAtO90NjZLCxTRBSdJNU'

# 📍 ڕێکخستنی نوێی بۆشاییەکە (هێنانە خوارەوەی زیاتر بۆ ناوەڕاستی چوارگۆشە شووشەییەکە)
BOXES = {
    '15': (100, 190, 980, 330),
    '20': (100, 190, 980, 330),
    '25': (100, 190, 980, 330),
    '30': (100, 190, 980, 330),
    '35': (100, 190, 980, 330),
    '40': (100, 190, 980, 330),
    '45': (100, 190, 980, 330),
    '50': (100, 190, 980, 330),
    '55': (100, 190, 980, 330),
    '60': (100, 190, 980, 330),
    '65': (100, 190, 980, 330),
    '70': (100, 190, 980, 330),
    '80': (100, 190, 980, 330),
    '85': (100, 190, 980, 330),
    '100': (100, 190, 980, 330),
    'default': (100, 190, 980, 330)
}

PRICE_ORDER = ['15', '20', '25', '30', '35', '40', '45', '50', '55', '60', '65', '70', '80', '85', '100']

def get_last_row():
    try:
        url = f'https://api.github.com/repos/{REPO}/actions/variables/LAST_ROW'
        headers = {'Authorization': f'token {PAT_TOKEN}'}
        r = requests.get(url, headers=headers)
        if r.status_code == 200:
            return int(r.json().get('value', '0'))
    except:
        pass
    return 0

def set_last_row(row):
    try:
        url = f'https://api.github.com/repos/{REPO}/actions/variables/LAST_ROW'
        headers = {'Authorization': f'token {PAT_TOKEN}'}
        requests.patch(url, headers=headers, json={'value': str(row)})
    except:
        pass

def draw_centered(draw, text, font_path, cx, cy, max_w, max_h, color, start=120):
    for size in range(start, 20, -2):
        font = ImageFont.truetype(font_path, size)
        bbox = draw.textbbox((0,0), text, font=font)
        tw, th = bbox[2]-bbox[0], bbox[3]-bbox[1]
        if tw <= max_w and th <= max_h:
            x = cx - (bbox[0]+bbox[2])//2
            y = cy - (bbox[1]+bbox[3])//2
            draw.text((x, y), text, font=font, fill=color)
            return size
    return 0

def format_price(raw):
    s = str(raw).strip().replace(',','').replace('،','').replace(' ','')
    digits = re.findall(r'\d+', s)
    if digits:
        try:
            n = float(digits[0])
            if n < 1000: n *= 1000
            return f'{int(n // 1000)} هەزار'
        except:
            pass
    return str(raw)

def get_sort_key(row):
    price_clean = format_price(row[1])
    words = price_clean.split()
    price_num = words[0] if words else ''
    if price_num in PRICE_ORDER:
        return PRICE_ORDER.index(price_num)
    return len(PRICE_ORDER)

def create_image(phone, price_raw, out_path):
    price_clean = format_price(price_raw)
    words = price_clean.split()
    price_num = words[0] if words else 'default'
    
    bg_name = f'{price_num}.jpg'
    if not os.path.exists(bg_name):
        print(f"⚠️ وێنەی {bg_name} نەدۆزرایەوە، background.jpg بەکاردێت.")
        bg_name = 'background.jpg'
        
    img = Image.open(bg_name).copy()
    
    if img.size != (1080, 1080):
        img = img.resize((1080, 1080), Image.LANCZOS)
        
    draw = ImageDraw.Draw(img)
    
    box = BOXES.get(price_num, BOXES['default'])
    cx1 = (box[0] + box[2]) // 2
    cy1 = (box[1] + box[3]) // 2
    
    # نووسینی سپی لە ناوەڕاستی چوارگۆشەکەدا
    draw_centered(draw, str(phone), 'NRT-Bd.ttf', cx1, cy1,
        box[2] - box[0] - 60, box[3] - box[1] - 10, '#FFFFFF', start=110)
        
    img.save(out_path, 'JPEG', quality=95)

async def main():
    if not TELEGRAM_TOKEN or not GOOGLE_CREDS:
        print("❌ کێشە لە سکرێتەکان (Secrets) هەیە!")
        return

    try:
        creds_json = json.loads(GOOGLE_CREDS)
        creds = Credentials.from_service_account_info(creds_json,
            scopes=['https://www.googleapis.com/auth/spreadsheets.readonly',
                    'https://www.googleapis.com/auth/drive.readonly'])
        gc = gspread.authorize(creds)
        sheet = gc.open_by_key(SHEET_ID).sheet1
        data = sheet.get_all_values()
    except Exception as e:
        print(f"❌ کێشە لە پەیوەستبوون بە گوگل شەیت هەیە: {e}")
        return

    raw_rows = []
    for r in data:
        if len(r) >= 2:
            p1 = str(r[0]).strip()
            p2 = str(r[1]).strip()
            if p1 and p2 and p1 != 'نۆرمال' and p1 != 'مۆبایل' and p2 != 'نرخ':
                raw_rows.append((p1, p2))

    if not raw_rows:
        print("❌ هیچ داتایەکی دروست نەدۆزرایەوە!")
        return

    rows = sorted(raw_rows, key=get_sort_key)
    last = get_last_row()
    if last >= len(rows):
        last = 0

    phone, price = rows[last]
    out = 'post.jpg'
    
    try:
        create_image(phone, price, out)
    except Exception as e:
        print(f"❌ کێشە لە دروستکردنی وێنەکە ڕوویدا: {e}")
        return

    keyboard = [[InlineKeyboardButton("بۆ کڕین نامە بنێرە 🛒", url="https://t.me/zanamobil")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    caption_text = f"📱 مۆبایل: \u200E{phone}\u200E\n💰 نرخ: {format_price(price)}\n\nبۆ کڕین پەیوەندیمان پێوە بکەن 👇"

    try:
        async with Bot(token=TELEGRAM_TOKEN) as bot:
            with open(out, 'rb') as f:
                result = await bot.send_photo(
                    chat_id=CHANNEL_ID, 
                    photo=f,
                    caption=caption_text,
                    reply_markup=reply_markup
                )
                print(f'✅ پۆست کرا بۆ چەناڵی تێست: {result.message_id}')
        set_last_row(last + 1)
    except Exception as e:
        print(f"❌ کێشە لە ناردنی پۆستەکە بۆ تێلەگرام ڕوویدا: {e}")

if __name__ == '__main__':
    asyncio.run(main())
