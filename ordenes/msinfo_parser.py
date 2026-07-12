import re
from typing import Optional


def parse_informe(content: str) -> list[dict]:
    if not content or not content.strip():
        return []

    first_line = content.strip().split('\n', 1)[0].strip()

    if first_line.startswith('['):
        return _parse_msinfo32(content)
    elif first_line.startswith('=') or '---' in content[:200]:
        return _parse_custom_powershell(content)
    else:
        return _parse_generic(content)


def _parse_msinfo32(content: str) -> list[dict]:
    sections = []
    current_name = None
    current_lines = []

    for raw in content.split('\n'):
        line = raw.rstrip('\r').rstrip('\n')
        stripped = line.strip()

        if re.match(r'^\[.+\]$', stripped):
            if current_name:
                parsed = _parse_section_blocks(current_lines)
                sections.append({'name': current_name, **parsed})
            current_name = stripped[1:-1]
            current_lines = []
        elif stripped:
            current_lines.append(line)

    if current_name:
        parsed = _parse_section_blocks(current_lines)
        sections.append({'name': current_name, **parsed})

    return sections


def _parse_section_blocks(lines: list[str]) -> dict:
    blocks = _split_blocks(lines)

    subsections = []
    for block in blocks:
        sub = _parse_block(block)
        if sub:
            subsections.append(sub)

    if not subsections:
        return {'type': 'empty', 'subsections': []}

    single_type = subsections[0]['type']
    if len(subsections) == 1 and single_type == 'kv':
        return {'type': 'kv', 'items': subsections[0]['items'], 'subsections': subsections}

    return {'type': 'mixed', 'subsections': subsections}


def _split_blocks(lines: list[str]) -> list[list[str]]:
    blocks = []
    current = []
    for line in lines:
        if not line.strip():
            if current:
                blocks.append(current)
                current = []
        else:
            current.append(line)
    if current:
        blocks.append(current)
    return blocks


def _parse_block(lines: list[str]) -> Optional[dict]:
    if not lines:
        return None

    non_empty = [l for l in lines if l.strip()]

    tab_lines = [l for l in non_empty if '\t' in l]
    no_tab_lines = [l for l in non_empty if '\t' not in l]

    if not tab_lines and no_tab_lines:
        return {'type': 'text', 'lines': [l.strip() for l in no_tab_lines]}

    if no_tab_lines:
        header = no_tab_lines[0].strip()
        data_lines = tab_lines
    else:
        header = None
        data_lines = tab_lines

    rows = [l.split('\t') for l in data_lines]
    col_counts = [len(r) for r in rows]
    max_cols = max(col_counts) if col_counts else 0

    if max_cols <= 2:
        items = []
        for r in rows:
            key = r[0].strip() if len(r) >= 1 else ''
            val = r[1].strip() if len(r) >= 2 else ''
            if key or val:
                items.append({'key': key, 'value': val})
        return {'type': 'kv', 'header': header, 'items': items}
    else:
        first = [c.strip() for c in rows[0]]
        remaining = [[c.strip() for c in r] for r in rows[1:]]

        looks_like_header = all(
            not any(c.isdigit() for c in cell if c)
            for cell in first
        ) and len(non_empty) > 1

        if looks_like_header and remaining:
            return {'type': 'table', 'header': header, 'columns': first, 'rows': remaining}
        else:
            return {'type': 'table', 'header': header, 'columns': None, 'rows': [first] + remaining}


def _parse_custom_powershell(content: str) -> list[dict]:
    sections = []
    current_name = None
    current_lines = []

    for line in content.split('\n'):
        stripped = line.strip()
        m = re.match(r'^---+\s*(.+?)\s*---+$', stripped)
        if m:
            if current_name:
                sections.append(_parse_custom_section(current_name, current_lines))
            current_name = m.group(1).strip()
            current_lines = []
        elif stripped:
            current_lines.append(line)
        else:
            current_lines.append(line)

    if current_name:
        sections.append(_parse_custom_section(current_name, current_lines))

    return sections


def _parse_custom_section(name: str, lines: list[str]) -> dict:
    items = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if ':' in stripped:
            key, _, val = stripped.partition(':')
            items.append({'key': key.strip(), 'value': val.strip()})
        else:
            items.append({'key': stripped, 'value': ''})

    return {
        'name': name,
        'type': 'kv',
        'items': items,
        'subsections': [{'type': 'kv', 'items': items}]
    }


def _parse_generic(content: str) -> list[dict]:
    return [{'name': 'Informe', 'type': 'text', 'subsections': [], 'lines': content.split('\n')}]


def sections_to_html(sections: list[dict]) -> str:
    if not sections:
        return ''

    parts = ['<div class="msinfo-container">']

    for section in sections:
        name = section.get('name', '')
        stype = section.get('type', 'empty')
        subsections = section.get('subsections', [])
        items = section.get('items', [])

        if stype == 'empty' and not subsections and not items:
            continue

        if stype == 'kv' and items:
            parts.append(f'<details class="msinfo-section" open>')
            parts.append(f'<summary class="msinfo-section-title">{_esc(name)}</summary>')
            parts.append('<table class="msinfo-table">')
            for item in items:
                k = item.get('key', '')
                v = item.get('value', '')
                parts.append(f'<tr><td class="msinfo-key">{_esc(k)}</td><td class="msinfo-val">{_esc(v)}</td></tr>')
            parts.append('</table>')
            parts.append('</details>')
            continue

        if stype == 'text':
            text_lines = section.get('lines', [])
            if text_lines:
                parts.append(f'<details class="msinfo-section">')
                parts.append(f'<summary class="msinfo-section-title">{_esc(name)}</summary>')
                parts.append(f'<pre class="msinfo-raw">{_esc(chr(10).join(text_lines))}</pre>')
                parts.append('</details>')
            continue

        # Mixed or empty
        has_content = False
        for sub in subsections:
            if sub.get('items') or sub.get('rows'):
                has_content = True
                break

        if not has_content:
            continue

        parts.append(f'<details class="msinfo-section">')
        parts.append(f'<summary class="msinfo-section-title">{_esc(name)}</summary>')

        for sub in subsections:
            parts.append(_render_subsection(sub))

        parts.append('</details>')

    parts.append('</div>')
    return '\n'.join(parts)


def _render_subsection(sub: dict) -> str:
    stype = sub.get('type', 'text')
    header = sub.get('header')
    items = sub.get('items', [])
    columns = sub.get('columns')
    rows = sub.get('rows', [])
    text_lines = sub.get('lines', [])

    if not items and not rows and not text_lines:
        return ''

    label = header if header else ''
    parts = []

    if label:
        parts.append(f'<div class="msinfo-subsection-title">{_esc(label)}</div>')

    if stype == 'kv' and items:
        parts.append('<table class="msinfo-table">')
        for item in items:
            k = item.get('key', '')
            v = item.get('value', '')
            if k or v:
                parts.append(f'<tr><td class="msinfo-key">{_esc(k)}</td><td class="msinfo-val">{_esc(v)}</td></tr>')
        parts.append('</table>')

    elif stype == 'table' and rows:
        parts.append('<table class="msinfo-table msinfo-table-data">')
        if columns:
            parts.append('<thead><tr>')
            for col in columns:
                parts.append(f'<th>{_esc(col)}</th>')
            parts.append('</tr></thead>')
        parts.append('<tbody>')
        for row in rows:
            parts.append('<tr>')
            for cell in row:
                parts.append(f'<td>{_esc(cell)}</td>')
            parts.append('</tr>')
        parts.append('</tbody>')
        parts.append('</table>')

    elif stype == 'text':
        parts.append(f'<pre class="msinfo-raw msinfo-text">{_esc(chr(10).join(text_lines))}</pre>')

    return '\n'.join(parts)


def _esc(s: str) -> str:
    return (s
            .replace('&', '&amp;')
            .replace('<', '&lt;')
            .replace('>', '&gt;')
            .replace('"', '&quot;')
            .replace("'", '&#x27;'))


def informe_to_html(content: str) -> str:
    sections = parse_informe(content)
    html = sections_to_html(sections)
    css = _get_css()
    return f'<style>{css}</style>{html}'


def _get_css() -> str:
    return """
.msinfo-container{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;font-size:.85rem;line-height:1.5}
.msinfo-section{margin-bottom:2px;border:1px solid #e2e8f0;border-radius:6px;overflow:hidden}
.msinfo-section[open]{background:#fff}
.msinfo-section-title{padding:8px 12px;cursor:pointer;font-weight:600;color:#0f172a;background:#f8fafc;border-bottom:1px solid transparent;user-select:none}
.msinfo-section[open]>.msinfo-section-title{border-bottom-color:#e2e8f0;background:#f1f5f9}
.msinfo-section-title:hover{background:#e2e8f0}
.msinfo-subsection-title{padding:6px 12px 2px;font-weight:600;color:#475569;font-size:.8rem;text-transform:uppercase;letter-spacing:.4px}
.msinfo-table{width:100%;border-collapse:collapse;margin:4px 0}
.msinfo-table tr{border-bottom:1px solid #f1f5f9}
.msinfo-table tr:last-child{border-bottom:none}
.msinfo-table td,.msinfo-table th{padding:3px 12px;vertical-align:top;font-size:.8rem}
.msinfo-table th{text-align:left;font-weight:600;color:#64748b;background:#f8fafc;border-bottom:2px solid #e2e8f0}
.msinfo-key{width:35%;font-weight:500;color:#334155;white-space:nowrap;padding-right:16px}
.msinfo-val{color:#0f172a;word-break:break-word}
.msinfo-table-data td,.msinfo-table-data th{padding:3px 10px;white-space:nowrap}
.msinfo-table-data tbody tr:hover{background:#f8fafc}
.msinfo-raw{padding:8px 12px;margin:4px 0;font-family:'Cascadia Code','Fira Code','Consolas',monospace;font-size:.77rem;line-height:1.4;background:#f8fafc;border-radius:4px;overflow-x:auto;color:#334155}
.msinfo-text{margin:4px 12px}
"""

