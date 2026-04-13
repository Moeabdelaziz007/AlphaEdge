"""Observability scaffold."""

def emit_metric(name, value, tags=None):
    return {'metric': name, 'value': value, 'tags': tags or {}}

def emit_health(service, ok=True):
    return {'service': service, 'status': 'ok' if ok else 'failed'}
