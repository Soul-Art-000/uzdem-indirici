#!/usr/bin/env python3
"""
Uzdem Ders İndirici — Windows sürümü (tek dosya .exe).

Kurulum sihirbazı 4 adımda yönlendirir:
  1. Hoş geldin
  2. Telegram API bilgileri (my.telegram.org)
  3. Telefon doğrulama (kod + 2FA)
  4. Klasör seçimi ve indirme

Bağımlılıklar .exe içine gömülüdür; karşı tarafta Python kurulu olması gerekmez.
"""
import asyncio
import os
import queue
import re
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from telethon import TelegramClient
from telethon.errors import FloodWaitError, SessionPasswordNeededError
from telethon.tl.functions.messages import ImportChatInviteRequest
from telethon.tl.types import ChatInviteAlready, MessageMediaDocument, MessageMediaPhoto

APP_ADI = "Uzdem Ders İndirici"
AYAR_DIZIN = os.path.join(os.path.expanduser("~"), "Documents", "UzdemIndirici")
SESSION = os.path.join(AYAR_DIZIN, "oturum")
VARSAYILAN_HEDEF = os.path.join(os.path.expanduser("~"), "Downloads", "Uzdem Dersler")

KANALLAR = [
    ("01 Emsile", "https://t.me/+UHm1MoC4mXg4YWUy"),
    ("02 Bina", "https://t.me/+0OwOKYryTjsxYmMy"),
    ("03 Maksud", "https://t.me/+43Q-3nBIq7JjNGQy"),
    ("04 Avamil", "https://t.me/+VTKLdnWfvBU3ZTRi"),
    ("05 İzhar", "https://t.me/+NCw4BQ3Fy0dkZmJi"),
    ("06 Kafiye", "https://t.me/+1mNpboWfvQ9iYzZi"),
    ("07 Nuru'l İzah", "https://t.me/+3e4yLz-f3mdhZDdi"),
    ("08 Kuduri Şerif", "https://t.me/+y_qYkbKzlkM2YTc6"),
    ("09 İsagoci", "https://t.me/+z5foyAsSBbc2MTZi"),
    ("10 Metn-i Akaid", "https://t.me/+9qwqKbEMryJmNzli"),
    ("11 Emali", "https://t.me/+peeBtx10JZE0Yzhi"),
    ("12 Menar", "https://t.me/+ealfUYdoT340NGUy"),
    ("13 Alaka", "https://t.me/+8pQQ9Al7mWkzM2Yy"),
    ("14 Telhis", "https://t.me/+Q8leQ0HNvhkwYWY6"),
    ("15 Aşr-ı Şerifler", "https://t.me/+a7R67jub0Y9mYjUy"),
    ("16 Talim dersi", "https://t.me/+nxdphWQ2ywNmZjc6"),
    ("17 Sohbetler", "https://t.me/+Ydgmp_QTw8BjZmU6"),
    ("18 Kitabet", "https://t.me/+ebh86kEzZgxmZmFi"),
    ("19 Muhadese", "https://t.me/+o54fG53vAbUwMzRi"),
    ("20 Mektubat 1. cilt", "https://t.me/+dSHi27xbnvFkMzgy"),
]


def guvenli_ad(ad, sinir=90):
    ad = re.sub(r'[\\/:*?"<>|\n\r\t]+', " ", str(ad)).strip()
    return (re.sub(r"\s+", " ", ad)[:sinir].rstrip() or "adsiz")


def dosya_adi(msg):
    f = msg.file
    if f and f.name:
        return guvenli_ad(f.name)
    if f and f.ext:
        return "%s.%s" % (msg.id, f.ext.lstrip("."))
    return "%s.bin" % msg.id


class Sihirbaz(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_ADI)
        self.geometry("700x620")
        self.minsize(640, 560)
        self.configure(bg="#f4f6f8")
        self.q = queue.Queue()
        self.client = None
        self.dur = False
        self.adim = 0
        self.telefon = ""
        self.api_id = None
        self.api_hash = ""
        self.hedef_dizin = tk.StringVar(value=VARSAYILAN_HEDEF)
        self._stil()
        self.govde = tk.Frame(self, bg="#f4f6f8")
        self.govde.pack(fill="both", expand=True)
        self._ciz()
        self.after(120, self._kuyruk)

    # ---------- görsel ----------
    def _stil(self):
        s = ttk.Style(self)
        try:
            s.theme_use("clam")
        except Exception:
            pass
        s.configure("TButton", font=("Segoe UI", 10))
        s.configure("Buyuk.TButton", font=("Segoe UI", 11, "bold"), padding=(14, 10),
                    background="#2d7d46", foreground="white")
        s.map("Buyuk.TButton", background=[("active", "#246337"), ("disabled", "#9bb3a3")])
        s.configure("Adim.TLabel", font=("Segoe UI", 9), foreground="#8a8f98")

    def _baslik(self, metin, alt=None):
        tk.Label(self.govde, text=metin, font=("Segoe UI", 16, "bold"),
                 bg="#f4f6f8", fg="#1b2430").pack(anchor="w", padx=24, pady=(18, 2))
        if alt:
            tk.Label(self.govde, text=alt, font=("Segoe UI", 10), bg="#f4f6f8",
                     fg="#5d6673", wraplength=620, justify="left").pack(anchor="w", padx=24)

    # ---------- akış ----------
    def _ciz(self):
        for w in self.govde.winfo_children():
            w.destroy()
        if self.adim == 0:
            self._ekran_hosgeldin()
        elif self.adim == 1:
            self._ekran_api()
        elif self.adim == 2:
            self._ekran_giris()
        elif self.adim == 3:
            self._ekran_klasor()
        else:
            self._ekran_indirme()

    def _alt_bar(self, ileri_metin, ileri_fn, geri=True, ileri_durum="normal"):
        bar = tk.Frame(self.govde, bg="#f4f6f8")
        bar.pack(side="bottom", fill="x", padx=24, pady=16)
        if geri:
            ttk.Button(bar, text="← Geri", command=self._geri).pack(side="left")
        ttk.Button(bar, text=ileri_metin, style="Buyuk.TButton", command=ileri_fn,
                   state=ileri_durum).pack(side="right")
        return bar

    def _geri(self):
        if self.adim > 0:
            self.adim -= 1
            self._ciz()

    # --- 1. hoş geldin ---
    def _ekran_hosgeldin(self):
        self._baslik("Uzdem Ders İndirici'ye hoş geldin",
                     "Bu program Telegram'daki 20 ders kanalındaki bütün video, ses ve "
                     "dokümanları tek tuşla bilgisayarına indirir.")
        k = tk.Frame(self.govde, bg="white", bd=0, highlightthickness=1,
                     highlightbackground="#e0e4e9")
        k.pack(fill="both", expand=True, padx=24, pady=16)
        tk.Label(k, text="Nelere ihtiyacın var?", font=("Segoe UI", 11, "bold"),
                 bg="white", fg="#1b2430").pack(anchor="w", padx=18, pady=(16, 6))
        adimlar = [
            ("1", "Telegram API bilgileri", "my.telegram.org sitesinden alacağız — 2 dakika."),
            ("2", "Telefon doğrulaması", "Telegram'dan gelen kodu gireceksin. Bu işlem bir kez yapılır."),
            ("3", "Klasör seçimi", "Dosyaların nereye ineceğini belirle."),
            ("4", "İndirme", "Geri kalan her şeyi program kendi yapar."),
        ]
        for no, bas, alt in adimlar:
            r = tk.Frame(k, bg="white")
            r.pack(fill="x", padx=18, pady=5)
            tk.Label(r, text=no, font=("Segoe UI", 11, "bold"), bg="#2d7d46", fg="white",
                     width=3).pack(side="left", padx=(0, 10), ipady=3)
            sut = tk.Frame(r, bg="white")
            sut.pack(side="left", anchor="w")
            tk.Label(sut, text=bas, font=("Segoe UI", 10, "bold"), bg="white",
                     fg="#1b2430").pack(anchor="w")
            tk.Label(sut, text=alt, font=("Segoe UI", 9), bg="white",
                     fg="#6b7480").pack(anchor="w")
        tk.Label(k, text="Not: İndirme sırasında Telegram'ın katılım hız limitine takılırsa program "
                         "kendisi bekler ve devam eder. Yarıda kalırsa aynı butona basınca "
                         "indirilmiş dosyalar atlanarak devam edilir.",
                 font=("Segoe UI", 9), bg="white", fg="#6b7480", wraplength=580,
                 justify="left").pack(anchor="w", padx=18, pady=(14, 16))
        self._alt_bar("Başla  →", self._ileri_api, geri=False)

    # --- 2. API ---
    def _ekran_api(self):
        self._baslik("1. Adım — Telegram API bilgileri",
                     "my.telegram.org adresine telefon numaranla giriş yap, "
                     "'API development tools' bölümünden uygulama oluştur ve iki değeri buraya yapıştır.")
        k = tk.Frame(self.govde, bg="white", bd=0, highlightthickness=1,
                     highlightbackground="#e0e4e9")
        k.pack(fill="x", padx=24, pady=14)
        tk.Label(k, text="api_id (sayı)", font=("Segoe UI", 9), bg="white",
                 fg="#5d6673").pack(anchor="w", padx=18, pady=(16, 2))
        self.e_api_id = tk.Entry(k, font=("Segoe UI", 11))
        self.e_api_id.pack(fill="x", padx=18)
        tk.Label(k, text="api_hash (32 karakter)", font=("Segoe UI", 9), bg="white",
                 fg="#5d6673").pack(anchor="w", padx=18, pady=(12, 2))
        self.e_api_hash = tk.Entry(k, font=("Segoe UI", 11))
        self.e_api_hash.pack(fill="x", padx=18, pady=(0, 16))
        if self.api_id:
            self.e_api_id.insert(0, str(self.api_id))
            self.e_api_hash.insert(0, self.api_hash)
        tk.Label(self.govde, text="Nereden alınır?  my.telegram.org → API development tools → "
                                  "App api_id / App api_hash",
                 font=("Segoe UI", 9), bg="#f4f6f8", fg="#7b838f").pack(anchor="w", padx=24)
        self._alt_bar("Devam  →", self._ileri_giris)

    # --- 3. giriş ---
    def _ekran_giris(self):
        self._baslik("2. Adım — Telefon doğrulaması",
                     "Telefon numaranı yaz ve 'Kod Gönder'e bas. Telegram uygulamasına veya "
                     "SMS'e gelen 5 haneli kodu gir.")
        k = tk.Frame(self.govde, bg="white", bd=0, highlightthickness=1,
                     highlightbackground="#e0e4e9")
        k.pack(fill="x", padx=24, pady=14)
        tk.Label(k, text="Telefon numarası (ülke koduyla)", font=("Segoe UI", 9),
                 bg="white", fg="#5d6673").pack(anchor="w", padx=18, pady=(16, 2))
        r = tk.Frame(k, bg="white")
        r.pack(fill="x", padx=18)
        self.e_tel = tk.Entry(r, font=("Segoe UI", 11))
        self.e_tel.pack(side="left", fill="x", expand=True)
        if self.telefon:
            self.e_tel.insert(0, self.telefon)
        self.b_kod = ttk.Button(r, text="Kod Gönder", command=self._kod_gonder)
        self.b_kod.pack(side="left", padx=(8, 0))
        tk.Label(k, text="Gelen kod", font=("Segoe UI", 9), bg="white",
                 fg="#5d6673").pack(anchor="w", padx=18, pady=(14, 2))
        self.e_kod = tk.Entry(k, font=("Segoe UI", 12))
        self.e_kod.pack(fill="x", padx=18)
        tk.Label(k, text="İki adımlı doğrulama şifresi (varsa)", font=("Segoe UI", 9),
                 bg="white", fg="#5d6673").pack(anchor="w", padx=18, pady=(14, 2))
        self.e_sifre = tk.Entry(k, font=("Segoe UI", 11), show="•")
        self.e_sifre.pack(fill="x", padx=18, pady=(0, 16))
        self.log = tk.Text(k, height=5, bg="#111820", fg="#c9d4e0", relief="flat",
                           font=("Consolas", 9))
        self.log.pack(fill="x", padx=18, pady=(0, 16))
        self._alt_bar("Giriş Yap ve Devam  →", self._giris_yap)

    # --- 4. klasör ---
    def _ekran_klasor(self):
        self._baslik("3. Adım — Nereye indirilsin?",
                     "Her ders kendi alt klasörüne iner. Yeterli boş alan olduğundan emin ol "
                     "(toplam 20 GB'ı geçebilir).")
        k = tk.Frame(self.govde, bg="white", bd=0, highlightthickness=1,
                     highlightbackground="#e0e4e9")
        k.pack(fill="x", padx=24, pady=14)
        tk.Label(k, text="Hedef klasör", font=("Segoe UI", 9), bg="white",
                 fg="#5d6673").pack(anchor="w", padx=18, pady=(16, 2))
        r = tk.Frame(k, bg="white")
        r.pack(fill="x", padx=18, pady=(0, 16))
        tk.Entry(r, textvariable=self.hedef_dizin, font=("Segoe UI", 10)).pack(
            side="left", fill="x", expand=True)
        ttk.Button(r, text="Gözat…", command=self._gozat).pack(side="left", padx=(8, 0))
        self._alt_bar("İndirmeyi Başlat  →", self._indirmeye_gec)

    def _gozat(self):
        d = filedialog.askdirectory(initialdir=os.path.expanduser("~"))
        if d:
            self.hedef_dizin.set(os.path.join(d, "Uzdem Dersler"))

    # --- 5. indirme ---
    def _ekran_indirme(self):
        self._baslik("4. Adım — İndirme",
                     "Program sırayla her kanala katılır ve içindeki bütün medyayı indirir.")
        k = tk.Frame(self.govde, bg="white", bd=0, highlightthickness=1,
                     highlightbackground="#e0e4e9")
        k.pack(fill="both", expand=True, padx=24, pady=14)
        self.pb = ttk.Progressbar(k, mode="determinate", maximum=len(KANALLAR))
        self.pb.pack(fill="x", padx=18, pady=(18, 6))
        self.lbl_durum = tk.Label(k, text="Hazır", font=("Segoe UI", 10, "bold"),
                                  bg="white", fg="#1b2430", anchor="w")
        self.lbl_durum.pack(fill="x", padx=18)
        self.lbl_sayac = tk.Label(k, text="0 kanal tamamlandı", font=("Segoe UI", 9),
                                  bg="white", fg="#6b7480", anchor="w")
        self.lbl_sayac.pack(fill="x", padx=18)
        self.log2 = tk.Text(k, height=12, bg="#111820", fg="#c9d4e0", relief="flat",
                            font=("Consolas", 9))
        self.log2.pack(fill="both", expand=True, padx=18, pady=14)
        self._log("Kayıt yeri: %s" % self.hedef_dizin.get())
        bar = tk.Frame(self.govde, bg="#f4f6f8")
        bar.pack(side="bottom", fill="x", padx=24, pady=16)
        self.b_basla = ttk.Button(bar, text="▶  İndirmeyi Başlat", style="Buyuk.TButton",
                                  command=self._indir_tikla)
        self.b_basla.pack(side="right")
        ttk.Button(bar, text="Klasörü Aç", command=self._klasor_ac).pack(side="left")

    # ---------- kuyruk / log ----------
    def _log(self, s, hedef=None):
        t = hedef or getattr(self, "log2", None)
        if t is not None:
            t.insert("end", s + "\n")
            t.see("end")

    def _kuyruk(self):
        try:
            while True:
                tur, veri = self.q.get_nowait()
                if tur == "log":
                    self._log(veri)
                elif tur == "log1":
                    self._log(veri, getattr(self, "log", None))
                elif tur == "durum":
                    if hasattr(self, "lbl_durum"):
                        self.lbl_durum.config(text=veri)
                elif tur == "adim":
                    if hasattr(self, "pb"):
                        self.pb["value"] = veri
                        self.lbl_sayac.config(text="%d / %d kanal tamamlandı" % (veri, len(KANALLAR)))
                elif tur == "bitti":
                    messagebox.showinfo("Tamamlandı", veri)
                    if hasattr(self, "b_basla"):
                        self.b_basla.config(text="▶  İndirmeyi Başlat")
        except queue.Empty:
            pass
        self.after(120, self._kuyruk)

    # ---------- geçişler ----------
    def _ileri_api(self):
        self.adim = 1
        self._ciz()

    def _ileri_giris(self):
        aid = self.e_api_id.get().strip()
        ah = self.e_api_hash.get().strip()
        if not aid.isdigit() or len(ah) < 20:
            messagebox.showwarning("Eksik bilgi",
                                   "api_id sayı, api_hash en az 20 karakter olmalı.\n"
                                   "my.telegram.org → API development tools bölümünden alabilirsin.")
            return
        self.api_id, self.api_hash = int(aid), ah
        self.adim = 2
        self._ciz()

    def _kod_gonder(self):
        tel = self.e_tel.get().strip().replace(" ", "").replace("-", "")
        if not tel.startswith("+") or len(tel) < 9:
            messagebox.showwarning("Telefon", "Numarayı ülke koduyla gir, örn: +905551112233")
            return
        self.telefon = tel
        os.makedirs(AYAR_DIZIN, exist_ok=True)
        self.q.put(("log1", "Kod isteniyor…"))

        async def is_kod():
            self.client = TelegramClient(SESSION, self.api_id, self.api_hash)
            await self.client.connect()
            if await self.client.is_user_authorized():
                self.q.put(("log1", "Bu bilgisayarda giriş zaten yapılmış."))
                self.q.put(("otomatik", None))
                return
            await self.client.send_code_request(tel)
            self.q.put(("log1", "Kod gönderildi. Telegram uygulamasına bak."))

        self._arka(is_kod)

    def _giris_yap(self):
        if not self.api_id:
            messagebox.showwarning("Eksik", "Önce API bilgilerini gir.")
            return
        kod = self.e_kod.get().strip()
        if not kod:
            messagebox.showwarning("Eksik", "Telegram'dan gelen kodu gir.")
            return
        sifre = self.e_sifre.get().strip()
        tel = self.telefon or self.e_tel.get().strip()

        async def is_giris():
            if not self.client or not self.client.is_connected():
                self.client = TelegramClient(SESSION, self.api_id, self.api_hash)
                await self.client.connect()
            try:
                await self.client.sign_in(tel, kod)
            except SessionPasswordNeededError:
                if not sifre:
                    self.q.put(("log1", "İki adımlı doğrulama açık — 2FA şifresini gir."))
                    return
                await self.client.sign_in(password=sifre)
            me = await self.client.get_me()
            self.q.put(("log1", "Giriş başarılı: %s" % (me.first_name or me.id)))
            self.q.put(("giris_ok", None))

        self._arka(is_giris)

    def _arka(self, coro_fn):
        def sarmal():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(coro_fn())
            except Exception as e:
                self.q.put(("log1", "HATA: %s: %s" % (type(e).__name__, e)))
            finally:
                loop.close()
        threading.Thread(target=sarmal, daemon=True).start()

    def _indirmeye_gec(self):
        self.adim = 3
        self._ciz()

    def _klasor_ac(self):
        d = self.hedef_dizin.get()
        os.makedirs(d, exist_ok=True)
        try:
            os.startfile(d)  # Windows
        except AttributeError:
            import subprocess
            subprocess.Popen(["open" if sys.platform == "darwin" else "xdg-open", d])

    # ---------- indirme ----------
    def _indir_tikla(self):
        if self.dur:
            self.q.put(("durum", "Durduruluyor…"))
            return
        self.dur = False
        self.b_basla.config(text="⏸  Durdur")

        def sarmal():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(self._indir())
            except Exception as e:
                self.q.put(("log", "HATA: %s: %s" % (type(e).__name__, e)))
            finally:
                self.dur = False
                loop.close()
                self.q.put(("bitti", "İndirme işlemi sona erdi.\nKlasör: %s" % self.hedef_dizin.get()))

        threading.Thread(target=sarmal, daemon=True).start()

    async def _kanal_bul(self, link):
        try:
            return await self.client.get_entity(link)
        except Exception:
            pass
        son = None
        for _ in range(4):
            try:
                res = await self.client(ImportChatInviteRequest(link.split("+")[-1].strip()))
                if isinstance(res, ChatInviteAlready):
                    return res.chat
                chats = [c for c in res.updates.chats if hasattr(c, "title")]
                return chats[0] if chats else None
            except FloodWaitError as e:
                self.q.put(("log", "  katılım hız limiti: %ds bekleniyor" % e.seconds))
                await asyncio.sleep(e.seconds + 5)
                son = e
            except Exception as e:
                son = e
                await asyncio.sleep(5)
        self.q.put(("log", "  kanala erişilemedi: %s" % type(son).__name__))
        return None

    async def _indir(self):
        if not self.client or not self.client.is_connected():
            self.client = TelegramClient(SESSION, self.api_id, self.api_hash)
            await self.client.connect()
        hedef_kok = self.hedef_dizin.get()
        os.makedirs(hedef_kok, exist_ok=True)
        toplam = 0
        for i, (ad, link) in enumerate(KANALLAR):
            if self.dur:
                self.q.put(("log", "Kullanıcı durdurdu."))
                break
            self.q.put(("durum", "%s — kanal açılıyor" % ad))
            self.q.put(("log", "=== %s ===" % ad))
            ent = await self._kanal_bul(link)
            if ent is None:
                self.q.put(("adim", i + 1))
                continue
            klasor = os.path.join(hedef_kok, ad)
            os.makedirs(klasor, exist_ok=True)
            indi = atlandi = 0
            try:
                async for msg in self.client.iter_messages(ent):
                    if self.dur:
                        break
                    if not msg.media or isinstance(msg.media, MessageMediaPhoto):
                        continue
                    if not isinstance(msg.media, MessageMediaDocument):
                        continue
                    yol = os.path.join(klasor, "%06d_%s" % (msg.id, dosya_adi(msg)))
                    if os.path.exists(yol) and os.path.getsize(yol) > 0:
                        atlandi += 1
                        continue
                    for _ in range(3):
                        try:
                            await self.client.download_media(msg, file=yol)
                            indi += 1
                            toplam += 1
                            break
                        except FloodWaitError as e:
                            await asyncio.sleep(e.seconds + 2)
                        except Exception:
                            await asyncio.sleep(3)
                    if (indi + atlandi) % 10 == 0:
                        self.q.put(("durum", "%s — %d yeni / %d mevcut" % (ad, indi, atlandi)))
            except Exception as e:
                self.q.put(("log", "  liste hatası: %s" % type(e).__name__))
            self.q.put(("log", "  %d yeni dosya, %d zaten vardı" % (indi, atlandi)))
            self.q.put(("adim", i + 1))
            await asyncio.sleep(6)
        self.q.put(("durum", "Bitti — bu oturumda %d dosya indirildi" % toplam))
        self.q.put(("log", "TAMAM. Klasör: %s" % hedef_kok))


if __name__ == "__main__":
    Sihirbaz().mainloop()
