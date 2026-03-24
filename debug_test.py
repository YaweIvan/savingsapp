import sys, traceback
sys.stdout.reconfigure(encoding='utf-8')

from app import app
app.config['TESTING'] = True
app.config['PROPAGATE_EXCEPTIONS'] = True

with app.test_client() as c:
    with c.session_transaction() as sess:
        sess['admin'] = 'admin'
    try:
        r = c.get('/admin/dashboard')
        print('STATUS:', r.status_code)
        print(r.data.decode('utf-8', errors='replace'))
    except Exception:
        traceback.print_exc()
