import time

from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, Response
from flask_mysqldb import MySQL
from werkzeug.utils import redirect
import MySQLdb.cursors
import re
from datetime import date, timedelta, datetime
from fpdf import FPDF

app = Flask(__name__)

# Change this to your secret key (can be anything, it's for extra protection)
app.secret_key = 'your secret key'

# Enter your database connection details below
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'ashy2000'
app.config['MYSQL_DB'] = 'bloodmanagement'

# Intialize MySQL
mysql = MySQL(app)


@app.route('/')
def index():
    return render_template('home.html')


# Function to retrieve the count of A+ blood type from the database
def get_a_positive_count_from_database():
    # Establish a connection to the database
    cur = mysql.connection.cursor()

    # Execute a query to retrieve the count of A+ blood type
    cur.execute("SELECT COUNT(*) FROM blood WHERE Bloodtype = 'A+'")
    result = cur.fetchone()

    # Close the database connection
    cur.close()

    # Return the count of A+ blood type
    return result[0]


@app.route('/bloodbank/')
def bloodbank():
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT COUNT(*) FROM donor")
    data = cursor.fetchone()[0]  # Fetch the count value directly

    # TOTAL BLOOD
    cursor.execute("SELECT COUNT(*) FROM blood")
    total_count = cursor.fetchone()[0]
    cursor.execute("SELECT name FROM bloodtype")
    bloodtypes = [item[0] for item in cursor.fetchall()]
    print(bloodtypes)
    cursor.execute("SELECT Bloodtype FROM blood")
    blooddatas = [item[0] for item in cursor.fetchall()]
    blood_dicts = {}
    for i in bloodtypes:
        blood_dicts[i] = blooddatas.count(i)
    print(blood_dicts)
    cursor.close()

    return render_template('bloodbank.html',
                           blood_dicts=blood_dicts,
                           bloodtypes=bloodtypes,
                           data=data,
                           total_count=len(blooddatas))


@app.route('/request1/')
def request1():
    return render_template('request.html')


@app.route('/report/')
def report():
    return render_template('Report.html')


@app.route('/donate/')
def donate():
    return render_template('donate.html')


@app.route('/admin/')
def admin():
    return render_template('admin.html')


@app.route('/patient/')
def patient():
    return render_template('patient.html')


@app.route('/thank/')
def thank():
    return render_template('thankyou.html')


# http://localhost:5000/pythonlogin/ - the following will be our login page, which will use both GET and POST requests
@app.route('/pythonlogin/', methods=['GET', 'POST'])
def login():
    # Output message if something goes wrong...
    msg = ''
    # Check if "username" and "password" POST requests exist (user submitted form)
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        # Create variables for easy access
        username = request.form['username']
        password = request.form['password']
        # Check if account exists using MySQL
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts WHERE username = %s AND password = %s', (username, password,))
        # Fetch one record and return result
        account = cursor.fetchone()

        # If account exists in accounts table in out database
        if account:
            # Create session data, we can access this data in other routes
            session['loggedin'] = True
            session['id'] = account['id']
            session['username'] = account['username']
            # Redirect to home page
            return redirect(url_for('admin'))
        else:
            # Account doesn't exist or username/password incorrect
            msg = 'Incorrect username/password!'
    return render_template('login.html', msg='')


# http://localhost:5000/python/logout - this will be the logout page
@app.route('/pythonlogin/logout')
def logout():
    # Remove session data, this will log the user out
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)
    # Redirect to login page
    return redirect(url_for('login'))


# http://localhost:5000/pythinlogin/register - this will be the registration page, we need to use both GET and POST requests
@app.route('/pythonlogin/register', methods=['GET', 'POST'])
def register():
    # Output message if something goes wrong...
    msg = ''
    # Check if "username", "password" and "email" POST requests exist (user submitted form)
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form:
        # Create variables for easy access
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        # Check if account exists using MySQL
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts WHERE username = %s', (username,))
        account = cursor.fetchone()
        # If account exists show error and validation checks
        if account:
            msg = 'Account already exists!'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Invalid email address!'
        elif not re.match(r'[A-Za-z0-9]+', username):
            msg = 'Username must contain only characters and numbers!'
        elif not username or not password or not email:
            msg = 'Please fill out the form!'
        else:
            # Account doesn't exist and the form data is valid, now insert new account into accounts table
            cursor.execute('INSERT INTO accounts VALUES (NULL, %s, %s, %s)', (username, password, email,))
            mysql.connection.commit()
            msg = 'You have successfully registered!'
    elif request.method == 'POST':
        # Form is empty... (no POST data)
        msg = 'Please fill out the form!'
    # Show registration form with message (if any)
    return render_template('login.html', msg=msg)


# http://localhost:5000/pythinlogin/home - this will be the home page, only accessible for loggedin users
@app.route('/pythonlogin/home')
def home():
    # Check if user is loggedin
    if 'loggedin' in session:
        # User is loggedin show them the home page
        return render_template('admin.html', username=session['username'])
    # User is not loggedin redirect to login page
    return redirect(url_for('login'))


# http://localhost:5000/pythinlogin/profile - this will be the profile page, only accessible for loggedin users
@app.route('/pythonlogin/profile')
def profile():
    # Check if user is loggedin
    if 'loggedin' in session:
        # We need all the account info for the user, so we can display it on the profile page
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts WHERE id = %s', (session['id'],))
        account = cursor.fetchone()
        # Show the profile page with account info
        return render_template('profile.html', account=account)
    # User is not loggedin redirect to login page
    return redirect(url_for('login'))


@app.route('/manage/')
def manage():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    cursor.execute('SELECT * FROM donor')
    data = cursor.fetchall()

    cursor.close()
    return render_template('donorlog.html', donor=data)


@app.route('/pmanage/')
def pmanage():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    cursor.execute('SELECT * FROM requestblood')
    data = cursor.fetchall()

    cursor.close()
    return render_template('patientlog.html', patient=data)


@app.route('/donorlog/')
def donorlog():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    cursor.execute('SELECT * FROM donorlog')
    data = cursor.fetchall()

    cursor.close()
    return render_template('donor.html', donorlog=data)


@app.route('/patientlog/')
def patientlog():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    cursor.execute('SELECT * FROM requestlog')
    data = cursor.fetchall()

    cursor.close()
    return render_template('patient.html', patientlog=data)


@app.route('/add_donor', methods=['POST'])
def add_donor():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    if request.method == 'POST':
        fullname = request.form['fullname']
        age = request.form['age']
        gender = request.form['gender']
        address = request.form['address']
        phone = request.form['phone']
        email = request.form['email']
        bloodtype = request.form['bloodtype']
        ddate = request.form['registeredAt']
        cursor.execute(
            "INSERT INTO donor (name, age, gender, address, email, phone, bloodtype, registeredAt) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
            (fullname, age, gender, address, email, phone, bloodtype, ddate))
        mysql.connection.commit()
        flash('Donor Added successfully')
        return redirect(url_for('manage'))


@app.route('/add_donor1/', methods=['POST'])
def add_donor1():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    if request.method == 'POST':
        name = request.form['name']
        age1 = request.form['age1']
        gender = request.form['gender']
        address1 = request.form['address1']
        phone1 = request.form['phone1']
        email1 = request.form['email1']
        bloodtype1 = request.form['bloodtype1']
        ddate1 = request.form['ddate1']
        cursor.execute(
            "INSERT INTO donor (name, age, gender, address, email, phone, bloodtype, registeredAt) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
            (name, age1, gender, address1, email1, phone1, bloodtype1, ddate1))
        mysql.connection.commit()
        flash('Donor Added successfully')
        return redirect(url_for('thank'))


@app.route('/add_patient/', methods=['POST'])
def add_patient():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    if request.method == 'POST':
        pname = request.form['pname']
        page = request.form['page']
        pbloodtype = request.form['pbloodtype']
        units = request.form['units']
        hospital = request.form['hospital']
        pphone = request.form['pphone']
        cursor.execute(
            "INSERT INTO requestblood (fullname, age, bloodtype, units, hospital, phone) VALUES (%s,%s,%s,%s,%s,%s)",
            (pname, page, pbloodtype, units, hospital, pphone))
        mysql.connection.commit()
        flash('Patient Added successfully')
        return redirect(url_for('pmanage'))


@app.route('/add_patient1/', methods=['POST'])
def add_patient1():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    if request.method == 'POST':
        pname = request.form['pname']
        page = request.form['page']
        pbloodtype = request.form['pbloodtype']
        units = request.form['units']
        hospital = request.form['hospital']
        pphone = request.form['pphone']
        cursor.execute(
            "INSERT INTO requestblood (fullname, age, bloodtype, units, hospital, phone) VALUES (%s,%s,%s,%s,%s,%s)",
            (pname, page, pbloodtype, units, hospital, pphone))
        mysql.connection.commit()
        flash('Patient Added successfully')
        return redirect(url_for('thank'))


@app.route('/edit/<id>', methods=['POST', 'GET'])
def get_donor(id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM donor WHERE id = %s', (id,))
    data = cursor.fetchall()
    cursor.close()
    print(data[0])
    return render_template('edit.html', donor=data[0])


@app.route('/edit1/<id>', methods=['POST', 'GET'])
def get_patient(id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM requestblood WHERE id = %s', (id,))
    requestBloodData = cursor.fetchone()
    today = date.today()
    print(requestBloodData)
    sql = "SELECT * FROM blood WHERE bloodtype = %s AND Expirationdate >= %s"
    blood = (str(requestBloodData['bloodtype']), today)
    cursor.execute(sql, blood)
    bloodData = cursor.fetchone()
    if bloodData is None:
        return render_template('error.html', message="No Blood Available!")
    cursor.execute("DELETE FROM blood WHERE BloodID = %s", (bloodData['BloodID'],))
    mysql.connection.commit()
    print(bloodData)
    cursor.execute(
        "INSERT INTO requestlog (fullname, age, bloodtype,units,hospital,phone,Status) VALUES (%s, %s, %s,%s, %s, %s, %s)",
        (
            requestBloodData['fullname'], requestBloodData['age'], requestBloodData['bloodtype'],
            requestBloodData['units'],
            requestBloodData['hospital'], requestBloodData['phone'], 'ACCEPTED!'))
    mysql.connection.commit()  # Use commit() instead of cursor.commit()
    cursor.execute('DELETE FROM requestblood WHERE id = %s', (id,))
    mysql.connection.commit()
    # print(requestBloodData)
    return redirect(url_for('patientlog'))


@app.route('/update2/<donor_id>', methods=['GET', 'POST'])
def edit_donor(donor_id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    if request.method == 'POST':
        print(donor_id)
        bloodtype = request.form['bloodtype']
        ddate = datetime.strptime(request.form['date'], "%Y-%m-%d")
        cursor.execute("INSERT INTO donorlog (donorId, bloodtype, ddate) VALUES (%s, %s, %s)",
                       (donor_id, bloodtype, ddate.date()))
        mysql.connection.commit()  # Use commit() instead of cursor.commit()
        expiration_date = ddate + timedelta(days=30)
        cursor.execute("INSERT INTO blood (donorId, bloodtype, Expirationdate, Dateextracted) VALUES (%s, %s, %s, %s)",
                       (donor_id, bloodtype, expiration_date.date(), ddate.date()))
        mysql.connection.commit()  # Use commit() instead of cursor.commit()
        print(ddate)
        print(ddate + timedelta(days=30))
        return redirect(url_for('donorlog'))
    else:
        cursor.execute("SELECT donorId, bloodtype, ddate FROM donorlog WHERE id = %s", (donor_id,))
        donor = cursor.fetchone()
        return render_template('edit2.html', donor=donor)


@app.route('/edit2/<id>', methods=['POST', 'GET'])
def get_donor2(id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT id, name, bloodtype FROM donor WHERE id = %s', (id,))
    data = cursor.fetchall()
    cursor.close()
    print(data[0])
    today = date.today()
    return render_template('edit2.html', donor=data[0], today=today)


@app.route('/update1/<id>', methods=['POST'])
def update_patient(id):
    if request.method == 'POST':
        pname = request.form['pname']
        page = request.form['page']
        pbloodtype = request.form['pbloodtype']
        units = request.form['units']
        hospital = request.form['hospital']
        pphone = request.form['pphone']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("""
                UPDATE requestblood
                SET fullname = %s,
                    age = %s,
                    bloodtype = %s,
                    units = %s,
                    hospital = %s,
                    phone = %s
                WHERE id = %s
            """, (pname, page, pbloodtype, units, hospital, pphone, id))
        flash('Patient Updated Successfully')
        mysql.connection.commit()
        return redirect(url_for('pmanage'))


@app.route('/update/<id>', methods=['POST'])
def update_donor(id):
    if request.method == 'POST':
        fullname = request.form['fullname']
        age = request.form['age']
        address = request.form['address']
        phone = request.form['phone']
        email = request.form['email']
        bloodtype = request.form['bloodtype']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("""
                UPDATE donor
                SET name = %s,
                    age = %s,
                    address = %s,
                    email = %s,
                    phone = %s,
                    Bloodtype = %s
                WHERE id = %s
            """, (fullname, age, address, email, phone, bloodtype, id))
        flash('Donor Updated Successfully')
        mysql.connection.commit()
        return redirect(url_for('manage'))


@app.route('/delete1/<string:id>', methods=['POST', 'GET'])
def delete_patient(id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM requestblood WHERE id = %s', (id,))
    requestBloodData = cursor.fetchone()
    today = date.today()
    cursor.execute(
        "INSERT INTO requestlog (fullname, age, bloodtype,units,hospital,phone,Status) VALUES (%s, %s, %s,%s, %s, %s, %s)",
        (
            requestBloodData['fullname'], requestBloodData['age'], requestBloodData['bloodtype'],
            requestBloodData['units'],
            requestBloodData['hospital'], requestBloodData['phone'], 'REJECTED!'))
    mysql.connection.commit()  # Use commit() instead of cursor.commit()
    cursor.execute('DELETE FROM requestblood WHERE id = %s', (id,))
    mysql.connection.commit()
    # print(requestBloodData)
    return redirect(url_for('patientlog'))


@app.route('/delete/<string:id>', methods=['POST', 'GET'])
def delete_donor(id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('DELETE FROM donor WHERE id = {0}'.format(id))
    mysql.connection.commit()
    flash('Donor Removed Successfully')
    return redirect(url_for('manage'))


@app.route('/data-age', methods=['GET'])
def age():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT age FROM donor')
    ages = cursor.fetchall()
    data_dicts = {}
    for age in ages:
        if int(age['age']) in data_dicts:
            data_dicts[int(age['age'])] += 1
        else:
            data_dicts[int(age['age'])] = 1
    return jsonify(data_dicts)


@app.route('/data-gender', methods=['GET'])
def gender():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT gender FROM donor')
    ggender = cursor.fetchall()
    data_dicts = {}
    for gender in ggender:
        if (gender['gender']) in data_dicts:
            data_dicts[(gender['gender'])] += 1
        else:
            data_dicts[(gender['gender'])] = 1
    return jsonify(data_dicts)


@app.route('/data-registeredAt', methods=['GET'])
def registeredat():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT registeredAt FROM donor')
    ddate = cursor.fetchall()
    data_dicts = {}
    for registeredAt in ddate:
        if (registeredAt['registeredAt']) in data_dicts:
            data_dicts[(registeredAt['registeredAt'])] += 1
        else:
            data_dicts[(registeredAt['registeredAt'])] = 1
    return jsonify(data_dicts)


@app.route('/data-addressbar', methods=['GET'])
def addressbar():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT address FROM donor')
    addr = cursor.fetchall()
    data_dicts = {}
    for addressbar in addr:
        if (addressbar['address']) in data_dicts:
            data_dicts[(addressbar['address'])] += 1
        else:
            data_dicts[(addressbar['address'])] = 1
    return jsonify(data_dicts)


@app.route('/data-totaldonor', methods=['GET'])
def totaldonor():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT registeredAt FROM donor')
    dnr = cursor.fetchall()
    data_dicts = {}
    for totaldonor in dnr:
        if (totaldonor['registeredAt']) in data_dicts:
            data_dicts[(totaldonor['registeredAt'])] += 1
        else:
            data_dicts[(totaldonor['registeredAt'])] = 1
    return jsonify(data_dicts)


@app.route('/data-blood', methods=['GET'])
def numblood():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT bloodtype FROM blood')
    bbd = cursor.fetchall()
    data_dicts = {}
    for numblood in bbd:
        if (numblood['bloodtype']) in data_dicts:
            data_dicts[(numblood['bloodtype'])] += 1
        else:
            data_dicts[(numblood['bloodtype'])] = 1
    return jsonify(data_dicts)


@app.route('/download/report/pdf')
def download_report():
    cursor = None
    try:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT * FROM donor")
        result = cursor.fetchall()

        pdf = FPDF()
        pdf.add_page()

        page_width = pdf.w - 2 * pdf.l_margin

        pdf.set_font('Times', 'B', 14.0)
        pdf.cell(page_width, 0.0, 'Donor Data', align='C')
        pdf.ln(10)

        pdf.set_font('Courier', 'B', 7)  # Adjust font size and style for header

        col_width_id = page_width / 12  # Adjust width for ID column
        col_width_name = page_width / 7  # Adjust width for Name column
        col_width_age = page_width / 18  # Adjust width for Age column
        col_width_gender = page_width / 18  # Adjust width for Gender column

        col_width = (page_width - col_width_id - col_width_name - col_width_age - col_width_gender) / 5  # Adjust width for remaining columns

        pdf.ln(1)

        th = pdf.font_size

        # Add header with text
        pdf.cell(col_width_id, th, 'ID', border=1)
        pdf.cell(col_width_name, th, 'Name', border=1)
        pdf.cell(col_width_age, th, 'Age', border=1)
        pdf.cell(col_width_gender, th, 'Gender', border=1)
        pdf.cell(col_width, th, 'Address', border=1)
        pdf.cell(col_width, th, 'Email', border=1)
        pdf.cell(col_width, th, 'Phone', border=1)
        pdf.cell(col_width, th, 'Blood Type', border=1)
        pdf.cell(col_width, th, 'Registered At', border=1)
        pdf.ln(th)

        pdf.set_font('Courier', '', 6)  # Reset font size for content

        for row in result:
            pdf.cell(col_width_id, th, str(row['id']), border=1)

            # Adjust font size for specific columns
            pdf.set_font('Courier', '', 6)
            pdf.cell(col_width_name, th, row['name'], border=1)

            pdf.set_font('Courier', '', 6)  # Reset font size for subsequent columns
            pdf.cell(col_width_age, th, str(row['age']), border=1)
            pdf.cell(col_width_gender, th, row['gender'], border=1)

            # Adjust font size for specific columns
            pdf.set_font('Courier', '', 4)
            pdf.cell(col_width, th, row['address'], border=1)
            pdf.cell(col_width, th, row['email'], border=1)

            pdf.set_font('Courier', '', 6)  # Reset font size for subsequent columns
            pdf.cell(col_width, th, row['phone'], border=1)
            pdf.cell(col_width, th, row['bloodtype'], border=1)
            pdf.cell(col_width, th, row['registeredAt'], border=1)
            pdf.ln(th)

        pdf.ln(10)

        pdf.set_font('Times', '', 10.0)
        pdf.cell(page_width, 0.0, '- end of report -', align='C')

        return Response(pdf.output(dest='S').encode('latin-1'), mimetype='application/pdf',
                        headers={'Content-Disposition': 'attachment;filename=donor_report.pdf'})
    except Exception as e:
        print(e)
    finally:
        if cursor is not None:
            cursor.close()


@app.route('/download_report1')
def download_report1():
    cursor = None
    try:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT * FROM blood")
        result = cursor.fetchall()

        pdf = FPDF()
        pdf.add_page()

        page_width = pdf.w - 2 * pdf.l_margin

        pdf.set_font('Times', 'B', 14.0)
        pdf.cell(page_width, 0.0, 'Blood Data', align='C')
        pdf.ln(10)

        pdf.set_font('Courier', '', 12)

        col_width = page_width / 5

        pdf.ln(1)

        th = pdf.font_size

        # Add header with text
        pdf.cell(col_width, th, 'ID', border=1)
        pdf.cell(col_width, th, 'DonorID', border=1)
        pdf.cell(col_width, th, 'BloodType', border=1)
        pdf.cell(col_width, th, 'ExpirationDate', border=1)
        pdf.cell(col_width, th, 'DateExtracted', border=1)
        pdf.ln(th)

        pdf.set_font('Courier', '', 12)

        for row in result:
            pdf.cell(col_width, th, str(row['BloodID']), border=1)
            pdf.cell(col_width, th, str(row['donorId']), border=1)
            pdf.cell(col_width, th, row['bloodtype'], border=1)
            pdf.cell(col_width, th, str(row['Expirationdate']), border=1)
            pdf.cell(col_width, th, str(row['Dateextracted']), border=1)
            pdf.ln(th)

        pdf.ln(10)

        pdf.set_font('Times', '', 10.0)
        pdf.cell(page_width, 0.0, '- end of report -', align='C')

        return Response(pdf.output(dest='S').encode('latin-1'), mimetype='application/pdf',
                        headers={'Content-Disposition': 'attachment;filename=blood_report.pdf'})
    except Exception as e:
        print(e)
    finally:
        if cursor is not None:  # Check if cursor is not None before closing
            cursor.close()

@app.route('/download_report2')
def download_report2():
    cursor = None
    try:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT * FROM requestlog")
        result = cursor.fetchall()

        pdf = FPDF()
        pdf.add_page()

        page_width = pdf.w - 2 * pdf.l_margin

        pdf.set_font('Times', 'B', 14.0)
        pdf.cell(page_width, 0.0, 'Patient Data', align='C')
        pdf.ln(10)

        pdf.set_font('Courier', '', 10)

        col_width = page_width / 8

        pdf.ln(1)

        th = pdf.font_size

        # Add header with text
        pdf.cell(col_width, th, 'ID', border=1)
        pdf.cell(col_width, th, 'Full Name', border=1)
        pdf.cell(col_width, th, 'Age', border=1)
        pdf.cell(col_width, th, 'BloodType', border=1)
        pdf.cell(col_width, th, 'Units', border=1)
        pdf.cell(col_width, th, 'Hospital', border=1)
        pdf.cell(col_width, th, 'Phone', border=1)
        pdf.cell(col_width, th, 'Status', border=1)
        pdf.ln(th)

        pdf.set_font('Courier', '', 10)

        for row in result:
            pdf.cell(col_width, th, str(row['id']), border=1)
            pdf.cell(col_width, th, row['fullname'], border=1)
            pdf.cell(col_width, th, row['age'], border=1)
            pdf.cell(col_width, th, row['bloodtype'], border=1)
            pdf.cell(col_width, th, str(row['units']), border=1)
            pdf.cell(col_width, th, row['hospital'], border=1)
            pdf.cell(col_width, th, str(row['phone']), border=1)
            pdf.cell(col_width, th, row['Status'], border=1)
            pdf.ln(th)

        pdf.ln(10)

        pdf.set_font('Times', '', 10.0)
        pdf.cell(page_width, 0.0, '- end of report -', align='C')

        return Response(pdf.output(dest='S').encode('latin-1'), mimetype='application/pdf',
                        headers={'Content-Disposition': 'attachment;filename=patient_report.pdf'})
    except Exception as e:
        print(e)
    finally:
        if cursor is not None:  # Check if cursor is not None before closing
            cursor.close()


if __name__ == '__main__':
    app.run(debug=True)
