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

# 🌐 داتابەیسی گشتی قالبەکان - شوێنی بۆشاییەکان بە تەواوی جیاکرانەوە
CONFIGS = {
    # 🎯 قالبە سەرەتاییەکان (١٥ تا ٣٥) - گەڕانەوە بۆ سندوقی ڕەسەنی خۆیان بۆ ئەوەی نەکەونە دەرەوە
    '15':  {'box': (100, 190, 980, 330), 'base': '#FFFFFF', 'special': '#FFFFFF'},
    '20':  {'box': (100, 190, 980, 330), 'base': '#FFFFFF', 'special': '#FFFFFF'},
    '25':  {'box': (100, 190, 980, 330), 'base': '#FFFFFF', 'special': '#FFFFFF'},
    '30':  {'box': (100, 190, 980, 330), 'base': '#FFFFFF', 'special': '#FFFFFF'},
    '35':  {'box': (100, 190, 980, 330), 'base': '#FFFFFF', 'special': '#FFFFFF'},
    
    # 🎯 قالبەکانی ٤٠ تا ٥٠ (کە ووتت زۆر ڕێکە و دەستکاری نەکراوە)
    '40':  {'box': (54, 324, 1026, 464),  'base': '#FFFFFF', 'special': '#FFFFFF'},
    '45':  {'box': (54, 324, 1026, 464),  'base': '#FFFFFF', 'special': '#FFFFFF'},
    '50':  {'box': (54, 324, 1026, 464),  'base': '#FFFFFF', 'special': '#FFFFFF'},
    
    # 🎯 قالبەکانی ٥٥ تا ٦٥ (کەپسولی سەرەوە - ڕەش و سوور)
    '55':  {'box': (54, 315, 1026, 465),  'base': '#000000', 'special': '#E60000'},
    '60':  {'box': (105, 121, 975, 273), 'base': '#000000', 'special': '#E60000'},
    '65':  {'box': (105, 121, 975, 273), 'base': '#000000', 'special': '#E60000'},
    
    # 🎯 قالبە بەرزەکان ٧٠ تا ١٠٠ (کەپسولی سەرەوە - سوور و ڕەش)
    '70':  {'box': (105, 150, 965, 285), 'base': '#E60000', 'special': '#000000'},
    '75':  {'box': (105, 150, 965, 285), 'base': '#E60000', 'special': '#000000'},
    '80':  {'box': (105, 150, 965, 285), 'base': '#E60000', 'special': '#000000'},
    '85':  {'box': (105, 150, 965, 285), 'base': '#E60000', 'special': '#000000'},
    '90':  {'box': (105, 150, 965, 285), 'base': '#E60000', 'special': '#000000'},
    '95':  {'box': (105, 150, 965, 285), 'base': '#E60000', 'special': '#000000'},
    '100': {'box': (105, 150, 965, 285), 'base': '#E60000', 'special': '#000000'},
    
    'default': {'box': (100, 190, 980, 330), 'base': '#FFFFFF', 'special': '#FFFFFF'}
}

ALL_TEST_PRICES = ['15', '20', '25', '30', '35', '40', '45', '50', '55', '60', '65', '70', '75', '80', '85', '90', '95', '100']

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

def create_image(phone, price_num, out_path):
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
    if not TELEGRAM_TOKEN:
        print("❌ کێشە لە TELEGRAM_TOKEN هەیە!")
        return

    print("🚀 دەستپێکردنی تاقیکردنەوەی نوێ بە پێوانەی جیاواز بۆ ١٥ تا ٣٥...")

    async with Bot(token=TELEGRAM_TOKEN) as bot:
        for price_num in ALL_TEST_PRICES:
            phone_test = f"0750 {price_num}0 1234"
            out = f'test_all_{price_num}.jpg'
            
            try:
                create_image(phone_test, price_num, out)
                keyboard = [[InlineKeyboardButton("بۆ کڕین نامە بنێرە 🛒", url="https://t.me/zanamobil")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                caption_text = f"🧪 [تاقیکردنەوەی کۆتایی]\n📱 مۆبایل: \u200E{phone_test}\u200E\n💰 قالب: {price_num} هەزار"
                
                await bot.send_photo(
                    chat_id=CHANNEL_ID, 
                    photo=open(out, 'rb'),
                    caption=caption_text,
                    reply_markup=reply_markup
                )
                print(f'✅ قالبی {price_num} هەزار ڕێکخرایەوە و ناردرا.')
                await asyncio.sleep(2)
                
            except Exception as e:
                print(f"❌ کێشە لە قالبی {price_num}: {e}")

if __name__ == '__main__':
    asyncio.run(main())
