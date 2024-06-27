import os
from django.conf import settings
from langchain_openai import OpenAIEmbeddings
from langchain_qdrant import Qdrant
from langchain_community.document_loaders.csv_loader import CSVLoader

def embed_stock_targets():

    ptt_stock_targets_path = os.path.join(settings.DATA_DIR, "ptt_stock_targets.csv")
    # print(ptt_stock_targets_path)
    loader = CSVLoader(
        file_path=ptt_stock_targets_path,
        csv_args={"delimiter":",", "quotechar":'"'},
        source_column="no"
    )
    stock_targets = loader.load()
    # for stock_target in stock_targets:
        # print(stock_target)

    metadatas = []
    for stock_target in stock_targets:
        metadatas.append({
            "type": "stock_target",
            "model": "text-embedding-3-large",
            "source": stock_target.metadata["source"],
            "row": stock_target.metadata["row"]
        })

    embeddings_model = OpenAIEmbeddings(model="text-embedding-3-large")

    qdrant = Qdrant.from_texts(
        [stock_target.page_content for stock_target in stock_targets],
        embeddings_model,
        collection_name="stock_targets_small",
        force_recreate=True,
        metadatas=metadatas
    )


    