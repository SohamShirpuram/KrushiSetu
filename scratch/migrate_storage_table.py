import sqlite3

conn = sqlite3.connect('data/krushisetu.db')
cur = conn.cursor()
cur.execute('PRAGMA table_info(major_warehouse_storage)')
cols = [r[1] for r in cur.fetchall()]
print('Existing cols:', cols)

new_cols = [
    ('farmer_id', 'VARCHAR(50)'),
    ('farmer_name', 'VARCHAR(100)'),
    ('crop_category', "VARCHAR(50) DEFAULT 'Grains'"),
    ('reserved_quantity_kg', 'FLOAT DEFAULT 0.0'),
    ('dispatched_quantity_kg', 'FLOAT DEFAULT 0.0'),
    ('notes', 'TEXT'),
]

for col_name, col_type in new_cols:
    if col_name not in cols:
        print(f'Adding {col_name}...')
        cur.execute(f'ALTER TABLE major_warehouse_storage ADD COLUMN {col_name} {col_type}')

# Populate farmer_id/farmer_name from major_warehouse_intakes if missing
cur.execute('''
    UPDATE major_warehouse_storage
    SET farmer_id = (SELECT farmer_id FROM major_warehouse_intakes WHERE major_warehouse_intakes.batch_id = major_warehouse_storage.batch_id),
        farmer_name = (SELECT farmer_name FROM major_warehouse_intakes WHERE major_warehouse_intakes.batch_id = major_warehouse_storage.batch_id)
    WHERE farmer_id IS NULL OR farmer_id = ''
''')

conn.commit()
conn.close()
print('Storage table migration complete!')

