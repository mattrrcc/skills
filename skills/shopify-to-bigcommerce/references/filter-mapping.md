# Liquid Filter to Handlebars Helper Mapping

## Built-in (No Custom Helper Needed)

| Liquid Filter | Handlebars | Notes |
|---------------|------------|-------|
| `money` | `{{money expr}}` | Stencil built-in |
| `img_url: 'size'` | `{{getImage expr "size"}}` | Stencil built-in |
| `t` | `{{lang expr}}` | Stencil built-in |
| `json` | `{{json expr}}` | Stencil built-in |
| `asset_url` | Direct path | Rewritten during migration |

## String Helpers (Custom)

| Liquid | Handlebars | Helper |
|--------|------------|--------|
| `upcase` | `{{toUpperCase expr}}` | toUpperCase |
| `downcase` | `{{toLowerCase expr}}` | toLowerCase |
| `capitalize` | `{{capitalize expr}}` | capitalize |
| `strip` | `{{strip expr}}` | strip |
| `strip_html` | `{{stripHtml expr}}` | stripHtml |
| `truncate: N` | `{{truncate expr N}}` | truncate |
| `truncatewords: N` | `{{truncateWords expr N}}` | truncateWords |
| `replace: a, b` | `{{replace expr a b}}` | replace |
| `remove: str` | `{{replace expr str ''}}` | replace |
| `append: str` | `{{concat expr str}}` | concat |
| `prepend: str` | `{{concat str expr}}` | concat |
| `split: sep` | `{{split expr sep}}` | split |
| `escape` | `{{sanitize expr}}` | sanitize |
| `url_encode` | `{{encodeURI expr}}` | encodeURI |
| `newline_to_br` | `{{nl2br expr}}` | nl2br |
| `pluralize: s, p` | `{{plural expr s p}}` | plural |
| `handleize` | `{{handleize expr}}` | handleize |

## Array Helpers (Custom)

| Liquid | Handlebars | Helper |
|--------|------------|--------|
| `size` | `{{length expr}}` | length |
| `first` | `{{first expr}}` | first |
| `last` | `{{last expr}}` | last |
| `join: sep` | `{{join expr sep}}` | join |
| `sort` | `{{sort expr}}` | sort |
| `map: key` | `{{pluck expr key}}` | pluck |
| `where: k, v` | `{{where expr k v}}` | where |
| `uniq` | `{{unique expr}}` | unique |
| `compact` | `{{compact expr}}` | compact |
| `reverse` | `{{reverse expr}}` | reverse |

## Math Helpers (Custom)

| Liquid | Handlebars | Helper |
|--------|------------|--------|
| `plus: N` | `{{add expr N}}` | add |
| `minus: N` | `{{subtract expr N}}` | subtract |
| `times: N` | `{{multiply expr N}}` | multiply |
| `divided_by: N` | `{{divide expr N}}` | divide |
| `modulo: N` | `{{mod expr N}}` | mod |
| `ceil` | `{{ceil expr}}` | ceil |
| `floor` | `{{floor expr}}` | floor |
| `round` | `{{round expr}}` | round |
| `abs` | `{{abs expr}}` | abs |

## Other Helpers (Custom)

| Liquid | Handlebars | Helper |
|--------|------------|--------|
| `date: format` | `{{moment expr format}}` | moment |
| `default: val` | `{{or expr val}}` | or |
| `highlight: term` | `{{highlight expr term}}` | highlight |

## No Direct Equivalent

These Shopify-specific filters have no BigCommerce equivalent and are flagged for manual review:

- `color_to_rgb`, `color_lighten`, `color_darken` (color manipulation)
- `font_face`, `font_modify`, `font_url` (Shopify font system)
- `stylesheet_tag`, `script_tag`, `preload_tag` (asset loading)
- `payment_type_svg_tag` (payment icons)
- `placeholder_svg_tag` (placeholder images)
- `weight_with_unit` (weight formatting)
