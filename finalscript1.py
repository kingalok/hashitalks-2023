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
    raise ValueError("❌ Unable to decode file")

def analyze_function_block(func_lines, known_funcs):
    data = {
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
        s = line.strip()
        if not s: continue

        # Collect params
        if re.search(r'\bparam\s*\((.*?)\)', s, re.IGNORECASE):
            data['params'] += re.findall(r'\$\w+', s)

        # Comments
        if s.startswith("#"):
            data['comments'].append(escape_html(s))

        # IF / ELSE / ELSEIF
        if re.search(r'\bif\b', s, re.IGNORECASE):
            data['ifs'].append(escape_html(s))
        if re.search(r'\belseif\b', s, re.IGNORECASE):
            data['ifs'].append(escape_html(s))
        if re.search(r'\belse\b', s, re.IGNORECASE):
            data['ifs'].append(escape_html(s))

        # Loops
        if re.search(r'\b(for|foreach|while)\b', s, re.IGNORECASE):
            data['loops'].append(escape_html(s))

        # Try/Catch
        if re.search(r'\btry\b', s, re.IGNORECASE):
            data['trycatch'].append("TRY: " + escape_html(s))
        if re.search(r'\bcatch\b', s, re.IGNORECASE):
            data['trycatch'].append("CATCH: " + escape_html(s))

        # Vars
        if re.match(r'^\s*\$\w+\s*=.*', s):
            data['vars'].append(escape_html(s))

        # Function calls
        tokens = re.findall(r'\b([a-zA-Z_][a-zA-Z0-9_-]+)\b', s)
        for token in tokens:
            if token in known_funcs and token not in data['calls']:
                data['calls'].append(token)

        data['steps'].append(escape_html(s))

    return data

def parse_powershell_script(input_file, output_html="script_flow_final_fixed.html"):
    lines = read_lines_any_encoding(input_file)

    func_map = []
    known_funcs = []
    inside_function = False
    brace_count = 0
    buffer = []
    func_name = ""
    start_line = 0

    # First: get all function names
    for line in lines:
        m = re.match(r'^\s*function\s+([^\s({]+)', line.strip(), re.IGNORECASE)
        if m:
            known_funcs.append(m.group(1))

    for idx, line in enumerate(lines):
        s = line.strip()

        if not inside_function:
            match = re.match(r'^\s*function\s+([^\s({]+)', s, re.IGNORECASE)
            if match:
                func_name = match.group(1)
                start_line = idx + 1
                inside_function = True
                brace_count = line.count("{") - line.count("}")
                buffer = [line]
            continue

        if inside_function:
            brace_count += line.count("{") - line.count("}")
            buffer.append(line)

            if brace_count <= 0:
                summary = analyze_function_block(buffer, known_funcs)
                summary['name'] = func_name
                summary['line'] = start_line
                func_map.append(summary)
                inside_function = False

    # HTML output
    with codecs.open(output_html, "w", encoding="utf-8") as f:
        f.write("""<html><head><title>PowerShell Deep Logic Summary</title>
<style>
body { font-family: Arial; padding: 20px; }
button { background: #3498db; color: white; border: none; padding: 10px; width: 100%; text-align: left; cursor: pointer; font-size: 16px; border-radius: 6px 6px 0 0; }
button:hover { background: #2980b9; }
.function-block { border: 1px solid #ccc; border-radius: 6px; margin-bottom: 20px; }
pre { background: #f9f9f9; padding: 10px; font-family: monospace; }
ul { margin: 0 0 10px 20px; padding: 0; }
</style>
<script>
function toggle(id) {
  var x = document.getElementById(id);
  x.style.display = (x.style.display === "none") ? "block" : "none";
}
</script>
</head><body><h2>PowerShell Script Function Summary (Full Depth)</h2>
""")
        for i, func in enumerate(func_map):
            div_id = "func_" + str(i)
            f.write('<div class="function-block">')
            f.write('<button onclick="toggle(\'%s\')">Function: %s (Line %d)</button>' % (div_id, func['name'], func['line']))
            f.write('<div id="%s" style="display:none; padding: 10px;">' % div_id)

            def write_ul(title, items):
                f.write("<strong>%s (%d):</strong><ul>" % (title, len(items)))
                for item in items:
                    f.write("<li>%s</li>" % item)
                f.write("</ul>")

            write_ul("Parameters", func['params'])
            write_ul("Variables", func['vars'])
            write_ul("Conditions", func['ifs'])
            write_ul("Loops", func['loops'])
            write_ul("Try/Catch", func['trycatch'])
            write_ul("Function Calls", func['calls'])
            write_ul("Comments", func['comments'])

            f.write("<strong>Logic Trace:</strong><pre>")
            for s in func['steps']:
                f.write(s + "<br>")
            f.write("</pre></div></div>")

        f.write("<p><strong>Total Functions:</strong> %d</p>" % len(func_map))
        f.write("</body></html>")

    print("✅ script_flow_final_fixed.html created. Open it in your browser.")
