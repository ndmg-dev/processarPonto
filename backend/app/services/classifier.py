import re
from app.models.schemas import PointStatus

def requires_second_period(schedule_code: str, schedule_map: dict, weekday: str) -> bool:
    """
    Determina se a jornada exige um segundo período (4 batidas).
    Se for sábado, ou o código de horário não estiver mapeado ou tiver apenas 2 batidas, retorna False.
    """
    if weekday.lower() == "sab" or weekday.lower() == "sáb":
        return False
        
    if schedule_code in schedule_map:
        times = schedule_map[schedule_code]
        # Se tiver 4 horários (ex: 07:00 12:00 13:00 16:00), exige segundo período
        if len(times) == 4:
            return True
        # Se tiver 2 horários (ex: 07:00 11:00), não exige
        if len(times) == 2:
            return False
            
    # Default fallback
    return True

def classify_record(record: dict, schedule_map: dict) -> dict:
    """
    Recebe um dicionário parcial e o schedule_map.
    Retorna o dicionário com o `status` classificado, além dos campos booleanos:
    `requires_second_period` e `has_missing_required_mark`.
    """
    weekday = record.get("weekday", "")
    first_entry = record.get("first_period_entry", "")
    first_exit = record.get("first_period_exit", "")
    second_entry = record.get("second_period_entry", "")
    second_exit = record.get("second_period_exit", "")
    raw_reason = record.get("reason", "")
    occurrence = record.get("occurrence", "")
    schedule_code = record.get("schedule_code", "")
    
    # Determinar se exige segundo período
    req_second = requires_second_period(schedule_code, schedule_map, weekday)
    
    # Checar falta de marcação obrigatória
    missing_mark = False
    if not first_entry or not first_exit:
        missing_mark = True
    if req_second and (not second_entry or not second_exit):
        missing_mark = True
        
    # Classificar Status com base nas palavras-chave no motivo/raw_line
    reason_upper = raw_reason.upper()
    
    if "FOL" in reason_upper or "FOLGA" in reason_upper:
        status = PointStatus.FOLGA
    elif "DOM" in reason_upper or "DOMINGO" in reason_upper:
        status = PointStatus.DOMINGO
    elif "FERIA" in reason_upper or "FÉRIAS" in reason_upper:
        status = PointStatus.FERIAS
    elif "MEDIC" in reason_upper or "ATESTADO" in reason_upper:
        status = PointStatus.ATESTADO
    elif "F.JUS" in reason_upper or "FALTA JUSTIFICADA" in reason_upper:
        status = PointStatus.FALTA_JUSTIFICADA
    elif "EXTER" in reason_upper or "SERVIÇO EXTERNO" in reason_upper:
        status = PointStatus.SERVICO_EXTERNO
    elif "FALTA DE MARCA" in reason_upper or "FALTA DE MARCAÇÃO" in reason_upper:
        if missing_mark:
            status = PointStatus.INCONSISTENCIA
        else:
            # Não faltou marcação, possivelmente trabalhou
            if first_entry and first_exit:
                if req_second and second_entry and second_exit:
                    status = PointStatus.TRABALHADO_COM_OCORRENCIA
                elif not req_second:
                    status = PointStatus.TRABALHADO_PARCIAL
                else:
                    status = PointStatus.INCONSISTENCIA
            else:
                status = PointStatus.INCONSISTENCIA
    else:
        # Lógica padrão se não houver palavras-chave óbvias
        if missing_mark:
            if occurrence == "I":
                status = PointStatus.INCONSISTENCIA
            else:
                status = PointStatus.FALTA
        else:
            if req_second:
                if occurrence:
                    status = PointStatus.TRABALHADO_COM_OCORRENCIA
                else:
                    status = PointStatus.TRABALHADO
            else:
                status = PointStatus.TRABALHADO_PARCIAL
                
    record["status"] = status
    record["requires_second_period"] = req_second
    record["has_missing_required_mark"] = missing_mark
    
    # Limpa código temporário se existir
    if "schedule_code" in record:
        del record["schedule_code"]
        
    return record
