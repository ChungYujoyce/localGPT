import logging
import os
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed

import click
import torch
from langchain.docstore.document import Document
from langchain.document_loaders import TextLoader
from langchain.text_splitter import Language, RecursiveCharacterTextSplitter
from langchain.vectorstores import Chroma
from utils import get_embeddings

from constants import (
    CHROMA_SETTINGS,
    DOCUMENT_MAP,
    EMBEDDING_MODEL_NAME,
    INGEST_THREADS,
    PERSIST_DIRECTORY,
    SOURCE_DIRECTORY,
)


def file_log(logentry):
    file1 = open("file_ingest.log", "a")
    file1.write(logentry + "\n")
    file1.close()
    print(logentry + "\n")


def load_single_document(file_path: str) -> Document:
    # Loads a single document from a file path
    try:
        file_extension = os.path.splitext(file_path)[1]
        loader_class = DOCUMENT_MAP.get(file_extension)
        if loader_class:
            file_log(file_path + " loaded.")
            loader = loader_class(file_path)
        else:
            file_log(file_path + " document type is undefined.")
            raise ValueError("Document type is undefined")
        return loader.load()
    except Exception as ex:
        file_log("%s loading error: \n%s" % (file_path, ex))
        return None


def load_document_batch(filepaths):
    logging.info("Loading document batch")
    # create a thread pool
    with ThreadPoolExecutor(len(filepaths)) as exe:
        # load files
        futures = [exe.submit(load_single_document, name) for name in filepaths]
        # collect data
        if futures is None:
            file_log(name + " failed to submit")
            return None
        else:
            data_list = [future.result() for future in futures]
            # return data and file paths
            return (data_list, filepaths)


def load_documents(source_dir: str) -> list[Document]:
    # Loads all documents from the source documents directory, including nested folders
    paths = []
    for root, _, files in os.walk(source_dir):
        for file_name in files:
            print("Importing: " + file_name)
            file_extension = os.path.splitext(file_name)[1]
            source_file_path = os.path.join(root, file_name)
            if file_extension in DOCUMENT_MAP.keys():
                paths.append(source_file_path)

    # Have at least one worker and at most INGEST_THREADS workers
    n_workers = min(INGEST_THREADS, max(len(paths), 1))
    chunksize = round(len(paths) / n_workers)
    docs = []
    with ProcessPoolExecutor(n_workers) as executor:
        futures = []
        # split the load operations into chunks
        for i in range(0, len(paths), chunksize):
            # select a chunk of filenames
            filepaths = paths[i : (i + chunksize)]
            # submit the task
            try:
                future = executor.submit(load_document_batch, filepaths)
            except Exception as ex:
                file_log("executor task failed: %s" % (ex))
                future = None
            if future is not None:
                futures.append(future)
        # process all results
        for future in as_completed(futures):
            # open the file and load the data
            try:
                contents, _ = future.result()
                docs.extend(contents)
            except Exception as ex:
                file_log("Exception: %s" % (ex))

    return docs


def split_documents(documents: list[Document]) -> tuple[list[Document], list[Document]]:
    # Splits documents for correct Text Splitter
    text_docs = []
    for doc in documents:
        if doc is not None:
            if isinstance(doc, list):
                text_docs += doc
            else:
                text_docs.append(doc)
    return text_docs

@click.command()
@click.option(
    "--device_type",
    default="cuda" if torch.cuda.is_available() else "cpu",
    type=click.Choice(
        [
            "cpu",
            "cuda",
            "ipu",
            "xpu",
            "mkldnn",
            "opengl",
            "opencl",
            "ideep",
            "hip",
            "ve",
            "fpga",
            "ort",
            "xla",
            "lazy",
            "vulkan",
            "mps",
            "meta",
            "hpu",
            "mtia",
        ],
    ),
    help="Device to run on. (Default is cuda)",
)
def main(device_type):
    # Load documents and split in chunks
    # logging.info(f"Loading documents from {SOURCE_DIRECTORY}")
    # documents = load_documents(SOURCE_DIRECTORY)
    # text_documents = split_documents(documents)
    # # All pages 
    # # langchain Document {page_content: str, metadata: dict}
    # import pdb
    # pdb.set_trace()
    # text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    # texts = text_splitter.split_documents(text_documents)
    # # List['langchain.schema.document.Document']
    # logging.info(f"Loaded {len(documents)} documents from {SOURCE_DIRECTORY}")
    # logging.info(f"Split into {len(texts)} chunks of text")

    """
    (1) Chooses an appropriate langchain library based on the enbedding model name.  Matching code is contained within fun_localGPT.py.
    
    (2) Provides additional arguments for instructor and BGE models to improve results, pursuant to the instructions contained on
    their respective huggingface repository, project page or github repository.
    """
    PARSED_DIRECTORY = f'/PARSED_DOCUMENTS'
    paragraph_path = '/home/chsieh/joyce/localGPT/PDFParser/PARSED_DOCUMENTS/Solution-Brief_Rack_Scale_AI/paragraphs'
    doc_list = []
    for root, _, files in os.walk(paragraph_path):
        for file in files:
            file = os.path.join(root, file)
            loader = TextLoader(file)
            documents = loader.load()
            doc_list += documents
    embeddings = get_embeddings(device_type)

    logging.info(f"Loaded embeddings from {EMBEDDING_MODEL_NAME}")
    db = Chroma.from_documents(
        doc_list,
        embeddings,
        persist_directory=PERSIST_DIRECTORY,
        client_settings=CHROMA_SETTINGS,
    )


if __name__ == "__main__":
    logging.basicConfig(
        format="%(asctime)s - %(levelname)s - %(filename)s:%(lineno)s - %(message)s", level=logging.INFO
    )
    main()
