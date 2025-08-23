# main.py
import os
from gui import App
import db
from models import Customer, Product

DB_PATH = "app.db"

#YES
def seed_if_empty(db_path: str):
    """
        Демонстрация работы программы, если данные в базе отсутствует, заполняет демонстрационные данные
        Args:
            db_path (str): путь к базе данных.
        """
    cs = db.get_customers(db_path)
    ps = db.get_products(db_path)
    if not cs:
        try:
            db.add_customer(db_path, Customer(name="Павлов Павел", email="chusov-pa@ug.rt.ru", phone="89024472231", city="Екатеринбург"))
            db.add_customer(db_path, Customer(name="Абубакир Абубакиров", email="maga@mail.kz", phone="+79211112233", city="Ашхабад"))
            db.add_customer(db_path, Customer(name="Алексей Долбатов", email="guf@gmail.com", phone="+7 495 765-43-21", city="Москва"))
        except Exception:
            pass
    if not ps:
        try:
            db.add_product(db_path, Product(name="Нубук", price=59990.0, sku="NB-001"))
            db.add_product(db_path, Product(name="Мышь", price=1290.0, sku="MS-002"))
            db.add_product(db_path, Product(name="Клава", price=2490.0, sku="KB-003"))
        except Exception:
            pass


def main():
    db.init_db(DB_PATH) # Инициализация/создание базы данных по пути DB_PATH
    seed_if_empty(DB_PATH) #Запуск функции демонстрации если база данных пуста/не создана
    app = App(DB_PATH)
    app.mainloop()


if __name__ == "__main__":
    main()