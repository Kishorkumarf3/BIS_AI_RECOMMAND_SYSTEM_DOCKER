"""
Ingest user-provided BIS Certification Rules & Standards dataset:
- Reads backend/data/bis_rules.json
- Seeds/updates SQLite database (Standard, QCOAlert, SimplifiedProcedure754)
- Embeds and updates vector points in Qdrant
"""

import json
import os
import re
import sys
from pathlib import Path
from typing import Dict, Any, List, Tuple

# Ensure backend root is on sys.path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from database import engine, SessionLocal, Base
from database.models import Standard, QCOAlert, SimplifiedProcedure754

DATA_FILE = backend_dir / "data" / "bis_rules.json"

CATEGORY_MAP = {
    # Water & Beverages
    "Packaged Drinking Water": ("Food & Agriculture", "Water & Beverages"),
    "Packaged Natural Mineral Water": ("Food & Agriculture", "Water & Beverages"),
    
    # Cement & Concrete
    "Ordinary Portland Cement (OPC)": ("Civil & Construction Materials", "Cement & Concrete"),
    "Portland Pozzolana Cement (PPC)": ("Civil & Construction Materials", "Cement & Concrete"),
    "Portland Slag Cement (PSC)": ("Civil & Construction Materials", "Cement & Concrete"),
    "Plain and Reinforced Concrete": ("Civil & Construction Materials", "Structural Concrete"),
    "Ready-Mixed Concrete (RMC)": ("Civil & Construction Materials", "Concrete Products"),
    "Concrete Admixtures": ("Civil & Construction Materials", "Chemical Admixtures"),
    "Autoclaved Aerated Concrete (AAC) Blocks": ("Civil & Construction Materials", "Masonry Units"),
    "Precast Concrete Blocks": ("Civil & Construction Materials", "Masonry Units"),
    "Ceramic and Vitrified Tiles": ("Civil & Construction Materials", "Tiles & Flooring"),
    
    # Steel & Metallurgy
    "TMT Steel Bars": ("Steel & Metallurgy", "Reinforcement Bars"),
    "Structural Steel": ("Steel & Metallurgy", "Structural Sections"),
    "Galvanized Steel Tubes and Pipes": ("Steel & Metallurgy", "Steel Tubes & Pipes"),
    "Seamless Steel Gas Cylinders": ("Steel & Metallurgy", "High Pressure Cylinders"),
    
    # Pipes & Plastics
    "UPVC Pipes for Potable Water Supplies": ("Plastics, Chemicals & Rubber", "Pipes & Fittings"),
    "HDPE Pipes for Water Supply": ("Plastics, Chemicals & Rubber", "Pipes & Fittings"),
    "PVC Pipes for Agricultural Use": ("Plastics, Chemicals & Rubber", "Agricultural Pipes"),
    
    # Wood & Plywood
    "Plywood for General Purposes": ("Civil & Construction Materials", "Wood & Plywood"),
    "Marine Plywood": ("Civil & Construction Materials", "Wood & Plywood"),
    "Fire Retardant Plywood": ("Civil & Construction Materials", "Specialty Plywood"),
    "Wooden Flush Door Shutters": ("Civil & Construction Materials", "Doors & Windows"),
    
    # Automotive & Transport
    "Helmets for Two-Wheeler Riders": ("Automotive & Transport", "Rider Safety Equipment"),
    "Safety Glass for Road Transport": ("Automotive & Transport", "Automotive Safety Glass"),
    "Automotive Tyres - Passenger Car": ("Automotive & Transport", "Pneumatic Tyres"),
    "Automotive Tyres - Commercial Vehicles": ("Automotive & Transport", "Commercial Vehicle Tyres"),
    "Two and Three Wheeler Tyres": ("Automotive & Transport", "Light Vehicle Tyres"),
    "Automotive Tyre Tubes": ("Automotive & Transport", "Rubber Inner Tubes"),
    
    # Domestic Appliances & Gas
    "Domestic Pressure Cookers": ("Domestic & Consumer Appliances", "Kitchenware"),
    "Domestic Gas Stoves (LPG)": ("Domestic & Consumer Appliances", "Gas Appliances"),
    "LPG Cylinders for Domestic Use": ("Domestic & Consumer Appliances", "LPG Storage"),
    "Valves for LPG Cylinders": ("Domestic & Consumer Appliances", "LPG Accessories"),
    "Electric Iron": ("Domestic & Consumer Appliances", "Heating Appliances"),
    "Electric Immersion Water Heaters": ("Domestic & Consumer Appliances", "Water Heaters"),
    "Stationary Storage Electric Water Heaters (Geysers)": ("Domestic & Consumer Appliances", "Water Heaters"),
    "Electric Food Mixers, Grinders, and Blenders": ("Domestic & Consumer Appliances", "Food Preparation"),
    "Electric Room Heaters": ("Domestic & Consumer Appliances", "Heating Appliances"),
    "Electric Toasters": ("Domestic & Consumer Appliances", "Kitchen Appliances"),
    "Microwave Ovens": ("Domestic & Consumer Appliances", "Kitchen Appliances"),
    "Ceiling Fans and Regulators": ("Domestic & Consumer Appliances", "Air Circulation"),
    "Electric Air Coolers": ("Domestic & Consumer Appliances", "Air Cooling"),
    "Domestic Refrigerators": ("Domestic & Consumer Appliances", "Refrigeration"),
    "Room Air Conditioners": ("Domestic & Consumer Appliances", "HVAC & Air Conditioning"),
    
    # Electrical Infrastructure & Power
    "PVC Insulated Cables (up to 1100V)": ("Electrical & Electronics", "Wires & Cables"),
    "XLPE Insulated Power Cables": ("Electrical & Electronics", "Power Cables"),
    "Self-Ballasted LED Lamps": ("Electrical & Electronics", "Lighting"),
    "Fixed General Purpose LED Luminaires": ("Electrical & Electronics", "Lighting"),
    "Smart Electricity Meters": ("Electrical & Electronics", "Energy Meters"),
    "AC Static Watt-hour Meters": ("Electrical & Electronics", "Energy Meters"),
    "Miniature Circuit Breakers (MCBs)": ("Electrical & Electronics", "Switchgear & Protection"),
    "Residual Current Circuit Breakers (RCCBs)": ("Electrical & Electronics", "Switchgear & Protection"),
    "Moulded Case Circuit Breakers (MCCBs)": ("Electrical & Electronics", "Switchgear & Protection"),
    "Distribution Transformers": ("Electrical & Electronics", "Transformers"),
    "Three-Phase Induction Motors": ("Electrical & Electronics", "Electric Motors"),
    "Single-Phase AC Motors": ("Electrical & Electronics", "Electric Motors"),
    
    # Solar & Renewable Energy
    "Solar Photovoltaic (PV) Modules": ("Solar & Renewable Energy", "PV Modules"),
    "Solar Inverters": ("Solar & Renewable Energy", "Power Conditioning"),
    "Solar Flat Plate Collectors": ("Solar & Renewable Energy", "Solar Thermal"),
    
    # Electronics & IT Equipment (CRS)
    "Mobile Phones": ("Electronics & IT Equipment", "Telecommunications"),
    "Laptops and Notebooks": ("Electronics & IT Equipment", "Computing"),
    "Tablet Computers": ("Electronics & IT Equipment", "Computing"),
    "Power Banks": ("Electronics & IT Equipment", "Portable Power"),
    "Smart Watches": ("Electronics & IT Equipment", "Wearables"),
    "Secondary Lithium-ion Cells and Batteries": ("Electronics & IT Equipment", "Batteries & Storage"),
    "Secondary Nickel Cells and Batteries": ("Electronics & IT Equipment", "Batteries & Storage"),
    "Lead-Acid Storage Batteries": ("Electrical & Electronics", "Batteries & Storage"),
    "Television Sets": ("Electronics & IT Equipment", "Audio/Video Displays"),
    "Wireless Keyboards and Mice": ("Electronics & IT Equipment", "Computer Peripherals"),
    "Audio Amplifiers and Wireless Speakers": ("Electronics & IT Equipment", "Audio Equipment"),
    
    # Toys & Child Safety
    "Toys - Mechanical and Physical Properties": ("Toys & Children Products", "Toy Safety"),
    "Toys - Flammability": ("Toys & Children Products", "Toy Safety"),
    "Toys - Migration of Certain Elements": ("Toys & Children Products", "Chemical Safety"),
    "Electric Toys": ("Toys & Children Products", "Electrical Safety"),
    
    # Precious Metals & Hallmarking
    "Gold Hallmarking": ("Precious Metals & Hallmarking", "Jewellery & Artefacts"),
    "Silver Hallmarking": ("Precious Metals & Hallmarking", "Jewellery & Artefacts"),
    
    # Food & Dairy
    "Infant Milk Food": ("Food & Agriculture", "Dairy Products"),
    "Milk Powder": ("Food & Agriculture", "Dairy Products"),
    "Condensed Milk": ("Food & Agriculture", "Dairy Products"),
    
    # Footwear & PPE
    "Safety Footwear": ("Leather, Footwear & PPE", "Personal Protective Equipment"),
    "Protective Footwear": ("Leather, Footwear & PPE", "Personal Protective Equipment"),
    "Rubber Hawai Chappal": ("Leather, Footwear & PPE", "Footwear"),
    "Canvas Footwear": ("Leather, Footwear & PPE", "Footwear"),
    
    # Fire Safety & Protection
    "Portable Fire Extinguishers": ("Fire Safety & Protection", "Extinguishers"),
    "Fire Hose Delivery Couplings": ("Fire Safety & Protection", "Fire Fighting Fittings"),
    
    # Medical & Healthcare
    "Disposable Hypodermic Syringes": ("Medical & Healthcare", "Medical Devices"),
    "Surgical Rubber Gloves": ("Medical & Healthcare", "Medical Gloves"),
    "Clinical Electronic Thermometers": ("Medical & Healthcare", "Diagnostic Instruments"),
    "Medical Electrical Equipment": ("Medical & Healthcare", "Medical Electrical Systems"),
    "Surgical Face Masks": ("Medical & Healthcare", "Personal Protective Equipment"),
    "Protective Rubber Gloves for Electrical Purposes": ("Electrical & Electronics", "Lineman Protective Equipment"),
    "Sanitary Napkins": ("Medical & Healthcare", "Hygiene Products"),
    
    # Packaging & Containers
    "Aluminium Foil for Food Packaging": ("Packaging & Containers", "Metallic Foil"),
    "Tinplate for Food Packaging": ("Packaging & Containers", "Metal Packaging"),
    "Corrugated Fibreboard Boxes": ("Packaging & Containers", "Fibreboard Packaging"),
    "HDPE and PP Woven Sacks": ("Packaging & Containers", "Woven Sacks"),
    "Jute Bags for Packing Foodgrains": ("Packaging & Containers", "Natural Fibre Sacks"),
    
    # Structural Engineering & Building Codes
    "Earthquake Resistant Design": ("Structural Engineering & Codes", "Seismic Design"),
    "Ductile Detailing of RC Structures": ("Structural Engineering & Codes", "Concrete Detailing"),
    "Structural Design Dead and Imposed Loads": ("Structural Engineering & Codes", "Design Loads"),
    
    # Chemicals & Safety
    "Safety Matches": ("Chemicals & Consumer Safety", "Match Boxes"),
}


def parse_rule_value(rule_val: str) -> Tuple[str, int | None]:
    """Parse 'IS 14543:2016' into ('IS 14543', 2016)."""
    m = re.match(r"^(.*?)(?::(\d{4}))?$", rule_val.strip())
    if m:
        base_code = m.group(1).strip()
        year = int(m.group(2)) if m.group(2) else None
        return base_code, year
    return rule_val.strip(), None


def populate_sqlite(rules_data: Dict[str, List[Dict[str, Any]]]):
    """Seed or enrich SQLite database with standards and certification rules."""
    print("[*] Updating SQLite database (bis_standards.db) with curated rules dataset...")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    added_count = 0
    updated_count = 0

    try:
        for product_name, entries in rules_data.items():
            cat_tuple = CATEGORY_MAP.get(product_name, ("General Engineering & Consumer Goods", None))
            category, subcategory = cat_tuple[0], cat_tuple[1]

            for entry in entries:
                rule_val = entry.get("Rule_value", "")
                state_name = entry.get("state_name", "Product Standard")
                context = entry.get("Context", "")

                base_code, year = parse_rule_value(rule_val)
                
                is_qco_mandatory = state_name in [
                    "Mandatory Certification",
                    "Compulsory Registration Scheme",
                    "Mandatory Hallmarking"
                ]
                is_crs = state_name == "Compulsory Registration Scheme"
                
                # Check if standard exists by base_code or full rule_val
                std = db.query(Standard).filter(
                    (Standard.is_code == base_code) | (Standard.is_code == rule_val)
                ).first()

                if not std:
                    # Check prefix / variation e.g. "IS 1489 (Part 1)"
                    std = db.query(Standard).filter(Standard.is_code.like(f"{base_code}%")).first()

                if not std:
                    std = Standard(
                        is_code=base_code,
                        title=product_name,
                        category=category,
                        subcategory=subcategory,
                        scope=context,
                        revision_year=year,
                        status="Active",
                    )
                    db.add(std)
                    db.flush()
                    added_count += 1
                    print(f"  [+] Added: {base_code} ({product_name})")
                else:
                    # Enrich existing standard with user context & revision year
                    updated_count += 1
                    if year and not std.revision_year:
                        std.revision_year = year
                    if category:
                        std.category = category
                    if subcategory and not std.subcategory:
                        std.subcategory = subcategory
                    if context:
                        # Append or augment scope
                        if std.scope and context not in std.scope:
                            std.scope = f"{std.scope} | Specifications: {context}"
                        else:
                            std.scope = context

                # Manage QCOAlert
                qco_order_title = {
                    "Mandatory Certification": "Mandatory Quality Control Order (QCO) - Ministry of Commerce & Industry / BIS",
                    "Compulsory Registration Scheme": "Compulsory Registration Scheme (CRS) - MeitY / BIS Order",
                    "Mandatory Hallmarking": "Mandatory Hallmarking Order - Ministry of Consumer Affairs / BIS",
                    "Voluntary Hallmarking": "Voluntary Hallmarking Scheme - BIS",
                    "Voluntary Certification": "Voluntary Product Certification Scheme - BIS",
                    "Product Standard": "Product Specification Standard - BIS",
                    "General Standard": "General Code of Practice - BIS",
                    "National Building Code Standard": "National Building Code of India (NBC) / BIS Structural Standard",
                    "Structural Safety Standard": "BIS Structural Safety Standard",
                    "Design Code": "BIS Civil & Structural Design Code",
                }.get(state_name, f"{state_name} - BIS")

                if not std.qco_alert:
                    qco = QCOAlert(
                        standard_id=std.id,
                        qco_notification=qco_order_title,
                        is_mandatory=is_qco_mandatory,
                        crs_applicable=is_crs,
                        penalty_non_compliance="Mandatory statutory compliance under Section 16 & Section 29 of the BIS Act, 2016."
                        if is_qco_mandatory else "Adherence as per tender / project engineering contract.",
                    )
                    db.add(qco)
                else:
                    if is_qco_mandatory:
                        std.qco_alert.is_mandatory = True
                    if is_crs:
                        std.qco_alert.crs_applicable = True
                    std.qco_alert.qco_notification = qco_order_title

                # Manage SimplifiedProcedure754
                if not std.simplified_procedure:
                    sp = SimplifiedProcedure754(
                        standard_id=std.id,
                        product_name=product_name,
                        option2_eligible=True,
                        fast_track_days=30,
                        notes="Eligible for Option 2 Simplified Procedure (Grant of license within 30 days).",
                    )
                    db.add(sp)

        db.commit()
        print(f"[+] SQLite sync complete: {added_count} added, {updated_count} updated. Total in DB: {db.query(Standard).count()}")
    finally:
        db.close()


def populate_qdrant(rules_data: Dict[str, List[Dict[str, Any]]]):
    """Upsert vector embeddings into Qdrant collection."""
    print("[*] Generating Qdrant embeddings for curated standards...")
    try:
        from qdrant_client import QdrantClient
        from qdrant_client.http import models as qdrant_models
        from sentence_transformers import SentenceTransformer
    except ImportError as err:
        print(f"[-] Vector packages not yet loaded: {err}. Skipping Qdrant vector index update.")
        return

    qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
    qdrant_api_key = os.getenv("QDRANT_API_KEY", None)
    try:
        client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key, prefer_grpc=False, timeout=5.0)
        client.get_collections()
        print(f"[+] Connected to Qdrant at {qdrant_url}")
    except Exception:
        storage_path = backend_dir / "qdrant_storage"
        print(f"[!] Using embedded Qdrant at {storage_path}")
        client = QdrantClient(path=str(storage_path))

    model_name = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    model = SentenceTransformer(model_name)

    points = []
    base_id = 95000

    for idx, (product_name, entries) in enumerate(rules_data.items()):
        cat_tuple = CATEGORY_MAP.get(product_name, ("General Engineering & Consumer Goods", None))
        category = cat_tuple[0]

        for sub_idx, entry in enumerate(entries):
            rule_val = entry.get("Rule_value", "")
            state_name = entry.get("state_name", "Product Standard")
            context = entry.get("Context", "")
            base_code, year = parse_rule_value(rule_val)

            is_qco_mandatory = state_name in [
                "Mandatory Certification",
                "Compulsory Registration Scheme",
                "Mandatory Hallmarking"
            ]
            is_crs = state_name == "Compulsory Registration Scheme"

            text = f"{base_code} ({rule_val}): {product_name}. Category: {category}. State: {state_name}. Context: {context}"
            vec = model.encode(text, normalize_embeddings=True)

            point_id = base_id + (idx * 10) + sub_idx
            points.append(
                qdrant_models.PointStruct(
                    id=point_id,
                    vector=vec.tolist(),
                    payload={
                        "is_code": base_code,
                        "full_is_code": rule_val,
                        "title": product_name,
                        "scope": context,
                        "category": category,
                        "state_name": state_name,
                        "qco_mandatory": is_qco_mandatory,
                        "crs_applicable": is_crs,
                        "simplified_procedure": True,
                        "revision_year": year,
                        "normative_refs": [],
                        "doc_type": "standard",
                    },
                )
            )

    client.upsert(
        collection_name="bis_standards",
        points=points
    )
    print(f"[+] Upserted {len(points)} curated points into Qdrant collection 'bis_standards'!")


def main():
    if not DATA_FILE.exists():
        print(f"[-] Data file {DATA_FILE} not found!")
        sys.exit(1)

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        rules_data = json.load(f)

    populate_sqlite(rules_data)
    populate_qdrant(rules_data)
    print("[SUCCESS] All curated rules and standards successfully ingested!")


if __name__ == "__main__":
    main()
