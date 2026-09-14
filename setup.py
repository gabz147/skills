#!/usr/bin/env python3
"""Install the private CLI kit on Windows/macOS. Preview unless --apply is supplied."""
import argparse
import datetime as dt
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
if sys.version_info < (3, 11):
    raise SystemExit('This setup requires Python 3.11 or newer; install it before continuing.')
import tomllib

for stream in (sys.stdout, sys.stderr):
    if hasattr(stream, 'reconfigure'):
        stream.reconfigure(encoding='utf-8')

ROOT = Path(__file__).resolve().parent
KIT = ROOT / 'kit'
CLIENT_PLUGINS = {'claude': ['skill-creator', 'superpowers', 'frontend-design', 'context-mode'],
                  'codex': ['ecc', 'ponytail']}
TOOLS = ['ctx_execute', 'ctx_execute_file', 'ctx_index', 'ctx_search',
         'ctx_fetch_and_index', 'ctx_batch_execute', 'ctx_stats']
NATIVE_FILES = ['.claude/settings.json', '.claude.json', '.codex/config.toml',
                '.claude/plugins/known_marketplaces.json', '.claude/plugins/installed_plugins.json',
                '.claude/hooks/context-mode-cache-heal.mjs']


def encoded(value):
    return (json.dumps(value, indent=2, ensure_ascii=False) + '\n').encode('utf-8')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8-sig')) if path.exists() else {}


def toml(data):
    """Preserve all parsed values; comments/formatting are retained in the backup."""
    def value(v):
        if isinstance(v, dict):
            return '{' + ', '.join(json.dumps(k) + ' = ' + value(x) for k, x in v.items()) + '}'
        if isinstance(v, list):
            return '[' + ', '.join(value(x) for x in v) + ']'
        if isinstance(v, (dt.datetime, dt.date, dt.time)):
            return v.isoformat()
        if isinstance(v, float):
            return repr(v)
        return json.dumps(v, ensure_ascii=False)
    lines = []
    def table(obj, keys):
        if keys:
            lines.append('[' + '.'.join(json.dumps(k) for k in keys) + ']')
        lines.extend(json.dumps(k) + ' = ' + value(v) for k, v in obj.items() if not isinstance(v, dict))
        for k, v in obj.items():
            if isinstance(v, dict):
                table(v, keys + [k])
    table(data, [])
    result = '\n'.join(lines) + '\n'
    assert tomllib.loads(result) == data
    return result.encode('utf-8')


def contained(path, root):
    if not path.resolve().is_relative_to(root.resolve()):
        raise ValueError(f'Path escapes installation root (including symlinks): {path}')


def portable(data, home, runtime):
    """Relocate explicit workstation paths in skill documentation, not arbitrary code."""
    text = data.decode('utf-8-sig')
    replacements = [('C:/Users/Tarlu/Developer/agent-tooling/2026-09-12', runtime.as_posix()),
                    ('C:/Users/Tarlu', home.as_posix())]
    # Use tokens so a destination inside the original home is never relocated twice.
    for i, (old, _) in enumerate(replacements):
        text = text.replace(old, f'__KIT_POSIX_{i}__').replace(old.replace('/', '\\'), f'__KIT_WIN_{i}__')
    for i, (_, new) in enumerate(replacements):
        token = f'__KIT_WIN_{i}__'
        text = re.sub(token + r'[^`\n\r"<>]*', lambda m: new + m.group()[len(token):].replace('\\', '/'), text)
        text = text.replace(f'__KIT_POSIX_{i}__', new)
    return text.encode('utf-8')


def verify_sources():
    manifest = read_json(ROOT / 'manifest.json')
    actual = {p.relative_to(ROOT).as_posix() for base in ['claude', 'codex', 'kit']
              for p in (ROOT / base).rglob('*') if p.is_file() and '__pycache__' not in p.parts}
    expected = manifest['files']
    if actual != set(expected):
        raise ValueError('Snapshot inventory differs from manifest; run refresh_manifest.py after reviewing changes')
    for name, digest in expected.items():
        p = ROOT / name
        contained(p, ROOT)
        if sha(p.read_bytes()) != digest:
            raise ValueError('Snapshot checksum mismatch: ' + name)
    return manifest


def plan(home, vault, client='all', skills_only=False, replace=False, blender=None, roblox=None):
    for root in (ROOT, home / '.claude', home / '.codex', home / '.local/share/skills-kit'):
        if vault == root or vault in root.parents or root in vault.parents:
            raise ValueError('Vault must be separate from the checkout and client/runtime directories')
    files = {}
    runtime = home / '.local/share/skills-kit/runtime'
    clients = ['claude', 'codex'] if client == 'all' else [client]
    for c in clients:
        for p in (ROOT / c).rglob('*'):
            if p.is_file():
                if not skills_only and p.relative_to(ROOT / c).parts[0] in {'obsidian-vault', 'handoff', 'source-to-vault'}:
                    continue
                data = p.read_bytes()
                if p.suffix == '.md':
                    data = portable(data, home, runtime)
                files[home / f'.{c}/skills' / p.relative_to(ROOT / c)] = data
    if skills_only:
        return checked(files, home, vault, replace)

    if client != 'all':
        raise ValueError('--client requires --skills-only; the full kit coordinates both clients')
    spec = importlib.util.spec_from_file_location('brain_install', KIT / 'agent-brain/install.py')
    brain = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(brain)
    # Overlay the canonical portable vault skills over the historical snapshots.
    files.update(brain.installation(home, vault, replace=True))
    for source, target in [(KIT / 'gsd', home / '.claude'),
                           (KIT / 'runtime', runtime), (KIT / 'plugins', runtime.parent / 'marketplace/plugins'),
                           (KIT / '.claude-plugin', runtime.parent / 'marketplace/.claude-plugin')]:
        for p in source.rglob('*'):
            if p.is_file() and '__pycache__' not in p.parts:
                files[target / p.relative_to(source)] = p.read_bytes()
    files[home / '.claude/statusline.py'] = (KIT / 'statusline.py').read_bytes()
    for name in ['notify.py', 'notify-done.ps1']:
        files[home / '.claude/hooks' / name] = (KIT / name).read_bytes()

    settings_path = home / '.claude/settings.json'
    settings = json.loads(files.get(settings_path, encoded(read_json(settings_path))))
    settings.setdefault('model', 'claude-opus-5')
    settings.setdefault('effortLevel', 'high')
    for selector in settings.get('enabledPlugins', {}):
        if selector.split('@')[0] in CLIENT_PLUGINS['claude'] and not selector.endswith('@skills-kit'):
            settings['enabledPlugins'][selector] = False
    settings['statusLine'] = {'type': 'command', 'command': shell_command([sys.executable, str(home / '.claude/statusline.py')])}
    settings.setdefault('env', {}).update(BRAIN_VAULT_ROOT=str(vault),
                                        BRAIN_AUTOMATION_DIR=str(home / '.claude/vault-automation'),
                                        BRAIN_PYTHON=sys.executable,
                                        HYPERFRAMES_NO_TELEMETRY='1', HYPERFRAMES_NO_UPDATE_CHECK='1')
    hooks = settings.setdefault('hooks', {})
    for event, extra in [('Stop', []), ('Notification', ['--waiting'])]:
        command = shell_command([sys.executable, str(home / '.claude/hooks/notify.py')] + extra)
        groups = hooks.setdefault(event, [])
        if not any('notify' in h.get('command', '') for g in groups for h in g.get('hooks', [])):
            groups.append({'hooks': [{'type': 'command', 'command': command, 'timeout': 20, 'async': True}]})
    entries = [('SessionStart', '', 'gsd-session-state.sh'),
               ('PostToolUse', 'Bash|Edit|Write|MultiEdit|Agent|Task', 'gsd-context-monitor.js'),
               ('PostToolUse', 'Read', 'gsd-read-injection-scanner.js'),
               ('PostToolUse', 'Write|Edit', 'gsd-phase-boundary.sh'),
               ('PreToolUse', 'Write|Edit', 'gsd-prompt-guard.js'),
               ('PreToolUse', 'Write|Edit', 'gsd-read-guard.js'),
               ('PreToolUse', 'Write|Edit', 'gsd-workflow-guard.js'),
               ('PreToolUse', 'Bash', 'gsd-validate-commit.sh')]
    for event, matcher, name in entries:
        command = shell_command([bash_path() if name.endswith('.sh') else 'node', str(home / '.claude/hooks' / name)])
        groups = hooks.setdefault(event, [])
        matches = [h for g in groups for h in g.get('hooks', []) if name in h.get('command', '')]
        if matches:
            # Preserve grouping/options; only relocate this package-owned command.
            for hook in matches:
                hook['command'] = command
        else:
            groups.append({'matcher': matcher, 'hooks': [{'type': 'command', 'command': command, 'timeout': 10}]})
    files[settings_path] = encoded(settings)

    config_path = home / '.codex/config.toml'
    config = tomllib.loads(config_path.read_text('utf-8-sig')) if config_path.exists() else {}
    config.setdefault('model', 'gpt-6-astra')
    config.setdefault('model_reasoning_effort', 'high')
    for selector, entry in config.get('plugins', {}).items():
        if selector.split('@')[0] in CLIENT_PLUGINS['codex'] and not selector.endswith('@skills-kit'):
            entry['enabled'] = False
    config.setdefault('tui', {}).setdefault('status_line', ['model-with-reasoning', 'fast-mode', 'current-dir',
                                                         'git-branch', 'context-used', 'five-hour-limit', 'weekly-limit'])
    config.setdefault('shell_environment_policy', {}).setdefault('set', {}).update(settings['env'])
    mcp = config.setdefault('mcp_servers', {})
    mcp.setdefault('openaiDeveloperDocs', {'url': 'https://developers.openai.com/mcp'})
    mcp['context-mode'] = {'command': sys.executable, 'args': [str(runtime / 'context-mode-launcher.py')], 'enabled_tools': TOOLS}
    for executable_path in [blender, roblox]:
        if executable_path and not executable_path.is_file():
            raise ValueError('Optional MCP executable is missing: ' + str(executable_path))
    if blender:
        mcp['blender'] = {'command': str(blender), 'startup_timeout_sec': 120, 'tool_timeout_sec': 240,
                          'enabled_tools': ['get_scene_info', 'get_object_info', 'get_viewport_screenshot', 'execute_blender_code'],
                          'env': {'BLENDER_HOST': '127.0.0.1', 'BLENDER_PORT': '9876', 'BLENDER_MCP_DISABLE_TELEMETRY': '1',
                                  'PYTHONIOENCODING': 'utf-8', 'PYTHONUTF8': '1'}}
    if roblox:
        mcp['Roblox_Studio'] = {'command': str(roblox)}
        claude_path = home / '.claude.json'
        claude_config = read_json(claude_path)
        claude_config.setdefault('mcpServers', {})['Roblox_Studio'] = {'type': 'stdio', 'command': str(roblox), 'args': []}
        files[claude_path] = encoded(claude_config)
    existing_config = config_path.read_bytes() if config_path.exists() else None
    files[config_path] = (existing_config if existing_config is not None and
                          tomllib.loads(existing_config.decode('utf-8-sig')) == config else toml(config))
    return checked(files, home, vault, replace)


def checked(files, home, vault, replace):
    changed = {}
    conflicts = []
    for target, data in files.items():
        if target.suffix in {'.sh', '.cmd'}:
            data = data.replace(b'\r\n', b'\n')
        contained(target, vault if target.is_relative_to(vault) else home)
        if target.exists():
            if not target.is_file():
                raise ValueError('Expected a file: ' + str(target))
            if target.read_bytes() == data:
                continue
            if not replace:
                conflicts.append(str(target))
        changed[target] = data
    if conflicts:
        raise ValueError('Existing files differ. Review, then use --replace (backs up every replacement):\n' + '\n'.join(conflicts))
    return changed


def shell_command(args):
    # Claude runs hooks through a shell on both platforms. Double-quote paths,
    # escaping shell expansion; normalize Windows separators for Git Bash.
    return ' '.join('"' + str(a).replace('\\', '/').replace('"', '\\"').replace('$', '\\$').replace('`', '\\`') + '"' for a in args)


def bash_path():
    if os.name == 'nt':
        for candidate in [os.environ.get('CLAUDE_CODE_GIT_BASH_PATH', ''),
                          'C:/Program Files/Git/bin/bash.exe', 'C:/Program Files (x86)/Git/bin/bash.exe']:
            if candidate and Path(candidate).is_file():
                return candidate
    return shutil.which('bash') or 'bash'


def executable(name):
    found = shutil.which(name)
    if not found:
        raise ValueError(f'{name} is missing from PATH')
    if Path(found).suffix.lower() == '.cmd' and name in {'codex', 'claude'}:
        package = Path(found).parent / 'node_modules' / ('@openai/codex' if name == 'codex' else '@anthropic-ai/claude-code')
        entry = read_json(package / 'package.json').get('bin', {})
        entry = entry.get(name) if isinstance(entry, dict) else entry
        if not isinstance(entry, str):
            raise ValueError(f'Missing {name} package executable declaration')
        script = package / entry
        contained(script, package)
        if not script.is_file():
            raise ValueError(f'Unsupported {name} shim: {found}; install the official CLI')
        return [shutil.which('node'), str(script)] if script.suffix in {'.js', '.mjs', '.cjs'} else [str(script)]
    return [found]


def atomic(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as f:
        f.write(data)
        tmp = Path(f.name)
    try:
        os.replace(tmp, path)
    finally:
        tmp.unlink(missing_ok=True)
    if path.read_bytes() != data:
        raise OSError('Read-back failed: ' + str(path))
    if path.suffix in {'.sh', '.cmd'} or data.startswith(b'#!'):
        path.chmod(path.stat().st_mode | 0o111)


def write_files(files, home, native=False):
    backup = home / '.local/state/skills-kit/backups' / dt.datetime.now().strftime('%Y%m%d-%H%M%S-%f')
    contained(backup, home)
    backup.mkdir(parents=True, mode=0o700)
    records = []
    # Prepare all before-images before the first installation write.
    for target, data in files.items():
        before = target.read_bytes() if target.exists() else None
        name = f'{len(records):05}.bak' if before is not None else None
        if before is not None:
            atomic(backup / name, before)
        records.append({'target': str(target), 'backup': name, 'before': sha(before) if before is not None else None,
                        'after': sha(data)})
    if native:
        for relative in NATIVE_FILES:
            target = home / relative
            contained(target, home)
            if target in files:
                continue
            before = target.read_bytes() if target.exists() else None
            name = f'{len(records):05}.bak' if before is not None else None
            if before is not None:
                atomic(backup / name, before)
            records.append({'target': str(target), 'backup': name,
                            'before': sha(before) if before is not None else None, 'after': None})
    atomic(backup / 'manifest.json', encoded(records))
    for target, record in zip(files, records):
        current = sha(target.read_bytes()) if target.exists() else None
        if current != record['before']:
            raise ValueError('Concurrent edit; installation stopped: ' + str(target))
        atomic(target, files[target])
    return backup


def record_native(backup, home):
    records = read_json(backup / 'manifest.json')
    paths = {home / relative for relative in NATIVE_FILES}
    for record in records:
        path = Path(record['target'])
        if path in paths:
            record['after'] = sha(path.read_bytes()) if path.exists() else None
    atomic(backup / 'manifest.json', encoded(records))


def restore(manifest, home, vault, apply=False):
    changes = []
    for record in read_json(manifest):
        target = Path(record['target'])
        contained(target, vault if target.is_relative_to(vault) else home)
        current = sha(target.read_bytes()) if target.exists() else None
        if current == record['before']:
            continue
        if current != record['after']:
            raise ValueError('Changed since installation; refusing to overwrite: ' + str(target))
        data = None
        if record['backup']:
            saved = manifest.parent / record['backup']
            contained(saved, manifest.parent)
            data = saved.read_bytes()
            if sha(data) != record['before']:
                raise ValueError('Corrupt backup: ' + str(saved))
        changes.append((target, data, record['after']))
    print(f'{len(changes)} file changes to restore. Downloaded caches remain on disk.')
    if apply:
        for target, data, expected in changes:
            if (sha(target.read_bytes()) if target.exists() else None) != expected:
                raise ValueError('Concurrent edit during restore: ' + str(target))
            if data is None:
                target.unlink()
            else:
                atomic(target, data)


def environment(home):
    env = os.environ.copy()
    env.update(HOME=str(home), USERPROFILE=str(home), CODEX_HOME=str(home / '.codex'),
               CLAUDE_CONFIG_DIR=str(home / '.claude'), PYTHONIOENCODING='utf-8',
               HYPERFRAMES_NO_TELEMETRY='1', HYPERFRAMES_NO_UPDATE_CHECK='1')
    # Native plugin administration must never inherit an enclosing Claude session.
    env.pop('CLAUDECODE', None)
    configured = read_json(home / '.claude/settings.json').get('env', {})
    env.update({k: v for k, v in configured.items() if k in {'BRAIN_VAULT_ROOT', 'BRAIN_AUTOMATION_DIR', 'BRAIN_PYTHON'}})
    return env


def run(args, home, cwd=None, json_result=False):
    args = executable(args[0]) + args[1:] if args[0] in {'claude', 'codex'} else args
    print('RUN ' + ' '.join(map(str, args)), flush=True)
    proc = subprocess.run(list(map(str, args)), env=environment(home), cwd=cwd,
                          capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=900)
    if proc.returncode:
        raise RuntimeError(proc.stdout + proc.stderr)
    if json_result:
        # Some native Codex failures return exit zero; require a structured result.
        try:
            return json.loads(proc.stdout)
        except ValueError as exc:
            raise RuntimeError(proc.stdout + proc.stderr) from exc
    if proc.stdout.strip():
        print(proc.stdout.strip(), flush=True)
    return proc.stdout


def npm_command():
    npm = Path(shutil.which('npm') or '')
    candidate = npm.parent / 'node_modules/npm/bin/npm-cli.js' if os.name == 'nt' else npm.resolve()
    if not candidate.is_file():
        raise ValueError('Install Node.js with npm on PATH before --apply')
    return [shutil.which('node'), str(candidate)]


def dependencies(directory, home):
    npm = npm_command()
    run(npm + ['ci', '--omit=dev', '--ignore-scripts', '--no-audit', '--no-fund'], home, directory)
    if (directory / 'node_modules/better-sqlite3').exists():
        run(npm + ['rebuild', 'better-sqlite3', '--ignore-scripts=false'], home, directory)
        run(['node', '-e', "new (require('better-sqlite3'))(':memory:').close()"], home, directory)


def finish(home):
    base = home / '.local/share/skills-kit'
    for directory in ['context-mode', 'hyperframes-runtime']:
        dependencies(base / 'runtime' / directory, home)
    for client, plugins in CLIENT_PLUGINS.items():
        result = run([client, 'plugin', 'marketplace', 'add', str(base / 'marketplace')] +
                     (['--json'] if client == 'codex' else []), home, json_result=client == 'codex')
        for plugin in plugins:
            result = run([client, 'plugin', 'add' if client == 'codex' else 'install', plugin + '@skills-kit', '--json'],
                         home, json_result=True)
            if client == 'codex' and result.get('pluginId') != plugin + '@skills-kit':
                raise RuntimeError('Plugin install did not return the requested plugin: ' + str(result))
        if client == 'claude':
            registry = read_json(home / '.claude/plugins/installed_plugins.json')
            for plugin in plugins:
                entries = registry.get('plugins', {}).get(plugin + '@skills-kit', [])
                if not entries or not Path(entries[0]['installPath']).is_dir():
                    raise RuntimeError('Missing installed plugin: ' + plugin)
            context = Path(registry['plugins']['context-mode@skills-kit'][0]['installPath'])
            dependencies(context, home)
    run([sys.executable, str(home / '.claude/vault-automation/vaultctl.py'), 'validate'], home)
    from check_runtime import main as check_runtime
    check_runtime(home)


def doctor(home):
    issues = []
    for exe in ['git', 'node', 'npm', 'bash', 'claude', 'codex']:
        found = bash_path() if exe == 'bash' else shutil.which(exe)
        print(f'{exe}: {found or "MISSING"}')
        if not found:
            issues.append(exe)
    try:
        subprocess.run([bash_path(), '-c', ':'], check=True, capture_output=True, timeout=15)
    except (OSError, subprocess.SubprocessError):
        issues.append('working Bash (Git Bash on Windows)')
    if sys.version_info < (3, 11):
        issues.append('Python 3.11+')
    if shutil.which('node'):
        version = subprocess.check_output(['node', '-p', 'process.versions.node'], text=True).strip()
        if tuple(map(int, version.split('.'))) < (22, 5, 0):
            issues.append('Node 22.5+')
    print('Manual setup: log into both clients; approve native plugin hooks in each client; open Brain in Obsidian.')
    print('Application integrations (Blender, Roblox, Resolve) and optional Windows scheduling: see SETUP.md.')
    return issues


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--home', type=Path, default=Path.home())
    parser.add_argument('--vault', type=Path)
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--replace', action='store_true', help='Back up and replace differing package files; preserve unrelated files')
    parser.add_argument('--skills-only', action='store_true')
    parser.add_argument('--client', choices=['all', 'claude', 'codex'], default='all')
    parser.add_argument('--files-only', action='store_true', help='Stage files without native plugin/dependency installation; incomplete offline setup')
    parser.add_argument('--doctor', action='store_true')
    parser.add_argument('--blender-server', type=Path, help='Existing blender-mcp executable; adds the four reviewed Codex tools')
    parser.add_argument('--roblox-server', type=Path, help='Existing StudioMCP executable; adds its direct command to both clients')
    parser.add_argument('--restore', type=Path, help='Preview recovery from a backup manifest; --apply performs it')
    args = parser.parse_args()
    home = args.home.expanduser().resolve()
    configured_vault = read_json(home / '.claude/settings.json').get('env', {}).get('BRAIN_VAULT_ROOT')
    vault = (args.vault or (Path(configured_vault) if configured_vault else home / 'Documents/Brain')).expanduser().resolve()
    if args.restore:
        restore(args.restore.resolve(), home, vault, args.apply)
        return 0
    if args.doctor:
        return bool(doctor(home))
    manifest = verify_sources()
    if args.skills_only and (args.blender_server or args.roblox_server):
        parser.error('Optional MCP connections require the full kit')
    files = plan(home, vault, args.client, args.skills_only, args.replace,
                 args.blender_server.expanduser().resolve() if args.blender_server else None,
                 args.roblox_server.expanduser().resolve() if args.roblox_server else None)
    print(f'Verified {len(manifest["files"])} source files; {len(files)} files to write under {home}; vault {vault}')
    if not args.apply:
        print('Preview only. Full apply also installs pinned npm dependencies and native plugins. Use --apply to proceed.')
        return 0
    if not args.skills_only and not args.files_only and doctor(home):
        raise ValueError('Missing prerequisites; no files installed')
    backup = write_files(files, home, native=not args.skills_only and not args.files_only)
    print('Backup manifest: ' + str(backup / 'manifest.json'), flush=True)
    if not args.skills_only and not args.files_only:
        try:
            finish(home)
        finally:
            record_native(backup, home)
    print('Files verified. ' + ('Offline stage only; dependencies/plugins still pending.' if args.files_only else 'Restart both clients; complete the acceptance checks in SETUP.md.'))
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (ValueError, OSError, RuntimeError, subprocess.SubprocessError) as exc:
        print('SETUP FAILED: ' + str(exc), file=sys.stderr)
        raise SystemExit(1)
