"""
Telegram bot untuk notifikasi & input cepat.
"""
from __future__ import annotations
import asyncio
from loguru import logger
from config.settings import settings

try:
    from telegram import Bot, Update
    from telegram.ext import Application, CommandHandler, ContextTypes
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False
    logger.warning("python-telegram-bot belum terinstall")


_bot_app = None


def _get_app():
    global _bot_app
    if not TELEGRAM_AVAILABLE or not settings.TELEGRAM_BOT_TOKEN:
        return None
    if _bot_app is None:
        _bot_app = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()
        _bot_app.add_handler(CommandHandler("start", _cmd_start))
        _bot_app.add_handler(CommandHandler("status", _cmd_status))
        _bot_app.add_handler(CommandHandler("lapor", _cmd_lapor))
    return _bot_app


async def _cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🌐 *SpatiaNomics Bot*\n\n"
        "Perintah:\n"
        "/status — status server\n"
        "/lapor <kode_wilayah> <kode_var> <nilai> — input laporan cepat\n"
        "\nContoh:\n"
        "`/lapor 11.01.01.2001 F-BANJIR-LOKAL 1`",
        parse_mode="Markdown",
    )


async def _cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🟢 Server SpatiaNomics online.")


async def _cmd_lapor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/lapor <kode_wilayah> <kode_var> <nilai>"""
    args = context.args
    if len(args) < 3:
        await update.message.reply_text("Format: /lapor <kode_wilayah> <kode_var> <nilai>")
        return
    kode, var, val = args[0], args[1], args[2]
    try:
        nilai = float(val)
    except ValueError:
        await update.message.reply_text("Nilai harus angka (0-1)")
        return

    # Simpan ke DB
    from server.database import SessionLocal
    from server.models import FieldObservation, CustomVariable
    db = SessionLocal()
    try:
        obs = FieldObservation(
            wilayah_kode=kode.replace(".", ""),
            variable_kode=var,
            nilai=nilai,
            observer=update.effective_user.username or "telegram",
            catatan=f"Via Telegram oleh @{update.effective_user.username}",
        )
        db.add(obs)
        db.commit()
        await update.message.reply_text(
            f"✅ Laporan tersimpan:\n"
            f"• Wilayah: {kode}\n"
            f"• Variabel: {var}\n"
            f"• Nilai: {nilai}\n"
            f"Menunggu verifikasi supervisor."
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")
    finally:
        db.close()


def notify_supervisor_new_critical(obs, var, db) -> None:
    """Kirim notifikasi ke supervisor saat ada laporan CRITICAL baru."""
    app = _get_app()
    if not app or not settings.TELEGRAM_CHAT_ID:
        logger.info(f"[SKIP Telegram] CRITICAL: {var.nama} di {obs.wilayah_kode}")
        return
    msg = (
        f"🔴 *LAPORAN CRITICAL BARU*\n\n"
        f"• Wilayah: `{obs.wilayah_kode}`\n"
        f"• Variabel: *{var.nama}*\n"
        f"• Nilai: {obs.nilai}\n"
        f"• Observer: {obs.observer}\n"
        f"• Catatan: {obs.catatan or '-'}\n\n"
        f"Segera verifikasi di dashboard supervisor."
    )
    try:
        bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
        asyncio.run(bot.send_message(
            chat_id=settings.TELEGRAM_CHAT_ID,
            text=msg,
            parse_mode="Markdown",
        ))
        logger.success(f"📤 Telegram alert terkirim: {var.nama}")
    except Exception as e:
        logger.error(f"Telegram send failed: {e}")


def run_bot():
    """Entry point untuk menjalankan bot (blocking)."""
    app = _get_app()
    if not app:
        print("❌ Telegram bot tidak tersedia (cek .env: TELEGRAM_BOT_TOKEN)")
        return
    print("🤖 SpatiaNomics Telegram bot running...")
    app.run_polling()