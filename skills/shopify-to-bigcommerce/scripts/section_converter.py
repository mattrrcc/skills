#!/usr/bin/env python3
"""Converts Shopify sections and snippets to BigCommerce Stencil components."""

import re
import json
from liquid_parser import (
    tokenize, parse, SchemaNode, StyleNode, JavaScriptNode
)
from handlebars_emitter import HandlebarsEmitter


class SectionConverter:
    """Convert Shopify sections/snippets to BigCommerce components.

    Shopify sections contain:
    - Liquid template content
    - {% schema %} JSON block defining settings, blocks, presets
    - Optional inline {% stylesheet %} and {% javascript %} blocks

    BigCommerce components are Handlebars partials.
    Section schemas become entries in schema.json.
    Inline CSS/JS is extracted to separate asset files.
    """

    def __init__(self, emitter: HandlebarsEmitter = None):
        self.emitter = emitter or HandlebarsEmitter()
        self.extracted_schemas = {}
        self.extracted_css = {}
        self.extracted_js = {}

    def convert_snippet(self, name: str, content: str) -> str:
        """Convert a Shopify snippet to a BigCommerce component partial.

        Returns the converted Handlebars content.
        Output path: templates/components/{name}.html
        """
        warnings = []
        tokens = tokenize(content)
        ast = parse(tokens, warnings)
        converted = self.emitter.emit(ast, filename=f'snippets/{name}.liquid')
        return converted

    def convert_section(self, name: str, content: str) -> tuple:
        """Convert a Shopify section to a BigCommerce component.

        Returns (handlebars_content, schema_dict_or_None, css_or_None, js_or_None).
        """
        warnings = []
        tokens = tokenize(content)
        ast = parse(tokens, warnings)

        # Extract special nodes before emitting
        schema_data = None
        css_content = None
        js_content = None

        for node in ast:
            if isinstance(node, SchemaNode):
                try:
                    schema_data = json.loads(node.json_content)
                except json.JSONDecodeError:
                    self.emitter.warnings.append(
                        f"sections/{name}.liquid: Invalid JSON in schema block"
                    )
            elif isinstance(node, StyleNode):
                css_content = node.css_content.strip()
            elif isinstance(node, JavaScriptNode):
                js_content = node.js_content.strip()

        # Emit the template (schema/style/js nodes return empty string)
        converted = self.emitter.emit(ast, filename=f'sections/{name}.liquid')

        # Store extracted assets
        if schema_data:
            self.extracted_schemas[name] = schema_data
        if css_content:
            self.extracted_css[name] = css_content
        if js_content:
            self.extracted_js[name] = js_content

        return converted, schema_data, css_content, js_content

    def convert_all_snippets(self, snippets: dict) -> dict:
        """Convert all snippets. snippets = {name: content}.

        Returns {name: converted_content}.
        """
        result = {}
        for name, content in snippets.items():
            clean_name = name.replace('.liquid', '')
            result[clean_name] = self.convert_snippet(clean_name, content)
        return result

    def convert_all_sections(self, sections: dict) -> dict:
        """Convert all sections. sections = {name: content}.

        Returns {name: (converted_content, schema, css, js)}.
        """
        result = {}
        for name, content in sections.items():
            clean_name = name.replace('.liquid', '')
            result[clean_name] = self.convert_section(clean_name, content)
        return result

    def get_merged_schemas(self) -> list:
        """Get all extracted section schemas merged into a list for schema.json."""
        merged = []
        for name, schema in self.extracted_schemas.items():
            if 'name' not in schema:
                schema['name'] = name.replace('-', ' ').replace('_', ' ').title()
            if 'settings' in schema:
                group = {
                    'name': f"Section: {schema.get('name', name)}",
                    'settings': self._convert_section_settings(schema['settings'])
                }
                merged.append(group)
        return merged

    def _convert_section_settings(self, settings: list) -> list:
        """Convert section setting definitions to BigCommerce schema format."""
        converted = []
        for setting in settings:
            if not isinstance(setting, dict):
                continue
            s_type = setting.get('type', 'text')
            s_id = setting.get('id', '')
            if not s_id:
                continue

            bc_setting = {
                'type': self._map_setting_type(s_type),
                'label': setting.get('label', s_id),
                'id': s_id,
            }

            if 'default' in setting:
                bc_setting['default'] = setting['default']
            if 'info' in setting:
                bc_setting['description'] = setting['info']
            if 'options' in setting:
                bc_setting['options'] = [
                    {'value': opt.get('value', ''), 'label': opt.get('label', '')}
                    for opt in setting['options']
                    if isinstance(opt, dict)
                ]

            converted.append(bc_setting)
        return converted

    def _map_setting_type(self, shopify_type: str) -> str:
        """Map Shopify setting type to BigCommerce type."""
        type_map = {
            'color': 'color',
            'color_background': 'color',
            'color_scheme': 'select',
            'color_scheme_group': 'select',
            'text': 'text',
            'textarea': 'text',
            'richtext': 'text',
            'html': 'text',
            'liquid': 'text',
            'number': 'input',
            'range': 'input',
            'select': 'select',
            'radio': 'select',
            'checkbox': 'checkbox',
            'image_picker': 'imageDimension',
            'url': 'text',
            'font_picker': 'font',
            'collection': 'text',
            'collection_list': 'text',
            'product': 'text',
            'product_list': 'text',
            'blog': 'text',
            'page': 'text',
            'link_list': 'text',
            'article': 'text',
            'video': 'text',
            'video_url': 'text',
            'header': 'heading',
            'paragraph': 'paragraph',
            'inline_richtext': 'text',
        }
        return type_map.get(shopify_type, 'text')
