import asyncio, os, gspread, json, requests
from PIL import Image, ImageDraw, ImageFont
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from google.oauth2.service_account import Credentials

TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN', '')
GOOGLE_CREDS = os.environ.get('GOOGLE_CREDS', '')
PAT_TOKEN = os.environ.get('PAT_TOKEN', '')
REPO = os.environ.get('GITHUB_REPOSITORY', '')
CHANNEL_ID = '@zanamobile1'
SHEET_ID = '1RkGwtLZfZ_DaScAnFH9zKdDuAtO90NjZLCxTRBSdJNU'

# 📍 لێرەدا شوێنی ژمارەی مۆبایل بۆ هەر وێنەیەک دیاری کراوە
BOXES = {
    '65': (247, 530, 3205, 1172),     # شوێنی وێنە پەمەییەکە
    '15': (247, 467, 3205, 1109),     # شوێنی وێنە سوورەکان
    '20': (247, 467, 3205, 1109),
    '25': (247, 467, 3205, 1109),
    '30': (247, 467, 3205, 1109),
    '35': (247, 467, 3205, 1109),
    '40': (247, 467, 3205, 1109),
    '45': (247, 467, 3205, 1109),
    '50': (247, 467, 3205, 1109),
    '55': (247, 467, 3205, 1109),
    '60': (247, 467, 3205, 1109),
    '70': (247, 467, 3205, 1109),
    '80': (247, 467, 3205, 1109),
    '85': (247, 467, 3205, 1109),
    '100': (247, 467, 3205, 1109),
    'default': (247, 467, 3205, 1109)
}

# 🔄 ئەو ڕێزبەندییە دەقیقەی کە دەتەوێت پۆستەکان پێڕەوی بکەن
PRICE_ORDER = ['15', '20', '25', '30', '35', '40', '45', '50', '55', '60', '65', '70', '80', '85', '100']

def get_last_row():
    url = f'https://api.github.com/repos/{REPO}/actions/variables/LAST_ROW'
    headers = {'Authorization': f'token {PAT_TOKEN}'}
    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        return int(r.json().get('value', '0'))
    return 0

def set_last_row(row):
    url = f'https://api.github.com/repos/{REPO}/actions/variables/LAST_ROW'
    headers = {'Authorization': f'token {PAT_TOKEN}'}
    requests.patch(url, headers=headers, json={'value': str(row)})

def draw_centered(draw, text, font_path, cx, cy, max_w, max_h, color, start=600):
    for size in range(start, 20, -5):
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
    s = s.replace('هەزار','').replace('هزار','')
    try:
        n = float(s)
        if n < 1000: n *= 1000
        return f'{int(n // 1000)} هەزار'
    except: return str(raw)

def get_sort_key(row):
    price_clean = format_price(row[1])
    price_num = price_clean.split()[0] if price_clean else ''
    if price_num in PRICE_ORDER:
        return PRICE_ORDER.index(price_num)
    return len(PRICE_ORDER)

def create_image(phone, price_raw, out_path):
    price_clean = format_price(price_raw)
    price_num = price_clean.split()[0]
    
    bg_name = f'{price_num}.jpg'
    
    if not os.path.exists(bg_name):
        print(f"⚠️ ئاگاداری: وێنەی {bg_name} نەدۆزرایەوە! وێنەی background.jpg بەکاردێت.")
        bg_name = 'background.jpg'
        
    img = Image.open(bg_name).copy()
    draw = ImageDraw.Draw(img)
    
    box = BOXES.get(price_num, BOXES['default'])
    cx1 = (box[0] + box[2]) // 2
    cy1 = (box[1] + box[3]) // 2
    
    draw_centered(draw, str(phone), 'NRT-Bd.ttf', cx1, cy1,
        box[2] - box[0] - 100, box[3] - box[1] - 60, '#CC0000', 600)
        
    img.resize((1080,1080), Image.LANCZOS).save(out_path, 'JPEG', quality=92)

async def main():
    creds_json = json.loads(GOOGLE_CREDS)
    creds = Credentials.from_service_account_info(creds_json,
        scopes=['https://www.googleapis.com/auth/spreadsheets.readonly',
                'https://www.googleapis.com/auth/drive.readonly'])
    gc = gspread.authorize(creds)
    sheet = gc.open_by_key(SHEET_ID).sheet1
    data = sheet.get_all_values()

    # خوێندنەوەی سەرەتایی داتاکان
    raw_rows = [(r[0].strip(), r[1].strip()) for r in data
            if r[0].strip() and r[1].strip() and r[0].strip() != 'نۆرمال']

    # 🔀 لێرەدا کۆدەکە خۆی داتاکان بەپێی ویستی تۆ لە ١٥ تا ١٠٠ ڕێکدەخاتەوە پێش پۆستکردن
    rows = sorted(raw_rows, key=get_sort_key)

    last = get_last_row()
    if last >= len(rows):
        last = 0

    phone, price = rows[last]
    out = 'post.jpg'
    create_image(phone, price, out)

    keyboard = [
        [
            InlineKeyboardButton("بۆ کڕین نامە بنێرە 🛒", url="https://t.me/zanamobil")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    caption_text = f"📱 مۆبایل: \u200E{phone}\u200E\n💰 نرخ: {format_price(price)}\n\nبۆ کڕین پەیوەندیمان پێوە بکەن 👇"

    async with Bot(token=TELEGRAM_TOKEN) as bot:
        with open(out, 'rb') as f:
            result = await bot.send_photo(
                chat_id=CHANNEL_ID, 
                photo=f,
                caption=caption_text,
                reply_markup=reply_markup
            )
            print(f'پۆست کرا: {result.message_id}')

    set_last_row(last + 1)
    print(f'✅ {phone} | پۆست {last+1} لە {len(rows)} (بەپێی ڕێزبەندی نرخ)')

asyncio.run(main())
