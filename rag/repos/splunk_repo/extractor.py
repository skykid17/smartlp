import os
import time
import tarfile

def get_archive_contents(tgz_file):
    """Get the top-level contents of a tar.gz file without extracting it."""
    try:
        with tarfile.open(tgz_file, 'r:gz') as tar:
            # Get all members and find top-level directories/files
            members = tar.getnames()
            top_level_items = set()
            for member in members:
                # Get the first part of the path (top-level item)
                top_level = member.split('/')[0]
                top_level_items.add(top_level)
            return top_level_items
    except Exception as e:
        print(f"Error reading {tgz_file}: {e}")
        return set()

def is_already_extracted(tgz_file):
    """Check if the tgz file has already been extracted by looking for its contents."""
    expected_contents = get_archive_contents(tgz_file)
    if not expected_contents:
        return False
    
    # Check if all expected top-level items exist in current directory
    current_items = set(os.listdir("."))
    return expected_contents.issubset(current_items)

def extract_tgz(filename):
    """Extract a tgz file using Python's tarfile module."""
    try:
        with tarfile.open(filename, 'r:gz') as tar:
            tar.extractall()
        print(f"Successfully extracted {filename}")
        return True
    except Exception as e:
        print(f"Error extracting {filename}: {e}")
        return False

def main():
    print("Starting TGZ file monitor...")
    
    while True:
        tgz_files_found = False
        
        # Get all files in current directory
        try:
            files = os.listdir(".")
        except OSError as e:
            print(f"Error reading directory: {e}")
            time.sleep(5)
            continue
        
        for filename in files:
            # Skip if it's a directory
            if os.path.isdir(filename):
                continue
                
            # Check if it's a tgz file
            if filename.endswith(".tgz") or filename.endswith(".tar.gz"):
                tgz_files_found = True
                
                # Check if already extracted
                if is_already_extracted(filename):
                    print(f"Skipping {filename} - already extracted")
                    continue
                
                print(f"Found new tgz file: {filename}")
                
                # Extract the file
                if extract_tgz(filename):
                    print(f"Successfully processed {filename}")
                else:
                    print(f"Failed to extract {filename}")
        
        if not tgz_files_found:
            print("No tgz files found in directory.")
        
        print("Waiting 5 seconds before next scan...")
        time.sleep(5)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nScript stopped by user.")
    except Exception as e:
        print(f"Unexpected error: {e}")