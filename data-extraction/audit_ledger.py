"""File snapshots and row lineage are metadata, never business dedupe keys."""
import hashlib, json, os, tempfile
from pathlib import Path
from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone

def snapshot(path):
    p=Path(path)
    with p.open('rb') as f:
        digest=hashlib.file_digest(f,'sha256').hexdigest()
    return {'size':p.stat().st_size,'sha256':digest}

def safe(value):
    return json.loads(json.dumps(value,ensure_ascii=False,default=lambda v:v.item() if hasattr(v,'item') else str(v),allow_nan=False))

def unique_column(used, name):
    key=name; n=2
    while key in used:
        key=f'{name}_{n}'; n+=1
    return key

class AuditLedger:
    def __init__(self,payload):
        self.manifest=deepcopy(payload['manifest'])
        self.lineage=dict(payload['lineage'])
        self.selection=deepcopy(payload['selection'])
        self.history=[]; self.exports=[]
        self.source_ids=list(payload['frame'].index)
        if len(self.source_ids)!=sum(x['read_rows'] for x in self.manifest):
            raise ValueError('Manifest total mismatch')
        self.current_ids=self.source_ids[:]
        self.record('import','files',[],self.source_ids,self.source_ids,{},list(payload['frame'].columns))

    def counts(self,ids):
        return dict(Counter(self.lineage[i][0] for i in ids))

    def record(self,operation,basis,before,base,after,filters,columns):
        if len(set(after))!=len(after) or any(i not in self.lineage for i in after):
            raise ValueError('Invalid row identity')
        b,a=set(base),set(after)
        event={'time_utc':datetime.now(timezone.utc).isoformat(),'stage':len(self.history)+1,'operation':operation,'input_basis':basis,
          'before':len(before),'base':len(base),'after':len(after),
          'excluded_from_base':len(b-a),'added_to_base':len(a-b),
          'removed_from_previous':len(set(before)-a),'added_to_previous':len(a-set(before)),
          'per_file_before':self.counts(before),'per_file_base':self.counts(base),
          'per_file_after':self.counts(after),'per_file_removed':self.counts(b-a),
          'per_file_added':self.counts(a-b),'filters':deepcopy(filters),'visible_columns':list(columns)}
        self.history.append(safe(event)); self.current_ids=list(after)

    def report(self,columns=None,pending=None):
        counts=self.counts(self.current_ids); files=[]
        for item in self.manifest:
            item=deepcopy(item); item['current_kept']=counts.get(item['file_id'],0)
            item['excluded']=item['read_rows']-item['current_kept']; files.append(item)
        return safe({'schema_version':1,'generated_at_utc':datetime.now(timezone.utc).isoformat(),'result_records':[{'file_id':self.lineage[i][0],'record_number':self.lineage[i][1]} for i in self.current_ids],'selection':self.selection,'files':files,
          'totals':{'read_rows':len(self.source_ids),'current_kept':len(self.current_ids),
          'excluded':len(self.source_ids)-len(self.current_ids),
          'consistent':sum(f['current_kept'] for f in files)==len(self.current_ids)},
          'history':self.history,'exports':self.exports,'visible_columns':columns,
          'pending_controls_not_applied':pending,'privacy':'Contains local source/output paths.',
          'notes':['Export verified status and hashes refer to verified_at_utc, NOT a recheck when saving this report. Same-path overwritten exports have superseded_by.',
          'Record numbers are 1-based parsed data records, NOT physical CSV/text lines.',
          'Excel reads the selected sheet only; other sheets are intentionally skipped.',
          'LOG/TRC unmatched raw records remain in source. Extraction may exclude them.',
          'Excluded = source minus current result; see stages for filter/extract/dedupe reasons.',
          'Apply/extract/reset recompute from source; dedupe uses result. Pending controls are NOT applied.',
          'Export cells preserve the CURRENT PARSED table as text, not original cell types or source bytes. CSV parsing may already infer leading zeros or NA literals.']})

def save_report(report,path,protected=()):
    dest=Path(path).resolve()
    for item in protected:
        p=Path(item).resolve()
        if dest==p or (dest.exists() and p.exists() and os.path.samefile(dest,p)):
            raise ValueError('Report path collides with source/output')
    payload=json.dumps(safe(report),ensure_ascii=False,indent=2,allow_nan=False)
    fd,tmp=tempfile.mkstemp(prefix='.audit-',dir=dest.parent)
    try:
        with os.fdopen(fd,'w',encoding='utf-8') as f:
            f.write(payload); f.flush(); os.fsync(f.fileno())
        # Exclusive atomic publication: existing files are never overwritten.
        os.link(tmp,dest)
    finally:
        os.unlink(tmp)


def export_identity(ids,lineage):
    data=[lineage[i] for i in ids]
    return hashlib.sha256(json.dumps(data,separators=(',',':')).encode()).hexdigest()
