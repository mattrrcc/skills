---
name: rebel-reaper-artwork
description: Create original REBEL REAPER artwork and brand visuals using persistent abstract style memory. Use when users request REBEL REAPER logos, mascots, merch graphics, tattoo-style art, decals, posters, or revisions based on approved/corrected REBEL REAPER artwork while avoiding copied source artwork.
---

# REBEL REAPER Artwork

Create original REBEL REAPER artwork using the user's current request, any supplied references, and the persistent abstract style memory when available.

## Persistent style memory

- Before generating or revising artwork, check for `.agents/memory/rebel-reaper-style.json` from the repository root.
- If the file exists, load it and use active `style_traits` as defaults when the user gives little or no prompt detail.
- Treat `user_declared: true` traits as stronger than inferred traits.
- Respect `style_traits.avoid` as negative constraints.
- Ask for clarification only when the current request/reference conflicts with the memory or when user-declared preferences conflict with each other.
- Do not mention memory details unless relevant to the user's request or a conflict needs resolution.

See `references/style-memory-schema.md` for the storage format and privacy/copyright constraints.

## Artwork workflow

1. Interpret the current request first: required text, format, placement, medium, dimensions, and any supplied references.
2. Apply memory defaults only where the user did not specify a direction.
3. Create original work. Use references for high-level direction only; do not trace, copy, or recreate copyrighted source artwork.
4. Keep default brand text as `REBEL REAPER` unless the user asks for different text.
5. Avoid storing generated outputs or source images in memory. Memory stores only abstract descriptors.

## Updating memory

After each approved or corrected artwork session, update `.agents/memory/rebel-reaper-style.json` with `scripts/update_style_memory.py`.

- For approved sessions, add abstract observations from the artwork analysis and user feedback.
- For corrected or rejected outputs, record rejected elements in `avoid`.
- Preserve user-declared preferences above inferred observations.
- Track recurring preferences; do not promote one-off inferred details as defaults.
- Do not store copyrighted image content, copied prompts, source files, embedded images, or instructions that reconstruct a protected reference.

Example:

```bash
python skills/rebel-reaper-artwork/scripts/update_style_memory.py \
  --memory .agents/memory/rebel-reaper-style.json \
  session-analysis.json
```
