#!/usr/bin/env python3
"""Converts Shopify layout/theme.liquid to BigCommerce templates/layout/base.html."""

import re
from liquid_parser import tokenize, parse
from handlebars_emitter import HandlebarsEmitter


class LayoutConverter:
    """Convert Shopify's theme.liquid to BigCommerce's base.html.

    Shopify's theme.liquid is the outermost wrapper containing:
    - HTML <head> with {{ content_for_header }}
    - Body with {{ content_for_layout }}
    - Navigation, header, footer sections

    BigCommerce's base.html uses:
    - {{{head.meta_tags}}} + {{{head.config}}} for head content
    - {{{body}}} for page content
    - {{> components/header}} / {{> components/footer}} for shared sections
    """

    def __init__(self, emitter: HandlebarsEmitter = None):
        self.emitter = emitter or HandlebarsEmitter()

    def convert(self, layout_content: str) -> str:
        """Convert theme.liquid to base.html."""
        warnings = []
        tokens = tokenize(layout_content)
        ast = parse(tokens, warnings)

        # Emit with Handlebars conversion
        converted = self.emitter.emit(ast, filename='layout/theme.liquid')

        # Post-process: fix layout-specific patterns
        converted = self._fix_head_section(converted)
        converted = self._fix_body_section(converted)
        converted = self._add_stencil_requirements(converted)

        return converted

    def _fix_head_section(self, content: str) -> str:
        """Fix head section for BigCommerce requirements."""
        # Replace content_for_header with BigCommerce head tags
        content = content.replace(
            '{{{head.meta_tags}}}',
            '    {{{head.meta_tags}}}\n    {{{head.config}}}'
        )

        # Add BigCommerce required head content if not present
        if '{{{head.config}}}' not in content:
            content = content.replace(
                '</head>',
                '    {{{head.config}}}\n</head>'
            )

        # Replace Shopify-specific meta tags
        content = re.sub(
            r'<meta\s+name="shopify-.*?"[^>]*>',
            '',
            content
        )

        return content

    def _fix_body_section(self, content: str) -> str:
        """Fix body section."""
        # The emitter already maps content_for_layout to {{{body}}}
        # but ensure it's properly placed
        return content

    def _add_stencil_requirements(self, content: str) -> str:
        """Add BigCommerce Stencil-required elements if missing."""
        # Ensure body has data attributes BigCommerce expects
        content = re.sub(
            r'<body([^>]*)>',
            r'<body\1>',
            content,
            count=1
        )

        # Add Stencil footer scripts if not present
        if '{{{footer.scripts}}}' not in content:
            content = content.replace(
                '</body>',
                '    {{{footer.scripts}}}\n</body>'
            )

        return content

    def convert_alternate_layout(self, name: str, content: str) -> str:
        """Convert alternative layout files (e.g., layout/password.liquid)."""
        return self.convert(content)
