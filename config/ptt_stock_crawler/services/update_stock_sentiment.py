import os
import json
import random
import logging
import warnings
import psycopg2
import concurrent.futures
import threading
from openai import AssistantEventHandler, OpenAI
from typing_extensions import override

warnings.filterwarnings("ignore", category=FutureWarning)
logging.getLogger().setLevel(logging.ERROR)

# 建立 OpenAI 連線
client = OpenAI()
ptt_stock_analyzer_asst_id = os.getenv("ASSISTANT_ID")

def process_comment_batch(comment_batch, max_retries=3):
    """
    處理單一批次的留言分析。
    若已分析過則直接回傳 comment_batch。
    若未分析則呼叫 GPT 服務，將結果更新回 comment_batch 後回傳。
    分析失敗超過 max_retries 次會拋出錯誤。
    """
    retry_count = 0
    while retry_count < max_retries:
        try:
            # 若該批次已經分析過，直接跳過不再呼叫 API
            if all("stock_sentiment" in c and "stock_targets" in c for c in comment_batch):
                print("留言已分析，跳過")
                return comment_batch

            # 未分析則呼叫 API 分析
            comment_batch_content = {index: comment for index, comment in enumerate(comment_batch)}
            message_thread = client.beta.threads.create(messages=[{"role": "user", "content": str(comment_batch)}])
            with client.beta.threads.runs.stream(
                thread_id=message_thread.id,
                assistant_id=ptt_stock_analyzer_asst_id,
            ) as stream:
                stream.until_done()

                # 取得分析結果
                try:
                    batch_analyze_results = json.loads(stream.current_message_snapshot.content[0].text.value)
                except Exception as e:
                    raise ValueError("分析失敗，請重新檢查")

                # 檢查回傳結果數量是否正確
                if len(batch_analyze_results) != len(comment_batch_content):
                    raise ValueError("輸入留言與回傳數量不一致，請檢查")

                # # 顯示部分分析結果
                # print("{", batch_analyze_results["0"], "...", batch_analyze_results[list(batch_analyze_results)[-1]], "}", flush=True)
                # print("傳入留言數：", len(comment_batch_content))
                # print("傳出留言數：", len(batch_analyze_results))

                # 將分析結果寫回 comment_batch
                for k, comment in enumerate(comment_batch):
                    comment["stock_sentiment"] = batch_analyze_results[str(k)]["stock_sentiment"]
                    comment["stock_targets"] = batch_analyze_results[str(k)]["stock_targets"]

                return comment_batch

        except ValueError as e:
            retry_count += 1
            print(f"發生錯誤: {e}，重試 {retry_count} 次當前批次...")
            if retry_count >= max_retries:
                print("已達到最大重試次數，請確認留言是否正確。")
                # 超過重試次數，拋出例外由外層處理停止整個流程
                raise


def update_stock_sentiment():
    # 建立資料庫連線
    conn = psycopg2.connect(user="root", password="root", host="localhost", port="5433", database="postgres")
    cur = conn.cursor()
    sql = """SELECT * FROM public.ptt_stock_paragraphs
                WHERE paragraph_published_time BETWEEN '2024-08-01' AND '2024-08-07' 
                AND paragraph_tag NOT IN ('新聞','請益','創作','心得','閒聊')
                AND paragraph_title NOT LIKE '%創作%'
                AND paragraph_content NOT LIKE '%水桶%'
                AND done_analyze = False
                AND id != 153570
                ORDER BY paragraph_published_time DESC
            """
    cur.execute(sql)
    records = cur.fetchall()
    batch_size = 45
    stop_event = threading.Event()  # 用於中斷後續處理

    for record in records:
        if stop_event.is_set(): break

        paragraph_id = record[0]
        paragraph_link = record[1]
        paragraph_title = record[3]
        comments = record[8]

        # 印出正在分析的文章資訊
        print(f"分析文章: {paragraph_id} {paragraph_title}")
        print(f"文章連結: {paragraph_link}")
        print(f"總留言數: {len(comments)}")

        # 將留言切成多個批次
        all_batches = []
        for i in range(0, len(comments), batch_size):
            all_batches.append((i, comments[i:i+batch_size]))

        # 使用多執行緒同時處理多個批次
        with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
            future_to_batch_index = {}
            for batch_index, comment_batch in all_batches:
                if stop_event.is_set(): break
                future = executor.submit(process_comment_batch, comment_batch)
                future_to_batch_index[future] = batch_index
                print(f"多線程處理批次: {batch_index}")

            # 等待所有批次完成
            for future in concurrent.futures.as_completed(future_to_batch_index):
                batch_index = future_to_batch_index[future]
                if stop_event.is_set(): break
                try:
                    batch_result = future.result()
                    # 將該批次更新回原本的 comments 列表中
                    for k, c in enumerate(batch_result):
                        comments[batch_index + k] = c

                    # 顯示已經有多少留言分析完成
                    print(f"批次號: {batch_index}")
                    print(f"批次留言數: {len(batch_result)}")
                    print(f"所有留言數: {len(comments)}")
                    print(f"總分析留言: {len([comment for comment in comments if "stock_sentiment" in comment])}")
                    print(f"[{batch_result[0]} ... {batch_result[-1]}]", flush=True)
                    print("=============================================")
                except Exception as exc:
                    # 若有一批次發生錯誤，設定 stop_event 並結束
                    print(f"批次 {batch_index} 分析失敗，原因: {exc}")
                    stop_event.set()
                    # 取消未執行的任務（如有必要）
                    for f in future_to_batch_index:
                        if not f.done():
                            f.cancel()
                    break

        # 若 stop_event 被設定，則停止後續處理
        if stop_event.is_set(): break

        # 檢查是否所有留言都分析完成
        if all("stock_sentiment" in c and "stock_targets" in c for c in comments):
            # 全部成功，更新資料庫
            sql = "UPDATE public.ptt_stock_paragraphs SET comments = %s, done_analyze = True WHERE id = %s"
            cur.execute(sql, (json.dumps(comments, ensure_ascii=False), paragraph_id))
            conn.commit()
            print("留言已全數分析，標記為分析完畢")
        else:
            # 部分失敗
            raise ValueError("留言未全數分析，請重新檢查。")

        print("=============================================")

    cur.close()
    conn.close()
