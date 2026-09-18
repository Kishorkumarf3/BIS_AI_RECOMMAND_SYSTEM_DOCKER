import os
import sys
from pathlib import Path
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.http import models as qdrant_models

backend_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(backend_dir))

from database import SessionLocal, Base, engine
from database.models import Standard, QCOAlert, SimplifiedProcedure754

NEW_STANDARDS = [
    {
        "is_code": "IS 4037",
        "title": "Specification for Hospital Bed, Fowler Beds",
        "category": "Medical & Healthcare",
        "subcategory": "Hospital Furniture",
        "scope": "Covers requirements, dimensions, materials, and functional specifications for Fowler hospital beds with adjustable backrest, knee rest, and foldable or detachable head and foot bows for inpatient wards and ICUs.",
        "is_qco": True,
        "is_crs": False,
        "option2": True,
        "normative_refs": [
            ("IS 2062", "Steel for General Structural Purposes"),
            ("IS 1363 (Part 1)", "Hexagon Head Bolts, Screws and Nuts")
        ]
    },
    {
        "is_code": "IS 503",
        "title": "Specification for Bedsteads, Hospital, General Purposes",
        "category": "Medical & Healthcare",
        "subcategory": "Hospital Furniture",
        "scope": "Specifies dimensional and constructional requirements for hospital bedsteads and beds for general inpatient use, including framing, tubular steel construction, and epoxy powder coating.",
        "is_qco": True,
        "is_crs": False,
        "option2": True,
        "normative_refs": [
            ("IS 2062", "Steel for General Structural Purposes")
        ]
    },
    {
        "is_code": "IS 504",
        "title": "Specification for Bedsteads, Hospital, Special Purposes",
        "category": "Medical & Healthcare",
        "subcategory": "Hospital Furniture",
        "scope": "Covers requirements for specialized hospital bedsteads and beds for maternity, pediatric, and orthopedic wards.",
        "is_qco": True,
        "is_crs": False,
        "option2": True,
        "normative_refs": [
            ("IS 2062", "Steel for General Structural Purposes")
        ]
    },
    {
        "is_code": "IS 13488",
        "title": "Hospital Furniture - Intensive Care Bed (ICU Bed) - Specification",
        "category": "Medical & Healthcare",
        "subcategory": "Hospital Furniture",
        "scope": "Covers mechanical, electrical, and structural specifications for intensive care hospital beds (ICU beds) with multi-position adjustments, collapsible and foldable side railings, and CPR release.",
        "is_qco": True,
        "is_crs": False,
        "option2": True,
        "normative_refs": [
            ("IS 2062", "Steel for General Structural Purposes")
        ]
    },
    {
        "is_code": "IS 5025",
        "title": "Specification for Obstetric Labour Beds",
        "category": "Medical & Healthcare",
        "subcategory": "Hospital Furniture",
        "scope": "Specifies constructional and functional requirements for obstetric labour and delivery beds with adjustable tilting mechanism and sliding leg section.",
        "is_qco": True,
        "is_crs": False,
        "option2": True,
        "normative_refs": []
    },
    {
        "is_code": "IS 7378",
        "title": "Specification for Bedside Lockers for Hospital Use",
        "category": "Medical & Healthcare",
        "subcategory": "Hospital Furniture",
        "scope": "Specifies requirements for hospital bedside lockers, cabinets, and bedside tables for inpatient hospital rooms.",
        "is_qco": True,
        "is_crs": False,
        "option2": True,
        "normative_refs": []
    },
    {
        "is_code": "IS 4036",
        "title": "Specification for Hospital Furniture, Bedside Screen (Folding Type)",
        "category": "Medical & Healthcare",
        "subcategory": "Hospital Furniture",
        "scope": "Specifies requirements for portable, folding bedside privacy screens with 3 or 4 folds for hospital wards.",
        "is_qco": True,
        "is_crs": False,
        "option2": True,
        "normative_refs": []
    },
    {
        "is_code": "IS 12993",
        "title": "Wheelchairs, Folding, Junior Size - Specification",
        "category": "Medical & Healthcare",
        "subcategory": "Hospital Equipment",
        "scope": "Specifies requirements for folding wheelchairs designed for pediatric and junior patients in hospitals.",
        "is_qco": True,
        "is_crs": False,
        "option2": True,
        "normative_refs": []
    },
    {
        "is_code": "IS 7454",
        "title": "Hospital Furniture - Revolving Stool - Specification",
        "category": "Medical & Healthcare",
        "subcategory": "Hospital Furniture",
        "scope": "Specifies requirements for revolving stools used by medical staff in operation theaters and hospital wards.",
        "is_qco": True,
        "is_crs": False,
        "option2": True,
        "normative_refs": []
    }
]

def add_to_sqlite():
    db = SessionLocal()
    try:
        for item in NEW_STANDARDS:
            std = db.query(Standard).filter(Standard.is_code == item["is_code"]).first()
            if not std:
                std = Standard(
                    is_code=item["is_code"],
                    title=item["title"],
                    category=item["category"],
                    subcategory=item.get("subcategory"),
                    scope=item["scope"],
                    status="Active",
                )
                db.add(std)
                db.flush()
                print(f"[SQLite] Added {item['is_code']}")

                # QCO Alert
                qco = QCOAlert(
                    standard_id=std.id,
                    qco_notification="Ministry of Health / BIS Mandatory QCO Order",
                    is_mandatory=item["is_qco"],
                    crs_applicable=item["is_crs"],
                    penalty_non_compliance="Mandatory compliance under Section 16 & Section 29 of the BIS Act, 2016.",
                )
                db.add(qco)

                # Option 2 Simplified
                if item["option2"]:
                    sp = SimplifiedProcedure754(
                        standard_id=std.id,
                        product_name=item["title"],
                        option2_eligible=True,
                        fast_track_days=30,
                    )
                    db.add(sp)
            else:
                std.title = item["title"]
                std.category = item["category"]
                std.scope = item["scope"]
                print(f"[SQLite] Updated {item['is_code']}")

        db.commit()
        print("[SQLite] Successfully updated SQLite standards!")
    finally:
        db.close()

def add_to_qdrant():
    storage_path = backend_dir / "qdrant_storage"
    client = QdrantClient(path=str(storage_path))
    model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

    points = []
    # Find next available id
    count_res = client.count("bis_standards")
    print(f"[Qdrant] Existing points count: {count_res.count}")

    for idx, item in enumerate(NEW_STANDARDS):
        text = f"{item['is_code']}: {item['title']}. Category: {item['category']}. Scope: {item['scope']}"
        vec = model.encode(text, normalize_embeddings=True)

        # check if is_code exists or create point with unique ID
        # use deterministic hash or large offset
        point_id = 90000 + idx
        norm_refs = [{"is_code": ref[0], "title": ref[1]} for ref in item.get("normative_refs", [])]

        points.append(
            qdrant_models.PointStruct(
                id=point_id,
                vector=vec.tolist(),
                payload={
                    "is_code": item["is_code"],
                    "title": item["title"],
                    "scope": item["scope"],
                    "category": item["category"],
                    "qco_mandatory": item["is_qco"],
                    "crs_applicable": item["is_crs"],
                    "simplified_procedure": item["option2"],
                    "normative_refs": norm_refs,
                    "doc_type": "standard",
                }
            )
        )

    client.upsert(
        collection_name="bis_standards",
        points=points
    )
    print(f"[Qdrant] Successfully upserted {len(points)} points into Qdrant!")

if __name__ == "__main__":
    add_to_sqlite()
    add_to_qdrant()
