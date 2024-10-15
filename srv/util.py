def _flatten(d, prefix, glue):
    for k, v in d.items():
        nk = prefix + glue + k if prefix else k
        if isinstance(v, dict):
            yield from flatten(v, nk, glue).items()
        else:
            yield nk, v

def flatten(d, prefix='', glue='.'):
    return dict(_flatten(d, prefix, glue))

def remap(d, md):
    return {
        md[k] if k in md else k: v
        for k, v in d.items()
    }
