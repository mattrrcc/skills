#!/usr/bin/env python3
"""Converts Liquid filters to BigCommerce Handlebars helpers."""

from dataclasses import dataclass


@dataclass
class FilterResult:
    expression: str
    custom_helpers_needed: list


class FilterConverter:
    """Convert Liquid filter chains to Handlebars helper expressions.

    Liquid: {{ expr | filter1 | filter2: arg }}
    Handlebars: {{helper2 (helper1 expr) arg}}
    """

    # filter_name -> (pattern, is_custom_helper)
    # {expr} = the input expression, {arg0}, {arg1} = filter arguments
    FILTER_MAP = {
        # Money / Currency
        "money": ("(money {expr})", False),
        "money_with_currency": ("(money {expr})", False),
        "money_without_currency": ("(money {expr})", False),
        "money_without_trailing_zeros": ("(money {expr})", False),

        # Image
        "img_url": ("(getImage {expr} {arg0})", False),
        "image_url": ("(getImage {expr} {arg0})", False),
        "img_tag": ("<img-placeholder>", True),

        # Asset URLs
        "asset_url": ("{expr}", False),
        "asset_img_url": ("(getImage {expr} {arg0})", False),
        "shopify_asset_url": ("{expr}", False),
        "file_url": ("{expr}", False),
        "file_img_url": ("(getImage {expr} {arg0})", False),
        "global_asset_url": ("{expr}", False),

        # String filters
        "upcase": ("(toUpperCase {expr})", True),
        "downcase": ("(toLowerCase {expr})", True),
        "capitalize": ("(capitalize {expr})", True),
        "strip": ("(strip {expr})", True),
        "lstrip": ("(lstrip {expr})", True),
        "rstrip": ("(rstrip {expr})", True),
        "strip_html": ("(stripHtml {expr})", True),
        "strip_newlines": ("(stripNewlines {expr})", True),
        "newline_to_br": ("(nl2br {expr})", True),
        "truncate": ("(truncate {expr} {arg0})", True),
        "truncatewords": ("(truncateWords {expr} {arg0})", True),
        "replace": ("(replace {expr} {arg0} {arg1})", True),
        "replace_first": ("(replaceFirst {expr} {arg0} {arg1})", True),
        "remove": ("(replace {expr} {arg0} '')", True),
        "remove_first": ("(replaceFirst {expr} {arg0} '')", True),
        "append": ("(concat {expr} {arg0})", True),
        "prepend": ("(concat {arg0} {expr})", True),
        "split": ("(split {expr} {arg0})", True),
        "escape": ("(sanitize {expr})", True),
        "escape_once": ("(sanitize {expr})", True),
        "url_encode": ("(encodeURI {expr})", True),
        "url_decode": ("(decodeURI {expr})", True),
        "url_param_escape": ("(encodeURIComponent {expr})", True),
        "base64_encode": ("(base64Encode {expr})", True),
        "base64_decode": ("(base64Decode {expr})", True),
        "md5": ("(md5 {expr})", True),
        "sha1": ("(sha1 {expr})", True),
        "sha256": ("(sha256 {expr})", True),
        "hmac_sha1": ("(hmacSha1 {expr} {arg0})", True),
        "hmac_sha256": ("(hmacSha256 {expr} {arg0})", True),
        "pluralize": ("(plural {expr} {arg0} {arg1})", True),
        "slice": ("(slice {expr} {arg0} {arg1})", True),

        # Array filters
        "size": ("(length {expr})", True),
        "first": ("(first {expr})", True),
        "last": ("(last {expr})", True),
        "join": ("(join {expr} {arg0})", True),
        "sort": ("(sort {expr})", True),
        "sort_natural": ("(sortNatural {expr})", True),
        "map": ("(pluck {expr} {arg0})", True),
        "where": ("(where {expr} {arg0} {arg1})", True),
        "uniq": ("(unique {expr})", True),
        "compact": ("(compact {expr})", True),
        "reverse": ("(reverse {expr})", True),
        "concat": ("(concatArrays {expr} {arg0})", True),
        "flatten": ("(flatten {expr})", True),

        # Math filters
        "plus": ("(add {expr} {arg0})", True),
        "minus": ("(subtract {expr} {arg0})", True),
        "times": ("(multiply {expr} {arg0})", True),
        "divided_by": ("(divide {expr} {arg0})", True),
        "modulo": ("(mod {expr} {arg0})", True),
        "ceil": ("(ceil {expr})", True),
        "floor": ("(floor {expr})", True),
        "round": ("(round {expr})", True),
        "abs": ("(abs {expr})", True),
        "at_least": ("(atLeast {expr} {arg0})", True),
        "at_most": ("(atMost {expr} {arg0})", True),

        # Date
        "date": ("(moment {expr} {arg0})", True),

        # Translation
        "t": ("(lang {expr})", False),

        # JSON
        "json": ("(json {expr})", False),

        # Type / Default
        "default": ("(or {expr} {arg0})", True),
        "type": ("(typeof {expr})", True),

        # URL
        "within": ("{expr}", False),
        "link_to": ("<a-placeholder>", True),
        "link_to_vendor": ("<a-placeholder>", True),
        "link_to_type": ("<a-placeholder>", True),
        "link_to_tag": ("<a-placeholder>", True),
        "link_to_add_tag": ("<a-placeholder>", True),
        "link_to_remove_tag": ("<a-placeholder>", True),
        "sort_by": ("{expr}", True),
        "url_for_type": ("{expr}", True),
        "url_for_vendor": ("{expr}", True),
        "payment_type_img_url": ("{expr}", True),

        # Handle/Slug
        "handle": ("(handleize {expr})", True),
        "handleize": ("(handleize {expr})", True),

        # Color
        "color_to_rgb": ("(colorToRgb {expr})", True),
        "color_to_hsl": ("(colorToHsl {expr})", True),
        "color_to_hex": ("(colorToHex {expr})", True),
        "color_lighten": ("(colorLighten {expr} {arg0})", True),
        "color_darken": ("(colorDarken {expr} {arg0})", True),
        "color_saturate": ("(colorSaturate {expr} {arg0})", True),
        "color_desaturate": ("(colorDesaturate {expr} {arg0})", True),
        "color_modify": ("(colorModify {expr} {arg0} {arg1})", True),
        "color_extract": ("(colorExtract {expr} {arg0})", True),
        "color_brightness": ("(colorBrightness {expr})", True),
        "color_mix": ("(colorMix {expr} {arg0} {arg1})", True),
        "brightness_difference": ("(brightnessDiff {expr} {arg0})", True),
        "color_difference": ("(colorDiff {expr} {arg0})", True),
        "color_contrast": ("(colorContrast {expr} {arg0})", True),

        # Media
        "external_video_tag": ("<video-placeholder>", True),
        "external_video_url": ("{expr}", True),
        "video_tag": ("<video-placeholder>", True),
        "model_viewer_tag": ("<model-placeholder>", True),
        "media_tag": ("<media-placeholder>", True),

        # Shopify specific
        "weight_with_unit": ("(weightWithUnit {expr})", True),
        "highlight": ("(highlight {expr} {arg0})", True),
        "preload_tag": ("", True),
        "stylesheet_tag": ("", True),
        "script_tag": ("", True),
        "font_face": ("", True),
        "font_modify": ("(fontModify {expr} {arg0} {arg1})", True),
        "font_url": ("{expr}", True),
        "payment_type_svg_tag": ("{expr}", True),
        "placeholder_svg_tag": ("{expr}", True),
        "time_tag": ("(moment {expr} {arg0})", True),
        "metafield_tag": ("{expr}", True),
        "metafield_text": ("{expr}", True),
    }

    def convert_filter_chain(self, expression: str, filters: list) -> FilterResult:
        """Apply filter chain to an expression.

        Args:
            expression: The base expression (already mapped by ObjectMapper)
            filters: List of FilterCall objects from the parser

        Returns:
            FilterResult with the converted expression and needed helpers.
        """
        current = expression
        custom_helpers = []

        for filt in filters:
            name = filt.name.strip()
            args = filt.args

            if name in self.FILTER_MAP:
                pattern, is_custom = self.FILTER_MAP[name]

                # Handle placeholder patterns (HTML tags)
                if '<' in pattern and '-placeholder>' in pattern:
                    result = self._handle_html_filter(name, current, args)
                    current = result
                    if is_custom:
                        custom_helpers.append(name)
                    continue

                # Build the expression
                result = pattern.replace('{expr}', current)

                # Replace argument placeholders
                for i, arg in enumerate(args):
                    result = result.replace('{arg' + str(i) + '}', arg.strip())

                # Remove unreplaced arg placeholders
                import re
                result = re.sub(r'\s*\{arg\d+\}', '', result)

                current = result
                if is_custom:
                    custom_helpers.append(name)
            else:
                # Unknown filter — wrap in comment
                if args:
                    arg_str = ' '.join(a.strip() for a in args)
                    current = f'({name} {current} {arg_str})'
                else:
                    current = f'({name} {current})'
                custom_helpers.append(name)

        return FilterResult(current, custom_helpers)

    def _handle_html_filter(self, name: str, expr: str, args: list) -> str:
        """Convert filters that produce HTML elements."""
        if name == 'img_tag':
            alt = args[0].strip("'\"") if args else ''
            css = args[1].strip("'\"") if len(args) > 1 else ''
            cls = f' class="{css}"' if css else ''
            return f'<img src="{{{{{expr}}}}}" alt="{alt}"{cls}>'

        if name in ('link_to', 'link_to_vendor', 'link_to_type', 'link_to_tag'):
            url = args[0].strip("'\"") if args else '#'
            title = args[1].strip("'\"") if len(args) > 1 else ''
            t = f' title="{title}"' if title else ''
            return f'<a href="{url}"{t}>{{{{{expr}}}}}</a>'

        if name in ('external_video_tag', 'video_tag'):
            return f'<video src="{{{{{expr}}}}}"></video>'

        return expr

    def generate_custom_helpers_js(self, needed_helpers: set) -> str:
        """Generate JavaScript file registering custom Handlebars helpers."""
        lines = [
            "'use strict';",
            "",
            "/**",
            " * Custom Handlebars helpers for Shopify-to-BigCommerce theme conversion.",
            " * Register these helpers in your Stencil theme.",
            " */",
            "",
        ]

        helper_implementations = {
            "toUpperCase": """
Handlebars.registerHelper('toUpperCase', function(str) {
    return typeof str === 'string' ? str.toUpperCase() : str;
});""",
            "toLowerCase": """
Handlebars.registerHelper('toLowerCase', function(str) {
    return typeof str === 'string' ? str.toLowerCase() : str;
});""",
            "capitalize": """
Handlebars.registerHelper('capitalize', function(str) {
    if (typeof str !== 'string') return str;
    return str.charAt(0).toUpperCase() + str.slice(1);
});""",
            "strip": """
Handlebars.registerHelper('strip', function(str) {
    return typeof str === 'string' ? str.trim() : str;
});""",
            "stripHtml": """
Handlebars.registerHelper('stripHtml', function(str) {
    return typeof str === 'string' ? str.replace(/<[^>]*>/g, '') : str;
});""",
            "stripNewlines": """
Handlebars.registerHelper('stripNewlines', function(str) {
    return typeof str === 'string' ? str.replace(/\\n/g, '') : str;
});""",
            "nl2br": """
Handlebars.registerHelper('nl2br', function(str) {
    return typeof str === 'string' ? new Handlebars.SafeString(str.replace(/\\n/g, '<br>')) : str;
});""",
            "truncate": """
Handlebars.registerHelper('truncate', function(str, len) {
    if (typeof str !== 'string') return str;
    len = parseInt(len) || 50;
    return str.length > len ? str.substring(0, len) + '...' : str;
});""",
            "truncateWords": """
Handlebars.registerHelper('truncateWords', function(str, count) {
    if (typeof str !== 'string') return str;
    count = parseInt(count) || 15;
    var words = str.split(/\\s+/);
    return words.length > count ? words.slice(0, count).join(' ') + '...' : str;
});""",
            "replace": """
Handlebars.registerHelper('replace', function(str, search, replacement) {
    if (typeof str !== 'string') return str;
    return str.split(search).join(replacement || '');
});""",
            "replaceFirst": """
Handlebars.registerHelper('replaceFirst', function(str, search, replacement) {
    if (typeof str !== 'string') return str;
    var idx = str.indexOf(search);
    if (idx === -1) return str;
    return str.substring(0, idx) + (replacement || '') + str.substring(idx + search.length);
});""",
            "concat": """
Handlebars.registerHelper('concat', function() {
    var args = Array.prototype.slice.call(arguments, 0, -1);
    return args.join('');
});""",
            "split": """
Handlebars.registerHelper('split', function(str, separator) {
    return typeof str === 'string' ? str.split(separator) : [];
});""",
            "sanitize": """
Handlebars.registerHelper('sanitize', function(str) {
    if (typeof str !== 'string') return str;
    return Handlebars.Utils.escapeExpression(str);
});""",
            "encodeURI": """
Handlebars.registerHelper('encodeURI', function(str) {
    return typeof str === 'string' ? encodeURIComponent(str) : str;
});""",
            "decodeURI": """
Handlebars.registerHelper('decodeURI', function(str) {
    return typeof str === 'string' ? decodeURIComponent(str) : str;
});""",
            "length": """
Handlebars.registerHelper('length', function(arr) {
    if (Array.isArray(arr)) return arr.length;
    if (typeof arr === 'string') return arr.length;
    return 0;
});""",
            "first": """
Handlebars.registerHelper('first', function(arr) {
    return Array.isArray(arr) && arr.length > 0 ? arr[0] : null;
});""",
            "last": """
Handlebars.registerHelper('last', function(arr) {
    return Array.isArray(arr) && arr.length > 0 ? arr[arr.length - 1] : null;
});""",
            "join": """
Handlebars.registerHelper('join', function(arr, separator) {
    return Array.isArray(arr) ? arr.join(separator || ', ') : '';
});""",
            "sort": """
Handlebars.registerHelper('sort', function(arr) {
    return Array.isArray(arr) ? arr.slice().sort() : arr;
});""",
            "pluck": """
Handlebars.registerHelper('pluck', function(arr, key) {
    if (!Array.isArray(arr)) return [];
    return arr.map(function(item) { return item[key]; });
});""",
            "where": """
Handlebars.registerHelper('where', function(arr, key, value) {
    if (!Array.isArray(arr)) return [];
    return arr.filter(function(item) { return item[key] == value; });
});""",
            "unique": """
Handlebars.registerHelper('unique', function(arr) {
    return Array.isArray(arr) ? arr.filter(function(v, i, a) { return a.indexOf(v) === i; }) : arr;
});""",
            "compact": """
Handlebars.registerHelper('compact', function(arr) {
    return Array.isArray(arr) ? arr.filter(Boolean) : arr;
});""",
            "reverse": """
Handlebars.registerHelper('reverse', function(arr) {
    return Array.isArray(arr) ? arr.slice().reverse() : arr;
});""",
            "add": """
Handlebars.registerHelper('add', function(a, b) {
    return Number(a) + Number(b);
});""",
            "subtract": """
Handlebars.registerHelper('subtract', function(a, b) {
    return Number(a) - Number(b);
});""",
            "multiply": """
Handlebars.registerHelper('multiply', function(a, b) {
    return Number(a) * Number(b);
});""",
            "divide": """
Handlebars.registerHelper('divide', function(a, b) {
    return b != 0 ? Number(a) / Number(b) : 0;
});""",
            "mod": """
Handlebars.registerHelper('mod', function(a, b) {
    return Number(a) % Number(b);
});""",
            "ceil": """
Handlebars.registerHelper('ceil', function(n) { return Math.ceil(Number(n)); });""",
            "floor": """
Handlebars.registerHelper('floor', function(n) { return Math.floor(Number(n)); });""",
            "round": """
Handlebars.registerHelper('round', function(n) { return Math.round(Number(n)); });""",
            "abs": """
Handlebars.registerHelper('abs', function(n) { return Math.abs(Number(n)); });""",
            "atLeast": """
Handlebars.registerHelper('atLeast', function(a, b) {
    return Math.max(Number(a), Number(b));
});""",
            "atMost": """
Handlebars.registerHelper('atMost', function(a, b) {
    return Math.min(Number(a), Number(b));
});""",
            "moment": """
Handlebars.registerHelper('moment', function(date, format) {
    // Basic date formatting - for full support consider moment.js
    var d = new Date(date);
    if (isNaN(d.getTime())) return date;
    return d.toLocaleDateString();
});""",
            "or": """
Handlebars.registerHelper('or', function(a, b) {
    return a || b;
});""",
            "plural": """
Handlebars.registerHelper('plural', function(count, singular, plural) {
    return Number(count) === 1 ? singular : plural;
});""",
            "handleize": """
Handlebars.registerHelper('handleize', function(str) {
    if (typeof str !== 'string') return str;
    return str.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
});""",
            "typeof": """
Handlebars.registerHelper('typeof', function(obj) { return typeof obj; });""",
            "default": """
Handlebars.registerHelper('default', function(val, defaultVal) {
    return val || defaultVal;
});""",
        }

        # Map filter names to helper names
        filter_to_helper = {
            "upcase": "toUpperCase", "downcase": "toLowerCase",
            "capitalize": "capitalize", "strip": "strip", "lstrip": "strip",
            "rstrip": "strip", "strip_html": "stripHtml",
            "strip_newlines": "stripNewlines", "newline_to_br": "nl2br",
            "truncate": "truncate", "truncatewords": "truncateWords",
            "replace": "replace", "replace_first": "replaceFirst",
            "remove": "replace", "remove_first": "replaceFirst",
            "append": "concat", "prepend": "concat", "split": "split",
            "escape": "sanitize", "escape_once": "sanitize",
            "url_encode": "encodeURI", "url_decode": "decodeURI",
            "size": "length", "first": "first", "last": "last",
            "join": "join", "sort": "sort", "map": "pluck",
            "where": "where", "uniq": "unique", "compact": "compact",
            "reverse": "reverse", "plus": "add", "minus": "subtract",
            "times": "multiply", "divided_by": "divide", "modulo": "mod",
            "ceil": "ceil", "floor": "floor", "round": "round", "abs": "abs",
            "at_least": "atLeast", "at_most": "atMost", "date": "moment",
            "default": "or", "pluralize": "plural", "handle": "handleize",
            "handleize": "handleize", "type": "typeof",
            "truncate": "truncate",
        }

        added = set()
        for filter_name in sorted(needed_helpers):
            helper_name = filter_to_helper.get(filter_name, filter_name)
            if helper_name in helper_implementations and helper_name not in added:
                lines.append(helper_implementations[helper_name].strip())
                lines.append("")
                added.add(helper_name)

        if not added:
            lines.append("// No custom helpers needed.")

        return '\n'.join(lines)
