"""Índice local fora do histórico; só o artigo selecionado atravessa a tool."""
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path

from aurora.observability import emit


def normalize(text: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", text.lower()) if unicodedata.category(c) != "Mn")


STOP = set("a o as os de do da dos das e em no na nos nas um uma para por com que qual quais como sobre ate aos ao se eu meu minha posso pode sao tem ser funciona funcionamento uso usar regra regras horario horarios horas hora assunto condominio residencial aurora".split())
ALIASES = {
    "IV": ("piscina", "natacao", "nadar"),
    "V": ("academia", "brinquedoteca", "playground"),
    "VI": ("salao", "churrasqueira", "quadra", "reserva", "reservar"),
    "VII": ("portaria", "seguranca", "visitante", "visitantes", "entrega", "entregas", "encomenda"),
    "VIII": ("animal", "animais", "cachorro", "gato", "pet"),
    "IX": ("mudanca", "mudancas"),
    "X": ("obra", "obras", "reforma", "reformas"),
    "XI": ("garagem", "veiculo", "veiculos", "vaga", "carro", "moto"),
    "XII": ("lixo", "reciclagem", "coleta", "residuos"),
    "XIII": ("infracao", "infracoes", "penalidade", "penalidades", "multa", "multas"),
    "III": ("silencio", "barulho", "ruido", "sossego", "convivencia"),
    "II": ("direitos", "deveres"),
}


@dataclass(frozen=True)
class Article:
    chapter: str
    numeral: str
    number: str
    text: str


class RegulationSearch:
    def __init__(self, path: Path):
        text = path.read_text(encoding="utf-8")
        self.articles = []
        for section in re.split(r"(?m)(?=^## Capítulo )", text):
            header = re.match(r"## (Capítulo ([IVXLC]+):[^\n]+)", section)
            if not header:
                continue
            for match in re.finditer(r"(?ms)^\*\*Art\. (\d+)[^\n]*.*?(?=^\*\*Art\.|\Z)", section):
                self.articles.append(Article(header[1], header[2], match[1], match[0].strip()))
        if not self.articles:
            raise ValueError("Regulamento sem artigos reconhecíveis")

    async def buscar_regulamento(self, pergunta: str) -> dict:
        """Retorna artigos completos pertinentes ao assunto explícito. Sem assunto claro, pede esclarecimento."""
        question = normalize(pergunta)
        words = set(re.findall(r"[a-z0-9]+", question))
        subjects = [chapter for chapter, aliases in ALIASES.items() if words.intersection(aliases)]
        if not subjects:
            emit("regulation.lookup", outcome="ambiguo")
            return {"status": "esclarecer", "trechos": [], "orientacao": "Especifique o assunto e a dúvida sobre o regulamento."}
        selected = []
        for chapter in subjects:
            terms = words - STOP - set(ALIASES[chapter])
            scores = []
            for article in self.articles:
                if article.numeral != chapter:
                    continue
                content = normalize(article.text)
                tokens = set(re.findall(r"[a-z0-9]+", content))
                score = len(tokens & terms)
                if words & {"horario", "horarios", "hora", "horas", "funciona", "funcionamento", "fecha", "abre", "abertura", "fechamento"}:
                    score += 4 * bool(re.search(r"\b\d{1,2}h\b", content))
                if words & {"domingo", "domingos"} and "domingos" in content:
                    score += 4
                scores.append((score, article))
            if not scores:
                continue
            best = max(score for score, _ in scores)
            winners = [a for score, a in scores if score == best and best > 0]
            if len(winners) == 1:
                selected.append(winners[0])
        if not selected:
            emit("regulation.lookup", outcome="sem_resultado")
            return {"status": "esclarecer", "trechos": [], "orientacao": "Especifique qual regra deseja consultar nesse assunto."}
        emit("regulation.lookup", outcome="encontrado")
        return {"status": "encontrado", "trechos": [
            {"fonte": "dados/regulamento.md", "capitulo": a.chapter, "artigo": a.number, "texto": a.text} for a in selected]}
