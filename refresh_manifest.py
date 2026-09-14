"""Regenerate the explicit snapshot inventory after reviewing an intentional update."""
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent

if __name__ == '__main__':
    result = {'schema': 2, 'claude': [], 'codex': [], 'skipped': {'codex': ['.system']},
              'versions': json.loads((ROOT / 'kit/versions.json').read_text()), 'files': {}}
    for client in ['claude', 'codex']:
        result[client] = sorted(p.parent.name for p in (ROOT / client).glob('*/SKILL.md'))
    for directory in ['claude', 'codex', 'kit']:
        for p in sorted((ROOT / directory).rglob('*')):
            if p.is_file() and '__pycache__' not in p.parts:
                result['files'][p.relative_to(ROOT).as_posix()] = hashlib.sha256(p.read_bytes()).hexdigest()
    (ROOT / 'manifest.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8', newline='\n')
    print({c: len(result[c]) for c in ['claude', 'codex']}, 'files:', len(result['files']))
    report = ['# Platform-specific skill recipes', '',
              'Generated from the packaged skill files. Home paths are relocated by the installer; ',
              'Windows commands and application paths still need the named platform/app. ',
              'These are recipe indicators, not claims that an entire skill is Windows-only.', '',
              '| Source file | Indicators |', '|---|---|']
    for client in ['claude', 'codex']:
        for p in sorted((ROOT / client).rglob('*.md')):
            text = p.read_text('utf-8-sig')
            flags = []
            if re.search(r'(?i)powershell|\.ps1\b|\bwinget\b', text):
                flags.append('PowerShell/Windows command')
            if re.search(r'(?i)[A-Z]:[\\/]|\bAPPDATA\b|\.exe\b', text):
                flags.append('Windows path/executable example')
            if flags:
                name = p.relative_to(ROOT).as_posix()
                report.append(f'| [{name}](<{name}>) | {"; ".join(flags)} |')
    (ROOT / 'PORTABILITY.md').write_text('\n'.join(report) + '\n', encoding='utf-8', newline='\n')
