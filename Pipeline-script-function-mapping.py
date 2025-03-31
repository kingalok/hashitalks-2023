import os
import re
import csv

SCRIPT_EXTENSIONS = ['.ps1', '.sh']

def find_all_scripts(base_path):
    script_map = {}
    for root, dirs, files in os.walk(base_path):
        for file in files:
            if any(file.endswith(ext) for ext in SCRIPT_EXTENSIONS):
                path = os.path.join(root, file)
                script_map[file.lower()] = path
    return script_map

def find_postgres_yaml_files(base_path):
    matched = []
    for root, dirs, files in os.walk(base_path):
        for file in files:
            if file.endswith(".yaml") and "postgres" in file.lower():
                full_path = os.path.join(root, file)
                try:
                    with open(full_path, "r") as f:
                        content = f.read().lower()
                        if "postgres" in content:
                            matched.append((file, full_path, content))
                except Exception as e:
                    print("Could not read YAML file: {0}".format(full_path))
    return matched

def extract_script_references(yaml_content):
    scripts = []
    lines = yaml_content.splitlines()

    for line in lines:
        line = line.strip()
        if ".ps1" in line or ".sh" in line:
            matches = re.findall(r'([^\s\'"=]+\.ps1)', line, re.IGNORECASE)
            matches += re.findall(r'([^\s\'"=]+\.sh)', line, re.IGNORECASE)
            for match in matches:
                script_name = os.path.basename(match.strip().lower())
                scripts.append(script_name)

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
        for script, usage in matrix.items():
            row = [script]
            for name in pipeline_names:
                row.append(usage.get(name, ""))
            writer.writerow(row)

def generate_html_from_csv(csv_file, html_file):
    with open(csv_file, "r") as f:
        import csv
        reader = csv.reader(f)
        rows = list(reader)

    headers = rows[0]

    with open(html_file, "w") as f:
        f.write("<html><head><title>Pipeline-Script Matrix</title>\n")
        f.write("""
        <style>
        body { font-family: Arial; padding: 20px; }
        input { padding: 6px; width: 300px; margin-bottom: 15px; font-size: 14px; }
        table, th, td { border: 1px solid #ccc; border-collapse: collapse; padding: 6px; text-align: center; }
        th { background-color: #f2f2f2; }
        td.tick { color: green; font-weight: bold; }
        .hide { display: none; }
        </style>
        <script>
        function filterTable() {
            var input = document.getElementById("search").value.toLowerCase();
            var table = document.getElementById("matrix");
            var headers = table.rows[0].cells;

            var showCol = -1;
            for (var c = 1; c < headers.length; c++) {
                if (headers[c].textContent.toLowerCase().indexOf(input) > -1) {
                    showCol = c;
                    break;
                }
            }

            for (var r = 1; r < table.rows.length; r++) {
                var row = table.rows[r];
                var scriptName = row.cells[0].textContent.toLowerCase();
                var showRow = false;

                if (scriptName.indexOf(input) > -1) {
                    showRow = true;
                } else if (showCol > 0 && row.cells[showCol].textContent.trim() === "✓") {
                    showRow = true;
                }

                row.style.display = showRow ? "" : "none";
            }

            for (var c = 1; c < headers.length; c++) {
                var show = (c === showCol || input === "") ? "" : "none";
                headers[c].style.display = show;

                for (var r = 1; r < table.rows.length; r++) {
                    var cell = table.rows[r].cells[c];
                    cell.style.display = show;
                }
            }
        }
        </script>
        """)
        f.write("</head><body>\n")
        f.write("<h2>Pipeline to Script Mapping</h2>\n")
        f.write('<input type="text" id="search" onkeyup="filterTable()" placeholder="Search script or pipeline name...">\n')
        f.write('<table id="matrix">\n')

        for i, row in enumerate(rows):
            f.write("<tr>")
            for j, cell in enumerate(row):
                if i == 0:
                    f.write("<th>{0}</th>".format(cell))
                else:
                    if cell.strip() == "✓":
                        f.write("<td class='tick'>&#10003;</td>")
                    else:
                        f.write("<td>{0}</td>".format(cell))
            f.write("</tr>\n")

        f.write("</table>\n</body></html>")
        
if __name__ == "__main__":
    BASE = "."

    print("🔍 Scanning for scripts...")
    all_scripts = find_all_scripts(BASE)

    print("🔍 Searching for postgres pipelines...")
    pipelines = find_postgres_yaml_files(BASE)

    print("⚙️ Building usage matrix...")
    matrix = build_matrix(pipelines, all_scripts)

    print("📄 Writing CSV...")
    write_csv(matrix, pipelines, "pipeline_script_matrix.csv")

    print("🌐 Generating HTML...")
    generate_html_from_csv("pipeline_script_matrix.csv", "pipeline_script_matrix.html")

    print("\n✅ Done! Files created:")
    print(" - pipeline_script_matrix.csv")
    print(" - pipeline_script_matrix.html")
