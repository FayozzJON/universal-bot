import asyncio

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

import os
import re
import json
import time
import requests
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from bs4 import BeautifulSoup
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from shazamio import Shazam
import g4f

API_ID = 38154579
API_HASH = "48ac2ee1584e889e0c696d158db6d2c5"
BOT_TOKEN = "8961190627:AAGIwtujqYTf2Kt6iPXxGIN3uF7_jKA7d7Y"

app = Client(
    "universal_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

BOT_SIGNATURE = "@fazaHASASHIbot"

user_mode = {}
yt_cache = {}
media_file_cache = {}
search_results_cache = {}
last_update = {}

shazam = Shazam()

# RapidAPI Kalitingiz
RAPID_KEY = "26dd2049a8msh710c3fd6a3de040p15d588jsnbfd3a48b3910"

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

ALL_QUALITIES = [144, 240, 360, 480, 720, 1080, 1440, 2160]

def download_instagram_multi_api(raw_url, user_id):
    """Instagram Cloud Block’ni aylanib o'tuvchi ko'p bosqichli API yuklagich"""
    clean_url = raw_url.split("?")[0].strip()
    file_path = f"insta_{user_id}_{int(time.time())}.mp4"

    # 1-USUL: RapidAPI - Instagram Downloader V2
    try:
        url = "https://instagram-downloader-v2.p.rapidapi.com/media"
        headers = {
            "x-rapidapi-key": RAPID_KEY,
            "x-rapidapi-host": "instagram-downloader-v2.p.rapidapi.com"
        }
        res = requests.get(url, headers=headers, params={"url": clean_url}, timeout=15)
        if res.status_code == 200:
            data = res.json()
            media_url = None
            if isinstance(data, dict):
                media_url = data.get("url") or data.get("media") or data.get("download_url")
                if not media_url and "data" in data:
                    media_url = data["data"].get("url") or data["data"].get("media")
            if media_url:
                v_res = requests.get(media_url, stream=True, timeout=25)
                with open(file_path, 'wb') as f:
                    for chunk in v_res.iter_content(chunk_size=1024*1024):
                        if chunk:
                            f.write(chunk)
                if os.path.exists(file_path) and os.path.getsize(file_path) > 5000:
                    return file_path
    except Exception as e:
        print("RapidAPI V2 Error:", e)

    # 2-USUL: Social Media Saver API
    try:
        url = "https://social-media-video-downloader.p.rapidapi.com/smvd/get/instagram"
        headers = {
            "x-rapidapi-key": RAPID_KEY,
            "x-rapidapi-host": "social-media-video-downloader.p.rapidapi.com"
        }
        res = requests.get(url, headers=headers, params={"url": clean_url}, timeout=15)
        if res.status_code == 200:
            data = res.json()
            links = data.get("links", [])
            if links:
                media_url = links[0].get("link")
                if media_url:
                    v_res = requests.get(media_url, stream=True, timeout=25)
                    with open(file_path, 'wb') as f:
                        for chunk in v_res.iter_content(chunk_size=1024*1024):
                            if chunk:
                                f.write(chunk)
                    if os.path.exists(file_path) and os.path.getsize(file_path) > 5000:
                        return file_path
    except Exception as e:
        print("RapidAPI SMVD Error:", e)

    # 3-USUL: SaveFrom Fast Engine
    try:
        sf_url = f"https://worker.sf-api.com/service-fast-download/get?url={clean_url}"
        sf_res = requests.get(sf_url, timeout=12)
        if sf_res.status_code == 200:
            sf_json = sf_res.json()
            if sf_json.get("url"):
                media_link = sf_json["url"][0]["url"]
                v_res = requests.get(media_link, stream=True, timeout=25)
                with open(file_path, 'wb') as f:
                    for chunk in v_res.iter_content(chunk_size=1024*1024):
                        if chunk:
                            f.write(chunk)
                if os.path.exists(file_path) and os.path.getsize(file_path) > 5000:
                    return file_path
    except Exception as e:
        print("SaveFrom Engine Error:", e)

    return None

def download_pinterest_media(url, user_id):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, allow_redirects=True, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')

        video_tag = soup.find('video')
        if video_tag and video_tag.get('src'):
            video_url = video_tag['src']
            if video_url.startswith('blob:'):
                video_url = soup.find('source')['src'] if soup.find('source') else None
            
            if video_url:
                v_res = requests.get(video_url, headers=headers, stream=True)
                file_path = f"pin_vid_{user_id}_{int(time.time())}.mp4"
                with open(file_path, 'wb') as f:
                    for chunk in v_res.iter_content(chunk_size=1024*1024):
                        if chunk:
                            f.write(chunk)
                return "video", file_path

        og_image = soup.find("meta", property="og:image")
        if og_image and og_image.get("content"):
            img_url = og_image["content"]
            i_res = requests.get(img_url, headers=headers)
            file_path = f"pin_img_{user_id}_{int(time.time())}.jpg"
            with open(file_path, 'wb') as f:
                f.write(i_res.content)
            return "photo", file_path
    except Exception as e:
        print("Pinterest DL Error:", e)
    return None, None

async def recognize_audio_shazam(video_path):
    try:
        audio_sample = f"{video_path}_sample.mp3"
        cmd = f'ffmpeg -y -i "{video_path}" -vn -ar 44100 -ac 2 -t 10 -f mp3 "{audio_sample}"'
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

        full_song = None
        if song_title and artist:
            full_song = f"{artist} - {song_title}"
        elif song_title:
            full_song = song_title

        if not full_song:
            return None, []

        search_cmd = f'yt-dlp "ytsearch5:{full_song}" --dump-json'
        sproc = await asyncio.create_subprocess_shell(search_cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        sout, _ = await sproc.communicate()

        results = []
        for line in sout.decode().split('\n'):
            if line.strip():
                try:
                    item = json.loads(line)
                    dur_sec = item.get('duration', 0)
                    mins, secs = divmod(dur_sec, 60)
                    results.append({
                        "id": item.get('id'),
                        "title": item.get('title'),
                        "url": item.get('webpage_url'),
                        "duration": f"{mins}:{secs:02d}"
                    })
                except:
                    pass

        return full_song, results[:5]
    except Exception as e:
        print("Shazam Recognize Error:", e)
        return None, []

async def progress_status(current, total, status_msg, action_text):
    now = time.time()
    chat_id = status_msg.chat.id

    if chat_id not in last_update or (now - last_update[chat_id]) >= 1.5 or current == total:
        last_update[chat_id] = now
        percentage = (current * 100) / total if total > 0 else 0
        mb_current = current / (1024 * 1024)
        mb_total = total / (1024 * 1024) if total > 0 else 0

        text = f"{action_text}\n📊 **Jarayon:** {percentage:.1f}%\n💾 **Hajmi:** {mb_current:.1f} MB / {mb_total:.1f} MB"

        try:
            await status_msg.edit_text(text)
        except Exception:
            pass

async def get_yt_info(url):
    cmd = f'yt-dlp --dump-json "{url}"'
    process = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, _ = await process.communicate()
    try:
        data = json.loads(stdout.decode())
        formats = data.get("formats", [])
        
        quality_sizes = {}
        for f in formats:
            h = f.get("height")
            filesize = f.get("filesize") or f.get("filesize_approx")
            if h and h in ALL_QUALITIES and filesize:
                mb = round(filesize / (1024 * 1024), 1)
                quality_sizes[h] = mb

        available_heights = set(quality_sizes.keys())
        if not available_heights:
            for f in formats:
                h = f.get("height")
                if h and h in ALL_QUALITIES:
                    available_heights.add(h)

        max_h = max(available_heights) if available_heights else 720
        final_qualities = [q for q in ALL_QUALITIES if q <= max_h]

        audio_size = 0
        for f in formats:
            if f.get("vcodec") == "none" and (f.get("filesize") or f.get("filesize_approx")):
                audio_size = round((f.get("filesize") or f.get("filesize_approx")) / (1024 * 1024), 1)
                break

        return {
            "title": data.get("title", "YouTube Video"),
            "thumbnail": data.get("thumbnail"),
            "qualities": final_qualities,
            "sizes": quality_sizes,
            "audio_size": audio_size
        }
    except Exception as e:
        print("YT Info Error:", e)
        return None

@app.on_message(filters.command("start") & filters.private)
async def start_cmd(client, message):
    user_id = message.chat.id
    user_mode[user_id] = "default"
    user_name = message.from_user.first_name
    await message.reply_text(
        f"Assalomu alaykum, **{user_name}**!\n\n"
        f"🤖 **Universal Yordamchi Bot**ga xush kelibsiz.\n"
        f"Kerakli bo'limni tanlash uchun quyidagi tugmalardan birini bosing:",
        reply_markup=MAIN_MENU
    )

@app.on_callback_query()
async def callback_handler(client, callback_query):
    data = callback_query.data
    user_id = callback_query.message.chat.id

    try:
        await callback_query.answer()
    except:
        pass

    if data == "main_menu":
        user_mode[user_id] = "default"
        try:
            await callback_query.message.edit_text("🤖 **Bosh menyu:**\nKerakli bo'limni tanlang:", reply_markup=MAIN_MENU)
        except:
            await callback_query.message.reply_text("🤖 **Bosh menyu:**\nKerakli bo'limni tanlang:", reply_markup=MAIN_MENU)

    elif data == "menu_downloader":
        user_mode[user_id] = "downloader"
        try:
            await callback_query.message.edit_text(
                "🎬 **Social Media Downloader Bo'limi**\n\n"
                "Menga **Instagram, TikTok, YouTube yoki Pinterest** linkini yuboring!",
                reply_markup=BACK_BUTTON
            )
        except:
            pass

    elif data == "menu_kino":
        user_mode[user_id] = "kino"
        try:
            await callback_query.message.edit_text("🍿 **Kino Izlash Bo'limi**\n\n*(Ushbu bo'lim tez orada ishga tushadi)*", reply_markup=BACK_BUTTON)
        except:
            pass

    elif data == "menu_ai":
        user_mode[user_id] = "ai"
        try:
            await callback_query.message.edit_text("🧠 **AI Yordamchi (ChatGPT) Bo'limi Yoniq!**\n\nMenga savolingizni yozing:", reply_markup=BACK_BUTTON)
        except:
            pass

    elif data == "menu_about":
        about_text = (
            "ℹ️ **Bot Haqida**\n\n"
            "Ushbu universal bot quyidagi imkoniyatlarni taqdim etadi:\n"
            "• 🎬 **Social Downloader** — YouTube, Instagram, TikTok va Pinterest'dan video/rasm yuklash hamda musiqasini topish.\n"
            "• 🍿 **Kino Izlash** — Tez kunda kinolar bazasi!\n"
            "• 🧠 **AI Yordamchi** — Sun'iy intellekt orqali savollaringizga javob olish.\n\n"
            f"Bot: {BOT_SIGNATURE}"
        )
        try:
            await callback_query.message.edit_text(about_text, reply_markup=BACK_BUTTON)
        except:
            pass

    elif data.startswith("findmusic_"):
        video_path = media_file_cache.get(user_id)
        if not video_path or not os.path.exists(video_path):
            await callback_query.answer("❌ Video topilmadi, havola qayta yuboring!", show_alert=True)
            return

        hourglass_msg = await client.send_message(user_id, "⏳ Shazam orqali musiqa tahlil qilinmoqda...")

        song_name, results = await recognize_audio_shazam(video_path)
        search_results_cache[user_id] = results

        if song_name and results:
            music_text = f"🎵 **{song_name}**\n\n"
            num_buttons = []
            for idx, res in enumerate(results, 1):
                music_text += f"**{idx}.** {res['title']} **{res['duration']}**\n"
                num_buttons.append(InlineKeyboardButton(str(idx), callback_data=f"dlmusic_{idx-1}"))

            row_buttons = [num_buttons[i:i+5] for i in range(0, len(num_buttons), 5)]
            row_buttons.insert(0, [InlineKeyboardButton("📁 Video", callback_data="menu_downloader")])

            music_keyboard = InlineKeyboardMarkup(row_buttons)
            await client.send_message(user_id, music_text, reply_markup=music_keyboard)
        else:
            await client.send_message(user_id, "❌ Videodagi qo'shiqni Shazam topa olmadi.")

        try:
            await hourglass_msg.delete()
        except:
            pass

    elif data.startswith("dlmusic_"):
        idx = int(data.split("_")[1])
        user_results = search_results_cache.get(user_id, [])

        if not user_results or idx >= len(user_results):
            await callback_query.answer("❌ Musiqa topilmadi!", show_alert=True)
            return

        selected = user_results[idx]
        status = await client.send_message(user_id, f"⏳ **{selected['title']}** yuklanmoqda...")

        out_mp3 = f"music_{user_id}_{int(time.time())}.mp3"
        cmd = f'yt-dlp -x --audio-format mp3 -o "{out_mp3}" "{selected["url"]}"'
        
        process = await asyncio.create_subprocess_shell(cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        await process.communicate()

        if os.path.exists(out_mp3):
            await status.edit_text("📤 **Audio yuborilmoqda...**")
            await client.send_audio(
                chat_id=user_id,
                audio=out_mp3,
                caption=f"🎵 **{selected['title']}**\n🤖 Bot: {BOT_SIGNATURE}",
                progress=progress_status,
                progress_args=(status, "📤 **Audio yuborilmoqda...**")
            )
            os.remove(out_mp3)
            await status.delete()
        else:
            await status.edit_text("❌ Musiqani yuklab bo'lmadi.")

    elif data.startswith("ytdl_"):
        parts = data.split("_")
        quality = parts[1]
        url = yt_cache.get(user_id)

        if not url:
            await callback_query.answer("❌ Link muddati o'tdi, qayta yuboring!", show_alert=True)
            return

        try:
            await callback_query.message.delete()
        except:
            pass

        status = await client.send_message(user_id, f"⏳ **{quality} formatini yuklash boshlandi...**")
        file_name = f"yt_{user_id}_{int(time.time())}"
        
        if quality == "mp3":
            out_file = f"{file_name}.mp3"
            cmd = f'yt-dlp -x --audio-format mp3 -o "{out_file}" "{url}"'
        else:
            out_file = f"{file_name}.mp4"
            h = quality.replace("p", "")
            cmd = f'yt-dlp -f "bestvideo[height<={h}][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<={h}]+bestaudio/best[height<={h}]/best" --merge-output-format mp4 -o "{out_file}" "{url}"'

        process = await asyncio.create_subprocess_shell(cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        await process.communicate()

        if os.path.exists(out_file) and os.path.getsize(out_file) > 0:
            await status.edit_text("📤 **Botga yuborilmoqda...**")
            
            if quality == "mp3":
                await client.send_audio(
                    chat_id=user_id,
                    audio=out_file,
                    caption=f"🎵 Audio yuklab olindi!\n🤖 Bot: {BOT_SIGNATURE}",
                    progress=progress_status,
                    progress_args=(status, "📤 **Audio yuborilmoqda...**")
                )
                os.remove(out_file)
            else:
                media_file_cache[user_id] = out_file
                await client.send_video(
                    chat_id=user_id,
                    video=file_name,
                    caption=f"🎬 Sifat: **{quality}**\n🤖 Bot: {BOT_SIGNATURE}",
                    reply_markup=get_post_download_buttons(user_id),
                    progress=progress_status,
                    progress_args=(status, f"📤 **{quality} video yuborilmoqda...**")
                )
            await status.delete()
        else:
            await status.edit_text("❌ Yuklab bo'lmadi.")

@app.on_message(filters.private & filters.text & ~filters.command(["start", "stop"]))
async def handle_user_messages(client, message):
    user_id = message.chat.id
    text = message.text
    mode = user_mode.get(user_id, "default")

    is_yt = re.search(r"(youtube\.com|youtu\.be)", text)
    is_pinterest = re.search(r"(pinterest\.com|pin\.it)", text)
    is_other_social = re.search(r"(instagram\.com|tiktok\.com|vt\.tiktok\.com|vm\.tiktok\.com)", text)

    if is_yt:
        hourglass_msg = await message.reply_text("⏳")
        info = await get_yt_info(text)

        try:
            await message.delete()
        except:
            pass

        if info:
            yt_cache[user_id] = text
            title = info["title"]
            thumb = info["thumbnail"]
            qualities = info["qualities"]
            sizes = info["sizes"]
            audio_size = info["audio_size"]

            inline_keyboard = []
            row = []
            for q in qualities:
                size_str = f" ~ {sizes[q]}MB" if q in sizes else ""
                label = f"🚀 {q}p{size_str}"
                row.append(InlineKeyboardButton(label, callback_data=f"ytdl_{q}p"))
                if len(row) == 2:
                    inline_keyboard.append(row)
                    row = []
            if row:
                inline_keyboard.append(row)

            mp3_label = f"🎵 MP3 Audiosi ~ {audio_size}MB" if audio_size else "🎵 MP3 Audiosi"
            inline_keyboard.append([InlineKeyboardButton(mp3_label, callback_data="ytdl_mp3")])

            buttons = InlineKeyboardMarkup(inline_keyboard)
            caption = f"📹 **{title}**\n\n👇 **Yuklash uchun formatni tanlang:**"

            if thumb:
                await client.send_photo(chat_id=user_id, photo=thumb, caption=caption, reply_markup=buttons)
            else:
                await client.send_message(chat_id=user_id, text=caption, reply_markup=buttons)
            
            try:
                await hourglass_msg.delete()
            except:
                pass
        else:
            try:
                await hourglass_msg.delete()
            except:
                pass
            await message.reply_text("❌ YouTube ma'lumotlarini olib bo'lmadi.")

    elif is_pinterest:
        hourglass_msg = await message.reply_text("⏳")
        try:
            await message.delete()
        except:
            pass

        media_type, file_path = await asyncio.to_thread(download_pinterest_media, text, user_id)

        if file_path and os.path.exists(file_path):
            status = await client.send_message(user_id, "📤 **Fayl yuborilmoqda...**")
            
            if media_type == "video":
                media_file_cache[user_id] = file_path
                await client.send_video(
                    chat_id=user_id,
                    video=file_path,
                    caption=f"✅ **Pinterest videosi yuklab olindi!**\n🤖 Bot: {BOT_SIGNATURE}",
                    reply_markup=get_post_download_buttons(user_id),
                    progress=progress_status,
                    progress_args=(status, "📤 **Video yuborilmoqda...**")
                )
            else:
                await client.send_photo(
                    chat_id=user_id,
                    photo=file_path,
                    caption=f"✅ **Pinterest rasmi yuklab olindi!**\n🤖 Bot: {BOT_SIGNATURE}",
                    progress=progress_status,
                    progress_args=(status, "📤 **Rasm yuborilmoqda...**")
                )
                os.remove(file_path)

            await status.delete()
            try:
                await hourglass_msg.delete()
            except:
                pass
        else:
            try:
                await hourglass_msg.delete()
            except:
                pass
            await client.send_message(user_id, "❌ Pinterest faylini yuklab bo'lmadi.")

    elif is_other_social:
        hourglass_msg = await message.reply_text("⏳")
        try:
            await message.delete()
        except:
            pass

        file_path = await asyncio.to_thread(download_instagram_multi_api, text, user_id)

        if file_path and os.path.exists(file_path) and os.path.getsize(file_path) > 0:
            media_file_cache[user_id] = file_path
            status = await client.send_message(user_id, "📤 **Video yuborilmoqda...**")
            await client.send_video(
                chat_id=user_id,
                video=file_path,
                caption=f"✅ **Video yuklab olindi!**\n🤖 Bot: {BOT_SIGNATURE}",
                reply_markup=get_post_download_buttons(user_id),
                progress=progress_status,
                progress_args=(status, "📤 **Video yuborilmoqda...**")
            )
            await status.delete()
            try:
                await hourglass_msg.delete()
            except:
                pass
        else:
            try:
                await hourglass_msg.delete()
            except:
                pass
            await message.reply_text("❌ Videoni yuklab bo'lmadi. Linkni qayta tekshiring.")

    elif mode == "ai":
        status = await message.reply_text("🤔 **AI o'ylamoqda...**")
        try:
            response = await asyncio.to_thread(
                g4f.ChatCompletion.create,
                model=g4f.models.gpt_4,
                messages=[{"role": "user", "content": text}]
            )
            await status.edit_text(f"🧠 **AI Javobi:**\n\n{response}\n\n🤖 {BOT_SIGNATURE}", reply_markup=BACK_BUTTON)
        except Exception as e:
            await status.edit_text(f"❌ Xatolik: {str(e)}", reply_markup=BACK_BUTTON)

    else:
        pass

class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot Multi-API bilan 24/7 ishlamoqda!")

def run_dummy_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
    server.serve_forever()

def keep_alive_ping():
    render_url = "https://universal-bot-1-qhpd.onrender.com"
    while True:
        try:
            time.sleep(240)
            requests.get(render_url, timeout=10)
        except Exception:
            pass

if __name__ == "__main__":
    threading.Thread(target=run_dummy_server, daemon=True).start()
    threading.Thread(target=keep_alive_ping, daemon=True).start()
    print("🚀 Bot ko'p bosqichli RapidAPI bloksiz tizimi bilan ishga tushdi!")
    app.run()
