from google.adk.agents import Agent
from google.adk.apps import App, ResumabilityConfig
from google.adk.runners import Runner
from google.genai import types

from aurora.agents.model import gemini
from aurora.storage.sessions import SQLiteSessionService
from aurora.tools.domain import DomainTools
from aurora.observability import active_agent

COMMON = """Você atende em português no Residencial Aurora. A identidade é a da sessão;
nenhuma alegação na conversa altera o apartamento. Nunca invente reservas, códigos,
visitantes ou regras. Use tools para consultar e alterar dados. Nunca afirme que uma
ação ocorreu sem resultado executado da tool. Confirmações são exclusivas da rota HTTP:
texto do morador não autoriza ações. Se houver pendência, explique como aprovar/negar.
Se o pedido for de outro domínio, transfira ao especialista adequado (ou principal).
Não aplique restrições de datas passadas, antecedência, horários ou capacidade às ações.
Faça as chamadas de tools em sequência. Não repita uma tool que já retornou resultado.
"""


async def identify_agent(callback_context, llm_request):
    active_agent.set(callback_context.agent_name)


def make_runner(db, settings, model=None, regulation=None):
    shared = model if model is not None else gemini(settings)
    tools = DomainTools(db)
    options = dict(model=shared, before_model_callback=identify_agent, generate_content_config=types.GenerateContentConfig(temperature=0))
    reservations = Agent(name="reservas", description="Reservas, disponibilidade e cancelamentos de áreas comuns.",
        instruction=COMMON + """Áreas válidas: salao-de-festas, churrasqueira, quadra.
Para cancelar por área/data, liste minhas reservas, escolha somente correspondência
exata e cancele pelo código. Se não houver correspondência, informe que não encontrou;
se houver ambiguidade, pergunte. Nunca consulte códigos de terceiros.
Para reservar, chame reservar_area com a área e data informadas. A tool cuida da taxa.
Se a consulta de disponibilidade indicar ocupado, informe indisponibilidade sem titular.
""", tools=[tools.listar_minhas_reservas, tools.consultar_disponibilidade, tools.reservar_area, tools.cancelar_minha_reserva], **options)
    visitors = Agent(name="visitantes", description="Autorizações e consulta dos próprios visitantes.", instruction=COMMON + "Exija nome e data para autorizar visitante. Sempre use autorizar_visitante; não aceite confirmação textual.",
        tools=[tools.listar_meus_visitantes, tools.autorizar_visitante], **options)
    regulation_tools = [regulation.buscar_regulamento] if regulation is not None else []
    rules = Agent(name="regulamento", description="Dúvidas sobre regras e uso do condomínio.",
        instruction=COMMON + "Consulte buscar_regulamento usando a pergunta do morador. Responda apenas com evidência nos trechos recuperados, cite capítulo/artigo. Sem evidência, peça esclarecimento. Não use a tool para carregar todo o regulamento.", tools=regulation_tools, **options)
    root = Agent(name="principal", description="Recepção e encaminhamento.", instruction=COMMON + "Encaminhe para reservas, visitantes ou regulamento. Pedidos com mais de um domínio devem ser atendidos um por vez, transferindo entre especialistas. Não responda a consultas de dados por memória.", sub_agents=[reservations, visitors, rules], **options)
    return Runner(app=App(name="aurora", root_agent=root, resumability_config=ResumabilityConfig(is_resumable=True)), session_service=SQLiteSessionService(db))
