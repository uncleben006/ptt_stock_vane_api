import os
import requests
import pandas as pd
from django.conf import settings
from django.db import connection, transaction

def insert_stock_targets(stock_targets):
    with transaction.atomic():
        with connection.cursor() as cursor:
            sql = "INSERT INTO ptt_stock_targets (no, name) VALUES "
            for stock_target in stock_targets:
                sql += f"('{stock_target['No']}', '{stock_target['Name']}'),"
            sql = sql[:-1] + "ON CONFLICT (no) DO NOTHING;"
            cursor.execute(sql)

def write_stock_targets_csv(stock_targets):
    stock_targets = pd.DataFrame(stock_targets)[["No", "Name"]].rename(columns={"No": "stock_no", "Name": "stock_name"})
    stock_targets_path = os.path.join(settings.DATA_DIR, "stock_targets.csv")
    stock_targets.to_csv(stock_targets_path, index=False)

def fetch_and_insert_stock_targets():
    print("Fetching stock targets...")
    url = "https://histock.tw/stock/module/stockdata.aspx?m=stocks"
    headers = {'referer': 'https://histock.tw/stock/rank.aspx?p=all'}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        stock_targets = response.json()
        insert_stock_targets(stock_targets)
        write_stock_targets_csv(stock_targets)
        print("Inserted:", len(stock_targets))
    else:
        print("Failed to fetch data")