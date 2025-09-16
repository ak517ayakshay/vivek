#!/usr/bin/env python3
"""
Vercel serverless function for Ayush Herbal Software
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
import sqlite3
from datetime import datetime, timedelta, date
import os
from typing import Optional, List, Tuple, Dict

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-here')

# For Vercel, we'll use a different database approach
# You can use Vercel Postgres, PlanetScale, or Supabase
DB_URL = os.environ.get('DATABASE_URL', 'sqlite:///wholesale_shop.db')

def get_conn():
    # For Vercel, you'll need to use a proper database
    # This is a placeholder - replace with your actual database connection
    conn = sqlite3.connect(':memory:')  # This won't work in production
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    
    # Vendors table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS vendors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        phone TEXT,
        email TEXT,
        address TEXT,
        default_credit_days INTEGER DEFAULT 30,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Purchases table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS purchases (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        vendor_id INTEGER NOT NULL,
        bill_no TEXT NOT NULL,
        bill_date TEXT NOT NULL,
        credit_days INTEGER NOT NULL,
        bill_amount REAL NOT NULL,
        advance_paid REAL DEFAULT 0,
        due_date TEXT NOT NULL,
        status TEXT NOT NULL,
        payment_type TEXT DEFAULT 'Credit',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(vendor_id) REFERENCES vendors(id)
    )
    """)
    
    # Payments table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        purchase_id INTEGER NOT NULL,
        paid_amount REAL NOT NULL,
        paid_date TEXT NOT NULL,
        payment_method TEXT DEFAULT 'Cash',
        note TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(purchase_id) REFERENCES purchases(id)
    )
    """)
    
    conn.commit()
    conn.close()

# Import all your existing functions here
# (Copy all the functions from your main app.py)

# ---------- Business Logic ----------
def parse_date(s: str) -> date:
    return datetime.strptime(s, "%Y-%m-%d").date()

def iso(d: date) -> str:
    return d.isoformat()

def calculate_due_date_and_status(bill_date_str: str, due_date_str: str, bill_amount: float, advance_paid: float) -> Tuple[str, str, int]:
    """Calculate due date, status, and days remaining"""
    due_date = parse_date(due_date_str)
    pending_amount = bill_amount - (advance_paid or 0)
    today = date.today()
    days_remaining = (due_date - today).days
    
    if pending_amount <= 0:
        status = "Paid"
    elif days_remaining < 0:
        status = "Overdue"
    elif days_remaining == 0:
        status = "Due Today"
    else:
        status = "Pending"
    
    return iso(due_date), status, days_remaining

def get_status_color(status: str, days_remaining: int) -> str:
    """Get Bootstrap color class for status"""
    if status == "Paid":
        return "success"
    elif status == "Overdue":
        return "danger"
    elif status == "Due Today":
        return "warning"
    elif days_remaining <= 7:
        return "warning"
    else:
        return "info"

# ---------- Routes ----------
@app.route('/')
def dashboard():
    """Main dashboard with reminders"""
    # Get reminder period from query parameter, default to 7 days
    reminder_days = int(request.args.get('days', 7))
    
    conn = get_conn()
    cur = conn.cursor()
    
    # Get all purchases with vendor info
    cur.execute("""
    SELECT p.*, v.name as vendor_name, v.phone as vendor_phone
    FROM purchases p 
    JOIN vendors v ON v.id = p.vendor_id 
    ORDER BY p.due_date
    """)
    purchases = cur.fetchall()
    
    # Categorize purchases
    overdue = []
    due_today = []
    due_soon = []
    paid = []
    
    today = date.today()
    
    for purchase in purchases:
        due_date = parse_date(purchase['due_date'])
        days_remaining = (due_date - today).days
        pending_amount = purchase['bill_amount'] - (purchase['advance_paid'] or 0)
        
        purchase_dict = dict(purchase)
        purchase_dict['pending_amount'] = pending_amount
        purchase_dict['days_remaining'] = days_remaining
        purchase_dict['status_color'] = get_status_color(purchase_dict['status'], days_remaining)
        
        if pending_amount <= 0:
            paid.append(purchase_dict)
        elif days_remaining < 0:
            overdue.append(purchase_dict)
        elif days_remaining == 0:
            due_today.append(purchase_dict)
        elif days_remaining <= reminder_days:
            due_soon.append(purchase_dict)
    
    # Calculate totals
    overdue_total = sum(p['pending_amount'] for p in overdue)
    due_today_total = sum(p['pending_amount'] for p in due_today)
    due_soon_total = sum(p['pending_amount'] for p in due_soon)
    paid_total = sum(p['bill_amount'] for p in paid)
    
    # Vendor-wise summary
    vendor_summary = {}
    for purchase in purchases:
        vendor_name = purchase['vendor_name']
        pending_amount = purchase['bill_amount'] - (purchase['advance_paid'] or 0)
        if pending_amount > 0:
            if vendor_name not in vendor_summary:
                vendor_summary[vendor_name] = {'count': 0, 'total': 0, 'phone': purchase['vendor_phone']}
            vendor_summary[vendor_name]['count'] += 1
            vendor_summary[vendor_name]['total'] += pending_amount
    
    conn.close()
    
    return render_template('dashboard.html', 
                         overdue=overdue, 
                         due_today=due_today, 
                         due_soon=due_soon, 
                         paid=paid,
                         reminder_days=reminder_days,
                         overdue_total=overdue_total,
                         due_today_total=due_today_total,
                         due_soon_total=due_soon_total,
                         paid_total=paid_total,
                         vendor_summary=vendor_summary)

# Add all other routes here...

# This is the entry point for Vercel
def handler(request):
    return app(request.environ, lambda *args: None)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
