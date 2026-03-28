import time
import glob
import re
from deep_translator import GoogleTranslator

translator = GoogleTranslator(source='en', target='es')

# We'll translate all non-es components
for filepath in glob.glob("docs/*.es.md"):
    if "index.es.md" in filepath:
        continue

    print(f"Translating {filepath}...")
    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()

    out_lines = []
    in_code_block = False
    in_yaml = False
    
    def translate_text(text):
        if not text.strip(): return text
        try:
            res = translator.translate(text)
            time.sleep(0.05)
            return res if res else text
        except:
            return text

    for line in lines:
        stripped = line.strip()
        
        if not stripped:
            out_lines.append(line)
            continue
        
        if stripped == "---":
            in_yaml = not in_yaml
            out_lines.append(line)
            continue
            
        if in_yaml:
            if stripped.startswith("description:"):
                val = line.split("description:")[1].strip().strip('"')
                trans = translate_text(val)
                out_lines.append(f'description: "{trans}"\n')
            else:
                out_lines.append(line)
            continue
            
        if stripped.startswith("```"):
            in_code_block = not in_code_block
            out_lines.append(line)
            continue
            
        if in_code_block:
            out_lines.append(line)
            continue
            
        # Protect specific visual lines (SVG maps, tables, Navigation lists)
        if "assets/diagram" in stripped or stripped.startswith("←") or "Siguiente:" in stripped or stripped.startswith("|"):
            out_lines.append(line)
            continue

        # Ignore markdown lists of chapters since they were structured in english or already structured
        if "01_gcp_setup.md" in stripped or "10_github_actions.md" in stripped:
            out_lines.append(line)
            continue

        # Protect markdown prefixes
        prefix = ""
        rest = line
        while rest and rest[0] in " \t#>*-":
            prefix += rest[0]
            rest = rest[1:]
            
        if not rest.strip():
            out_lines.append(line)
            continue
            
        # Extract markdown links and inline code blocks, replacing them with generic placeholders 
        # so Google Translate doesn't mangle or rewrite URLs and command arguments
        links = re.findall(r'\[(.*?)\]\((.*?)\)', rest)
        codes = re.findall(r'(`.*?`)', rest)
        
        temp_rest = rest
        for i, code in enumerate(codes):
            temp_rest = temp_rest.replace(code, f"__CODE{i}__", 1)
        for i, link in enumerate(links):
            original = f"[{link[0]}]({link[1]})"
            temp_rest = temp_rest.replace(original, f"__LINK{i}__", 1)
            
        # Translate the heavily sanitized text string
        trans = translate_text(temp_rest.strip())
        
        if trans:
            # Reattach squashed or mistyped placeholders (google translate occasionally adds weird spacing)
            trans = re.sub(r'__\s?LINK(\d+)\s?__', r'__LINK\1__', trans)
            trans = re.sub(r'__\s?CODE(\d+)\s?__', r'__CODE\1__', trans)
            
            # Repopulate all URLs but safely translate their display text naturally
            for i, link in enumerate(links):
                translated_link_text = translate_text(link[0])
                trans = trans.replace(f"__LINK{i}__", f"[{translated_link_text}]({link[1]})")
                
            # Drop the inline code blocks back into the text identically
            for i, code in enumerate(codes):
                trans = trans.replace(f"__CODE{i}__", code)
            
            out_lines.append(prefix + trans + "\n")
        else:
            out_lines.append(line)

    with open(filepath, "w", encoding="utf-8") as f:
        f.writelines(out_lines)

print("Translation completed.")
