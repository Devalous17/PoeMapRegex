"""Refresh bundled PoB skill tags. Run manually; imports never fetch game data.

Only parses generated data declarations; does not execute downloaded Lua.
"""
from pathlib import Path
import hashlib
import json
import re
import urllib.request

REPO = 'https://api.github.com/repos/PathOfBuildingCommunity/PathOfBuilding/commits/dev'
req = urllib.request.Request(REPO, headers={'User-Agent': 'MapRegex-metadata'})
with urllib.request.urlopen(req, timeout=30) as response:
    revision = json.load(response)['sha']
skills = {}
hashes = {}
for filename in ('act_int.lua', 'act_dex.lua', 'act_str.lua', 'other.lua'):
    url = f'https://raw.githubusercontent.com/PathOfBuildingCommunity/PathOfBuilding/{revision}/src/Data/Skills/{filename}'
    with urllib.request.urlopen(url, timeout=30) as response:
        raw = response.read()
    hashes[filename] = hashlib.sha256(raw).hexdigest()
    for match in re.finditer(r'^skills\["([^"]+)"\] = \{(.*?)(?=^skills\[|\Z)', raw.decode(), re.M | re.S):
        skill_id, block = match.groups()
        name = re.search(r'^\s*name = "([^"]+)"', block, re.M)
        tags = re.search(r'^\s*skillTypes = \{([^\n]+)', block, re.M)
        if not name or not tags or re.search(r'^\s*support = true', block, re.M):
            continue
        skills[skill_id] = {'name': name[1], 'tags': re.findall(r'\[SkillType\.(\w+)\] = true', tags[1])}
payload = {'source': 'PathOfBuildingCommunity/PathOfBuilding', 'revision': revision,
           'files_sha256': hashes, 'skills': skills}
target = Path(__file__).resolve().parents[1] / 'skill_metadata.json'
target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(f'Bundled {len(skills)} active skills at {revision}')
