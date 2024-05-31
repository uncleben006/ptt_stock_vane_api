from datetime import datetime
from django.core.management.base import BaseCommand
from ptt_stock_crawler.services.analyze_ptt_commet_stock_target import PttStockCommentsAnalyzer

class Command(BaseCommand):

    # 因為留言當中有太多公司名稱代稱，如「鰻魚代表元太」、「GG代表台積」、「螃蟹代表瑞昱」、「紅茶代表HTC」，
    # 故需要用 spacy 分析出裡面可能提及公司詞彙，並手動將這些詞翻譯對應到公司名稱並做成字典，
    # 最後分析出每一則留言都提過哪些公司標的，並更新資料庫，
    # 這樣 GPT 分析留言得出的股市情緒才能夠反應到對應的公司。

    help = 'Fetches stock targets from a remote API and inserts them into the database'

    def handle(self, *args, **kwargs):
        analyzer = PttStockCommentsAnalyzer()
        start_date = datetime.strptime("2024-01-01", "%Y-%m-%d")
        end_date = datetime.now()
        analyzer.analyze_and_save(start_date, end_date, "comments_analysis.json")