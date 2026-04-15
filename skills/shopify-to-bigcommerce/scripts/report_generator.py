#!/usr/bin/env python3
"""Generates detailed conversion reports."""

import json
from pathlib import Path
from dataclasses import dataclass, field


@dataclass
class ConversionReport:
    """Tracks everything that happened during conversion."""
    converted_files: list = field(default_factory=list)
    warnings: list = field(default_factory=list)
    errors: list = field(default_factory=list)
    manual_review: list = field(default_factory=list)
    settings_mapped: int = 0
    settings_skipped: int = 0
    filters_converted: int = 0
    custom_helpers_needed: list = field(default_factory=list)
    objects_remapped: int = 0
    objects_unmapped: list = field(default_factory=list)
    asset_report: dict = field(default_factory=dict)
    theme_name: str = ""

    def to_dict(self) -> dict:
        return {
            'theme_name': self.theme_name,
            'summary': {
                'total_files': len(self.converted_files),
                'successful': sum(1 for f in self.converted_files if f.get('status') == 'ok'),
                'with_warnings': sum(1 for f in self.converted_files if f.get('status') == 'warning'),
                'failed': sum(1 for f in self.converted_files if f.get('status') == 'error'),
                'manual_review_items': len(self.manual_review),
                'settings_mapped': self.settings_mapped,
                'settings_skipped': self.settings_skipped,
                'custom_helpers_needed': len(self.custom_helpers_needed),
                'objects_unmapped': len(self.objects_unmapped),
            },
            'files': self.converted_files,
            'warnings': self.warnings,
            'errors': self.errors,
            'manual_review': self.manual_review,
            'custom_helpers': self.custom_helpers_needed,
            'unmapped_objects': self.objects_unmapped,
            'assets': self.asset_report,
        }


class ReportGenerator:
    """Generate conversion reports in JSON and Markdown formats."""

    def generate(self, report: ConversionReport, output_dir: Path):
        """Write conversion-report.json and conversion-report.md."""
        output = Path(output_dir)

        # JSON report
        json_path = output / 'conversion-report.json'
        json_path.write_text(json.dumps(report.to_dict(), indent=2, default=str))

        # Markdown report
        md_path = output / 'conversion-report.md'
        md_path.write_text(self._generate_markdown(report))

    def _generate_markdown(self, report: ConversionReport) -> str:
        """Create a human-readable Markdown report."""
        lines = []
        data = report.to_dict()
        summary = data['summary']

        lines.append(f'# Theme Conversion Report: {report.theme_name}')
        lines.append('')

        # Summary
        lines.append('## Summary')
        lines.append('')
        lines.append(f'| Metric | Value |')
        lines.append(f'|--------|-------|')
        lines.append(f'| Total files processed | {summary["total_files"]} |')
        lines.append(f'| Successfully converted | {summary["successful"]} |')
        lines.append(f'| With warnings | {summary["with_warnings"]} |')
        lines.append(f'| Failed | {summary["failed"]} |')
        lines.append(f'| Manual review items | {summary["manual_review_items"]} |')
        lines.append(f'| Settings mapped | {summary["settings_mapped"]} |')
        lines.append(f'| Settings skipped | {summary["settings_skipped"]} |')
        lines.append(f'| Custom helpers needed | {summary["custom_helpers_needed"]} |')
        lines.append(f'| Unmapped objects | {summary["objects_unmapped"]} |')
        lines.append('')

        # Converted files
        lines.append('## Converted Files')
        lines.append('')
        for f in report.converted_files:
            status = f.get('status', 'unknown')
            icon = {'ok': '+', 'warning': '!', 'error': 'x'}.get(status, '?')
            lines.append(f'- [{icon}] `{f.get("src", "")}` -> `{f.get("dest", "")}`')
            if f.get('note'):
                lines.append(f'  - {f["note"]}')
        lines.append('')

        # Manual review items
        if report.manual_review:
            lines.append('## Items Requiring Manual Review')
            lines.append('')
            for item in report.manual_review:
                lines.append(f'### `{item.get("file", "")}`')
                lines.append(f'- **Reason**: {item.get("reason", "")}')
                if item.get('detail'):
                    lines.append(f'- **Detail**: {item["detail"]}')
                lines.append('')

        # Warnings
        if report.warnings:
            lines.append('## Warnings')
            lines.append('')
            for w in report.warnings:
                lines.append(f'- {w}')
            lines.append('')

        # Errors
        if report.errors:
            lines.append('## Errors')
            lines.append('')
            for e in report.errors:
                lines.append(f'- {e}')
            lines.append('')

        # Custom helpers
        if report.custom_helpers_needed:
            lines.append('## Custom Handlebars Helpers Needed')
            lines.append('')
            lines.append('These Handlebars helpers are used in the converted theme and must')
            lines.append('be registered in your Stencil theme. A `custom-helpers.js` file has')
            lines.append('been generated with implementations.')
            lines.append('')
            for h in sorted(report.custom_helpers_needed):
                lines.append(f'- `{h}`')
            lines.append('')

        # Unmapped objects
        if report.objects_unmapped:
            lines.append('## Unmapped Shopify Objects')
            lines.append('')
            lines.append('These Shopify object references could not be automatically mapped')
            lines.append('to BigCommerce equivalents and need manual attention:')
            lines.append('')
            for obj in sorted(set(report.objects_unmapped)):
                lines.append(f'- `{obj}`')
            lines.append('')

        # Asset report
        if report.asset_report:
            lines.append('## Asset Migration')
            lines.append('')
            ar = report.asset_report
            lines.append(f'- CSS/SCSS files: {len(ar.get("css_files", []))}')
            lines.append(f'- JavaScript files: {len(ar.get("js_files", []))}')
            lines.append(f'- Image files: {len(ar.get("img_files", []))}')
            lines.append(f'- Font files: {len(ar.get("font_files", []))}')
            lines.append(f'- Other files: {len(ar.get("other_files", []))}')
            if ar.get('scss_variables'):
                lines.append(f'- SCSS variables extracted: {len(ar["scss_variables"])}')
            lines.append('')

        # Next steps
        lines.append('## Next Steps')
        lines.append('')
        lines.append('1. Review all "Manual Review" items above and fix them')
        lines.append('2. Register custom Handlebars helpers in your Stencil theme')
        lines.append('3. Rebuild navigation using BigCommerce admin (Shopify linklists do not transfer)')
        lines.append('4. Test with `stencil start` (requires BigCommerce store + API token)')
        lines.append('5. Map SCSS variables in `_variables.scss` to your `config.json` settings')
        lines.append('6. Test checkout flow (BigCommerce checkout is different from Shopify)')
        lines.append('7. Upload theme with `stencil bundle` and apply in BigCommerce admin')
        lines.append('')

        lines.append('## Known Limitations')
        lines.append('')
        lines.append('- Shopify checkout customization does not transfer')
        lines.append('- Shopify app-specific Liquid tags have no BigCommerce equivalent')
        lines.append('- Navigation must be rebuilt manually')
        lines.append('- Some Liquid filters use custom helpers that may need tuning')
        lines.append('- Shopify OS 2.0 dynamic sections need manual recreation as BigCommerce widgets')
        lines.append('- Metafields map to custom fields but the structure differs')
        lines.append('')

        return '\n'.join(lines)
