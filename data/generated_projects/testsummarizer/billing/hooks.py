"""Billing hooks scaffold."""

def on_checkout_created(payload):
    return {'event': 'checkout_created', 'subscription_id': payload.get('subscription_id')}

def on_invoice_paid(payload):
    return {'event': 'invoice_paid', 'tenant_id': payload.get('tenant_id')}
