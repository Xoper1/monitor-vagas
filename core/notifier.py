import os
import requests
from scrapers.base import Vaga


class TelegramNotifier:
    def __init__(self):
        self.token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()

    @property
    def configurado(self) -> bool:
        return bool(self.token and self.chat_id)

    def enviar_mensagem(self, texto: str) -> bool:
        if not self.configurado:
            print("[AVISO - Telegram] TELEGRAM_BOT_TOKEN ou TELEGRAM_CHAT_ID não configurados.")
            return False

        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": texto,
            "parse_mode": "HTML",
            "disable_web_page_preview": False,
        }

        try:
            resp = requests.post(url, json=payload, timeout=15)
            if resp.status_code != 200:
                print(f"[ERRO - Telegram] HTTP {resp.status_code}: {resp.text}")
                return False
            return True
        except Exception as exc:
            print(f"[ERRO - Telegram] Falha ao enviar mensagem: {exc}")
            return False

    def notificar_vagas(self, vagas: list[Vaga]) -> int:
        if not vagas:
            return 0

        enviadas = 0
        for vaga in vagas:
            mensagem = (
                f"📢 <b>Nova publicação — {vaga.fonte}</b>\n"
                f"📌 <b>Título:</b> {vaga.titulo}\n"
                f"🗂️ <b>Categoria:</b> {vaga.categoria}\n"
                f"🔗 <a href=\"{vaga.link}\">Acessar edital / página</a>"
            )
            if self.enviar_mensagem(mensagem):
                enviadas += 1
        return enviadas
