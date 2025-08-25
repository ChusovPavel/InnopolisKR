import sqlite3
from typing import List, Optional, Dict, Any, Tuple
from contextlib import contextmanager
from datetime import datetime
import json
import csv
import os
from models import Customer, Product, Order, OrderItem

#работа с базой данных
#YES
@contextmanager
def connect(db_path: str):
    """
         Работа с базой данных, управление подключением, автоматический commit|rollback
        Args:
            db_path: str: путь к базе данных
        """
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    try:
        con.execute("PRAGMA foreign_keys = ON;")
        yield con
        con.commit()
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()
#YES
def init_db(db_path: str) -> None:
    """
        Создание базы данных без перезаписи IF NOT EXISTS с индексацией
         Args:
             db_path: str: путь к базе данных
         Returns:
             id вставленной записи
    """

    with connect(db_path) as con:
        cur = con.cursor()
        cur.executescript(
            """
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT,
                phone TEXT,
                city TEXT,
                created_at TEXT
            );
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                price REAL NOT NULL,
                sku TEXT UNIQUE,
                created_at TEXT
            );
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY,
                customer_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                status TEXT NOT NULL,
                total REAL NOT NULL,
                FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE
            );
            CREATE TABLE IF NOT EXISTS order_items (
                id INTEGER PRIMARY KEY,
                order_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                price REAL NOT NULL,
                subtotal REAL NOT NULL,
                FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
                FOREIGN KEY (product_id) REFERENCES products(id)
            );
            CREATE INDEX IF NOT EXISTS idx_orders_date ON orders(date);
            CREATE INDEX IF NOT EXISTS idx_orders_customer ON orders(customer_id);
            """
        )

#YES
def add_customer(db_path: str, customer: Customer) -> int:
    """
         Регистрация новых клиентов с валидацией введеных значений для Имени, телефона и email
         Args:
             db_path: str: путь к базе данных
             customer: Customer данные берутся из свойств объекта `product` в Customer.py.

         Returns:
             id вставленной записи
         """
    customer.validate()
    with connect(db_path) as con:
        cur = con.cursor()
        cur.execute(
            "INSERT INTO customers(name, email, phone, city, created_at) VALUES(?,?,?,?,?)",
            (customer.name, customer.email, customer.phone, customer.city, customer.created_at),
        )
        return cur.lastrowid

#YES
def get_customers(db_path: str, search: Optional[str] = None, order_by: str = "created_at DESC") -> List[Dict[str, Any]]:
    """
         получение списка клиентов из базы данных с возможностью поиска и сортировки
         Args:
             db_path: str: путь к базе данных
             search: Optional[str] = None поиск по имени или артикулу (SKU) по умолчанию не выполняется
             order_by: str = "created_at DESC" строка для сортировки, по умолчанию по убыванию
         Returns:
             список словарей клиентов, отсортированых и удовлетворяющих условию поиска
         """
    with connect(db_path) as con:
        cur = con.cursor()
        if search:
            like = f"%{search}%"
            cur.execute(
                f"SELECT * FROM customers WHERE name LIKE ? OR email LIKE ? OR phone LIKE ? OR city LIKE ? ORDER BY {order_by}",
                (like, like, like, like),
            )
        else:
            cur.execute(f"SELECT * FROM customers ORDER BY {order_by}")
        return [dict(row) for row in cur.fetchall()]


#YES
def add_product(db_path: str, product: Product) -> int:
    """
        Регистрация новых продуктов с валидацией введеных значений
        Args:
            db_path: str: путь к базе данных
            product: Product данные берутся из свойств объекта `product` в models.py.
        Returns:
            id вставленной записи
        """
    product.validate()
    with connect(db_path) as con:
        cur = con.cursor()
        cur.execute(
            "INSERT INTO products(name, price, sku, created_at) VALUES(?,?,?,?)",
            (product.name, product.price, product.sku, product.created_at),
        )
        return cur.lastrowid

#YES
def get_products(db_path: str, search: Optional[str] = None, order_by: str = "created_at DESC") -> List[Dict[str, Any]]:
    """
      получение списка товаров из базы данных с возможностью поиска и сортировки
      Args:
          db_path: str: путь к базе данных
          search: Optional[str] = None поиск по имени или артикулу (SKU) по умолчанию не выполняется
          order_by: str = "created_at DESC" строка для сортировки по умолчанию по убыванию
      Returns:
          список словарей товаров, отсортированых и удовлетворяющих условию поиска
      """
    with connect(db_path) as con:
        cur = con.cursor()
        if search:
            like = f"%{search}%"
            cur.execute(
                f"SELECT * FROM products WHERE name LIKE ? OR sku LIKE ? ORDER BY {order_by}",
                (like, like),
            )
        else:
            cur.execute(f"SELECT * FROM products ORDER BY {order_by}")
        return [dict(row) for row in cur.fetchall()]


#YES
def add_order(db_path: str, order: Order) -> int:
    """
    добавление нового заказа в базу данных
    :param db_path: путь до базы данных
    :param order: новый заказ
    :return: ID созданного заказа
    """
    with connect(db_path) as con:
        cur = con.cursor()
        # Обновим цену в позициях (чтобы зафиксировать цену на момент покупки)
        for it in order.items:
            if it.price <= 0:
                pr = cur.execute("SELECT price FROM products WHERE id = ?", (it.product_id,)).fetchone()
                if not pr:
                    raise ValueError(f"Товар id={it.product_id} не найден")
                it.price = float(pr["price"])
            it.subtotal = round(it.price * it.quantity, 2)
        order.validate()
        #добавление в order
        cur.execute(
            "INSERT INTO orders(customer_id, date, status, total) VALUES(?,?,?,?)",
            (order.customer_id, order.date, order.status, order.total),
        )
        order_id = cur.lastrowid
        for it in order.items:
            cur.execute(
                "INSERT INTO order_items(order_id, product_id, quantity, price, subtotal) VALUES(?,?,?,?,?)",
                (order_id, it.product_id, it.quantity, it.price, it.subtotal),
            )
        return order_id

#YES
def get_orders(db_path: str,date_from: Optional[str] = None,date_to: Optional[str] = None,status: Optional[str] = None,customer_search: Optional[str] = None,order_by: str = "date DESC",) -> List[Dict[str, Any]]:
    """
    выполняет поиск и извлечение данных о заказах из базы данных.
    :param db_path: Путь к базе данных
    :param date_from: начальная дата
    :param date_to: конечная дата
    :param status: статус заказа
    :param customer_search: поиск по email, имени или городу
    :param order_by: по умолчанию сортировка по убыванию даты
    :return:список словарей отсортированной таблицы
    """
    with connect(db_path) as con:
        cur = con.cursor()
        q = """
            SELECT o.*, c.name AS customer_name, c.email AS customer_email, c.city AS customer_city
            FROM orders o
            JOIN customers c ON c.id = o.customer_id
            WHERE 1=1
        """
        params: List[Any] = []
        if date_from:
            q += " AND date(o.date) >= date(?)"
            params.append(date_from)
        if date_to:
            q += " AND date(o.date) <= date(?)"
            params.append(date_to)
        if status:
            q += " AND o.status = ?"
            params.append(status)
        if customer_search:
            like = f"%{customer_search}%"
            q += " AND (c.name LIKE ? OR c.email LIKE ? OR c.city LIKE ?)"
            params.extend([like, like, like])
        q += f" ORDER BY {order_by}"
        cur.execute(q, params)
        return [dict(row) for row in cur.fetchall()]

#YES
def get_order_items(db_path: str, order_id: int) -> List[Dict[str, Any]]:
    """
    Функция для отображения деталей заказа
    Args:
        db_path: Путь к базе данных
        order_id: id заказа
    Returns: словарь с артикулом, суммой и названием товаров в заказе
    """
    with connect(db_path) as con:
        cur = con.cursor()
        cur.execute(
            """
            SELECT oi.*, p.name as product_name, p.sku
            FROM order_items oi
            JOIN products p ON p.id = oi.product_id
            WHERE oi.order_id = ?
            """,
            (order_id,),
        )
        return [dict(row) for row in cur.fetchall()]


# Импорт/экспорт CSV / JSON
#YES
def export_to_csv(db_path: str, folder: str) -> None:
    """
    Функция экспорта базы данных в .csv
    Args:
        db_path: путь к БД
        folder: путь для сохранения .csv
    Returns: файлы .csv
    """
    os.makedirs(folder, exist_ok=True)
    with connect(db_path) as con:
        cur = con.cursor()
        tables = ["customers", "products", "orders", "order_items"]
        for t in tables:
            rows = cur.execute(f"SELECT * FROM {t}").fetchall()
            if not rows:
                # создадим файл с заголовками
                cols = [c[1] for c in cur.execute(f"PRAGMA table_info({t})")]
            else:
                cols = rows[0].keys()
            path = os.path.join(folder, f"{t}.csv")
            with open(path, "w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=cols)
                w.writeheader()
                for r in rows:
                    w.writerow(dict(r))

#YES
def import_from_csv(db_path: str, folder: str, clear_before: bool = False) -> None:
    """
    Функция импорта файлов .csv в бузу данных
    Args:
        db_path: путь к БД
        folder: папка в которой находятся csv файлы
        clear_before: флаг для очистки базы данных, не очищать по умолчанию
    """
    with connect(db_path) as con:
        cur = con.cursor()
        if clear_before:# очистка базы данных по необходимости
            cur.executescript("DELETE FROM order_items; DELETE FROM orders; DELETE FROM products; DELETE FROM customers;")
        for t in ["customers", "products", "orders", "order_items"]:# для каждой таблицы формируем путь, преобразование
            path = os.path.join(folder, f"{t}.csv")
            if not os.path.exists(path):
                continue
            with open(path, "r", newline="", encoding="utf-8") as f:
                r = csv.DictReader(f)
                rows = list(r)
                if not rows:
                    continue
                cols = rows[0].keys()
                placeholders = ",".join(["?"] * len(cols))
                col_list = ",".join(cols)
                values = [tuple(row[c] for c in cols) for row in rows]
                # Попробуем сохранить указанное id, если оно есть
                cur.executemany(f"INSERT OR REPLACE INTO {t} ({col_list}) VALUES ({placeholders})", values)

#YES
def export_to_json(db_path: str, path: str) -> None:
    """
    Функция экспорта базы данных в .json
    Args:
        db_path: Путь к базе данных
        path: путь для сохранения .json
    Returns: файл .json в виде словарей, где кажды словарь это таблица
    """
    with connect(db_path) as con:
        cur = con.cursor()
        data = {}
        for t in ["customers", "products", "orders", "order_items"]:
            rows = cur.execute(f"SELECT * FROM {t}").fetchall()
            data[t] = [dict(r) for r in rows]
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

#YES
def import_from_json(db_path: str, path: str, clear_before: bool = False) -> None:
    """
    Функция импорта базы из файл .json
    Args:
        db_path: путь к базе данных
        path: путь к файлу .json
        clear_before: флаг для очистки текущей базы данных
    """
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    with connect(db_path) as con:
        cur = con.cursor()
        if clear_before:
            cur.executescript("DELETE FROM order_items; DELETE FROM orders; DELETE FROM products; DELETE FROM customers;")
        for t, rows in data.items():
            if not rows:
                continue
            cols = rows[0].keys()
            placeholders = ",".join(["?"] * len(cols))
            col_list = ",".join(cols)
            values = [tuple(row[c] for c in cols) for row in rows]
            cur.executemany(f"INSERT OR REPLACE INTO {t} ({col_list}) VALUES ({placeholders})", values)