"""List every blanket Free allowance and the dependency question still to validate."""
import argparse
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from backend.policy_audit import policy_inventory


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    rows=policy_inventory()
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        if args.output.suffix=='.md':
            lines=['# Free-policy validation inventory','',
                   'These are explicit historical allowances, not verified safety decisions. Review priority is a work queue, not an automatic block rating. The existing selections remain available.','',
                   '| Modifier | Priority | Dependency question |','| --- | --- | --- |']
            for row in sorted(rows,key=lambda r:({'high':0,'medium':1,'lower':2}[r['priority']],r['id'])):
                lines.append('| '+row['modifier'].replace('|',' · ')+' | '+row['priority']+' | '+row['question']+' |')
            content='\n'.join(lines)+'\n'
        else:
            content=json.dumps(rows,ensure_ascii=False,indent=2)+'\n'
        args.output.write_text(content,encoding='utf-8')
    print(json.dumps(dict(total=len(rows),by_priority={p:sum(row['priority']==p for row in rows) for p in ['high','medium','lower']}),indent=2))


if __name__=='__main__': main()
