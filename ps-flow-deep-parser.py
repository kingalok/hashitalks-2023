# -*- coding: utf-8 -*-
import re
import codecs

def escape_html(text):
    return text.replace("&", "&lt;").replace(">", "&gt;").replace("&", "&amp;")

def read_lines_any_encoding(path):
    encodings = ['utf-8', 'utf-8-sig', 'utf-16', 'utf-16-le', 'utf-16-be', 'latin1']
    for enc in encodings:
        try:
            with codecs.open(path, "r", encoding=enc) as f:
                return f.readlines()
        except:
            continue
    raise ValueError("❌ Could not decode the file.")

def collect_functions(lines):
    func_defs = []
    func_names = []
    in_func = False
    brace_count = 0
    func_block = []
    func_name = ""
    func_start = 0

    for i, line in enumerate(lines):
        stripped = line.strip()

        if not in_func:
            match = re.match(r'^\s*function\s+([^\s({]+)', stripped, re.IGNORECASE)
            if match:
                func_name = match.group(1)
                in_func = True
                brace_count = line.count("{") - line.count("}")
                func_block = [line]
                func_start = i + 1
                func_names.append(func_name)
                continue

        elif in_func:
            brace_count += line.count("{") - line.count("}")
            func_block.append(line)
            if brace_count <= 0:
                func_defs.append({
                    "name": func_name,
                    "start_line": func_start,
                    "lines": func_block
                })
                in_func = False

    return func_defs, func_names

def analyze_function_block(func_lines, known_funcs):
    result = {
        'params': [],
        'vars': [],
        'ifs': [],
        'loops': [],
        'trycatch': [],
        'comments': [],
        'calls': [],
        'steps': []
    }

    for line in func_lines:
        stripped = line.strip()
        if not stripped:
            continue

        # Collect all steps for trace
        result['steps'].append(escape_html(stripped))

        # Extract param
        if re.match(r'^\s*param\s*\((.*?)\)', stripped, re.IGNORECASE):
            result['params'].extend(re.findall(r'\$\w+', stripped))

        # Detect logic
        if re.match(r'^\s*#', stripped):
            result['comments'].append(escape_html(stripped))
        if re.search(r'\bif\b', stripped, re.IGNORECASE):
            result['ifs'].append(escape_html(stripped))
        if re.search(r'\belseif\b', stripped, re.IGNORECASE):
            result['ifs'].append(escape_html(stripped))
        if re.search(r'\belse\b', stripped, re.IGNORECASE):
            result['ifs'].append(escape_html(stripped))
        if re.search(r'\b(for|foreach|while)\b', stripped, re.IGNORECASE):
            result['loops'].append(escape_html(stripped))
        if re.search(r'\btry\b', stripped, re.IGNORECASE):
            result['trycatch'].append("TRY: " + escape_html(stripped))
        if re.search(r'\bcatch\b', stripped, re.IGNORECASE):
            result['trycatch'].append("CATCH: " + escape_html(stripped))
        if re.match(r'^\s*\$\w+\s*=', stripped):
            result['vars'].append(escape_html(stripped))

        # Detect calls to known functions
        tokens = re.findall(r'\b([a-zA-Z_][a-zA-Z0-9_-]+)\b', stripped)
        for token in tokens:
            if token in known_funcs and token not in result['calls']:
                result['calls'].append(token)

    return result

def parse_powershell_script(input_file, output_html="script_flow_deep.html"):
    lines = read_lines_any_encoding(input_file)
    func_defs, func_names = collect_functions(lines)

    analyzed = []
    for func in func_defs:
        details = analyze_function_block(func['lines'], func_names)
        details['name'] = func['name']
        details['line'] = func['start_line']
        analyzed.append(details)

    # Generate HTML
    with codecs.open(output_html, "w", encoding="utf-8") as out:
        out.write("""<html><head><title>PowerShell Logic Analyzer</title>
<style>
body { font-family: Arial; padding: 20px; background: #fdfdfd; }
h2 { color: #2c3e50; }
.function-block { margin-bottom: 20px; border: 1px solid #ccc; border-radius: 6px; }
pre { background: #f4f4f4; padding: 10px; font-family: monospace; overflow-x: auto; }
button { background: #3498db; color: white; border: none; padding: 10px; width: 100%; text-align: left; font-size: 15px; cursor: pointer; border-radius: 6px 6px 0 0; }
ul { margin: 5px 0 10px 20px; padding: 0; }
</style>
<script>
function toggle(id) {
  var e = document.getElementById(id);
  e.style.display = (e.style.display === "none") ? "block" : "none";
}
</script>
</head><body>
<h2>PowerShell Script Deep Function Summary</h2>
""")

        for idx, func in enumerate(analyzed):
            block_id = "block_" + str(idx)
            out.write('<div class="function-block">')
            out.write('<button onclick="toggle(\'%s\')">Function: %s (Line %d)</button>' % (
                block_id, func['name'], func['line']))
            out.write('<div id="%s" style="display:none;"><div style="padding:10px;">' % block_id)

            def write_list(title, items):
                out.write("<strong>%s (%d):</strong><ul>" % (title, len(items)))
                for item in items:
                    out.write("<li>%s</li>" % item)
                out.write("</ul>")

            write_list("Parameters", func['params'])
            write_list("Variables", func['vars'])
            write_list("Conditions", func['ifs'])
            write_list("Loops", func['loops'])
            write_list("Try/Catch", func['trycatch'])
            write_list("Function Calls", func['calls'])
            write_list("Comments", func['comments'])

            out.write("<strong>Logic Trace:</strong><pre>")
            for step in func['steps']:
                out.write(step + "<br>")
            out.write("</pre></div></div></div>")

        out.write('<div><strong>Total Functions Found: %d</strong></div>' % len(analyzed))
        out.write("</body></html>")

    print("✅ Done. File created:", output_html)

# Uncomment and run with your script
# parse_powershell_script("your_script.ps1")
