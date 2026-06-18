import os
from pathlib import Path
from typing import List, Dict, Any, Tuple
from pydantic import BaseModel, Field

from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate

from retrieval import load_bm25, resolve_chroma_dir, retrieve_reranked
from services.pricing_service import lookup_part_pricing, get_pricing_list

BOT_DIR = Path(__file__).resolve().parents[1]

# LLM structured output schemas
class PredictedPart(BaseModel):
    part_name: str = Field(description="단가표 상의 품명 또는 이에 매핑되는 예상 부품명 (예: PLC 모뎀, 보드, ELCB 누전차단기 등)")
    qty: int = Field(default=1, description="교체 예상 수량")
    reason: str = Field(description="이 부품을 선정한 조치 이력 상의 근거")

class LLMPrediction(BaseModel):
    symptom_summary: str = Field(description="증상 요약")
    likely_cause: str = Field(description="유사 사례 기반 예상 원인")
    parts: List[PredictedPart] = Field(default_factory=list, description="교체 소요 예상 부품 목록")

# Final return schema (API-level)
class PartDetail(BaseModel):
    part_name: str
    spec: str
    qty: int
    unit_price: int
    total_price: int
    category: str

class QuotationDraft(BaseModel):
    symptom_summary: str
    likely_cause: str
    parts: List[PartDetail]
    dispatch_fee: int
    labor_fee: int
    supply_value: int
    vat: int
    total_amount: int

SYS_PROMPT = """당신은 전기차 충전기 AS(애프터서비스) 견적서 작성 도우미입니다.
고객이 접수한 [고장 증상]과 로컬 데이터베이스에서 검색된 [과거 유사 사례], 그리고 공식 [계약 단가표 품목 목록]을 참고하여 예상되는 교체 부품과 비용을 산출하십시오.

반드시 다음 규칙을 지키십시오:
1. [과거 유사 사례]의 조치 내용과 교체 부품을 분석하여, 현재 고장 증상을 해결하기 위해 교체해야 할 가능성이 높은 부품과 수량을 예측하십시오.
2. 부품명은 제공된 [계약 단가표 품목 목록]의 이름(예: AC미터, DC미터 전력량계, IC결제만달기, LCD, PLC 모뎀, RFID리더기, 누전차단기, 보드, 산업용 PC, 충전케이블, 파워모듈)에 최대한 매핑하여 선택하십시오.
3. 만약 유사 사례에서 부품 교체 대신 '단순 원격 조치', 'HMI 업데이트', '설정 확인' 등 부품이 필요 없는 조치만 확인된다면, 빈 부품 목록을 반환하십시오.
4. 추측이나 일반론을 배제하고 오직 제공된 유사 사례에 기반하여 판단하십시오."""

HUMAN_PROMPT_TEMPLATE = """[고객 고장 증상]
{question}

[충전기 정보]
- 구분(완속/급속): {charger_type}

[로컬 참고 사례 (과거 유사 조치 이력)]
{context}

[공식 계약 단가표 품목 목록]
{pricing_list_text}

---
위 내용을 바탕으로 예상되는 고장 원인과 필요한 부품(수량 포함)을 JSON 형태로 출력해 주십시오."""

def _get_vs(chroma_dir: Path) -> Chroma:
    emb = OpenAIEmbeddings(model="text-embedding-3-small")
    return Chroma(
        persist_directory=str(chroma_dir),
        embedding_function=emb,
        collection_name="csautobot",
    )

def _generate_offline_quotation_draft(query: str, charger_type: str) -> QuotationDraft:
    q_clean = query.lower().replace(" ", "")
    parts_details = []
    matched_parts = []
    likely_cause = "오프라인 패턴 분석에 의한 진단 완료 (API 키 미설정)"
    symptom_summary = f"접수 증상: {query}"
    
    if "plc" in q_clean or "모뎀" in q_clean:
        matched_parts.append(("PLC 모뎀", 1))
        likely_cause = "PLC 통신 모뎀 불량 또는 제어 보드 통신 단절"
    if "카드" in q_clean or "태깅" in q_clean or "리더기" in q_clean or "rfid" in q_clean:
        matched_parts.append(("RFID리더기", 1))
        likely_cause = "RFID 카드 리더기 인식 오류 또는 결제 단말기 고장"
    if "차단기" in q_clean or "누전" in q_clean:
        matched_parts.append(("누전차단기", 1))
        likely_cause = "누전차단기(ELCB) 트립 또는 과전류 차단기 고장"
    if "pc" in q_clean or "컴퓨터" in q_clean or "화면안나옴" in q_clean:
        matched_parts.append(("산업용 PC", 1))
        likely_cause = "산업용 PC 본체 전원 불량 또는 어댑터 고장"
    if "케이블" in q_clean or "커넥터" in q_clean or "커플러" in q_clean:
        matched_parts.append(("충전케이블", 1))
        likely_cause = "충전 케이블 피복 소손, 커넥터 파손 또는 온도 센서 불량"
    if "파워" in q_clean or "모듈" in q_clean or "reg" in q_clean or "모듈" in q_clean:
        matched_parts.append(("파워모듈", 1))
        likely_cause = "전력부 파워 모듈 고장 또는 팬(FAN) 고장으로 인한 과열"
    if "lcd" in q_clean or "액정" in q_clean:
        matched_parts.append(("LCD", 1))
        likely_cause = "LCD 액정 패널 백라이트 수명 종료 또는 터치 불량"
    if "보드" in q_clean or "uc1" in q_clean:
        matched_parts.append(("보드", 1))
        likely_cause = "메인 컨트롤 보드(UC1) 전원/통신 불량"
        
    total_parts_price = 0
    is_wansok = (charger_type == "완속")
    
    for p_name, qty in matched_parts:
        pricing_info = lookup_part_pricing(p_name, charger_type)
        unit_price = pricing_info.get("contract_price", 0)
        total_price = unit_price * qty
        
        parts_details.append(PartDetail(
            part_name=pricing_info.get("name", p_name),
            spec=pricing_info.get("spec", "규격 미지정"),
            qty=qty,
            unit_price=unit_price,
            total_price=total_price,
            category=pricing_info.get("category", charger_type)
        ))
        total_parts_price += total_price
        
    dispatch_fee = 100000
    labor_fee = 70000
    
    has_wansok_board = any(
        is_wansok and ('보드' in x.part_name or 'UC1' in x.part_name or 'LCD' in x.part_name)
        for x in parts_details
    )
    if has_wansok_board:
        dispatch_fee = 0
        
    supply_value = total_parts_price + dispatch_fee + labor_fee
    vat = int(supply_value * 0.1)
    total_amount = supply_value + vat
    
    return QuotationDraft(
        symptom_summary=symptom_summary,
        likely_cause=likely_cause,
        parts=parts_details,
        dispatch_fee=dispatch_fee,
        labor_fee=labor_fee,
        supply_value=supply_value,
        vat=vat,
        total_amount=total_amount
    )

def generate_quotation_draft(
    query: str,
    charger_type: str = "급속",
    use_web_search: bool = False
) -> QuotationDraft:
    """
    RAG similarity search and LLM invocation to generate a quotation draft.
    """
    # Try loading keys from dotenv first
    if not os.environ.get("OPENAI_API_KEY") and not os.environ.get("GOOGLE_API_KEY"):
        from dotenv import load_dotenv
        load_dotenv(BOT_DIR / ".env")
        
    # Check if keys are still missing - if so, run offline fallback
    if not os.environ.get("OPENAI_API_KEY") and not os.environ.get("GOOGLE_API_KEY"):
        return _generate_offline_quotation_draft(query, charger_type)
        
    index_dir = resolve_chroma_dir(BOT_DIR)
    if index_dir is None:
        raise FileNotFoundError("Chroma DB 인덱스를 찾을 수 없습니다. build_index.py를 실행하십시오.")
        
    bm25 = load_bm25(index_dir)
    emb = OpenAIEmbeddings(model="text-embedding-3-small")
    vs = _get_vs(index_dir)
    
    # 1. RAG search
    # Run hybrid retrieval
    rr = retrieve_reranked(
        query, vs, bm25, emb,
        k_dense=30, k_sparse=30, k_hybrid=20, k_final=5
    )
    ctx = "\n\n---%s---\n\n".join(d.page_content for d in rr.documents)
    
    # 2. Get Pricing List Text for LLM reference
    pricing_list = get_pricing_list()
    pricing_list_text = "\n".join(
        f"- 품명: {p['name']} | 규격: {p['spec']} | 구분: {p['category']}"
        for p in pricing_list
    )
    
    # 3. Prompt setup
    prompt = ChatPromptTemplate.from_messages([
        ("system", SYS_PROMPT),
        ("human", HUMAN_PROMPT_TEMPLATE)
    ])
    
    # 4. Invoke LLM with structured output (OpenAI with Gemini fallback)
    openai_error = rr.details.get("openai_error", False)
    llm_success = False
    prediction = None
    
    if not openai_error:
        try:
            from langchain_openai import ChatOpenAI
            llm = ChatOpenAI(model="gpt-4o-mini", temperature=0).with_structured_output(LLMPrediction)
            chain = prompt | llm
            prediction = chain.invoke({
                "question": query,
                "charger_type": charger_type,
                "context": ctx,
                "pricing_list_text": pricing_list_text
            })
            llm_success = True
        except Exception as e:
            print(f"ChatOpenAI failed in quotation service: {e}")
            
    if not llm_success:
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            if not os.getenv("GOOGLE_API_KEY"):
                from dotenv import load_dotenv
                load_dotenv(BOT_DIR / ".env")
            llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0).with_structured_output(LLMPrediction)
            chain = prompt | llm
            prediction = chain.invoke({
                "question": query,
                "charger_type": charger_type,
                "context": ctx,
                "pricing_list_text": pricing_list_text
            })
            llm_success = True
        except Exception as e:
            raise RuntimeError(f"견적 초안 생성에 실패했습니다 (OpenAI/Gemini 모두 호출 실패): {e}")

    # 5. Process predicted parts and map to contract unit prices
    parts_details = []
    total_parts_price = 0
    
    # Check if category is 완속
    is_wansok = (charger_type == "완속")
    
    for p in prediction.parts:
        pricing_info = lookup_part_pricing(p.part_name, charger_type)
        # Apply the contract price (F column)
        unit_price = pricing_info.get("contract_price", 0)
        total_price = unit_price * p.qty
        
        parts_details.append(PartDetail(
            part_name=pricing_info.get("name", p.part_name),
            spec=pricing_info.get("spec", "규명되지 않음"),
            qty=p.qty,
            unit_price=unit_price,
            total_price=total_price,
            category=pricing_info.get("category", charger_type)
        ))
        total_parts_price += total_price
        
    # 6. Apply Technical Service Fees
    # Default fees: Dispatch (100,000 KRW), Labor (70,000 KRW)
    dispatch_fee = 100000
    labor_fee = 70000
    
    # Business rule check: If category is 완속 and part is UC1 보드/LCD (simple tasks),
    # or if no parts are replaced (simple diagnosis), we might adjust/omit dispatch.
    # For initial generation:
    # - If charger_type is 완속 and the part is '보드' (e.g. UC1 보드), default dispatch_fee to 0
    has_wansok_board = any(
        is_wansok and ('보드' in x.part_name or 'UC1' in x.part_name or 'LCD' in x.part_name)
        for x in parts_details
    )
    if has_wansok_board:
        dispatch_fee = 0
        
    # If no parts are predicted, default to standard labor/dispatch
    if not parts_details:
        dispatch_fee = 100000
        labor_fee = 70000
        
    # 7. Calculate Supply Value, VAT, and Grand Total
    supply_value = total_parts_price + dispatch_fee + labor_fee
    vat = int(supply_value * 0.1)
    total_amount = supply_value + vat
    
    return QuotationDraft(
        symptom_summary=prediction.symptom_summary,
        likely_cause=prediction.likely_cause,
        parts=parts_details,
        dispatch_fee=dispatch_fee,
        labor_fee=labor_fee,
        supply_value=supply_value,
        vat=vat,
        total_amount=total_amount
    )
