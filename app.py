from flask import Flask, render_template, request, redirect, url_for, flash
from psycopg2 import IntegrityError, Error
from db import get_connection
import os

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev-secret-key")


# -------------------------
# Helper Functions
# -------------------------
def fetch_all(query, params=None):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(query, params or ())
        return cur.fetchall()
    finally:
        cur.close()
        conn.close()


def fetch_one(query, params=None):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(query, params or ())
        return cur.fetchone()
    finally:
        cur.close()
        conn.close()


def execute_query(query, params=None, fetch_returning=False):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(query, params or ())
        result = cur.fetchone() if fetch_returning else None
        conn.commit()
        return result
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()


# -------------------------
# Home
# -------------------------
@app.route("/")
def home():
    stats = {
        "artists": fetch_one("SELECT COUNT(*) AS total FROM Artist")["total"],
        "concerts": fetch_one("SELECT COUNT(*) AS total FROM Concert")["total"],
        "customers": fetch_one("SELECT COUNT(*) AS total FROM Customer")["total"],
        "tickets": fetch_one("SELECT COUNT(*) AS total FROM Ticket")["total"],
    }

    return render_template("home.html", stats=stats)

# -------------------------
# Add Artist
# -------------------------
@app.route("/add_artist", methods=["GET", "POST"])
def add_artist():
    if request.method == "POST":
        artist_name = request.form.get("artist_name", "").strip()
        genre = request.form.get("genre", "").strip()

        if not artist_name or not genre:
            flash("Artist name and genre are required.", "danger")
            return redirect(url_for("add_artist"))

        try:
            execute_query(
                "INSERT INTO Artist (ArtistName, Genre) VALUES (%s, %s)",
                (artist_name, genre),
            )
            flash("Artist added successfully.", "success")
        except Error:
            flash("Unable to add artist. Please try again.", "danger")

        return redirect(url_for("add_artist"))

    return render_template("add_artist.html")


# -------------------------
# Add Customer
# -------------------------
@app.route("/add_customer", methods=["GET", "POST"])
def add_customer():
    if request.method == "POST":
        customer_name = request.form.get("customer_name", "").strip()

        if not customer_name:
            flash("Customer name is required.", "danger")
            return redirect(url_for("add_customer"))

        try:
            execute_query(
                "INSERT INTO Customer (CustomerName) VALUES (%s)",
                (customer_name,),
            )
            flash("Customer added successfully.", "success")
        except Error:
            flash("Unable to add customer. Please try again.", "danger")

        return redirect(url_for("add_customer"))

    return render_template("add_customer.html")


# -------------------------
# Add Concert
# -------------------------
@app.route("/add_concert", methods=["GET", "POST"])
def add_concert():
    artists = fetch_all(
        "SELECT ArtistId AS artistid, ArtistName AS artistname FROM Artist ORDER BY ArtistName"
    )

    if request.method == "POST":
        venue_name = request.form.get("venue_name", "").strip()
        city = request.form.get("city", "").strip()
        concert_date = request.form.get("concert_date", "").strip()
        artist_id = request.form.get("artist_id", "").strip()

        if not artists:
            flash("Please add an artist first before adding a concert.", "danger")
            return redirect(url_for("add_artist"))

        if not venue_name or not city or not concert_date:
            flash("Venue name, city, and concert date are required.", "danger")
            return redirect(url_for("add_concert"))

        if not artist_id:
            flash("Please select an artist.", "danger")
            return redirect(url_for("add_concert"))

        try:
            execute_query(
                """
                INSERT INTO Concert (VenueName, City, ConcertDate, ArtistId)
                VALUES (%s, %s, %s, %s)
                """,
                (venue_name, city, concert_date, artist_id),
            )
            flash("Concert added successfully.", "success")
        except Error:
            flash("Unable to add concert. Please check your input.", "danger")

        return redirect(url_for("add_concert"))

    return render_template("add_concert.html", artists=artists)


# -------------------------
# Add Ticket
# -------------------------
@app.route("/add_ticket", methods=["GET", "POST"])
def add_ticket():
    concerts = fetch_all(
        """
        SELECT
            ConcertId AS concertid,
            VenueName AS venuename,
            City AS city,
            ConcertDate AS concertdate
        FROM Concert
        ORDER BY ConcertDate
        """
    )

    customers = fetch_all(
        """
        SELECT
            CustomerId AS customerid,
            CustomerName AS customername
        FROM Customer
        ORDER BY CustomerName
        """
    )

    if request.method == "POST":
        concert_id = request.form.get("concert_id", "").strip()
        customer_id = request.form.get("customer_id", "").strip()
        order_date = request.form.get("order_date", "").strip()
        payment_method = request.form.get("payment_method", "").strip()
        seat_number = request.form.get("seat_number", "").strip()
        price = request.form.get("price", "").strip()

        if not concerts:
            flash("Please add a concert first before adding a ticket.", "danger")
            return redirect(url_for("add_concert"))

        if not customers:
            flash("Please add a customer first before adding a ticket.", "danger")
            return redirect(url_for("add_customer"))

        if not concert_id or not customer_id or not order_date or not payment_method or not seat_number or not price:
            flash("All ticket fields are required.", "danger")
            return redirect(url_for("add_ticket"))

        try:
            if float(price) <= 0:
                flash("Price must be greater than 0.", "danger")
                return redirect(url_for("add_ticket"))
        except ValueError:
            flash("Please enter a valid ticket price.", "danger")
            return redirect(url_for("add_ticket"))

        conn = get_connection()
        cur = conn.cursor()

        try:
            cur.execute(
                """
                INSERT INTO Orders (CustomerId, OrderDate, PaymentMethod)
                VALUES (%s, %s, %s)
                RETURNING OrderId
                """,
                (customer_id, order_date, payment_method),
            )

            order_row = cur.fetchone()
            order_id = list(order_row.values())[0]

            cur.execute(
                """
                INSERT INTO Ticket (ConcertId, OrderId, SeatNumber, Price)
                VALUES (%s, %s, %s, %s)
                """,
                (concert_id, order_id, seat_number, price),
            )

            conn.commit()
            flash("Ticket purchase added successfully.", "success")

        except IntegrityError:
            conn.rollback()
            flash("That seat is already taken for this concert.", "danger")
        except Error:
            conn.rollback()
            flash("Unable to add ticket purchase. Please try again.", "danger")
        finally:
            cur.close()
            conn.close()

        return redirect(url_for("add_ticket"))

    return render_template("add_ticket.html", concerts=concerts, customers=customers)


# -------------------------
# View Concerts / By City
# -------------------------
@app.route("/view_concerts")
def view_concerts():
    city = request.args.get("city", "").strip()

    cities = fetch_all(
        "SELECT DISTINCT City AS city FROM Concert ORDER BY City"
    )

    if city:
        concerts = fetch_all(
            """
            SELECT
                ConcertId AS concertid,
                VenueName AS venuename,
                City AS city,
                ConcertDate AS concertdate,
                ArtistId AS artistid
            FROM Concert
            WHERE City = %s
            ORDER BY ConcertDate
            """,
            (city,),
        )
    else:
        concerts = fetch_all(
            """
            SELECT
                ConcertId AS concertid,
                VenueName AS venuename,
                City AS city,
                ConcertDate AS concertdate,
                ArtistId AS artistid
            FROM Concert
            ORDER BY ConcertDate
            """
        )

    return render_template(
        "view_concerts.html",
        concerts=concerts,
        cities=cities,
        selected_city=city,
    )


# -------------------------
# Concerts By Artist
# -------------------------
@app.route("/concerts_by_artist")
def concerts_by_artist():
    artist_id = request.args.get("artist_id", "").strip()

    artists = fetch_all(
        "SELECT ArtistId AS artistid, ArtistName AS artistname FROM Artist ORDER BY ArtistName"
    )

    concerts = []
    if artist_id:
        concerts = fetch_all(
            """
            SELECT
                a.ArtistName AS artistname,
                c.VenueName AS venuename,
                c.City AS city,
                c.ConcertDate AS concertdate
            FROM Concert c
            JOIN Artist a ON c.ArtistId = a.ArtistId
            WHERE a.ArtistId = %s
            ORDER BY c.ConcertDate
            """,
            (artist_id,),
        )

    return render_template(
        "concerts_by_artist.html",
        artists=artists,
        concerts=concerts,
        selected_artist=artist_id,
    )


# -------------------------
# Spending By Customer
# -------------------------
@app.route("/spending_by_customer")
def spending_by_customer():
    customer_id = request.args.get("customer_id", "").strip()

    customers = fetch_all(
        "SELECT CustomerId AS customerid, CustomerName AS customername FROM Customer ORDER BY CustomerName"
    )

    if customer_id:
        spending = fetch_all(
            """
            SELECT
                c.CustomerId AS customerid,
                c.CustomerName AS customername,
                COALESCE(SUM(t.Price), 0) AS totalspent
            FROM Customer c
            LEFT JOIN Orders o ON c.CustomerId = o.CustomerId
            LEFT JOIN Ticket t ON o.OrderId = t.OrderId
            WHERE c.CustomerId = %s
            GROUP BY c.CustomerId, c.CustomerName
            ORDER BY c.CustomerName
            """,
            (customer_id,),
        )
    else:
        spending = fetch_all(
            """
            SELECT
                c.CustomerId AS customerid,
                c.CustomerName AS customername,
                COALESCE(SUM(t.Price), 0) AS totalspent
            FROM Customer c
            LEFT JOIN Orders o ON c.CustomerId = o.CustomerId
            LEFT JOIN Ticket t ON o.OrderId = t.OrderId
            GROUP BY c.CustomerId, c.CustomerName
            ORDER BY c.CustomerName
            """
        )

    return render_template(
        "spending_by_customer.html",
        customers=customers,
        spending=spending,
        selected_customer=customer_id,
    )


# -------------------------
# Top 3 Artists
# -------------------------
@app.route("/top_artists")
def top_artists():
    artists = fetch_all(
        """
        SELECT
            a.ArtistName AS artistname,
            COALESCE(SUM(t.Price), 0) AS totalrevenue
        FROM Artist a
        JOIN Concert c ON a.ArtistId = c.ArtistId
        JOIN Ticket t ON c.ConcertId = t.ConcertId
        GROUP BY a.ArtistId, a.ArtistName
        ORDER BY totalrevenue DESC
        LIMIT 3
        """
    )

    return render_template("top_artists.html", artists=artists)


# -------------------------
# Bonus: Customer Order Details
# -------------------------
@app.route("/bonus_orders")
def bonus_orders():
    customer_id = request.args.get("customer_id", "").strip()

    customers = fetch_all(
        "SELECT CustomerId AS customerid, CustomerName AS customername FROM Customer ORDER BY CustomerName"
    )

    orders = []
    if customer_id:
        orders = fetch_all(
            """
            SELECT
                c.CustomerName AS customername,
                o.OrderId AS orderid,
                o.OrderDate AS orderdate,
                o.PaymentMethod AS paymentmethod,
                a.ArtistName AS artistname,
                co.VenueName AS venuename,
                co.City AS city,
                co.ConcertDate AS concertdate,
                t.SeatNumber AS seatnumber,
                t.Price AS price
            FROM Customer c
            JOIN Orders o ON c.CustomerId = o.CustomerId
            JOIN Ticket t ON o.OrderId = t.OrderId
            JOIN Concert co ON t.ConcertId = co.ConcertId
            JOIN Artist a ON co.ArtistId = a.ArtistId
            WHERE c.CustomerId = %s
            ORDER BY o.OrderDate DESC, co.ConcertDate
            """,
            (customer_id,),
        )

    return render_template(
        "bonus_orders.html",
        customers=customers,
        orders=orders,
        selected_customer=customer_id,
    )


if __name__ == "__main__":
    app.run(debug=True)