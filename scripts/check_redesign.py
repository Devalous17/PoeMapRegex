"""Prove the visual redesign preserves the saved analysis and core source files."""
from pathlib import Path
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from backend.analysis_service import analyze_request
baseline=json.loads((ROOT/'fixtures/redesign-baseline.json').read_text(encoding='utf-8'))
for name,digest in baseline['protected'].items():
 assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest, 'Core file changed: '+name
source=(ROOT/'fixtures/test-build.pob.txt').read_text(encoding='utf-8').strip()
assert analyze_request({'source':source})==baseline['analysis'], 'Parsed build, ratings, or backend regex changed'
print('PASS: protected core files, parsed build, all modifier ratings and backend preset regex are identical.')
