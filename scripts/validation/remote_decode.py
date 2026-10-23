import base64
import gzip
import sys

dest = sys.argv[1]
src = sys.argv[2]
data = open(src, 'rb').read()
raw = gzip.decompress(base64.b64decode(data))
with open(dest, 'wb') as f:
    f.write(raw)
print("Decoded %d bytes to %s" % (len(raw), dest))
