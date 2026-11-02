#!/usr/bin/env python3
"""Uzdem ders kanallarındaki medyaları indirir (Telethon).

Kullanım:
  1) İlk çalıştırma:  /tmp/tgvenv/bin/python tg_indir.py login
     (telefon numarası + Telegram'a gelen kod + varsa 2FA şifresi sorulur)
  2) İndirme:         /tmp/tgvenv/bin/python tg_indir.py indir
     (başarısız/eksik kalanları tekrar dener: aynı komut tekrar çalıştırılır)
"""
import asyncio
import json
import os
import re
import sys

from telethon import TelegramClient
from telethon.errors import FloodWaitError
from telethon.tl.types import MessageMediaDocument, MessageMediaPhoto

HERE = os.path.dirname(os.path.abspath(__file__))
SESSION = os.path.join(HERE, "uzdem")
CFG = os.path.join(HERE, "config.json")
HEDEF = os.path.join(os.path.expanduser("~/Desktop"), "Uzdem Dersler")

# ilk 20 link (mesajdaki sırayla). İkinci gruptaki tekrarlar (Telhis, Mektubat
# Şerife) zaten bunların içinde.
KANALLAR = [
    ("01 Emsile", "https://t.me/+UHm1MoC4mXg4YWUy"),
    ("02 Bina", "https://t.me/+0OwOKYryTjsxYmMy"),
    ("03 Maksud", "https://t.me/+43Q-3nBIq7JjNGQy"),
    ("04 Avamil", "https://t.me/+VTKLdnWfvBU3ZTRi"),
    ("05 Izhar", "https://t.me/+NCw4BQ3Fy0dkZmJi"),
    ("06 Kafiye", "https://t.me/+1mNpboWfvQ9iYzZi"),
    ("07 Nurul Izah", "https://t.me/+3e4yLz-f3mdhZDdi"),
    ("08 Kuduri Serif", "https://t.me/+y_qYkbKzlkM2YTc6"),
    ("09 Isagoci", "https://t.me/+z5foyAsSBbc2MTZi"),
    ("10 Metn-i Akaid", "https://t.me/+9qwqKbEMryJmNzli"),
    ("11 Emali", "https://t.me/+peeBtx10JZE0Yzhi"),
    ("12 Menar", "https://t.me/+ealfUYdoT340NGUy"),
    ("13 Alaka", "https://t.me/+8pQQ9Al7mWkzM2Yy"),
    ("14 Telhis", "https://t.me/+Q8leQ0HNvhkwYWY6"),
    ("15 Asr-i Serifler", "https://t.me/+a7R67jub0Y9mYjUy"),
    ("16 Talim dersi", "https://t.me/+nxdphWQ2ywNmZjc6"),
    ("17 Sohbetler", "https://t.me/+Ydgmp_QTw8BjZmU6"),
    ("18 Kitabet", "https://t.me/+ebh86kEzZgxmZmFi"),
    ("19 Muhadese", "https://t.me/+o54fG53vAbUwMzRi"),
    ("20 Mektubat 1-cilt ses", "https://t.me/+dSHi27xbnvFkMzgy"),
]


def cfg_yukle():
    with open(CFG, encoding="utf-8") as f:
        c = json.load(f)
    if not c.get("api_id") or not c.get("api_hash"):
        sys.exit("config.json içinde api_id / api_hash boş. my.telegram.org'dan alıp doldur.")
    return int(c["api_id"]), str(c["api_hash"]).strip(), c.get("phone") or None


def guvenli_ad(ad, sinir=90):
    ad = re.sub(r'[\\/:*?"<>|\n\r\t]+', " ", ad).strip()
    ad = re.sub(r"\s+", " ", ad)
    return (ad[:sinir].rstrip() or "adsiz")


def dosya_adi(msg):
    f = msg.file
    if f and f.name:
        return guvenli_ad(f.name)
    if f and f.ext:
        return f"{msg.id}.{f.ext.lstrip('.')}"
    return f"{msg.id}.jpg"


async def login():
    api_id, api_hash, phone = cfg_yukle()
    client = TelegramClient(SESSION, api_id, api_hash)
    await client.start(phone=phone)
    me = await client.get_me()
    print("Giriş OK:", me.first_name, "|", me.username or "-", "| id:", me.id)
    await client.disconnect()


async def indir():
    api_id, api_hash, phone = cfg_yukle()
    client = TelegramClient(SESSION, api_id, api_hash)
    await client.start(phone=phone)
    os.makedirs(HEDEF, exist_ok=True)

    ozet = []
    for ad, link in KANALLAR:
        print(f"\n=== {ad} ===", flush=True)
        try:
            try:
                ent = await client.get_entity(link)
            except Exception:
                from telethon.tl.functions.messages import ImportChatInviteRequest
                from telethon.tl.types import ChatInviteAlready
                res = await client(ImportChatInviteRequest(link.split("+")[-1].strip()))
                if isinstance(res, ChatInviteAlready):
                    ent = res.chat
                else:
                    chats = [c for c in res.updates.chats if hasattr(c, "title")]
                    ent = chats[0] if chats else None
                if ent is None:
                    raise RuntimeError("katılım sonucundan kanal çıkarılamadı")
            print("kanal:", getattr(ent, "title", ent), flush=True)
        except FloodWaitError as e:
            bekle = e.seconds + 10
            print(f"FLOOD: {bekle}s bekleniyor sonra tekrar denenecek", flush=True)
            await asyncio.sleep(bekle)
            try:
                ent = await client.get_entity(link)
            except Exception:
                from telethon.tl.functions.messages import ImportChatInviteRequest
                from telethon.tl.types import ChatInviteAlready
                res = await client(ImportChatInviteRequest(link.split("+")[-1].strip()))
                if isinstance(res, ChatInviteAlready):
                    ent = res.chat
                else:
                    chats = [c for c in res.updates.chats if hasattr(c, "title")]
                    ent = chats[0] if chats else None
                if ent is None:
                    print("HATA: kanal çıkarılamadı", flush=True)
                    ozet.append([ad, "HATA", 0, 0])
                    continue
        except Exception as e:
            print("HATA (kanala erişilemedi):", type(e).__name__, e, flush=True)
            ozet.append([ad, f"HATA {type(e).__name__}", 0, 0])
            continue

        hedef = os.path.join(HEDEF, ad)
        os.makedirs(hedef, exist_ok=True)
        indirilen = eksik = 0
        try:
            async for msg in client.iter_messages(ent):
                if not msg.media or isinstance(msg.media, MessageMediaPhoto):
                    continue
                if not isinstance(msg.media, MessageMediaDocument):
                    continue
                yol = os.path.join(hedef, f"{msg.id:06d}_" + dosya_adi(msg))
                if os.path.exists(yol) and os.path.getsize(yol) > 0:
                    continue
                for deneme in range(3):
                    try:
                        await client.download_media(msg, file=yol)
                        indirilen += 1
                        break
                    except FloodWaitError as e:
                        print(f"  flood {e.seconds}s bekleniyor", flush=True)
                        await asyncio.sleep(e.seconds + 2)
                    except Exception as e:
                        print(f"  {msg.id} indirilemedi: {type(e).__name__} {e}", flush=True)
                        await asyncio.sleep(3)
                else:
                    eksik += 1
                if (indirilen + eksik) % 25 == 0:
                    print(f"  ... {indirilen} indi, {eksik} eksik", flush=True)
        except Exception as e:
            print("  mesaj listesi hatası:", type(e).__name__, e, flush=True)
        print(f"  -> {indirilen} indirildi, {eksik} eksik", flush=True)
        ozet.append([ad, "ok" if not eksik else "kısmi", indirilen, eksik])
        await asyncio.sleep(8)  # kanallar arası bekleme: katılım flood limitine yakalanmamak için

    print("\n=== ÖZET ===")
    for r in ozet:
        print(f"{r[0]:24s} {r[1]:10s} indi={r[2]:4d} eksik={r[3]:3d}")
    await client.disconnect()


if __name__ == "__main__":
    komut = sys.argv[1] if len(sys.argv) > 1 else "indir"
    if komut == "login":
        asyncio.run(login())
    else:
        asyncio.run(indir())
