import os
from datetime import datetime

from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager, UserMixin, login_user, login_required,
    logout_user, current_user
)
from werkzeug.security import generate_password_hash, check_password_hash

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "chanje-sa-a-nan-pwodiksyon")
# Kote baz done a rete: si Railway gen yon Volume monte sou /data, itilize l
# (done yo ap rete la atravè chak deplwaman). Sinon, itilize dosye pwojè a
# (itil pou tès lokal, men done yo ap efase chak redeploy sou Railway).
DATA_DIR = "/data" if os.path.isdir("/data") else basedir
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(DATA_DIR, "fidelite.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Konbyen goud pou 1 pwen
GOURDES_PA_PWEN = 100

db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"
login_manager.login_message = "Tanpri konekte pou kontinye."


# ---------------------------------------------------------------------------
# Modèl
# ---------------------------------------------------------------------------
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(30), unique=True, nullable=True)
    role = db.Column(db.String(20), nullable=False, default="client")  # 'admin' oswa 'client'
    points = db.Column(db.Integer, nullable=False, default=0)

    purchases = db.relationship(
        "Purchase", backref="client", lazy=True,
        foreign_keys="Purchase.client_id"
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Purchase(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    amount_gourdes = db.Column(db.Float, nullable=False)
    points_earned = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ---------------------------------------------------------------------------
# Woutaj / Routes
# ---------------------------------------------------------------------------
@app.route("/")
def index():
    if current_user.is_authenticated:
        if current_user.role == "admin":
            return redirect(url_for("admin_dashboard"))
        return redirect(url_for("client_dashboard"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for("index"))

        flash("Non itilizatè oswa modpas pa kòrèk.", "error")

    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))


# ---- Espas Admin ----------------------------------------------------------
@app.route("/admin")
@login_required
def admin_dashboard():
    if current_user.role != "admin":
        return redirect(url_for("client_dashboard"))

    clients = User.query.filter_by(role="client").order_by(User.full_name).all()
    return render_template("admin_dashboard.html", clients=clients)


@app.route("/admin/kliyan/nouvo", methods=["GET", "POST"])
@login_required
def new_client():
    if current_user.role != "admin":
        return redirect(url_for("client_dashboard"))

    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        phone = request.form.get("phone", "").strip() or None

        if not full_name or not username or not password:
            flash("Tanpri ranpli tout chan yo.", "error")
        elif User.query.filter_by(username=username).first():
            flash("Non itilizatè sa a deja pran.", "error")
        elif phone and User.query.filter_by(phone=phone).first():
            flash("Nimewo telefòn sa a deja itilize pou yon lòt kliyan.", "error")
        else:
            client = User(
                full_name=full_name,
                username=username,
                role="client",
                points=0,
                phone=phone,
            )
            client.set_password(password)
            db.session.add(client)
            db.session.commit()
            flash(f"Kont pou {full_name} kreye ak siksè.", "success")
            return redirect(url_for("admin_dashboard"))

    return render_template("new_client.html")


@app.route("/admin/kliyan/<int:client_id>/modifye", methods=["GET", "POST"])
@login_required
def edit_client(client_id):
    if current_user.role != "admin":
        return redirect(url_for("client_dashboard"))

    client = User.query.get_or_404(client_id)

    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        phone = request.form.get("phone", "").strip() or None

        existing = User.query.filter_by(phone=phone).first() if phone else None

        if not full_name:
            flash("Non konplè a obligatwa.", "error")
        elif existing and existing.id != client.id:
            flash("Nimewo telefòn sa a deja itilize pou yon lòt kliyan.", "error")
        else:
            client.full_name = full_name
            client.phone = phone
            db.session.commit()
            flash("Enfòmasyon kliyan an mete ajou.", "success")
            return redirect(url_for("client_detail", client_id=client.id))

    return render_template("edit_client.html", client=client)


@app.route("/admin/kliyan/<int:client_id>")
@login_required
def client_detail(client_id):
    if current_user.role != "admin":
        return redirect(url_for("client_dashboard"))

    client = User.query.get_or_404(client_id)
    purchases = (
        Purchase.query.filter_by(client_id=client.id)
        .order_by(Purchase.created_at.desc())
        .all()
    )
    return render_template(
        "client_detail.html",
        client=client,
        purchases=purchases,
        gourdes_pa_pwen=GOURDES_PA_PWEN,
    )


@app.route("/admin/kliyan/<int:client_id>/acha", methods=["POST"])
@login_required
def add_purchase(client_id):
    if current_user.role != "admin":
        return redirect(url_for("client_dashboard"))

    client = User.query.get_or_404(client_id)

    try:
        amount = float(request.form.get("amount", 0))
    except ValueError:
        amount = 0

    if amount <= 0:
        flash("Antre yon montan valab.", "error")
        return redirect(url_for("client_detail", client_id=client.id))

    points_earned = int(amount // GOURDES_PA_PWEN)

    purchase = Purchase(
        client_id=client.id,
        amount_gourdes=amount,
        points_earned=points_earned,
    )
    client.points += points_earned

    db.session.add(purchase)
    db.session.commit()

    flash(f"Acha anrejistre : {points_earned} pwen ajoute pou {client.full_name}.", "success")
    return redirect(url_for("client_detail", client_id=client.id))


# ---- Espas Kliyan ----------------------------------------------------------
@app.route("/mwen")
@login_required
def client_dashboard():
    if current_user.role != "client":
        return redirect(url_for("admin_dashboard"))

    purchases = (
        Purchase.query.filter_by(client_id=current_user.id)
        .order_by(Purchase.created_at.desc())
        .all()
    )
    return render_template(
        "client_dashboard.html",
        purchases=purchases,
        gourdes_pa_pwen=GOURDES_PA_PWEN,
    )


@app.route("/chanje-modpas", methods=["GET", "POST"])
@login_required
def change_password():
    if request.method == "POST":
        current_password = request.form.get("current_password", "")
        new_password = request.form.get("new_password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not current_user.check_password(current_password):
            flash("Modpas aktyèl la pa kòrèk.", "error")
        elif len(new_password) < 6:
            flash("Nouvo modpas la dwe gen omwen 6 karaktè.", "error")
        elif new_password != confirm_password:
            flash("Nouvo modpas yo pa menm.", "error")
        else:
            current_user.set_password(new_password)
            db.session.commit()
            flash("Modpas ou chanje ak siksè.", "success")
            return redirect(url_for("index"))

    return render_template("change_password.html")


@app.route("/verifye-pwen", methods=["GET", "POST"])
def verify_points():
    result = None
    searched = False

    if request.method == "POST":
        searched = True
        phone = request.form.get("phone", "").strip()
        if phone:
            result = User.query.filter_by(role="client", phone=phone).first()

    return render_template("verify_points.html", result=result, searched=searched)


# ---------------------------------------------------------------------------
# Inisyalizasyon baz done + premye kont admin
# ---------------------------------------------------------------------------
def init_db():
    with app.app_context():
        db.create_all()

        # Ti migrasyon: ajoute kolòn 'phone' si baz done a te kreye anvan
        # fonksyonalite sa a (san efase done ki deja la yo).
        with db.engine.connect() as conn:
            columns = [row[1] for row in conn.exec_driver_sql("PRAGMA table_info(user)")]
            if "phone" not in columns:
                conn.exec_driver_sql("ALTER TABLE user ADD COLUMN phone VARCHAR(30)")
                conn.commit()

        if not User.query.filter_by(role="admin").first():
            admin = User(
                full_name="Admin",
                username="admin",
                role="admin",
                points=0,
            )
            admin.set_password("changeme123")
            db.session.add(admin)
            db.session.commit()
            print("Kont admin kreye -> itilizatè: admin | modpas: changeme123")
            print("!! Chanje modpas sa a imedyatman apre premye koneksyon !!")


# Inisyalize baz done a nenpòt jan aplikasyon an lanse (Flask dev server
# oswa gunicorn sou Render).
init_db()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 3000))
    app.run(host="0.0.0.0", port=port)
