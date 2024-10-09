import os
import pandas as pd

from django.conf import settings
from langchain_openai import OpenAIEmbeddings
from langchain_qdrant import Qdrant
from langchain_community.document_loaders.csv_loader import CSVLoader

def embed_stock_targets():

    ptt_stock_targets_path = os.path.join(settings.DATA_DIR, "stock_targets.csv")
    stock_targets = pd.read_csv(ptt_stock_targets_path)

    embeddings_model = OpenAIEmbeddings(model="text-embedding-3-small")

    metadatas = []
    for stock_target in zip(stock_targets['no'], stock_targets['name']):
        print(stock_target)
        metadatas.append({
            "type": "stock_target",
            "model": "text-embedding-3-small",
            "no": stock_target[0],
            "name": stock_target[1]
        })
    
    stock_targets_no = Qdrant.from_texts(
        stock_targets['no'].tolist(),
        embeddings_model,
        collection_name="stock_targets_split_small",
        force_recreate=True,
        metadatas=metadatas
    )

    stock_targets_name = Qdrant.from_texts(
        stock_targets['name'].tolist(),
        embeddings_model,
        collection_name="stock_targets_split_small",
        force_recreate=False,
        metadatas=metadatas
    )

    # print(stock_targets.to_dict())
    # for stock_target in stock_targets.to_dict():
    #     print(stock_target)


    # # print(ptt_stock_targets_path)
    # loader = CSVLoader(
    #     file_path=ptt_stock_targets_path,
    #     csv_args={"delimiter":",", "quotechar":'"'},
    #     source_column="no"
    # )
    # stock_targets = loader.load()
    # # for stock_target in stock_targets:
    #     # print(stock_target)

    # metadatas = []
    # for stock_target in stock_targets:
    #     metadatas.append({
    #         "type": "stock_target",
    #         "model": "text-embedding-3-large",
    #         "source": stock_target.metadata["source"],
    #         "row": stock_target.metadata["row"]
    #     })


    