import pdfplumber
# import nltk
# nltk.download('punkt')
# from nltk.tokenize import sent_tokenize

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
    def curves_to_edges(cs):
        """See https://github.com/jsvine/pdfplumber/issues/127"""
        edges = []
        for c in cs:
            edges += pdfplumber.utils.rect_to_edges(c)
        return edges

    # Table settings.
    ts = {
        "vertical_strategy": "lines",
        "horizontal_strategy": "lines",
        "explicit_vertical_lines": curves_to_edges(p.curves + p.edges),
        "explicit_horizontal_lines": curves_to_edges(p.curves + p.edges),
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
