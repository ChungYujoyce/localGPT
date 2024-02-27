import os, logging
from langchain.vectorstores import Chroma
from langchain.docstore.document import Document
from langchain.document_loaders import PyPDFLoader, TextLoader
from utils import extract_text_without_tables, split_contexts
from pdf2image import convert_from_path
from pathlib import Path
from ocr import OCR
import csv
import pdfplumber
from langchain.text_splitter import RecursiveCharacterTextSplitter

#ROOT_DIRECTORY = os.path.dirname(os.path.realpath(__file__))
ROOT_DIRECTORY = '/home/joyce/localGPT'
SOURCE_DIRECTORY = f'{ROOT_DIRECTORY}/SOURCE_DOCUMENTS'
PARSED_DIRECTORY = f'{os.getcwd()}/PARSED_DOCUMENTS'

# Step 1: PDF to Image transformation

def pdf_to_img(source_dir, dis_dir):
    images = convert_from_path(source_dir)
    for i in range(len(images)):
        images[i].save(f'{dis_dir}/page_'+ str(i+1) +'.png', 'PNG')

def table_postprocess():
    pass
# Step 2: Table parsing (cell/column/row) with TableTransformer
def img_to_table(source_dir, dis_dir):               
    # walk through all tables in each of PDF
    for root, _, files in os.walk(source_dir):
        for file in files:
            file_name = os.path.join(root, file)
            data, cropped_table = OCR(file_name)
            
            count = os.path.splitext(file)[0].split('_')[-1]

            for i in range(len(cropped_table)):
                # save cropped_table.png
                cropped_table[i].convert("RGB").save(f'{dis_dir}/page_{count}_table_{i+1}.png')
                # save table ouput csv
                table_data = data[f'table_{i}']
                with open(f'{dis_dir}/page_{count}_table_{i+1}.csv','w') as result_file:
                    wr = csv.writer(result_file, dialect='excel')
                    for k, v in table_data.items():
                        wr.writerow(v)
                # table output csv postprocess
                
                        
def text_to_chunk(source_dir, dis_dir):  
    loader = PyPDFLoader(source_dir)
    pages = loader.load_and_split()
    pdf = pdfplumber.open(source_dir)
    text = ""
    for i in range(len(pages)):
        text += str(extract_text_without_tables(pdf.pages[i]))
        
    texts = split_contexts(text, chunk_size=300, overlap=False)
    for i in range(len(texts)):
        with open(f'{dis_dir}/chunk_{i+1}.txt', 'w', encoding='utf-8') as f:
            f.write(texts[i])

def table_to_chunk(source_dir, dis_dir):
    for root, _, files in os.walk(source_dir):
        for file in files:
            file_name = file.split('.')[0]
            if file.split('.')[1] == 'csv':
                data = ""
                with open(f'{root}/{file_name}.csv', 'r') as csvfile: 
                    csvFile = csv.DictReader(csvfile)
                    for lines in csvFile:
                        data += str(lines)
                        data += '\n'
                with open(f'{dis_dir}/{file_name}.txt', 'w', encoding='utf-8') as f:
                    f.write(data)

def main():
    Path(PARSED_DIRECTORY).mkdir(parents=True, exist_ok=True)
    for root, _, files in os.walk(SOURCE_DIRECTORY):
        for file in files:
            file_name = os.path.splitext(file)[0]
            source_file_path = os.path.join(root, file)

            # img_path = f'{PARSED_DIRECTORY}/{file_name}/page_imgs'
            # Path(img_path).mkdir(parents=True, exist_ok=True)
            # #pdf_to_img(source_file_path, img_path)

            table_path = f'{PARSED_DIRECTORY}/{file_name}/tables'
            # Path(table_path).mkdir(parents=True, exist_ok=True)
            #img_to_table(img_path, table_path)

            paragraph_path = f'{PARSED_DIRECTORY}/{file_name}/paragraphs'
            Path(paragraph_path).mkdir(parents=True, exist_ok=True)
            #text_to_chunk(source_file_path, paragraph_path)
            table_to_chunk(table_path, paragraph_path)

    doc_list = []
    for root, _, files in os.walk(PARSED_DIRECTORY):
        for file in files:
            loader = TextLoader(file)
            documents = loader.load()
            doc_list.append(documents)
            

if __name__ == "__main__":
    main()





