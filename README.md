# ContextFossil 🪨

**Know what your coding agent could see — and whether that context changed.**

AI coding agents increasingly operate inside real workspaces: repository instructions, local configuration, executable tools, environment shape, and Git state all influence a run. The problem is that the *workspace context* is usually implicit and hard to reproduce.

ContextFossil turns that hidden context into a small, deterministic **fossil** you can save, diff, and review before an agent run.

## The idea

```text
workspace → fossil → diff → "what changed around the agent?"
```

It deliberately does **not** capture secret values, prompt transcripts, file contents, or model output.

### What it records

- Git HEAD and dirty/clean state
- known agent instruction/config file metadata (`AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `.cursorrules`, etc.)
- SHA-256 + size of discovered context files (not their contents)
- presence/version of common developer executables
- operating-system and Python runtime identity
- environment-variable **names only**

### What it can answer

- Did the agent's instruction surface change between two runs?
- Did Git move or become dirty?
- Did a tool disappear, appear, or change version?
- Did the environment shape change without exposing values?

## Quick start

```bash
python -m contextfossil snapshot . --output before.json
# ... make changes / switch machines / change agent configuration ...
python -m contextfossil snapshot . --output after.json
python -m contextfossil diff before.json after.json
```

Exit status is `0` when no material drift is found and `1` when drift is detected. Invalid input or usage returns `2`.

## Why this exists

Agent context is becoming a first-class engineering concern. Recent research has found widespread smells in `AGENTS.md` files, including context bloat and conflicting instructions, while other studies show that repository context can change agent behavior and cost. Workspace-level evaluation is also emerging because agents still struggle with large, heterogeneous file dependencies.

Sources: [Configuration Smells in AGENTS.md](https://arxiv.org/abs/2606.15828), [Evaluating AGENTS.md](https://arxiv.org/abs/2602.11988), [Workspace-Bench](https://arxiv.org/abs/2605.03596).

Existing systems focus on generating/syncing agent instruction files, persistent memory, or evaluating agents. ContextFossil takes a different, deliberately small approach: **observe the ambient workspace conditions without storing the sensitive content itself**.

## Security boundary

ContextFossil is designed for untrusted workspaces:

- never records environment-variable values
- never reads instruction-file contents into the snapshot
- never executes repository code
- never follows URLs
- never makes network requests
- only hashes and reports metadata for discovered context files

## Development

```bash
python -m unittest discover -s tests -v
python -m compileall contextfossil
```

Python 3.10+ · dependency-free · MIT
