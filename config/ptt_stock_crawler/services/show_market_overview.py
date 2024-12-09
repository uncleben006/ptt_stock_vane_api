import psycopg2
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import rcParams

def load_stock_targets(file_path):
    """讀取股票代碼與名稱對照表並預處理數據。"""
    stock_targets_df = pd.read_csv(file_path)
    stock_targets_df['stock_no'] = stock_targets_df['stock_no'].astype(str)
    stock_name_set = set(stock_targets_df['stock_name'])
    stock_no_set = set(stock_targets_df['stock_no'])
    stock_name_to_no = dict(zip(stock_targets_df['stock_name'], stock_targets_df['stock_no']))
    stock_no_to_name = dict(zip(stock_targets_df['stock_no'], stock_targets_df['stock_name']))
    return stock_name_set, stock_no_set, stock_name_to_no, stock_no_to_name

def verify_with_stock_targets(stock_target, stock_name_set, stock_no_set, stock_name_to_no, stock_no_to_name):
    """驗證並整理股票目標，返回 {股票代碼: 股票名稱} 的字典。"""
    if not stock_target:
        return {}
    elif stock_target in stock_name_set:
        stock_no = stock_name_to_no[stock_target]
        return {stock_no: stock_target}
    elif stock_target in stock_no_set:
        stock_name = stock_no_to_name[stock_target]
        return {stock_target: stock_name}
    else:
        return {}

def fetch_records(conn, sql_query):
    """從資料庫中提取記錄。"""
    with conn.cursor() as cur:
        cur.execute(sql_query)
        return cur.fetchall()

def process_records(records, stock_name_set, stock_no_set, stock_name_to_no, stock_no_to_name):
    """處理資料庫記錄，提取並驗證股票目標和市場情緒。"""
    result_stock_targets_list = []
    for record in records:
        current_paragraph_stock_target = record[14]
        comments = record[8]
        for comment in comments:
            stock_comment = comment.get('comment')
            stock_targets = comment.get('stock_targets', [])
            stock_sentiment = comment.get('stock_sentiment', 0)
            result_stock_targets = {}
            for stock_target in stock_targets:
                if isinstance(stock_target, str):
                    verified_target = verify_with_stock_targets(
                        stock_target, stock_name_set, stock_no_set, stock_name_to_no, stock_no_to_name
                    )
                    result_stock_targets.update(verified_target)
                elif isinstance(stock_target, dict):
                    key, value = next(iter(stock_target.items()))
                    verified_target = verify_with_stock_targets(
                        key, stock_name_set, stock_no_set, stock_name_to_no, stock_no_to_name
                    )
                    if not verified_target:
                        verified_target = verify_with_stock_targets(
                            value, stock_name_set, stock_no_set, stock_name_to_no, stock_no_to_name
                        )
                    result_stock_targets.update(verified_target)
            if isinstance(current_paragraph_stock_target, dict):
                result_stock_targets.update(current_paragraph_stock_target)
            result_stock_targets_list.append({
                "stock_comment": stock_comment,
                "stock_target": result_stock_targets,
                "stock_sentiment": stock_sentiment
            })
    return result_stock_targets_list

def organize_data(result_stock_targets_list):
    """統計每個公司出現的次數並加總市場情緒分數。"""
    organized_data = {}
    for item in result_stock_targets_list:
        stock_sentiment = item.get('stock_sentiment', 0)
        stock_target = item.get('stock_target', {})
        for stock_no, stock_name in stock_target.items():
            if stock_no not in organized_data:
                organized_data[stock_no] = {
                    'stock_name': stock_name,
                    'count': 0,
                    'stock_sentiment': 0
                }
            organized_data[stock_no]['count'] += 1
            organized_data[stock_no]['stock_sentiment'] += stock_sentiment
    return organized_data

def plot_counts_and_sentiments(companies, counts, sentiments):
    """在一張圖中繪製公司名稱出現次數和市場情緒，兩者皆為柱狀圖，並在 y=0 處加上紅色線條。"""
    rcParams['font.family'] = 'Arial Unicode MS'
    fig, ax1 = plt.subplots(figsize=(12, 8))

    # 左側 Y 軸 - 出現次數
    color_counts = 'tab:blue'
    bars1 = ax1.bar(companies, counts, width=0.4, color=color_counts, alpha=0.6, label='出現次數')
    ax1.set_xlabel('公司名稱', fontsize=12)
    ax1.set_xticks(range(len(companies)), [label[:4] + '\n' + label[4:] if len(label) > 3 else label for label in companies], rotation=0, fontsize=8)
    ax1.set_ylabel('次數', fontsize=12, color=color_counts)
    ax1.tick_params(axis='y', labelcolor=color_counts)
    # 在每個柱狀圖上顯示次數數值
    for bar in bars1:
        yval = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2, yval + max(counts)*0.005, int(yval), ha='center', va='bottom', color=color_counts)

    # 右側 Y 軸 - 市場情緒
    ax2 = ax1.twinx()
    color_sentiments = 'tab:red'
    bars2 = ax2.bar(companies, sentiments, width=0.1, color=color_sentiments, alpha=0.6, label='市場情緒')
    ax2.set_ylabel('市場情緒', fontsize=12, color=color_sentiments)
    ax2.tick_params(axis='y', labelcolor=color_sentiments)
    ax2.axhline(y=0, color='red', linestyle='--')
    # 在每個柱狀圖上顯示市場情緒數值
    for bar in bars2:
        yval = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2, yval, f'{yval:.3f}', ha='center', va='bottom', color="black")

    # 添加圖例
    ax1.legend(loc='upper center', bbox_to_anchor=(0.1, 1.055))
    ax2.legend(loc='upper center', bbox_to_anchor=(0.9, 1.055))

    plt.title("留言提及公司的次數與該公司市場情緒", fontsize=16)
    fig.tight_layout()
    plt.show()

def plot_counts(companies, counts):
    """繪製公司名稱出現次數的柱狀圖。"""
    rcParams['font.family'] = 'Arial Unicode MS'
    plt.figure(figsize=(12, 8))
    bars = plt.bar(companies, counts, color='b', alpha=0.6)
    plt.xlabel("公司名稱", fontsize=12)
    plt.ylabel("次數", fontsize=12, color='b')
    plt.title("公司名稱出現次數統計", fontsize=16)
    plt.xticks(rotation=0, fontsize=8)
    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2, yval + max(counts)*0.005, int(yval), ha='center', va='bottom')
    plt.tight_layout()
    plt.show()

def plot_sentiments(companies, sentiments):
    """繪製市場情緒的柱狀圖。"""
    rcParams['font.family'] = 'Arial Unicode MS'
    plt.figure(figsize=(12, 8))
    bars = plt.bar(companies, sentiments, color='r', alpha=0.6)
    plt.xlabel("公司名稱", fontsize=12)
    plt.ylabel("市場情緒", fontsize=12, color='r')
    plt.title("公司名稱市場情緒", fontsize=16)
    plt.axhline(y=0, color='red', linestyle='--')
    plt.xticks(rotation=0, fontsize=8)
    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2, yval + max(sentiments)*0.005, f'{yval:.3f}', ha='center', va='bottom')
    plt.tight_layout()
    plt.show()

def show_market_overview():
    # 連接資料庫
    conn = psycopg2.connect(
        user="root",
        password="root",
        host="localhost",
        port="5433",
        database="postgres"
    )
    # 讀取股票代碼與名稱對照表
    stock_targets_file_path = "/Users/uncleben006/nextgen/code/python/ptt_stock_vane_api/config/data/stock_targets.csv"
    stock_name_set, stock_no_set, stock_name_to_no, stock_no_to_name = load_stock_targets(stock_targets_file_path)
    # 提取資料庫記錄
    sql_query = """
        SELECT * FROM public.ptt_stock_paragraphs
        WHERE paragraph_published_time BETWEEN '2024-08-01' AND '2024-08-07' 
        AND paragraph_tag NOT IN ('新聞','請益','創作','心得','閒聊')
        AND paragraph_title NOT LIKE '%創作%'
        AND paragraph_content NOT LIKE '%水桶%'
        AND done_analyze = True
        ORDER BY paragraph_published_time DESC
    """
    records = fetch_records(conn, sql_query)
    conn.close()
    # 處理記錄並組織數據
    result_stock_targets_list = process_records(
        records, stock_name_set, stock_no_set, stock_name_to_no, stock_no_to_name
    )
    organized_data = organize_data(result_stock_targets_list)
    # 移除特定股票代碼
    organized_data.pop('3167', None)
    # 準備數據進行繪圖
    sorted_data = sorted(organized_data.items(), key=lambda item: item[1]['count'], reverse=True)
    counts = [item[1]['count'] for item in sorted_data]
    companies = [item[1]['stock_name'] for item in sorted_data]
    sentiments = [item[1]['stock_sentiment'] / item[1]['count'] for item in sorted_data]
    # 取前 20 名
    top_n = 20
    limited_counts = counts[:top_n]
    limited_companies = companies[:top_n]
    limited_sentiments = sentiments[:top_n]
    # 繪製圖表
    plot_counts_and_sentiments(limited_companies, limited_counts, limited_sentiments)
    # plot_counts(limited_companies, limited_counts)
    # plot_sentiments(limited_companies, limited_sentiments)

if __name__ == "__main__":
    show_market_overview()
