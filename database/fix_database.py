#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
إصلاح قاعدة البيانات - إضافة الأعمدة الناقصة
"""

import sqlite3
import os

DB_PATH = 'database/pos.db'

def fix_database():
    """إصلاح قاعدة البيانات وإضافة الأعمدة الناقصة"""
    
    if not os.path.exists(DB_PATH):
        print(f"❌ خطأ: قاعدة البيانات غير موجودة: {DB_PATH}")
        return False
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        print("=" * 60)
        print("🔧 بدء إصلاح قاعدة البيانات...")
        print("=" * 60)
        
        # الحصول على الأعمدة الحالية
        cursor.execute("PRAGMA table_info(invoices)")
        existing_columns = [row[1] for row in cursor.fetchall()]
        print(f"\n📋 الأعمدة الموجودة حالياً في جدول invoices: {len(existing_columns)}")
        
        # قائمة الأعمدة المطلوبة
        required_columns = {
            'customer_id': 'INTEGER',
            'loyalty_points_earned': 'INTEGER DEFAULT 0',
            'loyalty_points_redeemed': 'INTEGER DEFAULT 0',
            'loyalty_discount': 'REAL DEFAULT 0',
            'has_return': 'INTEGER DEFAULT 0',
            'return_amount': 'REAL DEFAULT 0',
            'order_status': "TEXT DEFAULT 'pending'",
            'delivery_address': 'TEXT',
            'delivery_phone': 'TEXT',
            'estimated_delivery': 'DATETIME',
            'actual_delivery': 'DATETIME',
            'coupon_id': 'INTEGER',
            'coupon_code': 'TEXT',
            'coupon_discount': 'REAL DEFAULT 0'
        }
        
        # إضافة الأعمدة الناقصة
        added_count = 0
        for column_name, column_type in required_columns.items():
            if column_name not in existing_columns:
                try:
                    sql = f'ALTER TABLE invoices ADD COLUMN {column_name} {column_type}'
                    cursor.execute(sql)
                    print(f"  ✅ تم إضافة العمود: {column_name}")
                    added_count += 1
                except sqlite3.OperationalError as e:
                    if "duplicate column name" in str(e).lower():
                        print(f"  ⚠️  العمود موجود: {column_name}")
                    else:
                        print(f"  ❌ خطأ في إضافة {column_name}: {e}")
            else:
                print(f"  ⚠️  العمود موجود: {column_name}")
        
        print(f"\n📊 تم إضافة {added_count} عمود جديد")
        
        # إنشاء الجداول الجديدة
        print("\n🗂️  إنشاء الجداول الجديدة...")
        
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
        
        # جدول المرتجعات
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
        
        # جدول تفاصيل المرتجعات
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
        
        # جدول تاريخ حالات الطلب
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
        
        # جدول الموردين
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
        
        # جدول طلبات الشراء
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
        
        # جدول تفاصيل طلب الشراء
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
        
        # جدول مدفوعات الموردين
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
        
        # جدول الكوبونات
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
        
        # جدول استخدام الكوبونات
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
        
        # جدول العمليات الإضافية
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
        
        # جدول قوالب العمليات
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
        cursor.execute("SELECT COUNT(*) FROM operation_templates")
        if cursor.fetchone()[0] == 0:
            cursor.executemany('''
                INSERT INTO operation_templates (id, name, amount, taxable) VALUES (?, ?, ?, ?)
            ''', [
                (1, 'توصيل', 2.000, 0),
                (2, 'تغليف هدية', 1.000, 0),
                (3, 'تأمين', 0.500, 0),
                (4, 'تركيب', 5.000, 1),
                (5, 'خدمة عاجلة', 3.000, 0)
            ])
            print("  ✅ قوالب العمليات الافتراضية")
        
        # إنشاء الفهارس
        print("\n📊 إنشاء الفهارس...")
        indexes = [
            'CREATE INDEX IF NOT EXISTS idx_customers_phone ON customers(phone)',
            'CREATE INDEX IF NOT EXISTS idx_loyalty_customer ON loyalty_transactions(customer_id)',
            'CREATE INDEX IF NOT EXISTS idx_loyalty_invoice ON loyalty_transactions(invoice_id)',
            'CREATE INDEX IF NOT EXISTS idx_returns_invoice ON returns(invoice_id)',
            'CREATE INDEX IF NOT EXISTS idx_returns_customer ON returns(customer_id)',
            'CREATE INDEX IF NOT EXISTS idx_return_items_return ON return_items(return_id)',
            'CREATE INDEX IF NOT EXISTS idx_order_status_invoice ON order_status_history(invoice_id)',
            'CREATE INDEX IF NOT EXISTS idx_suppliers_name ON suppliers(name)',
            'CREATE INDEX IF NOT EXISTS idx_purchase_orders_supplier ON purchase_orders(supplier_id)',
            'CREATE INDEX IF NOT EXISTS idx_coupons_code ON coupons(code)',
            'CREATE INDEX IF NOT EXISTS idx_coupon_usage_coupon ON coupon_usage(coupon_id)',
            'CREATE INDEX IF NOT EXISTS idx_additional_ops_invoice ON invoice_additional_operations(invoice_id)'
        ]
        
        for idx_sql in indexes:
            cursor.execute(idx_sql)
        print("  ✅ تم إنشاء جميع الفهارس")
        
        conn.commit()
        
        # التحقق النهائي
        print("\n🔍 التحقق النهائي...")
        cursor.execute("PRAGMA table_info(invoices)")
        final_columns = [row[1] for row in cursor.fetchall()]
        
        missing = []
        for col in required_columns.keys():
            if col not in final_columns:
                missing.append(col)
        
        if missing:
            print(f"\n⚠️  تحذير: أعمدة ناقصة: {missing}")
            return False
        else:
            print("\n✅ جميع الأعمدة موجودة!")
        
        print("\n" + "=" * 60)
        print("✅ تم إصلاح قاعدة البيانات بنجاح!")
        print("=" * 60)
        print("\n📊 الإحصائيات:")
        print(f"  - أعمدة جديدة: {added_count}")
        print(f"  - جداول جديدة: 13")
        print(f"  - فهارس جديدة: 12")
        print("\n🎉 النظام جاهز للعمل!")
        
        return True
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ خطأ: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        conn.close()

if __name__ == '__main__':
    success = fix_database()
    if not success:
        print("\n⚠️  فشل الإصلاح! تحقق من الأخطاء أعلاه")
        exit(1)
