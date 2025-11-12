import json
import os

def split_postman_collection(input_file, output_dir):
    # Load the Postman collection JSON
    with open(input_file, 'r', encoding='utf-8') as f:
        collection = json.load(f)
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Extract collection name (optional)
    collection_name = collection.get('info', {}).get('name', 'postman_collection')

    # Recursive function to extract individual requests
    def extract_items(items, folder_path=""):
        for item in items:
            if 'item' in item:
                # This is a folder — recurse into it
                folder_name = item.get('name', 'unnamed_folder')
                extract_items(item['item'], os.path.join(folder_path, folder_name))
            else:
                # This is an actual request
                request_name = item.get('name', 'unnamed_request')
                safe_name = "".join(c if c.isalnum() or c in (' ', '-', '_') else "_" for c in request_name).strip()
                
                file_path = os.path.join(output_dir, folder_path)
                os.makedirs(file_path, exist_ok=True)
                
                output_file = os.path.join(file_path, f"{safe_name}.json")

                # Write individual request JSON
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(item, f, indent=4, ensure_ascii=False)

                print(f"Saved: {output_file}")

    # Start extraction
    extract_items(collection.get('item', []))
    print(f"\n✅ All API requests from '{collection_name}' saved in '{output_dir}'")

if __name__ == "__main__":
    input_file = "postman_collection.json"  # your input file
    output_dir = "split_apis"               # output folder for split JSONs
    split_postman_collection(input_file, output_dir)
