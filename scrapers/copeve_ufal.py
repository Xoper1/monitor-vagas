from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import requests

from scrapers.base import BaseScraper, Vaga


class CopeveUfalScraper(BaseScraper):
    nome_fonte = "COPEVE/UFAL"
    URL_BASE = "https://copeve.ufal.br/"

    PALAVRAS_CHAVE = (
        "edital",
        "selecao",
        "seleção",
        "processo",
        "concurso",
        "vaga",
        "inscricao",
        "inscrição",
        "chamada",
        "resultado",
    )

    TERMOS_IGNORAR = (
        "javascript:",
        "mailto:",
        "#",
        "facebook.com",
        "instagram.com",
        "youtube.com",
        "twitter.com",
        "x.com",
    )

    def _link_relevante(self, href: str, texto: str) -> bool:
        href_lower = href.strip().lower()
        if not href_lower or any(href_lower.startswith(ign) for ign in self.TERMOS_IGNORAR):
            return False

        combinado = f"{href_lower} {texto.lower()}"
        if href_lower.endswith(".pdf"):
            return True
        return any(palavra in combinado for palavra in self.PALAVRAS_CHAVE)

    def coletar(self) -> list[Vaga]:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
        }

        resp = requests.get(self.URL_BASE, headers=headers, timeout=25)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")
        vagas: list[Vaga] = []
        links_vistos: set[str] = set()

        for tag_a in soup.find_all("a", href=True):
            href_raw = tag_a["href"].strip()
            texto = " ".join(tag_a.get_text(" ", strip=True).split())

            if not self._link_relevante(href_raw, texto):
                continue

            url_completa = urljoin(self.URL_BASE, href_raw)
            parsed = urlparse(url_completa)
            if parsed.scheme not in ("http", "https"):
                continue

            if url_completa in links_vistos:
                continue
            links_vistos.add(url_completa)

            titulo = texto if len(texto) >= 4 else parsed.path.split("/")[-1] or "Publicação COPEVE/UFAL"
            categoria = "Documento / Edital (PDF)" if url_completa.lower().endswith(".pdf") else "Processo / Edital"

            vagas.append(
                Vaga(
                    titulo=titulo[:220],
                    link=url_completa,
                    fonte=self.nome_fonte,
                    categoria=categoria,
                )
            )

        return vagas
