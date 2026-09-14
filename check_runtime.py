"""Smoke-test the installed kit without logins, model calls, or application edits."""
import argparse
import json
from pathlib import Path
import queue
import subprocess
import tempfile
import threading

import setup


def mcp(command, home, cwd, label):
    output = queue.Queue()
    env = setup.environment(home)
    env.update(CONTEXT_MODE_PROJECT_DIR=str(cwd), CONTEXT_MODE_DIR=str(cwd / label),
               CONTEXT_MODE_DATA_DIR=str(cwd / label))
    with tempfile.TemporaryFile(mode='w+b') as errors:
        child = subprocess.Popen(command, cwd=cwd, env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                 stderr=errors, text=True, encoding='utf-8')
        def receive():
            for line in child.stdout:
                output.put(line)
            output.put(None)
        reader = threading.Thread(target=receive, daemon=True)
        reader.start()
        def send(value):
            child.stdin.write(json.dumps(value) + '\n')
            child.stdin.flush()
        def response(identifier):
            while True:
                try:
                    line = output.get(timeout=45)
                except queue.Empty as exc:
                    raise RuntimeError(label + ' MCP timed out') from exc
                if line is None:
                    errors.seek(0)
                    raise RuntimeError(label + ' MCP closed: ' + errors.read().decode('utf-8', errors='replace'))
                message = json.loads(line)
                if message.get('id') == identifier:
                    if 'error' in message:
                        raise RuntimeError(str(message['error']))
                    return message['result']
        try:
            send({'jsonrpc': '2.0', 'id': 1, 'method': 'initialize', 'params': {
                'protocolVersion': '2024-11-05', 'capabilities': {}, 'clientInfo': {'name': 'skills-kit-smoke', 'version': '1'}}})
            response(1)
            send({'jsonrpc': '2.0', 'method': 'notifications/initialized'})
            send({'jsonrpc': '2.0', 'id': 2, 'method': 'tools/list', 'params': {}})
            names = {tool['name'] for tool in response(2)['tools']}
            if not set(setup.TOOLS).issubset(names):
                raise RuntimeError(label + ' is missing required tools: ' + str(set(setup.TOOLS) - names))
            send({'jsonrpc': '2.0', 'id': 3, 'method': 'tools/call', 'params': {
                'name': 'ctx_execute', 'arguments': {'language': 'javascript', 'code': 'console.log("skills-kit-smoke-ok")'}}})
            result = response(3)
            if result.get('isError') or 'skills-kit-smoke-ok' not in json.dumps(result):
                raise RuntimeError(label + ' execution failed: ' + str(result))
            print(label + ': initialized, tools verified, local execution passed')
        finally:
            child.stdin.close()
            try:
                child.wait(timeout=10)
            except subprocess.TimeoutExpired:
                child.terminate()
                child.wait(timeout=10)
            reader.join(timeout=5)
            child.stdout.close()


def main(home):
    home = home.resolve()
    runtime = home / '.local/share/skills-kit/runtime'
    registry = setup.read_json(home / '.claude/plugins/installed_plugins.json')
    settings = setup.read_json(home / '.claude/settings.json')
    for name in setup.CLIENT_PLUGINS['claude']:
        entries = registry.get('plugins', {}).get(name + '@skills-kit', [])
        if not entries or not Path(entries[0]['installPath']).is_dir() or not settings.get('enabledPlugins', {}).get(name + '@skills-kit'):
            raise RuntimeError('Missing Claude plugin: ' + name)
    result = setup.run(['codex', 'plugin', 'list', '--json'], home, json_result=True)
    # Schema differs from Claude; inspect the native installed+enabled inventory.
    plugins = result['installed']
    for name in setup.CLIENT_PLUGINS['codex']:
        if not any(p.get('id', p.get('pluginId')) == name + '@skills-kit' and p.get('installed') and p.get('enabled') for p in plugins):
            raise RuntimeError('Codex plugin is not installed/enabled: ' + name)
    with tempfile.TemporaryDirectory(prefix='kit runtime ') as tmp:
        cwd = Path(tmp)
        mcp([setup.sys.executable, str(runtime / 'context-mode-launcher.py')], home, cwd, 'codex-context')
        context = Path(registry['plugins']['context-mode@skills-kit'][0]['installPath'])
        mcp(['node', str(context / 'start.mjs')], home, cwd, 'claude-context')
        output = setup.run(['node', str(runtime / 'hyperframes-runtime/node_modules/hyperframes/bin/hyperframes.mjs'), '--version'], home, cwd)
        if '0.8.36' not in output:
            raise RuntimeError('Unexpected HyperFrames version: ' + output)
        setup.run([setup.sys.executable, str(home / '.claude/vault-automation/vaultctl.py'), 'validate'], home, cwd)
    print('Runtime smoke checks passed. Interactive login, hook trust and Obsidian acceptance remain manual.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--home', type=Path, default=Path.home())
    main(parser.parse_args().home)
