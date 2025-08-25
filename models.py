from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import List, Dict, Any, Optional

#описаны основные классы и функции
class BaseModel:
    def to_dict(self) -> Dict[str, Any]:
        """
        Преобразует экземпляр класса в словарь с помощью
        Returns: словарь
        """
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        """
        Создает новый экземпляр класса из словаря данных.
        """
        return cls(**data)

    def validate(self) -> None:
        """
        Полиморфный метод — реализуется в наследниках, предназначен для корректности  данных, в базовом классе пуст
        """
        pass


@dataclass
class Customer(BaseModel):
    """
    Представляет клиента:
    - Поля включают ID, имя, email, телефон, город, дату создания.
    - Метод `validate()` проверяет корректность email и номера телефона с помощью регулярных выражений, а также обязательность имени.
    """
    id: Optional[int] = None
    name: str = ""
    email: str = ""
    phone: str = ""
    city: str = ""
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def validate(self) -> None:
        """
        Проверяет корректность email и номера телефона с помощью регулярных выражений, а также обязательность имени
        Демонстрация инкапсуляции: валидация внутри модели
        """
        import re
        email_re = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
        phone_re = re.compile(r"^\+?\d[\d\s\-()]{7,}$")
        if self.email and not email_re.match(self.email):
            raise ValueError("Некорректный email")
        if self.phone and not phone_re.match(self.phone):
            raise ValueError("Некорректный номер телефона")
        if not self.name:
            raise ValueError("Имя клиента обязательно")


@dataclass
class Product(BaseModel):
    """
    Представляет товар:
    Поля: ID, название, цена, артикул (SKU), дата создания.
    """
    id: Optional[int] = None
    name: str = ""
    price: float = 0.0
    sku: str = ""
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def validate(self) -> None:
        """
        Проверяет наличие названия и что цена не отрицательная.
        """
        if not self.name:
            raise ValueError("Название товара обязательно")
        if self.price < 0:
            raise ValueError("Цена не может быть отрицательной")


@dataclass
class OrderItem(BaseModel):
    """
    Представляет позицию заказа:
    Поля: ID, ID заказа, ID продукта, количество, цена, сумма.
    """
    id: Optional[int] = None
    order_id: Optional[int] = None
    product_id: int = 0
    quantity: int = 1
    price: float = 0.0  # Цена на момент заказа
    subtotal: float = 0.0

    def validate(self) -> None:
        """
        Проверяет что количество > 0, цена не отрицательна, и рассчитывает сумму
        """
        if self.quantity <= 0:
            raise ValueError("Количество должно быть > 0")
        if self.price < 0:
            raise ValueError("Цена не может быть отрицательной")
        if self.subtotal != round(self.quantity * self.price, 2):
            # Автоисправление, демонстрация инкапсуляции
            self.subtotal = round(self.quantity * self.price, 2)


@dataclass
class Order(BaseModel):
    """
    Представляет заказ:
    Поля:ID, ID клиента, дата, статус, общий итог, список позиций заказа.
    """
    id: Optional[int] = None
    customer_id: int = 0
    date: str = field(default_factory=lambda: datetime.utcnow().date().isoformat())
    status: str = "new"
    total: float = 0.0
    items: List[OrderItem] = field(default_factory=list)

    def validate(self) -> None:
        """
        Проверяет наличие клиента, наличие хотя бы одной позиции заказа
        """
        if not self.customer_id:
            raise ValueError("customer_id обязателен")
        if not self.items:
            raise ValueError("Заказ должен содержать хотя бы один товар")
        for it in self.items:
            it.validate()
        calc_total = round(sum(i.subtotal for i in self.items), 2)
        if self.total != calc_total:
            self.total = calc_total


#YES
def quicksort_orders(orders: List[Order], key=lambda o: o.date, reverse: bool = False) -> List[Order]:
    """
    Реализация алгоритма сортировки “быстрая сортировка” (quicksort), который принимает список объектов `Order` и сортирует
    его по определенному ключу (например, по дате или по общему итогу заказа).
    :param orders: Список, который нужно отсортировать
    :param key: функция, которая для каждого объекта возвращает значение для сравнения. По умолчанию сортировка по дате.
    :param reverse: если True итоговый список переворачивается
    :return: Возвращает отсортированный (или обратный при `reverse=True`) список объектов `Order`
    """
    if len(orders) <= 1:
        return orders[:]
    pivot = orders[len(orders) // 2]
    pivot_key = key(pivot)
    left = [o for o in orders if key(o) < pivot_key]
    middle = [o for o in orders if key(o) == pivot_key]
    right = [o for o in orders if key(o) > pivot_key]
    result = quicksort_orders(left, key) + middle + quicksort_orders(right, key)
    return list(reversed(result)) if reverse else result


# Полиморфизм на примере форматирования для экспорта
class Exportable:
    """
    Предложение для наследников реализовать метод `export()`, который возвращает словарь для экспорта.
    """
    def export(self) -> Dict[str, Any]:
        """
        Может быть переопределено наследниками
        """
        return self.to_dict()  # type: ignore


class ExportableCustomer(Customer, Exportable):
    """
    Наследование от соответствующих моделей и `Exportable`.
    """
    def export(self) -> Dict[str, Any]:
        d = super().export()
        d["type"] = "customer"
        return d


class ExportableProduct(Product, Exportable):
    """
    Наследования от соответствующих моделей и `Exportable`.
    """
    def export(self) -> Dict[str, Any]:
        d = super().export()
        d["type"] = "product"
        return d