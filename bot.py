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

# 📍 لێرەدا پۆزیشنی ٣٥ بە تەواوی ڕێکخراوە بۆ ناو کەپسولە سوورەکەی سەرەوە
BOXES = {
    '15': (100, 190, 980, 330),
    '20': (100, 190, 980, 330),
    '25': (100, 190, 980, 330),
    '30': (100, 190, 980, 330),
    '35': (194, 151, 886, 259),  # 🎯 پێوانەی نوێ و ورد بۆ قالبی ٣٥ هەزار
    '40': (100, 295, 980, 435),
    '45': (100, 215, 980, 355),
    '50': (100, 295, 980, 435),
    '55': (100, 190, 980, 330),
    '60': (100, 240, 980, 380),
    '65': (100, 240, 980, 380),
    '70': (100, 240, 980, 380),
    '80': (100, 240, 980, 380),
    '85': (100, 240, 980, 380),
    '100': (100, 240, 980, 380),
    'default': (100, 190, 980, 330)
}

PRICE_ORDER = ['15', '20', '25', '30', '35', '40', '45', '50', '55', '60', '65', '70', '80', '85', '100']

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
    box = BOXES.get(price_num, BOXES['default'])
    cx1 = (box[0] + box[2]) // 2
    cy1 = (box[1] + box[3]) // 2
    
    # 🎨 ڕەنگەکان
    if price_num in ['15', '25', '35', '45']:
        base_color = '#FFFFFF'     
        special_color = '#FFEA00'  
    elif price_num in ['20', '30']:
        base_color = '#000000'     
        special_color = '#E60000'  
    elif price_num in ['40', '50']:
        base_color = '#FFFFFF'     
        special_color = '#FFFFFF'  
    elif price_num in ['55']:
        base_color = '#000000'     
        special_color = '#000000'  
    elif price_num in ['60', '65', '70', '80', '85', '100']:
        base_color = '#E60000'     
        special_color = '#000000'  
    else:
        base_color = '#000000'     
        special_color = '#E60000'
    
    draw_centered_mixed(draw, str(phone), 'NRT-Bd.ttf', cx1, cy1,
        box[2] - box[0] - 20, box[3] - box[1] - 5, base_color, special_color, start=135)
        
    img.save(out_path, 'JPEG', quality=95)

async def main():
    if not TELEGRAM_TOKEN or not GOOGLE_CREDS:
        print("❌ کێشە لە سکرێتەکان هەیە!")
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

    async with Bot(token=TELEGRAM_TOKEN) as bot:
        for price_num in PRICE_ORDER:
            if price_num in samples:
                phone, price = samples[price_num]
                out = f'test_{price_num}.jpg'
                
                try:
                    create_image(phone, price, out)
                    keyboard = [[InlineKeyboardButton("بۆ کڕین نامە بنێرە 🛒", url="https://t.me/zanamobil")]]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    caption_text = f"🧪 [تاقیکردنەوە]\n📱 مۆبایل: \u200E{phone}\u200E\n💰 نرخ: {format_price(price)}"
                    
                    await bot.send_photo(
                        chat_id=CHANNEL_ID, 
                        photo=open(out, 'rb'),
                        caption=caption_text,
                        reply_markup=reply_markup
                    )
                    print(f'✅ وێنەی نرخی {price_num} هەزار ناردرا.')
                    await asyncio.sleep(3)
                    
                except Exception as e:
                    print(f"❌ کێشە لە نرخی {price_num}: {e}")

if __name__ == '__main__':
    asyncio.run(main())
