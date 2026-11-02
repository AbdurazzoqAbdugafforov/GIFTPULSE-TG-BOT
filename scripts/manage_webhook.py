"""Utility script to check and reset Telegram webhooks."""

import asyncio
import sys
from pathlib import Path

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from aiogram import Bot
from app.core.config import settings


async def main():
    if not settings.BOT_TOKEN:
        print("❌ Error: BOT_TOKEN is empty in .env")
        sys.exit(1)

    bot = Bot(token=settings.BOT_TOKEN)
    try:
        info = await bot.get_webhook_info()
        print("=" * 60)
        print("TELEGRAM WEBHOOK STATUS")
        print("=" * 60)
        print(f"URL: {info.url if info.url else '(None - Long-Polling mode ready)'}")
        print(f"Pending update count: {info.pending_update_count}")
        print(f"Last error: {info.last_error_message or 'None'}")
        print("=" * 60)

        if len(sys.argv) > 1 and sys.argv[1] == "--delete":
            print("\n🔄 Removing webhook from Telegram servers...")
            await bot.delete_webhook(drop_pending_updates=True)
            print("✅ Webhook deleted! Bot is now ready for local / cloud polling.")
        elif info.url:
            print("\n💡 NOTE: A webhook is currently registered.")
            print("To delete it, run: python scripts/manage_webhook.py --delete")
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
