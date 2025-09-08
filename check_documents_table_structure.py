#!/usr/bin/env python3
import sys
import os
sys.path.append('apps/api')

from database import SessionLocal
from sqlalchemy import text

db = SessionLocal()
result = db.execute(text("SELECT column_name, data_type, is_nullable FROM information_schema.columns WHERE table_name = 'documents' ORDER BY ordinal_position"))
print('Documents table structure:')
for row in result:
    print(f'  {row[0]}: {row[1]} (nullable: {row[2]})')
db.close()