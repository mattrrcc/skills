#!/usr/bin/env python3
"""Converts Shopify settings_schema.json + settings_data.json to BigCommerce format."""

import json
import copy


class SettingsConverter:
    """Convert Shopify theme settings to BigCommerce config.json + schema.json.

    Shopify settings_schema.json: array of setting groups with nested settings.
    Shopify settings_data.json: current values + presets.

    BigCommerce schema.json: array of setting groups (similar structure).
    BigCommerce config.json: theme metadata + flat settings values + variations.
    """

    TYPE_MAP = {
        'color': 'color',
        'color_background': 'color',
        'color_scheme': 'select',
        'color_scheme_group': 'select',
        'text': 'text',
        'textarea': 'text',
        'richtext': 'text',
        'html': 'text',
        'liquid': 'text',
        'inline_richtext': 'text',
        'number': 'input',
        'range': 'input',
        'select': 'select',
        'radio': 'select',
        'checkbox': 'checkbox',
        'image_picker': 'imageDimension',
        'url': 'text',
        'font_picker': 'font',
        'font': 'font',
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
    }

    def convert_schema(self, shopify_schema: list) -> list:
        """Convert settings_schema.json to BigCommerce schema.json format."""
        bc_schema = []

        for group in shopify_schema:
            if not isinstance(group, dict):
                continue

            # Skip theme_info group (metadata only)
            if group.get('name') == 'theme_info':
                continue

            settings = group.get('settings', [])
            if not settings:
                continue

            bc_group = {
                'name': group.get('name', 'Settings'),
                'settings': []
            }

            for setting in settings:
                converted = self._convert_setting(setting)
                if converted:
                    bc_group['settings'].append(converted)

            if bc_group['settings']:
                bc_schema.append(bc_group)

        return bc_schema

    def convert_data(self, shopify_data: dict, shopify_schema: list,
                     theme_name: str = "Converted Theme") -> dict:
        """Convert settings_data.json to BigCommerce config.json.

        Returns a config.json structure with:
        - name, version metadata
        - settings: flat key-value pairs of current values
        - variations: at least one variation
        """
        # Extract current values
        current = shopify_data.get('current', {})
        if not current:
            # Try first preset
            presets = shopify_data.get('presets', {})
            if presets:
                first_key = next(iter(presets))
                current = presets[first_key]

        # Build flat settings with defaults
        settings = {}
        for group in shopify_schema:
            if not isinstance(group, dict):
                continue
            for setting in group.get('settings', []):
                if not isinstance(setting, dict):
                    continue
                sid = setting.get('id')
                if not sid:
                    continue
                # Use current value if available, otherwise default
                if sid in current:
                    settings[sid] = current[sid]
                elif 'default' in setting:
                    settings[sid] = setting['default']

        # Build config.json
        config = {
            'name': theme_name,
            'version': '1.0.0',
            'meta': {
                'price': 0,
                'composed_image': '',
                'features': [
                    'fully_responsive',
                    'mega_navigation',
                    'multi_tiered_sidebar_menu',
                    'masonry_design',
                    'frontpage_slideshow',
                    'quick_add_to_cart',
                    'switchable_product_view',
                    'product_comparison_table',
                    'complex_search_filtering',
                    'customizable_product_selector',
                    'cart_suggested_products',
                    'free_customer_support',
                    'free_theme_upgrades',
                    'high_res_product_images',
                    'product_filtering',
                    'advanced_quick_view',
                    'product_showcase',
                    'persistent_cart',
                    'one_page_check_out',
                    'product_videos',
                    'google_amp',
                    'customized_checkout',
                    'account_payment_methods',
                    'enhanced_ecommerce',
                    'csrf_protection',
                    'shopper_consent_tracking',
                ]
            },
            'css_compiler': 'scss',
            'autoprefixer_cascade': True,
            'autoprefixer_browsers': [
                '> 1%',
                'last 2 versions',
                'Firefox ESR'
            ],
            'settings': settings,
            'variations': [
                {
                    'name': 'Default',
                    'id': 'default',
                    'meta': {
                        'desktop_screenshot': '',
                        'mobile_screenshot': '',
                        'description': f'Converted from Shopify theme: {theme_name}',
                    },
                    'settings': {}
                }
            ],
            'resources': {
                'cart': True,
                'bulk_discount_rates': True,
            },
        }

        return config

    def merge_section_schemas(self, base_schema: list,
                              section_schemas: list) -> list:
        """Merge section-extracted schemas into the base schema."""
        return base_schema + section_schemas

    def _convert_setting(self, setting: dict) -> dict:
        """Convert a single Shopify setting to BigCommerce format."""
        if not isinstance(setting, dict):
            return None

        s_type = setting.get('type', '')
        s_id = setting.get('id', '')

        # Header and paragraph types don't have IDs
        if s_type == 'header':
            return {
                'type': 'heading',
                'content': setting.get('content', setting.get('label', '')),
            }

        if s_type == 'paragraph':
            return {
                'type': 'paragraph',
                'content': setting.get('content', ''),
            }

        if not s_id:
            return None

        bc_type = self.TYPE_MAP.get(s_type, 'text')

        bc_setting = {
            'type': bc_type,
            'label': setting.get('label', s_id),
            'id': s_id,
        }

        # Default value
        if 'default' in setting:
            bc_setting['default'] = setting['default']

        # Description / info
        if 'info' in setting:
            bc_setting['description'] = setting['info']

        # Options for select/radio
        if 'options' in setting and bc_type == 'select':
            bc_setting['options'] = []
            for opt in setting['options']:
                if isinstance(opt, dict):
                    bc_setting['options'].append({
                        'value': str(opt.get('value', '')),
                        'label': opt.get('label', str(opt.get('value', ''))),
                    })

        # Range constraints → input with min/max
        if s_type == 'range' and bc_type == 'input':
            if 'min' in setting:
                bc_setting['min'] = setting['min']
            if 'max' in setting:
                bc_setting['max'] = setting['max']
            if 'step' in setting:
                bc_setting['step'] = setting['step']

        # Force reload for visual settings
        if bc_type in ('color', 'font', 'imageDimension'):
            bc_setting['force_reload'] = True

        return bc_setting
