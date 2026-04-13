"""csData xlsx 컬럼·행 수 요약 → UTF-8 리포트 파일로 저장."""
from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
CS = ROOT / "csData"
OUT = Path(__file__).resolve().parent / "column_report.txt"


def norm(s: str) -> str:
    s = str(s).replace("\n", " ").strip()
    return re.sub(r"\s+", " ", s)


def main() -> None:
    lines: list[str] = []
    files = sorted(CS.rglob("*.xlsx"))
    lines.append(f"csData xlsx: {len(files)}개\n")
    for fp in files:
        rel = fp.relative_to(ROOT).as_posix()
        try:
            xl = pd.ExcelFile(fp, engine="openpyxl")
        except Exception as e:
            lines.append(f"\n## {rel}\nERROR: {e}\n")
            continue
        lines.append(f"\n## {rel}")
        for sn in xl.sheet_names:
            try:
                df = pd.read_excel(fp, sheet_name=sn, header=None, nrows=30, engine="openpyxl")
            except Exception as e:
                lines.append(f"\n  [{sn}] read error: {e}")
                continue
            # 흔한 패턴: 앞 몇 행에 제목, 그 다음 헤더
            lines.append(f"\n  시트: {sn} | 샘플 30행 x {df.shape[1]}열")
            for ri in range(min(8, len(df))):
                row = [norm(x) if pd.notna(x) else "" for x in df.iloc[ri].tolist()]
                row = [x for x in row if x][:20]
                if row:
                    lines.append(f"    R{ri}: " + " | ".join(row)[:500])
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print("Wrote", OUT)


if __name__ == "__main__":
    main()
