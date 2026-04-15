#!/usr/bin/env python3
"""Tokenizer and AST builder for Shopify Liquid templates."""

import re
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Union, Optional


class TokenType(Enum):
    TEXT = auto()
    OUTPUT = auto()          # {{ ... }}
    TAG = auto()             # {% ... %}
    COMMENT = auto()         # {% comment %}...{% endcomment %}
    RAW = auto()             # {% raw %}...{% endraw %}
    SCHEMA = auto()          # {% schema %}...{% endschema %}
    STYLE = auto()           # {% stylesheet %}...{% endstylesheet %}
    JAVASCRIPT = auto()      # {% javascript %}...{% endjavascript %}


@dataclass
class Token:
    type: TokenType
    content: str
    line: int
    col: int


# ---------------------------------------------------------------------------
# AST Node types
# ---------------------------------------------------------------------------

@dataclass
class TextNode:
    text: str

@dataclass
class FilterCall:
    name: str
    args: list

@dataclass
class OutputNode:
    expression: str
    filters: list

@dataclass
class IfNode:
    condition: str
    body: list
    elsif_branches: list       # [(condition, body), ...]
    else_body: Optional[list]

@dataclass
class UnlessNode:
    condition: str
    body: list
    else_body: Optional[list]

@dataclass
class ForNode:
    variable: str
    iterable: str
    body: list
    else_body: Optional[list]
    limit: Optional[int]
    offset: Optional[int]
    reversed: bool

@dataclass
class CaseNode:
    expression: str
    whens: list                # [(value, body), ...]
    else_body: Optional[list]

@dataclass
class AssignNode:
    variable: str
    expression: str

@dataclass
class CaptureNode:
    variable: str
    body: list

@dataclass
class IncludeNode:
    template_name: str
    variables: dict
    tag: str                   # "include", "render", or "section"

@dataclass
class CommentNode:
    text: str

@dataclass
class RawNode:
    text: str

@dataclass
class PaginateNode:
    collection: str
    per_page: int
    body: list

@dataclass
class FormNode:
    form_type: str
    args: list
    body: list

@dataclass
class SchemaNode:
    json_content: str

@dataclass
class StyleNode:
    css_content: str

@dataclass
class JavaScriptNode:
    js_content: str

@dataclass
class BreakNode:
    pass

@dataclass
class ContinueNode:
    pass

@dataclass
class CycleNode:
    group: Optional[str]
    values: list

@dataclass
class IncrementNode:
    variable: str

@dataclass
class DecrementNode:
    variable: str

@dataclass
class LiquidNode:
    """{% liquid %} tag containing multiple statements."""
    body: list


ASTNode = Union[
    TextNode, OutputNode, IfNode, UnlessNode, ForNode, CaseNode,
    AssignNode, CaptureNode, IncludeNode, CommentNode, RawNode,
    PaginateNode, FormNode, SchemaNode, StyleNode, JavaScriptNode,
    BreakNode, ContinueNode, CycleNode, IncrementNode, DecrementNode,
    LiquidNode
]


# ---------------------------------------------------------------------------
# Tokenizer
# ---------------------------------------------------------------------------

# Block-level tags that grab everything until their matching end tag
_BLOCK_TAGS = {
    'comment': ('endcomment', TokenType.COMMENT),
    'raw': ('endraw', TokenType.RAW),
    'schema': ('endschema', TokenType.SCHEMA),
    'stylesheet': ('endstylesheet', TokenType.STYLE),
    'javascript': ('endjavascript', TokenType.JAVASCRIPT),
}

_TOKEN_RE = re.compile(
    r'(\{\{-?\s*.*?\s*-?\}\})'   # output tags {{ }}
    r'|'
    r'(\{%-?\s*.*?\s*-?%\})',     # logic tags {% %}
    re.DOTALL
)


def _count_lines(text: str, end: int):
    """Count line and col up to position end."""
    line = text[:end].count('\n') + 1
    last_nl = text.rfind('\n', 0, end)
    col = end - last_nl if last_nl >= 0 else end + 1
    return line, col


def tokenize(source: str) -> list:
    """Split Liquid source into tokens."""
    tokens = []
    pos = 0

    while pos < len(source):
        m = _TOKEN_RE.search(source, pos)
        if m is None:
            # Rest is plain text
            text = source[pos:]
            if text:
                line, col = _count_lines(source, pos)
                tokens.append(Token(TokenType.TEXT, text, line, col))
            break

        # Text before this match
        if m.start() > pos:
            text = source[pos:m.start()]
            line, col = _count_lines(source, pos)
            tokens.append(Token(TokenType.TEXT, text, line, col))

        raw = m.group(0)
        line, col = _count_lines(source, m.start())

        if raw.startswith('{{'):
            # Output tag
            inner = re.sub(r'^\{\{-?\s*', '', raw)
            inner = re.sub(r'\s*-?\}\}$', '', inner)
            tokens.append(Token(TokenType.OUTPUT, inner, line, col))
            pos = m.end()
        else:
            # Logic tag {% ... %}
            inner = re.sub(r'^\{%-?\s*', '', raw)
            inner = re.sub(r'\s*-?%\}$', '', inner)
            tag_name = inner.split()[0] if inner.split() else ''

            if tag_name in _BLOCK_TAGS:
                end_tag, token_type = _BLOCK_TAGS[tag_name]
                end_pattern = re.compile(
                    r'\{%-?\s*' + re.escape(end_tag) + r'\s*-?%\}', re.DOTALL
                )
                end_m = end_pattern.search(source, m.end())
                if end_m:
                    block_content = source[m.end():end_m.start()]
                    tokens.append(Token(token_type, block_content, line, col))
                    pos = end_m.end()
                else:
                    # No matching end tag — treat as text
                    tokens.append(Token(TokenType.TEXT, raw, line, col))
                    pos = m.end()
            else:
                tokens.append(Token(TokenType.TAG, inner, line, col))
                pos = m.end()

    return tokens


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------

def parse_output_expression(content: str):
    """Parse '{{ expression | filter1 | filter2: arg }}' content into OutputNode."""
    # Split on pipes not inside quotes
    parts = _split_filters(content)
    expression = parts[0].strip()
    filters = []
    for part in parts[1:]:
        part = part.strip()
        if ':' in part:
            name, rest = part.split(':', 1)
            args = [a.strip() for a in _split_args(rest.strip())]
        else:
            name = part
            args = []
        filters.append(FilterCall(name.strip(), args))
    return OutputNode(expression, filters)


def _split_filters(content: str) -> list:
    """Split on | that are not inside quotes."""
    parts = []
    current = []
    in_single = False
    in_double = False
    for ch in content:
        if ch == "'" and not in_double:
            in_single = not in_single
        elif ch == '"' and not in_single:
            in_double = not in_double
        elif ch == '|' and not in_single and not in_double:
            parts.append(''.join(current))
            current = []
            continue
        current.append(ch)
    parts.append(''.join(current))
    return parts


def _split_args(content: str) -> list:
    """Split comma-separated args respecting quotes."""
    args = []
    current = []
    in_single = False
    in_double = False
    for ch in content:
        if ch == "'" and not in_double:
            in_single = not in_single
        elif ch == '"' and not in_single:
            in_double = not in_double
        elif ch == ',' and not in_single and not in_double:
            args.append(''.join(current))
            current = []
            continue
        current.append(ch)
    if current:
        args.append(''.join(current))
    return args


def _parse_tag_content(content: str):
    """Return (tag_name, rest_of_content)."""
    parts = content.strip().split(None, 1)
    name = parts[0] if parts else ''
    rest = parts[1] if len(parts) > 1 else ''
    return name, rest


def _parse_for_tag(rest: str):
    """Parse 'item in collection limit:N offset:N reversed'."""
    # Split on 'in'
    m = re.match(r'(\w+)\s+in\s+(.+)', rest)
    if not m:
        return 'item', rest, None, None, False
    variable = m.group(1)
    remainder = m.group(2).strip()

    # Extract modifiers
    limit = None
    offset = None
    reversed_flag = False

    limit_m = re.search(r'limit\s*:\s*(\d+)', remainder)
    if limit_m:
        limit = int(limit_m.group(1))
        remainder = remainder[:limit_m.start()] + remainder[limit_m.end():]

    offset_m = re.search(r'offset\s*:\s*(\d+)', remainder)
    if offset_m:
        offset = int(offset_m.group(1))
        remainder = remainder[:offset_m.start()] + remainder[offset_m.end():]

    if 'reversed' in remainder:
        reversed_flag = True
        remainder = remainder.replace('reversed', '')

    iterable = remainder.strip()
    return variable, iterable, limit, offset, reversed_flag


def _parse_include_tag(tag: str, rest: str):
    """Parse include/render/section tag."""
    # Template name is the first argument (quoted string or bare word)
    rest = rest.strip()
    template_name = ''
    variables = {}

    m = re.match(r"""['"]([^'"]+)['"]""", rest)
    if m:
        template_name = m.group(1)
        rest = rest[m.end():].strip()
    else:
        parts = rest.split(',', 1)
        template_name = parts[0].strip()
        rest = parts[1].strip() if len(parts) > 1 else ''

    # Remove leading comma if present
    rest = rest.lstrip(',').strip()

    # Parse variable assignments: key: value, key: value
    if rest:
        # Handle 'with' keyword
        with_m = re.match(r'with\s+(.+?)(?:,|$)', rest)
        if with_m:
            variables['__with__'] = with_m.group(1).strip()
            rest = rest[with_m.end():].strip().lstrip(',').strip()

        for pair in _split_args(rest):
            pair = pair.strip()
            if ':' in pair:
                k, v = pair.split(':', 1)
                variables[k.strip()] = v.strip()

    return IncludeNode(template_name, variables, tag)


def _parse_assign(rest: str):
    """Parse 'variable = expression'."""
    m = re.match(r'(\w+)\s*=\s*(.+)', rest, re.DOTALL)
    if m:
        return AssignNode(m.group(1), m.group(2).strip())
    return AssignNode(rest, '')


def _parse_cycle(rest: str):
    """Parse cycle tag: 'group': val1, val2 or just val1, val2."""
    group = None
    rest = rest.strip()
    # Check for group name
    m = re.match(r"""['"]([^'"]+)['"]\s*:\s*(.+)""", rest)
    if m:
        group = m.group(1)
        rest = m.group(2)
    values = [v.strip().strip("'\"") for v in _split_args(rest)]
    return CycleNode(group, values)


class _Parser:
    """Recursive descent parser for Liquid token stream."""

    def __init__(self, tokens: list, warnings: list = None):
        self.tokens = tokens
        self.pos = 0
        self.warnings = warnings if warnings is not None else []

    def at_end(self):
        return self.pos >= len(self.tokens)

    def peek(self):
        if self.at_end():
            return None
        return self.tokens[self.pos]

    def advance(self):
        tok = self.tokens[self.pos]
        self.pos += 1
        return tok

    def peek_tag_name(self):
        """If current token is a TAG, return its tag name."""
        tok = self.peek()
        if tok and tok.type == TokenType.TAG:
            name, _ = _parse_tag_content(tok.content)
            return name
        return None

    def parse(self) -> list:
        return self._parse_block(set())

    def _parse_block(self, end_tags: set) -> list:
        """Parse nodes until we hit a tag in end_tags or end of tokens."""
        nodes = []
        while not self.at_end():
            tag_name = self.peek_tag_name()
            if tag_name in end_tags:
                break
            node = self._parse_node()
            if node is not None:
                nodes.append(node)
        return nodes

    def _parse_node(self):
        tok = self.peek()
        if tok is None:
            return None

        if tok.type == TokenType.TEXT:
            self.advance()
            return TextNode(tok.content)

        if tok.type == TokenType.OUTPUT:
            self.advance()
            return parse_output_expression(tok.content)

        if tok.type == TokenType.COMMENT:
            self.advance()
            return CommentNode(tok.content)

        if tok.type == TokenType.RAW:
            self.advance()
            return RawNode(tok.content)

        if tok.type == TokenType.SCHEMA:
            self.advance()
            return SchemaNode(tok.content)

        if tok.type == TokenType.STYLE:
            self.advance()
            return StyleNode(tok.content)

        if tok.type == TokenType.JAVASCRIPT:
            self.advance()
            return JavaScriptNode(tok.content)

        if tok.type == TokenType.TAG:
            return self._parse_tag()

        # Fallback
        self.advance()
        return TextNode(tok.content)

    def _parse_tag(self):
        tok = self.peek()
        name, rest = _parse_tag_content(tok.content)

        if name == 'if':
            return self._parse_if()
        elif name == 'unless':
            return self._parse_unless()
        elif name == 'for':
            return self._parse_for()
        elif name == 'case':
            return self._parse_case()
        elif name == 'capture':
            return self._parse_capture()
        elif name == 'paginate':
            return self._parse_paginate()
        elif name == 'form':
            return self._parse_form()
        elif name in ('include', 'render', 'section'):
            self.advance()
            return _parse_include_tag(name, rest)
        elif name == 'assign':
            self.advance()
            return _parse_assign(rest)
        elif name == 'cycle':
            self.advance()
            return _parse_cycle(rest)
        elif name == 'increment':
            self.advance()
            return IncrementNode(rest.strip())
        elif name == 'decrement':
            self.advance()
            return DecrementNode(rest.strip())
        elif name == 'break':
            self.advance()
            return BreakNode()
        elif name == 'continue':
            self.advance()
            return ContinueNode()
        elif name == 'liquid':
            self.advance()
            return self._parse_liquid_tag(rest)
        elif name.startswith('end'):
            # Stray end tag — skip with warning
            self.advance()
            self.warnings.append(
                f"Line {tok.line}: Unexpected closing tag '{name}'"
            )
            return None
        else:
            # Unknown tag — preserve as text
            self.advance()
            return TextNode('{%- ' + tok.content + ' -%}')

    def _parse_if(self):
        tok = self.advance()
        _, condition = _parse_tag_content(tok.content)
        body = self._parse_block({'elsif', 'else', 'endif'})
        elsif_branches = []

        while self.peek_tag_name() == 'elsif':
            t = self.advance()
            _, cond = _parse_tag_content(t.content)
            branch_body = self._parse_block({'elsif', 'else', 'endif'})
            elsif_branches.append((cond, branch_body))

        else_body = None
        if self.peek_tag_name() == 'else':
            self.advance()
            else_body = self._parse_block({'endif'})

        if self.peek_tag_name() == 'endif':
            self.advance()
        else:
            self.warnings.append(f"Line {tok.line}: Missing endif for if")

        return IfNode(condition, body, elsif_branches, else_body)

    def _parse_unless(self):
        tok = self.advance()
        _, condition = _parse_tag_content(tok.content)
        body = self._parse_block({'else', 'endunless'})

        else_body = None
        if self.peek_tag_name() == 'else':
            self.advance()
            else_body = self._parse_block({'endunless'})

        if self.peek_tag_name() == 'endunless':
            self.advance()
        else:
            self.warnings.append(f"Line {tok.line}: Missing endunless")

        return UnlessNode(condition, body, else_body)

    def _parse_for(self):
        tok = self.advance()
        _, rest = _parse_tag_content(tok.content)
        variable, iterable, limit, offset, reversed_flag = _parse_for_tag(rest)
        body = self._parse_block({'else', 'endfor'})

        else_body = None
        if self.peek_tag_name() == 'else':
            self.advance()
            else_body = self._parse_block({'endfor'})

        if self.peek_tag_name() == 'endfor':
            self.advance()
        else:
            self.warnings.append(f"Line {tok.line}: Missing endfor")

        return ForNode(variable, iterable, body, else_body, limit, offset, reversed_flag)

    def _parse_case(self):
        tok = self.advance()
        _, expression = _parse_tag_content(tok.content)
        # Skip whitespace text before first when
        self._parse_block({'when', 'else', 'endcase'})

        whens = []
        while self.peek_tag_name() == 'when':
            t = self.advance()
            _, value = _parse_tag_content(t.content)
            when_body = self._parse_block({'when', 'else', 'endcase'})
            whens.append((value.strip(), when_body))

        else_body = None
        if self.peek_tag_name() == 'else':
            self.advance()
            else_body = self._parse_block({'endcase'})

        if self.peek_tag_name() == 'endcase':
            self.advance()
        else:
            self.warnings.append(f"Line {tok.line}: Missing endcase")

        return CaseNode(expression.strip(), whens, else_body)

    def _parse_capture(self):
        tok = self.advance()
        _, variable = _parse_tag_content(tok.content)
        body = self._parse_block({'endcapture'})
        if self.peek_tag_name() == 'endcapture':
            self.advance()
        else:
            self.warnings.append(f"Line {tok.line}: Missing endcapture")
        return CaptureNode(variable.strip(), body)

    def _parse_paginate(self):
        tok = self.advance()
        _, rest = _parse_tag_content(tok.content)
        # Parse "collection.products by 12"
        m = re.match(r'(.+?)\s+by\s+(\d+)', rest)
        if m:
            collection = m.group(1).strip()
            per_page = int(m.group(2))
        else:
            collection = rest.strip()
            per_page = 20

        body = self._parse_block({'endpaginate'})
        if self.peek_tag_name() == 'endpaginate':
            self.advance()
        else:
            self.warnings.append(f"Line {tok.line}: Missing endpaginate")
        return PaginateNode(collection, per_page, body)

    def _parse_form(self):
        tok = self.advance()
        _, rest = _parse_tag_content(tok.content)
        # Parse form type and optional args
        parts = [p.strip().strip("'\"") for p in _split_args(rest)]
        form_type = parts[0] if parts else 'unknown'
        args = parts[1:] if len(parts) > 1 else []

        body = self._parse_block({'endform'})
        if self.peek_tag_name() == 'endform':
            self.advance()
        else:
            self.warnings.append(f"Line {tok.line}: Missing endform")
        return FormNode(form_type, args, body)

    def _parse_liquid_tag(self, content: str):
        """Parse {% liquid %} which contains multiple statements on lines."""
        nodes = []
        for line in content.strip().split('\n'):
            line = line.strip()
            if not line:
                continue
            name, rest = _parse_tag_content(line)
            if name == 'assign':
                nodes.append(_parse_assign(rest))
            elif name in ('include', 'render', 'section'):
                nodes.append(_parse_include_tag(name, rest))
            elif name == 'break':
                nodes.append(BreakNode())
            elif name == 'continue':
                nodes.append(ContinueNode())
            elif name == 'cycle':
                nodes.append(_parse_cycle(rest))
            elif name == 'increment':
                nodes.append(IncrementNode(rest.strip()))
            elif name == 'decrement':
                nodes.append(DecrementNode(rest.strip()))
            else:
                # For complex tags in liquid blocks, treat as text
                nodes.append(TextNode('{{!-- MANUAL: ' + line + ' --}}'))
        return LiquidNode(nodes)


def parse(tokens: list, warnings: list = None) -> list:
    """Build an AST from a token stream."""
    parser = _Parser(tokens, warnings)
    return parser.parse()


def parse_template(source: str, warnings: list = None) -> list:
    """Convenience: tokenize + parse a Liquid template string."""
    tokens = tokenize(source)
    return parse(tokens, warnings)
