import os
import json
import random
import logging
import warnings
import psycopg2
from openai import AssistantEventHandler, OpenAI
from typing_extensions import override

# 忽略所有 FutureWarning
# 設置所有日誌級別為 ERROR
warnings.filterwarnings("ignore", category=FutureWarning)
logging.getLogger().setLevel(logging.ERROR)

# 建立 OpenAI 連線
client = OpenAI()
ptt_stock_analyzer_asst_id = os.getenv("ASSISTANT_ID")

# 建立自訂義事件處理器客製 Assistant 行為
class EventHandler(AssistantEventHandler):

    @override
    def on_tool_call_created(self, tool_call):
        print(f"assistant > {tool_call.type} ...", flush=True)
    
    @override
    def on_message_done(self, message) -> None:
        # print a citation to the file searched
        message_content = message.content[0].text
        annotations = message_content.annotations
        citations = []
        for index, annotation in enumerate(annotations):
            message_content.value = message_content.value.replace(
                annotation.text, f"[{index}]"
            )
            if file_citation := getattr(annotation, "file_citation", None):
                cited_file = client.files.retrieve(file_citation.file_id)
                citations.append(f"[{index}] {cited_file.filename}")


def update_stock_sentiment():

    # 建立連線
    # TODO: 改成 Django ORM
    conn = psycopg2.connect( user="root", password="root", host="localhost", port="5433", database="postgres" )
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

    # 每 45 個留言一批傳進 GPT-4o-mini 分析，測試發現傳太多資料模型容易失焦，45 是一個比較穩定的數量
    batch_size = 45
    for record in records:
        paragraph_id = record[0]
        paragraph_link = record[1]
        paragraph_title = record[3]
        comments = record[8]
        comments_analyze_results = []

        # 將留言分批傳入 GPT-4o-mini 分析
        for i in range(0, len(comments), batch_size):
            print(f"分析文章: {paragraph_id} {paragraph_title}")
            print(f"文章連結: {paragraph_link}")
            comment_batch = comments[i:i+batch_size]
            comment_batch_content = {index:comment for index, comment in enumerate(comment_batch)}

            # 若這批已經分析過，則印出後跳過
            if all("stock_sentiment" in comment and "stock_targets" in comment for comment in comment_batch):
                comments_analyze_results += comment_batch
                # print(comment_batch)
                print(f"總更新留言數: {len(comments_analyze_results)}")
                print(f"留言已分析，跳過")
                print("=============================================")
                continue

            # 使用 Stream SDK 搭配自定義 EventHandler 來創建 Run 並串流返回的結果
            message_thread = client.beta.threads.create( messages=[{"role": "user", "content": str(comment_batch) }] )
            with client.beta.threads.runs.stream(
                thread_id=message_thread.id,
                assistant_id=ptt_stock_analyzer_asst_id,
                event_handler=EventHandler(),
            ) as stream:
                stream.until_done()
                try:
                    batch_analyze_results = json.loads(stream.current_message_snapshot.content[0].text.value)
                except Exception as e:
                    raise ValueError("分析失敗，請重新檢查。") from e
                if len(batch_analyze_results) != len(comment_batch_content):
                    raise ValueError("輸入留言與回傳數量不一致，請檢查。")     
                
                print("傳入留言數：",len(comment_batch_content))
                print("傳出留言數：",len(batch_analyze_results))
                print("{",batch_analyze_results["0"],"...",batch_analyze_results[list(batch_analyze_results)[-1]],"}", end="\n\n", flush=True)
                comments_analyze_results += [comment for index, comment in batch_analyze_results.items()]

            # 為了節省 token，模型回傳的留言結果不會包含一些原始資訊，故需要將這些資訊加回才算一筆完整分析完畢的留言
            for k, comment in enumerate(comment_batch):
                comments[i+k]["stock_sentiment"] = comments_analyze_results[i+k]["stock_sentiment"]
                comments[i+k]["stock_targets"] = comments_analyze_results[i+k]["stock_targets"]
            
            # 每次輸出的留言太穩定了，所以只要輸出的數量是正確的，就直接更新資料庫
            sql = "UPDATE public.ptt_stock_paragraphs SET comments = %s WHERE id = %s"
            cur.execute(sql, (json.dumps(comments, ensure_ascii=False), paragraph_id))
            conn.commit()
            print(f"更新文章: {paragraph_id} {paragraph_title}")
            print(f"總留言數: {len(comments)}")
            print(f"總更新留言數: {len(comments_analyze_results)}")
            print("=============================================")

        # 留言已全數分析，將此篇文章標記為已完成分析
        if len(comments_analyze_results) == len(comments):
            print("留言已全數分析，標記為分析完畢")
            sql = "UPDATE public.ptt_stock_paragraphs SET done_analyze = %s WHERE id = %s"
            cur.execute(sql, (True, record[0]))
            conn.commit()
        else:
            raise ValueError("留言未全數分析，請重新檢查。") 
        print("=============================================")

    cur.close()
    conn.close()
