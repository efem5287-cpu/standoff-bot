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

# Zorunlu Katılınması Gereken 3 Kanal
CHANNELS = ["@swarovskiyeniden", "@swarovskihile", "@hilemfk"]

# Dosyaların bulunduğu kanal
FILE_CHANNEL = "@hilemfk"

# Bellek Veritabanı
active_users = set()  # Benzersiz kullanıcılar
total_command_count = 0  # Toplam işlem/mesaj
referrals = {}  # {user_id: davet_sayisi}
referred_users = set()  # Zaten referansla kaydı düşülenler

router = Router()


# Admin şifreleme state yönetimi
class AdminState(StatesGroup):
  waiting_for_password = State()


# Abonelik kontrolü (3 kanal için)
async def check_user_subscriptions(bot: Bot, user_id: int) -> bool:
  for channel in CHANNELS:
    try:
      member = await bot.get_chat_member(chat_id=channel, user_id=user_id)
      if member.status in ["left", "kicked"]:
        return False
    except Exception:
      return False
  return True


# Zorunlu kanal butonları (3 kanal)
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
                  text="📢 3. Kanalımıza Katıl (Depo)",
                  url="https://t.me/hilemfk",
              )
          ],
          [
              InlineKeyboardButton(
                  text="✅ Hepsine Katıldım, Kontrol Et 🔄",
                  callback_data="check_sub",
              )
          ],
      ]
  )


# Ana Menü - VIP Arşiv ve Diğer Butonlar
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
                  text="🔥 Neptunium Hilesi", callback_data="other_cheat"
              )
          ],
          [
              InlineKeyboardButton(
                  text="🎮 Eğlence Menüsü (Mini Oyunlar)",
                  callback_data="fun_menu",
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


# Geri Dönüş Butonu
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


# Eğlence Menüsü Butonları
def get_fun_menu_keyboard():
  return InlineKeyboardMarkup(
      inline_keyboard=[
          [
              InlineKeyboardButton(
                  text="🎲 Zar At", callback_data="fun_dice"
              ),
              InlineKeyboardButton(
                  text="🎯 Şansını Dene", callback_data="fun_luck"
              ),
          ],
          [
              InlineKeyboardButton(
                  text="🤖 Botun Sırrı Ne?", callback_data="fun_secret"
              )
          ],
          [
              InlineKeyboardButton(
                  text="◀️ Ana Menüye Dön", callback_data="back_to_menu"
              )
          ],
      ]
  )


# /start komutu ve Referans Kontrolü
@router.message(Command("start", "menu"))
async def cmd_start(message: Message, bot: Bot, state: FSMContext):
  global total_command_count
  await state.clear()

  user_id = message.from_user.id
  active_users.add(user_id)
  total_command_count += 1

  # Referans argümanını yakala
  args = message.text.split()
  pending_referrer = None
  if len(args) > 1 and args[1].startswith("ref_"):
    try:
      referrer_id = int(args[1].split("_")[1])
      if referrer_id != user_id:
        pending_referrer = referrer_id
    except Exception:
      pass

  # Üyelik kontrolü
  is_subscribed = await check_user_subscriptions(bot, user_id)

  if not is_subscribed:
    text = (
        "⚠️ **DİKKAT! Botu Kullanabilmek İçin Şartlar Var** ⚠️\n\n"
        "Botumuzdaki tüm hile dosyalarına ve özelliklere ulaşabilmek için "
        "aşağıdaki **3 kanalımıza da** eksiksiz abone olman gerekiyor! 🚀\n\n"
    )
    if pending_referrer:
      text += (
          f"💡 *Not:* Bir arkadaşının davet linkiyle geldin! Kanallara katıldıktan"
          f" sonra referansı geçerli sayılacak."
      )

    # State içine bekleyen referansı kaydedebiliriz veya kontrol butonunda işleyebiliriz
    await state.update_data(pending_referrer=pending_referrer)

    await message.answer(
        text, reply_markup=get_subscribe_keyboard(), parse_mode="Markdown"
    )
    return

  # Eğer zaten kanallardaysa ve referansla geldiyse hemen işle
  if pending_referrer and user_id not in referred_users:
    referred_users.add(user_id)
    referrals[pending_referrer] = referrals.get(pending_referrer, 0) + 1
    try:
      await bot.send_message(
          pending_referrer,
          "🎉 **Harika!** Davet ettiğin bir arkadaşın kanallara katıldı ve"
          " botu başlattı. Referansın başarıyla işlendi! 🚀",
      )
    except Exception:
      pass

  await message.answer(
      "🔥 **SWAROVSKI VIP ARŞİV PANELİNE HOŞ GELDİN** 🔥\n\n"
      "👑 *İstediğin dosyayı veya hileyi aşağıdaki kategorilerden seçebilirsin:* 👇",
      reply_markup=get_main_menu_keyboard(),
      parse_mode="Markdown",
  )


# Üyelik Kontrol Butonu
@router.callback_query(F.data == "check_sub")
async def verify_subscription(
    callback: CallbackQuery, bot: Bot, state: FSMContext
):
  user_id = callback.from_user.id
  active_users.add(user_id)

  is_subscribed = await check_user_subscriptions(bot, user_id)

  if not is_subscribed:
    await callback.answer(
        "❌ Hey! Hala 3 kanalın hepsine katılmamışsın gözden kaçmış olmasın?",
        show_alert=True,
    )
    return

  # Kullanıcı katıldıysa, state'deki bekleyen referansı kontrol et
  data = await state.get_data()
  pending_referrer = data.get("pending_referrer")
  if pending_referrer and user_id not in referred_users:
    referred_users.add(user_id)
    referrals[pending_referrer] = referrals.get(pending_referrer, 0) + 1
    try:
      await bot.send_message(
          pending_referrer,
          "🎉 **Harika!** Davet ettiğin bir arkadaşın kanallara katıldı ve"
          " botu onayladı. Referansın başarıyla işlendi! 🚀",
      )
    except Exception:
      pass

  await state.clear()
  await callback.answer("🎉 Tüm üyeliklerin onaylandı!")
  await callback.message.edit_text(
      "👑 **Tebrikler, Erişim Onaylandı!** 👑\n\n"
      "🚀 *VIP Arşivi aşağıdan seçebilirsin:* 👇",
      reply_markup=get_main_menu_keyboard(),
      parse_mode="Markdown",
  )


# Eğlence Menüsü Handler
@router.callback_query(F.data == "fun_menu")
async def fun_menu_handler(callback: CallbackQuery):
  await callback.message.edit_text(
      "🎮 **EĞLENCE & MİNİ OYUNLAR MENÜSÜ** 🎮\n\n"
      "*Hilelerden sıkıldın mı? Biraz kafanı dağıtmak için aşağıdaki seçenekleri"
      " kullanabilirsin:* 👇",
      reply_markup=get_fun_menu_keyboard(),
      parse_mode="Markdown",
  )


@router.callback_query(F.data == "fun_dice")
async def fun_dice(callback: CallbackQuery, bot: Bot):
  await callback.answer("🎲 Zar atılıyor...")
  await bot.send_dice(chat_id=callback.message.chat.id)


@router.callback_query(F.data == "fun_luck")
async def fun_luck(callback: CallbackQuery):
  await callback.answer(
      "🍀 Şanslı Gününtesin! Bugün Standoff 2 maçlarında rank"
      " atlayacaksın!",
      show_alert=True,
  )


@router.callback_query(F.data == "fun_secret")
async def fun_secret(callback: CallbackQuery):
  await callback.answer(
      "🤖 Bu bot tamamen Swarovski güvencesiyle efsane kodlandı!",
      show_alert=True,
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
      "Bu linki arkadaşlarına at. Arkadaşın linke basıp botu başlatarak 3"
      " kanalımıza da katıldığında referansın anında geçerli sayılır!"
  )
  await callback.message.edit_text(
      text, reply_markup=get_back_keyboard(), parse_mode="Markdown"
  )


# Ana Menüye Dönüş
@router.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: CallbackQuery, state: FSMContext):
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
        f"🔗 Toplam Başarılı Referans: `{len(referred_users)}` kişi\n\n"
        f"🟢 *Sistem Durumu: Sorunsuz Çalışıyor (Stabil)*"
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
        "⚠️ İşlem iptal! Önce 3 kanalımızın hepsine katılman gerekiyor.",
        show_alert=True,
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


# Butonların Dosya Eşleştirmeleri (Ekstra Dosyalar ve Rootlu)
@router.callback_query(F.data.in_(["file_3", "file_5", "file_6", "file_7", "file_8"]))
async def send_indexed_files(callback: CallbackQuery, bot: Bot):
  msg_id = int(callback.data.split("_")[1])
  await send_file_from_channel(callback, bot, msg_id)


# Root uygulamaları için
@router.callback_query(F.data == "root_apps")
async def root_apps_handler(callback: CallbackQuery, bot: Bot):
  await callback.answer(
      "🛠️ Root uygulamaları yakında eklenecek!", show_alert=True
  )


# Neptunium Hilesi (Diğer Özel Hile Butonu)
@router.callback_query(F.data == "other_cheat")
async def other_cheat_handler(callback: CallbackQuery, bot: Bot):
  # Eğer Neptunium hilesini de kanala attıysan ve ID'sini biliyorsan doğrudan send_file_from_channel(callback, bot, MESAJ_ID) yapabilirsin.
  # Şimdilik örnek olarak mesaj ID'si üzerinden kanaldan çektiriyoruz (Kanalda Neptunium'un olduğu mesaj ID'sini buraya yazabilirsin, örneğin 9):
  await send_file_from_channel(callback, bot, 9)


async def main():
  bot = Bot(token=TOKEN)
  dp = Dispatcher(storage=MemoryStorage())
  dp.include_router(router)

  print("Tüm özellikler aktif, stabil bot çalışıyor...")
  await dp.start_polling(bot)


if __name__ == "__main__":
  logging.basicConfig(level=logging.INFO)
  asyncio.run(main())
      
