# CLAUDE.md — Agent Skills Repository Guide

## Project Overview

This is Anthropic's **Agent Skills** repository — a collection of skills that teach Claude how to complete specialized tasks. Skills are self-contained units packaged with a `SKILL.md` file (YAML frontmatter + markdown instructions) and optional supporting resources (scripts, references, assets, examples).

This repo serves as:
- The official reference implementation of the [Agent Skills standard](https://agentskills.io)
- A **Claude Code Plugin marketplace** with three plugin bundles
- Both open-source example skills (Apache 2.0) and proprietary document skills (source-available)

---

## Repository Structure

```
skills/
├── .claude-plugin/
│   └── marketplace.json         # Defines plugin bundles
├── template/
│   └── SKILL.md                 # Minimal skill starter template
├── spec/
│   └── agent-skills-spec.md     # Points to https://agentskills.io/specification
├── skills/
│   ├── docx/                    # Word document creation/editing (proprietary)
│   ├── pdf/                     # PDF processing: read, merge, forms, OCR (proprietary)
│   ├── pptx/                    # PowerPoint creation/editing (proprietary)
│   ├── xlsx/                    # Excel spreadsheet creation/editing (proprietary)
│   ├── mcp-builder/             # Guide for building MCP servers
│   ├── skill-creator/           # Meta-skill: create, test, and optimize skills
│   ├── web-artifacts-builder/   # React + TypeScript + Tailwind artifact bundler
│   ├── webapp-testing/          # Playwright-based web testing toolkit
│   ├── claude-api/              # Claude API and Anthropic SDK documentation
│   ├── algorithmic-art/         # p5.js generative art with seeded randomness
│   ├── canvas-design/           # Visual design via PDF/PNG creation
│   ├── theme-factory/           # UI theme creation and styling
│   ├── slack-gif-creator/       # Animated GIF creation for Slack
│   ├── internal-comms/          # Internal communications templates
│   ├── brand-guidelines/        # Brand standards and guidelines
│   ├── doc-coauthoring/         # Collaborative document editing
│   └── frontend-design/         # Frontend UI/UX design guidance
├── README.md
├── THIRD_PARTY_NOTICES.md
└── CLAUDE.md                    # This file
```

---

## Skill Structure

### Minimal Skill
```
skill-name/
└── SKILL.md
```

### Full Skill with Resources
```
skill-name/
├── SKILL.md                 # Required: metadata (YAML) + instructions (markdown)
├── scripts/                 # Executable code (Python, shell, JS) — loaded on-demand
├── references/              # Large documentation files — loaded on-demand
├── assets/                  # Static files (templates, fonts, icons)
├── examples/                # Usage examples
├── agents/                  # Subagent instruction files
└── requirements.txt         # Python dependencies (if applicable)
```

### SKILL.md Format

```yaml
---
name: skill-name              # Lowercase, hyphens
description: >
  Concise description of what the skill does and when Claude should use it.
  Be "pushy" about triggering. Include specific contexts. ~100 words max.
license: ...                  # Optional — full license terms in LICENSE.txt
compatibility: ...            # Optional — required dependencies
---

# Markdown Instructions Here
```

**Progressive Disclosure Model:**
1. **Metadata** (`name` + `description`) — Always loaded, ~100 words
2. **SKILL.md body** — Loaded when skill triggers, keep under ~500 lines
3. **Bundled resources** — Loaded on-demand (scripts, references, assets)

---

## Plugin Marketplace

`.claude-plugin/marketplace.json` defines three bundles:

| Bundle | License | Skills |
|--------|---------|--------|
| `document-skills` | Proprietary | xlsx, docx, pptx, pdf |
| `example-skills` | Apache 2.0 | All 12 example/creative/dev skills |
| `claude-api` | — | Claude API documentation skill |

---

## Key Skills Reference

### skill-creator (Meta-skill)
The most complex skill — used for authoring, testing, and optimizing other skills.

**Scripts:**
- `scripts/run_loop.py` — Optimize skill description for triggering
- `scripts/run_eval.py` — Run individual evaluations against a skill
- `scripts/aggregate_benchmark.py` — Aggregate results across runs
- `scripts/package_skill.py` — Package a skill as a `.skill` file
- `scripts/improve_description.py` — Description optimization helper
- `eval-viewer/generate_review.py` — Interactive HTML results viewer

**Agents:**
- `agents/grader.md` — How to grade eval assertions
- `agents/comparator.md` — Blind A/B comparison
- `agents/analyzer.md` — Benchmark analysis

**References:**
- `references/schemas.md` — JSON schema for evals, grading, results

### mcp-builder
Four-phase guide for building Model Context Protocol servers:
1. Research and planning
2. Implementation (tool registration, error handling)
3. Testing (syntax check, MCP Inspector)
4. Evaluations (10 test questions in XML format)

**References:**
- `reference/mcp_best_practices.md` — Universal MCP guidelines
- `reference/node_mcp_server.md` — TypeScript/Node patterns
- `reference/python_mcp_server.md` — Python/FastMCP patterns
- `reference/evaluation.md` — Creating MCP evaluations

### web-artifacts-builder
Bundles React apps into single self-contained HTML files.
- Stack: React 18 + TypeScript + Vite + Parcel + Tailwind CSS + shadcn/ui
- `scripts/init-artifact.sh` — Scaffolds new project
- `scripts/bundle-artifact.sh` — Bundles to single HTML

### webapp-testing
Playwright-based Python toolkit for browser automation.
- `scripts/with_server.py` — Manages server lifecycle (single or multi-server)
- Uses reconnaisance pattern: screenshot → inspect → identify selectors → act

### algorithmic-art
Generative art using p5.js in single HTML artifacts.
- `templates/viewer.html` — **Required starting point** (fixed structure, Anthropic branding)
- Uses seeded randomness (Art Blocks pattern) for reproducibility
- Sidebar controls: seed navigation, parameters, optional color pickers

### slack-gif-creator
Python PIL-based animated GIF toolkit.
- `core/gif_builder.py` — Main GIF assembly
- `core/frame_composer.py` — Frame composition utilities
- `core/easing.py` — Animation easing functions
- `core/validators.py` — Constraint validation
- Constraints: 128×128 (emoji) or 480×480 (message), 10–30 FPS, 48–128 colors

---

## Development Workflows

### Creating a New Skill

1. Copy `template/SKILL.md` to `skills/<skill-name>/SKILL.md`
2. Write YAML frontmatter: `name`, `description` (and optionally `license`)
3. Write markdown instructions in the body
4. Add supporting resources in subdirectories as needed
5. Register in `.claude-plugin/marketplace.json` if part of a bundle
6. Test using the `skill-creator` evaluation workflow

### Modifying an Existing Skill

1. Edit `SKILL.md` for instruction/guideline changes
2. Add/update scripts in `scripts/` for executable code changes
3. Update `references/` for large documentation changes
4. Add usage examples to `examples/`

### Testing and Evaluating Skills

1. Create `evals.json` using the schema in `skill-creator/references/schemas.md`
2. Run `skill-creator/scripts/run_eval.py` for individual evals
3. Run benchmarks with and without the skill to compare
4. Use `skill-creator/eval-viewer/generate_review.py` for a visual results review
5. Grade using `skill-creator/agents/grader.md` schema

### Optimizing Skill Descriptions

1. Create trigger eval queries (mix of should-trigger and should-not-trigger)
2. Run `skill-creator/scripts/run_loop.py` to iteratively optimize
3. Verify on both Claude Code and Claude.ai

### Packaging a Skill

```bash
python skills/skill-creator/scripts/package_skill.py skills/<skill-name>
```

---

## Code Conventions

### Python
- Shebang: `#!/usr/bin/env python3`
- All scripts in `scripts/` must be executable (`chmod +x`)
- Use type hints and docstrings
- Core modules live in `core/` subdirectories with `__init__.py`
- Dependencies in `requirements.txt`

### JavaScript / TypeScript
- Used in `web-artifacts-builder` and artifact scripts
- Prefer CDN-sourced libraries (p5.js, React) in single-file HTML artifacts
- No root-level `package.json` — individual skills manage their own dependencies

### Markdown / SKILL.md
- YAML frontmatter: use `>` (folded scalar) for multi-line descriptions
- Keep `description` under ~100 words
- Use headers (`#`, `##`, `###`) to organize sections
- Inline code examples preferred over separate files when brief

---

## Design Principles

1. **Progressive Disclosure** — Metadata always loads; body loads on trigger; resources load on-demand. Never put everything in SKILL.md if it belongs in a resource file.

2. **Descriptions Drive Triggering** — The `description` field is the primary mechanism for skill activation. Make it "pushy": include specific contexts, use-cases, and explicit activation language.

3. **Theory of Mind** — Explain *why* instructions exist, not just what to do. Claude follows instructions better when it understands the reasoning.

4. **Craftsmanship Over Rote** — Creative skills (art, design) should emphasize quality, expertise, and aesthetic intent — not just mechanical execution.

5. **Lean Instructions** — Remove anything that doesn't pull its weight. Avoid redundancy. Generalize rather than overfit to specific test cases.

6. **Principle of Least Surprise** — Skills must not contain malware, exploits, or unauthorized access code. Users should never be surprised by hidden intent.

7. **Generalization** — Write instructions that work across many similar tasks, not just the specific examples used during development.

---

## Git Workflow

- **Branch naming:** `claude/<description>-<session-id>`
- **Push:** Always use `git push -u origin <branch-name>`
- **Never push to `master` directly** without explicit permission
- Retry push on network failure with exponential backoff: 2s → 4s → 8s → 16s

```bash
git checkout -b claude/<feature>-<id>
# make changes
git add <specific files>
git commit -m "descriptive message"
git push -u origin claude/<feature>-<id>
```

---

## Important Files

| File | Purpose |
|------|---------|
| `template/SKILL.md` | Minimal skill template — start here |
| `skills/skill-creator/SKILL.md` | Comprehensive skill authoring guide |
| `skills/skill-creator/references/schemas.md` | Eval/grading JSON schemas |
| `skills/mcp-builder/reference/mcp_best_practices.md` | MCP development guidelines |
| `skills/algorithmic-art/templates/viewer.html` | Required p5.js art template |
| `.claude-plugin/marketplace.json` | Plugin bundle registry |
| `README.md` | Project overview and getting started |

---

## Quick Reference: Skill Description Best Practices

```yaml
description: >
  # Good: specific, pushy, includes contexts
  TRIGGER this skill whenever the user asks to create, analyze, or modify
  an Excel spreadsheet or .xlsx file. Handles formulas, charts, pivot tables,
  and data formatting. Use even for simple spreadsheet tasks.

  # Bad: vague, passive
  A skill for working with spreadsheets.
```

Key rules:
- State **when to trigger** (contexts, user phrases, file types)
- Use active, directive language ("TRIGGER", "Use when", "Make sure to use")
- Include key capabilities so Claude knows what the skill can do
- Keep under ~100 words (always-loaded budget)
