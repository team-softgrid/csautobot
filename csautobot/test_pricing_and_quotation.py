import sys
from pathlib import Path

# Setup python path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from services.pricing_service import lookup_part_pricing, get_pricing_list
from services.quotation_service import QuotationDraft, PartDetail

def test_pricing_lookups():
    print("=== Testing Pricing Lookup Logic ===")
    
    # Test 1: PLC Modem lookup
    plc = lookup_part_pricing("PLC 모뎀", "급속")
    print(f"1. PLC Modem: {plc['name']} | Spec: {plc['spec']} | Price: {plc['contract_price']:,} 원")
    assert plc["name"] == "PLC 모뎀", "Name mismatch"
    assert plc["contract_price"] == 500000, "Price mismatch"
    
    # Test 2: Board lookup
    board = lookup_part_pricing("UC1 보드", "완속")
    print(f"2. UC1 Board: {board['name']} | Spec: {board['spec']} | Price: {board['contract_price']:,} 원")
    assert board["contract_price"] == 525000, "Price mismatch"
    
    # Test 3: Circuit Breaker lookup
    cb = lookup_part_pricing("전력 차단기", "급속")
    print(f"3. Circuit Breaker: {cb['name']} | Spec: {cb['spec']} | Price: {cb['contract_price']:,} 원")
    assert cb["contract_price"] == 260000, "Price mismatch"
    
    # Test 4: Cable lookup
    cable = lookup_part_pricing("완속충전 케이블", "완속")
    print(f"4. Cable: {cable['name']} | Spec: {cable['spec']} | Price: {cable['contract_price']:,} 원")
    assert cable["contract_price"] == 120000, "Price mismatch"
    
    # Test 5: Fallback generic lookup
    unknown = lookup_part_pricing("비정형 임시 부품", "공용")
    print(f"5. Unknown part fallback: {unknown['name']} | Price: {unknown['contract_price']} 원")
    assert unknown["contract_price"] == 0, "Fallback price should be 0"

def test_math_calculation():
    print("\n=== Testing Calculation Math ===")
    # Simulate parts detail list
    parts = [
        PartDetail(part_name="PLC 모뎀", spec="신형", qty=2, unit_price=500000, total_price=1000000, category="급속"),
        PartDetail(part_name="AC미터", spec="좌타입", qty=1, unit_price=130000, total_price=130000, category="급속")
    ]
    
    parts_total = sum(x.total_price for x in parts)
    dispatch_fee = 100000
    labor_fee = 70000
    
    supply_value = parts_total + dispatch_fee + labor_fee
    vat = int(supply_value * 0.1)
    total_amount = supply_value + vat
    
    draft = QuotationDraft(
        symptom_summary="모의 증상",
        likely_cause="모의 원인",
        parts=parts,
        dispatch_fee=dispatch_fee,
        labor_fee=labor_fee,
        supply_value=supply_value,
        vat=vat,
        total_amount=total_amount
    )
    
    print(f"Parts Subtotal: {parts_total:,} 원")
    print(f"Dispatch Fee: {draft.dispatch_fee:,} 원")
    print(f"Labor Fee: {draft.labor_fee:,} 원")
    print(f"Supply Value (공급가액): {draft.supply_value:,} 원")
    print(f"VAT (부가세): {draft.vat:,} 원")
    print(f"Grand Total (최종 합계): {draft.total_amount:,} 원")
    
    assert parts_total == 1130000, "Parts total mismatch"
    assert draft.supply_value == 1300000, "Supply value mismatch"
    assert draft.vat == 130000, "VAT mismatch"
    assert draft.total_amount == 1430000, "Grand total mismatch"
    print("Math verified successfully!")

if __name__ == '__main__':
    try:
        test_pricing_lookups()
        test_math_calculation()
        print("\nAll unit tests passed successfully!")
    except AssertionError as e:
        print(f"\nAssertion error: {e}")
        sys.exit(1)
