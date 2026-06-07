import os
import ast
import xml.etree.ElementTree as ET
from xml.dom import minidom

def extract_strings(directory):
    strings = set()
    for root, dirs, files in os.walk(directory):
        for f in files:
            if f.endswith('.py'):
                path = os.path.join(root, f)
                with open(path, 'r', encoding='utf-8') as file:
                    content = file.read()
                try:
                    tree = ast.parse(content)
                    for node in ast.walk(tree):
                        if isinstance(node, ast.Call):
                            if isinstance(node.func, ast.Attribute) and node.func.attr == 'tr':
                                if node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
                                    strings.add(node.args[0].value)
                except Exception as e:
                    print(f"Error parsing {path}: {e}")
    return strings

def create_ts_file(strings, output_path, lang="en"):
    root = ET.Element("TS", version="2.1", language=lang)
    context = ET.SubElement(root, "context")
    name = ET.SubElement(context, "name")
    name.text = "GeomaticaPe"
    
    for s in sorted(strings):
        message = ET.SubElement(context, "message")
        source = ET.SubElement(message, "source")
        source.text = s
        translation = ET.SubElement(message, "translation")
        translation.set("type", "unfinished")
        
    xmlstr = minidom.parseString(ET.tostring(root)).toprettyxml(indent="  ")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(xmlstr)

if __name__ == "__main__":
    plugin_dir = os.path.dirname(os.path.abspath(__file__))
    strings = extract_strings(plugin_dir)
    i18n_dir = os.path.join(plugin_dir, "i18n")
    if not os.path.exists(i18n_dir):
        os.makedirs(i18n_dir)
    ts_path = os.path.join(i18n_dir, "geomaticape_en.ts")
    create_ts_file(strings, ts_path)
    print(f"Generado {ts_path} con {len(strings)} cadenas para traducir.")
