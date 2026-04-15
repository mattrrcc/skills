#!/usr/bin/env python3
"""Converts Liquid AST nodes to BigCommerce Stencil Handlebars templates."""

import re
from liquid_parser import (
    ASTNode, TextNode, OutputNode, IfNode, UnlessNode, ForNode, CaseNode,
    AssignNode, CaptureNode, IncludeNode, CommentNode, RawNode,
    PaginateNode, FormNode, SchemaNode, StyleNode, JavaScriptNode,
    BreakNode, ContinueNode, CycleNode, IncrementNode, DecrementNode,
    LiquidNode, FilterCall
)
from object_mapper import ObjectMapper
from filter_converter import FilterConverter


class HandlebarsEmitter:
    """Convert a Liquid AST into BigCommerce Stencil Handlebars source."""

    def __init__(self, object_mapper: ObjectMapper = None,
                 filter_converter: FilterConverter = None):
        self.mapper = object_mapper or ObjectMapper()
        self.filters = filter_converter or FilterConverter()
        self.custom_helpers_needed = set()
        self.warnings = []
        self.manual_review = []
        self._current_file = ""
        self._for_var_stack = []  # track for-loop variable remapping

    def emit(self, nodes: list, filename: str = "") -> str:
        """Convert a list of AST nodes to Handlebars source."""
        self._current_file = filename
        parts = []
        for node in nodes:
            parts.append(self.emit_node(node))
        return ''.join(parts)

    def emit_node(self, node) -> str:
        """Dispatch to the appropriate handler."""
        if isinstance(node, TextNode):
            return node.text
        elif isinstance(node, OutputNode):
            return self._emit_output(node)
        elif isinstance(node, IfNode):
            return self._emit_if(node)
        elif isinstance(node, UnlessNode):
            return self._emit_unless(node)
        elif isinstance(node, ForNode):
            return self._emit_for(node)
        elif isinstance(node, CaseNode):
            return self._emit_case(node)
        elif isinstance(node, AssignNode):
            return self._emit_assign(node)
        elif isinstance(node, CaptureNode):
            return self._emit_capture(node)
        elif isinstance(node, IncludeNode):
            return self._emit_include(node)
        elif isinstance(node, CommentNode):
            return self._emit_comment(node)
        elif isinstance(node, RawNode):
            return node.text
        elif isinstance(node, PaginateNode):
            return self._emit_paginate(node)
        elif isinstance(node, FormNode):
            return self._emit_form(node)
        elif isinstance(node, SchemaNode):
            return ''  # Schema extracted separately
        elif isinstance(node, StyleNode):
            return ''  # CSS extracted separately
        elif isinstance(node, JavaScriptNode):
            return ''  # JS extracted separately
        elif isinstance(node, BreakNode):
            return '{{!-- MANUAL: break not supported in Handlebars each --}}'
        elif isinstance(node, ContinueNode):
            return '{{!-- MANUAL: continue not supported in Handlebars each --}}'
        elif isinstance(node, CycleNode):
            return self._emit_cycle(node)
        elif isinstance(node, IncrementNode):
            return self._emit_increment(node)
        elif isinstance(node, DecrementNode):
            return self._emit_decrement(node)
        elif isinstance(node, LiquidNode):
            return self._emit_liquid(node)
        else:
            return str(node)

    def _emit_output(self, node: OutputNode) -> str:
        """Convert {{ expression | filter }} to Handlebars output."""
        expr = node.expression.strip()

        # Map the expression through object mapper
        mapped = self.mapper.map_expression(expr)
        if mapped.note and not mapped.confident:
            self.warnings.append(f"{self._current_file}: {mapped.note}")
        result_expr = mapped.expression

        # Apply filters
        if node.filters:
            fr = self.filters.convert_filter_chain(result_expr, node.filters)
            result_expr = fr.expression
            for h in fr.custom_helpers_needed:
                self.custom_helpers_needed.add(h)

        # Clean up expression for output
        result_expr = result_expr.strip()

        # Check if expression is a helper call (starts with parenthesis)
        if result_expr.startswith('(') and result_expr.endswith(')'):
            # Unwrap for block helper syntax
            inner = result_expr[1:-1]
            return '{{' + inner + '}}'

        # Check if it contains raw HTML (from HTML-producing filters)
        if '<' in result_expr and '>' in result_expr:
            return result_expr

        # Triple-stache for unescaped HTML content
        if any(f.name in ('newline_to_br', 'highlight', 'metafield_tag')
               for f in node.filters):
            return '{{{' + result_expr + '}}}'

        # Special content_for replacements that are already triple-stache
        if result_expr.startswith('{{{'):
            return result_expr

        return '{{' + result_expr + '}}'

    def _emit_if(self, node: IfNode) -> str:
        """Convert if/elsif/else/endif."""
        condition = self._convert_condition(node.condition)
        parts = [f'{{{{#if {condition}}}}}']
        parts.append(self._emit_body(node.body))

        for cond, body in node.elsif_branches:
            mapped_cond = self._convert_condition(cond)
            parts.append(f'{{{{else if {mapped_cond}}}}}')
            parts.append(self._emit_body(body))

        if node.else_body is not None:
            parts.append('{{else}}')
            parts.append(self._emit_body(node.else_body))

        parts.append('{{/if}}')
        return ''.join(parts)

    def _emit_unless(self, node: UnlessNode) -> str:
        """Convert unless to {{#unless}}."""
        condition = self._convert_condition(node.condition)
        parts = [f'{{{{#unless {condition}}}}}']
        parts.append(self._emit_body(node.body))

        if node.else_body is not None:
            parts.append('{{else}}')
            parts.append(self._emit_body(node.else_body))

        parts.append('{{/unless}}')
        return ''.join(parts)

    def _emit_for(self, node: ForNode) -> str:
        """Convert for loop to {{#each}}.

        Handles variable remapping: inside {{#each}}, the loop variable
        becomes 'this', so references to the variable need remapping.
        """
        # Map the iterable
        mapped_iter = self.mapper.map_expression(node.iterable)
        iterable = mapped_iter.expression

        # Track variable for remapping inside the body
        self._for_var_stack.append(node.variable)

        parts = []

        # Handle limit/offset with comments
        if node.limit or node.offset:
            notes = []
            if node.offset:
                notes.append(f'offset:{node.offset}')
            if node.limit:
                notes.append(f'limit:{node.limit}')
            parts.append(f'{{{{!-- MANUAL: for loop had {", ".join(notes)} --}}}}')

        if node.reversed:
            parts.append(f'{{{{!-- MANUAL: reversed iteration --}}}}')

        parts.append(f'{{{{#each {iterable}}}}}')
        parts.append(self._emit_body(node.body))

        if node.else_body is not None:
            parts.append('{{else}}')
            parts.append(self._emit_body(node.else_body))

        parts.append('{{/each}}')

        self._for_var_stack.pop()
        return ''.join(parts)

    def _emit_case(self, node: CaseNode) -> str:
        """Convert case/when to nested if/else if."""
        mapped_expr = self.mapper.map_expression(node.expression)
        expr = mapped_expr.expression
        parts = []

        for i, (value, body) in enumerate(node.whens):
            # Handle comma-separated when values
            values = [v.strip() for v in value.split(',')]
            conditions = [f'(eq {expr} {v})' for v in values]

            if len(conditions) > 1:
                condition = ' '.join(conditions)
                # Use or helper for multiple values
                parts.append(
                    f'{{{{{"#if" if i == 0 else "else if"} (or {" ".join(conditions)})}}}}'
                )
            else:
                cond = conditions[0]
                if i == 0:
                    parts.append(f'{{{{#if {cond}}}}}')
                else:
                    parts.append(f'{{{{else if {cond}}}}}')

            parts.append(self._emit_body(body))

        if node.else_body is not None:
            parts.append('{{else}}')
            parts.append(self._emit_body(node.else_body))

        if node.whens:
            parts.append('{{/if}}')

        self.custom_helpers_needed.add('eq')
        return ''.join(parts)

    def _emit_assign(self, node: AssignNode) -> str:
        """Convert assign — Handlebars doesn't have native assign."""
        mapped = self._map_filter_expression(node.expression)
        self.manual_review.append({
            'file': self._current_file,
            'reason': f'assign "{node.variable}" needs manual review',
            'detail': f'Original: {node.expression}'
        })
        return f'{{{{!-- assign {node.variable} = {mapped} --}}}}'

    def _emit_capture(self, node: CaptureNode) -> str:
        """Convert capture block."""
        body = self._emit_body(node.body)
        self.manual_review.append({
            'file': self._current_file,
            'reason': f'capture "{node.variable}" needs manual review',
        })
        return (f'{{{{!-- capture {node.variable} --}}}}'
                f'{body}'
                f'{{{{!-- endcapture {node.variable} --}}}}')

    def _emit_include(self, node: IncludeNode) -> str:
        """Convert include/render/section to partial."""
        name = node.template_name.replace('.liquid', '')

        if node.tag == 'section':
            partial_path = f'components/sections/{name}'
        else:
            partial_path = f'components/{name}'

        # Handle variable passing
        if node.variables:
            vars_str = ' '.join(
                f'{k}={v}' for k, v in node.variables.items()
                if k != '__with__'
            )
            if '__with__' in node.variables:
                with_var = node.variables['__with__']
                mapped = self.mapper.map_expression(with_var)
                return f'{{{{> {partial_path} {mapped.expression}}}}}'
            if vars_str:
                return f'{{{{> {partial_path} {vars_str}}}}}'

        return f'{{{{> {partial_path}}}}}'

    def _emit_comment(self, node: CommentNode) -> str:
        """Convert Liquid comment to Handlebars comment."""
        return f'{{{{!-- {node.text.strip()} --}}}}'

    def _emit_paginate(self, node: PaginateNode) -> str:
        """Convert paginate block."""
        mapped = self.mapper.map_expression(node.collection)
        body = self._emit_body(node.body)
        self.manual_review.append({
            'file': self._current_file,
            'reason': 'Pagination needs manual review — BigCommerce handles pagination differently',
        })
        return (f'{{{{!-- paginate {mapped.expression} by {node.per_page} --}}}}\n'
                f'{body}\n'
                f'{{{{!-- endpaginate --}}}}')

    def _emit_form(self, node: FormNode) -> str:
        """Convert Shopify form tags to BigCommerce equivalents."""
        form_type = node.form_type
        body = self._emit_body(node.body)

        # Map common Shopify form types to BigCommerce patterns
        form_mappings = {
            'product': ('<form action="/cart/add" method="post" '
                       'enctype="multipart/form-data">\n'
                       '  <input type="hidden" name="action" value="add">\n'
                       '  <input type="hidden" name="product_id" value="{{product.id}}">\n'),
            'customer_login': '<form action="{{urls.auth.login}}" method="post">\n',
            'create_customer': '<form action="{{urls.auth.create_account}}" method="post">\n',
            'recover_customer_password': '<form action="{{urls.auth.forgot_password}}" method="post">\n',
            'contact': '<form action="/pages/contact-us" method="post">\n',
            'customer_address': '<form action="/account/addresses" method="post">\n',
            'new_comment': '<form action="/blog/comment" method="post">\n',
            'activate_customer_password': '<form method="post">\n',
        }

        form_open = form_mappings.get(
            form_type,
            f'<form method="post">{{{{!-- MANUAL: unknown form type "{form_type}" --}}}}\n'
        )

        return f'{form_open}{body}\n</form>'

    def _emit_cycle(self, node: CycleNode) -> str:
        """Convert cycle to modulo-based class switching."""
        if len(node.values) == 2:
            return (f'{{{{#if @index}}}}{{{{#if (mod @index 2)}}}}'
                    f'{node.values[1]}{{{{else}}}}{node.values[0]}{{{{/if}}}}'
                    f'{{{{else}}}}{node.values[0]}{{{{/if}}}}')
        # For more values, generate a comment
        vals = ', '.join(f'"{v}"' for v in node.values)
        self.manual_review.append({
            'file': self._current_file,
            'reason': f'cycle with {len(node.values)} values needs custom helper',
        })
        return f'{{{{!-- MANUAL: cycle {vals} --}}}}'

    def _emit_increment(self, node: IncrementNode) -> str:
        self.manual_review.append({
            'file': self._current_file,
            'reason': f'increment "{node.variable}" has no Handlebars equivalent',
        })
        return f'{{{{!-- MANUAL: increment {node.variable} --}}}}'

    def _emit_decrement(self, node: DecrementNode) -> str:
        self.manual_review.append({
            'file': self._current_file,
            'reason': f'decrement "{node.variable}" has no Handlebars equivalent',
        })
        return f'{{{{!-- MANUAL: decrement {node.variable} --}}}}'

    def _emit_liquid(self, node: LiquidNode) -> str:
        """Emit inline liquid tag contents."""
        parts = []
        for child in node.body:
            parts.append(self.emit_node(child))
        return ''.join(parts)

    def _emit_body(self, nodes: list) -> str:
        """Emit a list of nodes."""
        return ''.join(self.emit_node(n) for n in nodes)

    def _convert_condition(self, condition: str) -> str:
        """Convert a Liquid condition to Handlebars-compatible condition."""
        condition = condition.strip()

        # Handle 'contains' operator
        if ' contains ' in condition:
            parts = condition.split(' contains ', 1)
            left = self.mapper.map_expression(parts[0].strip()).expression
            right = parts[1].strip()
            self.custom_helpers_needed.add('contains')
            return f'(contains {left} {right})'

        # Handle comparison operators
        for op, helper in [('==', 'eq'), ('!=', 'ne'), ('>=', 'gte'),
                           ('<=', 'lte'), ('>', 'gt'), ('<', 'lt')]:
            if f' {op} ' in condition:
                parts = condition.split(f' {op} ', 1)
                left = self.mapper.map_expression(parts[0].strip()).expression
                right = self._map_value(parts[1].strip())
                self.custom_helpers_needed.add(helper)
                return f'({helper} {left} {right})'

        # Handle 'and' / 'or'
        if ' and ' in condition:
            parts = condition.split(' and ')
            mapped = [self._convert_condition(p.strip()) for p in parts]
            self.custom_helpers_needed.add('and')
            return f'(and {" ".join(mapped)})'

        if ' or ' in condition:
            parts = condition.split(' or ')
            mapped = [self._convert_condition(p.strip()) for p in parts]
            self.custom_helpers_needed.add('or')
            return f'(or {" ".join(mapped)})'

        # Simple truthy check
        mapped = self.mapper.map_expression(condition)
        return mapped.expression

    def _map_value(self, value: str) -> str:
        """Map a value that might be a variable or literal."""
        value = value.strip()
        # Quoted strings, numbers, booleans — pass through
        if (value.startswith("'") or value.startswith('"') or
                re.match(r'^[\d.]+$', value) or
                value in ('true', 'false', 'nil', 'null', 'blank', 'empty')):
            if value in ('nil', 'null', 'blank', 'empty'):
                return 'null'
            return value
        # Variable reference
        return self.mapper.map_expression(value).expression

    def _map_filter_expression(self, expression: str) -> str:
        """Map an expression that may contain filters."""
        # Simple: just map the whole thing
        parts = expression.split('|')
        if len(parts) == 1:
            return self.mapper.map_expression(expression.strip()).expression
        base = self.mapper.map_expression(parts[0].strip()).expression
        filters_str = ' | '.join(p.strip() for p in parts[1:])
        return f'{base} | {filters_str}'
