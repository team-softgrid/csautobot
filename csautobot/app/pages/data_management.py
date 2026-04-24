"""
학습 데이터 관리 페이지
csData 폴더의 파일을 조회하고, 신규 파일을 업로드하며, 인덱스(학습)를 재구성합니다.
"""
from __future__ import annotations

import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

from paths import repo_root

# csautobot/app/pages/data_management.py 기준, HERE는 csautobot 디렉토리
HERE = Path(__file__).resolve().parent.parent.parent
CS_DIR = repo_root(HERE) / "csData"

def _format_size(size_bytes: int) -> str:
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.2f} MB"

def render() -> None:
    st.title("📂 학습 데이터 관리")
    st.markdown("""
    이곳에서 AI가 학습할 엑셀(민원, AS 접수내역 등) 파일을 관리할 수 있습니다.  
    새로운 파일을 업로드한 후 **인덱스 재구성** 버튼을 눌러야 챗봇/검색에 반영됩니다.
    """)
    
    st.divider()
    
    # 1. 파일 목록 조회
    st.subheader("📋 현재 등록된 학습 파일")
    
    if not CS_DIR.exists():
        CS_DIR.mkdir(parents=True, exist_ok=True)
        
    files = list(CS_DIR.glob("*.xlsx"))
    
    if files:
        file_data = []
        for f in files:
            stat = f.stat()
            file_data.append({
                "파일명": f.name,
                "크기": _format_size(stat.st_size),
                "수정일": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
            })
            
        df = pd.DataFrame(file_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info(f"{CS_DIR.name} 폴더에 등록된 엑셀 파일이 없습니다.")
        
    st.divider()
    
    # 2. 파일 업로드
    st.subheader("📤 신규 자료 업로드")
    uploaded_files = st.file_uploader(
        "추가할 엑셀(.xlsx) 파일을 선택하세요", 
        type=["xlsx"], 
        accept_multiple_files=True
    )
    
    if uploaded_files:
        if st.button("선택한 파일 서버에 저장", type="primary"):
            success_count = 0
            for uploaded_file in uploaded_files:
                save_path = CS_DIR / uploaded_file.name
                with save_path.open("wb") as f:
                    f.write(uploaded_file.getbuffer())
                success_count += 1
            
            st.success(f"{success_count}개 파일이 성공적으로 업로드되었습니다.")
            st.rerun()
            
    st.divider()
    
    # 3. 인덱스 재구성
    st.subheader("🔄 인덱스(DB) 재구성")
    st.markdown("새로운 파일을 업로드했거나 기존 파일을 수정했다면, 반드시 아래 버튼을 눌러 AI 학습 데이터를 최신화해야 합니다.")
    
    if st.button("🚀 인덱스 재구성 시작", type="primary", use_container_width=True):
        with st.status("인덱스 재구성 중...", expanded=True) as status:
            try:
                # 1. Ingest
                st.write("1. 엑셀 데이터 추출 및 정규화 (ingest.py) 실행 중...")
                ingest_script = HERE / "ingest.py"
                
                # subprocess env setup (preserving OPENAI_API_KEY if exists)
                env = os.environ.copy()
                env["PYTHONPATH"] = str(HERE) # Ensure module imports work
                
                ingest_res = subprocess.run(
                    [sys.executable, str(ingest_script)], 
                    capture_output=True, 
                    text=True, 
                    check=False,
                    env=env
                )
                if ingest_res.returncode != 0:
                    st.error(f"Ingest 실패:\n{ingest_res.stderr}")
                    status.update(label="인덱스 재구성 실패", state="error", expanded=True)
                    return
                st.code(ingest_res.stdout, language="text")
                if ingest_res.stderr:
                    st.code(ingest_res.stderr, language="text")
                st.write("✅ 추출 완료")
                
                # 2. Build Index
                st.write("2. 벡터 DB 임베딩 및 형태소 인덱스 생성 (build_index.py) 실행 중...")
                build_script = HERE / "build_index.py"
                build_res = subprocess.run(
                    [sys.executable, str(build_script)], 
                    capture_output=True, 
                    text=True, 
                    check=False,
                    env=env
                )
                if build_res.returncode != 0:
                    st.error(f"Build Index 실패:\n{build_res.stderr}")
                    status.update(label="인덱스 재구성 실패", state="error", expanded=True)
                    return
                st.code(build_res.stdout, language="text")
                if build_res.stderr:
                    st.code(build_res.stderr, language="text")
                st.write("✅ 인덱스 생성 완료")
                
                status.update(label="🎉 인덱스 재구성 성공! 이제 새로운 데이터로 검색이 가능합니다.", state="complete", expanded=False)
                st.balloons()
                
            except Exception as e:
                st.error(f"오류가 발생했습니다: {e}")
                status.update(label="인덱스 재구성 중 오류 발생", state="error", expanded=True)
