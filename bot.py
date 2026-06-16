import asyncio, os, gspread, json, requests, re
from PIL import Image, ImageDraw, ImageFont
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from google.oauth2.service_account import Credentials

TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN', '')
GOOGLE_CREDS = os.environ.get('GOOGLE_CREDS', '')
PAT_TOKEN = os.environ.get('PAT_TOKEN', '')
REPO = os.environ.get('GITHUB_REPOSITORY', '')

# چەناڵی تێست
CHANNEL_ID = '@zanatest123'
SHEET_ID = '1RkGwtLZfZ_DaScAnFH9zKdDuAtO90NjZLCxTRBSdJNU'

# 📊 ڕێکخستنی گشت قاڵب، بۆکس و ڕەنگەکان (١٥ تا ١٠٠ هەزار) بەپێی وێنەکانت
CONFIGS = {
    '15': {'box': (100, 190, 980, 330), 'base': '#FFFFFF', 'special': '#FFFFFF'},
    '20': {'box': (100, 190, 980, 330), 'base': '#A30000', 'special': '#A30000'},
    '25': {'box': (100, 190, 980, 330), 'base': '#FFFFFF', 'special': '#FFFFFF'},
    '30': {'box': (100, 190, 980, 330), 'base': '#000000', 'special': '#000000'},
    '35': {'box': (105, 121, 975, 273), 'base': '#FFFFFF', 'special': '#FFFFFF'},
    '40': {'box': (54, 290, 1026, 430), 'base': '#FFFFFF', 'special': '#FFFFFF'},
    '45': {'box': (105, 121, 975, 273), 'base': '#FFFFFF', 'special': '#FFFFFF'},
    '55': {'box': (54, 290, 1026, 430), 'base': '#FFFFFF', 'special': '#FFFFFF'},
    # قالبەکانی کەپسولی سپی (٦٠ تا ١٠٠) کە ڕەنگی تێکەڵاو (سوور و ڕەش) وەردەگرن
    '60': {'box': (105, 150, 965, 285), 'base': '#E60000', 'special': '#000000'},
    '65': {'box': (105, 150, 965, 285), 'base': '#E60000', 'special': '#000000'},
    '70': {'box': (105, 150, 965, 285), 'base': '#E60000', 'special': '#000000'},
    '80': {'box': (105, 150, 965, 285), 'base': '#E60000', 'special': '#000000'},
    '85': {'box': (105, 150, 965, 285), 'base': '#E60000', 'special': '#000000'},
    '100': {'box': (105, 150, 965, 285), 'base': '#E60000', 'special': '#000000'},
    'default': {'box': (100, 190, 980, 330), 'base': '#000000', 'special': '#000000'}
}

# گشتاندنی تەواوی نرخەکان لە ١٥ تا ١٠٠ هەزار بۆ پۆستکردن پێکەوە
PRICE_ORDER = ['15', '20', '25', '30', '35', '40', '45', '55', '60', '65', '70', '80', '85', '100']

def draw_centered_mixed(draw, text, font_path, cx, cy, max_w, max_h, base_color, special_color, start=135):
    digit_count = 0
    split_idx = len(text)
    for i in range(len(text) - 1, -1, -1):
        if text[i].isdigit():
            digit_count += 1
        if digit_count == 4:
            split_idx = i
            break
            
    part1 = text[:split_idx]
    part2 = text[split_idx:]

    for size in range(start, 20, -2):
        font = ImageFont.truetype(font_path, size)
        bbox = draw.textbbox((0,0), text, font=font)
        tw, th = bbox[2]-bbox[0], bbox[3]-bbox[1]
        if tw <= max_w and th <= max_h:
            x = cx - (bbox[0]+bbox[2])//2
            y = cy - (bbox[1]+bbox[3])//2
            
            draw.text((x, y), part1, font=font, fill=base_color)
            w1 = draw.textlength(part1, font=font)
            draw.text((x + w1, y), part2, font=font, fill=special_color)
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

def create_image(phone, price_raw, out_path):
    price_clean = format_price(price_raw)
    words = price_clean.split()
    price_num = words[0] if words else 'default'
    
    bg_name = f'{price_num}.jpg'
    if not os.path.exists(bg_name):
        bg_name = 'background.jpg'
        
    img = Image.open(bg_name).copy()
    if img.size != (1080, 1080):
        img = img.resize((1080, 1080), Image.LANCZOS)
        
    draw = ImageDraw.Draw(img)
    
    # بەدەستهێنانی ڕێکخستنی تایبەت بە هەر نرخێک بە شێوەی ئۆتۆماتیکی
    cfg = CONFIGS.get(price_num, CONFIGS['default'])
    box = cfg['box']
    base_color = cfg['base']
    special_color = cfg['special']
    
    cx1 = (box[0] + box[2]) // 2
    cy1 = (box[1] + box[3]) // 2
    
    draw_centered_mixed(draw, str(phone), 'NRT-Bd.ttf', cx1, cy1,
        box[2] - box[0] - 40, box[3] - box[1] - 5, base_color, special_color, start=135)
        
    img.save(out_path, 'JPEG', quality=95)

async def main():
    if not TELEGRAM_TOKEN or not GOOGLE_CREDS:
        print("❌ کێشە لە ڕێکخستنی سکرێتەکان هەیە!")
        return

    try:
        creds_json = json.loads(GOOGLE_CREDS)
        creds = Credentials.from_service_account_info(creds_json,
            scopes=['https://www.googleapis.com/auth/spreadsheets.readonly',
                    'https://www.googleapis.com/auth/drive.readonly'])
        gc = gspread.authorize(creds)
        sheet = gc.open_by_key(SHEET_ID).sheet1
        data = sheet.get_all_values()
        print(f"📊 داتا خوێندرایەوە. ژمارەی ڕیزەکان: {len(data)}")
    except Exception as e:
        print(f"❌ کێشە لە گوگل شێت: {e}")
        return

    raw_rows = []
    for r in data:
        if len(r) >= 2:
            p1 = str(r[0]).strip()
            p2 = str(r[1]).strip()
            if p1 and p2 and p1 != 'نۆرمال' and p1 != 'مۆبایل' and p2 != 'نرخ':
                raw_rows.append((p1, p2))

    samples = {}
    for phone, price in raw_rows:
        price_clean = format_price(price)
        words = price_clean.split()
        price_num = words[0] if words else 'default'
        if price_num in PRICE_ORDER and price_num not in samples:
            samples[price_num] = (phone, price)

    # 🔄 پۆستکردنی ڕاستەوخۆی داتاکانی ناو شێتەکە لە ١٥ تا ١٠٠ هەزار
    async with Bot(token=TELEGRAM_TOKEN) as bot:
        for price_num in PRICE_ORDER:
            if price_num in samples:
                phone, price = samples[price_num]
                out = f'test_{price_num}.jpg'
                
                try:
                    create_image(phone, price, out)
                    keyboard = [[InlineKeyboardButton("بۆ کڕین نامە بنێرە 🛒", url="https://t.me/zanamobil")]]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    caption_text = f"📱 مۆبایل: \u200E{phone}\u200E\n💰 نرخ: {format_price(price)}"
                    
                    await bot.send_photo(
                        chat_id=CHANNEL_ID, 
                        photo=open(out, 'rb'),
                        caption=caption_text,
                        reply_markup=reply_markup
                    )
                    print(f'✅ وێنەی {price_num} هەزار بە سەرکەوتوویی ناردرا.')
                    
                    if os.path.exists(out):
                        os.remove(out)
                        
                    await asyncio.sleep(2) # بۆ ئەوەی تێلێگرام بلۆکمان نەکات
                    
                except Exception as e:
                    print(f"❌ کێشە لە پۆستی {price_num} هەزار: {e}")

if __name__ == '__main__':
    asyncio.run(main())
