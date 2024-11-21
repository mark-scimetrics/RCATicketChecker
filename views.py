import os
import io
import csv
import sqlite3

from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    Response,
    request,
    session,
    url_for,
)

# Pre-defined users and passwords
USERS = {'user': 'BrahmsOp45', 'admin': 'adminBrahmsOp45'}

# Store ticket data in memory for simplicity
# In a real application, consider using a database
TICKETS = {}

appbp = Blueprint('views', __name__, template_folder='templates')
if __name__ == '__main__':
    appbp.run(debug=True)


@appbp.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in USERS and USERS[username] == password:
            session['username'] = username
            return redirect(
                url_for('views.upload_file' if username ==
                        'admin' else 'views.check_tickets'))
        else:
            flash('Invalid username or password')
    return render_template('index.html')


@appbp.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if session.get('username') != 'admin':
        return redirect(url_for('views.index'))
    if request.method == 'POST':
        filename = 'concert_tickets.csv'
        with open(filename, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            db = sqlite3.connect('tickets.db')
            cursor = db.cursor()
            # Clear existing records in the tickets table
            cursor.execute('DELETE FROM tickets')

            for row in reader:
                source = "None"  #row.get('source', 'other').strip() or 'other'
                cursor.execute(
                    '''
                    INSERT INTO tickets (order_number, name, total_tickets, zone, source)
                    VALUES (?, ?, ?, ?, ?)
                ''', (row['order_number'], row['name'],
                      int(row['number_of_tickets']), row['zone'], source))
            db.commit()
            db.close()

        flash('File uploaded successfully')
        return redirect(url_for('views.check_tickets'))
    return render_template('upload.html')


@appbp.route('/check_tickets', methods=['GET', 'POST'])
def check_tickets():
    if 'username' not in session:
        return redirect(url_for('views.index'))

    db = sqlite3.connect('tickets.db')
    cursor = db.cursor()
    cursor.execute('SELECT order_number FROM tickets')
    order_numbers = [row[0] for row in cursor.fetchall()]

    ticket_info = None
    if request.method == 'POST':
        order_value = request.form.get('order_number')
        if order_value:
            cursor.execute('SELECT * FROM tickets WHERE order_number=?',
                           (order_value, ))
            ticket_info = cursor.fetchone()
            if ticket_info:
                session['order_number'] = order_value
                session['ticket_info'] = {
                    'order_number': ticket_info[1],
                    'name': ticket_info[2],
                    'total_tickets': ticket_info[3],
                    'zone': ticket_info[4],
                    'allocated_tickets': ticket_info[5]
                }
                return redirect(url_for('views.check_tickets2'))
            else:
                flash('Order number not found')
    db.close()
    return render_template('check_tickets.html', order_numbers=order_numbers)


@appbp.route('/check_tickets2', methods=['GET', 'POST'])
def check_tickets2():
    if 'username' not in session:
        return redirect(url_for('views.index'))
    order_number = session.get('order_number')
    ticket_info = session.get('ticket_info')

    if request.method == 'POST' and ticket_info:
        attending = int(request.form.get('attending', 1))
        # Capture the source information
        source = request.form.get('source', 'other')

        if attending <= ticket_info['total_tickets'] - ticket_info[
                'allocated_tickets']:
            new_allocated = ticket_info['allocated_tickets'] + attending
            db = sqlite3.connect('tickets.db')
            cursor = db.cursor()
            cursor.execute(
                '''
              UPDATE tickets
              SET allocated_tickets = ?, source=?
              WHERE order_number = ?
          ''', (new_allocated, source, order_number))
            db.commit()
            db.close()

            # Update session info
            ticket_info['allocated_tickets'] = new_allocated
            session['ticket_info'] = ticket_info

            flash('Tickets updated successfully')
            return redirect(url_for('views.check_tickets'))
        else:
            flash('Cannot allocate more tickets than available')

    return render_template('check_tickets2.html',
                           order_number=order_number,
                           ticket_info=ticket_info)


@appbp.route('/ticketing_summary')
def ticketing_summary():
    summary = {}
    contacts_summary = {}

    db = sqlite3.connect('tickets.db')
    cursor = db.cursor()
    cursor.execute(
        'SELECT zone, total_tickets, allocated_tickets, source FROM tickets')

    for zone, total_tickets, allocated_tickets, source in cursor.fetchall():
        if zone not in summary:
            summary[zone] = {'total_tickets': 0, 'allocated_tickets': 0}
        summary[zone]['total_tickets'] += total_tickets
        summary[zone]['allocated_tickets'] += allocated_tickets
        # Record contact sources
        if source not in contacts_summary:
            contacts_summary[source] = 0
        contacts_summary[source] += 1
    db.close()

    ticket_summary = {
        zone: {
            'total_tickets': data['total_tickets'],
            'allocated_tickets': data['allocated_tickets']
        }
        for zone, data in summary.items()
    }

    return render_template('ticketing_summary.html',
                           ticket_summary=ticket_summary,
                           contacts_summary=contacts_summary)


@appbp.route('/logout')
def logout():
    session.clear()  # This clears all data stored in the session
    return redirect(url_for('views.index'))


@appbp.route('/download2')
def download_csv():
    # Connect to the database
    db = sqlite3.connect('tickets.db')
    cursor = db.cursor()
    cursor.execute('SELECT * FROM tickets')

    # Fetch all ticket data
    rows = cursor.fetchall()
    db.close()

    # Define CSV headers
    headers = [
        'ID', 'Order Number', 'Name', 'Total Tickets', 'Zone',
        'Allocated Tickets', 'Source'
    ]

    # Use io.StringIO to create an in-memory file-like object
    buffer = io.StringIO()
    csv_writer = csv.writer(buffer)

    # Write the header
    csv_writer.writerow(headers)

    # Write data rows
    for row in rows:
        csv_writer.writerow(row)

    # Move buffer's pointer to the beginning
    buffer.seek(0)

    # Create a response with the appropriate headers for file download
    response = Response(buffer, mimetype='text/csv')
    response.headers.set("Content-Disposition",
                         "attachment",
                         filename="tickets.csv")
    return response


def dict_to_array(data_dict):
    if not data_dict:
        return []  # Return an empty list if data_dict is empty

    # Assuming all dictionaries have the same structure,
    # use the keys of the first item as headers.
    # Adding 'ID' as the first header if you want to include the dictionary key.
    headers = ["ID"] + list(next(iter(data_dict.values())).keys())

    # Initialize the array with headers
    array = [headers]

    # Iterate through the dictionary, adding each item's details as a new row
    for id, info in data_dict.items():
        row = [id] + list(info.values())
        array.append(row)

    return array


def generate_csv(data):
    buffer = io.StringIO()  # Create a buffer to hold CSV data
    csv_writer = csv.writer(buffer, quoting=csv.QUOTE_NONNUMERIC)

    for row in data:
        csv_writer.writerow(row)
        buffer.seek(0)  # Move to the start of the buffer
        line = buffer.getvalue()  # Get the content of the buffer
        yield line
        buffer.truncate(0)  # Clear the buffer for the next row
        buffer.seek(0)  # Reset the buffer pointer to the start


# Generate the CSV data
def generate(csv_data):
    for line in generate_csv(csv_data):
        yield line
