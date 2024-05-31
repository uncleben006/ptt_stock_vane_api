import json
from datetime import datetime
from ptt_stock_vane_api.models import PttStockParagraphs

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain.memory import ChatMessageHistory

class Commet(BaseModel):
    sentiment: str = Field(description="stock sentiment of the comment")
    stock_targets: str = Field(description="translated text")

def update_stock_sentiments():

    # Format
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", """
                你是一個股票漲跌情緒分析器，你會做兩件事情。
                1. 你會回覆-1到1之間的浮點數，分析該留言是「看空」還是「看漲」，越看漲分數越接近1，越看空分數越接近-1。
                2. 論壇內有許多公司代稱，
                我將給你一段股票論壇中的留言，內容會包含許多回覆之前請仔細思考一下語句當中是否有反諷刺成分存在。
            """),
            ("human", "{comment}")
        ]
    )

    # Predict
    model = ChatOpenAI(model_name="gpt-3.5-turbo-0125", temperature=0)

    # Parser
    parser = JsonOutputParser(pydantic_object=Commet)

    # Chain
    chain = ( prompt | model | parser )

    # Comments data
    comments = [
        "鰻魚大家都不要了",
        # "6147調整中",
        # "99國統",
        # "居然沒永信建",
        # "小兒狂買成熟製程 又有fu糗了",
        # "金居被倒貨",
        # "良維誰拉尾盤?",
        # "鰻魚飯臭酸了",
        # "雙鴻是當作買菜嗎",
        # "大哥拿烏龜進補",
        # "臭酸的鰻魚飯，還好我空了嘻嘻",
        # "大哥不要了 99良維",
        # "6667投信連買幾天了？",
        # "鰻魚被大哥小兒聯手賣臭酸了嗎？",
        # "康和證QQ",
        # "到底盤中哪個阿呆一直講小兒買金居的",
        # "99光洋",
        # "850的雙鴻當便當再買",
        # "難怪新聞一直吹 銅價",
        # "買這麼多台星？",
        # "小兒被大媽無情教訓",
        # "電子股慘cc",
        # "2024年 就佔了4個了 外資 慢慢回來喔",
        # "都買權值",
        # "2024就是拿來刷榜的XD"
    ]

    for comment in comments:
        response = chain.invoke({"comment": comment})
        
    print(response)

    # TODO: 我應該要先將留言用 spacy 分析過一遍，找出裡面的火星文，手動將火星文翻譯成中文，
    # 做成字典，然後再確認一次所有留言到底提過哪些公司標的，存進資料庫，
    # 這樣 GPT 分析出來的 sentiment 才能夠對應到應該有的公司。

    # # Append into prompt
    # prompt.append(("human", "這支股票最近一直在跌，我覺得它還會繼續跌。"))

    # # 查看 prompt 中的所有消息
    # for comment in comments:
    #     print(message)

    

# print(prompt)

# # 設定文章範圍
# start_of_2024 = datetime(2024, 1, 1)
# end_of_2024 = datetime(2024, 1, 2)

# query = {
#   "$and":[
#     { "paragraph_published_time": { "$gt": start_of_2024 } },
#     { "paragraph_published_time": { "$lt": end_of_2024 } }
#   ]
# }

# for paragraph in paragraphs_collection.find(query).sort("paragraph_published_time", -1):
#   # print(paragraph["paragraph_published_time"], end=" ")
#   # print(paragraph["paragraph_title"])
#   # print(paragraph["paragraph_content"])

#   # 將文章內容拆成多個小段落
#   text_segments = text_splitter.split_text(paragraph["paragraph_content"])
#   print('The documents be split into: ', len(text_segments))

#   stock_targets = []
#   for segment in text_segments:
#     print("segment length:",len(segment))
#     response = chain.invoke({"text_segment": segment})
#     print("response:",response)
#     stock_targets = stock_targets + response
#   print("stock_targets:",stock_targets)
#   paragraphs_collection.update_one({"_id": paragraph["paragraph_link"]}, {"$set": {"stock_targets": stock_targets}})

#   # for comment in paragraph["comments"]:
#   #   print(comment["comment"]) 