import zipfile
import xml.etree.ElementTree as ET
import os
import re
from pathlib import Path
from typing import Dict, Any, List

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parent.parent
DEFAULT_EXCEL_PATH = REPO_ROOT / "docs" / "계약단가표-260522.xlsx"

# Robust fallback pricing rules in case Excel parsing fails
FALLBACK_PRICING = [
    {"num": 1, "category": "급속", "name": "AC미터", "spec": "OMWH-320D-B(좌타입)", "contract_price": 130000, "cs_price": 130000},
    {"num": 2, "category": "급속", "name": "DC미터 전력량계", "spec": "1P2W 1000V 200A", "contract_price": 185000, "cs_price": 190000},
    {"num": 3, "category": "공용", "name": "IC결제만달기", "spec": "IC/RF/MS(SVM600)", "contract_price": 385000, "cs_price": 400000},
    {"num": 4, "category": "완속", "name": "LCD", "spec": "8인치 액정 패널", "contract_price": 120000, "cs_price": 130000},
    {"num": 5, "category": "급속", "name": "PLC 모뎀", "spec": "PEPPERMINT-NNA_000(신형)", "contract_price": 500000, "cs_price": 500000},
    {"num": 6, "category": "급속", "name": "PLC 모뎀", "spec": "PEPPERMINT-NNA_001(신형)", "contract_price": 500000, "cs_price": 500000},
    {"num": 7, "category": "공용", "name": "RFID리더기", "spec": "ATM-100", "contract_price": 94000, "cs_price": 100000},
    {"num": 8, "category": "급속", "name": "누전차단기", "spec": "ELCB 4P 100A TYPE (감도전류 30/50/100mA)", "contract_price": 260000, "cs_price": 270000},
    {"num": 9, "category": "급속", "name": "보드", "spec": "EV Charger Controller V2.1", "contract_price": 500000, "cs_price": 536000},
    {"num": 10, "category": "완속", "name": "보드", "spec": "MDI-UC-1 V2.0 (8인치보드), (MAX 1A)", "contract_price": 525000, "cs_price": 525000},
    {"num": 11, "category": "완속", "name": "보드", "spec": "MDI-UC1-PILOT V4.0", "contract_price": 110000, "cs_price": 110000},
    {"num": 12, "category": "급속", "name": "산업용 PC", "spec": "12.1인치(신형)", "contract_price": 1248000, "cs_price": 1260000},
    {"num": 13, "category": "급속", "name": "산업용 PC", "spec": "12.1인치(구형) / 단종", "contract_price": 0, "cs_price": 0},
    {"num": 14, "category": "급속", "name": "충전케이블", "spec": "SW-EVT201MD-006 (CCS1/200A)", "contract_price": 1050000, "cs_price": 1125000},
    {"num": 15, "category": "급속", "name": "충전케이블", "spec": "SW-EVTN151MDLP-007 (CCS1/150A)", "contract_price": 960000, "cs_price": 1029000},
    {"num": 16, "category": "급속", "name": "충전케이블", "spec": "V3-DSIEC2e-EV63P-6m/3상", "contract_price": 400000, "cs_price": 429000},
    {"num": 17, "category": "급속", "name": "충전케이블", "spec": "KW1CGY10PDL0600E(6M)", "contract_price": 940000, "cs_price": 1000000},
    {"num": 18, "category": "완속", "name": "충전케이블", "spec": "AC 5핀 32A 5M 완속 C타입 케이블", "contract_price": 120000, "cs_price": 129000},
    {"num": 19, "category": "급속", "name": "파워모듈", "spec": "REG1K0100G (30KW)", "contract_price": 1800000, "cs_price": 1800000},
    {"num": 20, "category": "급속", "name": "파워모듈", "spec": "REG50040 (15KW)", "contract_price": 1200000, "cs_price": 1500000},
]

_cached_pricing: List[Dict[str, Any]] = []

def parse_xlsx_sheet(file_path: Path, sheet_filename: str = "worksheets/sheet3.xml") -> List[Dict[str, Any]]:
    """Helper to parse contract price sheet directly from xlsx zip without dependencies."""
    if not file_path.is_file():
        raise FileNotFoundError(f"단가표 파일 없음: {file_path}")
        
    try:
        with zipfile.ZipFile(file_path) as zip_ref:
            # 1. Parse shared strings
            shared_strings = []
            if 'xl/sharedStrings.xml' in zip_ref.namelist():
                ss_content = zip_ref.read('xl/sharedStrings.xml')
                ss_root = ET.fromstring(ss_content)
                ns = {'ns': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
                for t in ss_root.findall('.//ns:t', ns):
                    shared_strings.append(t.text if t.text else "")
                    
            # 2. Parse sheet
            sheet_content = zip_ref.read(f'xl/{sheet_filename}')
            sheet_root = ET.fromstring(sheet_content)
            ns = {'ns': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
            
            rows = {}
            for row in sheet_root.findall('.//ns:row', ns):
                r_idx = int(row.attrib.get('r'))
                rows[r_idx] = {}
                for cell in row.findall('ns:c', ns):
                    r = cell.attrib.get('r')
                    col_letter = re.match(r'[A-Z]+', r).group()
                    
                    t = cell.attrib.get('t')
                    val_node = cell.find('ns:v', ns)
                    val = ""
                    if val_node is not None:
                        val = val_node.text
                        
                    if t == 's':
                        val = shared_strings[int(val)]
                    
                    rows[r_idx][col_letter] = val
            
            pricing_list = []
            for r_idx in sorted(rows.keys()):
                if r_idx < 4:  # Skip headers
                    continue
                row = rows[r_idx]
                if 'B' not in row or 'D' not in row:
                    continue
                
                # We need column B(No), C(Category), D(Name), E(Spec), F(Omni price), H(CS price)
                num_str = row['B'].strip()
                if not num_str.isdigit():
                    continue
                
                num = int(num_str)
                category = row.get('C', '').strip()
                name = row.get('D', '').strip()
                spec = row.get('E', '').strip()
                
                try:
                    contract_price = int(float(row.get('F', '0').strip()))
                except ValueError:
                    contract_price = 0
                    
                try:
                    cs_price = int(float(row.get('H', '0').strip()))
                except ValueError:
                    cs_price = 0
                
                pricing_list.append({
                    "num": num,
                    "category": category,
                    "name": name,
                    "spec": spec,
                    "contract_price": contract_price,
                    "cs_price": cs_price
                })
            return pricing_list
    except Exception as e:
        print(f"Error parsing Excel pricing: {e}. Falling back to hardcoded rules.")
        return []

def get_pricing_list(file_path: Path = DEFAULT_EXCEL_PATH) -> List[Dict[str, Any]]:
    """Loads and returns the contract unit price list, caching the result."""
    global _cached_pricing
    if _cached_pricing:
        return _cached_pricing
        
    if file_path.is_file():
        parsed = parse_xlsx_sheet(file_path)
        if parsed:
            _cached_pricing = parsed
            return _cached_pricing
            
    # Fallback if file not found or parse error
    _cached_pricing = FALLBACK_PRICING
    return _cached_pricing

def lookup_part_pricing(part_name: str, category: str = None) -> Dict[str, Any]:
    """
    Look up pricing for a given part name using keyword/semantic matching rules.
    Returns a dictionary of matched pricing details or a default empty-match dict.
    """
    pricing = get_pricing_list()
    part_name_clean = part_name.lower().replace(" ", "")
    
    # Try exact or clean substring match first
    for p in pricing:
        p_name = p["name"].lower().replace(" ", "")
        p_spec = p["spec"].lower().replace(" ", "")
        
        # Exact name match
        if p_name == part_name_clean:
            return p
            
    # Try soft matching rules
    # 1. PLC 모뎀
    if "plc" in part_name_clean:
        # Check if 신형 or 000/001 is requested, or default to PEPPERMINT-NNA_000
        for p in pricing:
            if p["name"] == "PLC 모뎀" and "신형" in p["spec"]:
                return p
        return [p for p in pricing if p["name"] == "PLC 모뎀"][0]
        
    # 2. 보드 / UC1 보드
    if "uc1" in part_name_clean or "uc-1" in part_name_clean:
        for p in pricing:
            if "mdi-uc-1" in p["spec"].lower():
                return p
    if "pilot" in part_name_clean or "파일럿" in part_name_clean:
        for p in pricing:
            if "pilot" in p["spec"].lower():
                return p
    if "보드" in part_name_clean:
        # Check category
        target_cat = category or "급속"
        for p in pricing:
            if p["name"] == "보드" and p["category"] == target_cat:
                return p
                
    # 3. 누전차단기 / 차단기
    if "차단기" in part_name_clean or "elcb" in part_name_clean:
        for p in pricing:
            if p["name"] == "누전차단기":
                return p
                
    # 4. 카드단말기 / 결제단말기 / svm600
    if "결제" in part_name_clean or "단말기" in part_name_clean or "svm600" in part_name_clean:
        for p in pricing:
            if "ic결제" in p["name"].lower() or "svm600" in p["spec"].lower():
                return p
                
    # 5. 산업용 PC / pc / 어댑터
    if "pc" in part_name_clean or "컴퓨터" in part_name_clean:
        for p in pricing:
            if p["name"] == "산업용 PC" and "신형" in p["spec"]:
                return p
                
    # 6. 케이블 완속/급속
    if "케이블" in part_name_clean or "충전케이블" in part_name_clean:
        target_cat = category or ("완속" if "완속" in part_name_clean or "5핀" in part_name_clean else "급속")
        for p in pricing:
            if p["name"] == "충전케이블" and p["category"] == target_cat:
                # If specific amps/types match
                if "200a" in part_name_clean and "200a" in p["spec"].lower():
                    return p
                if "150a" in part_name_clean and "150a" in p["spec"].lower():
                    return p
        # Default category cable
        cables = [p for p in pricing if p["name"] == "충전케이블" and p["category"] == target_cat]
        if cables:
            return cables[0]
            
    # 7. 파워모듈
    if "파워모듈" in part_name_clean or "파워팩" in part_name_clean or "reg" in part_name_clean:
        target_spec = "30kw" if "30kw" in part_name_clean or "1k0100g" in part_name_clean else "15kw"
        for p in pricing:
            if p["name"] == "파워모듈" and target_spec in p["spec"].lower():
                return p
        return [p for p in pricing if p["name"] == "파워모듈"][0]
        
    # 8. LCD
    if "lcd" in part_name_clean or "액정" in part_name_clean or "화면" in part_name_clean or "패널" in part_name_clean:
        for p in pricing:
            if p["name"] == "LCD":
                return p
                
    # Generic partial name search
    for p in pricing:
        if part_name_clean in p["name"].lower().replace(" ", "") or p["name"].lower().replace(" ", "") in part_name_clean:
            return p
            
    # Return default empty values
    return {
        "num": 0,
        "category": category or "공용",
        "name": part_name,
        "spec": "수동 입력 품목",
        "contract_price": 0,
        "cs_price": 0
    }
