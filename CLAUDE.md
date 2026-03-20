# CLAUDE.md — Anthropic Agent Skills Repository

## Repository Overview

This repository is Anthropic's official collection of **Agent Skills** for Claude — self-contained folders of instructions, scripts, and resources that Claude loads dynamically to improve performance on specialized tasks. Skills are used in Claude Code, Claude.ai, and the Claude API.

The formal specification lives at [agentskills.io/specification](https://agentskills.io/specification).

---

## Repository Structure

```
skills/                          # Root
├── CLAUDE.md                    # This file
├── README.md                    # Public-facing overview
├── THIRD_PARTY_NOTICES.md       # Open source license notices
├── .gitignore                   # Ignores .DS_Store, __pycache__, .idea, .vscode
├── .claude-plugin/
│   └── marketplace.json         # Plugin marketplace configuration
├── spec/
│   └── agent-skills-spec.md     # Points to agentskills.io/specification
├── template/
│   └── SKILL.md                 # Minimal skill template (starting point)
└── skills/                      # All skill implementations
    ├── algorithmic-art/
    ├── brand-guidelines/
    ├── canvas-design/           # Includes bundled TTF fonts in canvas-fonts/
    ├── claude-api/              # Multi-language API/SDK reference docs
    ├── doc-coauthoring/
    ├── docx/                    # Word document skill (proprietary)
    ├── frontend-design/
    ├── internal-comms/
    ├── mcp-builder/
    ├── pdf/                     # PDF processing skill (proprietary)
    ├── pptx/                    # PowerPoint skill (proprietary)
    ├── skill-creator/           # Meta-skill: create and evaluate other skills
    ├── slack-gif-creator/
    ├── theme-factory/
    ├── web-artifacts-builder/
    ├── webapp-testing/
    └── xlsx/                    # Excel skill (proprietary)
```

---

## Skill Anatomy

Every skill is a directory with a required `SKILL.md` and optional supporting files:

```
my-skill/
├── SKILL.md          (required) — YAML frontmatter + markdown instructions
├── scripts/          (optional) — Executable code for deterministic/repetitive tasks
├── references/       (optional) — Docs loaded into context as needed
└── assets/           (optional) — Files used in output (templates, icons, fonts)
```

### SKILL.md Frontmatter

```yaml
---
name: my-skill-name          # Unique identifier: lowercase, hyphens for spaces
description: "..."           # Primary triggering mechanism — must explain WHAT and WHEN
license: Apache-2.0          # or "Proprietary. LICENSE.txt has complete terms"
---
```

Only `name` and `description` are required. The `description` is critical: Claude uses it to decide whether to invoke the skill. Write it to be "slightly pushy" — name specific contexts and user phrases, not just what the skill does.

---

## Progressive Disclosure (Loading Model)

Skills load in three levels:

| Level | Content | Always loaded? | Size guidance |
|-------|---------|---------------|---------------|
| 1 | `name` + `description` from frontmatter | Yes (~100 words) | Keep concise |
| 2 | Full `SKILL.md` body | When skill triggers | < 500 lines ideal |
| 3 | Bundled resources (scripts, references, assets) | On demand | Unlimited |

- Keep `SKILL.md` under 500 lines. If approaching this limit, add hierarchy and pointers to resource files.
- Scripts can be executed without loading their source into context.
- For large reference files (>300 lines), include a table of contents.

---

## Plugin Marketplace Configuration

`.claude-plugin/marketplace.json` defines the `anthropic-agent-skills` marketplace with three installable plugin bundles:

| Plugin name | Skills included |
|-------------|----------------|
| `document-skills` | `xlsx`, `docx`, `pptx`, `pdf` |
| `example-skills` | `algorithmic-art`, `brand-guidelines`, `canvas-design`, `doc-coauthoring`, `frontend-design`, `internal-comms`, `mcp-builder`, `skill-creator`, `slack-gif-creator`, `theme-factory`, `web-artifacts-builder`, `webapp-testing` |
| `claude-api` | `claude-api` |

---

## Licensing

Skills fall into two categories:

- **Apache 2.0 (open source)**: All example skills in the `example-skills` plugin. These have a `LICENSE.txt` with Apache 2.0 terms.
- **Proprietary (source-available)**: Document skills (`docx`, `pdf`, `pptx`, `xlsx`). These power Claude's production document capabilities. Full terms in each skill's `LICENSE.txt`.

---

## Key Skills Reference

### Document Skills (proprietary)
- **`pdf`** — PDF read/write/merge/split/OCR/forms. Uses `pypdf`, `pdfplumber`, `reportlab`, `qpdf`. Additional docs in `reference.md` and `forms.md`.
- **`docx`** — Word document creation and editing. Approach: create with `docx-js`; edit existing by unpack→XML edit→repack using `scripts/office/`. Uses `pandoc` for reading.
- **`pptx`** — PowerPoint creation and editing. Scripts in `scripts/`. Editing reference in `editing.md`.
- **`xlsx`** — Excel spreadsheet creation and editing. Scripts in `scripts/`. Includes `recalc.py`.

The `docx`, `pptx`, and `xlsx` skills share a common `scripts/office/` module with `pack.py`, `unpack.py`, `validate.py`, `soffice.py`, and XML schema files (ISO/ECMA standards).

### Creative & Design Skills
- **`canvas-design`** — Visual art/posters/designs as `.png`/`.pdf`. Bundled TTF fonts in `canvas-fonts/`. Two-step process: design philosophy → visual expression.
- **`algorithmic-art`** — Generative art via JavaScript. Templates: `generator_template.js` + `viewer.html`.
- **`theme-factory`** — Visual theme creation. Predefined theme examples in `themes/`.
- **`frontend-design`** — Frontend UI/UX design.
- **`brand-guidelines`** — Brand identity and guidelines.

### Development & Technical Skills
- **`claude-api`** — Claude API and SDK documentation. Organized by language (`python/`, `typescript/`, `go/`, `java/`, `ruby/`, `csharp/`, `php/`, `curl/`) and topic (`claude-api/` vs `agent-sdk/`). Shared reference files in `shared/`.
- **`mcp-builder`** — Build MCP (Model Context Protocol) servers. References for Node and Python. Evaluation scripts in `scripts/`.
- **`web-artifacts-builder`** — Build web artifacts. Scripts: `init-artifact.sh`, `bundle-artifact.sh`. Includes `shadcn-components.tar.gz`.
- **`webapp-testing`** — Automated web app testing with browser automation. Examples for console logging, element discovery, static HTML. `scripts/with_server.py` for local server testing.
- **`skill-creator`** — Meta-skill for creating, testing, and optimizing other skills. Full eval loop with subagent support. See below.

### Enterprise & Communication Skills
- **`internal-comms`** — Internal company communications. Examples in `examples/` for newsletters, FAQs, 3P updates, general comms.
- **`doc-coauthoring`** — Collaborative document writing.
- **`slack-gif-creator`** — Animated GIFs for Slack. Core modules: `easing.py`, `frame_composer.py`, `gif_builder.py`, `validators.py`.

---

## The `skill-creator` Skill (Meta-Skill)

This is the most complex skill in the repo. Use it when creating or improving any skill. Its workflow:

1. **Capture intent** — understand what the skill should do and when it should trigger
2. **Write `SKILL.md`** — draft instructions following skill writing patterns
3. **Create test cases** — save to `evals/evals.json` (2–3 realistic prompts)
4. **Run evals** — spawn parallel subagents (with-skill + baseline), save to `<skill>-workspace/iteration-N/`
5. **Grade & benchmark** — use `scripts/aggregate_benchmark.py`, view with `eval-viewer/generate_review.py`
6. **Iterate** — improve skill based on feedback; repeat until satisfied
7. **Optimize description** — run `scripts/run_loop.py` for triggering accuracy
8. **Package** — `scripts/package_skill.py` produces a `.skill` file

Key scripts:
- `scripts/run_eval.py` — run a single eval
- `scripts/run_loop.py` — description optimization loop
- `scripts/aggregate_benchmark.py` — aggregate eval results into `benchmark.json`
- `eval-viewer/generate_review.py` — launch HTML review viewer
- `scripts/improve_description.py` — improve skill description
- `scripts/package_skill.py` — package skill into `.skill` file

Subagent instructions in `agents/`: `grader.md`, `comparator.md`, `analyzer.md`.
JSON schemas in `references/schemas.md`.

**Environment notes:**
- **Claude Code**: Full workflow with subagents. Use `--static` flag for headless environments.
- **Claude.ai**: No subagents — run test cases sequentially inline; skip benchmarking; skip description optimization (requires `claude -p`).
- **Cowork**: Has subagents but no display — always use `--static` for the eval viewer.

---

## Writing a New Skill

1. Copy `template/SKILL.md` to `skills/<my-skill-name>/SKILL.md`
2. Fill in `name` and `description` in frontmatter
3. Write instructions in the body using imperative form
4. Add `scripts/`, `references/`, or `assets/` subdirectories only if needed
5. Keep `SKILL.md` under 500 lines; reference external files with clear pointers
6. Explain *why* instructions matter rather than using heavy-handed `MUST`/`ALWAYS`
7. Add to `.claude-plugin/marketplace.json` if it should be installable

**Skill description best practices:**
- Include both what the skill does AND when to use it
- Name specific trigger phrases/contexts
- Be slightly assertive to avoid undertriggering
- All "when to use" info goes in `description`, not the body

**Do not include** in skills: malware, exploit code, misleading instructions, or anything that would surprise a user given the skill's stated purpose.

---

## Installing Skills (for users)

**Claude Code (plugin marketplace):**
```bash
/plugin marketplace add anthropics/skills
/plugin install document-skills@anthropic-agent-skills
/plugin install example-skills@anthropic-agent-skills
/plugin install claude-api@anthropic-agent-skills
```

**Claude.ai:** Skills from this repo are pre-installed for paid plans. Custom skills can be uploaded via settings.

**Claude API:** See [Skills API Quickstart](https://docs.claude.com/en/api/skills-guide#creating-a-skill).

---

## Development Conventions

- **Branch naming**: Feature branches use `claude/<description>-<id>` format
- **No build system**: No `package.json`, `Makefile`, or test runner at the root level — each skill is self-contained
- **Python scripts**: Use standard library + common packages (`pypdf`, `pdfplumber`, `reportlab`, etc.); no shared virtualenv
- **Git ignore**: `.DS_Store`, `__pycache__/`, `.idea/`, `.vscode/`
- **Commit style**: Conventional-ish, descriptive subject lines (see `git log`)
- **No CLAUDE.md per skill**: Skills self-document via `SKILL.md`; only root-level `CLAUDE.md` exists
