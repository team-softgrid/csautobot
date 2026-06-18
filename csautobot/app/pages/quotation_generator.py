import streamlit as st
import pandas as pd
from typing import List, Dict, Any
import io

from app.ui import page_header
from app.theme import COLOR_PRIMARY, COLOR_ACCENT, COLOR_BG_SOFT, COLOR_TEXT, COLOR_MUTED
from services.quotation_service import generate_quotation_draft, QuotationDraft, PartDetail
from services.pricing_service import lookup_part_pricing

def _init_session_state():
    if "quote_query" not in st.session_state:
        st.session_state.quote_query = ""
    if "quote_charger_type" not in st.session_state:
        st.session_state.quote_charger_type = "급속"
    if "quote_draft" not in st.session_state:
        st.session_state.quote_draft = None

def render():
    _init_session_state()
    
    page_header(
        "AI 견적서 생성기",
        "고장 증상 입력 시 AS 이력을 실시간 검색하여 예상 부품과 계약 단가를 매핑하고 견적 총액을 산출합니다.",
        icon="💡",
        accent=COLOR_PRIMARY
    )
    
    # Left column: input form / Right column: generated quotation
    col_input, col_result = st.columns([1, 1.5])
    
    with col_input:
        st.markdown("### 🔧 고장 진단 및 조건 설정")
        with st.form("quotation_input_form"):
            query = st.text_area(
                "고객 접수 증상 및 불량 현상 입력",
                value=st.session_state.quote_query,
                placeholder="예: 급속 충전기 케이블 꽂자마자 충전 완료 뜸 / 카드 인식 불가",
                height=150,
                help="고객이 보내준 장애 설명이나 에러 코드를 상세히 적어주세요."
            )
            
            charger_type = st.selectbox(
                "충전기 구분",
                ["급속", "완속"],
                index=0 if st.session_state.quote_charger_type == "급속" else 1
            )
            
            submit_btn = st.form_submit_button("✨ AI 견적서 초안 생성", use_container_width=True)
            
        if submit_btn and query.strip():
            st.session_state.quote_query = query
            st.session_state.quote_charger_type = charger_type
            
            with st.spinner("유사 AS 사례 검색 및 견적 매핑 중..."):
                try:
                    draft = generate_quotation_draft(query, charger_type)
                    # Convert parts to a list of dicts to allow easier editing in session state
                    parts_list = []
                    for p in draft.parts:
                        parts_list.append({
                            "part_name": p.part_name,
                            "spec": p.spec,
                            "qty": p.qty,
                            "unit_price": p.unit_price,
                            "category": p.category
                        })
                    
                    st.session_state.quote_draft = {
                        "symptom_summary": draft.symptom_summary,
                        "likely_cause": draft.likely_cause,
                        "parts": parts_list,
                        "dispatch_fee": draft.dispatch_fee,
                        "labor_fee": draft.labor_fee
                    }
                    st.success("견적 초안이 성공적으로 생성되었습니다!")
                except Exception as e:
                    st.error(f"견적 산출 실패: {e}")
                    
        # Add a custom part addition section if a draft exists
        if st.session_state.quote_draft is not None:
            st.markdown("---")
            st.markdown("#### ➕ 수동 부품 추가")
            with st.container():
                add_c1, add_c2, add_c3 = st.columns([2, 1, 1])
                with add_c1:
                    new_part_name = st.text_input("부품명", placeholder="예: LCD 패널", key="new_part_name")
                with add_c2:
                    new_part_cat = st.selectbox("구분", ["급속", "완속", "공용"], key="new_part_cat")
                with add_c3:
                    new_part_qty = st.number_input("수량", min_value=1, value=1, step=1, key="new_part_qty")
                    
                if st.button("부품 추가", use_container_width=True):
                    if new_part_name.strip():
                        pricing_info = lookup_part_pricing(new_part_name, new_part_cat)
                        st.session_state.quote_draft["parts"].append({
                            "part_name": pricing_info.get("name", new_part_name),
                            "spec": pricing_info.get("spec", "수동 입력 품목"),
                            "qty": new_part_qty,
                            "unit_price": pricing_info.get("contract_price", 0),
                            "category": pricing_info.get("category", new_part_cat)
                        })
                        st.success(f"'{new_part_name}' 부품이 추가되었습니다.")
                        st.rerun()
                        
    with col_result:
        st.markdown("### 📄 산출 견적서 (실시간 편집)")
        
        draft_state = st.session_state.quote_draft
        if draft_state is None:
            st.info("왼쪽에서 고장 증상을 입력하고 초안 생성 버튼을 누르면 실시간 견적이 생성됩니다.")
            return
            
        # Display AI Diagnosis Summary
        with st.expander("🔍 AI 고장 진단 요약", expanded=True):
            st.markdown(f"**증상 요약:** {draft_state['symptom_summary']}")
            st.markdown(f"**예상 고장 원인:** {draft_state['likely_cause']}")
            
        # Display Parts Table and Quantity Inputs
        st.markdown("#### 🛠️ 소요 부품 세부 내역")
        parts = draft_state["parts"]
        
        if not parts:
            st.warning("예상되는 교체 부품이 없습니다. 단순 점검 공임만 청구됩니다.")
        else:
            updated_parts = []
            for idx, p in enumerate(parts):
                # We render a clean row for each part with: Name, spec, unit price, quantity edit, total price, delete checkbox
                card_c1, card_c2, card_c3, card_c4 = st.columns([3, 1, 1, 0.5])
                with card_c1:
                    st.markdown(f"**{p['part_name']}**")
                    st.caption(f"규격: {p['spec']} | {p['category']}")
                with card_c2:
                    st.markdown(f"{p['unit_price']:,} 원")
                with card_c3:
                    qty = st.number_input(
                        "수량",
                        min_value=1,
                        value=p["qty"],
                        step=1,
                        key=f"qty_{idx}",
                        label_visibility="collapsed"
                    )
                with card_c4:
                    delete = st.checkbox("🗑️", key=f"del_{idx}", help="삭제")
                    
                if not delete:
                    updated_parts.append({
                        "part_name": p["part_name"],
                        "spec": p["spec"],
                        "qty": qty,
                        "unit_price": p["unit_price"],
                        "category": p["category"]
                    })
            
            # Update parts list in session state if any change occurred
            if len(updated_parts) != len(parts) or any(updated_parts[i]["qty"] != parts[i]["qty"] for i in range(len(updated_parts))):
                st.session_state.quote_draft["parts"] = updated_parts
                st.rerun()
                
        # Technical Service Fees (editable via inputs)
        st.markdown("#### ⚡ 기술 서비스료 설정 (출장비 및 공임비)")
        fee_c1, fee_c2 = st.columns(2)
        with fee_c1:
            dispatch_fee = st.number_input(
                "출장 교통비 (원, VAT 별도)",
                min_value=0,
                value=draft_state["dispatch_fee"],
                step=10000,
                key="dispatch_fee_input"
            )
        with fee_c2:
            labor_fee = st.number_input(
                "작업 공임비 (원, VAT 별도)",
                min_value=0,
                value=draft_state["labor_fee"],
                step=10000,
                key="labor_fee_input"
            )
            
        # Update session state values
        st.session_state.quote_draft["dispatch_fee"] = dispatch_fee
        st.session_state.quote_draft["labor_fee"] = labor_fee
        
        # Calculate Totals
        parts_total = sum(p["unit_price"] * p["qty"] for p in st.session_state.quote_draft["parts"])
        supply_value = parts_total + dispatch_fee + labor_fee
        vat = int(supply_value * 0.1)
        grand_total = supply_value + vat
        
        # Display Totals in a Premium CSS layout
        st.markdown("---")
        st.markdown(
            f"""
            <div style="background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); 
                        border: 1px solid #334155; padding: 20px; border-radius: 12px; margin-bottom: 20px;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                    <span style="color: {COLOR_MUTED}; font-size: 14px;">부품 합계</span>
                    <span style="color: {COLOR_TEXT}; font-weight: 600;">{parts_total:,} 원</span>
                </div>
                <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                    <span style="color: {COLOR_MUTED}; font-size: 14px;">기술 서비스료 (출장 + 공임)</span>
                    <span style="color: {COLOR_TEXT}; font-weight: 600;">{dispatch_fee + labor_fee:,} 원</span>
                </div>
                <hr style="border-color: #334155; margin: 12px 0;"/>
                <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                    <span style="color: {COLOR_MUTED}; font-size: 15px; font-weight: bold;">공급가액 총계</span>
                    <span style="color: {COLOR_PRIMARY}; font-size: 18px; font-weight: 800;">{supply_value:,} 원</span>
                </div>
                <div style="display: flex; justify-content: space-between; margin-bottom: 8px; border-bottom: 1px dashed #334155; padding-bottom: 10px;">
                    <span style="color: {COLOR_MUTED}; font-size: 15px; font-weight: bold;">부가세 (VAT 10%)</span>
                    <span style="color: {COLOR_WARN if 'COLOR_WARN' in globals() else '#f97316'}; font-size: 18px; font-weight: 800;">{vat:,} 원</span>
                </div>
                <div style="display: flex; justify-content: space-between; margin-top: 12px;">
                    <span style="color: {COLOR_TEXT}; font-size: 18px; font-weight: 800;">💰 최종 견적 금액 (합계)</span>
                    <span style="color: {COLOR_ACCENT}; font-size: 24px; font-weight: 900; 
                                 text-shadow: 0 0 10px rgba(74, 222, 128, 0.3);">{grand_total:,} 원</span>
                </div>
                <div style="text-align: right; color: {COLOR_MUTED}; font-size: 11px; margin-top: 8px;">
                    * 부가세 포함 금액입니다.
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        # CSV Exporter (Excel compatible UTF-8-sig)
        csv_buffer = io.StringIO()
        csv_buffer.write("\ufeff")  # UTF-8 BOM
        
        csv_buffer.write("=== AI 자동 생성 견적서 ===\n")
        csv_buffer.write(f"고장 증상 요약,{st.session_state.quote_query.replace(',', ' ')},\n")
        csv_buffer.write(f"예상 고장 원인,{st.session_state.quote_draft['likely_cause'].replace(',', ' ')},\n\n")
        
        csv_buffer.write("구분,품명,규격,단가(원),수량,금액(원)\n")
        for p in st.session_state.quote_draft["parts"]:
            total_p = p["unit_price"] * p["qty"]
            csv_buffer.write(f"{p['category']},{p['part_name']},{p['spec'].replace(',', ' ')},{p['unit_price']},{p['qty']},{total_p}\n")
            
        csv_buffer.write(f"기술료,출장 교통비,-,{dispatch_fee},1,{dispatch_fee}\n")
        csv_buffer.write(f"기술료,작업 공임비,-,{labor_fee},1,{labor_fee}\n\n")
        
        csv_buffer.write(f"공급가액 합계,,,,,{supply_value}\n")
        csv_buffer.write(f"부가세 (VAT 10%),,,,,{vat}\n")
        csv_buffer.write(f"최종 견적 합계,,,,,{grand_total}\n")
        
        st.download_button(
            label="📥 견적서 다운로드 (Excel 호환 CSV)",
            data=csv_buffer.getvalue(),
            file_name=f"견적서_{st.session_state.quote_query[:10].replace(' ', '_')}.csv",
            mime="text/csv",
            use_container_width=True
        )
