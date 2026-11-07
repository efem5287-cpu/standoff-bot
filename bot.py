import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import Command
from aiogram.types import (
    CallbackQuery,
    FSInputFile,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

# Bot API Tokenin
TOKEN = "9181601804:AAFItnKGgrRpUa95ogtFdkeiL9KhHMwObCE"

# Zorunlu Kanalların Kullanıcı Adları
CHANNELS = ["@swarovskiyeniden", "@swarovskihile"]

router = Router()


# Kullanıcının kanallarda olup olmadığını kontrol eden fonksiyon
async def check_user_subscriptions(bot: Bot, user_id: int) -> bool:
  for channel in CHANNELS:
    try:
      member = await bot.get_chat_member(chat_id=channel, user_id=user_id)
      if member.status in ["left", "kicked"]:
        return False
    except Exception:
      return False
  return True


# Kanallara katılım butonları (Şık ve Renkli)
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


# Ana Menü Butonları (Rootlu sürüm aktif)
def get_standoff_keyboard():
  return InlineKeyboardMarkup(
      inline_keyboard=[
          [
              InlineKeyboardButton(
                  text="⚡ Standoff 2 Rootlu Sürüm İndir 📥",
                  callback_data="send_root",
              )
          ]
      ]
  )


# /start veya /menu komutu
@router.message(Command("start", "menu"))
async def cmd_start(message: Message, bot: Bot):
  user_id = message.from_user.id

  # Önce üyelik kontrolü yap
  is_subscribed = await check_user_subscriptions(bot, user_id)

  if not is_subscribed:
    await message.answer(
        "⚠️ **DİKKAT! Botu Kullanabilmek İçin Şartlar Var** ⚠️\n\n"
        "Botumuzun hile dosyalarından ve güncellemelerinden ücretsiz "
        "faydalanabilmek için lütfen aşağıdaki kanallarımıza abone ol! 🚀\n\n"
        "✨ Kanallara katıldıktan sonra alttaki **'✅ Katıldım, Kontrol Et'** "
        "butonuna basabilirsin.",
        reply_markup=get_subscribe_keyboard(),
        parse_mode="Markdown",
    )
    return

  # Abonleyse süslü menüyü göster
  await message.answer(
      "🔥 **SWAROVSKI VIP PANELİNE HOŞ GELDİN** 🔥\n\n"
      "👑 *Aşağıdaki butona tıklayarak Standoff 2 özel sürümünü "
      "anında indirebilirsin.* 👇",
      reply_markup=get_standoff_keyboard(),
      parse_mode="Markdown",
  )


# "Katıldım, Kontrol Et" butonuna basıldığında
@router.callback_query(F.data == "check_sub")
async def verify_subscription(callback: CallbackQuery, bot: Bot):
  user_id = callback.from_user.id
  is_subscribed = await check_user_subscriptions(bot, user_id)

  if not is_subscribed:
    await callback.answer(
        "❌ Hey! Hala kanalların hepsine katılmamışsın gözden kaçtı galiba!",
        show_alert=True,
    )
    return

  await callback.answer("🎉 Üyeliğin başarıyla onaylandı!")
  await callback.message.edit_text(
      "👑 **Tebrikler, Erişim Onaylandı!** 👑\n\n"
      "🚀 *Standoff 2 özel menüsüne giriş yaptın. "
      "Aşağıdaki butondan dosyayı indirebilirsin:* 👇",
      reply_markup=get_standoff_keyboard(),
      parse_mode="Markdown",
  )


# Rootlu butonuna basıldığında dosya gönderimi
@router.callback_query(F.data == "send_root")
async def send_root_file(callback: CallbackQuery, bot: Bot):
  if not await check_user_subscriptions(bot, callback.from_user.id):
    await callback.answer(
        "⚠️ İşlem iptal! Önce kanallara katılman gerekiyor.", show_alert=True
    )
    return

  await callback.answer("📦 Dosyan hazırlanıyor, lütfen bekçi...")
  file_path = "rootlu.apk"

  if os.path.exists(file_path):
    document = FSInputFile(file_path)
    await callback.message.answer_document(
        document=document,
        caption=(
            "⚡ **Standoff 2 Rootlu Sürüm Başarıyla Gönderildi!** ⚡\n\n"
            "🎯 *İyi eğlenceler dileriz, bizi takipte kalmayı unutma!* "
            "[@swarovskihile]"
        ),
        parse_mode="Markdown",
    )
  else:
    await callback.message.answer(
        "⚠️ `rootlu.apk` dosyası sunucu klasöründe bulunamadı! "
        "Lütfen yöneticinin dosyayı yüklediğinden emin ol.",
        parse_mode="Markdown",
    )


async def main():
  bot = Bot(token=TOKEN)
  dp = Dispatcher()
  dp.include_router(router)

  print("Bot süslü tasarımıyla başarıyla başlatıldı ve çalışıyor...")
  await dp.start_polling(bot)


if __name__ == "__main__":
  logging.basicConfig(level=logging.INFO)
  asyncio.run(main())
