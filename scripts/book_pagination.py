"""Map the stable scan sequence to the book's printed and catalog labels."""
import json
from pathlib import Path


def load_pagination(path):
    config = json.loads(Path(path).read_text(encoding='utf-8'))
    pages = [None]
    numeric = {}
    section_links = []
    for group in config['ranges']:
        first, last, section = group['first'], group['last'], group['section']
        if first != len(pages) or last < first:
            raise ValueError(f'Non-contiguous scan range: {group}')
        if section != '正文':
            section_links.append((section, first))
        for scan in range(first, last + 1):
            i = scan - first
            printed = group.get('printedStart')
            printed = i + printed if printed is not None else None
            special = config['special'].get(str(scan), {})
            ref = special.get('tocReference')
            label = special.get('name')
            if ref is not None:
                label = f'{label}（目录标第 {ref} 页）'
            elif label is None:
                if printed is None:
                    label = f'{section}第 {i + 1} 张'
                elif section == '正文':
                    label = f'原书第 {printed} 页'
                else:
                    label = f'{section} · 原印第 {printed} 页'
            pages.append({'scan': scan, 'section': section, 'printed': printed, 'label': label})
            number = ref if ref is not None else printed if group.get('numericLookup') else None
            if number is not None:
                if number in numeric:
                    raise ValueError(f'Conflicting primary lookup for page {number}')
                numeric[number] = scan
    if len(pages) - 1 != config['scanCount']:
        raise ValueError('Unexpected scan count')
    return pages, numeric, section_links
