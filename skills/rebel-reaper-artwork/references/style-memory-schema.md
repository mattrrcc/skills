# REBEL REAPER Style Memory Schema

Store the REBEL REAPER style memory outside generated artwork outputs, normally at:

```text
.agents/memory/rebel-reaper-style.json
```

The memory file is a compact, persistent profile of recurring abstract style preferences. It must not contain copied source artwork, copyrighted image content, embedded image data, prompts that reproduce a protected work, or traced composition details. Store only reusable descriptors such as palette tendencies, linework qualities, motifs, lettering preferences, composition patterns, texture treatments, and rejected/avoid items.

## Baseline shape

```json
{
  "brand_name": "REBEL REAPER",
  "default_text": "REBEL REAPER",
  "style_traits": {
    "palette_preferences": [],
    "linework": [],
    "motifs": [],
    "lettering_preferences": [],
    "composition_preferences": [],
    "texture_preferences": [],
    "avoid": []
  },
  "observations": [],
  "last_updated": ""
}
```

## Trait entries

Each `style_traits` array should contain normalized trait objects rather than raw image notes:

```json
{
  "value": "limited black, bone, and muted crimson palette",
  "count": 3,
  "source": "inferred",
  "user_declared": false,
  "status": "active",
  "first_seen": "2026-05-14T00:00:00Z",
  "last_seen": "2026-05-14T00:00:00Z"
}
```

Fields:

- `value`: Short abstract descriptor. Keep it general enough to guide new original work without copying a reference.
- `count`: Number of approved/corrected sessions where this descriptor appeared.
- `source`: `user` for explicit user preferences, otherwise `inferred`.
- `user_declared`: `true` when the user explicitly declared the preference. These traits take priority over inferred traits.
- `status`: `active` for usable defaults, `avoid` for rejected/corrected elements.
- `first_seen` / `last_seen`: ISO-8601 timestamps.

## Observations

Use `observations` as a short audit trail of artwork-analysis sessions. Observation records may include:

```json
{
  "timestamp": "2026-05-14T00:00:00Z",
  "approved": true,
  "summary": "User approved abstract reaper mascot direction with distressed ink texture.",
  "traits_seen": {
    "motifs": ["hooded reaper mascot", "skull emblem"],
    "texture_preferences": ["distressed screen-print grain"]
  },
  "avoid": []
}
```

Keep summaries brief and abstract. Do not include image bytes, file paths to source images, exact copies of source prompts, or detailed instructions that would reconstruct copyrighted artwork.

## Preference rules

1. Create the file with the baseline shape when it does not exist.
2. Promote inferred traits to active defaults only after they recur across sessions, typically `count >= 2`.
3. Add user-declared preferences immediately and never demote or overwrite them with inferred observations.
4. Add rejected or corrected elements to `style_traits.avoid` with `status: "avoid"`.
5. Keep one-off inferred details in `observations` and internal counts until they recur.
6. Normalize traits to concise lowercase descriptors unless capitalization is part of brand text.
7. Remove or reject descriptors that contain URLs, base64/data URIs, long copied passages, or source-artwork-specific content.
