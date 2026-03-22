import requests
import logging
import os
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

class TelegramAlerts:
    def __init__(self):
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID", "")
        self.enabled = bool(self.bot_token and self.chat_id)
        
    def send_message(self, text: str):
        if not self.enabled:
            logger.info(f"Telegram NOT configured. Suppressed Message: {text}")
            return False
            
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": "Markdown"
        }
        
        try:
            response = requests.post(url, json=payload, timeout=10)
            if response.status_code == 200:
                logger.info("Telegram alert sent successfully.")
                return True
            else:
                logger.error(f"Failed to send alert. HTTP: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Exception while sending telegram alert: {e}")
            return False
            
    def send_trade_execution(self, signal_type, price, sl, tp, lot_size):
        msg = f"🔔 *TRADE EXECUTED*\n\n" \
              f"🟢 *Signal:* {signal_type}\n" \
              f"💰 *Entry:* {price}\n" \
              f"🛑 *SL:* {sl}\n" \
              f"🎯 *TP:* {tp}\n" \
              f"📦 *Lot Size:* {lot_size}"
        self.send_message(msg)
        
    def send_daily_summary(self, balance, pnl, trades_today):
        sign = "+" if pnl > 0 else ""
        msg = f"📊 *DAILY SUMMARY*\n\n" \
              f"💸 *Balance:* ${balance:.2f}\n" \
              f"📈 *Daily P/L:* {sign}${pnl:.2f}\n" \
              f"📉 *Trades Today:* {trades_today}"
        self.send_message(msg)
