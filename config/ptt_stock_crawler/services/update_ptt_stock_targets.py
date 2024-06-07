import requests
from django.db import connection, transaction

def insert_stock_targets(stock_targets):
    with transaction.atomic():
        with connection.cursor() as cursor:
            sql = "INSERT INTO ptt_stock_targets (no, name) VALUES "
            for stock_target in stock_targets:
                sql += f"('{stock_target['No']}', '{stock_target['Name']}'),"
            sql = sql[:-1] + "ON CONFLICT (no) DO NOTHING;"
            cursor.execute(sql)

def fetch_and_insert_stock_targets():
    print("Fetching stock targets...")
    url = "https://histock.tw/stock/module/stockdata.aspx?m=stocks"
    headers = {'referer': 'https://histock.tw/stock/rank.aspx?p=all'}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        stock_targets = response.json()
        insert_stock_targets(stock_targets)
        print("Inserted:", len(stock_targets))
    else:
        print("Failed to fetch data")