#!/usr/bin/env python3
"""Main entry point: orchestrates full Shopify -> BigCommerce theme conversion."""

import sys
import json
import os
from pathlib import Path

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from liquid_parser import tokenize, parse, parse_template
from handlebars_emitter import HandlebarsEmitter
from object_mapper import ObjectMapper
from filter_converter import FilterConverter
from section_converter import SectionConverter
from layout_converter import LayoutConverter
from settings_converter import SettingsConverter
from locale_converter import LocaleConverter
from asset_migrator import AssetMigrator
from stencil_scaffolder import StencilScaffolder
from report_generator import ConversionReport, ReportGenerator


# Template name mapping: Shopify template -> BigCommerce page
TEMPLATE_MAP = {
    'index': 'home',
    'product': 'product',
    'collection': 'category',
    'cart': 'cart',
    'page': 'page',
    'blog': 'blog',
    'article': 'blog-post',
    'search': 'search',
    '404': 'errors/404',
    'password': 'auth/password',
    'customers/login': 'account/login',
    'customers/register': 'account/register',
    'customers/account': 'account/orders',
    'customers/order': 'account/order',
    'customers/addresses': 'account/addresses',
    'customers/reset_password': 'account/reset-password',
    'customers/activate_account': 'account/activate',
    'gift_card': 'gift-card',
    'list-collections': 'brands',
}


def convert_theme(shopify_dir: str, output_dir: str,
                  theme_name: str = 'converted-theme') -> ConversionReport:
    """Full conversion pipeline.

    Pipeline stages:
    1. Validate input directory
    2. Scaffold output Stencil structure
    3. Convert snippets (referenced by sections/templates)
    4. Convert sections (referenced by templates)
    5. Convert layout (theme.liquid -> base.html)
    6. Convert page templates
    7. Convert settings (schema + data)
    8. Convert locales
    9. Migrate assets
    10. Generate custom helpers
    11. Generate conversion report
    """
    shopify = Path(shopify_dir)
    output = Path(output_dir)
    report = ConversionReport(theme_name=theme_name)

    print(f'Converting Shopify theme: {shopify}')
    print(f'Output directory: {output}')
    print(f'Theme name: {theme_name}')
    print()

    # ---------------------------------------------------------------
    # Stage 1: Validate input
    # ---------------------------------------------------------------
    print('[1/11] Validating input directory...')
    if not shopify.exists():
        report.errors.append(f'Input directory does not exist: {shopify}')
        print('  ERROR: Input directory not found')
        return report

    # Check for key directories
    found = []
    for d in ['layout', 'templates', 'sections', 'snippets', 'assets', 'config']:
        if (shopify / d).exists():
            found.append(d)
    print(f'  Found directories: {", ".join(found) or "none"}')

    if not found:
        report.errors.append('No Shopify theme directories found')
        report.warnings.append(
            'Expected directories: layout/, templates/, sections/, snippets/, '
            'assets/, config/'
        )

    # ---------------------------------------------------------------
    # Stage 2: Scaffold output
    # ---------------------------------------------------------------
    print('[2/11] Scaffolding Stencil theme structure...')
    scaffolder = StencilScaffolder()
    scaffolder.scaffold(output, theme_name)
    print('  Created directory structure and boilerplate')

    # ---------------------------------------------------------------
    # Stage 3: Initialize converters
    # ---------------------------------------------------------------
    mapper = ObjectMapper()
    filter_conv = FilterConverter()
    emitter = HandlebarsEmitter(mapper, filter_conv)
    section_conv = SectionConverter(emitter)
    layout_conv = LayoutConverter(emitter)

    # ---------------------------------------------------------------
    # Stage 4: Convert snippets
    # ---------------------------------------------------------------
    print('[3/11] Converting snippets...')
    snippets_dir = shopify / 'snippets'
    snippets_count = 0
    if snippets_dir.exists():
        for snippet_file in sorted(snippets_dir.glob('*.liquid')):
            name = snippet_file.stem
            content = snippet_file.read_text(errors='replace')
            converted = section_conv.convert_snippet(name, content)

            dest = output / 'templates' / 'components' / f'{name}.html'
            dest.write_text(converted)

            report.converted_files.append({
                'src': f'snippets/{snippet_file.name}',
                'dest': f'templates/components/{name}.html',
                'status': 'ok',
            })
            snippets_count += 1
    print(f'  Converted {snippets_count} snippets')

    # ---------------------------------------------------------------
    # Stage 5: Convert sections
    # ---------------------------------------------------------------
    print('[4/11] Converting sections...')
    sections_dir = shopify / 'sections'
    sections_count = 0
    if sections_dir.exists():
        for section_file in sorted(sections_dir.glob('*.liquid')):
            name = section_file.stem
            content = section_file.read_text(errors='replace')
            converted, schema, css, js = section_conv.convert_section(name, content)

            # Write converted template
            dest = output / 'templates' / 'components' / 'sections' / f'{name}.html'
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(converted)

            # Write extracted CSS
            if css:
                css_dest = output / 'assets' / 'scss' / 'sections' / f'_{name}.scss'
                css_dest.parent.mkdir(parents=True, exist_ok=True)
                css_dest.write_text(css)

            # Write extracted JS
            if js:
                js_dest = output / 'assets' / 'js' / 'sections' / f'{name}.js'
                js_dest.parent.mkdir(parents=True, exist_ok=True)
                js_dest.write_text(js)

            status = 'warning' if schema else 'ok'
            report.converted_files.append({
                'src': f'sections/{section_file.name}',
                'dest': f'templates/components/sections/{name}.html',
                'status': status,
                'note': 'Schema extracted' if schema else '',
            })
            sections_count += 1
    print(f'  Converted {sections_count} sections')

    # ---------------------------------------------------------------
    # Stage 6: Convert layout
    # ---------------------------------------------------------------
    print('[5/11] Converting layout...')
    layout_dir = shopify / 'layout'
    if layout_dir.exists():
        for layout_file in sorted(layout_dir.glob('*.liquid')):
            content = layout_file.read_text(errors='replace')
            converted = layout_conv.convert(content)

            if layout_file.name == 'theme.liquid':
                dest_name = 'base.html'
            else:
                dest_name = layout_file.stem + '.html'

            dest = output / 'templates' / 'layout' / dest_name
            dest.write_text(converted)

            report.converted_files.append({
                'src': f'layout/{layout_file.name}',
                'dest': f'templates/layout/{dest_name}',
                'status': 'ok',
            })
            print(f'  Converted {layout_file.name} -> {dest_name}')
    else:
        print('  No layout directory found')

    # ---------------------------------------------------------------
    # Stage 7: Convert templates
    # ---------------------------------------------------------------
    print('[6/11] Converting templates...')
    templates_dir = shopify / 'templates'
    templates_count = 0
    if templates_dir.exists():
        # Handle both .liquid and .json templates
        for tmpl_file in sorted(templates_dir.glob('**/*')):
            if tmpl_file.is_dir():
                continue

            rel_path = tmpl_file.relative_to(templates_dir)
            name = str(rel_path.with_suffix('')).replace('\\', '/')

            if tmpl_file.suffix == '.liquid':
                content = tmpl_file.read_text(errors='replace')
                converted = _convert_template(content, name, emitter, report)

                # Map to BigCommerce page name
                bc_name = TEMPLATE_MAP.get(name, name)
                dest = output / 'templates' / 'pages' / f'{bc_name}.html'
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_text(converted)

                report.converted_files.append({
                    'src': f'templates/{rel_path}',
                    'dest': f'templates/pages/{bc_name}.html',
                    'status': 'ok',
                })
                templates_count += 1

            elif tmpl_file.suffix == '.json':
                # Shopify OS 2.0 JSON templates
                _convert_json_template(tmpl_file, name, output, report)
                templates_count += 1

    print(f'  Converted {templates_count} templates')

    # ---------------------------------------------------------------
    # Stage 8: Convert settings
    # ---------------------------------------------------------------
    print('[7/11] Converting settings...')
    settings_conv = SettingsConverter()
    config_dir = shopify / 'config'

    schema_data = []
    settings_data = {}

    if config_dir.exists():
        schema_file = config_dir / 'settings_schema.json'
        data_file = config_dir / 'settings_data.json'

        if schema_file.exists():
            try:
                raw_schema = json.loads(schema_file.read_text(errors='replace'))
                schema_data = settings_conv.convert_schema(raw_schema)
                report.settings_mapped = sum(
                    len(g.get('settings', [])) for g in schema_data
                )
                print(f'  Converted {report.settings_mapped} settings from schema')
            except json.JSONDecodeError as e:
                report.errors.append(f'Failed to parse settings_schema.json: {e}')
                print(f'  ERROR: Invalid settings_schema.json')

        if data_file.exists():
            try:
                raw_data = json.loads(data_file.read_text(errors='replace'))
                raw_schema_for_data = json.loads(
                    schema_file.read_text(errors='replace')
                ) if schema_file.exists() else []
                settings_data = settings_conv.convert_data(
                    raw_data, raw_schema_for_data, theme_name
                )
            except json.JSONDecodeError as e:
                report.errors.append(f'Failed to parse settings_data.json: {e}')
    else:
        print('  No config directory found')

    # Merge section schemas
    section_schemas = section_conv.get_merged_schemas()
    if section_schemas:
        schema_data = settings_conv.merge_section_schemas(schema_data, section_schemas)
        print(f'  Merged {len(section_schemas)} section schemas')

    # Write schema.json
    schema_dest = output / 'schema.json'
    schema_dest.write_text(json.dumps(schema_data, indent=2))

    # Write config.json
    if settings_data:
        config_dest = output / 'config.json'
        config_dest.write_text(json.dumps(settings_data, indent=2))
    else:
        # Generate minimal config.json
        minimal_config = settings_conv.convert_data({}, [], theme_name)
        config_dest = output / 'config.json'
        config_dest.write_text(json.dumps(minimal_config, indent=2))

    report.converted_files.append({
        'src': 'config/settings_schema.json',
        'dest': 'schema.json',
        'status': 'ok' if schema_data else 'warning',
    })
    report.converted_files.append({
        'src': 'config/settings_data.json',
        'dest': 'config.json',
        'status': 'ok' if settings_data else 'warning',
    })

    # ---------------------------------------------------------------
    # Stage 9: Convert locales
    # ---------------------------------------------------------------
    print('[8/11] Converting locales...')
    locale_conv = LocaleConverter()
    locales_dir = shopify / 'locales'
    locales_count = 0

    if locales_dir.exists():
        for locale_file in sorted(locales_dir.glob('*.json')):
            try:
                content = json.loads(locale_file.read_text(errors='replace'))
                code = locale_file.stem.replace('.default', '')
                converted = locale_conv.convert(content, code)

                dest = output / 'lang' / f'{code}.json'
                dest.write_text(json.dumps(converted, indent=2, ensure_ascii=False))

                report.converted_files.append({
                    'src': f'locales/{locale_file.name}',
                    'dest': f'lang/{code}.json',
                    'status': 'ok',
                })
                locales_count += 1
            except json.JSONDecodeError as e:
                report.errors.append(f'Failed to parse {locale_file.name}: {e}')
    else:
        # Generate default en.json
        default_lang = _generate_default_lang()
        dest = output / 'lang' / 'en.json'
        dest.write_text(json.dumps(default_lang, indent=2))
        print('  Generated default en.json')

    if locales_count:
        print(f'  Converted {locales_count} locale files')

    # ---------------------------------------------------------------
    # Stage 10: Migrate assets
    # ---------------------------------------------------------------
    print('[9/11] Migrating assets...')
    asset_migrator = AssetMigrator()
    assets_dir = shopify / 'assets'

    if assets_dir.exists():
        asset_report = asset_migrator.migrate(assets_dir, output)
        report.asset_report = asset_report
        total = (len(asset_report.get('css_files', [])) +
                 len(asset_report.get('js_files', [])) +
                 len(asset_report.get('img_files', [])) +
                 len(asset_report.get('font_files', [])))
        print(f'  Migrated {total} asset files')
    else:
        print('  No assets directory found')

    # ---------------------------------------------------------------
    # Stage 11: Generate custom helpers
    # ---------------------------------------------------------------
    print('[10/11] Generating custom helpers...')
    all_helpers = emitter.custom_helpers_needed
    if all_helpers:
        helpers_js = filter_conv.generate_custom_helpers_js(all_helpers)
        helpers_dest = output / 'assets' / 'js' / 'custom-helpers.js'
        helpers_dest.write_text(helpers_js)
        report.custom_helpers_needed = sorted(all_helpers)
        print(f'  Generated {len(all_helpers)} custom helpers')
    else:
        print('  No custom helpers needed')

    # ---------------------------------------------------------------
    # Stage 12: Collect warnings and generate report
    # ---------------------------------------------------------------
    print('[11/11] Generating conversion report...')
    report.warnings.extend(emitter.warnings)
    report.manual_review.extend(emitter.manual_review)

    # Collect unmapped objects from warnings
    for w in report.warnings:
        if 'Unmapped expression:' in w:
            expr = w.split('Unmapped expression:')[1].strip()
            report.objects_unmapped.append(expr)

    reporter = ReportGenerator()
    reporter.generate(report, output)
    print(f'  Report saved to {output}/conversion-report.md')

    # ---------------------------------------------------------------
    # Summary
    # ---------------------------------------------------------------
    print()
    print('=' * 60)
    print('CONVERSION COMPLETE')
    print('=' * 60)
    print(f'Files converted: {len(report.converted_files)}')
    print(f'Warnings: {len(report.warnings)}')
    print(f'Errors: {len(report.errors)}')
    print(f'Manual review items: {len(report.manual_review)}')
    print(f'Custom helpers: {len(report.custom_helpers_needed)}')
    print(f'Output: {output}')
    print()

    return report


def _convert_template(content: str, name: str, emitter: HandlebarsEmitter,
                      report: ConversionReport) -> str:
    """Convert a single Liquid template to Handlebars."""
    warnings = []
    tokens = tokenize(content)
    ast = parse(tokens, warnings)
    converted = emitter.emit(ast, filename=f'templates/{name}.liquid')

    # Wrap in BigCommerce page partial pattern
    bc_name = TEMPLATE_MAP.get(name, name)
    wrapped = f'{{{{!-- Converted from Shopify template: {name} --}}}}\n'
    wrapped += f'{{{{#partial "page"}}}}\n'
    wrapped += converted
    wrapped += f'\n{{{{/partial}}}}\n'
    wrapped += f'{{{{> layout/base}}}}\n'

    return wrapped


def _convert_json_template(tmpl_file: Path, name: str, output: Path,
                           report: ConversionReport):
    """Convert Shopify OS 2.0 JSON template.

    JSON templates define section ordering and are fundamentally different
    from BigCommerce's approach. We extract the section references and
    create a simple Handlebars template.
    """
    try:
        data = json.loads(tmpl_file.read_text(errors='replace'))
    except json.JSONDecodeError:
        report.errors.append(f'Failed to parse JSON template: {tmpl_file.name}')
        return

    # Extract sections and their order
    sections = data.get('sections', {})
    order = data.get('order', list(sections.keys()))

    # Build a Handlebars template with section includes
    bc_name = TEMPLATE_MAP.get(name, name)
    lines = [f'{{{{!-- Converted from Shopify JSON template: {name} --}}}}']
    lines.append('{{#partial "page"}}')

    for section_id in order:
        section = sections.get(section_id, {})
        section_type = section.get('type', section_id)
        lines.append(f'{{{{> components/sections/{section_type}}}}}')

    lines.append('{{/partial}}')
    lines.append('{{> layout/base}}')

    dest = output / 'templates' / 'pages' / f'{bc_name}.html'
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text('\n'.join(lines))

    report.converted_files.append({
        'src': f'templates/{tmpl_file.name}',
        'dest': f'templates/pages/{bc_name}.html',
        'status': 'warning',
        'note': 'JSON template - section ordering converted but dynamic sections need manual setup',
    })

    report.manual_review.append({
        'file': f'templates/{tmpl_file.name}',
        'reason': 'Shopify OS 2.0 JSON template with dynamic sections. '
                  'BigCommerce uses widgets for dynamic content regions. '
                  'Section ordering was preserved but needs manual verification.',
    })


def _generate_default_lang() -> dict:
    """Generate a default English language file."""
    return {
        'en': {
            'header': {
                'search': 'Search',
                'cart': 'Cart',
                'account': 'Account',
                'login': 'Log in',
                'logout': 'Log out',
            },
            'products': {
                'add_to_cart': 'Add to Cart',
                'sold_out': 'Sold Out',
                'unavailable': 'Unavailable',
                'quantity': 'Quantity',
                'description': 'Description',
                'price': 'Price',
                'sale_price': 'Sale Price',
            },
            'cart': {
                'title': 'Your Cart',
                'empty': 'Your cart is empty',
                'subtotal': 'Subtotal',
                'checkout': 'Check Out',
                'continue_shopping': 'Continue Shopping',
                'remove': 'Remove',
                'update': 'Update',
            },
            'pagination': {
                'previous': 'Previous',
                'next': 'Next',
            },
            'search': {
                'title': 'Search',
                'placeholder': 'Search our store',
                'results_for': 'Results for',
                'no_results': 'No results found',
            },
            'blog': {
                'read_more': 'Read More',
                'comments': 'Comments',
                'share': 'Share',
            },
            'account': {
                'title': 'My Account',
                'orders': {'title': 'Order History'},
                'addresses': {'title': 'Addresses'},
            },
            'auth': {
                'login': {'title': 'Login', 'submit': 'Sign In'},
                'register': {'title': 'Create Account', 'submit': 'Create'},
                'reset_password': {'title': 'Reset Password'},
            },
            'errors': {
                '404': {
                    'title': 'Page Not Found',
                    'message': 'The page you requested does not exist.',
                    'back_home': 'Back to Home',
                },
            },
            'social': {
                'share_on': 'Share on',
            },
        }
    }


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print('Usage: python convert_theme.py <shopify_dir> <output_dir> [theme_name]')
        print()
        print('Arguments:')
        print('  shopify_dir  Path to the Shopify theme directory')
        print('  output_dir   Path for the BigCommerce Stencil theme output')
        print('  theme_name   Optional theme name (default: converted-theme)')
        sys.exit(1)

    shopify_dir = sys.argv[1]
    output_dir = sys.argv[2]
    name = sys.argv[3] if len(sys.argv) > 3 else 'converted-theme'

    report = convert_theme(shopify_dir, output_dir, name)

    if report.errors:
        sys.exit(1)
