#!/usr/bin/env python3
"""Check foreign key constraints in the database"""

import psycopg2

def check_foreign_keys():
    try:
        conn = psycopg2.connect('postgresql://studioops:studioops123@localhost:5432/studioops')
        cur = conn.cursor()
        
        # Check foreign key constraints
        query = """
        SELECT 
            tc.table_name, 
            kcu.column_name, 
            ccu.table_name AS foreign_table_name,
            ccu.column_name AS foreign_column_name,
            tc.constraint_name,
            rc.delete_rule
        FROM 
            information_schema.table_constraints AS tc 
            JOIN information_schema.key_column_usage AS kcu
                ON tc.constraint_name = kcu.constraint_name
                AND tc.table_schema = kcu.table_schema
            JOIN information_schema.constraint_column_usage AS ccu
                ON ccu.constraint_name = tc.constraint_name
                AND ccu.table_schema = tc.table_schema
            JOIN information_schema.referential_constraints AS rc
                ON tc.constraint_name = rc.constraint_name
        WHERE tc.constraint_type = 'FOREIGN KEY' 
            AND tc.table_schema = 'public'
        ORDER BY tc.table_name, kcu.column_name;
        """
        
        cur.execute(query)
        
        print("Current Foreign Key Constraints:")
        print("=" * 80)
        for row in cur.fetchall():
            table, column, foreign_table, foreign_column, constraint_name, delete_rule = row
            print(f"{table}.{column} -> {foreign_table}.{foreign_column}")
            print(f"  Constraint: {constraint_name}")
            print(f"  DELETE Rule: {delete_rule}")
            print()
        
        # Check specific project-related constraints
        print("\nProject-related constraints:")
        print("=" * 40)
        
        project_related = [row for row in cur.fetchall() if 'project' in row[0] or 'project' in row[1]]
        for row in project_related:
            print(f"{row[0]}.{row[1]} -> {row[2]}.{row[3]} [DELETE: {row[5]}]")
        
        conn.close()
        
    except Exception as e:
        print(f"Error checking foreign keys: {e}")

if __name__ == "__main__":
    check_foreign_keys()