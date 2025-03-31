import os
import re

SCRIPT_EXTENSIONS = ['.ps1', '.sh']

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
                            matched_files.append((file_path, content))
                except Exception as e:
                    print("Could not read file: {0}. Error: {1}".format(file_path, str(e)))

    return matched_files

def extract_script_references(yaml_content):
    scripts = []
    lines = yaml_content.splitlines()
    for line in lines:
        for ext in SCRIPT_EXTENSIONS:
            if ext in line:
                match = re.search(r'([^\s\'"]+%s)' % ext, line)
                if match:
                    scripts.append(match.group(1))
    return list(set(scripts))  # remove duplicates

def extract_functions_from_script(script_path):
    functions = []
    try:
        with open(script_path, 'r') as f:
            content = f.read()
            if script_path.endswith(".ps1"):
                functions = re.findall(r'function\s+(\w+)', content, re.IGNORECASE)
            elif script_path.endswith(".sh"):
                functions = re.findall(r'^(\w+)\s*\(\)\s*\{', content, re.MULTILINE)
    except Exception as e:
        return ["Error reading: {0}".format(str(e))]
    return functions if functions else ["No functions found"]

if __name__ == "__main__":
    base_path = "."
    results = find_postgres_yaml_files(base_path)

    print("\nMapping of Pipelines to Scripts and Functions:\n")
    for yaml_file, content in results:
        print("Pipeline:", yaml_file)
        scripts = extract_script_references(content)
        if not scripts:
            print("  No scripts found.")
        for script in scripts:
            script_path = os.path.join(os.path.dirname(yaml_file), script)
            if os.path.exists(script_path):
                functions = extract_functions_from_script(script_path)
                print("  Script: {0}".format(script_path))
                print("    Functions: {0}".format(", ".join(functions)))
            else:
                print("  Script: {0} (not found)".format(script_path))
