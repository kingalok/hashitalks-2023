# -*- coding: utf-8 -*-
import re
import codecs

def escape_html(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

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

def parse_powershell_script(input_file, output_html="script_flow.html"):
    lines = read_lines_any_encoding(input_file)

    func_map = []
    inside_function = False
    current_func = None
    brace_count = 0

    for i in range(len(lines)):
        line = lines[i]
        stripped = line.strip()

        if stripped.startswith("#") or not stripped:
            continue

        if not inside_function:
            match = re.match(r'^\s*function\s+([^\s({]+)', stripped, re.IGNORECASE)
            if match:
                current_func = {
                    'name': match.group(1),
                    'line': i + 1,
                    'steps': []
                }
                func_map.append(current_func)
                inside_function = True
                brace_count = 0

        if inside_function:
            brace_count += line.count("{") - line.count("}")
            prefix = "&nbsp;&nbsp;" * max(0, brace_count)

            if re.match(r'^\s*if\b', stripped, re.IGNORECASE):
                current_func['steps'].append(prefix + "├── IF: " + escape_html(stripped))
            elif re.match(r'^\s*elseif\b', stripped, re.IGNORECASE):
                current_func['steps'].append(prefix + "├── ELSEIF: " + escape_html(stripped))
            elif re.match(r'^\s*else\b', stripped, re.IGNORECASE):
                current_func['steps'].append(prefix + "├── ELSE")
            elif re.match(r'^\s*(for|foreach|while)\b', stripped, re.IGNORECASE):
                current_func['steps'].append(prefix + "├── LOOP: " + escape_html(stripped))
            elif re.match(r'^\s*\$\w+\s*=', stripped):
                current_func['steps'].append(prefix + "├── VAR: " + escape_html(stripped))

            if brace_count <= 0:
                inside_function = False
                current_func = None

    # Generate HTML
    with codecs.open(output_html, "w", encoding="utf-8") as out:
        out.write("""<html><head><title>PowerShell Script Flow</title>
<style>
body { font-family: Arial; padding: 20px; }
h2 { color: #2c3e50; }
.function-block { margin-bottom: 15px; border: 1px solid #ccc; border-radius: 6px; }
.summary { font-size: 1.1em; margin-top: 30px; }
pre { background: #f4f4f4; padding: 10px; margin: 0; font-family: monospace; font-size: 14px; }
button { background: #3498db; color: white; border: none; padding: 10px; width: 100%; text-align: left; font-size: 15px; cursor: pointer; border-radius: 6px 6px 0 0; }
button:hover { background: #2980b9; }
</style>
<script>
function toggle(id) {
  var x = document.getElementById(id);
  if (x.style.display === "none") x.style.display = "block";
  else x.style.display = "none";
}
</script>
</head><body>
<h2>PowerShell Script Logic Overview</h2>
""")

        for idx, func in enumerate(func_map):
            block_id = "block_" + str(idx)
            out.write('<div class="function-block">')
            out.write('<button onclick="toggle(\'%s\')">Function: %s (Line %d)</button>' % (block_id, func['name'], func['line']))
            out.write('<div id="%s" style="display:none;"><pre>' % block_id)
            if func['steps']:
                for step in func['steps']:
                    out.write(step + "<br>")
            else:
                out.write("  (No logic found)")
            out.write('</pre></div></div>')

        out.write('<div class="summary"><strong>Total functions found: %d</strong></div>' % len(func_map))
        out.write("</body></html>")

    print("✅ script_flow.html created — open it in your browser.")

# Uncomment and set your file:
# parse_powershell_script("your_script.ps1")
