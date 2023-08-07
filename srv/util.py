def _flatten(d, pk, sep):
    for k, v in d.items():
        nk = pk + sep + k if pk else k
        if isinstance(v, dict):
            yield from flatten(v, nk, sep).items()
        else:
            yield nk, v

def flatten(d, pk='', sep='.'):
    return dict(_flatten(d, pk, sep))

def remap(d, md):
    return {
        md[k] if k in md else k: v
        for k, v in d.items()
    }
