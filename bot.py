async def main():
    if not TELEGRAM_TOKEN or not GOOGLE_CREDS:
        return

    try:
        creds_json = json.loads(GOOGLE_CREDS)
        creds = Credentials.from_service_account_info(creds_json,
            scopes=['https://www.googleapis.com/auth/spreadsheets', # پێویستە دەسەڵاتی نووسینیشی هەبێت
                    'https://www.googleapis.com/auth/drive'])
        gc = gspread.authorize(creds)
        sheet = gc.open_by_key(SHEET_ID).sheet1
        data = sheet.get_all_values()
    except Exception as e:
        print(f"Error: {e}")
        return

    async with Bot(token=TELEGRAM_TOKEN) as bot:
        # لێرە بە enumerate دەیخوێنینەوە بۆ ئەوەی ڕیزەکە بزانین
        for i, r in enumerate(data):
            if i == 0: continue # تێپەڕاندنی ناونیشانی ستونەکان (Header)
            if len(r) < 2: continue
            
            phone, price = str(r[0]).strip(), str(r[1]).strip()
            status = str(r[2]).strip() if len(r) > 2 else "" # خوێندنەوەی ستونی سێیەم

            # ئەگەر پۆست کرابوو، تێپەڕی بکە
            if status == "پۆستکراوە":
                continue
            
            if not phone or phone in ['مۆبایل', 'نۆرمال']: continue
            
            price_clean = format_price(price)
            price_num = price_clean.split()[0] if ' ' in price_clean else price_clean.replace('هەزار','')
            
            out = f'post_{phone.replace(" ", "_")}.jpg'
            create_image(phone, price_num, out)
            
            try:
                keyboard = [[InlineKeyboardButton("بۆ کڕین نامە بنێرە 🛒", url="https://t.me/zanamobil")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await bot.send_photo(chat_id=CHANNEL_ID, photo=open(out, 'rb'),
                                     caption=f"📱 مۆبایل: \u200E{phone}\u200E\n💰 نرخ: {price_clean}",
                                     reply_markup=reply_markup)
                
                # دوای پۆستکردن، ستونی سێیەم نوێ بکەرەوە بە "پۆستکراوە"
                sheet.update_cell(i + 1, 3, "پۆستکراوە")
                print(f"✅ ژمارەی {phone} پۆست کرا.")
                
                await asyncio.sleep(2)
            except Exception as e:
                print(f"❌ کێشە لە پۆستکردنی {phone}: {e}")
