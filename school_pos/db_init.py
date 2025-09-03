from werkzeug.security import generate_password_hash
import sqlite3

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
    
    # ตาราง admins (ครู/แอดมิน)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS admins (
            admin_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            name TEXT NOT NULL
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
            order_id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT,
            shop_id INTEGER,
            order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            total_amount REAL,
            status TEXT DEFAULT 'pending',
            FOREIGN KEY (student_id) REFERENCES students(student_id),
            FOREIGN KEY (shop_id) REFERENCES shops(shop_id)
        )
    ''')
    
    # ตาราง order_items
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS order_items (
            order_item_id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER,
            item_id INTEGER,
            quantity INTEGER,
            price REAL,
            FOREIGN KEY (order_id) REFERENCES orders(order_id),
            FOREIGN KEY (item_id) REFERENCES menu_items(item_id)
        )
    ''')
    
    # ใส่ข้อมูลตัวอย่าง
    insert_sample_data(cursor)
    
    conn.commit()
    conn.close()

def insert_sample_data(cursor):
    # ตัวอย่างครู / แอดมิน
    admins = [
        ('teacher1', 'pass1234', 'ครูสมศรี')  # username, password, ชื่อ
    ]
    
    for username, password, name in admins:
        cursor.execute('''
            INSERT OR IGNORE INTO admins (username, password_hash, name)
            VALUES (?, ?, ?)
        ''', (username, generate_password_hash(password), name))
    
    # ตัวอย่างนักเรียน
    students = [
        ('01514', 'สมชาย ใจดี', '01112547', 500.0),
        ('12346', 'สมหญิง สวยงาม', '02022010', 300.0)
    ]
    
    for student_id, name, birthdate, balance in students:
        cursor.execute('''
            INSERT OR IGNORE INTO students (student_id, name, password_hash, balance)
            VALUES (?, ?, ?, ?)
        ''', (student_id, name, generate_password_hash(birthdate), balance))
    
# ตัวอย่างร้านค้า
shops_data = [
    ('ร้านข้าวแม่สมปอง', 'แม่สมปอง', 'shop123', '/static/images/rice_shop.jpg'),
    ('ร้านก๋วยเตี๋ยวลุงสมชาย', 'ลุงสมชาย', 'shop456', '/static/images/noodle_shop.jpg')
]

for shop_name, owner_name, password, image_url in shops_data:
    cursor.execute('''
        INSERT OR IGNORE INTO shops (shop_name, owner_name, password_hash, image_url)
        VALUES (?, ?, ?, ?)
    ''', (shop_name, owner_name, generate_password_hash(password), image_url))
    
    # ตัวอย่างเมนู
    menu_items = [
        (1, 'ข้าวผัดหมู', 45.0, 25.0, True, '/static/images/fried_rice.jpg', 'ข้าว'),
        (1, 'ข้าวราดแกง', 40.0, 20.0, True, '/static/images/curry_rice.jpg', 'ข้าว'),
        (2, 'ก๋วยเตี๋ยวหมูน้ำใส', 35.0, 18.0, True, '/static/images/clear_soup.jpg', 'ก๋วยเตี๋ยว')
    ]

for shop_id, name, price, cost, available, image_url, category in menu_items:
    cursor.execute('SELECT 1 FROM menu_items WHERE shop_id=? AND name=?', (shop_id, name))
    exists = cursor.fetchone()
    if not exists:
        cursor.execute('''
            INSERT INTO menu_items (shop_id, name, price, cost, available, image_url, category)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (shop_id, name, price, cost, available, image_url, category))




if __name__ == '__main__':
    init_db()
    print("Database initialized!")
