import sys,re
f=sys.argv[1]; nums=sys.argv[2]
want=set()
for part in nums.split(','):
    if '-' in part:
        a,b=part.split('-'); want.update(range(int(a),int(b)+1))
    else: want.add(int(part))
for line in open(f,encoding='utf-8'):
    m=re.match(r'^(\d+)\t(.*)$',line.rstrip('\n'))
    if m and int(m.group(1)) in want:
        print(f"[{m.group(1)}] {m.group(2)}\n")
