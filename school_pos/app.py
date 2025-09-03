from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash 
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import json
import sqlite3
import os

print("Template folder exists:", os.path.exists("templates/index.html"))

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'

# สร้างฐานข้อมูล
def init_db():
    conn = sqlite3.connect('school_pos.db')
    cursor = conn.cursor()
    
    # ตาราง students
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS students (
            student_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            balance REAL DEFAULT 0
        )
    ''')
    
    # ตาราง admins
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS admins (
            admin_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            name TEXT NOT NULL
        )
    ''')
        
    # ตาราง shops
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS shops (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            shop_name TEXT UNIQUE,
            owner_name TEXT,
            password_hash TEXT,
            image_url TEXT
        )
    ''')
    
    # ตาราง menu_items
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS menu_items (
    item_id INTEGER PRIMARY KEY AUTOINCREMENT,
    shop_id INTEGER,
    name TEXT,
    price REAL,
    cost REAL,
    available BOOLEAN,
    image_url TEXT,
    category TEXT,
    UNIQUE(shop_id, name),
    FOREIGN KEY (shop_id) REFERENCES shops(shop_id)
)
''')

    
    # ตาราง orders
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            shop_id INTEGER,
            total_price REAL,
            order_status TEXT CHECK(order_status IN ('pending', 'completed', 'cancelled')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(shop_id) REFERENCES shops(id)
        )
    ''')
    
    # ตาราง order_items
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER,
            menu_id INTEGER,
            quantity INTEGER,
            FOREIGN KEY(order_id) REFERENCES orders(id),
            FOREIGN KEY(menu_id) REFERENCES menus(id)
        )
    ''')
    
    # เพิ่มข้อมูลตัวอย่าง
    insert_sample_data(cursor)
    
    conn.commit()
    conn.close()

def insert_sample_data(cursor):
    # ตัวอย่างนักเรียน
    cursor.execute('''
        INSERT OR IGNORE INTO students (student_id, name, password_hash, balance)
        VALUES (?, ?, ?, ?)
    ''', ('01514', 'สมชาย ใจดี', generate_password_hash('password123'), 500.0))
    
    cursor.execute('''
        INSERT OR IGNORE INTO students (student_id, name, password_hash, balance)
        VALUES (?, ?, ?, ?)
    ''', ('12346', 'สมหญิง สวยงาม', generate_password_hash('password456'), 300.0))
    
    # ตัวอย่างครู / แอดมิน
    admins = [
        ('teacher1', 'pass1234', 'ครูสมศรี')  # username, password, ชื่อ
    ]

    for username, password, name in admins:
        cursor.execute('''
            INSERT OR IGNORE INTO admins (username, password_hash, name)
            VALUES (?, ?, ?)
        ''', (username, generate_password_hash(password), name))
        
    # ตัวอย่างร้านค้า
    shops_data = [
        ('ร้านข้าวแม่สมปอง', 'แม่สมปอง', generate_password_hash('shop123'), '/static/images/rice_shop.jpg'),
        ('ร้านก๋วยเตี๋ยวลุงสมชาย', 'ลุงสมชาย', generate_password_hash('shop456'), '/static/images/noodle_shop.jpg'),
        ('ร้านน้ำผลไม้ป้าแก้ว', 'ป้าแก้ว', generate_password_hash('shop789'), '/static/images/drink_shop.jpg'),
        ('ร้านขนมอรุณี', 'อรุณี', generate_password_hash('shop000'), '/static/images/snack_shop.jpg')
    ]

    for shop_name, owner_name, password_hash, image_url in shops_data:
        cursor.execute('''
            INSERT OR IGNORE INTO shops (shop_name, owner_name, password_hash, image_url)
            VALUES (?, ?, ?, ?)
        ''', (shop_name, owner_name, password_hash, image_url))
    
    # ตัวอย่างเมนู
    menu_items = [
        # ร้านข้าว (shop_id = 1)
        (1, 'ข้าวผัดหมู', 45.0, 25.0, True, '/static/images/fried_rice.jpg', 'ข้าว'),
        (1, 'ข้าวราดแกง', 40.0, 20.0, True, '/static/images/curry_rice.jpg', 'ข้าว'),
        (1, 'ข้าวมันไก่', 50.0, 30.0, True, '/static/images/chicken_rice.jpg', 'ข้าว'),
        
        # ร้านก๋วยเตี๋ยว (shop_id = 2)
        (2, 'ก๋วยเตี๋ยวหมูน้ำใส', 35.0, 18.0, True, '/static/images/clear_soup.jpg', 'ก๋วยเตี๋ยว'),
        (2, 'ก๋วยเตี๋ยวต้มยำ', 40.0, 20.0, True, '/static/images/tomyum_noodle.jpg', 'ก๋วยเตี๋ยว'),
        (2, 'บะหมี่แห้ง', 38.0, 19.0, True, '/static/images/dry_noodle.jpg', 'ก๋วยเตี๋ยว'),
        
        # ร้านน้ำ (shop_id = 3)
        (3, 'น้ำส้มคั้น', 25.0, 10.0, True, '/static/images/orange_juice.jpg', 'เครื่องดื่ม'),
        (3, 'น้ำแตงโม', 20.0, 8.0, True, '/static/images/watermelon_juice.jpg', 'เครื่องดื่ม'),
        (3, 'ชาเย็น', 15.0, 5.0, True, '/static/images/iced_tea.jpg', 'เครื่องดื่ม'),
        
        # ร้านขนม (shop_id = 4)
        (4, 'ขนมปังปิ้ง', 25.0, 12.0, True, '/static/images/toast.jpg', 'ขนม'),
        (4, 'โรตี', 30.0, 15.0, True, '/static/images/roti.jpg', 'ขนม'),
        (4, 'ลูกชิ้นทอด', 20.0, 10.0, True, '/static/images/fried_meatball.jpg', 'ขนม')
    ]
    
    for shop_id, name, price, cost, available, image_url, category in menu_items:
        cursor.execute('''
            INSERT OR IGNORE INTO menu_items (shop_id, name, price, cost, available, image_url, category)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (shop_id, name, price, cost, available, image_url, category))


# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/student_login', methods=['GET', 'POST'])
def student_login():
    if request.method == 'POST':
        student_id = request.form['student_id']
        password = request.form['password']
        
        conn = sqlite3.connect('school_pos.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT name, password_hash, balance FROM students WHERE student_id = ?', (student_id,))
        student = cursor.fetchone()
        conn.close()
        
        if student and check_password_hash(student[1], password):
            session['user_type'] = 'student'
            session['student_id'] = student_id
            session['student_name'] = student[0]
            session['balance'] = student[2]
            return redirect(url_for('student_dashboard'))
        else:
            flash('รหัสนักเรียนหรือรหัสผ่านไม่ถูกต้อง')
    
    return render_template('student_login.html')

@app.route('/shop_login', methods=['GET', 'POST'])
def shop_login():
    if request.method == 'POST':
        shop_name = request.form['shop_name']
        password = request.form['password']
        
        conn = sqlite3.connect('school_pos.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT shop_id, owner_name, password_hash FROM shops WHERE shop_name = ?', (shop_name,))
        shop = cursor.fetchone()
        conn.close()
        
        if shop and check_password_hash(shop[2], password):
            session['user_type'] = 'shop'
            session['shop_id'] = shop[0]
            session['shop_name'] = shop_name
            session['owner_name'] = shop[1]
            return redirect(url_for('shop_dashboard'))
        else:
            flash('ชื่อร้านหรือรหัสผ่านไม่ถูกต้อง')
    
    return render_template('shop_login.html')

@app.route('/student_dashboard')
def student_dashboard():
    if 'user_type' not in session or session['user_type'] != 'student':
        return redirect(url_for('student_login'))
    
    conn = sqlite3.connect('school_pos.db')
    cursor = conn.cursor()
    
    # ดึงข้อมูลร้านค้า
    cursor.execute('SELECT shop_id, shop_name, image_url FROM shops')
    all_shops = cursor.fetchall()
    
    # กรองชื่อร้านซ้ำ
    seen = set()
    shops = []
    for shop_id, shop_name, image_url in all_shops:
        if shop_name not in seen:
            shops.append((shop_id, shop_name, image_url))
            seen.add(shop_name)
    
    conn.close()
    
    return render_template('student_dashboard.html', 
                           student_name=session['student_name'], 
                           balance=session['balance'], 
                           shops=shops)


@app.route('/shop/<int:shop_id>')
def shop_menu(shop_id):
    if 'user_type' not in session or session['user_type'] != 'student':
        return redirect(url_for('student_login'))
    
    conn = sqlite3.connect('school_pos.db')
    cursor = conn.cursor()
    
    # ดึงชื่อร้าน
    cursor.execute('SELECT shop_name FROM shops WHERE shop_id = ?', (shop_id,))
    shop = cursor.fetchone()
    
    # ดึงเมนูพร้อมกรองชื่อซ้ำ
    cursor.execute('''
    SELECT item_id, name, price, available, image_url, category
    FROM menu_items
    WHERE shop_id = ? AND available = 1
    GROUP BY name
''', (shop_id,))
    menu_items = cursor.fetchall()

    conn.close()
    
    return render_template('shop_menu.html', 
                           shop_name=shop[0], 
                           shop_id=shop_id,
                           menu_items=menu_items,
                           balance=session['balance'])

@app.route('/shop_dashboard')
def shop_dashboard():
    if 'user_type' not in session or session['user_type'] != 'shop':
        return redirect(url_for('shop_login'))
    
    conn = sqlite3.connect('school_pos.db')
    cursor = conn.cursor()
    
    # ดึงข้อมูลเมนู
    cursor.execute('''
        SELECT item_id, name, price, cost, available, category
        FROM menu_items 
        WHERE shop_id = ? AND available = 1
        GROUP BY name
    ''', (session['shop_id'],))
    menu_items = cursor.fetchall()
    
    # สถิติการขายวันนี้
    cursor.execute('''
        SELECT COUNT(*) as order_count, IFNULL(SUM(total_amount), 0) as daily_sales
        FROM orders 
        WHERE shop_id = ? AND date(order_date) = date('now')
    ''', (session['shop_id'],))
    daily_stats = cursor.fetchone()
    
    conn.close()
    
    return render_template('shop_dashboard.html', 
                         shop_name=session['shop_name'],
                         owner_name=session['owner_name'],
                         menu_items=menu_items,
                         daily_orders=daily_stats[0],
                         daily_sales=daily_stats[1])

@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    if 'cart' not in session:
        session['cart'] = []
    
    item_data = {
        'item_id': request.json['item_id'],
        'name': request.json['name'],
        'price': request.json['price'],
        'quantity': request.json['quantity'],
        'shop_id': request.json['shop_id']
    }
    
    # ตรวจสอบว่าสินค้าอยู่ในตะกร้าแล้วหรือไม่
    found = False
    for item in session['cart']:
        if item['item_id'] == item_data['item_id']:
            item['quantity'] += item_data['quantity']
            found = True
            break
    
    if not found:
        session['cart'].append(item_data)
    
    session.modified = True
    return jsonify({'success': True, 'cart_count': len(session['cart'])})

@app.route('/cart')
def view_cart():
    if 'user_type' not in session or session['user_type'] != 'student':
        return redirect(url_for('student_login'))
    
    cart = session.get('cart', [])
    total = sum(item['price'] * item['quantity'] for item in cart)
    
    return render_template('cart.html', cart=cart, total=total, balance=session['balance'])

@app.route('/checkout', methods=['POST'])
def checkout():
    if 'user_type' not in session or session['user_type'] != 'student':
        return redirect(url_for('student_login'))
    
    cart = session.get('cart', [])
    if not cart:
        flash('ตะกร้าว่าง')
        return redirect(url_for('student_dashboard'))
    
    total = sum(item['price'] * item['quantity'] for item in cart)
    
    if session['balance'] < total:
        flash('ยอดเงินไม่เพียงพอ')
        return redirect(url_for('view_cart'))
    
    conn = sqlite3.connect('school_pos.db')
    cursor = conn.cursor()
    
    # สร้างคำสั่งซื้อ
    for shop_id in set(item['shop_id'] for item in cart):
        shop_items = [item for item in cart if item['shop_id'] == shop_id]
        shop_total = sum(item['price'] * item['quantity'] for item in shop_items)
        
        cursor.execute('''
            INSERT INTO orders (student_id, shop_id, total_amount)
            VALUES (?, ?, ?)
        ''', (session['student_id'], shop_id, shop_total))
        
        order_id = cursor.lastrowid
        
        # เพิ่มรายการสินค้า
        for item in shop_items:
            cursor.execute('''
                INSERT INTO order_items (order_id, item_id, quantity, price)
                VALUES (?, ?, ?, ?)
            ''', (order_id, item['item_id'], item['quantity'], item['price']))
    
    # หักเงินจากบัญชี
    new_balance = session['balance'] - total
    cursor.execute('UPDATE students SET balance = ? WHERE student_id = ?', 
                  (new_balance, session['student_id']))
    
    conn.commit()
    conn.close()
    
    session['balance'] = new_balance
    session['cart'] = []
    session.modified = True
    
    flash('สั่งซื้อสำเร็จ!')
    return redirect(url_for('student_dashboard'))

@app.route('/manage_menu')
def manage_menu():
    if 'user_type' not in session or session['user_type'] != 'shop':
        return redirect(url_for('shop_login'))
    
    conn = sqlite3.connect('school_pos.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT item_id, name, price, cost, available, category
        FROM menu_items 
        WHERE shop_id = ? AND available = 1
        GROUP BY name
    ''', (session['shop_id'],))
    menu_items = cursor.fetchall()
    
    conn.close()
    
    return render_template('manage_menu.html', menu_items=menu_items)

@app.route('/add_menu_item', methods=['POST'])
def add_menu_item():
    if 'user_type' not in session or session['user_type'] != 'shop':
        return redirect(url_for('shop_login'))
    
    conn = sqlite3.connect('school_pos.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO menu_items (shop_id, name, price, cost, available, category)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (session['shop_id'], 
          request.form['name'],
          float(request.form['price']),
          float(request.form['cost']),
          True,
          request.form['category']))
    
    conn.commit()
    conn.close()
    
    flash('เพิ่มเมนูสำเร็จ!')
    return redirect(url_for('manage_menu'))

@app.route('/toggle_availability', methods=['POST'])
def toggle_availability():
    item_id = request.json['item_id']
    available = request.json['available']
    
    conn = sqlite3.connect('school_pos.db')
    cursor = conn.cursor()
    
    cursor.execute('UPDATE menu_items SET available = ? WHERE item_id = ?', (available, item_id))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})

@app.route('/sales_report')
def sales_report():
    if 'user_type' not in session or session['user_type'] != 'shop':
        return redirect(url_for('shop_login'))
    
    conn = sqlite3.connect('school_pos.db')
    cursor = conn.cursor()
    
    # รายงานการขายรายเมนู
    cursor.execute('''
        SELECT m.name, SUM(oi.quantity) as total_sold, 
               SUM(oi.quantity * oi.price) as revenue,
               SUM(oi.quantity * m.cost) as total_cost,
               SUM(oi.quantity * (oi.price - m.cost)) as profit
        FROM order_items oi
        JOIN menu_items m ON oi.item_id = m.item_id
        JOIN orders o ON oi.order_id = o.order_id
        WHERE m.shop_id = ?
        GROUP BY m.item_id, m.name
        ORDER BY total_sold DESC
    ''', (session['shop_id'],))
    
    menu_sales = cursor.fetchall()
    
    # รายงานการขายรายวัน (7 วันล่าสุด)
    cursor.execute('''
        SELECT date(order_date) as order_date, 
               COUNT(*) as orders_count,
               SUM(total_amount) as daily_revenue
        FROM orders 
        WHERE shop_id = ? 
        AND order_date >= date('now', '-7 days')
        GROUP BY date(order_date)
        ORDER BY order_date DESC
    ''', (session['shop_id'],))
    
    daily_sales = cursor.fetchall()
    
    conn.close()
    
    return render_template('sales_report.html', 
                         menu_sales=menu_sales, 
                         daily_sales=daily_sales)
    
# -------------------- Admin Portal --------------------
@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect('school_pos.db')
        cursor = conn.cursor()
        cursor.execute('SELECT admin_id, username, password_hash, name FROM admins WHERE username = ?', (username,))
        admin = cursor.fetchone()
        conn.close()

        if admin and check_password_hash(admin[2], password):
            session['user_type'] = 'admin'
            session['admin_id'] = admin[0]
            session['admin_name'] = admin[3]
            flash(f'ยินดีต้อนรับ {admin[3]}!')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง')

    return render_template('admin_login.html')



@app.route('/admin_dashboard')
def admin_dashboard():
    if 'user_type' not in session or session['user_type'] != 'admin':
        return redirect(url_for('admin_login'))
    
    conn = sqlite3.connect('school_pos.db')
    cursor = conn.cursor()
    
    # ดึงข้อมูลนักเรียน
    cursor.execute('SELECT student_id, name, balance FROM students')
    students = cursor.fetchall()
    
    # ดึงข้อมูลร้านค้า
    cursor.execute('SELECT shop_id, shop_name, owner_name FROM shops')
    shops = cursor.fetchall()
    
    conn.close()
    
    return render_template('admin_dashboard.html', students=students, shops=shops)

@app.route('/edit_student/<student_id>', methods=['GET', 'POST'])
def edit_student(student_id):
    if 'user_type' not in session or session['user_type'] != 'admin':
        return redirect(url_for('admin_login'))

    conn = sqlite3.connect('school_pos.db')
    cursor = conn.cursor()

    # ดึงข้อมูลนักเรียนก่อน
    cursor.execute('SELECT name, password_hash, balance FROM students WHERE student_id = ?', (student_id,))
    student = cursor.fetchone()
    if not student:
        conn.close()
        flash('ไม่พบข้อมูลนักเรียน')
        return redirect(url_for('admin_dashboard'))

    if request.method == 'POST':
        name = request.form['name']
        password = request.form.get('password', '').strip()
        balance = float(request.form['balance'])

        # ถ้า password ไม่ว่างก็ update hash ใหม่ ถ้าว่างให้เก็บค่าเดิม
        if password:
            password_hash = generate_password_hash(password)
        else:
            password_hash = student[1]

        cursor.execute('''
            UPDATE students
            SET name = ?, password_hash = ?, balance = ?
            WHERE student_id = ?
        ''', (name, password_hash, balance, student_id))

        conn.commit()
        conn.close()
        flash('อัปเดตข้อมูลนักเรียนเรียบร้อย')
        return redirect(url_for('admin_dashboard'))

    conn.close()
    return render_template('edit_student.html', student_id=student_id, student=student)

@app.route('/delete_student/<student_id>')
def delete_student(student_id):
    if 'user_type' not in session or session['user_type'] != 'admin':
        return redirect(url_for('admin_login'))
    
    conn = sqlite3.connect('school_pos.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM students WHERE student_id = ?', (student_id,))
    conn.commit()
    conn.close()
    
    flash('ลบนักเรียนเรียบร้อย')
    return redirect(url_for('admin_dashboard'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)