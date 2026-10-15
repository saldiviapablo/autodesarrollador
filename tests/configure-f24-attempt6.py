"""Create a separate attempt6 harness; do not alter historical attempt5."""
import pathlib
ROOT=pathlib.Path(__file__).resolve().parents[1]
p=ROOT/'tests/test-phase24-attempt6-live.py'
assert not p.exists()
text=(ROOT/'tests/test-phase24-attempt5-live.py').read_text(encoding='utf-8')
for old,new in [('attempt 5','attempt 6'),('Attempt 5','Attempt 6'),('attempt5','attempt6'),('attempt-5','attempt-6'),('f24-a5-','f24-a6-'),("'attempt': 5","'attempt': 6"),('f24-harness-preflight-20261014','f24-attempt6-preflight-20261014')]:text=text.replace(old,new)
p.write_bytes(text.encode('utf-8'))
