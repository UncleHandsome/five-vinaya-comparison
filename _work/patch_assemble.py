import re

p = '_work/assemble.py'
t = open(p, encoding='utf-8').read()
start = t.index('def clean_item(')
end = t.index('parsed = {}')

new = r'''def clean_item(title, body):
    out = [title]
    for raw in body.split('\n'):
        s = raw.strip()
        if s.startswith('>'):
            c = clean_quote_line(s)
            if c is None:
                continue
            c = re.sub(r'(段\s*\d+\s*[–\-]\s*\d+\s*[：:])', '\\n>\\n> **\\1**　', c)
            c = re.sub(r'(段\s*\d+\s*[：:])', '\\n>\\n> **\\1**　', c)
            out.extend(c.split('\n'))
        else:
            out.append(raw.rstrip())
    t = '\n'.join(out)
    t = re.sub(r'^\s*-\s*', '- ', t, flags=re.M)
    t = re.sub(r'\n{3,}', '\n\n', t)
    return t.strip()

'''
t = t[:start] + new + t[end:]
open(p, 'w', encoding='utf-8').write(t)
print('patched ok')
