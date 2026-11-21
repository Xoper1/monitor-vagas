from dataclasses import dataclass, asdict
import hashlib


@dataclass
class Vaga:
    titulo: str
    link: str
    fonte: str
    categoria: str = "Edital / Processo Seletivo"
    data_coleta: str = ""

    @property
    def id(self) -> str:
        raw = f"{self.fonte}|{self.titulo.strip().lower()}|{self.link.strip()}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]

    def to_dict(self) -> dict:
        data = asdict(self)
        data["id"] = self.id
        return data


class BaseScraper:
    nome_fonte: str = "Fonte Desconhecida"

    def coletar(self) -> list[Vaga]:
        raise NotImplementedError("Cada scraper deve implementar o método coletar().")
