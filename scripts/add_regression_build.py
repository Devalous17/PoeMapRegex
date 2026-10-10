"""Save a sanitized local export with explicit reviewer labels, then validate it."""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import re
import sys
import zlib
import xml.etree.ElementTree as ET
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.pob import decode_build
from backend.analysis_service import analyze_request


def sanitize_export(raw):
    if raw.startswith(('http://','https://')):
        raise ValueError('Save the PoB export text locally first.')
    root=decode_build(base64.urlsafe_b64encode(zlib.compress(raw.encode())).decode()) if raw.startswith('<') else decode_build(raw)
    for node in list(root):
        if node.tag not in {'Build','Skills','Items','Tree','Config'}: root.remove(node)
    for element in root.iter():
        for key in list(element.attrib):
            if key.lower() in {'accountname','charactername','author','url'} or key.lower()=='name' and element.tag in {'PathOfBuilding','Build'}:
                del element.attrib[key]
    return ET.tostring(root,encoding='utf-8')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path, help='Local text export or XML; never uploaded')
    parser.add_argument('--name', required=True, help='New fixture name, letters/digits/underscores')
    parser.add_argument('--expect', action='append', default=[], metavar='MODIFIER=RATING')
    parser.add_argument('--rationale', required=True, help='Why these expected decisions are correct')
    parser.add_argument('--label-origin', choices=['reviewer_judgment','in_game_test','conservative_policy'], default='reviewer_judgment')
    parser.add_argument('--split', choices=['development','holdout'], default='development')
    args=parser.parse_args()
    if not re.fullmatch(r'[a-z][a-z0-9_]{0,63}',args.name): parser.error('Use a lowercase fixture name.')
    if not args.expect: parser.error('Supply at least one reviewed --expect MODIFIER=RATING label.')
    raw=args.source.read_text(encoding='utf-8-sig').strip()
    xml=sanitize_export(raw)
    analysis=analyze_request({'source':base64.urlsafe_b64encode(zlib.compress(xml)).decode()})
    known={row['id'] for row in analysis['mods']}
    labels=[]
    for value in args.expect:
        mod,separator,rating=value.rpartition('=')
        if not separator or mod not in known or rating not in {'brick','dangerous','uncomfortable','free','review'}: parser.error('Unknown modifier or rating: '+value)
        labels.append(dict(modifier=mod,rating=rating,label_origin=args.label_origin,rationale=args.rationale))
    fixtures=ROOT/'tests/fixtures';target=fixtures/(args.name+'.xml')
    manifest_path=fixtures/'regression_manifest.json';manifest=json.loads(manifest_path.read_text(encoding='utf-8'))
    if target.exists() or any(row['id']==args.name for row in manifest['builds']): parser.error('Fixture already exists; review existing labels before changing it.')
    manifest['builds'].append(dict(id=args.name,fixture=target.name,sha256=hashlib.sha256(xml).hexdigest(),split=args.split,expectations=labels))
    target.write_bytes(xml)
    manifest_path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('Saved',target.name,'with',len(labels),'reviewed labels. Run scripts/validate_builds.py.')


if __name__=='__main__': main()
