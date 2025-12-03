import os
import json
from pathlib import Path  # [추가] 경로 찾기 도구
from openai import OpenAI
from dotenv import load_dotenv
from datetime import datetime

# [수정] .env 파일 위치를 명시적으로 지정
# 현재 파일: backend/app/services/llm_engine.py
# 목표 파일: backend/.env (상위->상위->상위 폴더)
current_file_path = Path(__file__).resolve()
backend_dir = current_file_path.parent.parent.parent
env_path = backend_dir / ".env"

# 지정한 경로의 .env 로드
load_dotenv(dotenv_path=env_path)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def get_playbook_data(risk_info, user_name):
    """
    입력된 분석 텍스트(risk_info)를 바탕으로 
    LLM이 대응 매뉴얼(Playbook) JSON을 생성합니다.
    """
    
    # [1] 등급 감지 로직
    current_grade = "GREEN" 

    # 1-1. 명시적인 등급 라벨 우선 확인
    if "RED" in risk_info:
        current_grade = "RED"
    elif "AMBER" in risk_info:
        current_grade = "AMBER"
    elif "GREEN" in risk_info:
        current_grade = "GREEN"
    
    # 1-2. 키워드 추론 (등급 라벨이 없을 경우 대비)
    else:
        if "경매" in risk_info:
            current_grade = "RED"
        elif "가압류" in risk_info:  # [중요] 압류보다 먼저 체크!
            current_grade = "AMBER"
        elif "압류" in risk_info:    # 가압류가 아닌 진짜 압류
            current_grade = "RED"
        elif "주의" in risk_info:
            current_grade = "AMBER"

    # [2] 등급별 가이드라인
    if current_grade == "RED":
        color = "#D32F2F"
        specific_guide = """
        - **상황**: 경매/압류 등 심각한 위기. 보증금 손실 가능성 높음.
        - **핵심 경고(warnings)**: 
          1. **이사/전출 절대 금지**: "보증금을 돌려받기 전까지는 절대 짐을 빼거나 다른 곳으로 전입신고를 하면 안 됩니다. (대항력 상실)"
          2. **배당요구종기일 엄수**: "법원이 정한 기한 내에 권리신고를 하지 않으면 배당에서 제외됩니다. 즉시 법원에 확인하세요."
        - **임대인 문자**: 법적 조치(임차권등기, 소송 등)를 예고하는 내용증명 수준의 단호한 장문.
        """
    elif current_grade == "AMBER":
        color = "#FF8F00"
        specific_guide = """
        - **상황**: 가압류 등 잠재적 위험. 당장은 안전하나 대비가 필요함.
        - **핵심 경고(warnings)**: 
          1. **골든타임 (계약 해지)**: "묵시적 갱신이 되면 보증금 반환이 3개월 늦어집니다. 반드시 계약 만료 '2개월 전'까지 갱신 거절 의사를 통보하세요."
          2. **임차권등기명령 필수**: "혹시 이사를 가야 한다면, 반드시 법원에 '임차권등기명령'을 신청하고 등기 완료 후 이동해야 대항력이 유지됩니다."
        - **임대인 문자**: 우려 표명 및 전세보증금 반환 계획을 묻는 정중하고 상세한 장문.
        """
    else: 
        color = "#388E3C"
        specific_guide = """
        - **상황**: 단순 정보 변경. 안전함.
        - **핵심 경고(warnings)**: 
          1. **정기 모니터링**: "현재는 안전하지만, 3~6개월마다 등기부를 확인하는 습관이 중요합니다."
          2. **재계약 주의**: "보증금 증액 시에는 반드시 등기부를 다시 확인하고 확정일자를 새로 받아야 합니다."
        - **임대인 문자**: 작성하지 않음 (빈 문자열).
        """

    # [3] 시스템 프롬프트
    system_msg = f"""
    너는 부동산 법률 전문가 AI다. 현재 등급: **[{current_grade}]**
    
    [지침]
    {specific_guide}
    
    [작성 규칙]
    1. **warnings**: 위 지침에 따라 핵심 주의사항 2가지를 구체적인 이유와 함께 작성하라.
    2. **message_to_lessor**: RED/AMBER는 장문, GREEN은 빈 문자열.
    3. **JSON Only**: 표준 JSON 포맷만 출력하라.
    """

    # [4] 유저 프롬프트
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    user_msg = f"""
    # [Input Data]
    {risk_info}

    # [Required JSON Schema]
    {{
        "meta": {{
            "title": "[보증금 레이더] 대응 가이드북",
            "grade": "{current_grade}",
            "color": "{color}",
            "generated_at": "{current_time}"
        }},
        "user_name": "{user_name}",
        "content": {{
            "summary": "상황 요약 (3문장)",
            "warnings": ["경고1", "경고2"],
            "message_to_lessor": "임대인 문자 내용",
            "checklist": ["1단계...", "2단계...", "3단계...", "4단계...", "5단계..."],
            "diff_table": [
                {{ "type": "신규", "purpose": "등기목적", "date": "날짜", "owner": "권리자" }}
            ],
            "glossary": [{{ "term": "용어", "definition": "설명" }}],
            "qna_list": [
                {{ "question": "Q1", "answer": "A1" }},
                {{ "question": "Q2", "answer": "A2" }},
                {{ "question": "Q3", "answer": "A3" }},
                {{ "question": "Q4", "answer": "A4" }},
                {{ "question": "Q5", "answer": "A5" }}
            ]
        }}
    }}
    """

    # [5] API 호출
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_msg}
            ],
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)

    except Exception as e:
        print(f"❌ AI Error: {e}")
        safe_color = locals().get('color', '#888888')
        return {
            "meta": {"title": "오류 발생", "grade": "AMBER", "color": safe_color},
            "user_name": user_name,
            "content": {"summary": "AI 연결 실패", "warnings": [], "checklist": [], "qna_list": [], "message_to_lessor": "오류가 발생했습니다."}
        }