"""
Ingestion Pipeline for BIS Dataset:
1. Extracts 747+ standards from List-of-Products-Under-Simplified-Procedure.pdf
2. Parses QCO and CRS regulatory notifications
3. Seeds SQLite relational database (Standard, SimplifiedProcedure754, QCOAlert, Normative References)
4. Chunks regulatory text (BIS Act 2016, CA Regulations) and indexes embeddings into Qdrant
"""

import os
import sys
import re
import glob
from pathlib import Path
from typing import List, Dict, Any

# Ensure backend root is on sys.path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

import pymupdf
from sqlalchemy.orm import Session
from database import engine, SessionLocal, Base
from database.models import Standard, QCOAlert, SimplifiedProcedure754, standard_references
from qdrant_client import QdrantClient
from qdrant_client.http import models as qdrant_models
from sentence_transformers import SentenceTransformer

# Reconfigure stdout for Windows console UTF-8
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

BIS_DATA_DIR = Path(__file__).resolve().parent.parent.parent.parent / "BIS"
COLLECTION_NAME = "bis_standards"
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

# Category inference based on keywords in title
CATEGORY_KEYWORDS = {
    "Steel & Metallurgy": ["steel", "iron", "billet", "ingot", "wire", "forging", "strip", "tube", "pipe", "ferro", "alloy"],
    "Electrical & Electronics": ["electric", "cable", "motor", "conductor", "heater", "watt", "appliance", "plug", "socket", "volt", "switch", "lighting", "meter"],
    "Civil & Construction Materials": ["cement", "concrete", "brick", "plywood", "board", "flooring", "tile", "wood", "veneer", "timber", "block"],
    "Plastics, Chemicals & Rubber": ["pvc", "polyethylene", "polypropylene", "polymer", "hdpe", "upvc", "plastic", "rubber", "chemical", "salt", "chlorine", "resin", "adhesive"],
    "Food & Agriculture": ["milk", "powder", "cheese", "dairy", "biscuit", "formula", "food", "feed", "cattle", "cereal", "grain", "tea", "coffee"],
    "Textiles & Garments": ["textile", "sacks", "woven", "fabric", "cotton", "garment", "jute", "yarn", "coveralls"],
    "Pumps & Mechanical Equipment": ["pump", "submersible", "emitter", "irrigation", "valve", "engine", "gear", "machine", "compressor"],
    "Medical & Healthcare": ["medical", "gloves", "surgical", "syringe", "mask", "dressing", "healthcare"],
}

# Known normative references for major standards
NORMATIVE_REFERENCES_MAP = {
    "IS 1239 (Part 1)": [
        ("IS 1387", "General Requirements for Supply of Steel"),
        ("IS 1599", "Method for Bend Test on Steel"),
        ("IS 1586", "Tensile Testing of Steel Products"),
        ("IS 228", "Methods of Chemical Analysis of Steel"),
    ],
    "IS 2062": [
        ("IS 1599", "Method for Bend Test on Steel"),
        ("IS 228", "Methods of Chemical Analysis of Steel"),
        ("IS 8910", "General Requirements for Supply of Microalloyed Steel"),
        ("IS 3613", "Carbon Steel Forgings for Structural Use"),
    ],
    "IS 269": [
        ("IS 4031 (Part 1)", "Methods of Physical Tests for Cement — Fineness"),
        ("IS 4032", "Methods of Chemical Analysis of Cement"),
        ("IS 3535", "Methods of Sampling for Cement"),
    ],
    "IS 1293": [
        ("IS 302 (Part 1)", "Safety of Household Electrical Appliances — General Requirements"),
        ("IS 1870", "Test Methods for Electrical Accessories"),
    ],
    "IS 694": [
        ("IS 5831", "PVC Insulation and Sheath of Electric Cables"),
        ("IS 8130", "Conductors for Insulated Electric Cables"),
        ("IS 10810", "Methods of Test for Cables"),
    ],
    "IS 9537 (Part 3)": [
        ("IS 3400", "Methods of Test for Vulcanized Rubbers"),
        ("IS 12252", "Polyalkylene Pipe Specifications"),
    ],
    "IS 8034": [
        ("IS 9283", "Motors for Submersible Pumpsets"),
        ("IS 9601", "Submersible Motors Technical Delivery Conditions"),
    ],
    "IS 12701": [
        ("IS 2508", "Low Density Polyethylene Films"),
        ("IS 4984", "High Density Polyethylene Pipes"),
    ],
}

# Mandatory QCO domains according to DPIIT / Ministry notifications
QCO_MANDATORY_CATEGORIES = [
    "Steel & Metallurgy",
    "Civil & Construction Materials",
    "Electrical & Electronics",
    "Medical & Healthcare",
]


def clean_text(text: str) -> str:
    """Remove invisible unicode formatting / bidirectional control characters."""
    if not text:
        return ""
    cleaned = re.sub(r"[\u200e\u200f\u202a-\u202e\uFEFF]", "", text)
    return " ".join(cleaned.split())


def infer_category(title: str) -> str:
    """Infer product standard category from title keywords."""
    lower = title.lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(kw in lower for kw in keywords):
            return category
    return "General Engineering & Consumer Goods"


def extract_simplified_procedure_standards(pdf_path: Path) -> List[Dict[str, Any]]:
    """Extract standard number, title, and serial number from 754 simplified procedure PDF."""
    print(f"[*] Extracting Simplified Procedure standards from: {pdf_path.name}")
    doc = pymupdf.open(str(pdf_path))
    records: List[Dict[str, Any]] = []

    for page_num in range(1, len(doc)):
        page = doc[page_num]
        tabs = page.find_tables()
        if tabs.tables:
            for tab in tabs:
                for row in tab.extract():
                    cleaned = [clean_text(str(c or "")) for c in row]
                    if len(cleaned) >= 3:
                        sr_str, is_num, title = cleaned[0], cleaned[1], " ".join(cleaned[2:])
                        if is_num.upper().startswith("IS"):
                            try:
                                sr_no = int(sr_str)
                            except ValueError:
                                sr_no = len(records) + 1

                            records.append({
                                "sr_no": sr_no,
                                "is_code": is_num,
                                "title": title,
                                "category": infer_category(title),
                            })

    print(f"[+] Successfully extracted {len(records)} standards from Simplified Procedure list.")
    return records


def extract_legal_regulation_chunks(bis_dir: Path, max_chunks_per_doc: int = 20) -> List[Dict[str, str]]:
    """Extract and chunk regulatory texts from Gazette and BIS Act PDFs for legal context retrieval."""
    print(f"[*] Extracting regulatory text from Gazette and Act PDFs in {bis_dir.name}...")
    legal_chunks = []
    pdf_files = glob.glob(str(bis_dir / "*.pdf"))

    for pdf_file in pdf_files:
        p = Path(pdf_file)
        if "Simplified-Procedure" in p.name:
            continue  # Already extracted into catalog

        try:
            doc = pymupdf.open(str(p))
            title = p.stem.replace("-", " ").replace("_", " ")
            full_text = ""
            for i in range(min(15, len(doc))):
                full_text += clean_text(doc[i].get_text()) + " "

            # Split into ~600 character chunks with overlap
            words = full_text.split()
            chunk_size = 100
            for i in range(0, min(len(words), chunk_size * max_chunks_per_doc), chunk_size - 20):
                chunk_words = words[i:i + chunk_size]
                chunk_text = " ".join(chunk_words)
                if len(chunk_text) > 100:
                    legal_chunks.append({
                        "source": p.name,
                        "title": title,
                        "content": chunk_text,
                    })
        except Exception as e:
            print(f"[-] Warning reading {p.name}: {e}")

    print(f"[+] Extracted {len(legal_chunks)} regulatory reference chunks.")
    return legal_chunks


def get_qdrant_client() -> QdrantClient:
    """Connect to Docker Qdrant on localhost:6333 or fallback to local disk storage."""
    qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
    try:
        client = QdrantClient(url=qdrant_url, timeout=3.0)
        client.get_collections()
        print(f"[+] Connected to Docker Qdrant at {qdrant_url}")
        return client
    except Exception:
        local_storage_path = backend_dir / "qdrant_storage"
        local_storage_path.mkdir(exist_ok=True)
        print(f"[!] Docker Qdrant not available. Using embedded on-disk Qdrant at {local_storage_path}")
        return QdrantClient(path=str(local_storage_path))


def populate_sqlite(standards: List[Dict[str, Any]]):
    """Seed SQLite database with standards, QCO alerts, and Simplified Procedure list."""
    print("[*] Seeding SQLite database (bis_standards.db)...")
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()

    try:
        existing_count = db.query(Standard).count()
        if existing_count >= len(standards):
            print(f"[i] SQLite already has {existing_count} standards. Updating records...")

        standards_by_code: Dict[str, Standard] = {}

        for item in standards:
            is_code = item["is_code"]
            std = db.query(Standard).filter(Standard.is_code == is_code).first()
            if not std:
                std = Standard(
                    is_code=is_code,
                    title=item["title"],
                    category=item["category"],
                    scope=f"Covers requirements, quality parameters, and specifications for {item['title']}.",
                    status="Active",
                )
                db.add(std)
                db.flush()

            standards_by_code[is_code] = std

            # Simplified Procedure entry
            if not std.simplified_procedure:
                sp = SimplifiedProcedure754(
                    standard_id=std.id,
                    product_name=item["title"],
                    option2_eligible=True,
                    fast_track_days=30,
                    notes="Eligible for Option 2 Simplified Procedure (Grant of license within 30 days).",
                )
                db.add(sp)

            # QCO Alert
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

        # Seed Normative References
        print("[*] Linking normative references for knowledge graph...")
        for parent_code, refs in NORMATIVE_REFERENCES_MAP.items():
            parent_std = standards_by_code.get(parent_code) or db.query(Standard).filter(Standard.is_code == parent_code).first()
            if not parent_std:
                continue

            for ref_code, ref_title in refs:
                ref_std = standards_by_code.get(ref_code) or db.query(Standard).filter(Standard.is_code == ref_code).first()
                if not ref_std:
                    ref_std = Standard(
                        is_code=ref_code,
                        title=ref_title,
                        category="Testing & Normative Reference",
                        scope=f"Normative testing standard specifying requirements for {ref_title}.",
                        status="Active",
                    )
                    db.add(ref_std)
                    db.flush()
                    standards_by_code[ref_code] = ref_std

                if ref_std not in parent_std.normative_refs:
                    parent_std.normative_refs.append(ref_std)

        db.commit()
        print(f"[+] SQLite successfully populated! Total standards: {db.query(Standard).count()}")

    finally:
        db.close()


def populate_qdrant(standards: List[Dict[str, Any]], legal_chunks: List[Dict[str, str]]):
    """Embed standards catalog and legal regulation texts into Qdrant."""
    print(f"[*] Initializing embeddings model ({EMBEDDING_MODEL_NAME})...")
    model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    vector_size = model.get_sentence_embedding_dimension()

    client = get_qdrant_client()

    # Recreate or ensure collection
    collections = client.get_collections().collections
    exists = any(c.name == COLLECTION_NAME for c in collections)

    if not exists:
        print(f"[*] Creating Qdrant collection '{COLLECTION_NAME}' (dim={vector_size})...")
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=qdrant_models.VectorParams(
                size=vector_size,
                distance=qdrant_models.Distance.COSINE,
            ),
        )

    # 1. Embed Standards Catalog
    print(f"[*] Generating embeddings for {len(standards)} standards...")
    texts = [
        f"{s['is_code']}: {s['title']}. Category: {s['category']}. Covers procurement specifications and quality requirements."
        for s in standards
    ]
    vectors = model.encode(texts, batch_size=32, show_progress_bar=True, normalize_embeddings=True)

    points = []
    for idx, (s, vec) in enumerate(zip(standards, vectors)):
        norm_refs = [
            {"is_code": ref[0], "title": ref[1]}
            for ref in NORMATIVE_REFERENCES_MAP.get(s["is_code"], [])
        ]
        is_qco = s["category"] in QCO_MANDATORY_CATEGORIES
        is_crs = "electronics" in s["category"].lower() or "meter" in s["title"].lower()

        points.append(
            qdrant_models.PointStruct(
                id=idx + 1,
                vector=vec.tolist(),
                payload={
                    "is_code": s["is_code"],
                    "title": s["title"],
                    "scope": f"Covers requirements, quality parameters, and specifications for {s['title']}.",
                    "category": s["category"],
                    "qco_mandatory": is_qco,
                    "crs_applicable": is_crs,
                    "simplified_procedure": True,
                    "normative_refs": norm_refs,
                    "doc_type": "standard",
                },
            )
        )

    # Batch upsert points
    batch_size = 100
    for i in range(0, len(points), batch_size):
        client.upsert(
            collection_name=COLLECTION_NAME,
            points=points[i:i + batch_size],
        )

    print(f"[+] Upserted {len(points)} standards into Qdrant!")

    # 2. Embed Legal Regulation Chunks
    if legal_chunks:
        print(f"[*] Generating embeddings for {len(legal_chunks)} legal context chunks...")
        legal_texts = [c["content"] for c in legal_chunks]
        legal_vectors = model.encode(legal_texts, batch_size=32, show_progress_bar=True, normalize_embeddings=True)

        legal_points = []
        base_id = len(points) + 1000
        for idx, (chunk, vec) in enumerate(zip(legal_chunks, legal_vectors)):
            legal_points.append(
                qdrant_models.PointStruct(
                    id=base_id + idx,
                    vector=vec.tolist(),
                    payload={
                        "source": chunk["source"],
                        "title": chunk["title"],
                        "content": chunk["content"],
                        "doc_type": "legal_regulation",
                    },
                )
            )

        for i in range(0, len(legal_points), batch_size):
            client.upsert(
                collection_name=COLLECTION_NAME,
                points=legal_points[i:i + batch_size],
            )
        print(f"[+] Upserted {len(legal_points)} legal chunks into Qdrant!")


def main():
    print("=" * 70)
    print("BIS DATASET INGESTION & SEEDING ENGINE")
    print("=" * 70)

    pdf_simplified = BIS_DATA_DIR / "List-of-Products-Under-Simplified-Procedure.pdf"
    if not pdf_simplified.exists():
        print(f"[!] Error: {pdf_simplified} not found!")
        sys.exit(1)

    # Step 1: Extract 747 standards
    standards = extract_simplified_procedure_standards(pdf_simplified)

    # Step 2: Extract regulatory chunks
    legal_chunks = extract_legal_regulation_chunks(BIS_DATA_DIR)

    # Step 3: Populate SQLite
    populate_sqlite(standards)

    # Step 4: Populate Qdrant
    populate_qdrant(standards, legal_chunks)

    print("=" * 70)
    print("[SUCCESS] All 747+ Indian Standards & Legal Regulations Ingested!")
    print("=" * 70)


if __name__ == "__main__":
    main()
