import sqlite3
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import networkx as nx
from typing import Optional


def get_connection(db_path: str):
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    return con

#YES
def top5_customers_figure(db_path: str):
    """
    функция получения графика топ-5 клиентов по числу заказов и их суммарной стоимости.
    для отображения используется matplotlib, для интеграции данных sql + pandas
    :param db_path: путь к базе данных
    :return: график
    """
    con = get_connection(db_path)
    df = pd.read_sql_query(
        """
        SELECT c.id, c.name, COUNT(o.id) AS order_count, COALESCE(SUM(o.total), 0) AS total_sum
        FROM customers c
        LEFT JOIN orders o ON o.customer_id = c.id
        GROUP BY c.id, c.name
        ORDER BY order_count DESC, total_sum DESC
        LIMIT 5
        """,
        con,
    )
    con.close()
    fig, ax = plt.subplots(figsize=(6, 4))
    sns.barplot(data=df, x="order_count", y="name", ax=ax, hue=None, palette="Blues_d")
    ax.set_title("Топ-5 клиентов по числу заказов")
    ax.set_xlabel("Кол-во заказов")
    ax.set_ylabel("Клиент")
    fig.tight_layout()
    return fig

#YES
def orders_timeseries_figure(db_path: str, freq: str = "D"):
    """
    функция получения графика кол-ва заказов от времени с указанной частотой
    для отображения используется matplotlib, для интеграции данных sql + pandas
    :param db_path: путь к базе данных
    :param freq: default "D" — дневной интервал (ежедневно)
    :return: график
    """
    con = get_connection(db_path)
    df = pd.read_sql_query("SELECT date, total FROM orders", con, parse_dates=["date"])
    con.close()
    if df.empty:
        df = pd.DataFrame({"date": [], "count": []})
    else:
        ts = df.groupby(pd.Grouper(key="date", freq=freq)).size().reset_index(name="count")
        df = ts
    fig, ax = plt.subplots(figsize=(6, 4))
    sns.lineplot(data=df, x="date", y="count", marker="o", ax=ax)
    ax.set_title(f"Динамика количества заказов ({freq})")
    ax.set_xlabel("Дата")
    ax.set_ylabel("Кол-во заказов")
    fig.autofmt_xdate()
    fig.tight_layout()
    return fig

#YES
def customers_network_figure(db_path: str, by: str = "city"):
    """
    функция построения простого граф: ребро между клиентами из одного города
    :param db_path:  путь к базе данных
    :param by: параметр групировки по умолчанию город
    :return: граф
    """
    con = get_connection(db_path)
    df = pd.read_sql_query("SELECT id, name, city FROM customers", con)
    con.close()
    G = nx.Graph()
    for _, row in df.iterrows():
        G.add_node(row["id"], label=row["name"], city=row["city"])
    if by == "city": #группируем по городу
        groups = df.groupby("city")
        for city, g in groups:
            ids = list(g["id"])
            for i in range(len(ids)):
                for j in range(i + 1, len(ids)):
                    G.add_edge(ids[i], ids[j], label=f"{city}")
    # Визуализация
    fig = plt.figure(figsize=(6, 5))
    pos = nx.spring_layout(G, seed=42, k=0.7)
    node_labels = {n: G.nodes[n]["label"] for n in G.nodes}
    nx.draw_networkx_nodes(G, pos, node_size=500, node_color="lightblue")
    nx.draw_networkx_edges(G, pos, alpha=0.4)
    nx.draw_networkx_labels(G, pos, labels=node_labels, font_size=8)
    plt.title("Граф связей клиентов (общий город)")
    plt.axis("off")
    fig.tight_layout()
    return fig