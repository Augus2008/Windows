"""Transactional multi-file loading without Tk calls or partial application state."""
from pathlib import Path
from types import SimpleNamespace
import os
import re
import pandas as pd
from audit_ledger import snapshot, unique_column


class ImportCancelled(Exception):
    pass


def enrich_fields(frame):
    """Fill values/percent per row across mixed text formats; preserve existing data."""
    frame = frame.copy()
    texts = [c for c in ('日志内容', '文本内容', '原始行') if c in frame.columns]
    for key in ('values', 'percent'):
        if not texts:
            continue
        values = frame[key].copy() if key in frame else pd.Series('', index=frame.index, dtype=object)
        values = values.astype(object)
        for col in texts:
            missing = values.isna() | values.astype(str).str.strip().eq('')
            extracted = frame[col].fillna('').astype(str).str.extract(
                r'(?i)(?<![A-Za-z0-9_])' + key + r'\s*[:=]\s*([^\s,;]+)', expand=False)
            values = values.where(~missing, extracted.fillna(''))
        frame[key] = values
    return frame


def read_dataset(path, parsers, sheet=None):
    path = Path(path)
    names = []
    if path.suffix.lower() in ('.xlsx', '.xls'):
        with pd.ExcelFile(path) as book:
            names = book.sheet_names
            if not names:
                raise ValueError('Excel contains no worksheets')
            frame = pd.read_excel(book, sheet_name=sheet or names[0])
    else:
        # Reuse legacy parsers on an isolated holder; loaded() must not touch Tk.
        holder = SimpleNamespace(source=None, loaded=lambda: None)
        parser = parsers.get(path.suffix.lower(), parsers['text'])
        parser(holder, str(path))
        frame = holder.source
    frame = frame.copy()
    frame.columns = [str(c) for c in frame.columns]
    if not frame.columns.is_unique:
        raise ValueError('Duplicate column names after normalization')
    return frame, names


def load_selection(paths, parsers, progress=None, cancelled=None, sheet=None):
    paths=list(paths)
    selected, seen = [], set()
    for value in paths:
        path = Path(value).resolve()
        identity = os.path.normcase(str(path))
        if identity not in seen:
            seen.add(identity)
            selected.append(path)
    if not selected:
        raise ValueError('No files selected')
    frames, names, manifest, lineage = [], [], [], {}
    offset=0
    batch = len(selected) > 1
    for index, path in enumerate(selected, 1):
        if cancelled and cancelled.is_set():
            raise ImportCancelled()
        if progress:
            progress(index, len(selected), path.name)
        try:
            before=snapshot(path)
            frame, sheets = read_dataset(path, parsers, sheet)
            if snapshot(path)!=before:
                raise ValueError("Source changed while reading")
            frames.append(enrich_fields(frame) if batch else frame)
            names.append(sheets)
            fid=f'file_{index}'
            selected_sheet=(sheet or sheets[0]) if sheets else None
            manifest.append(dict(file_id=fid,path=str(path),status='read',
                read_rows=len(frame),worksheets_read=[selected_sheet] if sheets else [],
                worksheets_skipped=[x for x in sheets if x!=selected_sheet],**before))
            for n in range(len(frame)):
                lineage[offset+n]=(fid,n+1)
            offset+=len(frame)
        except Exception as exc:
            raise ValueError(f'{path.name}: {exc}') from exc
    if cancelled and cancelled.is_set():
        raise ImportCancelled()
    source_column = None
    record_column = None
    if batch:
        source_column = '来源文件'
        used = {c for frame in frames for c in frame.columns}
        suffix = 2
        while source_column in used:
            source_column = f'来源文件_{suffix}'
            suffix += 1
        record_column=unique_column(used | {source_column}, '来源记录')
        for f in frames:
            f.insert(0,record_column,list(range(1,len(f)+1)))
        basenames = [p.name for p in selected]
        for path, frame in zip(selected, frames):
            # Distinguish identically named files from different directories.
            frame.insert(0, source_column, str(path) if basenames.count(path.name) > 1 else path.name)
        # Protect integers BEFORE missing columns introduce NaN/float coercion.
        frame = pd.concat([f.astype(object) for f in frames], ignore_index=True, sort=False)
        # pandas <2.2 fillna may silently infer mixed int/float objects back to float.
        frame = frame.where(frame.notna(), '')
    else:
        frame = frames[0]
    return {'paths': selected, 'frame': frame, 'sheet_names': names[0],
            'source_column': source_column, 'record_column':record_column,
            'manifest':manifest,'lineage':lineage,
            'selection':{'input_count':len(paths),'unique_files':len(selected),
                         'duplicate_selections':len(paths)-len(selected)}}
