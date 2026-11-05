# Participant guide

You'll work **in pairs**. One of you drives Claude Code; the other reads, questions and keeps
notes. Swap halfway.

## Before the workshop

You need:

- **A GitHub account** with access to this repository.
- **Claude Code**, signed in with a **Claude Pro** (or higher) subscription. At least one person
  per pair needs this.

Then choose one way to work.

**Option A — in the browser (nothing to install).** On this repository's GitHub page: green
*Code* button → *Codespaces* → *Create codespace on main*. In its terminal:

```bash
npm install -g @anthropic-ai/claude-code
claude          # sign in with your Claude account when prompted
```

**Option B — on your own laptop.** You need git, Python 3.11+ and Claude Code installed.

```bash
git clone https://github.com/UBC-MDS/ai-assisted-workflows.git
cd ai-assisted-workflows
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
claude          # sign in with your Claude account when prompted
```

**Check it works:** ask Claude *"What is this repository?"* If it answers, you're ready.

**Your API key (for testing in session 1).** You'll be given an Anthropic API key. Put it in a
file called `.env` in the repo root:

```bash
echo "ANTHROPIC_API_KEY=sk-ant-..." > .env
echo "ASKDB_MODEL=claude-haiku-5-5" >> .env
```

askdb reads both from there: your key, and the model it uses in the workshop. **Don't `export` it in your shell**: Claude Code would then bill that
key instead of your Claude subscription. If you already exported it, run
`unset ANTHROPIC_API_KEY` before starting `claude`.

## The day

1. **The package.** You'll get to know askdb, a small service that answers business questions by
   writing SQL. You'll explore it with Claude, then answer questions about it without Claude.
2. **Session 1.** Instructions are in `workshop/session1/README.md`. Don't read ahead; we'll open
   it together.
3. **A live walkthrough** of how a change moves from a ticket to production.
4. **Discussion:** what this means for how and what we teach.

## Ground rules

- Use Claude however you like, unless an exercise says not to.
- Make Claude show its work: the SQL and the numbers, not just its conclusion.
- Disagree with your partner out loud. The arguments are the useful part.
