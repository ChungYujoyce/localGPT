import os, logging, shutil
from langchain.vectorstores import Chroma
from langchain.docstore.document import Document
from langchain.document_loaders import PDFPlumberLoader, TextLoader
from utils import extract_text_without_tables, split_contexts
from pdf2image import convert_from_path
from pathlib import Path
from ocr import OCR
import csv, re
import pdfplumber
from langchain.text_splitter import RecursiveCharacterTextSplitter

#ROOT_DIRECTORY = os.path.dirname(os.path.realpath(__file__))
ROOT_DIRECTORY = '/home/chsieh/joyce/localGPT/PDFParser'
SOURCE_DIRECTORY = '/home/chsieh/joyce/localGPT/SOURCE_DOCUMENTS'
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

def text_filter(text):
    # take off copyright line
    idx = re.search(r"©", text).span()[0]
    return text[:idx]
                        
def text_to_chunk(pdf_dir, table_dir, dis_dir):  

    # loader = PDFPlumberLoader(pdf_dir)
    # pages = loader.load_and_split()
    pdf = pdfplumber.open(pdf_dir)
    pages = pdf.pages
    
    # [TODO] len(table_list) == len(pages)
    table_list = [] 
    for root, _, files in os.walk(table_dir):
        for file in files:
            if file.split('.')[1] == 'txt':
                table_list.append(os.path.join(root, file))

    chunks = []
    added_list = []
    for page_idx in range(len(pages)):
        text = ""
        table_text, raw_text = extract_text_without_tables(pages[page_idx], page_idx+1)
        # [TODO] save and stop here
        
        if table_text:
            # [TODO] no O^2
            
            for table in table_list:
                table_name = table.split('.')[0].split('/')[-1]
                if table_text.find(table_name) != -1:
                    table_content = open(table, "r").read()
                    table_text = table_text.replace("<|" + table_name + "|>", "\n\n"+table_content+"\n\n")
                    added_list.append(table)
            chunks.append(table_text)

        text += raw_text
        clean_text = text_filter(text)
        chunks += split_contexts(clean_text, chunk_size=300, overlap=False)
    
    # Tables cannot be recognized by pdfplumber
    chunks += [f"\n\n{open(table, 'r').read()}" for table in table_list if table not in added_list]
        
    # [str, str, str]
    final_chunks = []
    curr_text = ""

    for chunk in chunks:
        if len(split_contexts(curr_text + chunk, chunk_size=300, overlap=False)) == 1:
            curr_text += chunk
        else:
            final_chunks.append(curr_text)
            curr_text = chunk

    final_chunks.append(curr_text)
    
    # for i in range(len(chunks)-1):
    #     concat = []
    #     texts = str(chunks[i-1]) + str(chunks[i])
    #     concat = split_contexts(texts, chunk_size=300, overlap=False)
    #     if len(concat) == 1:
    #         chunks[i-1] = concat[0]
    #         chunks[i] = ""
    #         if i < len(chunks) - 1:
    #             i += 1
    # final_chunks = [c for c in chunks if c != ""]

    ## [TODO]
    ## 1. shrink chunk size if possible
    
    ## 3. the last things (may split out as another function)

    for i in range(len(final_chunks)):
        with open(f'{dis_dir}/chunk_{i+1}.txt', 'w', encoding='utf-8') as f:
            f.write(final_chunks[i])

def table_to_txt(source_dir, dis_dir):
    for root, _, files in os.walk(source_dir):
        for file in files:
            file_name = file.split('.')[0]
            if file.split('.')[1] == 'csv':
                shutil.copyfile(f'{root}/{file_name}.csv', f'{dis_dir}/{file_name}.txt')

def main():
    """
    # file1.py only generate the above files
    
     /intermediate
       /page0
         /table_0.csv
         /table_1.csv
         /raw_text.txt
         /table_text.txt
       /page1
       ...
       
    # file2.py replace table tags in table_text.txt with table.csv and combine raw_text.txt. Finally, split chunks.
     /paragraphs
       /chunk0.txt
       /chunk1.txt
       ...
    
    """
    
    Path(PARSED_DIRECTORY).mkdir(parents=True, exist_ok=True)
    for root, _, files in os.walk(SOURCE_DIRECTORY):
        for file in files:
            file_name = os.path.splitext(file)[0]
            source_file_path = os.path.join(root, file)

            # img_path = f'{PARSED_DIRECTORY}/{file_name}/page_imgs'
            # Path(img_path).mkdir(parents=True, exist_ok=True)
            # pdf_to_img(source_file_path, img_path)

            table_path = f'{PARSED_DIRECTORY}/{file_name}/tables'
            Path(table_path).mkdir(parents=True, exist_ok=True)
            # img_to_table(img_path, table_path)
            
            
             Other file (replace and chunk)
            paragraph_path = f'{PARSED_DIRECTORY}/{file_name}/paragraphs'
            Path(paragraph_path).mkdir(parents=True, exist_ok=True)
            table_to_txt(table_path, table_path) # [[str]]: [page1_tables, page2_tables, page3_tables]
            text_to_chunk(source_file_path, table_path, paragraph_path)

            

if __name__ == "__main__":
    main()





