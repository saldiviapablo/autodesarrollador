import json,os,subprocess,sys,time
from pathlib import Path
import psutil
if sys.argv[1]=='utf8':
 sys.stdout.buffer.write('á ñ € 😀\n'.encode());sys.stderr.buffer.write('diagnóstico ü\n'.encode());raise SystemExit(0)
if sys.argv[1]=='exit7':raise SystemExit(7)
if sys.argv[1]=='sleep':time.sleep(120)
if sys.argv[1]=='tree':
 child=subprocess.Popen([sys.executable,__file__,'sleep'])
 ids=[{'pid':os.getpid(),'birth':psutil.Process().create_time()},{'pid':child.pid,'birth':psutil.Process(child.pid).create_time()}]
 Path(sys.argv[2]).write_text(json.dumps(ids),encoding='utf-8');time.sleep(120)
