import sqlite3

conn = sqlite3.connect('bis_standards.db')
cur = conn.cursor()

targets = [
    ("IS 4984", "High Density Polyethylene Pipes"),
    ("IS 12701", "Rotational Moulded Polyethylene Water Storage Tanks"),
    ("IS 15658", "Precast Concrete Blocks For Paving"),
    ("IS 4990", "Plywood For Concrete Shuttering Work"),
    ("IS 694", "Polyvinyl Chloride Insulated... Cables"),
    ("IS 1180 (Part 1)", "Distribution Transformers"),
    ("IS 3854", "Switches For Domestic And Similar Purposes"),
    ("IS 4151", "Protective Helmet For Two Wheeler Riders"),
    ("IS 2925", "Industrial Safety Helmets"),
    ("IS 13422", "Disposable Surgical Rubber Gloves"),
    ("IS 15683", "Portable Fire Extinguishers"),
    ("IS 14220", "Openwell Submersible Pumpsets"),
    ("IS 14887", "Woven Sacks For Packing Foodgrains"),
    ("IS 1970", "Knapsack Sprayer"),
    ("IS 374", "Electric Ceiling Type Fans"),
    ("IS 1391 (Part 1)", "Room Air Conditioners"),
    ("IS 14433", "Infant Milk Substitutes"),
    ("IS 1786", "High Strength Deformed Steel Bars"),
    ("IS 2062", "Hot Rolled Structural Steel"),
    ("IS 277", "Galvanized Steel Strips And Sheets"),
    ("IS 1038", "Steel Doors, Windows And Ventilators"),
    ("IS 13334 (Part 1)", "Skimmed Milk Powder"),
    ("IS 1166", "Condensed Milk"),
    ("IS 2785", "Cheese"),
    ("IS 16232", "Iron Fortified Iodized Salt"),
    ("IS 3390", "Sphygmomanometers, Mercurial"),
    ("IS 4605", "Crepe Bandage"),
    ("IS 1061", "Disinfectant Fluids, Phenolic Type"),
    ("IS 758", "Handloom Cotton Gauze"),
    ("IS 4250", "Domestic Electric Food-mixers"),
    ("IS 2082", "Stationary Storage Type Electric Water Heaters"),
    ("IS 2347", "Domestic Pressure Cookers"),
    ("IS 303", "Plywood For General Purposes"),
    ("IS 2546", "Galvanized Mild Steel Fire Bucket"),
    ("IS 636", "Fire Fighting Delivery Hose"),
    ("IS 14561", "Fire Resisting Filing Cabinets")
]

present = []
missing = []

for code, desc in targets:
    # Try exact match or base match
    base_code = code.split("(")[0].strip()
    cur.execute("SELECT is_code, title FROM standards WHERE is_code = ? OR is_code LIKE ?", (code, f"{base_code}%"))
    rows = cur.fetchall()
    if rows:
        present.append((code, desc, rows[0][0], rows[0][1]))
    else:
        missing.append((code, desc))

print(f"Total Targets: {len(targets)}")
print(f"Present in DB: {len(present)}")
print(f"Missing in DB: {len(missing)}")

print("\n--- MISSING STANDARDS ---")
for code, desc in missing:
    print(f"MISSING: {code} -> {desc}")

print("\n--- PRESENT STANDARDS ---")
for code, desc, matched_code, matched_title in present:
    print(f"EXISTS: {code} matched '{matched_code}' -> {matched_title[:50]}")

conn.close()
