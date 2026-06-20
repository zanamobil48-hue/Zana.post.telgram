import asyncio, os, gspread, json, requests, re, sys, random
from datetime import datetime, timezone, timedelta
from PIL import Image, ImageDraw, ImageFont
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from google.oauth2.service_account import Credentials

TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN', '')
GOOGLE_CREDS = os.environ.get('GOOGLE_CREDS', '')
PAT_TOKEN = os.environ.get('PAT_TOKEN', '')
REPO = os.environ.get('GITHUB_REPOSITORY', '')

CHANNEL_ID = '@zanamobile1'
SHEET_ID = '1RkGwtLZfZ_DaScAnFH9zKdDuAtO90NjZLCxTRBSdJNU'

CONFIGS = {
    '15': {'box': (100, 190, 980, 330), 'base': '#FFFFFF', 'special': '#FFFFFF'},
    '20': {'box': (100, 190, 980, 330), 'base': '#A30000', 'special': '#A30000'},
    '25': {'box': (100, 190, 980, 330), 'base': '#FFFFFF', 'special': '#FFFFFF'},
    '30': {'box': (100, 190, 980, 330), 'base': '#000000', 'special': '#000000'},
    '35': {'box': (140, 145, 940, 230), 'base': '#FFFFFF', 'special': '#FFFFFF'},
    '45': {'box': (140, 145, 940, 230), 'base': '#FFFFFF', 'special': '#FFFFFF'},
    
    '40': {'box': (50, 315, 1030, 460), 'base': '#FFFFFF', 'special': '#FFFFFF'},
    '50': {'box': (50, 315, 1030, 460), 'base': '#FFFFFF', 'special': '#FFFFFF'},
    '55': {'box': (50, 315, 1030, 460), 'base': '#E60000', 'special': '#000000'},
    
    '60': {'box': (105, 125, 975, 270), 'base': '#E60000', 'special': '#000000'},
    '65': {'box': (105, 125, 975, 270), 'base': '#E60000', 'special': '#000000'},
    
    '70': {'box': (105, 140, 975, 285), 'base': '#E60000', 'special': '#000000'},
    '80': {'box': (105, 140, 975, 285), 'base': '#E60000', 'special': '#000000'},
    '85': {'box': (105, 140, 975, 285), 'base': '#E60000', 'special': '#000000'},
    '100': {'box': (105, 140, 975, 285), 'base': '#E60000', 'special': '#000000'},
    
    'default': {'box': (100, 190, 980, 330), 'base': '#000000', 'special': '#000000'}
}

PRICE_ORDER = ['15', '20', '25', '30', '35', '40', '45', '50', '55', '60', '65', '70', '80', '85', '100']
POST_HOURS = [15, 16, 17, 18, 19]

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
        raise ValueError("❌ کێشە لە سکرێتەکان هەیە!")

    tz_iraq = timezone(timedelta(hours=3))
    now = datetime.now(tz_iraq)
    current_hour = now.hour

    if current_hour not in POST_HOURS:
        print(f"⏳ ئێستا کاتژمێر {current_hour}:00ـە بە کاتی عێراق. کاتی پۆستکردن نییە.")
        return

    cycle_day = now.date().toordinal() % 3
    hour_index = POST_HOURS.index(current_hour)
    
    price_index = (cycle_day * 5) + hour_index
    price_to_post = PRICE_ORDER[price_index]

    print(f"⏰ کاتی پۆستکردنە! سوڕی ڕۆژی {cycle_day + 1}، کاتژمێر {current_hour}:00، پۆستی {price_to_post} هەزاری دەکرێت.")

    try:
        creds_json = json.loads(GOOGLE_CREDS)
        # مۆڵەتی دەستکاری کردنی شیتەکە دراوە بە بۆتەکە لێرەدا
        creds = Credentials.from_service_account_info(creds_json,
            scopes=['https://www.googleapis.com/auth/spreadsheets',
                    'https://www.googleapis.com/auth/drive'])
        gc = gspread.authorize(creds)
        sheet = gc.open_by_key(SHEET_ID).sheet1
        data = sheet.get_all_values()
        print("📊 داتا خوێندرایەوە.")
    except Exception as e:
        raise RuntimeError(f"❌ کێشە لە پەیوەندی گوگل شێت: {e}")

    all_matches = []
    
    for i, r in enumerate(data):
        row_num = i + 1  # ژمارەی ڕیزەکە لەناو شیتەکەدا
        
        # پشکنین بۆ ئەوەی بزانین ئایا نیشانەی ✅ ی هەیە یان نا (لە کۆڵۆمی سێیەم)
        status = str(r[2]).strip() if len(r) > 2 else ""
        if status == '✅':
            continue  # ئەگەر پۆست کرابوو پێشتر، باز دەدات بەسەریدا
            
        if len(r) >= 2:
            p1 = str(r[0]).strip()
            p2 = str(r[1]).strip()
            if p1 and p2 and p1 != 'نۆرمال' and p1 != 'مۆبایل' and p2 != 'نرخ':
                price_clean = format_price(p2)
                words = price_clean.split()
                price_num = words[0] if words else 'default'
                
                # تەنها ئەوانە هەڵدەگرێت کە مەرجەکانیان تێدایە و نیشانەی ✅ یان نییە
                if price_num == price_to_post:
                    all_matches.append((p1, p2, row_num))

    async with Bot(token=TELEGRAM_TOKEN) as bot:
        if all_matches:
            # یەکێک بە هەڕەمەکی لەو ژمارە نوێیانە هەڵدەبژێرێت
            phone, price, row_num = random.choice(all_matches)
            out = f'test_{price_to_post}.jpg'
            
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
                
                # لێرەدا نیشانەی ✅ لە ڕیزی سێیەمی گۆگڵ شیتەکە دەدات
                sheet.update_cell(row_num, 3, '✅')
                
                print(f'✅ وێنەی {price_to_post} هەزار ناردرا و نیشانە کرا (ژمارە: {phone}).')
                if os.path.exists(out):
                    os.remove(out)
            except Exception as e:
                print(f"❌ کێشە لە پۆستکردنی {price_to_post}: {e}")
        else:
            print(f"⚠️ هۆشداری: هیچ ژمارەیەکی نوێ بۆ {price_to_post} هەزاری نەماوە (هەمووی نیشانەی ✅ ی هەیە یان بوونی نییە).")

if __name__ == '__main__':
    asyncio.run(main())
