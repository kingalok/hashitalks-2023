import os
import re
import csv

SCRIPT_EXTENSIONS = ['.ps1', '.sh']

def find_all_scripts(base_path):
    script_map = {}
    for root, dirs, files in os.walk(base_path):
        for file in files:
            if any(file.endswith(ext) for ext in SCRIPT_EXTENSIONS):
                script_path = os.path.join(root, file)
                script_map[file.lower()] = script_path
    return script_map

def find_postgres_yaml_files(base_path):
    matched = []
    for root, dirs, files in os.walk(base_path):
        for file in files:
            if file.endswith(".yaml") and "postgres" in file.lower():
                path = os.path.join(root, file)
                try:
                    with open(path, "r") as f:
                        content = f.read().lower()
                        if "postgres" in content:
                            matched.append((file, path, content))
                except Exception as e:
                    print("Could not read YAML file: {0}".format(path))
    return matched

def extract_script_references(content):
    scripts = []
    lines = content.splitlines()
    for line in lines:
        for ext in SCRIPT_EXTENSIONS:
            if ext in line:
                match = re.search(r'([^\s\'"]+%s)' % ext, line)
                if match:
                    scripts.append(os.path.basename(match.group(1)).lower())
    return list(set(scripts))

def build_matrix(pipelines, all_scripts):
    matrix = {}

    for script_name in all_scripts.keys():
        matrix[script_name] = {}

    for pipeline_name, yaml_path, content in pipelines:
        referenced_scripts = extract_script_references(content)
        for script in matrix:
            matrix[script][pipeline_name] = "✓" if script in referenced_scripts else ""

    return matrix

def write_csv(matrix, pipelines, out_file):
    pipeline_names = [p[0] for p in pipelines]
    with open(out_file, "w") as f:
        writer = csv.writer(f)
        writer.writerow(["Script File"] + pipeline_names)
        for script, uses in matrix.items():
            row = [script]
            for name in pipeline_names:
                row.append(uses.get(name, ""))
            writer.writerow(row)

if __name__ == "__main__":
    BASE = "."
    all_scripts = find_all_scripts(BASE)
    pipelines = find_postgres_yaml_files(BASE)
    matrix = build_matrix(pipelines, all_scripts)
    write_csv(matrix, pipelines, "pipeline_script_matrix.csv")
    print("✅ CSV written: pipeline_script_matrix.csv")
