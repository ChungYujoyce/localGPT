import pdfplumber
from collections import Counter
# import nltk
# nltk.download('punkt')
from nltk.tokenize import sent_tokenize

def split_contexts(context: str, chunk_size=1000, overlap=False):
    all_chunks = []
    chunk = []
    num_words = 0
    for sent in sent_tokenize(context.strip()):
        num_words += len(sent.split())
        chunk.append(sent)
        if num_words >= chunk_size:
            chunk_str = " ".join(chunk)
            all_chunks.append(chunk_str)

            if overlap:
                num_words -= len(chunk[0].split())
                chunk = chunk[1:]
            else:
                chunk = []
                num_words = 0
        
    if len(chunk) > 0:
        chunk_str = " ".join(chunk)
        all_chunks.append(chunk_str)
        chunk = []
        num_words = 0
        
    return all_chunks

#Parse PDFs excluding tables.
def extract_text_without_tables(p, page_idx):
    try:
        ts = {
            "vertical_strategy": "lines",
            "horizontal_strategy": "lines",
            "explicit_vertical_lines": p.edges,
            "explicit_horizontal_lines": p.edges,
            "intersection_y_tolerance": 10,
        }
        # Get the bounding boxes of the tables on the page.
        bboxes = [table.bbox for table in p.find_tables(table_settings=ts)]
        table_texts, raw_texts = "", ""
        if len(bboxes) > 0:
            head = 0
            for idx, __bbox in enumerate(bboxes):
                x0, top, x1, bottom = __bbox
                table_texts += p.crop((0, head, p.width, top), relative=False, strict=True).extract_text()
                table_texts += f'<|page_{page_idx}_table_{idx+1}|>'
                head = bottom
            raw_texts = p.crop((0, head, p.width, p.height), relative=False, strict=True).extract_text()
        else:
            raw_texts = p.extract_text()
    except:
        v_lines, h_lines = [], []
        if len(p.lines) > 0:
            h_pnt_cnts = Counter([(line['x0'], line['x1']) for line in p.lines if line['height'] == 0])
            v_lines = [index for k, v in h_pnt_cnts.items() if v > 1 for index in k]
            v_pnt_cnts = Counter([(line['y0'], line['y1']) for line in p.lines if line['width'] == 0])
            h_lines = [index for k, v in v_pnt_cnts.items() if v > 1 for index in k]
            
        ts = {
            "vertical_strategy": "lines_strict",
            "horizontal_strategy": "lines_strict",
            "explicit_vertical_lines": v_lines,
            "explicit_horizontal_lines": h_lines,
            "intersection_y_tolerance": 10,
        }
        # Get the bounding boxes of the tables on the page.
        bboxes = [table.bbox for table in p.find_tables(table_settings=ts)]
        table_texts, raw_texts = "", ""
        if len(bboxes) > 0:
            head = 0
            for idx, __bbox in enumerate(bboxes):
                x0, top, x1, bottom = __bbox
                table_texts += p.crop((0, head, p.width, top), relative=False, strict=True).extract_text()
                table_texts += f'<|page_{page_idx}_table_{idx+1}|>'
                head = bottom
            raw_texts = p.crop((0, head, p.width, p.height), relative=False, strict=True).extract_text()
        else:
            raw_texts = p.extract_text()
            
    # im = p.to_image()
    # im.debug_tablefinder(ts).save('test.png')
    # import pdb
    # pdb.set_trace()
    
    return table_texts, raw_texts
    
    
#     def not_within_bboxes(obj):
#         """Check if the object is in any of the table's bbox."""
#         def obj_in_bbox(_bbox):
#             """See https://github.com/jsvine/pdfplumber/blob/stable/pdfplumber/table.py#L404"""
#             v_mid = (obj["top"] + obj["bottom"]) / 2
#             h_mid = (obj["x0"] + obj["x1"]) / 2
#             x0, top, x1, bottom = _bbox
#             return (h_mid >= x0) and (h_mid < x1) and (v_mid >= top) and (v_mid < bottom)

#         return not any(obj_in_bbox(__bbox) for __bbox in bboxes)
    
#     return p.filter(not_within_bboxes).extract_text()
