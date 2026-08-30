Preorder App - Multi-file Flask project (JSON 'memory')
-----------------------------------------------------
Structure:
- app/__init__.py        : app factory, register blueprints
- app/auth.py            : auth (register/login/logout)
- app/store.py           : data access layer (JSON files)
- app/routes.py          : main routes (menu, cart, checkout, cafeteria)
- app/admin.py           : admin blueprint (manage items/users/orders)
- run.py                 : run app
- requirements.txt       : python deps
- data/                  : where JSON files will be created at runtime
- templates/             : HTML templates (Jinja2)
- static/                : static files (CSS)

Default admin: admin@example.com / adminpass (created on first run)

To run:
1. pip install -r requirements.txt
2. python run.py
3. Open http://127.0.0.1:5000
