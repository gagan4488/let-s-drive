from flask import Flask, render_template, flash, redirect, url_for, session, request, logging
from flask import Flask, session
import pandas as pd
import pyodbc
import pandas as pd
from wtforms import Form, StringField, TextAreaField, PasswordField, DateTimeField, validators
from functools import wraps
import numpy as np
from datetime import datetime
import time
import base64
import matplotlib
from matplotlib import pyplot as plt
from io import BytesIO

app = Flask(__name__)

conn = pyodbc.connect("Driver={SQL Server Native Client 11.0};"
                      "Server=DESKTOP-4SBKB3C\SQLEXPRESS;"
                      "Database=mydb;"
                      "Trusted_Connection=yes;")

cur = conn.cursor()
print("done")
# mysql = MySQL(app)

FORMAT = '%Y-%m-%d %H:%M:%S'
def check_date(in_date):
    return datetime.now() < in_date

def get_total_rent(s, e):
    print(s)
    start = time.mktime(time.strptime(s, FORMAT))
    end = time.mktime(time.strptime(e, FORMAT))
    return (end - start)/60

class AddTruckForm(Form):
    vin = StringField('VIN', [validators.Length(min=17, max=17)])
    location = StringField('Location', [validators.Length(min=3, max=20)])

class PaymentForm(Form):
    creditCard = StringField('Account Number', [validators.Length(min=16, max=16)])
    billingAddress = StringField('Billing Address', [validators.Length(min=1, max=100)])
    code = StringField('CVV Code', [validators.Length(min=3, max=4)])

class MakeReservationForm(Form):
    fromloc = StringField('From Location', [validators.Length(min=2, max=45)])
    toloc = StringField('To Location', [validators.Length(min=2, max=45)])
    fromdate = StringField('From Date and Time (in yyyy-mm-dd hh:mm:ss)', [validators.Length(min=18, max=20)])
    todate = StringField('To Date and Time (in yyyy-mm-dd hh:mm:ss)', [validators.Length(min=18, max=20)])
    totalrent = StringField('Estimate Total Time Rent (in minute)')

class RegisterForm(Form):
    firstname = StringField('First Name', [validators.Length(min=2, max=45)])
    lastname = StringField('Last Name', [validators.Length(min=2, max=45)])
    email = StringField('Email', [validators.Length(min=6, max=100)])
    username = StringField('Username', [validators.Length(min=2, max=20)])
    password = PasswordField('Password', [validators.DataRequired(), validators.EqualTo('confirm', message='Passwords do not match')])
    confirm = PasswordField('Confirm Password')

def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, Please login', 'danger')
            return redirect(url_for('login'))
    return wrap

@app.route('/admin_dashboard')
def admin_dash():
    sql = " select top 5 (r.fromLocation) ,max(p.amount) AS  Payment from  Reservation as  R,Payment as p where R.reservationID=p.Reservation_reservationID and YEAR(fromDate) <= 2018 group by (r.fromLocation)  order by Payment desc;"
    df = pd.read_sql(sql, conn)
    df_plot = pd.DataFrame({"Payment": df['Payment'].tolist()}, index=df['fromLocation'].tolist())
    plot = df_plot.plot(kind='bar',  title='Top 5 Location').get_figure()
    img = BytesIO()
    plot.savefig(img, format='png')
    img.seek(0)
    buffer = b''.join(img)
    b3 = base64.b64encode(buffer)
    plot5 = b3.decode('utf-8')

    #graph to show users of a car type
    sql1 = "SELECT C.Car_Type, count(R.User_userName) as Total_Users from Reservation as R, Car as C " \
           "where R.Car_VIN= C.VIN " \
           "group by C.Car_Type Order By  count(R.User_userName) DESC;"
    df = pd.read_sql(sql1, conn)
    df_plot = pd.DataFrame({"Total Users": df['Total_Users'].tolist()}, index=df['Car_Type'].tolist())
    plot1 = df_plot.plot(kind='bar').get_figure()
    img = BytesIO()
    plot1.savefig(img, format='png')
    img.seek(0)
    buffer = b''.join(img)
    b1 = base64.b64encode(buffer)
    plot2 = b1.decode('utf-8')

    #top 10 highest amount of payment
    sql2 = "SELECT top 10 Reservation_User_userName AS Username,amount AS '"'Highest Amount'"' " \
                                                                                         "FROM Payment order by amount desc;"
    df = pd.read_sql(sql2, conn)
    df_plot = pd.DataFrame({"Amount": df['Highest Amount'].tolist()}, index=df['Username'].tolist())
    plot3 = df_plot.plot().get_figure()
    img = BytesIO()
    plot3.savefig(img, format='png')
    img.seek(0)
    buffer = b''.join(img)
    b2 = base64.b64encode(buffer)
    plot4 = b2.decode('utf-8')

    # location where type of car not available
    cur = conn.cursor()
    cur.execute("Select Car_Type,Location from Car where isAvailable=0;")
    res = []
    columns = [column[0] for column in cur.description]
    for row in cur.fetchall():
        res.append(dict(zip(columns, row)))
    return render_template('admin_dashboard.html', plot=plot5, plot1=plot2, plot2=plot4, res = res)
    cur.close()

@app.route('/register', methods=['GET', 'POST'])
def register():
    global cur
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        firstname = form.firstname.data
        lastname = form.lastname.data
        email = form.email.data
        username = form.username.data
        password = str(form.password.data)

        cur = conn.cursor()
        cur.execute("""INSERT INTO Customer(email, lastName, firstName) VALUES('{}', '{}', '{}')""".format(email, lastname, firstname))
        cur.execute("""INSERT INTO "User"(userName, password, isVIP, Customer_email) VALUES('{}', '{}', 0, '{}')""".format(username, password, email))
        cur.connection.commit()
        cur.close()
        flash('Your are now registered and can log in', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/add_truck', methods=['GET', 'POST'])
@is_logged_in
def add_truck():
    form = AddTruckForm(request.form)
    if request.method == 'POST':
        if request.form['submit'] == 'Cancel':
            return redirect(url_for('reservation'))
        elif request.form['submit'] == 'Add' and form.validate():
            vin = form.vin.data
            location = form.location.data
            cur = conn.cursor()
            cur.execute("""INSERT INTO Car VALUES('{}', 1, '{}')""".format(vin, location))
            cur.connection.commit()
            return redirect(url_for('truck'))
            cur.close()
    return render_template('add_truck.html', form=form)

@app.route('/logout')
@is_logged_in
def logout():
    session.clear()
    flash('You are now logged out', 'success')
    return redirect(url_for('login'))

# @app.route('/admin_dashboard')
# def admin_dashboard():
#     cur = conn.cursor()


@app.route('/truck')
@is_logged_in
def truck():
    cur = conn.cursor()
    result = cur.execute("""SELECT * FROM Car""")
    res = []
    columns = [column[0] for column in cur.description]
    for row in cur.fetchall():
        res.append(dict(zip(columns, row)))

    if len(res) > 0:
        cur.close()
        # res = cur.fetchall()
        for i in range(len(res)):
            res[i]['rm'], res[i]['isAvailableBool'], res[i]['value'] = ('RESERVED', False, 'btn btn-basic') if res[i]['isAvailable'] == 0 else ('DELETE', True, 'btn btn-danger')
        return render_template('truck.html', truc=res)
    else:
        error = 'No Car found'
        return render_template('truck.html', error=error)

@app.route('/edit_truck/<string:id>', methods=['GET', 'POST'])
@is_logged_in
def edit_truck(id):
    form = AddTruckForm(request.form)
    if request.method == 'POST':
        if request.form['submit'] == 'Cancel':
            return redirect(url_for('truck'))
        elif request.form['submit'] == 'Edit':
            location = form.location.data
            cur = conn.cursor()
            cur.execute("""UPDATE Car SET Location='{}' WHERE VIN='{}'""".format(location, id))
            cur.connection.commit()
            cur.close()
            flash('Truck VIN {} location has been updated to {}'.format(id, location), 'success')
            return redirect(url_for('truck'))

    return render_template('edit_truck.html', form=form)

@app.route('/delete_truck/<string:id>', methods=['POST'])
@is_logged_in
def delete_truck(id):
    if 'DELETE' in id:
        idx = [i for i,a in enumerate(id) if a == '\'']
        vin = id[idx[0]+1:idx[1]]
        cur = conn.cursor()
        cur.execute("""DELETE FROM Truck WHERE VIN='{}'""".format(vin))
        cur.connection.commit()
        cur.close()
        flash('Truck VIN {} Deleted'.format(vin), 'danger')
    return redirect(url_for('truck'))

@app.route('/check_reservation')
@is_logged_in
def check_reservation():
    cur = conn.cursor()
    result = cur.execute("""SELECT * FROM Reservation""")
    res = []
    columns = [column[0] for column in cur.description]
    for row in cur.fetchall():
        res.append(dict(zip(columns, row)))
    if len(res) > 0:
        return render_template('/check_reservation.html', res=res)
    cur.close()
    return render_template('/check_reservation.html')

@app.route('/check_payment')
@is_logged_in
def check_payment():
    cur = conn.cursor()
    result = cur.execute("""SELECT * FROM Payment""")
    res = []
    columns = [column[0] for column in cur.description]
    for row in cur.fetchall():
        res.append(dict(zip(columns, row)))
    if len(res) > 0:
        return render_template('/check_payment.html', trans=res)
    cur.close()
    return render_template('/check_payment.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password_candidate = request.form['password']
        cur = conn.cursor()
        result = cur.execute("""SELECT * FROM "User" WHERE userName='{}'""".format(username))
        res = []
        columns = [column[0] for column in cur.description]
        for row in cur.fetchall():
            res.append(dict(zip(columns, row)))

        if len(res) > 0:
            data = res[0]
            password = data['password']
            isVIP = data['isVIP']
            email = data['Customer_email']

            if password_candidate == password:
                session['logged_in'] = True
                session['username'] = username
                flash("You are now logged in", "success")
                if username == 'admin':
                    session['is_admin'] = True
                    return redirect(url_for('truck'))
                else:
                    session['is_admin'] = False
                    return redirect(url_for('reservation'))
            else:
                error = 'Invalid login'
                return render_template('login.html', error=error)
            cur.close()
        else:
            error = 'Username not found'
            return render_template('login.html', error=error)
    return render_template('login.html')

@app.route('/make_reservation', methods=['GET', 'POST'])
@is_logged_in
def make_reservation():
    form = MakeReservationForm(request.form)
    if request.method == 'POST':
        if request.form['submit'] == 'Cancel':
            return redirect(url_for('reservation'))
        elif request.form['submit'] == 'Proceed' and form.validate():
            fromloc = form.fromloc.data
            toloc = form.toloc.data
            fromdate = form.fromdate.data
            todate = form.todate.data
            # totalrent = int(form.totalrent.data)
            totalrent = get_total_rent(fromdate, todate)
            cur = conn.cursor()
            result = cur.execute("""SELECT * FROM Car WHERE Location='{}' AND isAvailable=1""".format(fromloc))
            res = []
            columns = [column[0] for column in cur.description]
            for row in cur.fetchall():
                res.append(dict(zip(columns, row)))

            if len(res) > 0:
                data = res[0]
                username = session['username']
                vin = data['VIN']
                result = cur.execute("SELECT reservationID FROM Reservation")
                # data = cur.fetchall()
                res = []
                columns = [column[0] for column in cur.description]
                for row in cur.fetchall():
                    res.append(dict(zip(columns, row)))
                n = np.max([int(res[i]['reservationID'][3:]) for i in range(len(res))])
                resID = 'res' + str(n+1)

                session['amount'] = float("{:.2f}".format(totalrent*35.0/30.))
                session['resID'] = resID
                session['vin'] = vin
                session['fromloc'] = fromloc
                session['toloc'] = toloc
                session['fromdate'] = fromdate
                session['todate'] = todate
                session['totalrent'] = totalrent
                return redirect(url_for('payment'))
            else:
                error = 'Car is not available in this location'
                return render_template('make_reservation.html', error=error)
            cur.close()
    return render_template('make_reservation.html', form=form)

@app.route('/payment', methods=['GET', 'POST'])
@is_logged_in
def payment():
    form = PaymentForm(request.form)
    if request.method == 'POST':
        if request.form['submit'] == 'Cancel':
            return redirect(url_for('reservation'))

        elif request.form['submit'] == 'Pay' and form.validate():
            # creditCard = form.creditCard.data
            # billingAddress = form.billingAddress.data
            # code = form.code.data
            payID = 'pay' +str(session['resID'][3:])
            cur = conn.cursor()
            cur.execute("""UPDATE Car SET isAvailable=0 WHERE VIN='{}'""".format(session['vin']))
            cur.execute("""INSERT INTO Reservation(User_userName, Car_VIN, reservationID, fromLocation, toLocation, rentMinutes, fromDate, toDate) VALUES('{}', '{}', '{}', '{}', '{}', {}, '{}', '{}')""".format(session['username'], session['vin'], session['resID'], session['fromloc'], session['toloc'], session['totalrent'], session['fromdate'], session['todate']))
            cur.execute("""INSERT INTO Payment VALUES('{}', '{}', '{}', '{}', {:.2f})""".format(session['username'], session['vin'], session['resID'], payID, session['amount']))

            cur.connection.commit()
            flash('Make Reservation Success', 'success')
            return redirect(url_for('reservation'))

        conn.close()
    return render_template('payment.html', form=form)

@app.route('/transaction')
@is_logged_in
def transaction():
    cur = conn.cursor()
    result = cur.execute("""SELECT * FROM Payment WHERE Reservation_User_userName='{}'""".format(session['username']))
    res = []
    columns = [column[0] for column in cur.description]
    for row in cur.fetchall():
        res.append(dict(zip(columns, row)))

    if len(res) > 0:
        trans = res
        return render_template('transaction.html', trans=trans)
    else:
        error = 'No Transaction found'
        return render_template('transaction.html', error=error)
    cur.close()


@app.route('/reservation')
@is_logged_in
def reservation():
    cur = conn.cursor()
    result = cur.execute("""SELECT * FROM Reservation WHERE User_userName='{}'""".format(session['username']))
    res = []
    columns = [column[0] for column in cur.description]
    for row in cur.fetchall():
        res.append(dict(zip(columns, row)))

    if len(res) > 0:
        for i in range(len(res)):
            res[i]['rm'], res[i]['value'] = ('DELETE', 'btn btn-danger') if check_date(res[i]['fromDate']) else ('DONE', 'btn btn-basic')
        return render_template('reservation.html', res=res)
    else:
        error = 'No Reservation found'
        return render_template('reservation.html', error=error)
    cur.close()

@app.route('/delete_reservation/<string:id>', methods=['POST'])
@is_logged_in
def delete_reservation(id):
    if 'DELETE' in id:
        idx = [i for i,a in enumerate(id) if a == '\'']
        resid = id[idx[0]+1:idx[1]]
        cur = conn.cursor()
        cur.execute("""DELETE FROM Payment WHERE Reservation_reservationID='{}'""".format(resid))
        cur.execute("""DELETE FROM Reservation WHERE reservationID='{}'""".format(resid))
        cur.connection.commit()
        cur.close()
        flash('Reservation ID {} and Payment Deleted'.format(resid), 'danger')
    return redirect(url_for('reservation'))

@app.route('/')
def index():
    cur = conn.cursor()
    result = cur.execute("SELECT * FROM Reservation")
    data = cur.fetchall()
    print(data[1])
    # print(check_date(data[1]['fromDate']))
    cur.close()
    return render_template('home.html')

@app.route('/about')
def about():
    return render_template('about.html')




if __name__ == '__main__':

    app.secret_key = '12'
    app.run(debug=True)

