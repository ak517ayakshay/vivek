# Ayush Herbal Software - Purchase Payment Reminder System

A comprehensive herbal shop management system with automated payment reminders, built with Flask and SQLite.

## Features

### 🌿 **Vendor Management**
- Add, view, and manage vendors
- Store contact information (phone, email, address)
- Set default credit days per vendor
- Vendor-specific payment terms

### 💰 **Purchase Management**
- Create purchase entries with auto-calculation
- Support for different payment types (Credit, Advance, Cash)
- Automatic due date calculation based on credit days
- Real-time pending amount calculation
- Payment status tracking (Paid, Due, Overdue)

### 🔔 **Payment Reminders Dashboard**
- **Color-coded status indicators:**
  - 🔴 **Red**: Overdue bills
  - 🟡 **Yellow**: Due today & due soon (7 days)
  - 🟢 **Green**: Paid bills
- Real-time status updates
- Vendor-wise pending bills view
- Export functionality for reminders

### 💳 **Payment Recording**
- Record partial or full payments
- Multiple payment methods (Cash, Cheque, Bank Transfer, UPI)
- Payment history tracking
- Automatic status updates

## Installation & Setup

### Prerequisites
- Python 3.7 or higher
- pip (Python package installer)

### Quick Start

1. **Clone or download the project files**

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application:**
   ```bash
   python app.py
   ```

4. **Open your browser and go to:**
   ```
   http://localhost:5000
   ```

## Usage Guide

### 1. **Add Vendors**
- Go to "Vendors" section
- Click "Add Vendor" button
- Fill in vendor details including default credit days
- Save vendor information

### 2. **Create Purchase Entries**
- Go to "Purchases" section
- Click "Add Purchase" button
- Select vendor (auto-fills default credit days)
- Choose payment type (Credit/Advance/Cash)
- Enter bill details
- System auto-calculates due date and pending amount
- Save purchase entry

### 3. **View Payment Reminders**
- Dashboard shows all reminders categorized by status
- **Overdue**: Bills past due date (red)
- **Due Today**: Bills due today (yellow)
- **Due Soon**: Bills due within 7 days (yellow)
- **Paid**: Completed payments (green)

### 4. **Record Payments**
- Click "Payment" button on any purchase
- Enter payment amount and details
- System automatically updates pending amount and status
- Payment history is maintained

## Database Schema

The system uses SQLite with three main tables:

- **vendors**: Vendor information and default credit days
- **purchases**: Purchase entries with calculated due dates and status
- **payments**: Payment records linked to purchases

## Key Features Explained

### Auto-Calculation Logic
- **Due Date**: Bill Date + Credit Days
- **Pending Amount**: Bill Amount - Advance Paid
- **Status**: Based on pending amount and due date
- **Days Remaining**: Due Date - Today's Date

### Status Categories
- **Paid**: Pending amount ≤ 0
- **Overdue**: Pending amount > 0 AND days remaining < 0
- **Due Today**: Pending amount > 0 AND days remaining = 0
- **Due Soon**: Pending amount > 0 AND 0 < days remaining ≤ 7
- **Pending**: Pending amount > 0 AND days remaining > 7

## Customization

### Change Reminder Window
Modify the reminder window (default 7 days) in the dashboard:
```python
# In app.py, line ~150
remind_window_days = 7  # Change this value
```

### Add New Payment Methods
Edit the payment method options in `templates/purchases.html`:
```html
<option value="New Method">New Method</option>
```

## API Endpoints

- `GET /` - Dashboard
- `GET /vendors` - Vendor management
- `POST /add_vendor` - Add new vendor
- `GET /purchases` - Purchase management
- `POST /add_purchase` - Add new purchase
- `POST /add_payment` - Record payment
- `GET /api/vendors` - Get vendors (JSON)
- `GET /api/purchase/<id>` - Get purchase details (JSON)

## Troubleshooting

### Common Issues

1. **Port already in use**: Change port in `app.py`:
   ```python
   app.run(debug=True, host='0.0.0.0', port=5001)  # Use different port
   ```

2. **Database errors**: Delete `wholesale_shop.db` file and restart the application

3. **Missing dependencies**: Run `pip install -r requirements.txt`

## Future Enhancements

- Email/SMS reminder notifications
- PDF report generation
- Multi-currency support
- Advanced reporting and analytics
- Mobile app integration
- Cloud database support

## Support

For issues or feature requests, please check the code comments or create an issue in the project repository.

---

**Built with ❤️ for Ayush Herbal shop owners**

