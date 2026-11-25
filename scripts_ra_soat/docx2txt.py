import sys, zipfile, re
from xml.etree import ElementTree as ET
W='{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
for p in sys.argv[1:]:
    root=ET.fromstring(zipfile.ZipFile(p).read('word/document.xml'))
    out=[]
    for el in root.iter():
        if el.tag==W+'p':
            t=''.join(x.text or '' for x in el.iter(W+'t'))
            if t.strip(): out.append(t)
    open(p.rsplit('/',1)[-1]+'.txt','w',encoding='utf-8').write('\n'.join(out))
    print(p, len(out))
