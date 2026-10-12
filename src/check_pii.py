import json
import re
import glob

phone = re.compile(r'(?<![\d.])[6-9]\d{9}(?![\d.])')
words = re.compile(r'\w*(?:mobile|phone|farmer|contact)\w*', re.I)

for f in sorted(glob.glob('notebooks/*.ipynb')):
    nb = json.load(open(f, encoding='utf-8'))
    for i, c in enumerate(nb['cells']):
        for o in c.get('outputs', []):
            txt = json.dumps(o, ensure_ascii=False)
            nums = phone.findall(txt)
            cols = sorted(set(words.findall(txt)))
            if nums or cols:
                masked = [n[:2] + 'xxxxxx' + n[-2:] for n in nums]
                print(f'{f} | cell {i} | {o.get("output_type")} | '
                      f'words: {cols} | numbers: {masked}')
