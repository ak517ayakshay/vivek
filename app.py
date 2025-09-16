#!/usr/bin/env python3
"""
Wholesale Shop Software - Purchase Payment Reminder System
A complete solution with Flask backend and modern UI
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
import sqlite3
from datetime import datetime, timedelta, date
import os
from typing import Optional, List, Tuple, Dict

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'
DB_FILE = "wholesale_shop.db"

# ---------- Database Setup ----------
def get_conn():
    conn = sqlite3.connect(DB_FILE)
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
    
    # Check Issuance table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS check_issuance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        vendor_id INTEGER NOT NULL,
        vendor_name TEXT NOT NULL,
        check_number TEXT NOT NULL,
        check_date TEXT NOT NULL,
        remarks TEXT,
        status TEXT NOT NULL DEFAULT 'Pending',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(vendor_id) REFERENCES vendors(id)
    )
    """)
    
    conn.commit()
    conn.close()

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
    # Get payment type filter from query parameter
    payment_type_filter = request.args.get('payment_type', 'all')
    
    conn = get_conn()
    cur = conn.cursor()
    
    # Build query with optional payment type filter
    query = """
    SELECT p.*, v.name as vendor_name, v.phone as vendor_phone
    FROM purchases p 
    JOIN vendors v ON v.id = p.vendor_id 
    """
    
    params = []
    if payment_type_filter != 'all':
        query += " WHERE p.payment_type = ?"
        params.append(payment_type_filter)
    
    query += " ORDER BY p.due_date"
    
    cur.execute(query, params)
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
                         payment_type_filter=payment_type_filter,
                         overdue_total=overdue_total,
                         due_today_total=due_today_total,
                         due_soon_total=due_soon_total,
                         paid_total=paid_total,
                         vendor_summary=vendor_summary)

@app.route('/vendors')
def vendors():
    """Vendor management page"""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM vendors ORDER BY name")
    vendors = cur.fetchall()
    conn.close()
    return render_template('vendors.html', vendors=vendors)

@app.route('/add_vendor', methods=['POST'])
def add_vendor():
    """Add new vendor"""
    name = request.form['name']
    phone = request.form.get('phone', '')
    email = request.form.get('email', '')
    address = request.form.get('address', '')
    default_credit_days = int(request.form.get('default_credit_days', 30))
    
    conn = get_conn()
    cur = conn.cursor()
    
    try:
        cur.execute("""
        INSERT INTO vendors (name, phone, email, address, default_credit_days) 
        VALUES (?, ?, ?, ?, ?)
        """, (name, phone, email, address, default_credit_days))
        conn.commit()
        flash('Vendor added successfully!', 'success')
    except sqlite3.IntegrityError:
        flash('Vendor with this name already exists!', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('vendors'))

@app.route('/purchases')
def purchases():
    """Purchase management page"""
    conn = get_conn()
    cur = conn.cursor()
    
    # Get all purchases with vendor info
    cur.execute("""
    SELECT p.*, v.name as vendor_name, v.phone as vendor_phone
    FROM purchases p 
    JOIN vendors v ON v.id = p.vendor_id 
    ORDER BY p.created_at DESC
    """)
    purchases = cur.fetchall()
    
    # Calculate days remaining for each purchase
    today = date.today()
    purchases_with_days = []
    for purchase in purchases:
        purchase_dict = dict(purchase)
        due_date = parse_date(purchase['due_date'])
        days_remaining = (due_date - today).days
        purchase_dict['days_remaining'] = days_remaining
        purchase_dict['pending_amount'] = purchase['bill_amount'] - (purchase['advance_paid'] or 0)
        purchases_with_days.append(purchase_dict)
    
    # Get all vendors for dropdown
    cur.execute("SELECT id, name FROM vendors ORDER BY name")
    vendors = cur.fetchall()
    
    conn.close()
    return render_template('purchases.html', purchases=purchases_with_days, vendors=vendors)

@app.route('/add_purchase', methods=['POST'])
def add_purchase():
    """Add new purchase"""
    vendor_id = int(request.form['vendor_id'])
    bill_no = request.form['bill_no']
    bill_date = request.form['bill_date']
    due_date = request.form['due_date']  # Manual due date input
    bill_amount = float(request.form['bill_amount'])
    advance_paid = float(request.form.get('advance_paid', 0))
    payment_type = request.form.get('payment_type', 'Credit')
    
    # Calculate status based on manual due date
    due_date, status, days_remaining = calculate_due_date_and_status(
        bill_date, due_date, bill_amount, advance_paid
    )
    
    # Calculate credit days for display
    bill_date_obj = parse_date(bill_date)
    due_date_obj = parse_date(due_date)
    credit_days = (due_date_obj - bill_date_obj).days
    
    conn = get_conn()
    cur = conn.cursor()
    
    try:
        cur.execute("""
        INSERT INTO purchases 
        (vendor_id, bill_no, bill_date, credit_days, bill_amount, advance_paid, due_date, status, payment_type)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (vendor_id, bill_no, bill_date, credit_days, bill_amount, advance_paid, due_date, status, payment_type))
        conn.commit()
        flash('Purchase added successfully!', 'success')
    except Exception as e:
        flash(f'Error adding purchase: {str(e)}', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('purchases'))

@app.route('/add_payment', methods=['POST'])
def add_payment():
    """Add payment to purchase"""
    purchase_id = int(request.form['purchase_id'])
    paid_amount = float(request.form['paid_amount'])
    paid_date = request.form.get('paid_date', date.today().isoformat())
    payment_method = request.form.get('payment_method', 'Cash')
    note = request.form.get('note', '')
    
    conn = get_conn()
    cur = conn.cursor()
    
    try:
        # Add payment record
        cur.execute("""
        INSERT INTO payments (purchase_id, paid_amount, paid_date, payment_method, note)
        VALUES (?, ?, ?, ?, ?)
        """, (purchase_id, paid_amount, paid_date, payment_method, note))
        
        # Update purchase with new advance_paid amount
        cur.execute("SELECT bill_amount, advance_paid, bill_date, due_date FROM purchases WHERE id = ?", (purchase_id,))
        purchase = cur.fetchone()
        
        if purchase:
            new_advance_paid = (purchase['advance_paid'] or 0) + paid_amount
            due_date, status, days_remaining = calculate_due_date_and_status(
                purchase['bill_date'], purchase['due_date'], purchase['bill_amount'], new_advance_paid
            )
            
            cur.execute("""
            UPDATE purchases 
            SET advance_paid = ?, due_date = ?, status = ?
            WHERE id = ?
            """, (new_advance_paid, due_date, status, purchase_id))
        
        conn.commit()
        flash('Payment recorded successfully!', 'success')
    except Exception as e:
        flash(f'Error recording payment: {str(e)}', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('purchases'))

@app.route('/api/vendors')
def api_vendors():
    """API endpoint to get vendors for AJAX"""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, name, default_credit_days FROM vendors ORDER BY name")
    vendors = [dict(row) for row in cur.fetchall()]
    conn.close()
    return jsonify(vendors)

@app.route('/api/purchase/<int:purchase_id>')
def api_purchase(purchase_id):
    """API endpoint to get purchase details"""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
    SELECT p.*, v.name as vendor_name 
    FROM purchases p 
    JOIN vendors v ON v.id = p.vendor_id 
    WHERE p.id = ?
    """, (purchase_id,))
    purchase = cur.fetchone()
    conn.close()
    
    if purchase:
        return jsonify(dict(purchase))
    return jsonify({'error': 'Purchase not found'}), 404

@app.route('/api/payments/<int:purchase_id>')
def api_payments(purchase_id):
    """API endpoint to get payments for a purchase"""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
    SELECT * FROM payments 
    WHERE purchase_id = ? 
    ORDER BY paid_date DESC
    """, (purchase_id,))
    payments = cur.fetchall()
    conn.close()
    
    return jsonify([dict(payment) for payment in payments])

@app.route('/api/payment/<int:payment_id>')
def api_payment(payment_id):
    """API endpoint to get individual payment details"""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM payments WHERE id = ?", (payment_id,))
    payment = cur.fetchone()
    conn.close()
    
    if payment:
        return jsonify(dict(payment))
    return jsonify({'error': 'Payment not found'}), 404

@app.route('/edit_payment/<int:payment_id>', methods=['POST'])
def edit_payment(payment_id):
    """Edit a payment"""
    paid_amount = float(request.form['paid_amount'])
    paid_date = request.form['paid_date']
    payment_method = request.form['payment_method']
    note = request.form.get('note', '')
    
    conn = get_conn()
    cur = conn.cursor()
    
    try:
        # Get the old payment amount
        cur.execute("SELECT paid_amount, purchase_id FROM payments WHERE id = ?", (payment_id,))
        old_payment = cur.fetchone()
        
        if not old_payment:
            flash('Payment not found!', 'error')
            return redirect(url_for('purchases'))
        
        old_amount = old_payment['paid_amount']
        purchase_id = old_payment['purchase_id']
        amount_difference = paid_amount - old_amount
        
        # Update payment
        cur.execute("""
        UPDATE payments 
        SET paid_amount = ?, paid_date = ?, payment_method = ?, note = ?
        WHERE id = ?
        """, (paid_amount, paid_date, payment_method, note, payment_id))
        
        # Update purchase advance_paid
        cur.execute("SELECT bill_amount, advance_paid, bill_date, due_date FROM purchases WHERE id = ?", (purchase_id,))
        purchase = cur.fetchone()
        
        if purchase:
            new_advance_paid = (purchase['advance_paid'] or 0) + amount_difference
            due_date, status, days_remaining = calculate_due_date_and_status(
                purchase['bill_date'], purchase['due_date'], purchase['bill_amount'], new_advance_paid
            )
            
            cur.execute("""
            UPDATE purchases 
            SET advance_paid = ?, due_date = ?, status = ?
            WHERE id = ?
            """, (new_advance_paid, due_date, status, purchase_id))
        
        conn.commit()
        flash('Payment updated successfully!', 'success')
    except Exception as e:
        flash(f'Error updating payment: {str(e)}', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('purchases'))

@app.route('/delete_payment/<int:payment_id>', methods=['POST'])
def delete_payment(payment_id):
    """Delete a payment"""
    conn = get_conn()
    cur = conn.cursor()
    
    try:
        # Get payment details
        cur.execute("SELECT paid_amount, purchase_id FROM payments WHERE id = ?", (payment_id,))
        payment = cur.fetchone()
        
        if not payment:
            flash('Payment not found!', 'error')
            return redirect(url_for('purchases'))
        
        paid_amount = payment['paid_amount']
        purchase_id = payment['purchase_id']
        
        # Delete payment
        cur.execute("DELETE FROM payments WHERE id = ?", (payment_id,))
        
        # Update purchase advance_paid
        cur.execute("SELECT bill_amount, advance_paid, bill_date, due_date FROM purchases WHERE id = ?", (purchase_id,))
        purchase = cur.fetchone()
        
        if purchase:
            new_advance_paid = (purchase['advance_paid'] or 0) - paid_amount
            due_date, status, days_remaining = calculate_due_date_and_status(
                purchase['bill_date'], purchase['due_date'], purchase['bill_amount'], new_advance_paid
            )
            
            cur.execute("""
            UPDATE purchases 
            SET advance_paid = ?, due_date = ?, status = ?
            WHERE id = ?
            """, (new_advance_paid, due_date, status, purchase_id))
        
        conn.commit()
        flash('Payment deleted successfully!', 'success')
    except Exception as e:
        flash(f'Error deleting payment: {str(e)}', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('purchases'))

# ---------- Check Issuance Routes ----------
@app.route('/check_issuance')
def check_issuance():
    """Check issuance management page"""
    conn = get_conn()
    cur = conn.cursor()
    
    # Get all check issuances with vendor details
    cur.execute("""
    SELECT ci.*, v.name as vendor_name, v.phone 
    FROM check_issuance ci 
    JOIN vendors v ON v.id = ci.vendor_id 
    ORDER BY ci.created_at DESC
    """)
    checks = cur.fetchall()
    
    # Get all vendors for dropdown
    cur.execute("SELECT id, name FROM vendors ORDER BY name")
    vendors = cur.fetchall()
    
    conn.close()
    
    return render_template('check_issuance.html', checks=checks, vendors=vendors)

@app.route('/add_check_issuance', methods=['POST'])
def add_check_issuance():
    """Add new check issuance"""
    vendor_id = int(request.form['vendor_id'])
    vendor_name = request.form['vendor_name']
    check_number = request.form['check_number']
    check_date = request.form['check_date']
    remarks = request.form.get('remarks', '')
    status = request.form.get('status', 'Pending')
    
    conn = get_conn()
    cur = conn.cursor()
    
    try:
        cur.execute("""
        INSERT INTO check_issuance (vendor_id, vendor_name, check_number, check_date, remarks, status)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (vendor_id, vendor_name, check_number, check_date, remarks, status))
        
        conn.commit()
        flash('Check issuance added successfully!', 'success')
    except Exception as e:
        flash(f'Error adding check issuance: {str(e)}', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('check_issuance'))

@app.route('/update_check_status/<int:check_id>', methods=['POST'])
def update_check_status(check_id):
    """Update check status"""
    new_status = request.form['status']
    remarks = request.form.get('remarks', '')
    
    conn = get_conn()
    cur = conn.cursor()
    
    try:
        cur.execute("""
        UPDATE check_issuance 
        SET status = ?, remarks = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """, (new_status, remarks, check_id))
        
        conn.commit()
        flash('Check status updated successfully!', 'success')
    except Exception as e:
        flash(f'Error updating check status: {str(e)}', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('check_issuance'))

@app.route('/delete_check/<int:check_id>', methods=['POST'])
def delete_check(check_id):
    """Delete check issuance"""
    conn = get_conn()
    cur = conn.cursor()
    
    try:
        cur.execute("DELETE FROM check_issuance WHERE id = ?", (check_id,))
        conn.commit()
        flash('Check deleted successfully!', 'success')
    except Exception as e:
        flash(f'Error deleting check: {str(e)}', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('check_issuance'))

# ---------- Main ----------
if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5001)

