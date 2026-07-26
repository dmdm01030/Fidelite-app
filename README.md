# Kat Fidelite

Aplikasyon web ki ajoute pwen fidelite pou kliyan yo pou chak acha yo fè.

- **1 pwen pou chak 100 goud** depanse (kalkil otomatik)
- **Espas admin** : kreye kont kliyan, anrejistre acha
- **Espas kliyan** : konekte pou wè pwen ou ak istwa acha ou
- Sèlman admin lan ka kreye kont kliyan (pa gen enskripsyon lib)

## Estrikti pwojè a

```
fidelite-app/
├── app.py
├── requirements.txt
├── static/css/style.css
└── templates/
    ├── base.html
    ├── login.html
    ├── admin_dashboard.html
    ├── new_client.html
    ├── client_detail.html
    └── client_dashboard.html
```

## Enstalasyon lokal (pou teste anvan)

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

Premye fwa ou lanse l, li kreye baz done a (`fidelite.db`) ansanm ak yon
kont admin default:

- **itilizatè** : `admin`
- **modpas** : `changeme123`

⚠️ Chanje modpas sa a imedyatman (nan konsòl Python, oswa ajoute yon
paj pou chanje modpas si w bezwen l pita).

## Deplwaman sou PythonAnywhere

Ou deja gen yon virtualenv konfigire (etap ou fè avan yo). Swiv sa a:

1. **Uploade dosye yo** — nan onglè **Files**, kreye yon dosye
   (egzanp `fidelite-app`) epi telechaje tout fichye yo ladan, oswa
   itilize `git clone` si kòd la sou GitHub.

2. **Aktive virtualenv la epi enstale pakè yo** nan console Bash:
   ```bash
   source /home/myston509/.virtualenvs/monenv/bin/activate
   pip install -r /home/myston509/fidelite-app/requirements.txt
   ```

3. **Modifye fichye WSGI a**
   (`/var/www/myston509_pythonanywhere_com_wsgi.py`) pou l pwente sou
   aplikasyon an:
   ```python
   import sys
   path = '/home/myston509/fidelite-app'
   if path not in sys.path:
       sys.path.insert(0, path)

   from app import app as application
   ```

4. **Verifye chemen Virtualenv la** nan onglè **Web** toujou make
   `/home/myston509/.virtualenvs/monenv`.

5. **Inisyalize baz done a** yon fwa nan console Bash (pou kreye
   `fidelite.db` ak kont admin default la):
   ```bash
   cd /home/myston509/fidelite-app
   python3 -c "from app import init_db; init_db()"
   ```

6. Klike **Reload** nan onglè Web, epi vizite sit ou a.

## Pwochèn etap posib

- Chanje modpas admin default la
- Paj pou admin modifye/efase yon kliyan
- Egzòte istwa acha an CSV
