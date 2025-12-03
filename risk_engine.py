from backend.app.models.risk import RiskReportRequest

# ---------------------------------------------------------
# [1] LLM & PDF 생성용 포맷터 (님의 기능)
# ---------------------------------------------------------
def format_risk_data(data: RiskReportRequest) -> str:
    """
    입력받은 구조화된 JSON 데이터를 LLM에게 전달할 
    '요약 텍스트(Context)'로 변환합니다.
    """
    
    # 안전 여부 텍스트 변환
    safety_status = "안전(선순위)" if data.analysis.is_safe else "위험(후순위)"

    # LLM에게 먹여줄 텍스트 조립
    context_text = f"""
    [1. 사건 정보]
    - 발생 이벤트: {data.event.name} ({data.event.type})
    - 접수 일자: {data.event.date}
    - 채권자: {data.event.creditor}
    - 청구 금액: {data.event.amount}
    - 사건 번호: {data.event.case_number}

    [2. 위험 분석 결과]
    - 위험 등급: {data.analysis.grade}
    - LTV(부채비율): {data.analysis.ltv}
    - 권리 순위: {safety_status}
    - 핵심 위험 사유: {data.analysis.reason}
    - 예상 손실액: {data.analysis.expected_loss}

    [3. 임대차 계약 현황]
    - 보증금: {data.contract.deposit}
    - 추정 시세: {data.contract.market_price}
    - 확정 일자: {data.contract.fixed_date}
    """
    
    return context_text

# ---------------------------------------------------------
# [2] 기존 레거시 기능 지원 (팀원 코드 호환용)
# snapshot_service.py 등이 이 함수들을 찾으므로 지우면 안 됩니다.
# ---------------------------------------------------------
def evaluate_risk(diff_result: dict) -> dict:
    """
    (기존) 등기부 변동 사항을 분석하여 위험도를 평가하는 함수
    * 현재는 에러 방지용 더미(Dummy) 로직으로 유지
    """
    # 실제 로직이 필요하다면 팀원들의 코드를 복구해야 함
    return {
        "risk_level": "GREEN",
        "score": 100,
        "events": [],
        "ltv": 0.0,
        "deposit_amount": 0
    }

def calculate_total_liens(eulgu_list: list) -> int:
    """
    (기존) 을구의 채권 총액 계산 함수
    """
    return 0