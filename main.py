import asyncio

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

import os
import re
import json
import time
import requests
from bs4 import BeautifulSoup
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from shazamio import Shazam

API_ID = 38154579
API_HASH = "48ac2ee1584e889e0c696d158db6d2c5"
BOT_TOKEN = "8961190627:AAGIwtujqYTf2Kt6iPXxGIN3uF7_jKA7d7Y"

app = Client(
    "universal_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    drop_pending_updates=True
)

BOT_SIGNATURE = "@fazaHASASHIbot"

user_mode = {}
yt_cache = {}
media_file_cache = {}
search_results_cache = {}

shazam = Shazam()

MAIN_MENU = InlineKeyboardMarkup([
    [
        InlineKeyboardButton("🎬 Social Downloader", callback_data="menu_downloader"),
        InlineKeyboardButton("🍿 Kino Izlash", callback_data="menu_kino")
    ],
    [
        InlineKeyboardButton("🧠 AI Yordamchi", callback_data="menu_ai"),
        InlineKeyboardButton("ℹ️ Bot Haqida", callback_data="menu_about")
    ]
])

BACK_BUTTON = InlineKeyboardMarkup([
    [InlineKeyboardButton("⬅️ Bosh menyuga qaytish", callback_data="main_menu")]
])

def get_post_download_buttons(user_id):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🎵 Musiqasini topish", callback_data=f"findmusic_{user_id}")
        ],
        [
            InlineKeyboardButton("🎬 Yana video yuklash", callback_data="menu_downloader"),
            InlineKeyboardButton("🏠 Bosh menyu", callback_data="main_menu")
        ]
    ])

async def safe_delete_message(msg):
    try:
        await msg.delete()
    except Exception:
        pass

async def recognize_audio_shazam(video_path):
    audio_sample = f"{video_path}_sample.mp3"
    try:
        cmd = f'ffmpeg -y -i "{video_path}" -vn -ar 44100 -ac 2 -t 7 -f mp3 "{audio_sample}"'
        proc = await asyncio.create_subprocess_shell(cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        await proc.communicate()

        if not os.path.exists(audio_sample) or os.path.getsize(audio_sample) == 0:
            return None, []

        out = await shazam.recognize(audio_sample)

        if os.path.exists(audio_sample):
            os.remove(audio_sample)

        track = out.get('track', {})
        song_title = track.get('title')
        artist = track.get('subtitle')

        full_song = f"{artist} - {song_title}" if artist and song_title else song_title

        if not full_song:
            return None, []

        search_cmd = f'yt-dlp "ytsearch5:{full_song}" --dump-json --flat-playlist'
        sproc = await asyncio.create_subprocess_shell(search_cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        sout, _ = await sproc.communicate()

        results = []
        for line in sout.decode().split('\n'):
            if line.strip():
                try:
                    item = json.loads(line)
                    dur_sec = item.get('duration', 0) or 0
                    mins, secs = divmod(int(dur_sec), 60)
                    results.append({
                        "id": item.get('id'),
                        "title": item.get('title'),
                        "url": f"https://www.youtube.com/watch?v={item.get('id')}",
                        "duration": f"{mins}:{secs:02d}"
                    })
                except Exception:
                    pass

        return full_song, results[:5]
    except Exception as e:
        print("Shazam Error:", e)
        if os.path.exists(audio_sample):
            os.remove(audio_sample)
        return None, []

@app.on_message(filters.command("start") & filters.private)
async def start_cmd(client, message):
    user_id = message.chat.id
    user_mode[user_id] = "default"
    await message.reply_text(
        f"Assalomu alaykum, **{message.from_user.first_name}**!\n\n"
        f"🤖 **Universal Yordamchi Bot**ga xush kelibsiz.\n"
        f"Kerakli bo'limni tanlang:",
        reply_markup=MAIN_MENU
    )

@app.on_callback_query()
async def callback_handler(client, callback_query):
    data = callback_query.data
    user_id = callback_query.message.chat.id

    try:
        await callback_query.answer()
    except Exception:
        pass

    if data == "main_menu":
        user_mode[user_id] = "default"
        try:
            await callback_query.message.edit_text("🤖 **Bosh menyu:**\nKerakli bo'limni tanlang:", reply_markup=MAIN_MENU)
        except Exception:
            pass

    elif data == "menu_downloader":
        user_mode[user_id] = "downloader"
        try:
            await callback_query.message.edit_text(
                "🎬 **Social Media Downloader Bo'limi**\n\n"
                "Menga **Instagram, TikTok, YouTube yoki Pinterest** linkini yuboring!",
                reply_markup=BACK_BUTTON
            )
        except Exception:
            pass

    elif data == "menu_kino":
        try:
            await callback_query.message.edit_text("🍿 **Kino Izlash Bo'limi**\n\n*(Tez orada ishga tushadi)*", reply_markup=BACK_BUTTON)
        except Exception:
            pass

    elif data == "menu_ai":
        user_mode[user_id] = "ai"
        try:
            await callback_query.message.edit_text("🧠 **AI Yordamchi Bo'limi Yoniq!**\n\nMenga savolingizni yozing:", reply_markup=BACK_BUTTON)
        except Exception:
            pass

    elif data == "menu_about":
        about_text = f"ℹ️ **Bot Haqida**\n\nSocial downloader, Shazam va AI bot.\n🤖 {BOT_SIGNATURE}"
        try:
            await callback_query.message.edit_text(about_text, reply_markup=BACK_BUTTON)
        except Exception:
            pass

    elif data.startswith("findmusic_"):
        video_path = media_file_cache.get(user_id)
        if not video_path or not os.path.exists(video_path):
            await callback_query.answer("❌ Video topilmadi, iltimos linkni qayta yuboring!", show_alert=True)
            return

        hourglass_msg = await client.send_message(user_id, "⏳ **Shazam orqali musiqa qidirilmoqda...**")

        song_name, results = await recognize_audio_shazam(video_path)
        search_results_cache[user_id] = results

        await safe_delete_message(hourglass_msg)

        if song_name and results:
            music_text = f"🎵 **{song_name}**\n\n"
            num_buttons = []
            for idx, res in enumerate(results, 1):
                music_text += f"**{idx}.** {res['title']} **({res['duration']})**\n"
                num_buttons.append(InlineKeyboardButton(str(idx), callback_data=f"dlmusic_{idx-1}"))

            row_buttons = [num_buttons[i:i+5] for i in range(0, len(num_buttons), 5)]
            row_buttons.insert(0, [InlineKeyboardButton("📁 Video yuklash", callback_data="menu_downloader")])

            await client.send_message(user_id, music_text, reply_markup=InlineKeyboardMarkup(row_buttons))
        else:
            await client.send_message(user_id, "❌ Videodagi qo'shiqni Shazam topa olmadi.")

    elif data.startswith("dlmusic_"):
        idx = int(data.split("_")[1])
        user_results = search_results_cache.get(user_id, [])

        if not user_results or idx >= len(user_results):
            await callback_query.answer("❌ Musiqa topilmadi!", show_alert=True)
            return

        selected = user_results[idx]
        status = await client.send_message(user_id, f"⚡ **{selected['title']}** yuklanmoqda...")

        out_mp3 = f"music_{user_id}_{int(time.time())}.mp3"
        cmd = f'yt-dlp -x --audio-format mp3 -o "{out_mp3}" "{selected["url"]}"'
        
        process = await asyncio.create_subprocess_shell(cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        await process.communicate()

        if os.path.exists(out_mp3):
            await status.edit_text("📤 **Audio yuborilmoqda...**")
            await client.send_audio(
                chat_id=user_id,
                audio=out_mp3,
                caption=f"🎵 **{selected['title']}**\n🤖 {BOT_SIGNATURE}"
            )
            os.remove(out_mp3)
            await safe_delete_message(status)
        else:
            await status.edit_text("❌ Musiqani yuklab bo'lmadi.")

@app.on_message(filters.private & filters.text & ~filters.command(["start", "stop"]))
async def handle_user_messages(client, message):
    user_id = message.chat.id
    text = message.text

    is_social = re.search(r"(instagram\.com|tiktok\.com|vt\.tiktok\.com|pinterest\.com|pin\.it|youtube\.com|youtu\.be)", text)

    if is_social:
        hourglass_msg = await message.reply_text("⏳ **Media yuklanmoqda...**")

        file_name = f"video_{user_id}_{int(time.time())}.mp4"

        cmd = f'yt-dlp --referer "https://www.tiktok.com/" --user-agent "Mozilla/5.0" -o "{file_name}" "{text}"'
        process = await asyncio.create_subprocess_shell(cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        await process.communicate()

        await safe_delete_message(hourglass_msg)

        if os.path.exists(file_name) and os.path.getsize(file_name) > 0:
            media_file_cache[user_id] = file_name
            status = await client.send_message(user_id, "📤 **Video yuborilmoqda...**")
            
            await client.send_video(
                chat_id=user_id,
                video=file_name,
                caption=f"✅ **Video yuklab olindi!**\n🤖 {BOT_SIGNATURE}",
                reply_markup=get_post_download_buttons(user_id)
            )
            await safe_delete_message(status)
        else:
            await message.reply_text("❌ Videoni yuklab bo'lmadi. Havolani qayta tekshiring.")

if __name__ == "__main__":
    print("🚀 Bot ishga tushdi!")
    app.run()
