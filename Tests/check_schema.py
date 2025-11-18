#!/usr/bin/env python3
import psycopg

conn = psycopg.connect(
    dbname='sact',
    user='sergiomendes',
    host='localhost',
    port=5432,
    options='-c search_path=core,cte,ibge,public'
)

cur = conn.cursor()
cur.execute("""
    SELECT column_name, data_type, is_nullable, column_default
    FROM information_schema.columns 
    WHERE table_schema='cte' AND table_name='documento' 
    ORDER BY ordinal_position
""")

print("ESTRUTURA DA TABELA cte.documento:")
print("="*80)
for row in cur.fetchall():
    nullable = "NULL" if row[2] == 'YES' else "NOT NULL"
    default = f" DEFAULT {row[3]}" if row[3] else ""
    print(f"{row[0]:30} {row[1]:20} {nullable:10} {default}")

conn.close()
