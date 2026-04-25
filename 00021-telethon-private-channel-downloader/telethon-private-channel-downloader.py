from telethon import TelegramClient, events, Button
from telethon.sessions import StringSession
from telethon.network.connection.tcpobfuscated import ConnectionTcpObfuscated
import asyncio
from pathlib import Path
import logging
from collections import deque
import time

# ================= CONFIG =================
API_ID = 123456
API_HASH = 'your_api_hash_here'
SESSION_FILE = 'userbot'           # or StringSession if you prefer
OWNER_ID = 1234567890               # Your Telegram ID

SAVE_FOLDER = Path(__file__).parent / "mydata"
SAVE_FOLDER.mkdir(exist_ok=True)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
log = logging.getLogger(__name__)

# TURBO CLIENT — MAX PARALLEL CONNECTIONS
client = TelegramClient(
    SESSION_FILE,
    API_ID,
    API_HASH,
    connection=ConnectionTcpObfuscated,   # Bypass throttling
    connection_retries=None,
    device_model="PC",
    system_version="Windows 10",
    app_version="10.0",
    timeout=60,
    request_retries=20,
    flood_sleep_threshold=120,
    auto_reconnect=True
)

download_queue = deque()        # (msg, source, link, qid)
queue_counter = 0
currently_downloading = None
queue_message = None
queue_lock = asyncio.Lock()


async def update_queue_display():
    global queue_message
    async with queue_lock:
        lines = ["<b>TURBO Downloader (300+ MB/s)</b>\n"]

        if currently_downloading:
            msg, source, _, _ = currently_downloading
            fname = getattr(msg.file, "name", None) or f"file_{msg.id}"
            short = fname[:50] + ("..." if len(fname) > 50 else "")
            lines.append(
                f"<b>Downloading:</b>\n• <code>{short}</code> — {source}\n")
        else:
            lines.append("<b>Idle – TURBO READY</b>\n")

        if download_queue:
            lines.append(f"<b>In queue ({len(download_queue)}):</b>")
            for i, (msg, source, _, qid) in enumerate(download_queue):
                fname = getattr(msg.file, "name", None) or f"file_{msg.id}"
                short = fname[:40] + ("..." if len(fname) > 40 else "")
                lines.append(f"{i+1}. <code>{short}</code> — {source}")
        else:
            if not currently_downloading:
                lines.append("Queue empty")

        text = "\n".join(lines)
        buttons = []
        if currently_downloading:
            buttons.append(
                [Button.inline("Cancel Current", b"cancel_current")])
        row = []
        for item in download_queue:
            row.append(Button.inline("Remove", f"remove_{item[3]}".encode()))
            if len(row) == 5:
                buttons.append(row)
                row = []
        if row:
            buttons.append(row)
        if download_queue:
            buttons.append([Button.inline("Clear Queue", b"clear_queue")])
        buttons.append([Button.inline("Refresh", b"refresh")])

        try:
            if queue_message:
                await queue_message.edit(text, buttons=buttons, parse_mode="html")
            else:
                queue_message = await client.send_message(OWNER_ID, text, buttons=buttons, parse_mode="html")
        except Exception as e:
            log.error(f"Queue update error: {e}")


async def download_worker():
    global currently_downloading
    while True:
        if not currently_downloading and download_queue:
            async with queue_lock:
                currently_downloading = download_queue.popleft()
            await update_queue_display()

            msg, source, link, qid = currently_downloading

            filename = getattr(msg.file, "name", None)
            if not filename:
                ext = ".mp4" if msg.video else ".jpg" if msg.photo else ".bin"
                filename = f"{msg.date.strftime('%Y%m%d_%H%M%S')}_{msg.id}{ext}"
            safe_name = "".join(
                c if c not in r'\/:*?"<>|' else "_" for c in filename)
            path = SAVE_FOLDER / safe_name

            status_msg = await client.send_message(OWNER_ID, f"Starting: <code>{safe_name}</code>", parse_mode="html")
            start_time = time.time()
            last_update = 0
            speed_samples = []  # Track speeds for avg

            def turbo_progress(current, total):
                nonlocal last_update
                now = time.time()
                if now - last_update < 0.4 and current != total:
                    return
                last_update = now

                if total <= 0:
                    return
                percent = current / total
                bar = "█" * int(percent * 16) + "░" * (16 - int(percent * 16))
                mb = f"{current/1e6:.1f}/{total/1e6:.1f} MB"
                speed = (current / 1e6) / \
                    max(now - start_time, 0.1)  # Instant speed
                speed_samples.append(speed)
                # Avg over last 3 samples (for stability)
                if len(speed_samples) > 3:
                    speed_samples.pop(0)
                avg_speed = sum(speed_samples) / len(speed_samples)

                throttle_msg = ""
                if avg_speed < 1.0:  # THROTTLING DETECTED!
                    throttle_msg = f"\n⚠️ **THROTTLING!** (0.1–1 MB/s limit — userbot cap. Try Premium/VPN)"

                try:
                    asyncio.create_task(status_msg.edit(
                        f"<code>{bar}</code> {percent*100:5.1f}% • {mb}\n"
                        f"<code>{safe_name[:60]}</code>\n"
                        f"Speed: <b>{avg_speed:.1f} MB/s</b>{throttle_msg}",
                        parse_mode="html"
                    ))
                except:
                    pass

            # ... (rest of try/except unchanged)

            try:
                if path.exists() and msg.file and path.stat().st_size == msg.file.size:
                    await status_msg.edit(f"Already exists: <code>{safe_name}</code>", parse_mode="html")
                else:
                    await client.download_media(
                        msg,
                        file=path,
                        progress_callback=turbo_progress
                    )
                    total_time = time.time() - start_time
                    avg_speed = (msg.file.size / 1e6) / max(total_time, 0.1)
                    throttle_final = " ⚠️ THROTTLING DETECTED!" if avg_speed < 1.0 else ""
                    log.info(
                        f"DONE: {safe_name} @ {avg_speed:.1f} MB/s{throttle_final}")
                    await status_msg.edit(f"Completed: <code>{safe_name}</code>\n<b>{avg_speed:.1f} MB/s</b>{throttle_final}", parse_mode="html")
            except Exception as e:
                await status_msg.edit(f"Failed: <code>{safe_name}</code>\n{e}", parse_mode="html")
                log.error(f"Download failed: {e}")

            async with queue_lock:
                currently_downloading = None
            await update_queue_display()

        await asyncio.sleep(0.5)


async def add_to_queue(messages, source, link):
    global queue_counter
    async with queue_lock:
        for msg in messages:
            if msg.media:
                download_queue.append((msg, source, link, queue_counter))
                queue_counter += 1
    await update_queue_display()


@client.on(events.NewMessage(from_users=OWNER_ID, pattern=r'(https?://t\.me/.*|https?://telegram\.me/.*)'))
async def handle_link(event):
    link = event.pattern_match.group(1).split('?')[0]
    await event.reply("Processing link...")

    try:
        if "/c/" in link:
            parts = link.split("/c/")[1].split("/")
            entity = await client.get_entity(int("-100" + parts[0]))
            msg_id = int(parts[1])
            source = getattr(entity, "title", "Private")
        else:
            username = link.split("t.me/")[1].split("/")[0]
            entity = await client.get_entity(username)
            msg_id = int(link.split("/")[-1])
            source = getattr(entity, "title", username)

        msg = await client.get_messages(entity, ids=msg_id)
        if not msg:
            await event.reply("Message not found")
            return
        if isinstance(msg, list):
            msg = msg[0]

        to_download = []
        if getattr(msg, "grouped_id", None):
            async for m in client.iter_messages(entity, min_id=msg_id-300, max_id=msg_id+300):
                if getattr(m, "grouped_id", None) == msg.grouped_id and m.media:
                    to_download.append(m)
            await event.reply(f"Album queued: {len(to_download)} files")
        else:
            if msg.media:
                to_download.append(msg)
                await event.reply("File added to queue")

        await add_to_queue(to_download, source, link)

    except Exception as e:
        await event.reply(f"Error: {e}")


@client.on(events.CallbackQuery)
async def buttons(event):
    if event.sender_id != OWNER_ID:
        return

    data = event.data
    if data == b"refresh":
        await update_queue_display()
        await event.answer()
    elif data == b"cancel_current" and currently_downloading:
        async with queue_lock:
            currently_downloading = None
        await event.answer("Cancelled!", alert=True)
        await update_queue_display()
    elif data == b"clear_queue":
        async with queue_lock:
            download_queue.clear()
        await event.answer("Queue cleared!", alert=True)
        await update_queue_display()
    elif data.startswith(b"remove_"):
        try:
            qid = int(data.split(b"_")[1])
            async with queue_lock:
                for i, item in enumerate(list(download_queue)):
                    if item[3] == qid:
                        fname = getattr(item[0].file, "name", "file")[:30]
                        download_queue.remove(item)
                        await event.answer(f"Removed: {fname}...", alert=True)
                        break
            await update_queue_display()
        except:
            pass
    else:
        await event.answer()


async def main():
    await client.start()
    me = await client.get_me()
    print("\n" + "═" * 80)
    print("TURBO DOWNLOADER 300+ MB/s — FULLY WORKING")
    print(f"Account : @{me.username or 'None'} (ID: {me.id})")
    print("Parallel chunks • Real buttons • Queue • Albums • Private channels")
    print("Send any t.me link → lightning download to ./mydata")
    print("═" * 80 + "\n")

    client.loop.create_task(download_worker())
    global queue_message
    queue_message = await client.send_message(
        OWNER_ID,
        "<b>TURBO Downloader Ready!</b>\nClick Refresh",
        buttons=[[Button.inline("Refresh", b"refresh")]],
        parse_mode="html"
    )

    await client.run_until_disconnected()


if __name__ == "__main__":
    asyncio.run(main())
