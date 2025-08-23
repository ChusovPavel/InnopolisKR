import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
import re
from typing import List

from models import Customer, Product, Order, OrderItem, quicksort_orders
import db
import analysis

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
PHONE_RE = re.compile(r"^\+?\d[\d\s\-()]{7,}$")

#класс для работы с GUI
class App(tk.Tk):
    def __init__(self, db_path: str):
        super().__init__()
        self.title("Интернет-магазин")
        self.geometry("1100x750")
        self.db_path = db_path

        nb = ttk.Notebook(self)
        self.tab_customers = ttk.Frame(nb)
        self.tab_products = ttk.Frame(nb)
        self.tab_orders = ttk.Frame(nb)
        self.tab_analytics = ttk.Frame(nb)
        self.tab_admin = ttk.Frame(nb)

        nb.add(self.tab_customers, text="Клиенты")
        nb.add(self.tab_products, text="Товары")
        nb.add(self.tab_orders, text="Заказы")
        nb.add(self.tab_analytics, text="Аналитика")
        nb.add(self.tab_admin, text="Администрирование")
        nb.pack(fill=tk.BOTH, expand=True)

        #вызываем методы класса в которых описана каждая вкладка
        self._build_customers_tab()
        self._build_products_tab()
        self._build_orders_tab()
        self._build_analytics_tab()
        self._build_admin_tab()

        self.refresh_customers()
        self.refresh_products()
        self.refresh_orders()

    #YES
    # Вкладка клиентов с методами добавления и перезагрузки/сортировки таблицы клиентов в БД
    def _build_customers_tab(self):
        """
        в данном методе описана вкладка виджета Регистрации клиентов
        визуально выделен блок регистрации клиентов
        """
        frm = self.tab_customers #для удобства

        form = ttk.LabelFrame(frm, text="Добавить клиента")  #рамка
        form.pack(side=tk.TOP, fill=tk.X, padx=8, pady=8)

        self.c_name = tk.StringVar()
        self.c_email = tk.StringVar()
        self.c_phone = tk.StringVar()
        self.c_city = tk.StringVar()

        ttk.Label(form, text="Имя:").grid(row=0, column=0, sticky="w")
        ttk.Entry(form, textvariable=self.c_name, width=30).grid(row=0, column=1, sticky="w")
        ttk.Label(form, text="Email:").grid(row=0, column=2, sticky="w")
        ttk.Entry(form, textvariable=self.c_email, width=30).grid(row=0, column=3, sticky="w")
        ttk.Label(form, text="Телефон:").grid(row=1, column=0, sticky="w")
        ttk.Entry(form, textvariable=self.c_phone, width=30).grid(row=1, column=1, sticky="w")
        ttk.Label(form, text="Город:").grid(row=1, column=2, sticky="w")
        ttk.Entry(form, textvariable=self.c_city, width=30).grid(row=1, column=3, sticky="w")
        ttk.Button(form, text="Добавить", command=self.add_customer).grid(row=0, column=4, rowspan=2, padx=6)

        search_frm = ttk.Frame(frm) #поиск клиентов
        search_frm.pack(fill=tk.X, padx=8)
        self.c_search = tk.StringVar()
        ttk.Label(search_frm, text="Поиск:").pack(side=tk.LEFT)
        ttk.Entry(search_frm, textvariable=self.c_search, width=40).pack(side=tk.LEFT)
        ttk.Button(search_frm, text="Найти", command=self.refresh_customers).pack(side=tk.LEFT, padx=6)

        #виджет вывода таблицы клиентов
        self.c_tree = ttk.Treeview(frm, columns=("id", "name", "email", "phone", "city", "created_at"), show="headings")
        for col, txt, w in [
            ("id", "ID", 50),
            ("name", "Имя", 160),
            ("email", "Email", 170),
            ("phone", "Телефон", 120),
            ("city", "Город", 120),
            ("created_at", "Создан", 160),
        ]:
            self.c_tree.heading(col, text=txt)
            self.c_tree.column(col, width=w, anchor="w")
        self.c_tree.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

    #YES
    def add_customer(self):
        """
        добавляет новых пользователей в базу данных с указанием времени, после ч его очищает поля ввода,
        проводит проверку через регулярные выражения корректности email и телефона
        при возникновении выводит ошибку через конструкцию try..except
        """
        try:
            name = self.c_name.get().strip()
            email = self.c_email.get().strip()
            phone = self.c_phone.get().strip()
            city = self.c_city.get().strip()
            if email and not EMAIL_RE.match(email):
                raise ValueError("Некорректный email")
            if phone and not PHONE_RE.match(phone):
                raise ValueError("Некорректный телефон")
            cust = Customer(name=name, email=email, phone=phone, city=city)
            db.add_customer(self.db_path, cust)
            self.c_name.set("")
            self.c_email.set("")
            self.c_phone.set("")
            self.c_city.set("")
            self.refresh_customers()
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

    #YES
    def refresh_customers(self):
        """
        метод перезагрузки базы и вывода актуальной базы данных
        """
        for i in self.c_tree.get_children():
            self.c_tree.delete(i)
        search = self.c_search.get().strip() or None
        rows = db.get_customers(self.db_path, search=search) #загружаем отсоритрованю таблицу из базы данных
        for r in rows:
            #выводим результаты в виджет построчно
            self.c_tree.insert("", tk.END, values=(r["id"], r["name"], r["email"], r["phone"], r["city"], r["created_at"]))

    #yes
    # Вкладка товаров с методами добавления и перезагрузки/сортировки таблицы товаров в БД
    def _build_products_tab(self):
        """
               в данном методе визуализированная вкладка виджета Товаров
               Визуально выделен блок заведения товаров
               оформление аналогично вкладке клиентов
               """
        # Блок ренгистрации в системе товаров
        frm = self.tab_products
        form = ttk.LabelFrame(frm, text="Добавить товар")
        form.pack(side=tk.TOP, fill=tk.X, padx=8, pady=8)

        self.p_name = tk.StringVar()
        self.p_price = tk.StringVar()
        self.p_sku = tk.StringVar()

        ttk.Label(form, text="Название:").grid(row=0, column=0, sticky="w")
        ttk.Entry(form, textvariable=self.p_name, width=30).grid(row=0, column=1, sticky="w")
        ttk.Label(form, text="Цена:").grid(row=0, column=2, sticky="w")
        ttk.Entry(form, textvariable=self.p_price, width=20).grid(row=0, column=3, sticky="w")
        ttk.Label(form, text="SKU:").grid(row=0, column=4, sticky="w")
        ttk.Entry(form, textvariable=self.p_sku, width=20).grid(row=0, column=5, sticky="w")
        ttk.Button(form, text="Добавить", command=self.add_product).grid(row=0, column=6, padx=6)

        # блок поиска/сортировки товаров
        search_frm = ttk.Frame(frm)
        search_frm.pack(fill=tk.X, padx=8)
        self.p_search = tk.StringVar()
        ttk.Label(search_frm, text="Поиск:").pack(side=tk.LEFT)
        ttk.Entry(search_frm, textvariable=self.p_search, width=40).pack(side=tk.LEFT)
        ttk.Button(search_frm, text="Найти", command=self.refresh_products).pack(side=tk.LEFT, padx=6)

        # оформление блока визуализации зарегистрированных товаров
        self.p_tree = ttk.Treeview(frm, columns=("id", "name", "price", "sku", "created_at"), show="headings")
        for col, txt, w in [
            ("id", "ID", 50),
            ("name", "Название", 220),
            ("price", "Цена", 100),
            ("sku", "SKU", 120),
            ("created_at", "Создан", 160),
        ]:
            self.p_tree.heading(col, text=txt)
            self.p_tree.column(col, width=w, anchor="w")
        self.p_tree.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

    #YES
    def add_product(self):
        """
        добавляет новые товары в базу данных с указанием времени, после чего очищает поля ввода
        при возникновении выводит ошибку через конструкцию try..except
        """
        try:
            name = self.p_name.get().strip()
            price = float(self.p_price.get().strip().replace(",", "."))
            sku = self.p_sku.get().strip()
            pr = Product(name=name, price=price, sku=sku)
            db.add_product(self.db_path, pr)
            self.p_name.set("")
            self.p_price.set("")
            self.p_sku.set("")
            self.refresh_products()
        except ValueError as ve:
            messagebox.showerror("Ошибка", str(ve))
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось добавить товар: {e}")

    #YES
    def refresh_products(self):
        """
        метод перезагрузки базы и вывода актуальной таблицы товаров из базы данных
        """
        for i in self.p_tree.get_children():
            self.p_tree.delete(i)
        search = self.p_search.get().strip() or None
        rows = db.get_products(self.db_path, search=search)
        for r in rows:
            self.p_tree.insert("", tk.END, values=(r["id"], r["name"], f'{r["price"]:.2f}', r["sku"], r["created_at"]))

    #YES
    # Вкладка заказов с методами добавления/отображения заказов
    def _build_orders_tab(self):
        """
        в данном методе описана вкладка виджета Заказов клиентов
        реализована сортировка(собственная)
        визуально выделен блок создания заказов
        """
        frm = self.tab_orders

        top = ttk.Frame(frm)
        top.pack(fill=tk.X, padx=8, pady=6)

        # блок фильтрации/сортировки
        ttk.Label(top, text="От:").pack(side=tk.LEFT)
        self.o_from = tk.StringVar()
        self.o_to = tk.StringVar()
        ttk.Entry(top, textvariable=self.o_from, width=12).pack(side=tk.LEFT)
        ttk.Label(top, text="До:").pack(side=tk.LEFT)
        ttk.Entry(top, textvariable=self.o_to, width=12).pack(side=tk.LEFT)
        ttk.Label(top, text="Статус:").pack(side=tk.LEFT)
        self.o_status = tk.StringVar()
        ttk.Combobox(top, textvariable=self.o_status, values=["", "new", "paid", "shipped", "cancelled"], width=12).pack(side=tk.LEFT)
        ttk.Label(top, text="Клиент:").pack(side=tk.LEFT)
        self.o_cust_search = tk.StringVar()
        ttk.Entry(top, textvariable=self.o_cust_search, width=20).pack(side=tk.LEFT)
        ttk.Button(top, text="Применить фильтры", command=self.refresh_orders).pack(side=tk.LEFT, padx=6)

        # демонстрация собственной сортировки
        ttk.Label(top, text="Сортировка:").pack(side=tk.LEFT, padx=(20, 2))
        self.o_sort = tk.StringVar(value="date_desc")
        ttk.Combobox(top, textvariable=self.o_sort, values=["date_desc", "date_asc", "total_desc", "total_asc"], width=12).pack(side=tk.LEFT)
        ttk.Button(top, text="Моя сортировка", command=self.custom_sort_orders).pack(side=tk.LEFT, padx=6)

        # Виджет создания заказов с реализацией выпадащего списка Combobox для товаров и заказов
        form = ttk.LabelFrame(frm, text="Создать заказ")
        form.pack(fill=tk.X, padx=8, pady=6)

        ttk.Label(form, text="Клиент:").grid(row=0, column=0, sticky="w")
        self.o_customer = tk.StringVar()
        self.o_customer_cb = ttk.Combobox(form, textvariable=self.o_customer, width=35, postcommand=self._reload_customers_cb)
        self.o_customer_cb.grid(row=0, column=1, sticky="w")

        ttk.Label(form, text="Товар:").grid(row=0, column=2, sticky="w")
        self.o_product = tk.StringVar()
        self.o_product_cb = ttk.Combobox(form, textvariable=self.o_product, width=35, postcommand=self._reload_products_cb)
        self.o_product_cb.grid(row=0, column=3, sticky="w")

        ttk.Label(form, text="Кол-во:").grid(row=0, column=4, sticky="w")
        self.o_qty = tk.IntVar(value=1)
        ttk.Spinbox(form, from_=1, to=999, textvariable=self.o_qty, width=6).grid(row=0, column=5, sticky="w")
        ttk.Button(form, text="Добавить позицию", command=self.add_order_item_to_list).grid(row=0, column=6, padx=6)

        #визулизация блока создания нового заказа
        self.items_tree = ttk.Treeview(form, columns=("product_id", "name", "price", "qty", "subtotal"), show="headings", height=5)
        for col, txt, w in [
            ("product_id", "ID товара", 80),
            ("name", "Название", 220),
            ("price", "Цена", 90),
            ("qty", "Кол-во", 70),
            ("subtotal", "Итого", 90),
        ]:
            self.items_tree.heading(col, text=txt)
            self.items_tree.column(col, width=w, anchor="w")
        self.items_tree.grid(row=1, column=0, columnspan=7, sticky="we", pady=6)

        ttk.Button(form, text="Удалить позицию", command=self.remove_selected_item).grid(row=2, column=0, sticky="w")
        ttk.Button(form, text="Создать заказ", command=self.create_order).grid(row=2, column=6, sticky="e")

        # визуализация блока всех заказов
        self.o_tree = ttk.Treeview(frm, columns=("id", "date", "customer", "status", "total"), show="headings")
        for col, txt, w in [
            ("id", "ID", 60),
            ("date", "Дата", 110),
            ("customer", "Клиент", 220),
            ("status", "Статус", 100),
            ("total", "Сумма", 100),
        ]:
            self.o_tree.heading(col, text=txt)
            self.o_tree.column(col, width=w, anchor="w")
        self.o_tree.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        self.o_tree.bind("<Double-1>", self.show_order_details)

        self._order_buffer = []  # для своей сортировки

    #YES
    def _reload_customers_cb(self):
        """
        выгрузка списка клиентов с id из базы данных в выпадающий список
        """
        rows = db.get_customers(self.db_path)
        self._customers_map = {f'{r["name"]} (id={r["id"]})': r["id"] for r in rows}
        self.o_customer_cb["values"] = list(self._customers_map.keys())

    #YES
    def _reload_products_cb(self):
        """
        выгрузка списка товаров с id из базы данных в выпадающий список
        """
        rows = db.get_products(self.db_path)
        self._products_map = {f'{r["name"]} (id={r["id"]}, {r["price"]:.2f})': (r["id"], float(r["price"]), r["name"]) for r in rows}
        self.o_product_cb["values"] = list(self._products_map.keys())

    #YES
    def add_order_item_to_list(self):
        """
        добавления товара в текущий заказ с проверкой того, что бы поля были выбраны
        """
        sel = self.o_product.get()
        if not sel or sel not in getattr(self, "_products_map", {}):
            messagebox.showwarning("Внимание", "Выберите товар")
            return
        pid, price, pname = self._products_map[sel]
        qty = max(1, int(self.o_qty.get()))
        subtotal = round(price * qty, 2)
        self.items_tree.insert("", tk.END, values=(pid, pname, f"{price:.2f}", qty, f"{subtotal:.2f}"))

    #YES
    def remove_selected_item(self):
        """
        Удаление выбранной позиции из окна формирования заказа
        """
        for i in self.items_tree.selection():
            self.items_tree.delete(i)

    #YES
    def create_order(self):
        """
        оформление нового заказа: сбор данных, проверка, добавление в базу и очистка интерфейса
        """
        try:
            sel = self.o_customer.get()
            if not sel or sel not in getattr(self, "_customers_map", {}):
                raise ValueError("Выберите клиента")
            customer_id = self._customers_map[sel]
            items = []
            for i in self.items_tree.get_children():
                pid, name, price, qty, subtotal = self.items_tree.item(i, "values")
                it = OrderItem(product_id=int(pid), quantity=int(qty), price=float(price), subtotal=float(subtotal))
                items.append(it)
            if not items:
                raise ValueError("Добавьте хотя бы один товар в заказ")
            order = Order(customer_id=customer_id, date=datetime.utcnow().date().isoformat(), status="new", items=items)
            db.add_order(self.db_path, order)
            # Очистить форму
            for i in self.items_tree.get_children():
                self.items_tree.delete(i)
            self.o_customer.set("")
            self.o_product.set("")
            self.o_qty.set(1)
            self.refresh_orders()
            messagebox.showinfo("Успех", "Заказ создан")
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

    #YES
    def refresh_orders(self):
        """
        обновляет таблицу виджета отображения заказов применя сортировку по дате, имени, email и статусу заказа клиента
        """
        for i in self.o_tree.get_children(): #очищает предыдущий вывод
            self.o_tree.delete(i)
        rows = db.get_orders(
            self.db_path,
            date_from=self.o_from.get().strip() or None,
            date_to=self.o_to.get().strip() or None,
            status=self.o_status.get().strip() or None,
            customer_search=self.o_cust_search.get().strip() or None,
            order_by="date DESC",
        )
        self._order_buffer = rows[:]  # сохраняем для своей сортировки
        for r in rows:
            self.o_tree.insert("", tk.END, values=(r["id"], r["date"], r["customer_name"], r["status"], f'{r["total"]:.2f}'))

    #YES
    def custom_sort_orders(self):
        """
        Собственная сортировка, конвертирует список словарей в объекты `Order`, сортирует их по выбранному
        пользовательским способом критерию с помощью быстрой сортировки (`quicksort_orders`) и обновляет таблицу заказов
        """
        orders = []
        for r in self._order_buffer:
            o = Order(id=r["id"], customer_id=r["customer_id"], date=r["date"], status=r["status"], total=r["total"], items=[])
            orders.append(o)
        #создаем словарь
        keymap = {
            "date_desc": (lambda o: o.date, True),
            "date_asc": (lambda o: o.date, False),
            "total_desc": (lambda o: o.total, True),
            "total_asc": (lambda o: o.total, False),
        }
        key, rev = keymap.get(self.o_sort.get(), (lambda o: o.date, True))
        sorted_orders = quicksort_orders(orders, key=key, reverse=rev)

        # Обновить таблицу, удаляя и вставляя результаты сортировки
        by_id = {r["id"]: r for r in self._order_buffer}
        for i in self.o_tree.get_children():
            self.o_tree.delete(i)
        for o in sorted_orders:
            r = by_id[o.id]
            self.o_tree.insert("", tk.END, values=(r["id"], r["date"], r["customer_name"], r["status"], f'{r["total"]:.2f}'))

    #YES
    def show_order_details(self, event=None):
        """
        Обработчик событий
        Формирование и вывод текста с подробностями заказа по двойном клике ПКМ
        :param event: none gj evjkxfyb.
        :return: messagebox "Детали заказа"
        """
        sel = self.o_tree.selection()
        if not sel:
            return
        order_id = int(self.o_tree.item(sel[0], "values")[0])
        items = db.get_order_items(self.db_path, order_id)
        details = "\n".join([f'- {i["product_name"]} x{i["quantity"]} = {i["subtotal"]:.2f}' for i in items])
        messagebox.showinfo("Детали заказа", f"Позиции заказа #{order_id}:\n{details}")

    # Вкладка аналитики
    def _build_analytics_tab(self):
        #размещение виджетов на странице GUI
        frm = self.tab_analytics
        btns = ttk.Frame(frm)
        btns.pack(fill=tk.X, padx=8, pady=8)
        ttk.Button(btns, text="Топ-5 клиентов", command=self.draw_top5).pack(side=tk.LEFT, padx=6)
        ttk.Button(btns, text="Динамика заказов", command=lambda: self.draw_timeseries("D")).pack(side=tk.LEFT, padx=6)
        ttk.Button(btns, text="Граф связей", command=self.draw_network).pack(side=tk.LEFT, padx=6)

        self.canvas_frame = ttk.Frame(frm)
        self.canvas_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        self._current_canvas = None

    #YES
    def _show_figure(self, fig):
        """
        отображает, растягивает, проверят, не отображен ли другой график в интерфейсе, по необходимости удаляет.
        размещает график полученный из matplotlib в tkinter
        :param fig: график полученный из matplotlib
        """
        if self._current_canvas:
            self._current_canvas.get_tk_widget().destroy()
        canvas = FigureCanvasTkAgg(fig, master=self.canvas_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self._current_canvas = canvas

    #YES
    def draw_top5(self):
        """
        функция вызова функции построения графика ТОП-5 клиентов и размещения фигуры на странице
        """
        fig = analysis.top5_customers_figure(self.db_path)
        self._show_figure(fig)

    #YES
    def draw_timeseries(self, freq="D"):
        """
        функция вызова функции динамики заказов и размещения фигуры на странице
        """
        fig = analysis.orders_timeseries_figure(self.db_path, freq=freq)
        self._show_figure(fig)

    #YES
    def draw_network(self):
        fig = analysis.customers_network_figure(self.db_path, by="city")
        self._show_figure(fig)

    # Администрирование
    def _build_admin_tab(self):
        frm = self.tab_admin
        lbl = ttk.LabelFrame(frm, text="Импорт/Экспорт")
        lbl.pack(fill=tk.X, padx=8, pady=8)

        ttk.Button(lbl, text="Экспорт CSV (папка)", command=self.export_csv).pack(side=tk.LEFT, padx=6, pady=6)
        ttk.Button(lbl, text="Импорт CSV (папка)", command=self.import_csv).pack(side=tk.LEFT, padx=6, pady=6)
        ttk.Button(lbl, text="Экспорт JSON (файл)", command=self.export_json).pack(side=tk.LEFT, padx=6, pady=6)
        ttk.Button(lbl, text="Импорт JSON (файл)", command=self.import_json).pack(side=tk.LEFT, padx=6, pady=6)

        lbl2 = ttk.LabelFrame(frm, text="Утилиты")
        lbl2.pack(fill=tk.X, padx=8, pady=8)
        ttk.Button(lbl2, text="Резервная копия БД", command=self.backup_db).pack(side=tk.LEFT, padx=6, pady=6)

    def export_csv(self):
        try:
            folder = filedialog.askdirectory()
            if not folder:
                return
            db.export_to_csv(self.db_path, folder)
            messagebox.showinfo("Готово", f"Экспортировано в {folder}")
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

    def import_csv(self):
        try:
            folder = filedialog.askdirectory()
            if not folder:
                return
            clear = messagebox.askyesno("Очистка", "Очистить текущие данные перед импортом?")
            db.import_from_csv(self.db_path, folder, clear_before=clear)
            self.refresh_customers(); self.refresh_products(); self.refresh_orders()
            messagebox.showinfo("Готово", f"Импортировано из {folder}")
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

    def export_json(self):
        try:
            path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON", "*.json")])
            if not path:
                return
            db.export_to_json(self.db_path, path)
            messagebox.showinfo("Готово", f"Экспортировано в {path}")
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

    def import_json(self):
        try:
            path = filedialog.askopenfilename(filetypes=[("JSON", "*.json")])
            if not path:
                return
            clear = messagebox.askyesno("Очистка", "Очистить текущие данные перед импортом?")
            db.import_from_json(self.db_path, path, clear_before=clear)
            self.refresh_customers(); self.refresh_products(); self.refresh_orders()
            messagebox.showinfo("Готово", f"Импортировано из {path}")
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

    def backup_db(self):
        try:
            path = filedialog.asksaveasfilename(defaultextension=".db", filetypes=[("SQLite DB", "*.db")])
            if not path:
                return
            import shutil
            shutil.copyfile(self.db_path, path)
            messagebox.showinfo("Готово", f"Резервная копия сохранена: {path}")
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))