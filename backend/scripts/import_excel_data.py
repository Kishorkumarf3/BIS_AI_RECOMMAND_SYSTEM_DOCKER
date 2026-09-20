"""
Excel Data Ingestion Script for BIS Standards Platform:
1. Reads extracted IS code data from extracted_results (1).xlsx (2,494 entries).
2. Cleans & normalizes IS numbers (e.g. 'IS 12615 : 2018' -> 'IS 12615:2018').
3. Infers categories (Electrical, Steel, Civil, Mechanical, etc.) based on keywords.
4. Inserts/Upserts standards, QCO Alerts, and Simplified Procedure (Option 2) records into SQLite (bis_standards.db).
5. Generates dense vector embeddings using SentenceTransformers and upserts into embedded Qdrant vector storage.
"""

import os
import sys
import re
import pandas as pd
from pathlib import Path

# Ensure backend root is on sys.path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy.orm import Session
from database import engine, SessionLocal, Base
from database.models import Standard, QCOAlert, SimplifiedProcedure754
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.http import models as qdrant_models

# Reconfigure stdout for Windows console UTF-8
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

PROJECT_ROOT = backend_dir.parent.parent
EXCEL_PATH = PROJECT_ROOT / "extracted_results (1).xlsx"

CATEGORY_KEYWORDS = {
    "Steel & Metallurgy": ["steel", "iron", "billet", "ingot", "wire", "forging", "strip", "tube", "pipe", "ferro", "alloy"],
    "Electrical & Electronics": ["electric", "cable", "motor", "conductor", "heater", "watt", "appliance", "plug", "socket", "volt", "switch", "lighting", "meter", "induction", "a.c."],
    "Civil & Construction Materials": ["cement", "concrete", "brick", "plywood", "board", "flooring", "tile", "wood", "veneer", "timber", "block", "refractory"],
    "Plastics, Chemicals & Rubber": ["pvc", "polyethylene", "polypropylene", "polymer", "hdpe", "upvc", "plastic", "rubber", "chemical", "salt", "chlorine", "resin", "adhesive"],
    "Food & Agriculture": ["milk", "powder", "cheese", "dairy", "biscuit", "formula", "food", "feed", "cattle", "cereal", "grain", "tea", "coffee", "sugar"],
    "Textiles & Garments": ["textile", "sacks", "woven", "fabric", "cotton", "garment", "jute", "yarn", "coveralls"],
    "Pumps & Mechanical Equipment": ["pump", "submersible", "emitter", "irrigation", "valve", "engine", "gear", "machine", "compressor", "drill", "saw", "grinder", "wrench", "tool"],
    "Medical & Healthcare": ["medical", "gloves", "surgical", "syringe", "mask", "dressing", "healthcare"],
}

QCO_MANDATORY_CATEGORIES = [
    "Steel & Metallurgy",
    "Civil & Construction Materials",
    "Electrical & Electronics",
    "Medical & Healthcare",
]


def infer_category(text: str) -> str:
    lower = text.lower()
    for cat, kws in CATEGORY_KEYWORDS.items():
        if any(kw in lower for kw in kws):
            return cat
    return "General Engineering & Consumer Goods"


def clean_is_code(raw: str) -> str:
    if not isinstance(raw, str) or not raw.strip():
        return ""
    cleaned = raw.strip()
    cleaned = re.sub(r"\s+", " ", cleaned)
    cleaned = re.sub(r"\s*:\s*", ":", cleaned)
    return cleaned


def main():
    if not EXCEL_PATH.exists():
        print(f"[!] Error: {EXCEL_PATH} not found!")
        sys.exit(1)

    print("=" * 70)
    print("BIS EXCEL DATA INGESTION & SEEDING ENGINE")
    print("=" * 70)
    print(f"[*] Reading Excel data from: {EXCEL_PATH.name}")

    df = pd.read_excel(EXCEL_PATH)
    print(f"[*] Total rows in Excel: {len(df)}")

    processed_standards = {}

    for idx, row in df.iterrows():
        raw_is = str(row.get("IS_Number", ""))
        is_code = clean_is_code(raw_is)
        if not is_code:
            continue

        prod_topic = str(row.get("Product_or_Topic", "")).strip()
        if prod_topic == "nan" or not prod_topic:
            prod_topic = is_code

        summary = str(row.get("Summary", "")).strip()
        if summary == "nan":
            summary = ""

        source_file = str(row.get("Source_File", "")).strip()
        page_num = row.get("Page_Number", "")

        category = infer_category(f"{prod_topic} {summary}")

        if is_code not in processed_standards:
            processed_standards[is_code] = {
                "is_code": is_code,
                "title": prod_topic,
                "summary": summary,
                "source": f"{source_file} (Page {page_num})",
                "category": category,
            }
        else:
            existing = processed_standards[is_code]
            if len(prod_topic) > len(existing["title"]) and prod_topic != is_code:
                existing["title"] = prod_topic
            if len(summary) > len(existing["summary"]):
                existing["summary"] = summary

    print(f"[*] Processed {len(processed_standards)} unique IS codes from Excel.")

    # 1. Populate SQLite Database
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()

    inserted_count = 0
    updated_count = 0

    try:
        for is_code, item in processed_standards.items():
            std = db.query(Standard).filter(Standard.is_code == is_code).first()

            scope_text = item["summary"]
            if not scope_text:
                scope_text = f"Covers requirements, quality parameters, and specifications for {item['title']}."
            else:
                scope_text = f"{scope_text} (Specification: {item['title']})."

            if not std:
                std = Standard(
                    is_code=is_code,
                    title=item["title"],
                    category=item["category"],
                    scope=scope_text,
                    status="Active",
                )
                db.add(std)
                db.flush()
                inserted_count += 1
            else:
                if std.title in ["Title", "IS Number"] or len(item["title"]) > len(std.title):
                    std.title = item["title"]
                if len(scope_text) > len(std.scope or ""):
                    std.scope = scope_text
                std.category = item["category"]
                updated_count += 1

            # Option 2 Simplified Procedure entry
            if not std.simplified_procedure:
                sp = SimplifiedProcedure754(
                    standard_id=std.id,
                    product_name=item["title"],
                    option2_eligible=True,
                    fast_track_days=30,
                    notes="Eligible for Option 2 Simplified Procedure (Grant of license within 30 days).",
                )
                db.add(sp)

            # QCO Alert entry
            is_qco = item["category"] in QCO_MANDATORY_CATEGORIES
            is_crs = "electronics" in item["category"].lower() or "meter" in item["title"].lower()
            if not std.qco_alert:
                qco = QCOAlert(
                    standard_id=std.id,
                    qco_notification="Mandatory Quality Control Order (Ministry of Commerce & Industry / BIS)" if is_qco else None,
                    is_mandatory=is_qco,
                    crs_applicable=is_crs,
                    penalty_non_compliance="Non-compliance attracts penal provisions under Section 29 of the BIS Act, 2016.",
                )
                db.add(qco)

        db.commit()
        total_db_standards = db.query(Standard).count()
        print(f"[+] SQLite Population Complete!")
        print(f"    - Inserted new standards: {inserted_count}")
        print(f"    - Updated existing standards: {updated_count}")
        print(f"    - Total standards in bis_standards.db: {total_db_standards}")

    finally:
        db.close()

    # 2. Populate Qdrant Vector DB
    COLLECTION_NAME = "bis_standards"
    EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    print(f"[*] Initializing embedding model ({EMBEDDING_MODEL_NAME})...")

    try:
        model = SentenceTransformer(EMBEDDING_MODEL_NAME)
        vector_size = model.get_sentence_embedding_dimension()

        local_qdrant_path = backend_dir / "qdrant_storage"
        local_qdrant_path.mkdir(exist_ok=True)
        qclient = QdrantClient(path=str(local_qdrant_path))

        collections = qclient.get_collections().collections
        exists = any(c.name == COLLECTION_NAME for c in collections)
        if not exists:
            qclient.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=qdrant_models.VectorParams(
                    size=vector_size,
                    distance=qdrant_models.Distance.COSINE,
                ),
            )

        print(f"[*] Generating embeddings for {len(processed_standards)} standards...")
        std_list = list(processed_standards.values())
        texts = [
            f"{s['is_code']}: {s['title']}. Category: {s['category']}. {s['summary']}"
            for s in std_list
        ]
        vectors = model.encode(texts, batch_size=32, show_progress_bar=True, normalize_embeddings=True)

        points = []
        for idx, (s, vec) in enumerate(zip(std_list, vectors)):
            is_qco = s["category"] in QCO_MANDATORY_CATEGORIES
            is_crs = "electronics" in s["category"].lower() or "meter" in s["title"].lower()

            points.append(
                qdrant_models.PointStruct(
                    id=idx + 5000,
                    vector=vec.tolist(),
                    payload={
                        "is_code": s["is_code"],
                        "title": s["title"],
                        "scope": s["summary"] or f"Covers requirements, quality parameters, and specifications for {s['title']}.",
                        "category": s["category"],
                        "qco_mandatory": is_qco,
                        "crs_applicable": is_crs,
                        "simplified_procedure": True,
                        "doc_type": "standard",
                    },
                )
            )

        batch_size = 100
        for i in range(0, len(points), batch_size):
            qclient.upsert(
                collection_name=COLLECTION_NAME,
                points=points[i:i + batch_size],
            )

        print(f"[+] Qdrant Vector DB updated with {len(points)} vector points!")

    except Exception as e:
        print(f"[!] Vector embedding update warning: {e}")

    print("=" * 70)
    print("[SUCCESS] Data from extracted_results (1).xlsx stored into database successfully!")
    print("=" * 70)


if __name__ == "__main__":
    main()
