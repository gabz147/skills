"""Run with python -m unittest -v test_setup. Uses disposable homes, never live profiles."""
import contextlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import tomllib
import unittest

import setup


class SetupIntegration(unittest.TestCase):
    def test_full_install_merge_repeat_backup_and_runtimes(self):
        setup.verify_sources()
        with tempfile.TemporaryDirectory(prefix='skills kit ') as tmp:
            home = Path(tmp) / 'home with spaces'
            vault = Path(tmp) / 'custom vault'
            settings_path = home / '.claude/settings.json'
            settings_path.parent.mkdir(parents=True)
            original = {'permissions': {'deny': ['Read(.env)']}, 'model': 'keep-existing-model',
                        'hooks': {'Stop': [{'hooks': [{'type': 'command', 'command': 'echo unrelated'}]}]}}
            settings_path.write_text(json.dumps(original), encoding='utf-8')
            config_path = home / '.codex/config.toml'
            config_path.parent.mkdir()
            config_path.write_text('approval_policy = "on-request"\n[projects."/existing project"]\ntrust_level = "untrusted"\n')
            with self.assertRaisesRegex(ValueError, 'Existing files differ'):
                setup.plan(home, vault)
            files = setup.plan(home, vault, replace=True)
            before = settings_path.read_bytes()
            with contextlib.redirect_stdout(io.StringIO()):
                backup = setup.write_files(files, home)
            records = setup.read_json(backup / 'manifest.json')
            saved = next(r for r in records if r['target'] == str(settings_path))
            self.assertEqual((backup / saved['backup']).read_bytes(), before)
            settings = setup.read_json(settings_path)
            self.assertEqual(settings['permissions'], original['permissions'])
            self.assertEqual(settings['model'], original['model'])
            self.assertEqual(settings['skillOverrides']['gsd-plan-phase'], 'name-only')
            self.assertEqual(settings['skillOverrides']['design-taste-frontend-v1'], 'name-only')
            self.assertIn(original['hooks']['Stop'][0], settings['hooks']['Stop'])
            config = tomllib.loads(config_path.read_text())
            self.assertEqual(config['approval_policy'], 'on-request')
            self.assertEqual(config['projects']['/existing project']['trust_level'], 'untrusted')
            self.assertEqual(config['shell_environment_policy']['set']['PONYTAIL_DEFAULT_MODE'], 'off')
            self.assertFalse(config['skills']['include_instructions'])
            self.assertIn(setup.COMPACT_CODING_DEFAULTS, (home / '.codex/AGENTS.md').read_text(encoding='utf-8'))
            self.assertIn(setup.ON_DEMAND_SKILLS.format(home=home.as_posix()),
                          (home / '.codex/AGENTS.md').read_text(encoding='utf-8'))
            self.assertEqual(config['mcp_servers']['context-mode']['enabled_tools'], setup.TOOLS)
            self.assertNotIn('hooks', config)  # Never carry over native hook trust hashes.
            self.assertFalse(setup.plan(home, vault))
            note = vault / 'Active Priorities.md'
            note.write_bytes(note.read_bytes() + b'\nPrivate local addition\n')
            extra = home / '.codex/skills/context-output-tools/local-only.txt'
            extra.write_text('keep me')
            setup.write_files(setup.plan(home, vault, replace=True), home)
            self.assertIn(b'Private local addition', note.read_bytes())
            self.assertEqual(extra.read_text(), 'keep me')
            for client in ['claude', 'codex']:
                for name in setup.read_json(setup.ROOT / 'manifest.json')[client]:
                    self.assertTrue((home / f'.{client}/skills' / name / 'SKILL.md').is_file(), name)
            for p in (home / '.codex/skills').rglob('*.md'):
                relocated = p.read_text('utf-8').replace(home.as_posix(), '<HOME>')
                self.assertNotIn('C:\\Users\\Tarlu', relocated, str(p))
                self.assertNotIn('C:/Users/Tarlu', relocated, str(p))
            context_skill = (home / '.codex/skills/context-output-tools/SKILL.md').read_text('utf-8')
            self.assertIn((home / '.local/share/skills-kit/runtime/context-mode-launcher.py').as_posix(), context_skill)
            env = setup.environment(home)
            auto = home / '.claude/vault-automation/vaultctl.py'
            result = subprocess.run([sys.executable, str(auto), 'validate'], env=env, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            # Exercise real GSD command resolution and the actual statusline renderer.
            result = subprocess.run(['node', str(home / '.claude/get-shit-done/bin/gsd-tools.cjs'), 'current-timestamp'],
                                    env=env, cwd=home, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            result = subprocess.run([sys.executable, str(home / '.claude/statusline.py')],
                                    input='{"session_id":"fixture-check","model":{"display_name":"fixture"},"context_window":{"used_percentage":25}}',
                                    env=dict(env, TMP=str(home), TEMP=str(home), TMPDIR=str(home)), capture_output=True, text=True, encoding='utf-8')
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn('fixture', result.stdout)
            self.assertIn('25%', result.stdout)
            self.assertEqual(json.loads((home / 'claude-ctx-fixture-check.json').read_text())['remaining_percentage'], 75)
            # Recovery refuses to overwrite local work modified since installation.
            with self.assertRaisesRegex(ValueError, 'Changed since installation'):
                setup.restore(backup / 'manifest.json', home, vault)

    def test_existing_context_choices_and_plugin_mode_are_preserved(self):
        with tempfile.TemporaryDirectory(prefix='context defaults ') as tmp:
            home = Path(tmp) / 'home'
            vault = Path(tmp) / 'vault'
            settings = home / '.claude/settings.json'
            settings.parent.mkdir(parents=True)
            settings.write_text(json.dumps({'skillOverrides': {'gsd-plan-phase': 'on', 'custom': 'off'}}))
            config = home / '.codex/config.toml'
            config.parent.mkdir()
            config.write_text('[shell_environment_policy.set]\nPONYTAIL_DEFAULT_MODE = "full"\n'
                              '[skills]\ninclude_instructions = true\nmax_context_tokens = 1200\n')
            files = setup.plan(home, vault, replace=True)
            result = json.loads(files[settings])
            self.assertEqual(result['skillOverrides']['gsd-plan-phase'], 'on')
            self.assertEqual(result['skillOverrides']['custom'], 'off')
            self.assertEqual(tomllib.loads(files.get(config, config.read_bytes()).decode())['shell_environment_policy']['set']['PONYTAIL_DEFAULT_MODE'], 'full')
            self.assertEqual(tomllib.loads(files[config].decode())['skills'],
                             {'include_instructions': True, 'max_context_tokens': 1200})
            self.assertNotIn('## On-demand skills', files[home / '.codex/AGENTS.md'].decode())
            # Exercise the packaged resolver, not a duplicate of its mode logic.
            script = setup.KIT / 'plugins/ponytail/hooks/ponytail-config.js'
            for mode in ('off', 'full'):
                proc = subprocess.run(['node', '-e', 'process.stdout.write(require(process.argv[1]).getDefaultMode())', str(script)],
                                      env=dict(os.environ, PONYTAIL_DEFAULT_MODE=mode), capture_output=True, text=True)
                self.assertEqual(proc.returncode, 0, proc.stderr)
                self.assertEqual(proc.stdout, mode)

    def test_boundaries_and_invalid_arguments(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            with self.assertRaisesRegex(ValueError, 'separate'):
                setup.plan(home, home / '.claude/vault')
            with self.assertRaises(ValueError):
                setup.contained(home.parent / 'escape', home)
            proc = subprocess.run([sys.executable, str(setup.ROOT / 'setup.py'), '--client', 'typo'], capture_output=True)
            self.assertNotEqual(proc.returncode, 0)
            sample = {'mcp_servers': {'a.b': {'command': 'a "quoted" \\ path', 'args': ['x', 'y']}},
                      'values': [{'nested': [1, 2]}, {'enabled': False}], 'f': 1.25}
            self.assertEqual(tomllib.loads(setup.toml(sample).decode()), sample)
            existing, created = home / 'existing.txt', home / 'created.txt'
            existing.write_bytes(b'original')
            backup = setup.write_files({existing: b'replacement', created: b'new'}, home)
            setup.restore(backup / 'manifest.json', home, home / 'Documents/Brain', apply=True)
            self.assertEqual(existing.read_bytes(), b'original')
            self.assertFalse(created.exists())
            wrapper = (['powershell.exe', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', str(setup.ROOT / 'install.ps1'),
                        '-SkillsOnly', '-TargetHome', str(home)] if os.name == 'nt' else
                       [str(setup.ROOT / 'install.sh'), '--skills-only', '--home', str(home)])
            proc = subprocess.run(wrapper, capture_output=True, text=True, encoding='utf-8')
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            self.assertIn('Preview only', proc.stdout)


if __name__ == '__main__':
    unittest.main()
