import asyncio, os, gspread
from PIL import Image, ImageDraw, ImageFont
from telegram import Bot
from google.oauth2.service_account import Credentials
import json

TELEGRAM_TOKEN = os.environ['8621239974:AAGJNDusfecacpoy_6O0tTtExOgw44cc7vk']
CHANNEL_ID = '@zanamobile1'
SHEET_ID = '1RkGwtLZfZ_DaScAnFH9zKdDuAtO90NjZLCxTRBSdJNU'

TOP_BOX = (247, 467, 3205, 1109)
BOT_BOX = (1285, 2740, 2161, 3080)

def format_price(raw):
    s = str(raw).strip().replace(',','').replace('،','').replace(' ','')
    s = s.replace('هەزار','').replace('هزار','')
    try:
        n = float(s)
        if n < 1000: n *= 1000
        return f'{int(n // 1000)} هەزار'
    except: return str(raw)

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

def create_image(phone, price_raw, out_path):
    img = Image.open('background.jpg').copy()
    draw = ImageDraw.Draw(img)
    price = format_price(price_raw)
    cx1=(TOP_BOX[0]+TOP_BOX[2])//2; cy1=(TOP_BOX[1]+TOP_BOX[3])//2
    draw_centered(draw, str(phone), 'NRT-Bd.ttf', cx1, cy1,
        TOP_BOX[2]-TOP_BOX[0]-100, TOP_BOX[3]-TOP_BOX[1]-60, '#CC0000', 600)
    cx2=(BOT_BOX[0]+BOT_BOX[2])//2; cy2=(BOT_BOX[1]+BOT_BOX[3])//2
    draw_centered(draw, price, 'NRT-Bd.ttf', cx2, cy2,
        BOT_BOX[2]-BOT_BOX[0]-60, BOT_BOX[3]-BOT_BOX[1]-40, '#CC0000', 350)
    img.resize((1080,1080), Image.LANCZOS).save(out_path, 'JPEG', quality=92)
    return price

async def main():
    # گۆگل شەیت
    creds_json = json.loads(os.environ['GOOGLE_CREDS'])
    creds = Credentials.from_service_account_info(creds_json,
        scopes=['https://www.googleapis.com/auth/spreadsheets.readonly'])
    gc = gspread.authorize(creds)
    sheet = gc.open_by_key(SHEET_ID).sheet1
    data = sheet.get_all_values()

    # ژمارەی پۆستی ئەمڕۆ لە environment
    post_num = int(os.environ.get('POST_NUM', '1'))
    
    bot = Bot(token=TELEGRAM_TOKEN)
    count = 0
    for row in data:
        phone = row[0].strip()
        price = row[1].strip()
        if phone and price and phone != 'نۆرمال':
            count += 1
            if count == post_num:
                out = f'post_{post_num}.jpg'
                fmt = create_image(phone, price, out)
                with open(out, 'rb') as f:
                    await bot.send_photo(chat_id=CHANNEL_ID, photo=f)
                print(f'✅ پۆست {post_num}: {phone} | {fmt}')
                break

asyncio.run(main())
