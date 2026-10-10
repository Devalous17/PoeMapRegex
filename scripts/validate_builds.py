"""Run all saved build labels and optionally write a portable JSON report."""
import argparse
import json
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.regression import run_suite


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, default=ROOT/'tests/fixtures/regression_manifest.json')
    parser.add_argument('--output', type=Path, help='Optional complete JSON report destination')
    args = parser.parse_args()
    report = run_suite(args.manifest)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(report['metrics'], indent=2))
    for build in report['builds']:
        if build['status'] != 'pass':
            print(build['build'], build['status'])
            for row in build['checks']:
                if not row['passed']: print(' ', row['modifier'], 'expected', row['expected'], 'got', row['actual'])
    return 0 if report['success'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
