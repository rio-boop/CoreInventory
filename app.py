from flask import Flask, render_template, request, redirect
import sqlite3

app = Flask(__name__)
import os

if not os.path.exists("database.db"):
    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("""
    CREATE TABLE products(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        category TEXT,
        price REAL,
        stock INTEGER
    )
    """)

    c.execute("""
    CREATE TABLE stock_in(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER,
        quantity INTEGER
    )
    """)

    c.execute("""
    CREATE TABLE stock_out(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER,
        quantity INTEGER
    )
    """)

    conn.commit()
    conn.close()

DATABASE = "database.db"


def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


# ---------------- LOGIN ----------------

@app.route("/")
def login():
    return render_template("login.html")


@app.route("/login", methods=["POST"])
def do_login():
    return redirect("/dashboard")


# ---------------- DASHBOARD ----------------

@app.route("/dashboard")
def dashboard():

    db = get_db()

    total_products = db.execute(
        "SELECT COUNT(*) FROM products"
    ).fetchone()[0]

    total_stock = db.execute(
        "SELECT SUM(stock) FROM products"
    ).fetchone()[0]

    stock_in = db.execute(
        "SELECT SUM(quantity) FROM stock_in"
    ).fetchone()[0]

    stock_out = db.execute(
        "SELECT SUM(quantity) FROM stock_out"
    ).fetchone()[0]

    low_stock = db.execute(
        "SELECT * FROM products WHERE stock <= 5"
    ).fetchall()

    if total_stock is None:
        total_stock = 0

    if stock_in is None:
        stock_in = 0

    if stock_out is None:
        stock_out = 0

    return render_template(
        "dashboard.html",
        total_products=total_products,
        total_stock=total_stock,
        stock_in=stock_in,
        stock_out=stock_out,
        low_stock=low_stock
    )


# ---------------- PRODUCTS ----------------

@app.route("/products")
def products():

    db = get_db()

    search = request.args.get("search")

    if search:
        products = db.execute(
            "SELECT * FROM products WHERE name LIKE ?",
            ('%' + search + '%',)
        ).fetchall()
    else:
        products = db.execute(
            "SELECT * FROM products"
        ).fetchall()

    return render_template(
        "products.html",
        products=products
    )


@app.route("/add_product", methods=["POST"])
def add_product():

    name = request.form["name"]
    category = request.form["category"]
    price = request.form["price"]
    stock = request.form["stock"]

    db = get_db()

    db.execute(
        "INSERT INTO products (name, category, price, stock) VALUES (?,?,?,?)",
        (name, category, price, stock)
    )

    db.commit()

    return redirect("/products")


# ---------------- STOCK IN ----------------

@app.route("/stock_in")
def stock_in():

    db = get_db()

    products = db.execute(
        "SELECT * FROM products"
    ).fetchall()

    return render_template(
        "stock_in.html",
        products=products
    )


@app.route("/add_stock", methods=["POST"])
def add_stock():

    product_id = request.form["product_id"]
    quantity = int(request.form["quantity"])

    db = get_db()

    db.execute(
        "INSERT INTO stock_in (product_id, quantity) VALUES (?,?)",
        (product_id, quantity)
    )

    db.execute(
        "UPDATE products SET stock = stock + ? WHERE id=?",
        (quantity, product_id)
    )

    db.commit()

    return redirect("/products")


# ---------------- STOCK OUT ----------------

@app.route("/stock_out")
def stock_out():

    db = get_db()

    products = db.execute(
        "SELECT * FROM products"
    ).fetchall()

    return render_template(
        "stock_out.html",
        products=products
    )

@app.route("/remove_stock", methods=["POST"])
def remove_stock():

    product_id = request.form["product_id"]
    quantity = int(request.form["quantity"])

    db = get_db()

    product = db.execute(
        "SELECT stock FROM products WHERE id=?",
        (product_id,)
    ).fetchone()

    if product["stock"] < quantity:
        return "Error: Not enough stock available"

    db.execute(
        "INSERT INTO stock_out (product_id, quantity) VALUES (?,?)",
        (product_id, quantity)
    )

    db.execute(
        "UPDATE products SET stock = stock - ? WHERE id=?",
        (quantity, product_id)
    )

    db.commit()

    return redirect("/products")


# ---------------- HISTORY ----------------

@app.route("/history")
def history():

    db = get_db()

    stock_in_data = db.execute("""
    SELECT products.name, stock_in.quantity
    FROM stock_in
    JOIN products ON products.id = stock_in.product_id
    """).fetchall()

    stock_out_data = db.execute("""
    SELECT products.name, stock_out.quantity
    FROM stock_out
    JOIN products ON products.id = stock_out.product_id
    """).fetchall()

    return render_template(
        "history.html",
        stock_in=stock_in_data,
        stock_out=stock_out_data
    )
@app.route("/delete_product/<int:id>")
def delete_product(id):

    db = get_db()

    db.execute(
        "DELETE FROM products WHERE id=?",
        (id,)
    )

    db.commit()

    return redirect("/products")

@app.route("/edit_product/<int:id>")
def edit_product(id):

    db = get_db()

    product = db.execute(
        "SELECT * FROM products WHERE id=?",
        (id,)
    ).fetchone()

    return render_template("edit_product.html", product=product)




# ---------------- RUN APP ----------------

if __name__ == "__main__":
    app.run(debug=True)