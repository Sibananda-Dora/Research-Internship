import zipfile, xml.etree.ElementTree as ET
with zipfile.ZipFile(r'c:\Users\Asus\Desktop\Opencode_research\Research-Wiki\research-ppt-diagrams\final-report\Product Development Project Report Format.docx') as docx:
    xml_content = docx.read('word/document.xml')
    tree = ET.fromstring(xml_content)
    text = '\n'.join([node.text for node in tree.iter() if node.tag.endswith('t') and node.text])
    with open('temp_format.txt', 'w', encoding='utf-8') as f:
        f.write(text)
