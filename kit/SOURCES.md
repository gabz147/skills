# Snapshot provenance

Prepared 2026-09-13 by astra (`gpt-6-astra`). Exact packaged bytes are recorded
in the root `manifest.json`; versions/revisions are in `kit/versions.json`.

| Snapshot | Original source |
|---|---|
| `agent-brain` | [gabz147/agent-brain](https://github.com/gabz147/agent-brain), ae54ef9; public generic template, never the private Brain vault |
| `statusline.py` | [gabz147/cli-statusline](https://github.com/gabz147/cli-statusline), 07b8004 |
| `gsd` | Installed get-shit-done-cc 1.40.0 workflows, helpers, agents and hooks |
| `plugins/ecc` | [affaan-m/ECC](https://github.com/affaan-m/ECC), installed 2.2.1 native Codex package |
| `plugins/ponytail` | [DietrichGebert/ponytail](https://github.com/DietrichGebert/ponytail), installed 4.9.0 |
| `plugins/context-mode` | [mksglu/context-mode](https://github.com/mksglu/context-mode), installed Claude 1.0.107 |
| `runtime/context-mode` | Same upstream, separate Codex MCP-only runtime 1.0.169 |
| `plugins/superpowers` | Installed official-marketplace Superpowers 6.3.0, e7a2d16476bf042e9add4699c9d018a90f86e4a6 |
| `plugins/skill-creator`, `plugins/frontend-design` | [anthropics/claude-plugins-official](https://github.com/anthropics/claude-plugins-official), installed revision 85cce0381e7860082641b59d961a2b8c368b8b79 |
| `optional/blender_mcp.py` | Installed Blender MCP 1.9.1 add-on with the existing reference_mcp namespace, loopback/socket and telemetry-off adaptations |

Packaging excludes Git repositories, dependency installations, bytecode and logs.
Upstream licenses included in the installed sources are retained. This is a
private backup, not a public relicensing of third-party skills/plugins.

Intentional packaging changes:

- Undo the workstation's absolute Windows paths in Claude Context Mode manifests.
- Generate an npm lockfile for Claude Context Mode from its installed dependency
  lock and package declaration. Native SQLite is rebuilt on each destination.
- Give the two versionless official Claude plugins the explicit private package
  version `0.0.0-snapshot.85cce0381e78`.
- Pin ECC's optional Chrome DevTools MCP package to 1.9.0 instead of `latest`.
- Preserve packaged bytes through Git using a final `-text -eol` attribute override;
  normalize shell/polyglot line endings and executable permissions when installing.
- Extend the custom status line with GSD's temporary context-metrics bridge.
- Provide native macOS/Windows notification dispatch; mark pywin32 Windows-only
  in the optional Blender dependency lock.

The 54 Codex plugin mirrors are copied from the existing installed mirrors. They
are not claimed to regenerate automatically from installing the six plugins in
this kit. Some describe additional integrations that remain optional; their
presence is not evidence that those integrations are connected.
