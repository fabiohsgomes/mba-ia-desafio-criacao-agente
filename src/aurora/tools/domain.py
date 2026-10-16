from google.adk.tools import ToolContext

from aurora.services.domain import DomainService


class DomainTools:
    def __init__(self, db):
        self.service = DomainService(db)

    async def reservar_area(self, area: str, data: str, tool_context: ToolContext) -> dict:
        """Reserva area (salao-de-festas, churrasqueira ou quadra) na data AAAA-MM-DD. Taxa exige confirmação pela API."""
        try:
            return await self.service.stage("reservar_area", {"area": area, "data": data}, tool_context)
        except ValueError:
            return {"status": "invalida", "motivo": "Confira área e data AAAA-MM-DD."}

    async def listar_minhas_reservas(self, tool_context: ToolContext) -> dict:
        """Lista somente reservas ativas do apartamento da sessão."""
        return {"reservas": await self.service.scoped(tool_context)}

    async def listar_meus_visitantes(self, tool_context: ToolContext) -> dict:
        """Lista somente visitantes autorizados pelo apartamento da sessão."""
        return {"visitantes": await self.service.scoped(tool_context, visitors=True)}

    async def consultar_disponibilidade(self, area: str, data: str, tool_context: ToolContext) -> dict:
        """Informa apenas se área/data está livre; nunca identifica a reserva existente."""
        try:
            return await self.service.availability(area, data, tool_context)
        except ValueError:
            return {"status": "invalida", "motivo": "Confira área e data AAAA-MM-DD."}

    async def cancelar_minha_reserva(self, codigo: str, tool_context: ToolContext) -> dict:
        """Cancela sem confirmação somente uma reserva própria pelo código; consulte as próprias reservas antes para resolver área/data."""
        return await self.service.stage("cancelar_minha_reserva", {"codigo": codigo}, tool_context)

    async def autorizar_visitante(self, nome: str, data: str, tool_context: ToolContext) -> dict:
        """Propõe entrada de visitante com nome e data AAAA-MM-DD. Sempre exige confirmação pela API."""
        try:
            return await self.service.stage("autorizar_visitante", {"nome": nome, "data": data}, tool_context)
        except ValueError:
            return {"status": "invalida", "motivo": "Informe nome e data AAAA-MM-DD válidos."}
