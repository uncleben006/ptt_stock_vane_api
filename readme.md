## Environment
使用 poetry 安裝套件和管理虛擬環境

```
poetry install
poetry shell
```

## Dataset
1. 將所有股票版資料爬取整理好，每日更新最新50頁的所有文章，確保資料庫內資料與時俱進

<!-- 2. 準備好所有台股標的，搭配 NER實例辨識(Spacy)判斷每篇文章、留言提到了哪些股票的標的
   - 難點：如何才能讓留言當中的公司綽號被找出來？留言當中有太多公司綽號，要將 Spacy fine tune 才能提高辨識率 
   - 策略
      1. 先將已知公司綽號列成表
      2. 將資料庫當中的留言拿去給 GPT 4o，轉成 Spacy 用於訓練的資料結構，fine tune Spacy 
      3. 將 train 好的 Spacy 再次分析留言，看看有哪些「疑似公司」的詞彙，並手動填上後再次 fine tune

   - 參考資料
      - [PTT股版公司綽號](https://pttpedia.fandom.com/zh/wiki/PTT%E4%BC%81%E6%A5%AD%E7%B6%BD%E8%99%9F%E5%88%97%E8%A1%A8)
      - [Spacy 介紹](https://medium.com/willhanchen/%E8%87%AA%E7%84%B6%E8%AA%9E%E8%A8%80%E8%99%95%E7%90%86-spacy-%E5%88%9D%E6%8E%A2%E5%BC%B7%E5%A4%A7%E7%9A%84%E5%B7%A5%E5%85%B7%E5%BA%ABspacy-%E8%AE%93%E6%A9%9F%E5%99%A8%E8%AE%80%E6%87%82%E6%88%91%E5%80%91%E7%9A%84%E8%AA%9E%E8%A8%80%E5%90%A7-4a35daa895d0)
      - [Spacy fine-tunning](https://medium.com/willhanchen/%E8%87%AA%E7%84%B6%E8%AA%9E%E8%A8%80%E8%99%95%E7%90%86-spacy-%E5%96%84%E7%94%A8-chatgpt%E5%B9%AB%E6%88%91%E5%80%91%E8%A8%93%E7%B7%B4%E5%87%BA%E8%87%AA%E8%A8%82%E7%9A%84named-entity-recognition%E5%AF%A6%E9%AB%94-2450df2127cc) -->


2. 使用 gpt-3.5-turbo-0125 模型分析每則留言的股市情緒
   **目標**：將 prompt 和留言傳入後，回傳「留言提及的公司名稱(如果有的話)」及「多空分數(-1~1)」
   **難點**：
   &emsp;1：留言當中有太多公司綽號，導致模型無法判斷留言是否有提及特定公司。
   &emsp;2：留言當中參雜次文化，導致模型判斷結果與事實相差甚遠。
   
   <!-- **方向1**：用RAG的將[PTT股版公司綽號](https://pttpedia.fandom.com/zh/wiki/PTT%E4%BC%81%E6%A5%AD%E7%B6%BD%E8%99%9F%E5%88%97%E8%A1%A8)一起提交進 prompt，可以解決公司辨識問題 -->
   **方向**：準備一批資料 fine tune gpt-3.5，解決閱讀次文化以及公司辨識問題。
   
   **策略**：
      &emsp;1. 將 [PTT股版公司綽號](https://pttpedia.fandom.com/zh/wiki/PTT%E4%BC%81%E6%A5%AD%E7%B6%BD%E8%99%9F%E5%88%97%E8%A1%A8) 提供給 GPT 4o，並將資料庫中的留言轉換成「留言與公司」表。
      &emsp;2. 將資料庫中的留言手動標註，轉換成「留言與多空分數」。
      &emsp;3. 將資料轉換成訓練格式提交給 gpt-3.5-turbo-0125。

3. 寫成排程將上述兩個行為每日執行

## Database
1. 使用資料庫：PostgreSQL
2. Migrate
```
python manage.py makemigrations
python manage.py migrate
```

## Model Fee
```
gpt-4
費用：input $30.00 / 1M tokens | $60.00 / 1M tokens

gpt-3.5-turbo-0125
費用：input $0.5 / 1M Tokens | $1.5 / 1M Tokens
```

## Feature：

#### 介面
使用 Line bot 作為主要介面

#### 主功能： 
選擇時間區間後，回傳條狀圖顯示 前十名 過去多少時間 討論數量最多的股票
- 計算方式：只要某篇文章有提到某個股票標的，那底下的留言都會被歸屬於討論該標的，底下留言若有提到其他股票標的則另外加總進提到的股票標的當中。
- 實作方式：用 Matplotlib 套件創造出來。

#### 主功能： 
選擇股票與時間區間，顯示「該股票」在該「時間區間」當中有多少討論，鄉民們看漲還是看跌
- 顯示該個標被文章提及的次數
- 顯示該標地被留言提及的數量(只要文章有該標的，留言就會計算有提及該標的)
- 顯示鄉民們看漲或看跌的分數(TODO: 這裡可以做成線性圖，顯示鄉民們這段時間看漲看跌的分數變化)
- 總結這些文章內容

#### 次要功能：
- 顯示前十名推文推爆的文章，提供 標題 連結 並條列出標題，用 AI 計算出文章大綱、與留言 內容
- 顯示前十名鄉民認為會漲的股票，顯示他們的留言，總結他們的觀點
- 顯示前十名鄉民認為會下跌的股票，顯示他們的留言，總結他們的觀點
- 顯示前十名績效最好的鄉民，他們績效各多少

## 股票提取：
使用模型： Spacy 
```
pip install spacy
python -m spacy download zh_core_web_trf
```

## ngrok
使用 ngrok 進行開發
```
ngrok http http://localhost:8000
```

## 流程
將近半年討論最多的股票標的給用戶選擇
用戶選完之後，bot 回傳時間，過去1日、15日、30日、自訂
選擇自訂則跳出「請輸入時間區間」
用戶輸入完時間後
系統開始查詢，會需要幾秒時間
用戶點選查看結果
系統將結果回傳出來

## AI 分析資料心路歷程
[AI Data Analysis Journey](./AI_data_analysis_journey.md)