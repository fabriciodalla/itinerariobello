from enum import Enum


class PerfilUsuario(str, Enum):
    motorista = "motorista"
    supervisor = "supervisor"
    analista = "analista"
    admin = "admin"


class TipoVeiculo(str, Enum):
    proprio = "proprio"
    alugado = "alugado"
    empresa = "empresa"


class TipoDisponibilidadeVeiculo(str, Enum):
    fixo = "fixo"
    alocado = "alocado"


class StatusViagem(str, Enum):
    em_andamento = "em_andamento"
    concluida = "concluida"


class TipoFotoHodometro(str, Enum):
    inicial = "inicial"
    final = "final"


class TipoLocalizacaoGPS(str, Enum):
    partida = "partida"
    chegada = "chegada"


class AcaoAprovacao(str, Enum):
    aprovar = "aprovar"
    reprovar = "reprovar"
    solicitar_ajuste = "solicitar_ajuste"


class StatusFechamentoMensal(str, Enum):
    aberto = "aberto"
    fechado = "fechado"


def enum_values(enum_cls: type[Enum]) -> list[str]:
    return [item.value for item in enum_cls]
