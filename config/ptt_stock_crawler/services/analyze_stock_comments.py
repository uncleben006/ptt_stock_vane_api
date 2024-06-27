import os
import spacy

from datetime import datetime
from django.conf import settings
from langchain_openai import OpenAIEmbeddings
from ptt_stock_vane_api.models import PttStockParagraphs
from qdrant_client import QdrantClient
from langchain_qdrant import Qdrant
from qdrant_client.http import models
from ptt_stock_crawler.services.update_stock_paragraphs import PttStockCrawler


    # 要想辨識出留言當中的股票，有幾個方法可以嘗試

    # 1. 做一個股票字典，將所有股票代碼、名稱、簡稱、綽號 都列出來，只要留言有提到的，就代表留言有提到該支股票
    # 1-1. 事實證明這個方法不太好，因為留言中提到股票時，綽號太多，撇開綽號不談有些股票名也跟一般文字重疊，容易混淆，例如 世界先進、綠電、鰻魚 等等

    # 2. NER 命名實體識別：用 NER 模型來辨識留言中提到公司、機構、組織的詞彙，再搭配上一點的股票字典，有匹配就代表留言有提到該支股票
    # 2-1. 這個方法理論上可行，但我選用的 Spacy 模型有時判斷不準確，例如這則留言「長榮送分題300起 陽明100 順勢抱緊加碼」
    # Spacy 應該要將「長榮」判斷成 ORG，但實際上只有判斷出以下結果「300起 QUANTITY」「陽明 ORG」
    # ```
    # nlp_zh = spacy.load("zh_core_web_trf")
    # spacy_comment = nlp_zh('長榮送分題300起 陽明100 順勢抱緊加碼')
    # for ent in spacy_comment.ents:
    #     print(ent, ent.label_)
    # ```
    # 可能要用現有的留言餵進 GPT 4 取得資料後，進行監督式學習 fine tune Spacy 模型，再拿來使用才會比較準確
    # 缺點：要正確判斷詞彙詞性，並且要匹配股票字典，所以可能會漏掉一些留言提到的股票標的
    # 優點：經過兩次篩選，最後判斷的結果正確度高，不會有太多誤判

    # 3. RAG 架構：將股票字典轉成 Embedding，詢問 GPT 時先將留言文字轉成放入向量資料庫比對，
    # 取最相似的資料放入 prompt 中一齊詢問 GPT，讓 GPT 判斷留言是否有提到股票以及留言對市場的情緒分數。

    # 3-1. 這個方法理論上可行，但經過測試發現用留言去比對股票字典時常會有誤判，
    # 例如這則留言「GG九月不是有除息行情 怎麼」照理提到「GG」應該要匹配字典中的「台積電」綽號，但卻是以下結果(最相近五名)
    # no: 890B
    # name: 凱基ESGBBB債15+
    # score: 0.41803676
    # no: 00890B
    # name: 凱基ESGBBB債15+
    # score: 0.41031525
    # no: 874B
    # name: 凱基BBB公司債15+
    # score: 0.4020667
    # no: 00779B
    # name: 凱基美債25+
    # score: 0.39041612
    # no: 00874B
    # name: 凱基BBB公司債15+
    # score: 0.39025843 

    # 而這則留言「3715不翻黑是吧 來補一補」，應該匹配到字典中的 3715 也就是「定穎投控」，但卻是以下結果(最相近五名)
    # no: 3028
    # name: 增你強
    # score: 0.39106822
    # no: 3015
    # name: 全漢
    # score: 0.38480386
    # no: 6625
    # name: 必應
    # score: 0.38193548
    # no: 4155
    # name: 訊映
    # score: 0.38128218
    # no: 6015
    # name: 宏遠證
    # score: 0.37946245


    # 應該也沒什麼副作用。就是會多花一些 Embedding API 的費用。
    # 但因為我們只是要取最相似的資料，不用多高的準確度，所以用最便宜的 Embedding API 就可以了，
    # 最便宜的 Embedding model 是 text-embedding-3-small US$0.00002 / 1K tokens，
    # 過去半年股票論壇中留言的 token 總數大約 40000000(四千萬)個，換算費用大約是 US$0.8。
    # 優點：不會有太多誤判，且不會漏掉太多留言提到的股票標的


def analyze_stock_comments():

    # 從 DB 取得 2024-01-01~2024-01-02 的文章
    start_of_2024 = datetime(2024, 1, 1)
    end_of_2024 = datetime(2024, 1, 2)
    paragraphs = PttStockParagraphs.objects.filter(paragraph_published_time__gt=start_of_2024, paragraph_published_time__lt=end_of_2024)

    # Init QdrantClient
    embeddings_model = OpenAIEmbeddings(model="text-embedding-3-large")
    client = QdrantClient()
    collection_name = "stock_targets_large"
    qdrant = Qdrant(client, collection_name, embeddings_model)

    # TODO: 要研究一下讓模型處理兩個任務還是一個任務，處理一個任務會不會正確率更高

    # prompt = 你有兩個任務，1. 依照 target 裡的資訊來判斷此留言是否有提到台灣股票
    # 2. 依照留言的內容仔細判斷此留言的市場情緒是正面還是負面
    # <context>
    # {context}
    # </context>
    # Question: {input}

    
            
    # retriever = qdrant.as_retriever(search_kwargs=dict(
    #     filter=models.Filter(
    #         must=[
    #             models.FieldCondition(
    #                 key="metadata.department",
    #                 match=models.MatchValue(value="MRT")
    #             )
    #         ]
    #     )
    # ))

    result = qdrant.similarity_search_with_score(
        # query="原來這是鴻海股價這麼強的秘密", 
        # query="阿姨宇宙夢都沒有一個成形",
        # query="GG九月不是有除息行情 怎麼",
        # query="GG這個量 超窒息",
        query="3715不翻黑是吧 來補一補",
        k=5,
        filter=models.Filter(
            must=[
                models.FieldCondition(
                    key="metadata.type", match=models.MatchValue(value="stock_target",)
                ),
            ]
        )
    )
    for item in result:
        # print(item)
        print(item[0].page_content)
        print("score:",item[1])
    # print(result)

# class CommetResult(BaseModel):
#     sentiment: str=Field(description="stock sentiment of the comment")
#     stock_targets: str=Field(description="translated text")



# def update_stock_sentiments():

#     # Format
#     prompt = ChatPromptTemplate.from_messages(
#         [
#             ("system", """
#                 你是一個股票漲跌情緒分析器，你會做兩件事情。
#                 1. 你會回覆-1到1之間的浮點數，分析該留言是「看空」還是「看漲」，越看漲分數越接近1，越看空分數越接近-1。
#                 2. 論壇內有許多公司代稱，
#                 我將給你一段股票論壇中的留言，內容會包含許多回覆之前請仔細思考一下語句當中是否有反諷刺成分存在。
#             """),
#             ("human", "{comment}")
#         ]
#     )

#     # Predict
#     model = ChatOpenAI(model_name="gpt-3.5-turbo-0125", temperature=0)

#     # Parser
#     parser = JsonOutputParser(pydantic_object=Commet)

#     # Chain
#     chain = ( prompt | model | parser )

#     # Comments data
#     comments = [
#         "鰻魚大家都不要了",
#         # "6147調整中",
#         # "99國統",
#         # "居然沒永信建",
#         # "小兒狂買成熟製程 又有fu糗了",
#         # "金居被倒貨",
#         # "良維誰拉尾盤?",
#         # "鰻魚飯臭酸了",
#         # "雙鴻是當作買菜嗎",
#         # "大哥拿烏龜進補",
#         # "臭酸的鰻魚飯，還好我空了嘻嘻",
#         # "大哥不要了 99良維",
#         # "6667投信連買幾天了？",
#         # "鰻魚被大哥小兒聯手賣臭酸了嗎？",
#         # "康和證QQ",
#         # "到底盤中哪個阿呆一直講小兒買金居的",
#         # "99光洋",
#         # "850的雙鴻當便當再買",
#         # "難怪新聞一直吹 銅價",
#         # "買這麼多台星？",
#         # "小兒被大媽無情教訓",
#         # "電子股慘cc",
#         # "2024年 就佔了4個了 外資 慢慢回來喔",
#         # "都買權值",
#         # "2024就是拿來刷榜的XD"
#     ]

#     for comment in comments:
#         response = chain.invoke({"comment": comment})
        
#     print(response)

#     # TODO: 我應該要先將留言用 spacy 分析過一遍，找出裡面的火星文，手動將火星文翻譯成中文，
#     # 做成字典，然後再確認一次所有留言到底提過哪些公司標的，存進資料庫，
#     # 這樣 GPT 分析出來的 sentiment 才能夠對應到應該有的公司。

#     # # Append into prompt
#     # prompt.append(("human", "這支股票最近一直在跌，我覺得它還會繼續跌。"))

#     # # 查看 prompt 中的所有消息
#     # for comment in comments:
#     #     print(message)

    

# # print(prompt)

# # # 設定文章範圍
# # start_of_2024 = datetime(2024, 1, 1)
# # end_of_2024 = datetime(2024, 1, 2)

# # query = {
# #   "$and":[
# #     { "paragraph_published_time": { "$gt": start_of_2024 } },
# #     { "paragraph_published_time": { "$lt": end_of_2024 } }
# #   ]
# # }

# # for paragraph in paragraphs_collection.find(query).sort("paragraph_published_time", -1):
# #   # print(paragraph["paragraph_published_time"], end=" ")
# #   # print(paragraph["paragraph_title"])
# #   # print(paragraph["paragraph_content"])

# #   # 將文章內容拆成多個小段落
# #   text_segments = text_splitter.split_text(paragraph["paragraph_content"])
# #   print('The documents be split into: ', len(text_segments))

# #   stock_targets = []
# #   for segment in text_segments:
# #     print("segment length:",len(segment))
# #     response = chain.invoke({"text_segment": segment})
# #     print("response:",response)
# #     stock_targets = stock_targets + response
# #   print("stock_targets:",stock_targets)
# #   paragraphs_collection.update_one({"_id": paragraph["paragraph_link"]}, {"$set": {"stock_targets": stock_targets}})

# #   # for comment in paragraph["comments"]:
# #   #   print(comment["comment"]) 