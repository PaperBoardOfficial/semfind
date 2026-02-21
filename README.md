# semfind

Semantic grep for the terminal. Search files by meaning, not pattern.

`grep` finds exact text matches. `semfind` finds lines that mean the same thing. Search your logs, notes, docs, or any text file using natural language — no regex needed.

## Why semfind?

Traditional grep fails when you don't know the exact wording. If your log says "container build failed due to missing environment variables" but you search for "deployment issue", grep finds nothing. semfind finds it instantly because it understands meaning.

**Built for AI agents.** Tools like [OpenClaw](https://github.com/PaperBoardOfficial/openclaw) and other AI agents need lightweight semantic search over local files — searching memory, history, and context without spinning up a full vector database. semfind is a single CLI command with auto-caching that agents can call directly from the shell.

**Also great for humans.** Search your markdown notes, project logs, documentation, or any text files by what you mean, not what you remember typing.

### Key features

- **No API keys** — runs 100% locally using [fastembed](https://github.com/qdrant/fastembed) (BAAI/bge-small-en-v1.5) + FAISS
- **Auto-caching** — indexes files on first search, caches embeddings, auto-invalidates when files change
- **Fast** — ~2s cold start, 14ms cached queries, 252MB RAM
- **Grep-like output** — colored results with file, line number, and similarity score
- **Zero config** — just `pip install semfind` and go

## Install

```bash
pip install semfind
```

## Usage

```bash
# Search a file
semfind "deployment issue" logs.md

# Search multiple files, top 3 results
semfind "permission error" memory/*.md -k 3

# Show 2 lines of context around each match
semfind "database migration" notes.md -n 2

# Force re-index (ignore cache)
semfind "query" file.md --reindex

# Set minimum similarity threshold
semfind "auth bug" *.md -m 0.5
```

### Output

```
memory/HISTORY.md:9: [2026-01-15 10:30] DEPLOYMENT: Fixed docker build...  (0.796)
memory/HISTORY.md:3: [2026-01-17 09:15] FILE_PERMS: Agent couldn't...     (0.689)
```

## How it works

1. On first search, each file's non-empty lines are embedded and cached in `~/.cache/semfind/`
2. Cache is keyed by file content hash — changes auto-invalidate
3. Your query is embedded and compared via FAISS inner-product search
4. Results are printed grep-style with similarity scores

## Options

| Flag | Description | Default |
|------|-------------|---------|
| `-k, --top-k` | Number of results | 5 |
| `-n, --context` | Context lines before/after | 0 |
| `-m, --max-distance` | Minimum similarity score | none |
| `--reindex` | Force re-embed | false |
| `--model` | Embedding model | BAAI/bge-small-en-v1.5 |
| `--no-cache` | Skip cache | false |
| `--version` | Print version | |

## Use with AI agents

semfind is designed to be called from AI agent tool loops. Example use cases:

- **Memory search** — agents searching their own history/memory files for relevant past context
- **Document retrieval** — finding relevant docs before answering user questions
- **Log analysis** — searching logs by describing the problem rather than knowing exact error strings

```bash
# An agent searching its memory
semfind "user asked about authentication" memory/*.md -k 3

# Searching project docs for context
semfind "how to configure database" docs/*.md -k 5
```

## License

MIT
