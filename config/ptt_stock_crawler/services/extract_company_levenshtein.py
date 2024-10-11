import warnings
import logging
import os
import spacy
import pandas as pd
import textdistance
import threading
import concurrent.futures
from datetime import datetime

# 忽略所有 FutureWarning
# 設置所有日誌級別為 ERROR
warnings.filterwarnings("ignore", category=FutureWarning)
logging.getLogger().setLevel(logging.ERROR)

# django
from django.conf import settings
from ptt_stock_vane_api.models import PttStockParagraphs

# langchain
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain.output_parsers.json import SimpleJsonOutputParser
from langchain.globals import set_verbose
set_verbose(False)

def extract_company_levenshtein():
    global zh_spacy
    global stock_dict
    global lock

    lock = threading.Lock()
    # 從 DB 取得 2024-01-01~2024-01-02 的文章
    print('loading data...')
    # start_of_2024 = datetime(2024, 5, 1)
    # end_of_2024 = datetime(2024, 5, 3)
    # paragraphs = PttStockParagraphs.objects.filter(paragraph_published_time__gt=start_of_2024, paragraph_published_time__lt=end_of_2024)
    paragraphs = PttStockParagraphs.objects.filter(id__in=[152703])

    print('loading spacy model...')
    zh_spacy = spacy.load("zh_core_web_trf")
    stock_dict = pd.read_csv(os.path.join(settings.DATA_DIR, "stock_dataset.csv"))
    
    # 多線程處理留言，分析完後再將留言更新至文章
    print('start analyzing...')
    for paragraph in paragraphs:
            
        with concurrent.futures.ThreadPoolExecutor(max_workers=250) as executor:
            futures = [executor.submit(analyze_comment, comment_obj) for comment_obj in paragraph.comments]
            result_comments = [future.result() for future in concurrent.futures.as_completed(futures)]
            concurrent.futures.wait(futures)
        # current_paragraph = PttStockParagraphs.objects.get(id=paragraph.id)
        # current_paragraph.comments = result_comments
        # current_paragraph.save()

def analyze_comment(comment_obj):
    comment_text, match_token = check_token_match_using_stock_dict(comment_obj)
    context = create_context(match_token)
    result = langchain_analyze_comment(comment_text, context)
    result_comment = comment_obj | result
    with lock:
        print(result_comment['comment'])
        print(context)
        print(result_comment['sentiment'], result_comment['stock_targets'])
        print('-------------------')
    return result_comment

def check_token_match_using_stock_dict(comment_obj):
    comment_text = comment_obj['comment']
    comment = zh_spacy(comment_text)
    match_token = {}

    for token in comment:
        for index, row in stock_dict.iterrows():

            # 匹配股票綽號
            if pd.notna(row['stock_nickname']):
                is_match, similarity = match_token_with_threshold(token.text, row['stock_nickname'], 0.65)
                if is_match:
                    update_match_token(match_token, token.text, row, similarity, 'stock_nickname')

            # 匹配股票代碼
            is_match, similarity = match_token_with_threshold(token.text, row['stock_no'], 0.9)
            if is_match:
                update_match_token(match_token, token.text, row, similarity, 'stock_no')

            # 匹配公司名稱
            is_match, similarity = match_token_with_threshold(token.text, row['stock_name'], 0.65)
            if is_match:
                update_match_token(match_token, token.text, row, similarity, 'stock_name')

    return comment_text, match_token

def match_token_with_threshold(token_text, comparison_text, threshold):
    similarity = textdistance.damerau_levenshtein.normalized_similarity(token_text, comparison_text)
    return similarity >= threshold, similarity

def update_match_token(match_token, token_text, row, similarity, match_type):
    if (token_text not in match_token) or (similarity > match_token[token_text]['similarity']):
        match_token[token_text] = {
            'match_token': token_text,
            'stock_no': row['stock_no'],
            'stock_name': row['stock_name'],
            'business_scope': row.get('business_scope', None),
            'competitor': row.get('competitor', None),
            'stock_nickname': row.get('stock_nickname', None),
            'nickname_explain': row.get('nickname_explain', None),
            'similarity': similarity,
            'match_type': match_type
        }

def create_context(match_token):
    context = "Comment matches: \n"
    business_info = ""
    for stock_target, value in match_token.items():
        value['similarity'] = round(value['similarity'] * 100, 2)
        match value['match_type']:
            case 'stock_nickname':
                context += (f"[{value['stock_name']}:{value['stock_no']}] because the term [{value['match_token']}] is similar to it's nickname [{value['stock_nickname']}] up to {value['similarity']}%. Nickname explanation:{value['nickname_explain']}.\n")
            case 'stock_no':
                context += (f"[{value['stock_name']}:{value['stock_no']}] because the term [{value['match_token']}] is similar to it's stock number [{value['stock_no']}] up to {value['similarity']}%.\n")
            case 'stock_name':
                context += (f"[{value['stock_name']}:{value['stock_no']}] because the term [{value['match_token']}] is similar to it's stock name [{value['stock_name']}] up to {value['similarity']}%.\n")
        if pd.notna(value['competitor']):
            business_info += (f"{value['business_scope']}\n")
    
    context += "Company introduction:\n" + business_info if business_info else ""
    context = "Comment matches nothing." if context == "Comment matches: \n" else context.removesuffix('\n')
    return context

def langchain_analyze_comment(comment_text, context):

    # comment_text = "要看就看現在 GG強成這樣台灣應該可以把匯率控在2"
    # context = "Comment matches:\n[台積電:2330] because the term [GG] is similar to it's nickname [GG] up to 100.0%. Nickname explanation:「台積積」音近「台GG」，簡稱「GG」.\n[台灣大:3045] because the term [台灣] is similar to it's stock name [台灣大] up to 66.67%.\nCompany introduction:\n台積電是做什麼的？台積電主要經營依客戶之訂單與其提供之產品設計說明，以從事製造與銷售積體電路以及其他晶圓半導體裝置。提供前述產品之封裝與測試服務、積體電路之電腦輔助設計技術服務。提供製造光罩及其設計服務。\n台灣大是做什麼的？台灣大主要經營通訊業"
    # comment_text = "最近怎麼跌成這樣..."
    # context = "Comment matches nothing."

    # print(comment_text)
    # print(context)

    # Prompt
    prompt = ChatPromptTemplate.from_template("""You are a stock market sentiment analyzer tasked with the following:
                                              
    1. Sentiment Analysis
    - Analyze the <comment> from the commenter's perspective, considering any sarcasm or irony.
    - Assign a sentiment score between -1 (most bearish) and 1 (most bullish), with at least two decimal places.

    2. Company Identification
    - Identify Taiwanese publicly traded companies mentioned in the <comment> by analyzing both the <comment> and the <context>.
    - The <context> lists potential company names extracted from the <comment>, but may include everyday terms or nicknames.
                                                                                        
    Guidelines:
    - Understand the <comment>: Grasp its full meaning and context.
    - Use the <context> wisely: Refer to it to identify potential companies but don't assume every term is a company.
    - Disambiguate terms: Determine if each term in the <context> actually refers to a company in the <comment> or is used as everyday language.
    - Consider nicknames and common words: Be mindful that some company names or nicknames may be common words; pay attention to their usage in the <comment>.
    - Ensure accuracy: Use contextual clues to accurately identify the companies mentioned.

    Output Requirement:
    - Output a JSON object containing a "sentiment" key with a float value and a "stock_targets" key with an array value. 
    - Example: {{"sentiment": 0.7732953298,"stock_targets": ["2498","2454"]}}

    <comment>{comment}</comment>

    <context>{context}</context>
    """)

    # Model
    model = ChatOpenAI(
        model_name="gpt-4o-mini-2024-07-18", 
        temperature=0, 
        model_kwargs={ "response_format": { "type": "json_object" } },
    )

    # Parser
    parser = SimpleJsonOutputParser()

    # Chain
    chain = prompt | model | parser
    result = chain.invoke({ "comment": comment_text, "context": context})
    
    return result