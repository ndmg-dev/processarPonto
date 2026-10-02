from app.models.schemas import PointStatus

# Códigos de ocorrência do layout "Acesso Relógio de Ponto Digital v.4.5.153" —
# aparecem NO LUGAR de uma marcação de horário, dentro de uma célula de
# período (extra/1º/2º/extra), nunca "por dia inteiro" como um campo à parte.
OCORRENCIAS = {"DOM", "SAB", "FERD", "MEDIC", "FALTA"}


def classify_day(record: dict) -> PointStatus:
    """Classifica o dia usando horas_trab/horas_desc e os códigos de
    ocorrência presentes nas células — nunca a contagem de tokens, que varia
    demais entre os casos reais (ocorrência parcial, batida isolada em dia de
    falta, etc.). Ver §2.4 de reestruturacao-processar-ponto.md."""
    quadro = record.get("quadro") or []
    ocorrencias = set(record.get("ocorrencias", {}).values())
    horas_trab = record.get("horas_trab_min", 0)
    horas_desc = record.get("horas_desc_min", 0)

    # O quadro (jornada prevista) vem como "DOM"/"SAB" quando o dia não tem
    # expediente esperado — isso é o que define Domingo/Sábado, não o rótulo
    # de dia da semana (Seg/Ter/...), que aparece sempre.
    primeiro_quadro = quadro[0] if quadro else ""
    if primeiro_quadro == "DOM":
        return PointStatus.DOMINGO
    if primeiro_quadro == "SAB":
        return PointStatus.SABADO

    if "FERD" in ocorrencias:
        return PointStatus.FERIADO
    if "MEDIC" in ocorrencias:
        return PointStatus.ATESTADO_PARCIAL if horas_trab > 0 else PointStatus.ATESTADO_INTEGRAL
    if "FALTA" in ocorrencias:
        return PointStatus.FALTA_PARCIAL if horas_trab > 0 else PointStatus.FALTA_INTEGRAL

    n_marcacoes = record.get("n_marcacoes", 0)
    if n_marcacoes % 2 == 1:
        return PointStatus.MARCACAO_IMPAR

    return PointStatus.TRABALHADO
