import json
import argparse
from constants import PERSIST_DIRECTORY
from langchain.vectorstores import Chroma

def main(args):
    with open(args.mapping_path, 'r') as f:
        mapping = json.load(f)
        
    db = Chroma(persist_directory=PERSIST_DIRECTORY)
    
    if args.delete:
        # vec_counts = db.count()
        db.delete(ids=[mapping[args.source_path]])
        # print(f'Delete {db.count() - vec_counts} files')
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="DB management")

    # Add arguments
    parser.add_argument('--mapping_path', type=str, default=f'{PERSIST_DIRECTORY}/mapping.json', help='mapping.json path')
    parser.add_argument('--source_path', type=str, help='file source path')
    parser.add_argument('--delete', action='store_true')
    args = parser.parse_args()

    # Call the main function with parsed arguments
    main(args)