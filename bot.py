import os
import time
import telebot
from PIL import Image, ImageDraw, ImageFont

# ─── 🔑 زانیارییەکانی بۆت و چەناڵەکەت ──────────────────────────────────
BOT_TOKEN = "لێرە_تۆکنی_بۆتەکەت_دابنێ"
CHANNEL_ID = "لێرە_ئایدی_چەناڵەکەت_دابنێ"  # بۆ نموونە: -100xxxxxxxxx یان "@mychannel"

bot = telebot.TeleBot(BOT_TOKEN)

# ─── 📊 ڕێکخستنی وردی بۆکسەکان و ڕەنگەکان (١٥ تا ١٠٠ هەزار) ──────────────
CONFIGS = {
    # جۆری ١: بۆکسی خۆڵەمێشی تاریک (١٥ و ٢٥)
    '15': {'box': (100, 190, 980, 330), 'text_color': '#FFFFFF'},
    '25': {'box': (100, 190, 980, 330), 'text_color': '#FFFFFF'},
    
    # جۆری ٢: بۆکسی سپی (٢٠ و ٣٠)
    '20': {'box': (100, 190, 980, 330), 'text_color': '#A30000'}, # نووسینی سوور
    '30': {'box': (100, 190, 980, 330), 'text_color': '#000000'}, # نووسینی ڕەش

    # جۆری ٣: قاڵبی VIP (٣٥ و ٤٥)
    '35': {'box': (105, 121, 975, 273), 'text_color': '#FFFFFF'},
    '45': {'box': (105, 121, 975, 273), 'text_color': '#FFFFFF'},

    # جۆری ٤: قاڵبی مۆبایل و ئەڵقەی سوور (٤٠ تا ١٠٠)
    '40':  {'box': (54, 290, 1026, 430), 'text_color': '#FFFFFF'}, # پلاتفۆرمی زێڕین
    '55':  {'box': (54, 290, 1026, 430), 'text_color': '#FFFFFF'}, # پلاتفۆرمی زێڕین
    '60':  {'box': (54, 290, 1026, 430), 'text_color': '#000000'},
    '65':  {'box': (54, 290, 1026, 430), 'text_color': '#000000'},
    '70':  {'box': (54, 290, 1026, 430), 'text_color': '#000000'},
    '80':  {'box': (54, 290, 1026, 430), 'text_color': '#000000'},
    '85':  {'box': (54, 290, 1026, 430), 'text_color': '#000000'},
    '100': {'box': (54, 290, 1026, 430), 'text_color': '#000000'},

    'default': {'box': (100, 190, 980, 330), 'text_color': '#000000'}
}

# ─── 🖼️ فانکشنی دروستکردنی وێنە بە شێوازی سەنتەر ───────────────────────────
def generate_image(phone_number, price_key, output_path):
    template_path = f"{price_key}.jpg"
    font_path = "NRT-Bd.ttf" # ناوی فۆنتەکەت ڕێک وەک ناوەکەی ناو گیتهەب

    if not os.path.exists(template_path):
        return False

    img = Image.open(template_path).convert("RGB")
    draw = ImageDraw.Draw(img)

    config = CONFIGS.get(str(price_key), CONFIGS['default'])
    box = config['box']
    text_color = config['text_color']

    try:
        font = ImageFont.truetype(font_path, 65)
    except IOError:
        font = ImageFont.load_default()

    # حیسابکردنی ناوەڕاستی بۆکسەکە بە وردی
    bbox = draw.textbbox((0, 0), phone_number, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]

    box_w = box[2] - box[0]
    box_h = box[3] - box[1]

    x = box[0] + (box_w - text_w) / 2
    y = box[1] + (box_h - text_h) / 2 - bbox[1]

    draw.text((x, y), phone_number, fill=text_color, font=font)
    img.save(output_path, "JPEG", quality=95)
    return True

# ─── 🤖 بەشی فەرمانەکانی بۆتەکە (Bot Commands) ───────────────────────────

# ١. فەرمانی دەستپێکردن
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "👋 بەخێربێیت!\n\n🔹 بۆ تاقیکردنەوە و پۆستکردنی گشت قالبەکان (١٥ تا ١٠٠ هەزار) بنووسە: `/postall`")

# ٢. فەرمانی پۆستکردنی گشتی بۆ تاقیکردنەوە (قالبەکان لە ١٥ تا ١٠٠ هەزار)
@bot.message_handler(commands=['postall'])
def post_all_templates(message):
    bot.reply_to(message, "⏳ دەستکرا بە دروستکردن و پۆستکردنی گشت قالبەکان بۆ چەناڵەکەت...")
    
    test_number = "0770 123 45 67" # ژمارەی تاقیکاری
    
    for price in CONFIGS.keys():
        if price == 'default':
            continue
            
        temp_file = f"final_{price}.jpg"
        
        # دروستکردنی وێنەکە
        if generate_image(test_number, price, temp_file):
            try:
                # ناردنی بۆ چەناڵەکەت
                with open(temp_file, 'rb') as photo:
                    bot.send_photo(
                        chat_id=CHANNEL_ID,
                        photo=photo,
                        caption=f"📊 پۆستی گشتی ئۆتۆماتیکی | نرخی: {price} هەزار"
                    )
                
                # سڕینەوەی فایلی کاتی
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                    
                time.sleep(1.5) # بۆ ئەوەی تێلێگرام بلۆکمان نەکات
            except Exception as e:
                print(f"Error sending {price}: {e}")
                
    bot.send_message(message.chat.id, "✨ پیرۆزە! گشت وێنەکان (١٥ تا ١٠٠ هەزار) بە سەرکەوتوویی پۆست کران لە چەناڵەکەت.")

# ─── 🚀 کارپێکردنی بۆتەکە ────────────────────────────────────────────────
if __name__ == "__main__":
    print("🤖 بۆتەکەت ئێستا چالاکە و چاوەڕوانی فەرمانەکانە...")
    bot.infinity_polling()
