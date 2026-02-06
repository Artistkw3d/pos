#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
خادم API لنظام POS
Flask + SQLite
محسّن لأجهزة Synology DS120j
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import sqlite3
import os
from datetime import datetime
import json

app = Flask(__name__, static_folder='frontend')
CORS(app)

# إعدادات قاعدة البيانات
DB_PATH = 'database/pos.db'

def get_db():
    """الاتصال بقاعدة البيانات"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def dict_from_row(row):
    """تحويل صف قاعدة البيانات إلى قاموس"""
    return dict(zip(row.keys(), row))

# ===== API المستخدمين =====

@app.route('/api/login', methods=['POST'])
def login():
    """تسجيل دخول المستخدم"""
    try:
        data = request.json
        username = data.get('username')
        password = data.get('password')
        
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT u.id, u.username, u.full_name, u.role, u.invoice_prefix, u.is_active, u.branch_id,
                   u.can_view_products, u.can_add_products, u.can_edit_products, u.can_delete_products,
                   u.can_view_inventory, u.can_add_inventory, u.can_edit_inventory, u.can_delete_inventory,
                   u.can_view_invoices, u.can_delete_invoices,
                   u.can_view_customers, u.can_add_customer, u.can_edit_customer, u.can_delete_customer,
                   u.can_view_reports, u.can_view_accounting, u.can_manage_users, u.can_access_settings,
                   b.name as branch_name
            FROM users u
            LEFT JOIN branches b ON u.branch_id = b.id
            WHERE u.username = ? AND u.password = ? AND u.is_active = 1
        ''', (username, password))
        
        user = cursor.fetchone()
        conn.close()
        
        if user:
            user_data = dict_from_row(user)
            return jsonify({'success': True, 'user': user_data})
        else:
            return jsonify({'success': False, 'error': 'اسم المستخدم أو كلمة المرور غير صحيحة'}), 401
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/users', methods=['GET'])
def get_users():
    """جلب جميع المستخدمين"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT id, username, full_name, role, invoice_prefix, branch_id, is_active, created_at FROM users ORDER BY created_at DESC')
        users = [dict_from_row(row) for row in cursor.fetchall()]
        conn.close()
        return jsonify({'success': True, 'users': users})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/users', methods=['POST'])
def add_user():
    """إضافة مستخدم جديد"""
    try:
        data = request.json
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO users (username, password, full_name, role, invoice_prefix, branch_id,
                             can_view_products, can_add_products, can_edit_products, can_delete_products,
                             can_view_inventory, can_add_inventory, can_edit_inventory, can_delete_inventory,
                             can_view_invoices, can_delete_invoices,
                             can_view_customers, can_add_customer, can_edit_customer, can_delete_customer,
                             can_view_reports, can_view_accounting, can_manage_users, can_access_settings)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data.get('username'),
            data.get('password'),
            data.get('full_name'),
            data.get('role', 'cashier'),
            data.get('invoice_prefix', ''),
            data.get('branch_id', 1),
            data.get('can_view_products', 0),
            data.get('can_add_products', 0),
            data.get('can_edit_products', 0),
            data.get('can_delete_products', 0),
            data.get('can_view_inventory', 0),
            data.get('can_add_inventory', 0),
            data.get('can_edit_inventory', 0),
            data.get('can_delete_inventory', 0),
            data.get('can_view_invoices', 1),
            data.get('can_delete_invoices', 0),
            data.get('can_view_customers', 0),
            data.get('can_add_customer', 0),
            data.get('can_edit_customer', 0),
            data.get('can_delete_customer', 0),
            data.get('can_view_reports', 0),
            data.get('can_view_accounting', 0),
            data.get('can_manage_users', 0),
            data.get('can_access_settings', 0)
        ))
        
        user_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'id': user_id})
    except sqlite3.IntegrityError:
        return jsonify({'success': False, 'error': 'اسم المستخدم موجود مسبقاً'}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    """تحديث بيانات مستخدم"""
    try:
        data = request.json
        conn = get_db()
        cursor = conn.cursor()
        
        # بناء الاستعلام ديناميكياً
        updates = []
        params = []
        
        if 'password' in data and data['password']:
            updates.append('password = ?')
            params.append(data['password'])
        if 'full_name' in data:
            updates.append('full_name = ?')
            params.append(data['full_name'])
        if 'role' in data:
            updates.append('role = ?')
            params.append(data['role'])
        if 'invoice_prefix' in data:
            updates.append('invoice_prefix = ?')
            params.append(data['invoice_prefix'])
        if 'branch_id' in data:
            updates.append('branch_id = ?')
            params.append(data['branch_id'])
        if 'can_view_products' in data:
            updates.append('can_view_products = ?')
            params.append(data['can_view_products'])
        if 'can_add_products' in data:
            updates.append('can_add_products = ?')
            params.append(data['can_add_products'])
        if 'can_edit_products' in data:
            updates.append('can_edit_products = ?')
            params.append(data['can_edit_products'])
        if 'can_delete_products' in data:
            updates.append('can_delete_products = ?')
            params.append(data['can_delete_products'])
        if 'can_view_inventory' in data:
            updates.append('can_view_inventory = ?')
            params.append(data['can_view_inventory'])
        if 'can_add_inventory' in data:
            updates.append('can_add_inventory = ?')
            params.append(data['can_add_inventory'])
        if 'can_edit_inventory' in data:
            updates.append('can_edit_inventory = ?')
            params.append(data['can_edit_inventory'])
        if 'can_delete_inventory' in data:
            updates.append('can_delete_inventory = ?')
            params.append(data['can_delete_inventory'])
        if 'can_view_invoices' in data:
            updates.append('can_view_invoices = ?')
            params.append(data['can_view_invoices'])
        if 'can_delete_invoices' in data:
            updates.append('can_delete_invoices = ?')
            params.append(data['can_delete_invoices'])
        if 'can_view_customers' in data:
            updates.append('can_view_customers = ?')
            params.append(data['can_view_customers'])
        if 'can_add_customer' in data:
            updates.append('can_add_customer = ?')
            params.append(data['can_add_customer'])
        if 'can_edit_customer' in data:
            updates.append('can_edit_customer = ?')
            params.append(data['can_edit_customer'])
        if 'can_delete_customer' in data:
            updates.append('can_delete_customer = ?')
            params.append(data['can_delete_customer'])
        if 'can_view_reports' in data:
            updates.append('can_view_reports = ?')
            params.append(data['can_view_reports'])
        if 'can_view_accounting' in data:
            updates.append('can_view_accounting = ?')
            params.append(data['can_view_accounting'])
        if 'can_manage_users' in data:
            updates.append('can_manage_users = ?')
            params.append(data['can_manage_users'])
        if 'can_access_settings' in data:
            updates.append('can_access_settings = ?')
            params.append(data['can_access_settings'])
        if 'is_active' in data:
            updates.append('is_active = ?')
            params.append(data['is_active'])
        
        if updates:
            params.append(user_id)
            query = f"UPDATE users SET {', '.join(updates)} WHERE id = ?"
            cursor.execute(query, params)
            conn.commit()
        
        conn.close()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    """حذف مستخدم"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # لا يمكن حذف المستخدم admin
        cursor.execute('SELECT role FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()
        
        if user and dict_from_row(user)['role'] == 'admin':
            return jsonify({'success': False, 'error': 'لا يمكن حذف حساب المدير'}), 400
        
        cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ===== الصفحة الرئيسية =====
@app.route('/')
def index():
    return send_from_directory('frontend', 'index.html')

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory('frontend', path)

# ===== API المنتجات =====

@app.route('/api/products', methods=['GET'])
def get_products():
    """جلب جميع المنتجات - من التوزيعات على الفروع"""
    try:
        branch_id = request.args.get('branch_id')
        conn = get_db()
        cursor = conn.cursor()
        
        # جلب المنتجات من branch_stock مع معلومات المنتج من inventory
        if branch_id == 'all':
            # جلب كل التوزيعات
            cursor.execute('''
                SELECT bs.id, bs.stock, bs.branch_id, 
                       i.name, i.barcode, i.category, i.price, i.cost, i.image_data
                FROM branch_stock bs
                JOIN inventory i ON bs.inventory_id = i.id
                ORDER BY bs.branch_id, i.name
            ''')
        elif branch_id:
            # جلب توزيعات فرع معين
            cursor.execute('''
                SELECT bs.id, bs.stock, bs.branch_id,
                       i.name, i.barcode, i.category, i.price, i.cost, i.image_data
                FROM branch_stock bs
                JOIN inventory i ON bs.inventory_id = i.id
                WHERE bs.branch_id = ?
                ORDER BY i.name
            ''', (branch_id,))
        else:
            # افتراضياً الفرع 1
            cursor.execute('''
                SELECT bs.id, bs.stock, bs.branch_id,
                       i.name, i.barcode, i.category, i.price, i.cost, i.image_data
                FROM branch_stock bs
                JOIN inventory i ON bs.inventory_id = i.id
                WHERE bs.branch_id = ?
                ORDER BY i.name
            ''', (1,))
        
        products = [dict_from_row(row) for row in cursor.fetchall()]
        conn.close()
        return jsonify({'success': True, 'products': products})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/products', methods=['POST'])
def add_product():
    """إضافة منتج جديد"""
    try:
        data = request.json
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO products (name, barcode, price, cost, stock, category, image_data, branch_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data.get('name'),
            data.get('barcode'),
            data.get('price', 0),
            data.get('cost', 0),
            data.get('stock', 0),
            data.get('category', ''),
            data.get('image_data', ''),
            data.get('branch_id', 1)
        ))
        
        product_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'id': product_id})
    except sqlite3.IntegrityError:
        return jsonify({'success': False, 'error': 'الباركود موجود مسبقاً'}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/products/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    """تحديث منتج"""
    try:
        data = request.json
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE products 
            SET name=?, barcode=?, price=?, cost=?, stock=?, category=?, image_data=?, branch_id=?, updated_at=CURRENT_TIMESTAMP
            WHERE id=?
        ''', (
            data.get('name'),
            data.get('barcode'),
            data.get('price'),
            data.get('cost'),
            data.get('stock'),
            data.get('category'),
            data.get('image_data'),
            data.get('branch_id', 1),
            product_id
        ))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/products/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    """حذف منتج"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM products WHERE id=?', (product_id,))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ===== API المخزون الأساسي =====

@app.route('/api/inventory', methods=['GET'])
def get_inventory():
    """جلب جميع المنتجات الأساسية"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM inventory ORDER BY name')
        inventory = [dict_from_row(row) for row in cursor.fetchall()]
        conn.close()
        return jsonify({'success': True, 'inventory': inventory})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/inventory', methods=['POST'])
def add_inventory():
    """إضافة منتج أساسي للمخزون"""
    conn = None
    try:
        data = request.json
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO inventory (name, barcode, category, price, cost, image_data)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            data.get('name'),
            data.get('barcode'),
            data.get('category', ''),
            data.get('price', 0),
            data.get('cost', 0),
            data.get('image_data', '')
        ))
        
        inventory_id = cursor.lastrowid
        conn.commit()
        
        return jsonify({'success': True, 'id': inventory_id})
    except sqlite3.IntegrityError:
        if conn:
            conn.rollback()
        return jsonify({'success': False, 'error': 'الباركود موجود مسبقاً'}), 400
    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if conn:
            conn.close()

@app.route('/api/inventory/<int:inventory_id>', methods=['PUT'])
def update_inventory(inventory_id):
    """تعديل منتج أساسي"""
    try:
        data = request.json
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE inventory 
            SET name=?, barcode=?, category=?, price=?, cost=?, image_data=?, updated_at=CURRENT_TIMESTAMP
            WHERE id=?
        ''', (
            data.get('name'),
            data.get('barcode'),
            data.get('category'),
            data.get('price'),
            data.get('cost'),
            data.get('image_data'),
            inventory_id
        ))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/inventory/<int:inventory_id>', methods=['DELETE'])
def delete_inventory(inventory_id):
    """حذف منتج أساسي"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        # حذف التوزيعات أولاً
        cursor.execute('DELETE FROM branch_stock WHERE inventory_id=?', (inventory_id,))
        cursor.execute('DELETE FROM inventory WHERE id=?', (inventory_id,))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ===== API توزيع المخزون على الفروع =====

@app.route('/api/branch-stock', methods=['GET'])
def get_branch_stock():
    """جلب توزيع المخزون (حسب الفرع أو المنتج)"""
    try:
        branch_id = request.args.get('branch_id')
        inventory_id = request.args.get('inventory_id')
        
        conn = get_db()
        cursor = conn.cursor()
        
        query = '''
            SELECT bs.*, i.name, i.barcode, i.category, i.price, i.cost, i.image_data
            FROM branch_stock bs
            JOIN inventory i ON bs.inventory_id = i.id
            WHERE 1=1
        '''
        params = []
        
        if branch_id:
            query += ' AND bs.branch_id = ?'
            params.append(branch_id)
        
        if inventory_id:
            query += ' AND bs.inventory_id = ?'
            params.append(inventory_id)
        
        query += ' ORDER BY i.name'
        
        cursor.execute(query, params)
        stock = [dict_from_row(row) for row in cursor.fetchall()]
        conn.close()
        
        return jsonify({'success': True, 'stock': stock})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/branch-stock', methods=['POST'])
def add_branch_stock():
    """توزيع منتج على فرع"""
    try:
        data = request.json
        conn = get_db()
        cursor = conn.cursor()
        
        # التحقق من وجود التوزيع
        cursor.execute('''
            SELECT id, stock FROM branch_stock 
            WHERE inventory_id = ? AND branch_id = ?
        ''', (data.get('inventory_id'), data.get('branch_id')))
        
        existing = cursor.fetchone()
        
        if existing:
            # تحديث الكمية
            new_stock = existing['stock'] + data.get('stock', 0)
            cursor.execute('''
                UPDATE branch_stock SET stock = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (new_stock, existing['id']))
            stock_id = existing['id']
        else:
            # إضافة جديد
            cursor.execute('''
                INSERT INTO branch_stock (inventory_id, branch_id, stock)
                VALUES (?, ?, ?)
            ''', (
                data.get('inventory_id'),
                data.get('branch_id'),
                data.get('stock', 0)
            ))
            stock_id = cursor.lastrowid
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'id': stock_id})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/branch-stock/<int:stock_id>', methods=['PUT'])
def update_branch_stock(stock_id):
    """تحديث كمية في فرع"""
    try:
        data = request.json
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE branch_stock 
            SET stock = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (data.get('stock', 0), stock_id))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/branch-stock/<int:stock_id>', methods=['DELETE'])
def delete_branch_stock(stock_id):
    """حذف توزيع من فرع"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM branch_stock WHERE id = ?', (stock_id,))
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/products/search', methods=['GET'])
def search_products():
    """البحث عن منتج بالاسم أو الباركود"""
    try:
        query = request.args.get('q', '')
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM products 
            WHERE name LIKE ? OR barcode LIKE ?
            LIMIT 20
        ''', (f'%{query}%', f'%{query}%'))
        
        products = [dict_from_row(row) for row in cursor.fetchall()]
        conn.close()
        
        return jsonify({'success': True, 'products': products})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ===== API الفواتير =====

@app.route('/api/invoices', methods=['GET'])
def get_invoices():
    """جلب الفواتير مع إمكانية التصفية"""
    try:
        # معاملات البحث
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        limit = request.args.get('limit', 100, type=int)
        
        conn = get_db()
        cursor = conn.cursor()
        
        query = 'SELECT * FROM invoices WHERE 1=1'
        params = []
        
        if start_date:
            query += ' AND date(created_at) >= ?'
            params.append(start_date)
        
        if end_date:
            query += ' AND date(created_at) <= ?'
            params.append(end_date)
        
        query += ' ORDER BY created_at DESC LIMIT ?'
        params.append(limit)
        
        cursor.execute(query, params)
        invoices = [dict_from_row(row) for row in cursor.fetchall()]
        conn.close()
        
        return jsonify({'success': True, 'invoices': invoices})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/invoices/<int:invoice_id>', methods=['GET'])
def get_invoice(invoice_id):
    """جلب فاتورة محددة مع عناصرها"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # جلب الفاتورة
        cursor.execute('SELECT * FROM invoices WHERE id=?', (invoice_id,))
        invoice_row = cursor.fetchone()
        
        if not invoice_row:
            return jsonify({'success': False, 'error': 'الفاتورة غير موجودة'}), 404
        
        invoice = dict_from_row(invoice_row)
        
        # جلب عناصر الفاتورة
        cursor.execute('SELECT * FROM invoice_items WHERE invoice_id=?', (invoice_id,))
        items = [dict_from_row(row) for row in cursor.fetchall()]
        
        invoice['items'] = items
        conn.close()
        
        return jsonify({'success': True, 'invoice': invoice})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/invoices/clear-all', methods=['DELETE'])
def clear_all_invoices():
    """حذف جميع الفواتير (Admin فقط)"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # حذف عناصر الفواتير أولاً
        cursor.execute('DELETE FROM invoice_items')
        
        # حذف الفواتير
        cursor.execute('DELETE FROM invoices')
        
        conn.commit()
        deleted_count = cursor.rowcount
        conn.close()
        
        return jsonify({'success': True, 'deleted': deleted_count})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/invoices', methods=['POST'])
def create_invoice():
    """إنشاء فاتورة جديدة"""
    try:
        data = request.json
        conn = get_db()
        cursor = conn.cursor()
        
        # الحصول على اسم الفرع
        branch_id = data.get('branch_id', 1)
        cursor.execute('SELECT name FROM branches WHERE id = ?', (branch_id,))
        branch = cursor.fetchone()
        branch_name = branch['name'] if branch else 'الفرع الرئيسي'
        
        # تعديل رقم الفاتورة ليشمل رقم الفرع (مثل: AHM-001-B1)
        original_invoice_number = data.get('invoice_number', '')
        invoice_number_with_branch = f"{original_invoice_number}-B{branch_id}"
        
        # بيانات الولاء
        customer_id = data.get('customer_id')
        loyalty_points_earned = data.get('loyalty_points_earned', 0)
        loyalty_points_redeemed = data.get('loyalty_points_redeemed', 0)
        loyalty_discount = data.get('loyalty_discount', 0)
        
        # إدراج الفاتورة
        cursor.execute('''
            INSERT INTO invoices 
            (invoice_number, customer_id, customer_name, customer_phone, customer_address,
             subtotal, discount, total, payment_method, employee_name, notes, transaction_number, 
             branch_name, delivery_fee, loyalty_points_earned, loyalty_points_redeemed, loyalty_discount)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            invoice_number_with_branch,
            customer_id,
            data.get('customer_name', ''),
            data.get('customer_phone', ''),
            data.get('customer_address', ''),
            data.get('subtotal', 0),
            data.get('discount', 0),
            data.get('total', 0),
            data.get('payment_method', 'نقداً'),
            data.get('employee_name', ''),
            data.get('notes', ''),
            data.get('transaction_number', ''),
            branch_name,
            data.get('delivery_fee', 0),
            loyalty_points_earned,
            loyalty_points_redeemed,
            loyalty_discount
        ))
        
        invoice_id = cursor.lastrowid
        
        # إدراج عناصر الفاتورة وتحديث المخزون
        for item in data.get('items', []):
            # الحصول على branch_stock_id
            branch_stock_id = item.get('branch_stock_id') or item.get('product_id')
            
            cursor.execute('''
                INSERT INTO invoice_items 
                (invoice_id, product_id, product_name, quantity, price, total, branch_stock_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                invoice_id,
                item.get('product_id'),
                item.get('product_name'),
                item.get('quantity'),
                item.get('price'),
                item.get('total'),
                branch_stock_id
            ))
            
            # تحديث المخزون في branch_stock
            if branch_stock_id:
                cursor.execute('''
                    UPDATE branch_stock 
                    SET stock = stock - ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (item.get('quantity'), branch_stock_id))
        
        # تحديث نقاط العميل (إذا كان موجوداً)
        if customer_id:
            # إضافة النقاط المكتسبة
            if loyalty_points_earned > 0:
                cursor.execute('''
                    UPDATE customers 
                    SET points = points + ?,
                        total_spent = total_spent + ?,
                        last_visit = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (loyalty_points_earned, data.get('total', 0), customer_id))
                
                # تسجيل في تاريخ النقاط
                cursor.execute('''
                    INSERT INTO loyalty_transactions (customer_id, invoice_id, points, type, description)
                    VALUES (?, ?, ?, 'earned', 'نقاط من فاتورة')
                ''', (customer_id, invoice_id, loyalty_points_earned))
            
            # خصم النقاط المستخدمة
            if loyalty_points_redeemed > 0:
                cursor.execute('''
                    UPDATE customers 
                    SET points = points - ?,
                        last_visit = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (loyalty_points_redeemed, customer_id))
                
                # تسجيل في تاريخ النقاط
                cursor.execute('''
                    INSERT INTO loyalty_transactions (customer_id, invoice_id, points, type, description)
                    VALUES (?, ?, ?, 'redeemed', ?)
                ''', (customer_id, invoice_id, -loyalty_points_redeemed, f'استخدام نقاط - خصم {loyalty_discount:.3f} د.ك'))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'id': invoice_id, 'invoice_number': invoice_number_with_branch})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ===== API التالف =====

@app.route('/api/damaged-items', methods=['GET'])
def get_damaged_items():
    """جلب التالف"""
    try:
        branch_id = request.args.get('branch_id')
        conn = get_db()
        cursor = conn.cursor()
        
        query = '''
            SELECT d.*, i.name as product_name, b.name as branch_name
            FROM damaged_items d
            JOIN inventory i ON d.inventory_id = i.id
            LEFT JOIN branches b ON d.branch_id = b.id
            WHERE 1=1
        '''
        params = []
        
        if branch_id:
            query += ' AND d.branch_id = ?'
            params.append(branch_id)
        
        query += ' ORDER BY d.created_at DESC'
        
        cursor.execute(query, params)
        damaged = [dict_from_row(row) for row in cursor.fetchall()]
        conn.close()
        
        return jsonify({'success': True, 'damaged': damaged})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/damaged-items', methods=['POST'])
def add_damaged_item():
    """إضافة تالف"""
    try:
        data = request.json
        conn = get_db()
        cursor = conn.cursor()
        
        # إضافة التالف
        cursor.execute('''
            INSERT INTO damaged_items 
            (inventory_id, branch_id, quantity, reason, reported_by)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            data.get('inventory_id'),
            data.get('branch_id'),
            data.get('quantity'),
            data.get('reason', ''),
            data.get('reported_by')
        ))
        
        # تحديث المخزون (خصم التالف)
        cursor.execute('''
            UPDATE branch_stock 
            SET stock = stock - ?
            WHERE inventory_id = ? AND branch_id = ?
        ''', (
            data.get('quantity'),
            data.get('inventory_id'),
            data.get('branch_id')
        ))
        
        damaged_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'id': damaged_id})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/damaged-items/<int:damaged_id>', methods=['DELETE'])
def delete_damaged_item(damaged_id):
    """حذف تالف"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM damaged_items WHERE id = ?', (damaged_id,))
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/system-logs', methods=['GET'])
def get_system_logs():
    """جلب سجل النظام"""
    try:
        limit = request.args.get('limit', 100)
        action_type = request.args.get('action_type')
        user_id = request.args.get('user_id')
        
        conn = get_db()
        cursor = conn.cursor()
        
        query = 'SELECT * FROM system_logs WHERE 1=1'
        params = []
        
        if action_type:
            query += ' AND action_type = ?'
            params.append(action_type)
        
        if user_id:
            query += ' AND user_id = ?'
            params.append(user_id)
        
        query += ' ORDER BY created_at DESC LIMIT ?'
        params.append(limit)
        
        cursor.execute(query, params)
        logs = [dict_from_row(row) for row in cursor.fetchall()]
        conn.close()
        
        return jsonify({'success': True, 'logs': logs})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/system-logs', methods=['POST'])
def add_system_log():
    """إضافة سجل"""
    try:
        data = request.json
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO system_logs 
            (action_type, description, user_id, user_name, branch_id, target_id, details)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            data.get('action_type'),
            data.get('description'),
            data.get('user_id'),
            data.get('user_name'),
            data.get('branch_id'),
            data.get('target_id'),
            data.get('details')
        ))
        
        log_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'id': log_id})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ===== API التقارير =====

@app.route('/api/reports/sales', methods=['GET'])
def sales_report():
    """تقرير المبيعات خلال فترة"""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        branch_id = request.args.get('branch_id')
        
        conn = get_db()
        cursor = conn.cursor()
        
        # الإحصائيات العامة
        query = '''
            SELECT 
                COUNT(*) as total_invoices,
                SUM(subtotal) as total_subtotal,
                SUM(discount) as total_discount,
                SUM(delivery_fee) as total_delivery,
                SUM(total) as total_sales,
                AVG(total) as average_sale
            FROM invoices
            WHERE 1=1
        '''
        params = []
        
        if start_date:
            query += ' AND date(created_at) >= ?'
            params.append(start_date)
        
        if end_date:
            query += ' AND date(created_at) <= ?'
            params.append(end_date)
        
        if branch_id:
            # البحث بـ branch_id أو branch_name
            try:
                # استخدام cursor منفصل للبحث عن الفرع
                temp_cursor = conn.cursor()
                temp_cursor.execute('SELECT name FROM branches WHERE id = ?', (branch_id,))
                branch = temp_cursor.fetchone()
                if branch:
                    query += ' AND branch_name = ?'
                    params.append(branch['name'])
                else:
                    query += ' AND branch_name LIKE ?'
                    params.append(f'%{branch_id}%')
            except:
                # إذا فشل، استخدم LIKE
                query += ' AND branch_name LIKE ?'
                params.append(f'%{branch_id}%')
        
        cursor.execute(query, params)
        report = dict_from_row(cursor.fetchone())
        
        # تقرير حسب طريقة الدفع
        query_payment = '''
            SELECT payment_method, COUNT(*) as count, SUM(total) as total
            FROM invoices
            WHERE 1=1
        '''
        
        if start_date:
            query_payment += ' AND date(created_at) >= ?'
        if end_date:
            query_payment += ' AND date(created_at) <= ?'
        if branch_id:
            query_payment += ' AND branch_name LIKE ?'
        
        query_payment += ' GROUP BY payment_method'
        
        cursor.execute(query_payment, params)
        payment_methods = [dict_from_row(row) for row in cursor.fetchall()]
        
        # تقرير حسب الفرع
        query_branch = '''
            SELECT branch_name, COUNT(*) as count, SUM(total) as total
            FROM invoices
            WHERE branch_name IS NOT NULL
        '''
        
        if start_date:
            query_branch += ' AND date(created_at) >= ?'
        if end_date:
            query_branch += ' AND date(created_at) <= ?'
        if branch_id:
            query_branch += ' AND branch_name LIKE ?'
        
        query_branch += ' GROUP BY branch_name'
        
        cursor.execute(query_branch, params)
        branches = [dict_from_row(row) for row in cursor.fetchall()]
        
        # جلب الفواتير
        query_invoices = '''
            SELECT * FROM invoices
            WHERE 1=1
        '''
        
        if start_date:
            query_invoices += ' AND date(created_at) >= ?'
        if end_date:
            query_invoices += ' AND date(created_at) <= ?'
        if branch_id:
            query_invoices += ' AND branch_name LIKE ?'
        
        query_invoices += ' ORDER BY created_at DESC'
        
        cursor.execute(query_invoices, params)
        invoices = [dict_from_row(row) for row in cursor.fetchall()]
        
        report['payment_methods'] = payment_methods
        report['branches'] = branches
        report['invoices'] = invoices
        
        conn.close()
        
        return jsonify({'success': True, 'report': report})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/reports/inventory', methods=['GET'])
def inventory_report():
    """تقرير المخزون"""
    try:
        branch_id = request.args.get('branch_id')
        
        conn = get_db()
        cursor = conn.cursor()
        
        # جلب المخزون مع الحسابات
        query = '''
            SELECT 
                i.id,
                i.name,
                i.barcode,
                i.category,
                i.price,
                i.cost,
                bs.branch_id,
                b.name as branch_name,
                bs.stock,
                (bs.stock * i.cost) as stock_value
            FROM inventory i
            LEFT JOIN branch_stock bs ON i.id = bs.inventory_id
            LEFT JOIN branches b ON bs.branch_id = b.id
            WHERE 1=1
        '''
        params = []
        
        if branch_id:
            query += ' AND bs.branch_id = ?'
            params.append(branch_id)
        
        query += ' ORDER BY i.name'
        
        cursor.execute(query, params)
        items = [dict_from_row(row) for row in cursor.fetchall()]
        
        # الإحصائيات
        total_items = len(items)
        total_stock = sum(item['stock'] or 0 for item in items)
        total_value = sum(item['stock_value'] or 0 for item in items)
        
        conn.close()
        
        return jsonify({
            'success': True,
            'report': {
                'total_items': total_items,
                'total_stock': total_stock,
                'total_value': total_value,
                'items': items
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/reports/damaged', methods=['GET'])
def damaged_report():
    """تقرير التالف خلال فترة"""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        branch_id = request.args.get('branch_id')
        
        conn = get_db()
        cursor = conn.cursor()
        
        query = '''
            SELECT 
                d.*,
                i.name as product_name,
                i.cost,
                (d.quantity * i.cost) as damage_value,
                b.name as branch_name
            FROM damaged_items d
            JOIN inventory i ON d.inventory_id = i.id
            LEFT JOIN branches b ON d.branch_id = b.id
            WHERE 1=1
        '''
        params = []
        
        if start_date:
            query += ' AND date(d.created_at) >= ?'
            params.append(start_date)
        
        if end_date:
            query += ' AND date(d.created_at) <= ?'
            params.append(end_date)
        
        if branch_id:
            query += ' AND d.branch_id = ?'
            params.append(branch_id)
        
        query += ' ORDER BY d.created_at DESC'
        
        cursor.execute(query, params)
        damaged = [dict_from_row(row) for row in cursor.fetchall()]
        
        # الإحصائيات
        total_damaged = sum(item['quantity'] for item in damaged)
        total_value = sum(item['damage_value'] or 0 for item in damaged)
        
        conn.close()
        
        return jsonify({
            'success': True,
            'report': {
                'total_damaged': total_damaged,
                'total_value': total_value,
                'items': damaged
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
        conn.close()
        
        return jsonify({'success': True, 'report': report})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/reports/top-products', methods=['GET'])
def top_products_report():
    """تقرير المنتجات الأكثر مبيعاً"""
    try:
        limit = request.args.get('limit', 10, type=int)
        
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                product_name,
                SUM(quantity) as total_quantity,
                SUM(total) as total_sales,
                COUNT(DISTINCT invoice_id) as times_sold
            FROM invoice_items
            GROUP BY product_name
            ORDER BY total_quantity DESC
            LIMIT ?
        ''', (limit,))
        
        products = [dict_from_row(row) for row in cursor.fetchall()]
        conn.close()
        
        return jsonify({'success': True, 'products': products})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/reports/low-stock', methods=['GET'])
def low_stock_report():
    """تقرير المنتجات منخفضة المخزون"""
    try:
        threshold = request.args.get('threshold', 10, type=int)
        
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM products 
            WHERE stock <= ?
            ORDER BY stock ASC
        ''', (threshold,))
        
        products = [dict_from_row(row) for row in cursor.fetchall()]
        conn.close()
        
        return jsonify({'success': True, 'products': products})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ===== API الإعدادات =====

@app.route('/api/settings', methods=['GET'])
def get_settings():
    """جلب جميع الإعدادات"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM settings')
        settings = {row['key']: row['value'] for row in cursor.fetchall()}
        conn.close()
        return jsonify({'success': True, 'settings': settings})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/settings', methods=['PUT'])
def update_settings():
    """تحديث الإعدادات"""
    try:
        data = request.json
        conn = get_db()
        cursor = conn.cursor()
        
        for key, value in data.items():
            cursor.execute('''
                INSERT OR REPLACE INTO settings (key, value, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            ''', (key, value))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ===== API الفروع =====

@app.route('/api/branches', methods=['GET'])
def get_branches():
    """جلب كل الفروع"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM branches WHERE is_active = 1 ORDER BY name')
        branches = [dict_from_row(row) for row in cursor.fetchall()]
        conn.close()
        return jsonify({'success': True, 'branches': branches})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/branches', methods=['POST'])
def add_branch():
    """إضافة فرع جديد"""
    try:
        data = request.json
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO branches (name, location, phone)
            VALUES (?, ?, ?)
        ''', (data.get('name'), data.get('location', ''), data.get('phone', '')))
        branch_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'id': branch_id})
    except sqlite3.IntegrityError:
        return jsonify({'success': False, 'error': 'اسم الفرع موجود مسبقاً'}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/branches/<int:branch_id>', methods=['PUT'])
def update_branch(branch_id):
    """تحديث فرع"""
    try:
        data = request.json
        conn = get_db()
        cursor = conn.cursor()
        updates = []
        params = []
        
        if 'name' in data:
            updates.append('name = ?')
            params.append(data['name'])
        if 'location' in data:
            updates.append('location = ?')
            params.append(data['location'])
        if 'phone' in data:
            updates.append('phone = ?')
            params.append(data['phone'])
        if 'is_active' in data:
            updates.append('is_active = ?')
            params.append(data['is_active'])
        
        if updates:
            params.append(branch_id)
            query = f"UPDATE branches SET {', '.join(updates)} WHERE id = ?"
            cursor.execute(query, params)
            conn.commit()
        
        conn.close()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/branches/<int:branch_id>', methods=['DELETE'])
def delete_branch(branch_id):
    """حذف فرع (soft delete)"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('UPDATE branches SET is_active = 0 WHERE id = ?', (branch_id,))
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ===== API سجل الحضور =====

@app.route('/api/attendance/check-in', methods=['POST'])
def check_in():
    """تسجيل حضور"""
    try:
        data = request.json
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO attendance_log (user_id, user_name, branch_id, check_in)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        ''', (data.get('user_id'), data.get('user_name'), data.get('branch_id', 1)))
        attendance_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'id': attendance_id})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/attendance/check-out', methods=['POST'])
def check_out():
    """تسجيل انصراف"""
    try:
        data = request.json
        conn = get_db()
        cursor = conn.cursor()
        # البحث عن آخر سجل حضور بدون انصراف
        cursor.execute('''
            SELECT id FROM attendance_log
            WHERE user_id = ? AND check_out IS NULL
            ORDER BY check_in DESC LIMIT 1
        ''', (data.get('user_id'),))
        record = cursor.fetchone()
        
        if record:
            cursor.execute('''
                UPDATE attendance_log SET check_out = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (record['id'],))
            conn.commit()
            conn.close()
            return jsonify({'success': True})
        else:
            conn.close()
            return jsonify({'success': False, 'error': 'لا يوجد سجل حضور'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/attendance', methods=['GET'])
def get_attendance():
    """جلب سجل الحضور مع الفلترة"""
    try:
        user_id = request.args.get('user_id')
        date = request.args.get('date')
        branch_id = request.args.get('branch_id')
        
        conn = get_db()
        cursor = conn.cursor()
        
        query = 'SELECT * FROM attendance_log WHERE 1=1'
        params = []
        
        if user_id:
            query += ' AND user_id = ?'
            params.append(user_id)
        
        if date:
            query += ' AND DATE(check_in) = ?'
            params.append(date)
        
        if branch_id:
            query += ' AND branch_id = ?'
            params.append(branch_id)
        
        query += ' ORDER BY check_in DESC'
        
        cursor.execute(query, params)
        records = [dict_from_row(row) for row in cursor.fetchall()]
        conn.close()
        return jsonify({'success': True, 'records': records})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ===== API التكاليف =====

@app.route('/api/expenses', methods=['GET'])
def get_expenses():
    """جلب التكاليف"""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        branch_id = request.args.get('branch_id')
        
        conn = get_db()
        cursor = conn.cursor()
        
        query = 'SELECT * FROM expenses WHERE 1=1'
        params = []
        
        if start_date:
            query += ' AND date(expense_date) >= ?'
            params.append(start_date)
        if end_date:
            query += ' AND date(expense_date) <= ?'
            params.append(end_date)
        if branch_id:
            query += ' AND branch_id = ?'
            params.append(branch_id)
        
        query += ' ORDER BY expense_date DESC'
        
        cursor.execute(query, params)
        expenses = [dict_from_row(row) for row in cursor.fetchall()]
        conn.close()
        
        return jsonify({'success': True, 'expenses': expenses})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/expenses', methods=['POST'])
def add_expense():
    """إضافة تكلفة"""
    conn = None
    try:
        data = request.json
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO expenses (expense_type, amount, description, expense_date, branch_id, created_by)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            data.get('expense_type'),
            data.get('amount'),
            data.get('description', ''),
            data.get('expense_date'),
            data.get('branch_id'),
            data.get('created_by')
        ))
        
        expense_id = cursor.lastrowid
        conn.commit()
        
        return jsonify({'success': True, 'id': expense_id})
    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if conn:
            conn.close()

@app.route('/api/expenses/<int:expense_id>', methods=['DELETE'])
def delete_expense(expense_id):
    """حذف تكلفة"""
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM expenses WHERE id = ?', (expense_id,))
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if conn:
            conn.close()

# ===== التقارير المتقدمة =====

@app.route('/api/reports/sales-by-product', methods=['GET'])
def sales_by_product():
    """تقرير المبيعات حسب المنتج"""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        branch_id = request.args.get('branch_id')
        
        conn = get_db()
        cursor = conn.cursor()
        
        query = '''
            SELECT 
                ii.product_name,
                SUM(ii.quantity) as total_quantity,
                SUM(ii.total) as total_sales,
                COUNT(DISTINCT ii.invoice_id) as invoice_count,
                AVG(ii.price) as avg_price
            FROM invoice_items ii
            JOIN invoices i ON ii.invoice_id = i.id
            WHERE 1=1
        '''
        params = []
        
        if start_date:
            query += ' AND date(i.created_at) >= ?'
            params.append(start_date)
        if end_date:
            query += ' AND date(i.created_at) <= ?'
            params.append(end_date)
        if branch_id:
            cursor.execute('SELECT name FROM branches WHERE id = ?', (branch_id,))
            branch = cursor.fetchone()
            if branch:
                query += ' AND i.branch_name = ?'
                params.append(branch['name'])
        
        query += ' GROUP BY ii.product_name ORDER BY total_sales DESC'
        
        cursor.execute(query, params)
        products = [dict_from_row(row) for row in cursor.fetchall()]
        
        # إحصائيات إجمالية
        total_sales = sum(p['total_sales'] for p in products)
        total_quantity = sum(p['total_quantity'] for p in products)
        
        conn.close()
        
        return jsonify({
            'success': True,
            'products': products,
            'summary': {
                'total_sales': total_sales,
                'total_quantity': total_quantity,
                'products_count': len(products)
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/reports/sales-by-branch', methods=['GET'])
def sales_by_branch():
    """تقرير المبيعات حسب الفرع"""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        conn = get_db()
        cursor = conn.cursor()
        
        query = '''
            SELECT 
                branch_name,
                COUNT(*) as invoice_count,
                SUM(subtotal) as total_subtotal,
                SUM(discount) as total_discount,
                SUM(delivery_fee) as total_delivery,
                SUM(total) as total_sales,
                AVG(total) as avg_sale
            FROM invoices
            WHERE 1=1
        '''
        params = []
        
        if start_date:
            query += ' AND date(created_at) >= ?'
            params.append(start_date)
        if end_date:
            query += ' AND date(created_at) <= ?'
            params.append(end_date)
        
        query += ' GROUP BY branch_name ORDER BY total_sales DESC'
        
        cursor.execute(query, params)
        branches = [dict_from_row(row) for row in cursor.fetchall()]
        
        # إحصائيات إجمالية
        total_sales = sum(b['total_sales'] for b in branches)
        total_invoices = sum(b['invoice_count'] for b in branches)
        
        conn.close()
        
        return jsonify({
            'success': True,
            'branches': branches,
            'summary': {
                'total_sales': total_sales,
                'total_invoices': total_invoices,
                'branches_count': len(branches)
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/reports/profit-loss', methods=['GET'])
def profit_loss():
    """تقرير الربح والخسارة"""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        branch_id = request.args.get('branch_id')
        
        conn = get_db()
        cursor = conn.cursor()
        
        # حساب المبيعات
        sales_query = 'SELECT SUM(total) as total_sales, SUM(subtotal) as subtotal FROM invoices WHERE 1=1'
        sales_params = []
        
        if start_date:
            sales_query += ' AND date(created_at) >= ?'
            sales_params.append(start_date)
        if end_date:
            sales_query += ' AND date(created_at) <= ?'
            sales_params.append(end_date)
        if branch_id:
            cursor.execute('SELECT name FROM branches WHERE id = ?', (branch_id,))
            branch = cursor.fetchone()
            if branch:
                sales_query += ' AND branch_name = ?'
                sales_params.append(branch['name'])
        
        cursor.execute(sales_query, sales_params)
        sales_data = dict_from_row(cursor.fetchone())
        total_revenue = sales_data['total_sales'] or 0
        
        # حساب تكلفة البضاعة المباعة (COGS)
        cogs_query = '''
            SELECT SUM(ii.quantity * COALESCE(inv.cost, 0)) as total_cogs
            FROM invoice_items ii
            LEFT JOIN inventory inv ON ii.product_name = inv.name
            JOIN invoices i ON ii.invoice_id = i.id
            WHERE 1=1
        '''
        cogs_params = []
        
        if start_date:
            cogs_query += ' AND date(i.created_at) >= ?'
            cogs_params.append(start_date)
        if end_date:
            cogs_query += ' AND date(i.created_at) <= ?'
            cogs_params.append(end_date)
        if branch_id:
            cursor.execute('SELECT name FROM branches WHERE id = ?', (branch_id,))
            branch = cursor.fetchone()
            if branch:
                cogs_query += ' AND i.branch_name = ?'
                cogs_params.append(branch['name'])
        
        cursor.execute(cogs_query, cogs_params)
        cogs_data = dict_from_row(cursor.fetchone())
        total_cogs = cogs_data['total_cogs'] or 0
        
        # حساب التكاليف
        expenses_query = 'SELECT SUM(amount) as total_expenses FROM expenses WHERE 1=1'
        expenses_params = []
        
        if start_date:
            expenses_query += ' AND date(expense_date) >= ?'
            expenses_params.append(start_date)
        if end_date:
            expenses_query += ' AND date(expense_date) <= ?'
            expenses_params.append(end_date)
        if branch_id:
            expenses_query += ' AND branch_id = ?'
            expenses_params.append(branch_id)
        
        cursor.execute(expenses_query, expenses_params)
        expenses_data = dict_from_row(cursor.fetchone())
        total_expenses = expenses_data['total_expenses'] or 0
        
        # حساب الربح
        gross_profit = total_revenue - total_cogs
        net_profit = gross_profit - total_expenses
        profit_margin = (net_profit / total_revenue * 100) if total_revenue > 0 else 0
        
        conn.close()
        
        return jsonify({
            'success': True,
            'report': {
                'total_revenue': total_revenue,
                'total_cogs': total_cogs,
                'gross_profit': gross_profit,
                'total_expenses': total_expenses,
                'net_profit': net_profit,
                'profit_margin': profit_margin
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ===============================================
# 🎯 APIs نظام الولاء (Loyalty System)
# ===============================================

@app.route('/api/customers', methods=['GET'])
def get_customers():
    """جلب جميع العملاء"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, name, phone, email, points, total_spent, 
                   join_date, last_visit, notes, is_active
            FROM customers 
            WHERE is_active = 1
            ORDER BY name
        ''')
        customers = [dict_from_row(row) for row in cursor.fetchall()]
        conn.close()
        return jsonify({'success': True, 'customers': customers})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/customers/<int:customer_id>', methods=['GET'])
def get_customer(customer_id):
    """جلب تفاصيل عميل محدد"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # بيانات العميل
        cursor.execute('''
            SELECT id, name, phone, email, points, total_spent,
                   join_date, last_visit, notes, is_active
            FROM customers
            WHERE id = ?
        ''', (customer_id,))
        customer = cursor.fetchone()
        
        if not customer:
            conn.close()
            return jsonify({'success': False, 'error': 'العميل غير موجود'}), 404
        
        customer_data = dict_from_row(customer)
        
        # تاريخ النقاط
        cursor.execute('''
            SELECT id, points, type, description, created_at
            FROM loyalty_transactions
            WHERE customer_id = ?
            ORDER BY created_at DESC
            LIMIT 50
        ''', (customer_id,))
        transactions = [dict_from_row(row) for row in cursor.fetchall()]
        customer_data['transactions'] = transactions
        
        conn.close()
        return jsonify({'success': True, 'customer': customer_data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/customers/search', methods=['GET'])
def search_customer():
    """البحث عن عميل بالهاتف"""
    try:
        phone = request.args.get('phone', '').strip()
        if not phone:
            return jsonify({'success': False, 'error': 'رقم الهاتف مطلوب'}), 400
        
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, name, phone, email, points, total_spent,
                   join_date, last_visit
            FROM customers
            WHERE phone = ? AND is_active = 1
        ''', (phone,))
        customer = cursor.fetchone()
        conn.close()
        
        if customer:
            return jsonify({'success': True, 'customer': dict_from_row(customer)})
        else:
            return jsonify({'success': False, 'error': 'العميل غير موجود'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/customers', methods=['POST'])
def add_customer():
    """إضافة عميل جديد"""
    try:
        data = request.json
        
        # التحقق من البيانات المطلوبة
        if not data.get('name') or not data.get('phone'):
            return jsonify({'success': False, 'error': 'الاسم ورقم الهاتف مطلوبان'}), 400
        
        conn = get_db()
        cursor = conn.cursor()
        
        # التحقق من عدم تكرار الهاتف
        cursor.execute('SELECT id FROM customers WHERE phone = ?', (data.get('phone'),))
        if cursor.fetchone():
            conn.close()
            return jsonify({'success': False, 'error': 'رقم الهاتف مستخدم بالفعل'}), 400
        
        cursor.execute('''
            INSERT INTO customers (name, phone, email, points, notes)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            data.get('name'),
            data.get('phone'),
            data.get('email', ''),
            data.get('points', 0),
            data.get('notes', '')
        ))
        
        customer_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'id': customer_id})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/customers/<int:customer_id>', methods=['PUT'])
def update_customer(customer_id):
    """تحديث بيانات عميل"""
    try:
        data = request.json
        
        conn = get_db()
        cursor = conn.cursor()
        
        # التحقق من وجود العميل
        cursor.execute('SELECT id FROM customers WHERE id = ?', (customer_id,))
        if not cursor.fetchone():
            conn.close()
            return jsonify({'success': False, 'error': 'العميل غير موجود'}), 404
        
        # تحديث البيانات
        cursor.execute('''
            UPDATE customers
            SET name = ?, phone = ?, email = ?, notes = ?
            WHERE id = ?
        ''', (
            data.get('name'),
            data.get('phone'),
            data.get('email', ''),
            data.get('notes', ''),
            customer_id
        ))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/customers/<int:customer_id>', methods=['DELETE'])
def delete_customer(customer_id):
    """حذف (إلغاء تفعيل) عميل"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('UPDATE customers SET is_active = 0 WHERE id = ?', (customer_id,))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/customers/<int:customer_id>/points/adjust', methods=['POST'])
def adjust_customer_points(customer_id):
    """تعديل نقاط العميل يدوياً"""
    try:
        data = request.json
        points = data.get('points', 0)
        reason = data.get('reason', 'تعديل يدوي')
        
        conn = get_db()
        cursor = conn.cursor()
        
        # تحديث النقاط
        cursor.execute('''
            UPDATE customers
            SET points = points + ?
            WHERE id = ?
        ''', (points, customer_id))
        
        # تسجيل في تاريخ النقاط
        cursor.execute('''
            INSERT INTO loyalty_transactions (customer_id, points, type, description)
            VALUES (?, ?, 'adjusted', ?)
        ''', (customer_id, points, reason))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/loyalty/stats', methods=['GET'])
def get_loyalty_stats():
    """إحصائيات نظام الولاء"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # إجمالي العملاء
        cursor.execute('SELECT COUNT(*) as total FROM customers WHERE is_active = 1')
        total_customers = cursor.fetchone()[0]
        
        # إجمالي النقاط الموزعة
        cursor.execute('SELECT SUM(points) as total FROM customers WHERE is_active = 1')
        total_points = cursor.fetchone()[0] or 0
        
        # إجمالي المبيعات للعملاء
        cursor.execute('SELECT SUM(total_spent) as total FROM customers WHERE is_active = 1')
        total_sales = cursor.fetchone()[0] or 0
        
        # أفضل 10 عملاء
        cursor.execute('''
            SELECT name, phone, points, total_spent
            FROM customers
            WHERE is_active = 1
            ORDER BY total_spent DESC
            LIMIT 10
        ''')
        top_customers = [dict_from_row(row) for row in cursor.fetchall()]
        
        conn.close()
        
        return jsonify({
            'success': True,
            'stats': {
                'total_customers': total_customers,
                'total_points': total_points,
                'total_sales': total_sales,
                'top_customers': top_customers
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ===== تشغيل الخادم =====

if __name__ == '__main__':
    print("🚀 تشغيل خادم POS...")
    print("📍 العنوان: http://0.0.0.0:5000")
    print("💡 يمكنك الوصول من أي جهاز على الشبكة المحلية")
    print("⏹️  لإيقاف الخادم: اضغط Ctrl+C")
    
    app.run(host='0.0.0.0', port=5000, debug=False)

# ===============================================
# 🔄 APIs نظام المسترجع (Returns System)
# ===============================================

@app.route('/api/returns', methods=['GET'])
def get_returns():
    """جلب جميع المرتجعات"""
    try:
        branch_id = request.args.get('branch_id')
        status = request.args.get('status')
        
        conn = get_db()
        cursor = conn.cursor()
        
        query = '''
            SELECT r.*, i.invoice_number, c.name as customer_name, u.full_name as processed_by_name
            FROM returns r
            LEFT JOIN invoices i ON r.invoice_id = i.id
            LEFT JOIN customers c ON r.customer_id = c.id
            LEFT JOIN users u ON r.processed_by = u.id
            WHERE 1=1
        '''
        params = []
        
        if status:
            query += ' AND r.status = ?'
            params.append(status)
        
        query += ' ORDER BY r.return_date DESC'
        
        cursor.execute(query, params)
        returns = [dict_from_row(row) for row in cursor.fetchall()]
        conn.close()
        
        return jsonify({'success': True, 'returns': returns})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/returns/<int:return_id>', methods=['GET'])
def get_return(return_id):
    """جلب تفاصيل مرتجع"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT r.*, i.invoice_number, c.name as customer_name, c.phone as customer_phone
            FROM returns r
            LEFT JOIN invoices i ON r.invoice_id = i.id
            LEFT JOIN customers c ON r.customer_id = c.id
            WHERE r.id = ?
        ''', (return_id,))
        
        return_data = cursor.fetchone()
        if not return_data:
            conn.close()
            return jsonify({'success': False, 'error': 'المرتجع غير موجود'}), 404
        
        return_dict = dict_from_row(return_data)
        
        # جلب العناصر
        cursor.execute('''
            SELECT * FROM return_items WHERE return_id = ?
        ''', (return_id,))
        items = [dict_from_row(row) for row in cursor.fetchall()]
        return_dict['items'] = items
        
        conn.close()
        return jsonify({'success': True, 'return': return_dict})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/returns', methods=['POST'])
def create_return():
    """إنشاء مرتجع جديد"""
    try:
        data = request.json
        conn = get_db()
        cursor = conn.cursor()
        
        # إدراج المرتجع
        cursor.execute('''
            INSERT INTO returns 
            (invoice_id, customer_id, total_amount, refund_method, reason, status, processed_by, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data.get('invoice_id'),
            data.get('customer_id'),
            data.get('total_amount', 0),
            data.get('refund_method', 'cash'),
            data.get('reason', ''),
            data.get('status', 'pending'),
            data.get('processed_by'),
            data.get('notes', '')
        ))
        
        return_id = cursor.lastrowid
        
        # إدراج العناصر المرتجعة
        for item in data.get('items', []):
            cursor.execute('''
                INSERT INTO return_items 
                (return_id, product_id, product_name, quantity, unit_price, total)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                return_id,
                item.get('product_id'),
                item.get('product_name'),
                item.get('quantity'),
                item.get('unit_price'),
                item.get('total')
            ))
            
            # إرجاع المخزون (إذا كان معتمد)
            if data.get('status') == 'approved':
                cursor.execute('''
                    UPDATE branch_stock 
                    SET stock = stock + ?
                    WHERE product_id = ?
                ''', (item.get('quantity'), item.get('product_id')))
        
        # خصم من نقاط الولاء (إذا كان معتمد وهناك عميل)
        if data.get('status') == 'approved' and data.get('customer_id'):
            points_to_deduct = int(data.get('total_amount', 0))
            cursor.execute('''
                UPDATE customers 
                SET points = MAX(0, points - ?),
                    total_spent = MAX(0, total_spent - ?)
                WHERE id = ?
            ''', (points_to_deduct, data.get('total_amount', 0), data.get('customer_id')))
            
            # تسجيل في تاريخ النقاط
            cursor.execute('''
                INSERT INTO loyalty_transactions (customer_id, points, type, description)
                VALUES (?, ?, 'adjusted', ?)
            ''', (data.get('customer_id'), -points_to_deduct, f'خصم نقاط - مرتجع #{return_id}'))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'id': return_id})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/returns/<int:return_id>/approve', methods=['POST'])
def approve_return(return_id):
    """اعتماد مرتجع"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # الحصول على بيانات المرتجع
        cursor.execute('SELECT * FROM returns WHERE id = ?', (return_id,))
        return_data = cursor.fetchone()
        
        if not return_data:
            conn.close()
            return jsonify({'success': False, 'error': 'المرتجع غير موجود'}), 404
        
        return_dict = dict_from_row(return_data)
        
        # تحديث الحالة
        cursor.execute('''
            UPDATE returns SET status = 'approved' WHERE id = ?
        ''', (return_id,))
        
        # إرجاع المخزون
        cursor.execute('SELECT * FROM return_items WHERE return_id = ?', (return_id,))
        items = cursor.fetchall()
        
        for item in items:
            item_dict = dict_from_row(item)
            cursor.execute('''
                UPDATE branch_stock 
                SET stock = stock + ?
                WHERE product_id = ?
            ''', (item_dict['quantity'], item_dict['product_id']))
        
        # خصم النقاط
        if return_dict['customer_id']:
            points_to_deduct = int(return_dict['total_amount'])
            cursor.execute('''
                UPDATE customers 
                SET points = MAX(0, points - ?),
                    total_spent = MAX(0, total_spent - ?)
                WHERE id = ?
            ''', (points_to_deduct, return_dict['total_amount'], return_dict['customer_id']))
            
            cursor.execute('''
                INSERT INTO loyalty_transactions (customer_id, points, type, description)
                VALUES (?, ?, 'adjusted', ?)
            ''', (return_dict['customer_id'], -points_to_deduct, f'خصم نقاط - مرتجع #{return_id}'))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/returns/<int:return_id>/reject', methods=['POST'])
def reject_return(return_id):
    """رفض مرتجع"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE returns SET status = 'rejected' WHERE id = ?
        ''', (return_id,))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ===============================================
# 📦 APIs حالات الطلب (Order Status)
# ===============================================

@app.route('/api/invoices/<int:invoice_id>/status', methods=['PUT'])
def update_order_status(invoice_id):
    """تحديث حالة الطلب"""
    try:
        data = request.json
        new_status = data.get('status')
        changed_by = data.get('changed_by')
        notes = data.get('notes', '')
        
        conn = get_db()
        cursor = conn.cursor()
        
        # الحصول على الحالة القديمة
        cursor.execute('SELECT order_status FROM invoices WHERE id = ?', (invoice_id,))
        result = cursor.fetchone()
        old_status = result[0] if result else None
        
        # تحديث الحالة
        cursor.execute('''
            UPDATE invoices SET order_status = ? WHERE id = ?
        ''', (new_status, invoice_id))
        
        # تسجيل في التاريخ
        cursor.execute('''
            INSERT INTO order_status_history (invoice_id, old_status, new_status, changed_by, notes)
            VALUES (?, ?, ?, ?, ?)
        ''', (invoice_id, old_status, new_status, changed_by, notes))
        
        # تحديث actual_delivery إذا كانت الحالة delivered
        if new_status == 'delivered':
            cursor.execute('''
                UPDATE invoices SET actual_delivery = CURRENT_TIMESTAMP WHERE id = ?
            ''', (invoice_id,))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/orders/by-status', methods=['GET'])
def get_orders_by_status():
    """جلب الطلبات حسب الحالة"""
    try:
        status = request.args.get('status')
        branch_id = request.args.get('branch_id')
        
        conn = get_db()
        cursor = conn.cursor()
        
        query = '''
            SELECT id, invoice_number, customer_name, total, order_status, date
            FROM invoices
            WHERE 1=1
        '''
        params = []
        
        if status:
            query += ' AND order_status = ?'
            params.append(status)
        
        if branch_id:
            query += ' AND branch_id = ?'
            params.append(branch_id)
        
        query += ' ORDER BY date DESC'
        
        cursor.execute(query, params)
        orders = [dict_from_row(row) for row in cursor.fetchall()]
        conn.close()
        
        return jsonify({'success': True, 'orders': orders})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ===============================================
# 🏭 APIs نظام الموردين (Suppliers System)
# ===============================================

@app.route('/api/suppliers', methods=['GET'])
def get_suppliers():
    """جلب جميع الموردين"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM suppliers WHERE is_active = 1 ORDER BY name
        ''')
        suppliers = [dict_from_row(row) for row in cursor.fetchall()]
        conn.close()
        return jsonify({'success': True, 'suppliers': suppliers})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/suppliers', methods=['POST'])
def add_supplier():
    """إضافة مورد جديد"""
    try:
        data = request.json
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO suppliers (name, company, phone, email, address, tax_number, payment_terms, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data.get('name'),
            data.get('company', ''),
            data.get('phone', ''),
            data.get('email', ''),
            data.get('address', ''),
            data.get('tax_number', ''),
            data.get('payment_terms', ''),
            data.get('notes', '')
        ))
        
        supplier_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'id': supplier_id})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/suppliers/<int:supplier_id>', methods=['PUT'])
def update_supplier(supplier_id):
    """تحديث مورد"""
    try:
        data = request.json
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE suppliers
            SET name = ?, company = ?, phone = ?, email = ?, 
                address = ?, tax_number = ?, payment_terms = ?, notes = ?
            WHERE id = ?
        ''', (
            data.get('name'),
            data.get('company', ''),
            data.get('phone', ''),
            data.get('email', ''),
            data.get('address', ''),
            data.get('tax_number', ''),
            data.get('payment_terms', ''),
            data.get('notes', ''),
            supplier_id
        ))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/purchase-orders', methods=['POST'])
def create_purchase_order():
    """إنشاء طلب شراء"""
    try:
        data = request.json
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO purchase_orders 
            (supplier_id, order_number, expected_date, total_amount, tax_amount, 
             discount, final_amount, notes, created_by, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data.get('supplier_id'),
            data.get('order_number'),
            data.get('expected_date'),
            data.get('total_amount', 0),
            data.get('tax_amount', 0),
            data.get('discount', 0),
            data.get('final_amount', 0),
            data.get('notes', ''),
            data.get('created_by'),
            data.get('status', 'draft')
        ))
        
        po_id = cursor.lastrowid
        
        # إضافة العناصر
        for item in data.get('items', []):
            cursor.execute('''
                INSERT INTO purchase_order_items 
                (purchase_order_id, product_id, product_name, quantity, unit_cost, total)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                po_id,
                item.get('product_id'),
                item.get('product_name'),
                item.get('quantity'),
                item.get('unit_cost'),
                item.get('total')
            ))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'id': po_id})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ===============================================
# 🎟️ APIs نظام الكوبونات (Coupons System)
# ===============================================

@app.route('/api/coupons', methods=['GET'])
def get_coupons():
    """جلب جميع الكوبونات"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM coupons ORDER BY created_at DESC
        ''')
        coupons = [dict_from_row(row) for row in cursor.fetchall()]
        conn.close()
        return jsonify({'success': True, 'coupons': coupons})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/coupons/validate', methods=['POST'])
def validate_coupon():
    """التحقق من صلاحية كوبون"""
    try:
        data = request.json
        code = data.get('code')
        customer_id = data.get('customer_id')
        total = data.get('total', 0)
        
        conn = get_db()
        cursor = conn.cursor()
        
        # جلب الكوبون
        cursor.execute('''
            SELECT * FROM coupons WHERE code = ? AND status = 'active'
        ''', (code,))
        coupon = cursor.fetchone()
        
        if not coupon:
            conn.close()
            return jsonify({'success': False, 'error': 'الكوبون غير صالح'}), 400
        
        coupon_dict = dict_from_row(coupon)
        
        # التحقق من التواريخ
        now = datetime.now()
        if coupon_dict.get('start_date') and datetime.fromisoformat(coupon_dict['start_date']) > now:
            conn.close()
            return jsonify({'success': False, 'error': 'الكوبون لم يبدأ بعد'}), 400
        
        if coupon_dict.get('end_date') and datetime.fromisoformat(coupon_dict['end_date']) < now:
            conn.close()
            return jsonify({'success': False, 'error': 'الكوبون منتهي الصلاحية'}), 400
        
        # التحقق من حد الاستخدام
        if coupon_dict.get('usage_limit') and coupon_dict['usage_count'] >= coupon_dict['usage_limit']:
            conn.close()
            return jsonify({'success': False, 'error': 'تم استخدام الكوبون بالكامل'}), 400
        
        # التحقق من الحد الأدنى للشراء
        if coupon_dict.get('min_purchase', 0) > total:
            conn.close()
            return jsonify({'success': False, 'error': f'الحد الأدنى للشراء {coupon_dict["min_purchase"]} د.ك'}), 400
        
        # حساب الخصم
        if coupon_dict['discount_type'] == 'percentage':
            discount = total * (coupon_dict['discount_value'] / 100)
            if coupon_dict.get('max_discount'):
                discount = min(discount, coupon_dict['max_discount'])
        else:
            discount = coupon_dict['discount_value']
        
        discount = min(discount, total)
        
        conn.close()
        return jsonify({
            'success': True,
            'coupon': coupon_dict,
            'discount': discount
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/coupons', methods=['POST'])
def create_coupon():
    """إنشاء كوبون جديد"""
    try:
        data = request.json
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO coupons 
            (code, name, description, discount_type, discount_value, min_purchase,
             max_discount, usage_limit, per_customer_limit, start_date, end_date,
             status, applicable_to, applicable_ids, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data.get('code'),
            data.get('name', ''),
            data.get('description', ''),
            data.get('discount_type'),
            data.get('discount_value'),
            data.get('min_purchase', 0),
            data.get('max_discount'),
            data.get('usage_limit'),
            data.get('per_customer_limit', 1),
            data.get('start_date'),
            data.get('end_date'),
            data.get('status', 'active'),
            data.get('applicable_to', 'all'),
            data.get('applicable_ids'),
            data.get('created_by')
        ))
        
        coupon_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'id': coupon_id})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/coupons/<int:coupon_id>/use', methods={'POST'})
def use_coupon(coupon_id):
    """تسجيل استخدام كوبون"""
    try:
        data = request.json
        conn = get_db()
        cursor = conn.cursor()
        
        # تحديث عدد الاستخدامات
        cursor.execute('''
            UPDATE coupons SET usage_count = usage_count + 1 WHERE id = ?
        ''', (coupon_id,))
        
        # تسجيل الاستخدام
        cursor.execute('''
            INSERT INTO coupon_usage (coupon_id, customer_id, invoice_id, discount_amount)
            VALUES (?, ?, ?, ?)
        ''', (
            coupon_id,
            data.get('customer_id'),
            data.get('invoice_id'),
            data.get('discount_amount')
        ))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ===============================================
# ➕ APIs العمليات الإضافية
# ===============================================

@app.route('/api/operation-templates', methods=['GET'])
def get_operation_templates():
    """جلب قوالب العمليات"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM operation_templates WHERE is_active = 1 ORDER BY name
        ''')
        templates = [dict_from_row(row) for row in cursor.fetchall()]
        conn.close()
        return jsonify({'success': True, 'templates': templates})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/operation-templates', methods=['POST'])
def add_operation_template():
    """إضافة قالب عملية"""
    try:
        data = request.json
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO operation_templates (name, amount, taxable)
            VALUES (?, ?, ?)
        ''', (
            data.get('name'),
            data.get('amount', 0),
            data.get('taxable', 0)
        ))
        
        template_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'id': template_id})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ===============================================
# 🔐 API التحقق من الاتصال
# ===============================================

@app.route('/api/ping', methods=['GET'])
def ping():
    """التحقق من اتصال الخادم"""
    return jsonify({'success': True, 'message': 'Server is online'})


# ===== تشغيل الخادم =====

if __name__ == '__main__':
    print("🚀 تشغيل خادم POS...")
    print("📍 العنوان: http://0.0.0.0:5000")
    print("💡 يمكنك الوصول من أي جهاز على الشبكة المحلية")
    print("⏹️  لإيقاف الخادم: اضغط Ctrl+C")
    
    app.run(host='0.0.0.0', port=5000, debug=False)
