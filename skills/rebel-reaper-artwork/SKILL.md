---
name: rebel-reaper-artwork
description: Generate original REBEL REAPER artwork from user-uploaded reference images and instructions, preserving broad stylistic direction while avoiding copying, using persistent style memory when available, and defaulting to REBEL REAPER text unless instructed otherwise.
---

# REBEL REAPER Artwork

## Trigger / Inputs
Use this skill when the user uploads artwork references and asks for new artwork, brand art, poster art, apparel graphics, tattoo-flash-style art, logo-adjacent art, or “make something in this style.”

Accept optional user instructions for subject, mood, palette, composition, typography, print format, and exclusions.

## Core Rule
Never copy, trace, duplicate, or closely recreate uploaded artwork. Use references only to infer high-level attributes: mood, palette family, texture language, broad genre, line weight, typography category, and composition energy.

Require a substantial transformation target: new subject structure, new layout, new symbols, new focal elements, new ornamentation, and changed composition. Exact mathematical “80% different” cannot be guaranteed by an image model, so enforce the originality checklist below instead.

## Mandatory Text Rule
Include `REBEL REAPER` inside the generated image unless the user explicitly says not to.

Prefer font direction based on the reference when appropriate. Otherwise choose from gothic, traditional tattoo, pueblo, hardcore, bold, Y2K, flames, or 3D lettering based on the artwork style.

## Reference Analysis
Analyze uploaded artwork into:
- palette
- motifs
- line quality
- rendering style
- era / subculture cues
- typography cues
- composition type
- print/use-case assumptions

Explicitly separate:
- **Allowed inspiration:** broad style signals such as mood, palette family, texture language, genre, line weight, typography category, and composition energy.
- **Protected/non-copy elements:** exact layouts, exact symbols, exact characters, distinctive lettering, logos, marks, watermarks, proprietary mascots, and any uniquely identifying arrangement.

## Generation Prompt Construction
Build prompts that include:
- original subject concept
- `REBEL REAPER` text placement
- selected lettering style
- style-memory traits if available
- originality constraints requiring new subject structure, layout, symbols, focal elements, ornamentation, and composition
- negative prompt against copying, tracing, exact layouts, exact symbols, exact characters, exact lettering, watermarks, or existing logos

## Originality Gate
Before finalizing, check that the proposed artwork changes:
- main subject
- composition
- symbol set
- lettering treatment
- layout
- decorative details
- color arrangement

If too close to the reference, regenerate or revise the prompt toward a more distinct concept.

## Output Behavior
Return the final prompt or generated artwork instructions depending on available tools.

If image-generation tools are available, use the appropriate image generation skill/tool. If no image tool is available, provide a ready-to-use image prompt.
