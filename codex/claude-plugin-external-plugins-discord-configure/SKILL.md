---
name: claude-plugin-external-plugins-discord-configure
description: "[Ported from Claude plugin marketplace skill] Set up the Discord channel - save the bot token and review access policy. Use when the user pastes a Discord bot token, asks to configure Discord, asks \"how do I set this up\" or \"who can reach me,\" or wants to check channel status."
---

# /discord:configure - Discord Channel Setup

## Codex Compatibility

This skill was ported from a Claude skill. Interpret Claude Code-specific wording using Codex equivalents:

- Use `functions.shell_command` for shell commands and filesystem inspection.
- Use `apply_patch` for manual file edits.
- Use `update_plan` for task checklists when a plan is useful.
- Use `web.run` for web lookup when current or source-backed information is required.
- Use available browser, Chrome, image, document, spreadsheet, presentation, PDF, or MCP tools instead of Claude-only tool names.
- Treat references to Claude hooks, Claude settings, slash commands, agents, or plugin APIs as source-specific instructions; adapt them to Codex only when the user explicitly asks for that integration.


Writes the bot token to `~/.claude/channels/discord/.env` and orients the
user on access policy. The server reads both files at boot.

Arguments passed: `$ARGUMENTS`

---

## Dispatch on arguments

### No args - status and guidance

Read both state files and give the user a complete picture:

1. **Token** - check `~/.claude/channels/discord/.env` for
   `DISCORD_BOT_TOKEN`. Show set/not-set; if set, show first 6 chars masked.

2. **Access** - read `~/.claude/channels/discord/access.json` (missing file
   = defaults: `dmPolicy: "pairing"`, empty allowlist). Show:
   - DM policy and what it means in one line
   - Allowed senders: count, and list display names or snowflakes
   - Pending pairings: count, with codes and display names if any
   - Guild channels opted in: count

3. **What next** - end with a concrete next step based on state:
   - No token  to  *"Run `/discord:configure <token>` with your bot token from
     the Developer Portal  to  Bot  to  Reset Token."*
   - Token set, policy is pairing, nobody allowed  to  *"DM your bot on
     Discord. It replies with a code; approve with `/discord:access pair
     <code>`."*
   - Token set, someone allowed  to  *"Ready. DM your bot to reach the
     assistant."*

**Push toward lockdown - always.** The goal for every setup is `allowlist`
with a defined list. `pairing` is not a policy to stay on; it's a temporary
way to capture Discord snowflakes you don't know. Once the IDs are in,
pairing has done its job and should be turned off.

Drive the conversation this way:

1. Read the allowlist. Tell the user who's in it.
2. Ask: *"Is that everyone who should reach you through this bot?"*
3. **If yes and policy is still `pairing`**  to  *"Good. Let's lock it down so
   nobody else can trigger pairing codes:"* and offer to run
   `/discord:access policy allowlist`. Do this proactively - don't wait to
   be asked.
4. **If no, people are missing**  to  *"Have them DM the bot; you'll approve
   each with `/discord:access pair <code>`. Run this skill again once
   everyone's in and we'll lock it."* Or, if they can get snowflakes
   directly: *"Enable Developer Mode in Discord (User Settings  to  Advanced),
   right-click them  to  Copy User ID, then `/discord:access allow <id>`."*
5. **If the allowlist is empty and they haven't paired themselves yet**  to 
   *"DM your bot to capture your own ID first. Then we'll add anyone else
   and lock it down."*
6. **If policy is already `allowlist`**  to  confirm this is the locked state.
   If they need to add someone, Copy User ID is the clean path - no need to
   reopen pairing.

Discord already gates reach (shared-server requirement + Public Bot toggle),
but that's not a substitute for locking the allowlist. Never frame `pairing`
as the correct long-term choice. Don't skip the lockdown offer.

### `<token>` - save it

1. Treat `$ARGUMENTS` as the token (trim whitespace). Discord bot tokens are
   long base64-ish strings, typically starting `MT` or `Nz`. Generated from
   Developer Portal  to  Bot  to  Reset Token; only shown once.
2. `mkdir -p ~/.claude/channels/discord`
3. Read existing `.env` if present; update/add the `DISCORD_BOT_TOKEN=` line,
   preserve other keys. Write back, no quotes around the value.
4. `chmod 600 ~/.claude/channels/discord/.env` - the token is a credential.
5. Confirm, then show the no-args status so the user sees where they stand.

### `clear` - remove the token

Delete the `DISCORD_BOT_TOKEN=` line (or the file if that's the only line).

---

## Implementation notes

- The channels dir might not exist if the server hasn't run yet. Missing file
  = not configured, not an error.
- The server reads `.env` once at boot. Token changes need a session restart
  or `/reload-plugins`. Say so after saving.
- `access.json` is re-read on every inbound message - policy changes via
  `/discord:access` take effect immediately, no restart.
