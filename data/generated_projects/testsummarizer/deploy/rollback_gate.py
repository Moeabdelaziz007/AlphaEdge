import os
import json

def run_rollback_if_needed():
    health_status = os.getenv('DEPLOY_HEALTH', 'ok').lower()
    report = {'health': health_status, 'rollback_triggered': health_status != 'ok'}
    with open('deploy/rollback_report.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    if health_status != 'ok':
        raise SystemExit('Deploy health check failed; rollback gate activated.')

if __name__ == '__main__':
    run_rollback_if_needed()
