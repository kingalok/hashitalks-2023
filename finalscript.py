# -*- coding: utf-8 -*-
import re
import codecs

def escape_html(text):
    return text.replace("&", "&lt;").replace(">", "&gt;").replace("&", "&amp;")

def read_lines_any_encoding(path):
    encodings = ['utf-8', 'utf-8-sig', 'utf-16', 'utf-16-le', 'utf-16-be', 'latin1']
    for enc in encodings:
        try:
            f = codecs.open(path, "r", encoding=enc)
            lines = f.readlines()
            f.close()
            return lines
        except:
            continue
    raise ValueError("❌ Unable to decode file with common encodings")

def parse_powershell_script(input_file, output_html="script_flow_summary.html"):
    lines = read_lines_any_encoding(input_file)

    func_map = []
    inside_function = False
    current_func = None
    brace_count = 0
    known_funcs = []

    # First pass: Collect all function names
    for line in lines:
        match = re.match(r'^\s*function\s+([^\s({]+)', line.strip(), re.IGNORECASE)
        if match:
            known_funcs.append(match.group(1).strip())

    for i, line in enumerate(lines):
        stripped = line.strip()

        if not stripped:
            continue

        if not inside_function:
            match = re.match(r'^\s*function\s+([^\s({]+)(\s*\((.*?)\))?', stripped, re.IGNORECASE)
            if match:
                func_name = match.group(1)
                inline_params = match.group(3)
                current_func = {
                    'name': func_name,
                    'line': i + 1,
                    'params': [],
                    'vars': [],
                    'ifs': [],
                    'loops': [],
                    'trycatch': [],
                    'comments': [],
                    'calls': [],
                    'steps': []
                }
                if inline_params:
                    current_func['params'] = [p.strip() for p in inline_params.split(',')]
                func_map.append(current_func)
                inside_function = True
                brace_count = 0
            continue

        if inside_function:
            brace_count += line.count("{") - line.count("}")
            prefix = "&nbsp;&nbsp;" * max(0, brace_count)

            # Param block inside function
            if re.match(r'^\s*param\s*\((.*?)\)', stripped, re.IGNORECASE):
                param_match = re.match(r'^\s*param\s*\((.*?)\)', stripped)
                if param_match:
                    param_list = [p.strip() for p in param_match.group(1).split(',')]
                    current_func['params'].extend(param_list)

            # Comments
            if re.match(r'^\s*#', stripped):
                current_func['comments'].append(escape_html(stripped))

            # Conditions
            elif re.match(r'^\s*if\b', stripped, re.IGNORECASE):
                current_func['ifs'].append(escape_html(stripped))
                current_func['steps'].append(prefix + "├── IF: " + escape_html(stripped))
            elif re.match(r'^\s*elseif\b', stripped, re.IGNORECASE):
                current_func['ifs'].append(escape_html(stripped))
                current_func['steps'].append(prefix + "├── ELSEIF: " + escape_html(stripped))
            elif re.match(r'^\s*else\b', stripped, re.IGNORECASE):
                current_func['ifs'].append(escape_html(stripped))
                current_func['steps'].append(prefix + "├── ELSE")

            # Loops
            elif re.match(r'^\s*(for|foreach|while)\b', stripped, re.IGNORECASE):
                current_func['loops'].append(escape_html(stripped))
                current_func['steps'].append(prefix + "├── LOOP: " + escape_html(stripped))

            # Try/Catch
            elif re.match(r'^\s*try\b', stripped, re.IGNORECASE):
                current_func['trycatch'].append("TRY: " + escape_html(stripped))
                current_func['steps'].append(prefix + "├── TRY: " + escape_html(stripped))
            elif re.match(r'^\s*catch\b', stripped, re.IGNORECASE):
                current_func['trycatch'].append("CATCH: " + escape_html(stripped))
                current_func['steps'].append(prefix + "├── CATCH: " + escape_html(stripped))

            # Variable assignment
            elif re.match(r'^\s*\$\w+\s*=', stripped):
                current_func['vars'].append(escape_html(stripped))
                current_func['steps'].append(prefix + "├── VAR: " + escape_html(stripped))

            # Function calls (naive match)
            tokens = re.findall(r'\b([a-zA-Z_][a-zA-Z0-9_-]+)\b', stripped)
            for token in tokens:
                if token != current_func['name'] and token in known_funcs and token not in current_func['calls']:
                    current_func['calls'].append(token)

            if brace_count <= 0:
                inside_function = False
                current_func = None

    # HTML Output
    with codecs.open(output_html, "w", encoding="utf-8") as out:
        out.write("""<html><head><title>PowerShell Function Summary</title>
<style>
body { font-family: Arial; padding: 20px; }
h2 { color: #2c3e50; }
.function-block { margin-bottom: 20px; border: 1px solid #ccc; border-radius: 6px; }
.summary { font-size: 1.1em; margin-top: 30px; }
pre { background: #f4f4f4; padding: 10px; font-family: monospace; font-size: 14px; overflow-x: auto; }
button { background: #3498db; color: white; border: none; padding: 10px; width: 100%; text-align: left; font-size: 15px; cursor: pointer; border-radius: 6px 6px 0 0; }
button:hover { background: #2980b9; }
ul { margin: 0 0 10px 20px; padding: 0; }
</style>
<script>
function toggle(id) {
  var x = document.getElementById(id);
  if (x.style.display === "none") x.style.display = "block";
  else x.style.display = "none";
}
</script>
</head><body>
<h2>PowerShell Script Function Summary</h2>
""")

        for idx, func in enumerate(func_map):
            block_id = "block_" + str(idx)
            out.write('<div class="function-block">')
            out.write('<button onclick="toggle(\'%s\')">Function: %s (Line %d)</button>' % (
                block_id, func['name'], func['line']))
            out.write('<div id="%s" style="display:none;">' % block_id)

            # Summary section
            def write_list(title, items):
                out.write("<strong>%s (%d):</strong><ul>" % (title, len(items)))
                for item in items:
                    out.write("<li>%s</li>" % item)
                out.write("</ul>")

            out.write("<div style='padding:10px;'>")
            write_list("Parameters", func['params'])
            write_list("Variables", func['vars'])
            write_list("Conditions", func['ifs'])
            write_list("Loops", func['loops'])
            write_list("Try/Catch", func['trycatch'])
            write_list("Function Calls", func['calls'])
            write_list("Comments", func['comments'])
            out.write("</div>")

            # Full logic
            out.write('<pre>')
            for step in func['steps']:
                out.write(step + "<br>")
            out.write('</pre></div></div>')

        out.write('<div class="summary"><strong>Total functions found: %d</strong></div>' % len(func_map))
        out.write("</body></html>")

    print("✅ script_flow_summary.html created — open it in your browser.")

# Uncomment and run this line with your script path:
# parse_powershell_script("your_script.ps1")
