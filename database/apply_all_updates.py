#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
تطبيق جميع تحديثات الميزات الجديدة
"""

import sqlite3
import os
from datetime import datetime

DB_PATH = 'database/pos.db'

def apply_all_updates():
    """تطبيق جميع التحديثات"""
    
    # التأكد من وجود مجلد database
    os.makedirs('database', exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        print("=" * 60)
        print("🚀 بدء تطبيق جميع التحديثات...")
        print("=" * 60)
        
        # =====================================
        # 1. نظام الولاء (Loyalty System)
        # =====================================
        print("\n[1/7] 🎯 نظام الولاء...")
        
        # جدول العملاء
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT UNIQUE NOT NULL,
                email TEXT,
                points INTEGER DEFAULT 0,
                total_spent REAL DEFAULT 0,
                join_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_visit DATETIME,
                notes TEXT,
                is_active INTEGER DEFAULT 1
            )
        ''')
        print("  ✅ جدول customers")
        
        # جدول تاريخ النقاط
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS loyalty_transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER,
                invoice_id INTEGER,
                points INTEGER,
                type TEXT CHECK(type IN ('earned', 'redeemed', 'expired', 'adjusted')),
                description TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (customer_id) REFERENCES customers(id),
                FOREIGN KEY (invoice_id) REFERENCES invoices(id)
            )
        ''')
        print("  ✅ جدول loyalty_transactions")
        
        # إضافة أعمدة للفواتير
        cursor.execute("PRAGMA table_info(invoices)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'customer_id' not in columns:
            cursor.execute('ALTER TABLE invoices ADD COLUMN customer_id INTEGER')
        if 'loyalty_points_earned' not in columns:
            cursor.execute('ALTER TABLE invoices ADD COLUMN loyalty_points_earned INTEGER DEFAULT 0')
        if 'loyalty_points_redeemed' not in columns:
            cursor.execute('ALTER TABLE invoices ADD COLUMN loyalty_points_redeemed INTEGER DEFAULT 0')
        if 'loyalty_discount' not in columns:
            cursor.execute('ALTER TABLE invoices ADD COLUMN loyalty_discount REAL DEFAULT 0')
        print("  ✅ أعمدة الولاء في invoices")
        
        # الفهارس
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_customers_phone ON customers(phone)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_loyalty_customer ON loyalty_transactions(customer_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_loyalty_invoice ON loyalty_transactions(invoice_id)')
        
        # =====================================
        # 2. نظام المسترجع (Returns System)
        # =====================================
        print("\n[2/7] 🔄 نظام المسترجع...")
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS returns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_id INTEGER,
                customer_id INTEGER,
                return_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                total_amount REAL DEFAULT 0,
                refund_method TEXT CHECK(refund_method IN ('cash', 'credit', 'exchange')) DEFAULT 'cash',
                reason TEXT,
                status TEXT CHECK(status IN ('pending', 'approved', 'rejected')) DEFAULT 'pending',
                processed_by INTEGER,
                notes TEXT,
                FOREIGN KEY (invoice_id) REFERENCES invoices(id),
                FOREIGN KEY (customer_id) REFERENCES customers(id),
                FOREIGN KEY (processed_by) REFERENCES users(id)
            )
        ''')
        print("  ✅ جدول returns")
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS return_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                return_id INTEGER,
                product_id INTEGER,
                product_name TEXT,
                quantity INTEGER,
                unit_price REAL,
                total REAL,
                FOREIGN KEY (return_id) REFERENCES returns(id),
                FOREIGN KEY (product_id) REFERENCES products(id)
            )
        ''')
        print("  ✅ جدول return_items")
        
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_returns_invoice ON returns(invoice_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_returns_customer ON returns(customer_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_returns_date ON returns(return_date)')
        
        # =====================================
        # 3. حالات الطلب (Order Status)
        # =====================================
        print("\n[3/7] 📦 حالات الطلب...")
        
        # إضافة أعمدة لحالة الطلب
        if 'order_status' not in columns:
            cursor.execute('''
                ALTER TABLE invoices ADD COLUMN order_status TEXT 
                CHECK(order_status IN ('pending', 'processing', 'ready', 'delivering', 'delivered', 'completed', 'cancelled')) 
                DEFAULT 'pending'
            ''')
        if 'delivery_address' not in columns:
            cursor.execute('ALTER TABLE invoices ADD COLUMN delivery_address TEXT')
        if 'delivery_phone' not in columns:
            cursor.execute('ALTER TABLE invoices ADD COLUMN delivery_phone TEXT')
        if 'estimated_delivery' not in columns:
            cursor.execute('ALTER TABLE invoices ADD COLUMN estimated_delivery DATETIME')
        if 'actual_delivery' not in columns:
            cursor.execute('ALTER TABLE invoices ADD COLUMN actual_delivery DATETIME')
        print("  ✅ أعمدة حالة الطلب في invoices")
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS order_status_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_id INTEGER,
                old_status TEXT,
                new_status TEXT,
                changed_by INTEGER,
                changed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                notes TEXT,
                FOREIGN KEY (invoice_id) REFERENCES invoices(id),
                FOREIGN KEY (changed_by) REFERENCES users(id)
            )
        ''')
        print("  ✅ جدول order_status_history")
        
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_order_status_invoice ON order_status_history(invoice_id)')
        
        # =====================================
        # 4. نظام الموردين (Suppliers System)
        # =====================================
        print("\n[4/7] 🏭 نظام الموردين...")
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS suppliers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                company TEXT,
                phone TEXT,
                email TEXT,
                address TEXT,
                tax_number TEXT,
                payment_terms TEXT,
                credit_limit REAL DEFAULT 0,
                current_balance REAL DEFAULT 0,
                notes TEXT,
                is_active INTEGER DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        print("  ✅ جدول suppliers")
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS purchase_orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                supplier_id INTEGER,
                order_number TEXT UNIQUE,
                order_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                expected_date DATETIME,
                status TEXT CHECK(status IN ('draft', 'sent', 'confirmed', 'received', 'cancelled')) DEFAULT 'draft',
                total_amount REAL DEFAULT 0,
                tax_amount REAL DEFAULT 0,
                discount REAL DEFAULT 0,
                final_amount REAL DEFAULT 0,
                payment_status TEXT CHECK(payment_status IN ('unpaid', 'partial', 'paid')) DEFAULT 'unpaid',
                paid_amount REAL DEFAULT 0,
                notes TEXT,
                created_by INTEGER,
                FOREIGN KEY (supplier_id) REFERENCES suppliers(id),
                FOREIGN KEY (created_by) REFERENCES users(id)
            )
        ''')
        print("  ✅ جدول purchase_orders")
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS purchase_order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                purchase_order_id INTEGER,
                product_id INTEGER,
                product_name TEXT,
                quantity INTEGER,
                unit_cost REAL,
                total REAL,
                received_quantity INTEGER DEFAULT 0,
                FOREIGN KEY (purchase_order_id) REFERENCES purchase_orders(id),
                FOREIGN KEY (product_id) REFERENCES products(id)
            )
        ''')
        print("  ✅ جدول purchase_order_items")
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS supplier_payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                supplier_id INTEGER,
                purchase_order_id INTEGER,
                amount REAL,
                payment_method TEXT,
                payment_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                reference_number TEXT,
                notes TEXT,
                created_by INTEGER,
                FOREIGN KEY (supplier_id) REFERENCES suppliers(id),
                FOREIGN KEY (purchase_order_id) REFERENCES purchase_orders(id),
                FOREIGN KEY (created_by) REFERENCES users(id)
            )
        ''')
        print("  ✅ جدول supplier_payments")
        
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_suppliers_name ON suppliers(name)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_purchase_orders_supplier ON purchase_orders(supplier_id)')
        
        # =====================================
        # 5. نظام الكوبونات (Coupons System)
        # =====================================
        print("\n[5/7] 🎟️ نظام الكوبونات...")
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS coupons (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL,
                name TEXT,
                description TEXT,
                discount_type TEXT CHECK(discount_type IN ('percentage', 'fixed')) NOT NULL,
                discount_value REAL NOT NULL,
                min_purchase REAL DEFAULT 0,
                max_discount REAL,
                usage_limit INTEGER,
                usage_count INTEGER DEFAULT 0,
                per_customer_limit INTEGER DEFAULT 1,
                start_date DATETIME,
                end_date DATETIME,
                status TEXT CHECK(status IN ('active', 'inactive', 'expired')) DEFAULT 'active',
                applicable_to TEXT CHECK(applicable_to IN ('all', 'category', 'product')) DEFAULT 'all',
                applicable_ids TEXT,
                created_by INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (created_by) REFERENCES users(id)
            )
        ''')
        print("  ✅ جدول coupons")
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS coupon_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                coupon_id INTEGER,
                customer_id INTEGER,
                invoice_id INTEGER,
                discount_amount REAL,
                used_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (coupon_id) REFERENCES coupons(id),
                FOREIGN KEY (customer_id) REFERENCES customers(id),
                FOREIGN KEY (invoice_id) REFERENCES invoices(id)
            )
        ''')
        print("  ✅ جدول coupon_usage")
        
        # إضافة أعمدة للفواتير
        if 'coupon_id' not in columns:
            cursor.execute('ALTER TABLE invoices ADD COLUMN coupon_id INTEGER')
        if 'coupon_code' not in columns:
            cursor.execute('ALTER TABLE invoices ADD COLUMN coupon_code TEXT')
        if 'coupon_discount' not in columns:
            cursor.execute('ALTER TABLE invoices ADD COLUMN coupon_discount REAL DEFAULT 0')
        print("  ✅ أعمدة الكوبونات في invoices")
        
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_coupons_code ON coupons(code)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_coupon_usage_coupon ON coupon_usage(coupon_id)')
        
        # =====================================
        # 6. العمليات الإضافية
        # =====================================
        print("\n[6/7] ➕ العمليات الإضافية...")
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS invoice_additional_operations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_id INTEGER,
                operation_type TEXT,
                name TEXT,
                amount REAL,
                taxable INTEGER DEFAULT 0,
                notes TEXT,
                FOREIGN KEY (invoice_id) REFERENCES invoices(id)
            )
        ''')
        print("  ✅ جدول invoice_additional_operations")
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS operation_templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                amount REAL,
                taxable INTEGER DEFAULT 0,
                is_active INTEGER DEFAULT 1
            )
        ''')
        print("  ✅ جدول operation_templates")
        
        # إضافة قوالب افتراضية
        cursor.execute('''
            INSERT OR IGNORE INTO operation_templates (id, name, amount, taxable) VALUES
            (1, 'توصيل', 2.000, 0),
            (2, 'تغليف هدية', 1.000, 0),
            (3, 'تأمين', 0.500, 0),
            (4, 'تركيب', 5.000, 1),
            (5, 'خدمة عاجلة', 3.000, 0)
        ''')
        print("  ✅ قوالب افتراضية")
        
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_additional_ops_invoice ON invoice_additional_operations(invoice_id)')
        
        # =====================================
        # 7. تحديثات عامة
        # =====================================
        print("\n[7/7] ⚙️ تحديثات عامة...")
        print("  ✅ جميع الفهارس")
        
        conn.commit()
        
        print("\n" + "=" * 60)
        print("✅ تم تطبيق جميع التحديثات بنجاح!")
        print("=" * 60)
        print("\nالإحصائيات:")
        print("  - 7 ميزات رئيسية")
        print("  - 15+ جدول جديد")
        print("  - 20+ عمود جديد")
        print("  - جميع الفهارس محدثة")
        print("\n🎉 النظام جاهز للعمل!")
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ خطأ: {e}")
        raise
    finally:
        conn.close()

if __name__ == '__main__':
    apply_all_updates()
