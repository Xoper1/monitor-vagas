from datetime import datetime, timezone, timedelta
import json
from pathlib import Path

from core.notifier import TelegramNotifier
from scrapers.base import Vaga
from scrapers.copeve_ufal import CopeveUfalScraper

ARQUIVO_VAGAS = Path("docs/vagas.json")
TZ_BR = timezone(timedelta(hours=-3))


def carregar_base_existente() -> dict:
    if not ARQUIVO_VAGAS.exists():
        return {"atualizado_em": None, "total": 0, "vagas": []}

    raw_text = ARQUIVO_VAGAS.read_text(encoding="utf-8").strip()
    if not raw_text:
        return {"atualizado_em": None, "total": 0, "vagas": []}

    try:
        data = json.loads(raw_text)
        if isinstance(data, dict) and isinstance(data.get("vagas"), list):
            return data
    except json.JSONDecodeError:
        pass

    return {"atualizado_em": None, "total": 0, "vagas": []}


def salvar_base(vagas_dict: list[dict], agora_iso: str) -> None:
    ARQUIVO_VAGAS.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "atualizado_em": agora_iso,
        "total": len(vagas_dict),
        "vagas": vagas_dict,
    }
    ARQUIVO_VAGAS.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def executar() -> None:
    agora = datetime.now(TZ_BR)
    agora_iso = agora.isoformat()

    base_anterior = carregar_base_existente()
    vagas_anteriores: list[dict] = base_anterior.get("vagas", [])
    ids_conhecidos = {item.get("id") for item in vagas_anteriores if item.get("id")}
    primeira_execucao_vazia = len(vagas_anteriores) == 0

    scrapers = [
        CopeveUfalScraper(),
    ]

    coletadas: list[Vaga] = []
    for scraper in scrapers:
        try:
            itens = scraper.coletar()
            for item in itens:
                if not item.data_coleta:
                    item.data_coleta = agora_iso
            print(f"[{scraper.nome_fonte}] Coletados: {len(itens)}")
            coletadas.extend(itens)
        except Exception as exc:
            print(f"[ERRO - {scraper.nome_fonte}] {exc}")

    novas_vagas: list[Vaga] = []
    mapa_vagas: dict[str, dict] = {}

    for item in coletadas:
        d = item.to_dict()
        mapa_vagas[d["id"]] = d
        if d["id"] not in ids_conhecidos:
            novas_vagas.append(item)

    # Mantém vagas anteriores que ainda não foram substituídas pelo mesmo ID
    for antiga in vagas_anteriores:
        antiga_id = antiga.get("id")
        if antiga_id and antiga_id not in mapa_vagas:
            mapa_vagas[antiga_id] = antiga

    lista_final = list(mapa_vagas.values())
    salvar_base(lista_final, agora_iso)
    print(f"Total na base ({ARQUIVO_VAGAS}): {len(lista_final)} | Novas: {len(novas_vagas)}")

    notifier = TelegramNotifier()
    if novas_vagas:
        enviadas = notifier.notificar_vagas(novas_vagas)
        print(f"Notificações enviadas no Telegram: {enviadas}/{len(novas_vagas)}")
    elif primeira_execucao_vazia:
        notifier.enviar_mensagem(
            "🤖 <b>Monitor de Vagas ativo!</b>\n"
            f"Coleta concluída em {agora.strftime('%d/%m/%Y %H:%M')}, mas nenhuma vaga/edital foi retornado nesta rodada."
        )
    else:
        print("Nenhuma vaga nova para notificar.")


if __name__ == "__main__":
    executar()
