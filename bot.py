import asyncio
import logging
from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

# Bot API Tokenin
TOKEN = "9181601804:AAFItnKGgrRpUa95ogtFdkeiL9KhHMwObCE"

# Zorunlu Kanallar
CHANNELS = ["@swarovskiyeniden", "@swarovskihile"]

# Dosyaların bulunduğu kanal
FILE_CHANNEL = "@hilemfk"

# Bellek Veritabanı
active_users = set()  # Benzersiz kullanıcı ID'leri
total_command_count = 0  # Toplam işlem/mesaj sayısı
referrals = {}  # {user_id: davet_ettigi_kisi_sayisi}
referred_users = set()  # Daha önce biri tarafından davet edilip ödül kazandırılmış kullanıcılar

router = Router()


# Admin şifreleme state yönetimi
class AdminState(StatesGroup):
  waiting_for_password = State()


# Abonelik kontrolü
async def check_user_subscriptions(bot: Bot, user_id: int) -> bool:
  for channel in CHANNELS:
    try:
      member = await bot.get_chat_member(chat_id=channel, user_id=user_id)
      if member.status in ["left", "kicked"]:
        return False
    except Exception:
      return False
  return True


# Zorunlu kanal butonu
def get_subscribe_keyboard():
  return InlineKeyboardMarkup(
      inline_keyboard=[
          [
              InlineKeyboardButton(
                  text="📢 1. Kanalımıza Katıl", url="https://t.me/swarovskiyeniden"
              )
          ],
          [
              InlineKeyboardButton(
                  text="📢 2. Kanalımıza Katıl", url="https://t.me/swarovskihile"
              )
          ],
          [
              InlineKeyboardButton(
                  text="✅ Katıldım, Kontrol Et 🔄", callback_data="check_sub"
              )
          ],
      ]
  )


# Ana Menü - VIP Arşiv Butonları (+ Referans ve Admin Paneli)
def get_main_menu_keyboard():
  return InlineKeyboardMarkup(
      inline_keyboard=[
          [
              InlineKeyboardButton(
                  text="⚡ Standoff 2 Rootlu Sürüm 📥", callback_data="file_3"
              )
          ],
          [
              InlineKeyboardButton(
                  text="📂 Ekstra Dosya 1", callback_data="file_5"
              ),
              InlineKeyboardButton(
                  text="📂 Ekstra Dosya 2", callback_data="file_6"
              ),
          ],
          [
              InlineKeyboardButton(
                  text="📂 Ekstra Dosya 3", callback_data="file_7"
              ),
              InlineKeyboardButton(
                  text="📂 Ekstra Dosya 4", callback_data="file_8"
              ),
          ],
          [
              InlineKeyboardButton(
                  text="🛠️ Root Uygulamaları", callback_data="root_apps"
              )
          ],
          [
              InlineKeyboardButton(
                  text="🔥 Diğer Özel Hile", callback_data="other_cheat"
              )
          ],
          [
              InlineKeyboardButton(
                  text="👥 Davet Et & Kazan (Referans)", callback_data="ref_menu"
              )
          ],
          [
              InlineKeyboardButton(
                  text="🔐 Admin Paneli", callback_data="admin_panel"
              )
          ],
      ]
  )


# Geri Dönüş Butonları
def get_back_keyboard():
  return InlineKeyboardMarkup(
      inline_keyboard=[
          [
              InlineKeyboardButton(
                  text="◀️ Ana Menüye Dön", callback_data="back_to_menu"
              )
          ]
      ]
  )


# /start komutu (Referans ve üyelik kontrol mantıklı)
@router.message(Command("start", "menu"))
async def cmd_start(message: Message, bot: Bot, state: FSMContext):
  global total_command_count
  await state.clear()

  user_id = message.from_user.id
  active_users.add(user_id)
  total_command_count += 1

  # Komuttan gelen referans parametresini yakala (Örn: /start ref_12345678)
  args = message.text.split()
  if len(args) > 1 and args[1].startswith("ref_"):
    try:
      referrer_id = int(args[1].split("_")[1])
      # Kendini davet edemez ve daha önce başka bir referansla kayıt olmamış olmalı
      if referrer_id != user_id and user_id not in referred_users:
        # Kullanıcının kanallara katılıp katılamadığını kontrol etmeden önce
        # önce kanallarda mi diye bakıyoruz veya kanallara katıldıktan sonra sayılması için
        # kullanıcının kanallarda olması şartını arıyoruz:
        if await check_user_subscriptions(bot, user_id):
          referred_users.add(user_id)
          referrals[referrer_id] = referrals.get(referrer_id, 0) + 1
          # Davet edene bildirim gönder
          try:
            await bot.send_message(
                referrer_id,
                "🎉 **Tebrikler!** Davet ettiğin bir arkadaşın kanallara katıldı"
                " ve referansın başarıyla eklendi! 🚀",
            )
          except Exception:
            pass
    except Exception:
      pass

  # Üyelik kontrolü
  is_subscribed = await check_user_subscriptions(bot, user_id)

  if not is_subscribed:
    await message.answer(
        "⚠️ **DİKKAT! Botu Kullanabilmek İçin Şartlar Var** ⚠️\n\n"
        "Botumuzdaki tüm hile ve dosyalara ücretsiz ulaşabilmek için "
        "lütfen aşağıdaki kanallarımıza abone ol! 🚀",
        reply_markup=get_subscribe_keyboard(),
        parse_mode="Markdown",
    )
    return

  await message.answer(
      "🔥 **SWAROVSKI VIP ARŞİV PANELİNE HOŞ GELDİN** 🔥\n\n"
      "👑 *İstediğin dosyayı veya hileyi aşağıdaki kategorilerden seçebilirsin:* 👇",
      reply_markup=get_main_menu_keyboard(),
      parse_mode="Markdown",
  )


# Üyelik kontrol butonu (Burada da referans tetiklenebilir)
@router.callback_query(F.data == "check_sub")
async def verify_subscription(
    callback: CallbackQuery, bot: Bot, state: FSMContext
):
  await state.clear()
  user_id = callback.from_user.id
  active_users.add(user_id)

  is_subscribed = await check_user_subscriptions(bot, user_id)

  if not is_subscribed:
    await callback.answer(
        "❌ Hey! Hala kanalların hepsine katılmamışsın!", show_alert=True
    )
    return

  await callback.answer("🎉 Üyeliğin onaylandı!")
  await callback.message.edit_text(
      "👑 **Tebrikler, Erişim Onaylandı!** 👑\n\n"
      "🚀 *VIP Arşivi aşağıdan seçebilirsin:* 👇",
      reply_markup=get_main_menu_keyboard(),
      parse_mode="Markdown",
  )


# Referans Menüsü
@router.callback_query(F.data == "ref_menu")
async def ref_menu_handler(callback: CallbackQuery, bot: Bot):
  user_id = callback.from_user.id
  bot_info = await bot.get_me()
  bot_username = bot_info.username

  user_ref_count = referrals.get(user_id, 0)
  ref_link = f"https://t.me/{bot_username}?start=ref_{user_id}"

  text = (
      f"👥 **DAVET ET & KAZAN (REFERANS SİSTEMİ)** 👥\n\n"
      f"🔗 *Senin Kişisel Davet Linkin:*\n`{ref_link}`\n\n"
      f"📊 **Toplam Davet Ettiğin Kişi:** `{user_ref_count}` kişi\n\n"
      "💡 *Nasıl Çalışır?*\n"
      "Yukarıdaki linki arkadaşlarına veya Telegram gruplarına gönder. "
      "Linkine tıklayıp bota start veren ve kanallarımıza katılan her arkadaşın "
      "saymana eklenir!"
  )
  await callback.message.edit_text(
      text, reply_markup=get_back_keyboard(), parse_mode="Markdown"
  )


# Ana Menüye Dönüş
@router.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: CallbackQuery, bot: Bot, state: FSMContext):
  await state.clear()
  await callback.message.edit_text(
      "🔥 **SWAROVSKI VIP ARŞİV PANELİ** 🔥\n\n"
      "👑 *İstediğin dosyayı veya hileyi aşağıdaki kategorilerden seçebilirsin:* 👇",
      reply_markup=get_main_menu_keyboard(),
      parse_mode="Markdown",
  )


# Admin Paneline Tıklandığında Şifre İste
@router.callback_query(F.data == "admin_panel")
async def admin_panel_click(callback: CallbackQuery, state: FSMContext):
  await callback.answer()
  await state.set_state(AdminState.waiting_for_password)
  await callback.message.edit_text(
      "🔐 **YÖNETİCİ GİRİŞİ** 🔐\n\n"
      "Lütfen admin paneline erişmek için **şifreyi** yazıp gönder:",
      reply_markup=get_back_keyboard(),
      parse_mode="Markdown",
  )


# Şifre Kontrolü
@router.message(AdminState.waiting_for_password)
async def check_admin_password(message: Message, state: FSMContext):
  entered_password = message.text.strip()

  if entered_password == "efe01":
    await state.clear()
    user_count = len(active_users)

    stats_text = (
        f"👑 **SWAROVSKI ADMIN PANELİ** 👑\n\n"
        f"📊 **Bot İstatistikleri:**\n"
        f"👥 Toplam Kullanıcı Sayısı: `{user_count}` kişi\n"
        f"💬 Toplam Etkileşim / Komut: `{total_command_count}` kez\n"
        f"🔗 Toplam Kayıtlı Referans İşlemi: `{len(referred_users)}` kişi\n\n"
        f"🟢 *Sistem Durumu: Sorunsuz Çalışıyor (Render)*"
    )
    await message.answer(
        stats_text,
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="◀️ Ana Menüye Dön", callback_data="back_to_menu"
                    )
                ]
            ]
        ),
        parse_mode="Markdown",
    )
  else:
    await message.answer(
        "❌ **Yanlış Şifre!**\n\nTekrar deneyebilir veya vazgeçebilirsin.",
        reply_markup=get_back_keyboard(),
        parse_mode="Markdown",
    )


# Genel Dosya Gönderme Fonksiyonu
async def send_file_from_channel(callback: CallbackQuery, bot: Bot, msg_id: int):
  global total_command_count
  total_command_count += 1
  active_users.add(callback.from_user.id)

  if not await check_user_subscriptions(bot, callback.from_user.id):
    await callback.answer(
        "⚠️ İşlem iptal! Önce kanallara katılman gerekiyor.", show_alert=True
    )
    return

  await callback.answer("📦 Dosya kanaldan çekiliyor, beklemede kal...")

  try:
    await bot.copy_message(
        chat_id=callback.message.chat.id,
        from_chat_id=FILE_CHANNEL,
        message_id=msg_id,
    )
  except Exception as e:
    await callback.message.answer(
        "⚠️ Dosya gönderilirken bir hata oluştu! "
        "Yöneticinin kanaldaki mesaj ID'sini doğru ayarladığından emin ol.",
        parse_mode="Markdown",
    )


# Butonların Dosya Eşleştirmeleri
@router.callback_query(F.data.in_(["file_3", "file_5", "file_6", "file_7", "file_8"]))
async def send_indexed_files(callback: CallbackQuery, bot: Bot):
  msg_id = int(callback.data.split("_")[1])
  await send_file_from_channel(callback, bot, msg_id)


# Root uygulamaları ve diğer hile için
@router.callback_query(F.data == "root_apps")
async def root_apps_handler(callback: CallbackQuery, bot: Bot):
  await callback.answer(
      "🛠️ Root uygulamaları yakında eklenecek!", show_alert=True
  )


@router.callback_query(F.data == "other_cheat")
async def other_cheat_handler(callback: CallbackQuery, bot: Bot):
  await callback.answer(
      "🔥 Diğer özel hile yakında eklenecek!", show_alert=True
  )


async def main():
  bot = Bot(token=TOKEN)
  dp = Dispatcher(storage=MemoryStorage())
  dp.include_router(router)

  print("Referans ve Admin destekli bot aktif ve çalışıyor...")
  await dp.start_polling(bot)


if __name__ == "__main__":
  logging.basicConfig(level=logging.INFO)
  asyncio.run(main())
    
