# Uzdem Ders İndirici

Telegram'daki 20 ders kanalındaki bütün medyayı (video / ses / doküman) tek programla, kendi bilgisayarına indiren basit bir Windows uygulaması.

## İndir

Son sürümü [Releases](../../releases/latest) sayfasından indir: **`UzdemIndirici.exe`**

Ek kurulum gerekmez — Python, Telethon vb. her şey `.exe` içine gömülüdür. İndirdikten sonra çift tıkla.

> Windows SmartScreen uyarısı çıkarsa: **Ek bilgi → Yine de çalıştır**. (İmzasız derleme olduğu için normaldir.)

## Kullanım — 4 adım

1. **API bilgileri** — [my.telegram.org](https://my.telegram.org) → telefon numaranla gir → *API development tools* → uygulama oluştur → `api_id` ve `api_hash` değerlerini programa yapıştır.
   - URL alanına `https://example.com` yazabilirsin.
2. **Telefon doğrulaması** — numaranı gir, *Kod Gönder*'e bas, Telegram'a gelen kodu yaz. (İki adımlı doğrulama açıksa şifresini de gir.) Bu işlem bir kez yapılır; oturum bilgisayarda saklanır.
3. **Klasör** — dosyaların ineceği yeri seç (varsayılan: `Downloads\Uzdem Dersler`).
4. **İndir** — *İndirmeyi Başlat*. Program sırayla her kanala katılıp bütün medyayı indirir.

## İndirilen kanallar

Emsile · Bina · Maksud · Avamil · İzhar · Kafiye · Nuru'l İzah · Kuduri Şerif · İsagoci · Metn-i Akaid · Emali · Menar · Alaka · Telhis · Aşr-ı Şerifler · Talim dersi · Sohbetler · Kitabet · Muhadese · Mektubat 1. cilt

## Bilmen gerekenler

- **Disk alanı:** 20 kanalın tamamı 20 GB'ı aşabilir. Başlamadan önce yer olduğundan emin ol.
- **Hız:** Telegram'ın katılım hız limiti yüzünden her kanal arasında kısa bekleme olur. Program bunu kendisi yönetir.
- **Yarıda kaldıysa:** aynı butona tekrar bas — indirilmiş dosyalar atlanır, kaldığı yerden devam eder.
- **Dosya adları:** `000123_ders-adi.mp4` biçiminde, kanaldaki mesaj sırasına göre.
- **Oturum dosyası:** `%USERPROFILE%\Documents\UzdemIndirici\oturum.session` — silinirse yeniden kod istenir. Bu dosyayı kimseyle paylaşma.

## Sorumluluk

Bu araç, kullanıcının kendi Telegram hesabıyla, üyesi olduğu kanallardaki içeriği kendi bilgisayarına indirmek için hazırlanmıştır. İndirilen içeriğin telif ve kullanım haklarına uymak kullanıcının sorumluluğundadır.
