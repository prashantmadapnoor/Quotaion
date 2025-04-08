from flask import Flask,flash, render_template, request, redirect, url_for, session,jsonify, send_file,send_from_directory
from flask_mysqldb import MySQL
from main import app
import json
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import re
import random
from fpdf import FPDF
import MySQLdb
from flask import Flask, render_template, redirect, url_for, request
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import letter
from reportlab.lib.colors import black,green
from reportlab.lib.utils import simpleSplit
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors
from io import BytesIO
import os
from datetime import datetime


app = Flask(__name__, template_folder='templates')

app.secret_key = 'prashanth'

# MySQL Configuration
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'root'
app.config['MYSQL_DB'] = 'userre'

mysql = MySQL(app)

def create_tables():
    cursor = mysql.connection.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user (
            userid INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            lastname VARCHAR(100) NOT NULL,
            email VARCHAR(100) NOT NULL UNIQUE,
            phone_number VARCHAR(15),
            password VARCHAR(100) NOT NULL
        )
    ''')


    cursor.execute('''
        CREATE TABLE IF NOT EXISTS devices (
            device_id INT AUTO_INCREMENT PRIMARY KEY,
            project_name VARCHAR(100) NOT NULL,
            email VARCHAR(100) NOT NULL,
            project_id VARCHAR(50) NOT NULL,
            FOREIGN KEY (email) REFERENCES user(email) ON DELETE CASCADE
        )
    ''')

    mysql.connection.commit()
    cursor.close()

# Ensure tables are created when the application starts
with app.app_context():
    create_tables()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST' and 'email' in request.form and 'password' in request.form:
        email = request.form['email']
        password = request.form['password']
        cursor = mysql.connection.cursor()
        cursor.execute('SELECT * FROM user WHERE email = %s', (email,))
        user = cursor.fetchone()
        cursor.close()
        
        if user and check_password_hash(user[5], password):  # Assuming password is the 4th field in the user table
            session['loggedin'] = True
            session['userid'] = user[0]  # Primary key, assumed to be 'userid'
            session['name'] = user[1]
            session['email'] = user[3]
            session['phone'] = user[4]
            
            if email == 'admin@example.com' and check_password_hash(user[5],'adminpassword'):
                return redirect(url_for('admin'))
            else:
                message = 'Logged in successfully!'
                return redirect(url_for('user'))
        else:
            message = 'Please enter correct email / password!'
            return render_template('login.html', message=message)
    return render_template('login.html')

@app.route('/user/logout')
def user_logout():
    session.pop('loggedin', None)
    session.pop('userid', None)
    session.pop('name', None)
    session.pop('email', None)
    return render_template('user_logout.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        lastname = request.form.get('lastname')  # corrected from 'lname' to 'lastname'
        email = request.form.get('email')
        phone_number = request.form.get('phone')
        password = request.form.get('password')
        cursor = mysql.connection.cursor()
        cursor.execute('SELECT * FROM user WHERE email = %s', (email,))
        account = cursor.fetchone()
        if account:
            message = 'Account already exists!'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            message = 'Invalid email address!'
        elif not name or not password or not email:
            message = 'Please fill out the form!'
        else:
            hashed_password = generate_password_hash(password)
            cursor.execute('INSERT INTO user (name, lastname, email, phone_number, password) VALUES (%s, %s, %s, %s, %s)', (name, lastname, email, phone_number, hashed_password))
            mysql.connection.commit()
            message = 'You have successfully registered!'
            cursor.close()
            return render_template('login.html', message=message)
    return render_template('index.html')

@app.route('/admin')
def admin():
    if 'loggedin' in session:
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM user")
        users = cursor.fetchall()
        cursor.close()
        masked_users = []
        for user in users:
            masked_user = list(user)  # Convert tuple to list to modify the password
            masked_user[5] = '#' * 10  # Show a fixed length of masked password
            masked_users.append(tuple(masked_user))  # Convert back to tuple
        return render_template('admin.html', users=masked_users, name=session['name'])
    else:
        return redirect(url_for('login'))

@app.route('/admin/users')
def admin_users():
    if 'loggedin' in session:
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM user")
        users = cursor.fetchall()
        cursor.close()
        masked_users = []
        for user in users:
            masked_user = list(user)  # Convert tuple to list to modify the password
            masked_user[5] = '#' * 5  # Show a fixed length of masked password
            masked_users.append(tuple(masked_user))  # Convert back to tuple
        return render_template('admin_users.html', users=masked_users, name=session['name'])
    else:
        return redirect(url_for('login'))

@app.route('/admin/add_user', methods=['GET', 'POST'])
def admin_add_user():
    if 'loggedin' in session:
        if request.method == 'POST':
            name = request.form['name']
            lastname = request.form['lastname']
            email = request.form['email']
            phone_number = request.form['phone']
            password = request.form['password']
            cursor = mysql.connection.cursor()
            cursor.execute('SELECT * FROM user WHERE email = %s', (email,))
            account = cursor.fetchone()
            if account:
                message = 'Account already exists!'
            elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
                message = 'Invalid email address!'
            elif not name or not password or not email:
                message = 'Please fill out the form!'
            else:
                hashed_password = generate_password_hash(password)
                cursor.execute('INSERT INTO user (name, lastname, email, phone_number, password) VALUES (%s, %s, %s, %s, %s)', (name, lastname, email, phone_number, hashed_password))
                mysql.connection.commit()
                message = 'User added successfully!'
                cursor.close()
                return redirect(url_for('admin_users'))
        return render_template('admin_add_user.html', name=session['name'])
    else:
        return redirect(url_for('login'))

@app.route('/delete_user/<int:userid>', methods=['POST'])
def delete_user(userid):
    if 'loggedin' in session:
        cursor = mysql.connection.cursor()
        try:
            # Get the email of the user to be deleted
            cursor.execute("SELECT email FROM user WHERE userid = %s", (userid,))
            user_email = cursor.fetchone()
            
            if user_email:
                email = user_email[0]

                # Delete associated devices
                cursor.execute("DELETE FROM devices WHERE email = %s", (email,))

                # Delete the user
                cursor.execute("DELETE FROM user WHERE userid = %s", (userid,))
                mysql.connection.commit()

                flash('User and associated devices deleted successfully!', 'success')
            else:
                flash('User not found!', 'danger')
        except MySQLdb.IntegrityError as e:
            mysql.connection.rollback()
            flash(f'Failed to delete user: {e}', 'danger')
        finally:
            cursor.close()
        
        return redirect(url_for('admin_users'))
    else:
        return redirect(url_for('login'))


@app.route('/delete_user_by_email/<email>', methods=['POST'])
def delete_user_by_email(email):
    if 'loggedin' in session:
        cursor = mysql.connection.cursor()
        try:
            cursor.execute("DELETE FROM user WHERE email = %s", (email,))
            mysql.connection.commit()
            message = f"User with email {email} has been deleted."
        except Exception as e:
            message = str(e)
        cursor.close()
        return render_template('admin_users.html', message=message)
    else:
        return redirect(url_for('login'))

@app.route('/drop_column/<table_name>/<column_name>', methods=['POST'])
def drop_column(table_name, column_name):
    if 'loggedin' in session:
        cursor = mysql.connection.cursor()
        try:
            cursor.execute(f"ALTER TABLE {table_name} DROP COLUMN {column_name}")
            mysql.connection.commit()
            message = f"Column {column_name} has been dropped from {table_name}."
        except Exception as e:
            message = str(e)
        cursor.close()
        return render_template('admin_users.html', message=message)
    else:
        return redirect(url_for('login'))
    
@app.route('/admin/select_user', methods=['GET', 'POST'])
def admin_select_user():
    if 'loggedin' in session:
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM user")
        users = cursor.fetchall()
        cursor.close()
        
        if request.method == 'POST':
            selected_user_email = request.form['user_email']
            return redirect(url_for('admin_add_device', email=selected_user_email))
        
        return render_template('admin_select_user.html', users=users, name=session['name'])
    else:
        return redirect(url_for('login'))

@app.route('/admin/add_device/<email>', methods=['GET', 'POST'])
def admin_add_device(email):
    if 'loggedin' not in session:
        return redirect(url_for('login'))

    cursor = mysql.connection.cursor()

    if request.method == 'POST':
        project_name = request.form['project_name']
        project_id = request.form['project_id']

        # Insert device into the database
        try:
            cursor.execute("INSERT INTO devices (project_name, email, project_id) VALUES (%s, %s, %s)",
                           (project_name, email, project_id))
            mysql.connection.commit()
            flash('Device added successfully!', 'success')
        except Exception as e:
            mysql.connection.rollback()  # Rollback if there's an error
            flash(f'Error adding device: {str(e)}', 'danger')

    # Fetch all devices for the user
    cursor.execute("SELECT device_id, project_name, email, project_id FROM devices WHERE email = %s", (email,))
    devices = cursor.fetchall()

    # Fetch project IDs for the dropdown
    cursor.execute("SELECT id, name FROM project_id")
    projects = cursor.fetchall()

    cursor.close()

    return render_template('admin_add_device.html', email=email, devices=devices, projects=projects)

@app.route('/admin/remove_device/<int:device_id>', methods=['POST'])
def remove_device(device_id):
    if 'loggedin' not in session:
        return redirect(url_for('login'))

    cursor = mysql.connection.cursor()
    try:
        cursor.execute("DELETE FROM devices WHERE device_id = %s", (device_id,))
        mysql.connection.commit()
        flash('Device removed successfully!', 'success')
    except Exception as e:
        mysql.connection.rollback()
        flash(f'Error removing device: {str(e)}', 'danger')
    finally:
        cursor.close()

    return redirect(url_for('admin_add_device', email=request.form['email']))


@app.route('/admin/project_management', methods=['GET', 'POST'])
def project_management():
    if 'loggedin' not in session:
        return redirect(url_for('login'))

    cursor = mysql.connection.cursor()

    if request.method == 'POST':
        if 'add_project' in request.form:
            project_name = request.form['new_project']
            cursor.execute("INSERT INTO project_id (name) VALUES (%s)", (project_name,))
            mysql.connection.commit()
            flash('Project added successfully!', 'success')
        elif 'delete_project' in request.form:
            project_id = request.form['project_id']
            cursor.execute("DELETE FROM project_id WHERE id = %s", (project_id,))
            mysql.connection.commit()
            flash('Project deleted successfully!', 'success')
        elif 'rename_project' in request.form:
            project_id = request.form['project_id']
            new_name = request.form['new_name']
            cursor.execute("UPDATE project_id SET name = %s WHERE id = %s", (new_name, project_id))
            mysql.connection.commit()
            flash('Project renamed successfully!', 'success')

    cursor.execute("SELECT * FROM project_id")
    projects = cursor.fetchall()
    cursor.close()

    return render_template('project_management.html', projects=projects)
    
@app.route('/user')
def user():
    if 'loggedin' in session:
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM user")
        users = cursor.fetchall()
        cursor.close()
        masked_users = []
        for user in users:
            masked_user = list(user)  # Convert tuple to list to modify the password
            masked_user[5] = '#' * 10  # Show a fixed length of masked password
            masked_users.append(tuple(masked_user))  # Convert back to tuple
        return render_template('user.html', users=masked_users, name=session['name'])
    else:
        return redirect(url_for('login'))

@app.route('/devices', methods=['GET', 'POST'])
def devices():
    if 'loggedin' not in session:
        return redirect(url_for('login'))
    user_email = session['email']
    if request.method == 'POST':
        project_name = request.form['project_name']
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT project_name, device_id, email, project_id FROM devices WHERE project_name = %s AND email = %s", (project_name, user_email))
        device_data = cursor.fetchall()
        cursor.close()
        return render_template('devices1.html', devices=device_data)
    else:
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT project_name, device_id, email, project_id FROM devices WHERE email = %s", (user_email,))
        device_data = cursor.fetchall()
        cursor.close()
        return render_template('devices1.html', devices=device_data)


@app.route('/dashboard')
def dashboard():
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT project_name, device_id, email, project_id FROM devices")
    devices = cursor.fetchall()
    cursor.close()
    return render_template('dashboard.html', devices=devices)

@app.route('/add_device', methods=['GET', 'POST'])
def add_device():
    if 'loggedin' in session:
        if request.method == 'POST':
            project_name = request.form['project_name']
            project_id = request.form['project_id']
            email = session['email']  # Get the email from session

            cur = mysql.connection.cursor()
            cur.execute("INSERT INTO devices (project_name, email, project_id) VALUES (%s, %s, %s)",
                        (project_name, email, project_id))
            mysql.connection.commit()
            cur.close()
            message = 'Device added successfully!'
            return redirect(url_for('user', message=message))

        # Fetch project IDs for the dropdown
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT id, name FROM project_id")  # Fetch the project IDs and names
        projects = cursor.fetchall()  # This will be a list of tuples (id, name)
        cursor.close()

        return render_template('add_device.html', projects=projects)

    return redirect(url_for('login'))



@app.route('/admin/profile')
def admin_profile():
    if 'loggedin' in session:
        return render_template('admin_profile.html', name=session['name'])
    else:
        return redirect(url_for('login'))
    
@app.route('/contact')
def contact():
    return render_template('contact.html')



@app.route('/user/user_profile')
def user_profile():
    if 'loggedin' in session:
        return render_template('user_profile.html', name=session['name'], email=session['email'])
    else:
        return redirect(url_for('login'))
    
@app.route('/update_user_details', methods=['POST'])
def update_user_details():
    if 'userid' not in session:
        return redirect(url_for('login'))  # Redirect to login if user is not logged in

    userid = session['userid']
    name = request.form.get('name', '')
    lastname = request.form.get('lastname', '')
    new_email = request.form.get('email', '')
    phone_number = request.form.get('phone', '')

    cursor = mysql.connection.cursor()

    try:
        # Fetch the user details to ensure the user exists
        cursor.execute('SELECT * FROM user WHERE userid = %s', (userid,))
        account = cursor.fetchone()

        if account:
            old_email = account[3]  # Assuming email is the 4th field in the user table

            # Update email if changed and ensure email is valid and not taken
            if new_email != old_email:
                cursor.execute('SELECT * FROM user WHERE email = %s', (new_email,))
                email_account = cursor.fetchone()
                if email_account:
                    message = 'The new email address is already registered!'
                    flash(message)
                    return redirect(url_for('user_profile'))
                
                cursor.execute('UPDATE devices SET email = %s WHERE email = %s', (new_email, old_email))
                session['email'] = new_email  # Update session with the new email

            # Update the user details
            cursor.execute('UPDATE user SET email = %s, name = %s, lastname = %s, phone_number = %s WHERE userid = %s', 
                           (new_email, name, lastname, phone_number, userid))
            message = 'Profile updated successfully!'
            mysql.connection.commit()
        else:
            message = 'User does not exist!'
    except Exception as e:
        mysql.connection.rollback()
        message = f'Error: {str(e)}'
    finally:
        cursor.close()

    flash(message)
    return redirect(url_for('user_profile'))
@app.route('/Quotation')
def quotation():
    return render_template('Quotation.html')
@app.route('/Existing')
def existing():
    return render_template('existing.html')
@app.route('/generate_pdf', methods=['POST'])
def generate_pdf():
    data = request.get_json()

    customer_name = data['customer_name']
    customer_village = data['customer_village']
    customer_email = data['customer_email']
    customer_phone = data['customer_phone']
    total_amount = data['total_amount']
    items = data['items']

    cur = mysql.connection.cursor()
    
    # Ensure date format is correct for MySQL (YYYY-MM-DD)
    current_date = datetime.now().strftime("%Y-%m-%d")

    # Insert data into quotations table (excluding quotation_number initially)
    cur.execute("""
        INSERT INTO quotations (customer_name, customer_village, customer_email, customer_phone, total_amount, created_at, quotation_date) 
        VALUES (%s, %s, %s, %s, %s, NOW(), %s)
    """, (customer_name, customer_village, customer_email, customer_phone, total_amount, current_date))
    
    mysql.connection.commit()

    # Get the last inserted quotation ID
    quotation_id = cur.lastrowid  

    # Generate Quotation Number (Example: Q-00001)
    quotation_number = f"MGT-{quotation_id:05d}"

    # Update quotation_number in the table
    cur.execute("""
        UPDATE quotations SET quotation_number = %s WHERE id = %s
    """, (quotation_number, quotation_id))
    
    mysql.connection.commit()

    # Insert items related to this quotation
    for item in items:
        cur.execute("""
            INSERT INTO quotation_items (quotation_id, serial_no, description, quantity, price, gst_percentage, gst_amount, total)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (quotation_id, item['serial_no'], item['description'], item['quantity'], item['price'], item['gst_percentage'], item['gst_amount'], item['total']))
    
    mysql.connection.commit()
    cur.close()

    buffer = BytesIO()
    pdf = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []

    # Paths for header and footer images
    static_folder = os.path.join(os.getcwd(), r'C:\Users\mreti\Downloads\web prg\web prg\static')
    header_path = os.path.join(static_folder, 'header.png')
    footer_path = os.path.join(static_folder, 'footer.png')

    styles = getSampleStyleSheet()

    # Header & Footer Drawing Function for First Page
    def draw_header_footer_first_page(canvas, doc):
        width, height = letter

        # Header Image
        try:
            canvas.drawImage(header_path, 8, height - 90, width=600, height=100, preserveAspectRatio=True, mask='auto')
        except Exception as e:
            print(f"Header image error: {e}")

        # Footer Image
        try:
            canvas.drawImage(footer_path, 6, 10, width=600, height=100, preserveAspectRatio=True, mask='auto')
        except Exception as e:
            print(f"Footer image error: {e}")

        # Document Title (Centered) - Only on First Page
        canvas.setFont("Helvetica-Bold", 16)
        canvas.drawString(270, height - 110, "QUOTATION")

        # # Date (Right-Aligned) - Only on First Page
        # canvas.setFont("Helvetica", 12)
        # canvas.drawString(500, height - 130, f"Date: {current_date}")
        # Add Quotation Number & Date
    elements.append(Paragraph(f"<b>Quotation Number:</b> {quotation_number}", styles['Normal']))
    elements.append(Paragraph(f"<b>Date:</b> {current_date}", styles['Normal']))
    elements.append(Spacer(1, 20))

    # Header & Footer Drawing Function for Later Pages (No Title or Date)
    def draw_header_footer_later_pages(canvas, doc):
        width, height = letter

        # Header Image
        try:
            canvas.drawImage(header_path, 8, height - 90, width=600, height=100, preserveAspectRatio=True, mask='auto')
        except Exception as e:
            print(f"Header image error: {e}")

        # Footer Image
        try:
            canvas.drawImage(footer_path, 6, 10, width=600, height=100, preserveAspectRatio=True, mask='auto')
        except Exception as e:
            print(f"Footer image error: {e}")

    # Add Space After Quotation Title
    elements.append(Spacer(1, 40))  

    # Customer Info Section (After Quotation Title)
    customer_info = [
        ["To:"],
        [f"Mr. {customer_name}"],
        [f"{customer_village}"],
        [f"{customer_email}"],
        [f"{customer_phone}"]
    ]

    customer_table = Table(customer_info, colWidths=[460,500])
    customer_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))

    elements.append(customer_table)
    elements.append(Spacer(1, 20))  # Space after customer details

    # Table Header
    table_data = [
        ["S. No.", "Description", "Qty", "Price", "GST (%)", "GST Amt", "Total"]
    ]

    # Formatting long descriptions to wrap text properly
    for item in items:
        serial_no = str(item['serial_no'])
        description = Paragraph(item['description'], styles['Normal'])
        quantity = str(item['quantity'])
        price = str(item['price'])
        gst_percentage = str(item['gst_percentage'])
        gst_amount = str(item['gst_amount'])
        total = str(item['total'])

        table_data.append([serial_no, description, quantity, price, gst_percentage, gst_amount, total])

    # Table Styling
    table = Table(table_data, colWidths=[40, 180, 50, 60, 50, 70, 80])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),  # Header background
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),  # Header text color
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)  # Proper table borders
    ]))

    elements.append(table)
    elements.append(Spacer(1, 20))  # Space before Grand Total

    # Grand Total Section
    grand_total_table = Table([
        ["", "", "", "", "Grand Total:", f"{total_amount}"]
    ], colWidths=[40, 180, 50, 60, 70, 70, 80])

    grand_total_table.setStyle(TableStyle([
        ('FONTNAME', (4, 0), (-1, -1), 'Helvetica-Bold'),
        ('ALIGN', (4, 0), (-1, -1), 'CENTER'),
        ('GRID', (4, 0), (-1, -1), 1, colors.black),
        ('BACKGROUND', (4, 0), (-1, -1), colors.lightgrey),
        ('TEXTCOLOR', (4, 0), (-1, -1), colors.black),
        ('BOTTOMPADDING', (4, 0), (-1, -1), 10),
    ]))

    elements.append(grand_total_table)

    # **Build PDF with Different Header/Footer for First and Later Pages**
    pdf.build(elements, onFirstPage=draw_header_footer_first_page, onLaterPages=draw_header_footer_later_pages)

    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name="quotation.pdf", mimetype='application/pdf')

@app.route('/change_password', methods=['POST'])
def change_password():
    if 'userid' not in session:
        return redirect(url_for('login'))  # Redirect to login if user is not logged in

    userid = session['userid']
    current_password = request.form.get('current_password', '')
    new_password = request.form.get('new_password', '')
    confirm_password = request.form.get('confirm_password', '')

    cursor = mysql.connection.cursor()

    try:
        # Fetch the user details to ensure the user exists
        cursor.execute('SELECT * FROM user WHERE userid = %s', (userid,))
        account = cursor.fetchone()

        if account:
            # Verify current password
            if not check_password_hash(account[5], current_password):  # Assuming password is the 6th field
                message = 'Current password is incorrect!'
            elif new_password != confirm_password:
                message = 'New password and confirm password do not match!'
            else:
                hashed_password = generate_password_hash(new_password)
                cursor.execute('UPDATE user SET password = %s WHERE userid = %s', (hashed_password, userid))
                mysql.connection.commit()
                message = 'Password updated successfully!'
        else:
            message = 'User does not exist!'
    except Exception as e:
        mysql.connection.rollback()
        message = f'Error: {str(e)}'
    finally:
        cursor.close()

    flash(message)
    return redirect(url_for('user_profile'))

# Generate a unique quotation number
def generate_quotation_number():
    return f"MGT-{random.randint(100000, 999999)}"

@app.route('/fetch_items', methods=['POST'])
def fetch_items():
    data = request.get_json()
    category = data.get("category")
    capacity = data.get("capacity")

    cursor = mysql.connection.cursor()

    cursor.execute('''
        SELECT id, description, quantity, price, gst_percentage, gst_amount, total
        FROM Existing_items
        WHERE category = %s AND capacity = %s
    ''', (category, capacity))

    items = cursor.fetchall()
    cursor.close()

    # Check if no items were fetched
    if not items:
        return jsonify({"error": "No items found for this category and capacity"}), 404

    # Convert the fetched data into a list of dictionaries
    items_list = []
    for item in items:
        item_dict = {
            'id': item[0],
            'description': item[1],
            'quantity': item[2],
            'price': item[3],
            'gst_percentage': item[4],
            'gst_amount': item[5],
            'total': item[6]
        }
        items_list.append(item_dict)

    # Return the items as JSON
    return jsonify({"items": items_list})

@app.route('/dgenerate_pdf', methods=['POST'])
def dgenerate_pdf():
    data = request.get_json()

    customer_name = data['customer_name']
    customer_village = data['customer_village']
    customer_email = data['customer_email']
    customer_phone = data['customer_phone']
    total_amount = data['total_amount']
    items = data['items']

    conn = mysql.connection
    cur = conn.cursor()

    # Generate quotation number BEFORE inserting
    quotation_number = generate_quotation_number()
    current_date = datetime.now().strftime("%Y-%m-%d")

    # Insert into Existing_quotations
    cur.execute("""
        INSERT INTO quotations 
        (customer_name, customer_village, customer_email, customer_phone, total_amount, created_at, quotation_date, quotation_number) 
        VALUES (%s, %s, %s, %s, %s, NOW(), %s, %s)
    """, (customer_name, customer_village, customer_email, customer_phone, total_amount, current_date, quotation_number))

    conn.commit()

    # Get inserted quotation ID
    quotation_id = cur.lastrowid

    # Insert items into Existing_quotation_items
    for item in items:
        cur.execute("""
            INSERT INTO Existing_quotation_items 
            (quotation_id, serial_no, description, quantity, price, gst_percentage, gst_amount, total)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (quotation_id, item['serial_no'], item['description'], item['quantity'], 
              item['price'], item['gst_percentage'], item['gst_amount'], item['total']))

    conn.commit()
    cur.close()

    # Generate PDF
    buffer = BytesIO()
    pdf = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []

    # Paths for header and footer images
    static_folder = os.path.join(os.getcwd(), r'C:\Users\mreti\Downloads\web prg\web prg\static')
    header_path = os.path.join(static_folder, 'header.png')
    footer_path = os.path.join(static_folder, 'footer.png')

    styles = getSampleStyleSheet()

    # Header & Footer Drawing Function for First Page
    def draw_header_footer_first_page(canvas, doc):
        width, height = letter

        # Header Image
        try:
            canvas.drawImage(header_path, 8, height - 90, width=600, height=100, preserveAspectRatio=True, mask='auto')
        except Exception as e:
            print(f"Header image error: {e}")

        # Footer Image
        try:
            canvas.drawImage(footer_path, 6, 10, width=600, height=100, preserveAspectRatio=True, mask='auto')
        except Exception as e:
            print(f"Footer image error: {e}")

        # Document Title (Centered) - Only on First Page
        canvas.setFont("Helvetica-Bold", 16)
        canvas.drawString(270, height - 110, "QUOTATION")

    # Header & Footer Drawing Function for Later Pages (No Title or Date)
    def draw_header_footer_later_pages(canvas, doc):
        width, height = letter

        # Header Image
        try:
            canvas.drawImage(header_path, 8, height - 90, width=600, height=100, preserveAspectRatio=True, mask='auto')
        except Exception as e:
            print(f"Header image error: {e}")

        # Footer Image
        try:
            canvas.drawImage(footer_path, 6, 10, width=600, height=100, preserveAspectRatio=True, mask='auto')
        except Exception as e:
            print(f"Footer image error: {e}")

    # Add Space After Quotation Title
    elements.append(Spacer(1, 40))

    # Add Quotation Number & Date
    elements.append(Paragraph(f"<b>Quotation Number:</b> {quotation_number}", styles['Normal']))
    elements.append(Paragraph(f"<b>Date:</b> {current_date}", styles['Normal']))
    elements.append(Spacer(1, 20))

    # Customer Info Section (After Quotation Title)
    customer_info = [
        ["To:"],
        [f"Mr. {customer_name}"],
        [f"{customer_village}"],
        [f"{customer_email}"],
        [f"{customer_phone}"]
    ]

    customer_table = Table(customer_info, colWidths=[460,500])
    customer_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))

    elements.append(customer_table)
    elements.append(Spacer(1, 20))  # Space after customer details

    # Table Header
    table_data = [
        ["S. No.", "Description", "Qty", "Price", "GST (%)", "GST Amt", "Total"]
    ]

    # Formatting long descriptions to wrap text properly
    for item in items:
        serial_no = str(item['serial_no'])
        description = Paragraph(item['description'], styles['Normal'])
        quantity = str(item['quantity'])
        price = str(item['price'])
        gst_percentage = str(item['gst_percentage'])
        gst_amount = str(item['gst_amount'])
        total = str(item['total'])

        table_data.append([serial_no, description, quantity, price, gst_percentage, gst_amount, total])

    # Table Styling
    table = Table(table_data, colWidths=[40, 180, 50, 60, 50, 70, 80])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),  # Header background
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),  # Header text color
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)  # Proper table borders
    ]))

    elements.append(table)
    elements.append(Spacer(1, 20))  # Space before Grand Total

    # Grand Total Section
    grand_total_table = Table([
        ["", "", "", "", "Grand Total:", f"{total_amount}"]
    ], colWidths=[40, 180, 50, 60, 70, 70])

    grand_total_table.setStyle(TableStyle([
        ('FONTNAME', (4, 0), (-1, -1), 'Helvetica-Bold'),
        ('ALIGN', (4, 0), (-1, -1), 'CENTER'),
        ('GRID', (4, 0), (-1, -1), 1, colors.black),
        ('BACKGROUND', (4, 0), (-1, -1), colors.lightgrey),
        ('TEXTCOLOR', (4, 0), (-1, -1), colors.black),
        ('BOTTOMPADDING', (4, 0), (-1, -1), 10),
    ]))

    elements.append(grand_total_table)

    # **Build PDF with Different Header/Footer for First and Later Pages**
    pdf.build(elements, onFirstPage=draw_header_footer_first_page, onLaterPages=draw_header_footer_later_pages)

    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name="quotation.pdf", mimetype='application/pdf')

@app.route('/process_form', methods=['POST'])
def process_form():
    # Process form data here
    # Example:
    name = request.form.get('name')
    email = request.form.get('email')
    # Save data or perform actions as needed

    # Redirect to another page after processing
    return redirect(url_for('dashboard'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == "__main__":
    app.run()

