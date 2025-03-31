import os

def find_postgres_yaml_files(base_path="."):
    matched_files = []

    for root, dirs, files in os.walk(base_path):
        for file in files:
            if file.endswith(".yaml") and "postgres" in file.lower():
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, "r") as f:
                        content = f.read().lower()
                        if "postgres" in content:
                            matched_files.append(file_path)
                except Exception as e:
                    print("Could not read file: {0}. Error: {1}".format(file_path, str(e)))

    return matched_files

if __name__ == "__main__":
    results = find_postgres_yaml_files()
    print("Matching files with 'postgres' in filename and content:\n")
    for path in results:
        print(path)
