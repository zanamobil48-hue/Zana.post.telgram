import asyncio, os, gspread, json, requests
from PIL import Image, ImageDraw, ImageFont
from telegram import Bot
from google.oauth2.service_account import Credentials

TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN', '')
GOOGLE_CREDS = os.environ.get('GOOGLE_CREDS', '')
PAT_TOKEN = os.environ.get('PAT_TOKEN', '')
REPO = os.environ.get('GITHUB_REPOSITORY', '')
CHANNEL_ID = '@zanamobile1'
SHEET_ID = '1RkGwtLZfZ_DaScAnFH9zKdDuAtO90NjZLCxTRBSdJNU'
TOP_BOX = (247, 467, 3205, 1109)
BOT_BOX = (1285, 2740, 2161, 3080)

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
    cx1=(TOP_BOX[0]+TOP_BOX[2])//2; cy1=(TOP_BOX[1]+TOP_BOX[3])//2
    draw_centered(draw, str(phone), 'NRT-Bd.ttf', cx1, cy1,
        TOP_BOX[2]-TOP_BOX[0]-100, TOP_BOX[3]-TOP_BOX[1]-60, '#CC0000', 600)
    img.resize((1080,1080), Image.LANCZOS).save(out_path, 'JPEG', quality=92)

async def main():
    creds_json = json.loads(GOOGLE_CREDS)
    creds = Credentials.from_service_account_info(creds_json,
        scopes=['https://www.googleapis.com/auth/spreadsheets.readonly',
                'https://www.googleapis.com/auth/drive.readonly'])
    gc = gspread.authorize(creds)
    sheet = gc.open_by_key(SHEET_ID).sheet1
    data = sheet.get_all_values()

    rows = [(r[0].strip(), r[1].strip()) for r in data
            if r[0].strip() and r[1].strip() and r[0].strip() != 'نۆرمال']

    last = get_last_row()
    if last >= len(rows):
        last = 0

    phone, price = rows[last]
    out = 'post.jpg'
    create_image(phone, price, out)

    bot = Bot(token=TELEGRAM_TOKEN, connect_timeout=30, read_timeout=30)
    with open(out, 'rb') as f:
        await bot.send_photo(chat_id=CHANNEL_ID, photo=f)

    set_last_row(last + 1)
    print(f'✅ {phone} | پۆست {last+1} لە {len(rows)}')

asyncio.run(main())
