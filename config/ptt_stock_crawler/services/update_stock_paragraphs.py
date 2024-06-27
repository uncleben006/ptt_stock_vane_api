import os
import re
import json
import requests
import hashlib
import spacy
from bs4 import BeautifulSoup
from datetime import datetime
from cachetools import LRUCache
from django.db import connection, transaction
from ptt_stock_vane_api.models import PttStockParagraphs, PttStockTargets
from transformers import GPT2Tokenizer
from concurrent.futures import ThreadPoolExecutor
import warnings

# ignore future warning
warnings.filterwarnings("ignore", category=FutureWarning)


# 股版爬蟲
class PttStockCrawler():

    def __init__(self, page_url="https://www.ptt.cc/bbs/Stock/index.html", past_pages=50):
        self.page_url = page_url
        self.past_pages = past_pages
        self.get_stock_targets_dicts() # 取得股票代碼和名稱
        self.get_end_index() # 取得最後一頁的編號
        self.start_index = self.end_index - self.past_pages
        self.nlp_zh = spacy.load("zh_core_web_trf") # 載入 spacy 模型

    # 傳入股版頁面網址，返回該頁面所有文章連結
    def get_post_links(self):
        response = requests.get(self.page_url)
        soup = BeautifulSoup(response.text, "html.parser")
        links = soup.find_all("div", class_="title")
        return ["https://www.ptt.cc" + link.a["href"] for link in links if link.a]

    # 傳入文章連結，多線程抓取文章內容
    def crawl_paragraphs(self, links):
    
        # 建立快取以紀錄最後一篇文章的發布時間
        cache = LRUCache(maxsize=1)

        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(self.scrape, link) for link in links]
            for i, future in enumerate(futures):
                result = future.result()
                print(result["paragraph_link"], result["status"], end=" ")
                paragraph = PttStockParagraphs.objects.filter(paragraph_link=result["paragraph_link"]).first()

                # 若文章存在於資料庫中，但抓下的文章狀態為 502，則新增
                if not paragraph and result["status"] == "502": 
                    print("INSERT")
                    new_paragraph = PttStockParagraphs(
                        paragraph_link=result["paragraph_link"],
                        status=result["status"],
                        md5_hash=result["md5_hash"],
                        page_url=self.page_url
                    )
                    new_paragraph.save()
                    continue

                # 若資料庫中沒有該文章則新增
                if not paragraph:
                    print("INSERT")
                    new_paragraph = PttStockParagraphs(
                        paragraph_link=result["paragraph_link"],
                        paragraph_author=result["paragraph_author"],
                        paragraph_title=result["paragraph_title"],
                        paragraph_published_time=result["paragraph_published_time"],
                        paragraph_content=result["paragraph_content"],
                        paragraph_ip=result["paragraph_ip"],
                        paragraph_country=result["paragraph_country"],
                        comments=result["comments"],
                        status=result["status"],
                        md5_hash=result["md5_hash"],
                        paragraph_content_token_count=result["paragraph_content_token_count"],
                        comments_token_count=result["comments_token_count"],
                        paragraph_tag=result["paragraph_tag"],
                        paragraph_stock_targets=result["paragraph_stock_targets"],
                        page_url=self.page_url
                    )
                    new_paragraph.save()
                    continue

                # 若資料庫中的文章有 MD5 且完全匹配則直接跳過
                if paragraph.md5_hash == result["md5_hash"]:
                    print("MD5-MATCH, SKIP")
                    continue
                # 若文章存在於資料庫中，但抓下的文章狀態為 502，則跳過
                if paragraph and result["status"] == "502": 
                    print("STATUS-502, SKIP")
                    continue
                # 若資料庫中的文章與抓下的文章 MD5 不一致則更新
                if paragraph:
                    print("MD5-UNMATCH, UPDATE")
                    # print(json.dumps(result["comments"], ensure_ascii=False))
                    paragraph.paragraph_link = result["paragraph_link"]
                    paragraph.paragraph_author = result["paragraph_author"]
                    paragraph.paragraph_title = result["paragraph_title"]
                    paragraph.paragraph_published_time = result["paragraph_published_time"]
                    paragraph.paragraph_content = result["paragraph_content"]
                    paragraph.paragraph_ip = result["paragraph_ip"]
                    paragraph.paragraph_country = result["paragraph_country"]
                    paragraph.comments = result["comments"]
                    paragraph.status = result["status"]
                    paragraph.md5_hash = result["md5_hash"]
                    paragraph.paragraph_content_token_count = result["paragraph_content_token_count"]
                    paragraph.comments_token_count = result["comments_token_count"]
                    paragraph.paragraph_tag = result["paragraph_tag"]
                    paragraph.paragraph_stock_targets = result["paragraph_stock_targets"]
                    paragraph.page_url = self.page_url
                    paragraph.save()
                    continue

    # 爬取股版文章內容
    def scrape(self, url, cache=LRUCache(maxsize=1)):
        response = requests.get(url)
        if response.status_code != 200:
            return { "paragraph_link": url, "status": "502", "md5_hash": "None" }

        soup = BeautifulSoup(response.text, "html.parser")
        main_content = soup.find("div", id="main-content")

        # 解析出文章作者、標題、發佈時間
        paragraph_author = paragraph_title = paragraph_published_time = paragraph_content = "Unknown"
        metadatas = main_content.find_all("div", "article-metaline")
        for metadata in metadatas:
            if metadata.find("span", "article-meta-tag").text == "作者":
                paragraph_author = metadata.find("span", "article-meta-value").text
            if metadata.find("span", "article-meta-tag").text == "標題":
                paragraph_title = metadata.find("span", "article-meta-value").text
            if metadata.find("span", "article-meta-tag").text == "時間":
                paragraph_published_time = metadata.find("span", "article-meta-value").text
            try:
                paragraph_published_time = paragraph_published_time.replace('Tus', 'Tue')
                paragraph_published_time = datetime.strptime(paragraph_published_time, "%a %b %d %H:%M:%S %Y").strftime("%Y-%m-%d %H:%M:%S")
                paragraph_year = paragraph_published_time[:4]
                cache["last_paragraph_published_time"] = paragraph_published_time
            except:
                paragraph_published_time = cache.get("last_paragraph_published_time", "Unknown")
                paragraph_year = paragraph_published_time[:4]

        # 移除非必要文字
        for meta in main_content.find_all("div", "article-metaline"):
            meta.decompose()
        for meta in main_content.find_all("div", "article-metaline-right"):
            meta.decompose()

        # 解析出(推文之前的)文章內容
        end_of_content_index = main_content.text.rfind("\n--\n※ 發信站")
        paragraph_content = main_content.text[:end_of_content_index].strip()

        # 解析出文章 IP 和國家
        footer_info = main_content.find_all("span", "f2")
        paragraph_ip = "Unknown"
        paragraph_country = "Unknown"

        for info in footer_info:
            # print(info.text+"\n")
            if "來自" in info.text:
                paragraph_ip_match = re.search(r"來自: (\d+\.\d+\.\d+\.\d+)", info.text)
                paragraph_ip = paragraph_ip_match.group(1) if paragraph_ip_match else paragraph_ip
                paragraph_country_match = re.search(r"來自: \d+\.\d+\.\d+\.\d+ \((.+)\)", info.text)
                paragraph_country = paragraph_country_match.group(1) if paragraph_country_match else paragraph_country

        # 解析推文
        comments = []
        for push in soup.find_all("div", "push"):
            try:
                comment_score = push.find("span", "push-tag").text.strip() # 推 = 1, 噓 = -1, → = 0
                comment_score = 1 if comment_score == "推" else -1 if comment_score == "噓" else 0
                commenter = push.find("span", "push-userid").text.strip() if push.find("span", "push-userid") else "Unknown"
                comment = push.find("span", "push-content").text.strip()[1:]  # Remove ":" at the beginning
                comment_time = datetime.strptime(push.find("span", "push-ipdatetime").text.strip(),"%m/%d %H:%M").strftime(f"{paragraph_year}-%m-%d %H:%M")
                comments.append({"comment_score": comment_score, "commenter": commenter, "comment": comment, "comment_time": comment_time})
            except:
                pass

        results = {
            "paragraph_link": url,
            "paragraph_author": paragraph_author,
            "paragraph_title": paragraph_title,
            "paragraph_published_time": paragraph_published_time,
            "paragraph_content": paragraph_content,
            "paragraph_ip": paragraph_ip,
            "paragraph_country": paragraph_country,
            "comments": comments,
            "status": "200"
        }

        # 產生 MD5 雜湊值
        serialized_data = json.dumps(results, sort_keys=True).encode('utf-8')
        md5_hash = hashlib.md5(serialized_data).hexdigest()
        results["md5_hash"] = md5_hash

        # 計算文章和推文的 tokens 數量
        results["paragraph_content_token_count"] = self.calculate_paragraph_tokens(paragraph_content)
        results["comments_token_count"] = self.calculate_comments_tokens(comments)

        # 解析出文章標籤
        results["paragraph_tag"] = self.get_paragraph_tag(paragraph_title)
        
        # 解析出文章或標題中提到的股票代碼或名稱
        results["paragraph_stock_targets"] = self.identify_stock_targets(paragraph_title, paragraph_content)

        # 處理發佈時間為 Unknown 的情況
        results["paragraph_published_time"] = datetime.strptime(paragraph_published_time, "%Y-%m-%d %H:%M:%S") if results["paragraph_published_time"] != "Unknown" else datetime.strptime("2007-01-01", "%Y-%m-%d")

        return results

    # 計算文章 tokens 數量
    def calculate_paragraph_tokens(self, paragraph_content, tokenizer=GPT2Tokenizer.from_pretrained("gpt2")):        
        if paragraph_content == None: return 0
        paragraph_content_token_count = len(tokenizer.encode(paragraph_content))
        return paragraph_content_token_count

    # 計算推文的 tokens 數量
    def calculate_comments_tokens(self, comments, tokenizer=GPT2Tokenizer.from_pretrained("gpt2")):
        comments_token_count = sum(len(tokenizer.encode(comment["comment"])) for comment in comments) if comments else 0
        return comments_token_count

    # 傳入文章標題，返回文章標籤
    def get_paragraph_tag(self, paragraph_title):
        if paragraph_title == None: return "Unknown"
        matches = re.findall(r'\[([^\]]+)\]', paragraph_title)
        return matches[0] if matches else "Unknown"

    # 解析出文章或標題中提到的股票代碼或名稱
    def identify_stock_targets(self, paragraph_title, paragraph_content):

        paragraph_stock_targets = {}

        # 判斷標題是否有股票代碼或名稱
        for stock in self.stock_list:
            if stock in paragraph_title:
                if stock in self.stock_name_dicts:
                    paragraph_stock_targets[self.stock_name_dicts[stock]] = stock
                elif stock in self.stock_no_dicts:
                    paragraph_stock_targets[stock] = self.stock_no_dicts[stock]

        # 將標題用 Spacy 斷詞，找出是可能是股票代碼或名稱的實體
        title = self.nlp_zh(paragraph_title)
        for ent in title.ents:
            if ent.label_ == "ORG" or ent.label_ == "CARDINAL":
                if ent.text in self.stock_list:
                    if ent.text in self.stock_name_dicts:
                        paragraph_stock_targets[self.stock_name_dicts[ent.text]] = ent.text
                    elif ent.text in self.stock_no_dicts:
                        paragraph_stock_targets[ent.text] = self.stock_no_dicts[ent.text]

        # 將文章內容用 Spacy 斷詞，找出是可能是股票代碼或名稱的實體
        doc = self.nlp_zh(paragraph_content)
        for ent in doc.ents:
            if ent.label_ == "ORG" or ent.label_ == "CARDINAL":
                if ent.text in self.stock_list:
                    if ent.text in self.stock_name_dicts:
                        paragraph_stock_targets[self.stock_name_dicts[ent.text]] = ent.text
                    elif ent.text in self.stock_no_dicts:
                        paragraph_stock_targets[ent.text] = self.stock_no_dicts[ent.text]
        
        return paragraph_stock_targets

    # 取得股票代碼和名稱
    def get_stock_targets_dicts(self):
        stock_targets = PttStockTargets.objects.all()
        self.stock_list = []
        self.stock_name_dicts = {}
        self.stock_no_dicts = {}
        for stock_target in stock_targets:
            self.stock_list += [stock_target.name]
            self.stock_list += [stock_target.no]
            self.stock_name_dicts[stock_target.name] = stock_target.no
            self.stock_no_dicts[stock_target.no] = stock_target.name

    # 取得結束頁面編號
    def get_end_index(self):
        with connection.cursor() as cursor:
            cursor.execute("SELECT value FROM ptt_stock_setting where setting = 'end_index'")
            self.end_index = cursor.fetchone()[0]
        while requests.get("https://www.ptt.cc/bbs/Stock/index{}.html".format(self.end_index)).status_code == 200:
            self.end_index += 1
        with connection.cursor() as cursor:
            cursor.execute("UPDATE ptt_stock_setting SET value = {} WHERE setting = 'end_index'".format(self.end_index))
        print("last page:", self.end_index)


# 抓取最，爬取文章內容
def fetch_and_update_stock_paragraphs():

    # 建立 PttStockCrawler，指定要往前爬取多少頁
    ptc = PttStockCrawler(past_pages=50)

    # 依照起始和結束頁面編碼，決定要取出哪些文章字典來多線程抓取文章內容
    for index in range(ptc.start_index, ptc.end_index):
        curr_page_url = 'https://www.ptt.cc/bbs/Stock/index{}.html'.format(index)
        print("START SCANNING: "+ curr_page_url)
        ptc.page_url = curr_page_url
        links = ptc.get_post_links()
        ptc.crawl_paragraphs(links)

    print("========== get stock paragraph end ==========")