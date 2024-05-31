
# 主要先用 spacy 將留言分析一遍，找出裡面可能提及公司的火星文
# 手動將火星文翻譯成中文，
# 做成字典，然後再確認一次所有留言到底提過哪些公司標的，存進資料庫，
# 這樣 GPT 分析出來的 sentiment 才能夠對應到應該有的公司。

import spacy
from datetime import datetime
from typing import List, Dict

class PttStockCommentsAnalyzer():

    def __init__(self):
        self.nlp_zh = spacy.load("zh_core_web_trf") # 載入 spacy 模型

    # 從資料庫取出一段時間的留言，並組成一個 list
    def fetch_comments_from_db(self, start_date: datetime, end_date: datetime) -> List[str]:
        # 模擬從資料庫中提取留言，這裡使用靜態列表代替
        # 實際實現中應根據 start_date 和 end_date 從資料庫中查詢
        comments = [
            "今天看好台積電的股價",
            "鴻海的業績表現不錯",
            "鰻魚大家都不要了",
            "6147調整中",
            "99國統",
            "居然沒永信建",
            "小兒狂買成熟製程 又有fu糗了",
            "金居被倒貨",
            "良維誰拉尾盤?",
            "鰻魚飯臭酸了",
            "雙鴻是當作買菜嗎",
            "大哥拿烏龜進補",
            "臭酸的鰻魚飯，還好我空了嘻嘻",
            "大哥不要了 99良維"
        ]
        return comments
    
    # 丟進 spacy 分析
    def analyze_comments(self, comments: List[str]) -> List[Dict[str, str]]:
        results = []
        for comment in comments:
            doc = self.nlp_zh(comment)
            print(doc)
            # entities = [{"text": ent.text, "label": ent.label_} for ent in doc.ents if ent.label_ in ["ORG", "GPE"]]
            # results.append({"comment": comment, "entities": entities})
        return results

    # 存進 json 檔案
    def save_results_to_json(self, data: List[Dict[str, str]], filename: str):
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)


    def analyze_and_save(self, start_date: datetime, end_date: datetime, filename: str):
        comments = self.fetch_comments_from_db(start_date, end_date)
        analyzed_comments = self.analyze_comments(comments)
        # self.save_results_to_json(analyzed_comments, filename)