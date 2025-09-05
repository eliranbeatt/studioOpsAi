#!/usr/bin/env python3
"""
Seed script for StudioOps AI database
"""
import os
import psycopg2
import psycopg2.extras as pg_extras
import csv
from pathlib import Path

def run_seeds():
    """Run all database seeds"""
    
    # Get database connection string from environment
    database_url = os.getenv('DATABASE_URL', 'postgresql://studioops:studioops@localhost:5432/studioops')
    
    conn = None
    try:
        # Connect to database
        conn = psycopg2.connect(database_url)
        conn.autocommit = True
        cursor = conn.cursor()
        
        print("Connected to database for seeding")
        
        # Seed vendors
        print("Seeding vendors...")
        vendors = [
            ('Hardware Store', 'Local hardware supplier', 'https://example.com', 4),
            ('Lumber Yard', 'Wood and building materials', 'https://lumber.example.com', 5),
            ('Electronics Shop', 'Electronic components', 'https://electronics.example.com', 4),
            ('Fabric Store', 'Textiles and fabrics', 'https://fabric.example.com', 3),
            ('Paint Store', 'Paints and coatings', 'https://paint.example.com', 4)
        ]
        
        for name, notes, url, rating in vendors:
            cursor.execute(
                "INSERT INTO vendors (name, notes, url, rating) VALUES (%s, %s, %s, %s) ON CONFLICT DO NOTHING",
                (name, notes, url, rating)
            )
        
        # Seed materials
        print("Seeding materials...")
        materials = [
            ('Plywood 4x8', '1/2 inch plywood sheet', 'sheet', 'construction', 5.0),
            ('2x4 Lumber', 'Standard 2x4 lumber', 'piece', 'construction', 3.0),
            ('Screws', '#8 wood screws', 'box', 'hardware', 1.0),
            ('Paint', 'Interior latex paint', 'gallon', 'finishing', 2.0),
            ('Fabric', 'Cotton fabric', 'yard', 'upholstery', 10.0),
            ('LED Bulb', '10W LED light bulb', 'piece', 'lighting', 0.0),
            ('Nails', '16d common nails', 'lb', 'hardware', 1.0),
            ('Drywall', '1/2 inch drywall', 'sheet', 'construction', 8.0)
        ]
        
        for name, spec, unit, category, waste in materials:
            cursor.execute(
                "INSERT INTO materials (name, spec, unit, category, typical_waste_pct) VALUES (%s, %s, %s, %s, %s) ON CONFLICT DO NOTHING",
                (name, spec, unit, category, waste)
            )
        
        # Seed vendor prices
        print("Seeding vendor prices...")
        cursor.execute("SELECT id FROM vendors WHERE name = 'Hardware Store'")
        hardware_vendor = cursor.fetchone()[0]
        
        cursor.execute("SELECT id FROM vendors WHERE name = 'Lumber Yard'")
        lumber_vendor = cursor.fetchone()[0]
        
        cursor.execute("SELECT id FROM materials WHERE name = 'Plywood 4x8'")
        plywood_material = cursor.fetchone()[0]
        
        cursor.execute("SELECT id FROM materials WHERE name = '2x4 Lumber'")
        lumber_material = cursor.fetchone()[0]
        
        cursor.execute("SELECT id FROM materials WHERE name = 'Screws'")
        screws_material = cursor.fetchone()[0]
        
        vendor_prices = [
            (hardware_vendor, plywood_material, 'PLY-001', 45.99, 0.9, False),
            (lumber_vendor, plywood_material, 'PLY-002', 42.50, 0.95, False),
            (lumber_vendor, lumber_material, 'LUM-001', 8.99, 0.9, False),
            (hardware_vendor, screws_material, 'SCR-001', 12.99, 0.85, False)
        ]
        
        for vendor_id, material_id, sku, price, confidence, is_quote in vendor_prices:
            cursor.execute(
                """INSERT INTO vendor_prices (vendor_id, material_id, sku, price_nis, confidence, is_quote, fetched_at) 
                VALUES (%s, %s, %s, %s, %s, %s, NOW()) ON CONFLICT DO NOTHING""",
                (vendor_id, material_id, sku, price, confidence, is_quote)
            )
        
        # Seed rate cards
        print("Seeding rate cards...")
        rate_cards = [
            ('Carpenter', 120.0, {'overtime_rate': 180.0}, 0.9),
            ('Electrician', 150.0, {'overtime_rate': 225.0}, 0.85),
            ('Painter', 100.0, {'overtime_rate': 150.0}, 0.8),
            ('Laborer', 80.0, {'overtime_rate': 120.0}, 1.0)
        ]
        
        for role, rate, overtime, efficiency in rate_cards:
            cursor.execute(
                "INSERT INTO rate_cards (role, hourly_rate_nis, overtime_rules_json, default_efficiency) VALUES (%s, %s, %s, %s) ON CONFLICT (role) DO UPDATE SET hourly_rate_nis = EXCLUDED.hourly_rate_nis",
                (role, rate, pg_extras.Json(overtime), efficiency)
            )
        
        print("Seeding completed successfully")
        
    except Exception as e:
        print(f"Error running seeds: {e}")
        raise
    finally:
        try:
            if conn:
                conn.close()
        except NameError:
            pass

if __name__ == "__main__":
    run_seeds()
