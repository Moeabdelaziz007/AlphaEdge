"""Auth hooks scaffold."""

def before_auth_request(request):
    request.setdefault('context', {})
    request['context']['trace_id'] = request.get('trace_id', 'auto-trace')
    return request

def after_auth_success(user, token):
    return {'user_id': user.get('id'), 'token': token, 'status': 'issued'}
