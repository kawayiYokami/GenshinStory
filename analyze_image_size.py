import os
from pathlib import Path
import sys

def get_size(path):
    """Recursively get size of a directory or file, ignoring errors."""
    total_size = 0
    try:
        if os.path.isfile(path) and not os.path.islink(path):
            return os.path.getsize(path)
        elif os.path.isdir(path):
            for dirpath, dirnames, filenames in os.walk(path, topdown=True, onerror=None):
                # Exclude other mount points to avoid recursion errors in some environments
                dirnames[:] = [d for d in dirnames if not os.path.ismount(os.path.join(dirpath, d))]
                for f in filenames:
                    fp = os.path.join(dirpath, f)
                    if not os.path.islink(fp):
                        try:
                            total_size += os.path.getsize(fp)
                        except OSError:
                            continue
    except OSError:
        return 0
    return total_size

def analyze_directory(dir_path: Path, top_n: int = 25):
    """Analyzes a directory and prints the top N largest items."""
    if not dir_path.exists():
        print(f"Warning: Directory '{dir_path}' not found. Skipping.")
        return

    print(f"\n--- Analyzing size of contents in {dir_path} ---")
    
    items = []
    try:
        for item in dir_path.iterdir():
            size_bytes = get_size(item)
            items.append((item.name, size_bytes))
    except OSError as e:
        print(f"Error reading directory {dir_path}: {e}")
        return

    items.sort(key=lambda x: x[1], reverse=True)

    print(f"\n--- Top {top_n} largest items in {dir_path} ---")
    for i, (name, size) in enumerate(items[:top_n]):
        size_mb = size / (1024 * 1024)
        if size_mb > 0.1: # Only print items larger than 0.1MB to keep it clean
            print(f"{i+1}. {name:<20} {size_mb:.2f} MB")

def main():
    """Main function to analyze multiple directory sizes."""
    print("--- Starting comprehensive image content analysis ---")
    
    # Analyze the root directory
    analyze_directory(Path("/"))

    print("\n--- Analysis complete ---")

if __name__ == "__main__":
    main()