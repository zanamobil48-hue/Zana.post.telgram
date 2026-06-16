import os
from PIL import Image, ImageDraw, ImageFont

# ─── ڕێکخستنی بۆکسەکان و ڕەنگەکان بەپێی قاڵبەکان ──────────────────────────
CONFIGS = {
    # جۆری ١: بۆکسی خۆڵەمێشی تاریک (١٥ و ٢٥)
    '15': {'box': (100, 180, 900, 310), 'text_color': '#FFFFFF'},
    '25': {'box': (100, 180, 900, 310), 'text_color': '#FFFFFF'},
    
    # جۆری ٢: بۆکسی سپی (٢٠ و ٣٠)
    '20': {'box': (100, 150, 910, 290), 'text_color': '#A30000'}, # نووسینی سوور
    '30': {'box': (100, 150, 910, 290), 'text_color': '#000000'}, # نووسینی ڕەش

    # جۆری ٣: قاڵبی VIP (٣٥ و ٤٥)
    '35': {'box': (180, 130, 840, 250), 'text_color': '#FFFFFF'},
    '45': {'box': (180, 130, 840, 250), 'text_color': '#FFFFFF'},

    # جۆری ٤: پلاتفۆرمی زێڕین (٤٠ و ٥٥)
    '40': {'box': (70, 300, 950, 420), 'text_color': '#FFFFFF'},
    '55': {'box': (70, 300, 950, 420), 'text_color': '#FFFFFF'},

    # جۆری ٥: قاڵبی مۆبایل و ئەڵقەی سوور (٦٠ تا ١٠٠)
    '60':  {'box': (110, 120, 910, 270), 'text_color': '#000000'},
    '65':  {'box': (110, 120, 910, 270), 'text_color': '#000000'},
    '70':  {'box': (110, 120, 910, 270), 'text_color': '#000000'},
    '80':  {'box': (110, 120, 910, 270), 'text_color': '#000000'},
    '85':  {'box': (110, 120, 910, 270), 'text_color': '#000000'},
    '100': {'box': (110, 120, 910, 270), 'text_color': '#000000'},

    # ئەگەر نرخێکی تر بوو کە لێرەدا نییە
    'default': {'box': (100, 150, 910, 290), 'text_color': '#000000'}
}

# ─── فانکشنی سەرەکی دروستکردنی وێنەکە ──────────────────────────────────
def generate_number_image(phone_number, price_key):
    """
    ئەم فانکشنە ڕاستەوخۆ فایلەکان لە تەنیشت خۆی دەخوێنێتەوە بەپێی مۆدێلی گیتهەبەکەت.
    """
    # ١. دیاریکردنی ناوی فایلی قاڵبەکە ڕاستەوخۆ لە چەقی پڕۆژەکە
    template_path = f"{price_key}.jpg"
    output_path = "output_result.jpg" # وێنە دروستبووەکە لێرە سەیڤ دەبێت
    font_path = "NRT-Bd.ttf" # ناوی فۆنتەکەت ڕێک وەک ناوەکەی ناو گیتهەب

    if not os.path.exists(template_path):
        print(f"❌ قاڵبی نرخی {price_key} نەدۆزرایەوە!")
        return None

    # ٢. کردنەوەی وێنە و ئامادەکردنی بۆ نووسین
    img = Image.open(template_path).convert("RGB")
    draw = ImageDraw.Draw(img)

    # ٣. هێنانی پێوانەی بۆکس و ڕەنگ بۆ ئەو نرخە
    config = CONFIGS.get(str(price_key), CONFIGS['default'])
    box = config['box']
    text_color = config['text_color']

    # ٤. بارکردنی فۆنتەکەت
    try:
        font = ImageFont.truetype(font_path, 65) # قەبەرەی فۆنتەکە 65ـە و گونجاوە
    except IOError:
        font = ImageFont.load_default()

    # ٥. حیسابکردنی ناوەڕاستی بۆکسەکە (Centering)
    bbox = draw.textbbox((0, 0), phone_number, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]

    box_w = box[2] - box[0]
    box_h = box[3] - box[1]

    x = box[0] + (box_w - text_w) / 2
    y = box[1] + (box_h - text_h) / 2 - bbox[1]

    # ٦. نووسینی ژمارەکە و پاشەکەوتکردنی
    draw.text((x, y), phone_number, fill=text_color, font=font)
    img.save(output_path, "JPEG", quality=95)
    
    return output_path


# ─── چۆنیەتی بەکارهێنان لەناو bot.py ──────────────────────────────────
# کاتێک بەکارهێنەر داوای ژمارەیەک دەکات، تەنها بەم شێوەیە بانگی بکە:
#
# image_to_send = generate_number_image("0770 501 52 52", "70")
# کاتێک وێنەکەت بۆ نارد، دەتوانیت لە ڕێگەی فایلی "output_result.jpg"ـەوە بینێریت.
