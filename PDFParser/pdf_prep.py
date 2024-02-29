import os
from collections import defaultdict 
from utils import extract_text_without_tables
from pdf2image import convert_from_path
from pathlib import Path
from ocr import OCR
import csv, re
import pdfplumber


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
    table_dict = dict()
    for root, _, files in os.walk(source_dir):
        for file in files:
            file_path = os.path.join(root, file)
            data, cropped_table = OCR(file_path)
            
            page = os.path.splitext(file)[0].split('_')[-1]
            table = []
            for i in range(len(cropped_table)):
                # save cropped_table.png
                file_name = f'{dis_dir}/page_{page}/table_{i+1}'
                cropped_table[i].convert("RGB").save(file_name + '.png')
                # save table ouput csv
                table_data = data[f'table_{i}']
                with open(file_name + '.csv','w') as result_file:
                    wr = csv.writer(result_file, dialect='excel')
                    for k, v in table_data.items():
                        wr.writerow(v)
                table.append(os.path.join(root, file_name + '.csv'))
            table_dict[int(page) - 1] = table

    return table_dict

def text_filter(text):
    # take off copyright line
    idx = re.search(r"©", text).span()[0]
    return text[:idx]
                    
            
def text_extract(pdf_dir, dis_dir):  

    pdf = pdfplumber.open(pdf_dir)
    pages = pdf.pages
    text_dict = defaultdict(dict)

    for page_idx in range(len(pages)):
        Path(f'{dis_dir}/page_'+ str(page_idx+1)).mkdir(parents=True, exist_ok=True)

        table_text, raw_text = extract_text_without_tables(pages[page_idx], page_idx+1)

        text_dict[page_idx]['table_text'] = table_text
        text_dict[page_idx]['raw_text'] = raw_text

        with open(f'{dis_dir}/page_{page_idx+1}/table_text.txt', 'w', encoding='utf-8') as f:
            f.write(text_dict[page_idx]['table_text'])

        with open(f'{dis_dir}/page_{page_idx+1}/raw_text.txt', 'w', encoding='utf-8') as f:
            f.write(text_dict[page_idx]['raw_text'])
  
    return text_dict
    

def pdf_prep(parsed_dir, file_name, source_file_path):

    img_path = f'{parsed_dir}/{file_name}/page_imgs'
    Path(img_path).mkdir(parents=True, exist_ok=True)
    pdf_to_img(source_file_path, img_path)

    inter_path = f'{parsed_dir}/{file_name}/intermediate'
    Path(inter_path).mkdir(parents=True, exist_ok=True)
    
    text_dict = text_extract(source_file_path, inter_path)
    table_dict = img_to_table(img_path, inter_path)

    return table_dict, text_dict
