import csv
import os
import io

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
USERS = {'user': 'BWV244', 'admin': 'adminBWV244'}

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
    #   file = request.files['file']
    #   if file and file.filename.endswith('.csv'):

    #DEBUG SET THE FILENAME HERE
    filename = 'concert_tickets.csv'
    global TICKETS
    TICKETS = {}
    with open(  # file.
        filename, 'r', encoding='utf-8') as file:
      reader = csv.DictReader(file)
      #reader = csv.DictReader(file.stream)
      k = 0
      for row in reader:
        order_number2 = k  #int(row['order_number'])
        k = k + 1
        TICKETS[order_number2] = {
            'order_number': row['order_number'],
            'name': row['name'],
            'total_tickets': int(row['number_of_tickets']),
            'zone': row['zone'],
            'allocated_tickets': 0
        }

      print(TICKETS)

    flash('File uploaded successfully')
    return redirect(url_for('views.check_tickets'))
  #  else:
  #    flash('Invalid file format')
  return render_template('upload.html')


@appbp.route('/check_tickets', methods=['GET', 'POST'])
def check_tickets():
  if 'username' not in session:
    return redirect(url_for('views.index'))

  # Assuming TICKETS is a dictionary with order numbers as keys
  #order_numbers = list(TICKETS.keys())
  order_numbers = [details['order_number'] for details in TICKETS.values()]
  print("check tick - order_num")  #,order_numbers)
  ticket_info = None

  #if request.method == 'POST':
  #data = request.get_json()
  #order_number = int(data.get('order_number'))
  if request.method == 'POST':


    order_value = request.form.get('order_number')
    order_number = order_numbers.index(order_value)
    print("check tick - order_num2", order_number)

    

    if order_number>=0:
      order_num = int(order_number)
      ticket_info = TICKETS[order_num]
      print("check tick - ticket_info", ticket_info)

  #order_num = 1
  #ticket_info = TICKETS[order_num]
  print("ticket_info2", ticket_info)

  if ticket_info == None:
    return render_template('check_tickets.html', order_numbers=order_numbers)
  else:
    session['order_number'] = order_num
    session['ticket_info'] = ticket_info
    return redirect(url_for('views.check_tickets2'))

    #render_template('check_tickets2.html', order_number=order_num, ticket_info=ticket_info)


@appbp.route('/check_tickets2', methods=['GET', 'POST'])
def check_tickets2():
  if 'username' not in session:
    return redirect(url_for('views.index'))
  order_number = session.get('order_number')
  ticket_info = session.get('ticket_info')

  if request.method == 'POST':
    #order_number = request.form.get('order_number')
   print("check tick 2 - order number:", order_number)

   if order_number>=0 :

      print("check tick 2 - ticket info:", ticket_info)

      if ticket_info:
        attending = int(request.form.get('attending', 1))
        print("check tick2 - attending:", attending)
        if attending <= ticket_info['total_tickets'] - ticket_info[
            'allocated_tickets']:
          ticket_info['allocated_tickets'] += attending
          TICKETS[order_number] = ticket_info
          flash('Tickets updated successfully')
          print("check tick2 out: ticket_info", ticket_info)
          return redirect(url_for('views.check_tickets'))
        else:
          flash('Cannot allocate more tickets than available')
   else:
      flash('Please enter an order number.')

  return render_template('check_tickets2.html',
                         order_number=order_number,
                         ticket_info=ticket_info)


@appbp.route('/ticketing_summary')
def ticketing_summary():
  # Assuming TICKETS is a global dictionary storing all ticket info
  # You would calculate the summary info here, which is simplified for this example
  summary = {}
  for order in TICKETS.values():
    zone = order['zone']
    if zone not in summary:
      summary[zone] = {'total_tickets': 0, 'allocated_tickets': 0}
    summary[zone]['total_tickets'] += order['total_tickets']
    summary[zone]['allocated_tickets'] += order['allocated_tickets']

  # Convert to a format suitable for the template if necessary
  ticket_summary = {
      zone: {
          'total_tickets': data['total_tickets'],
          'allocated_tickets': data['allocated_tickets']
      }
      for zone, data in summary.items()
  }

  return render_template('ticketing_summary.html',
                         ticket_summary=ticket_summary)


@appbp.route('/logout')
def logout():
  session.clear()  # This clears all data stored in the session
  return redirect(url_for('views.index'))


@appbp.route('/download2')
def download_csv():
  # Define the CSV data or generate dynamically
  # Convert the dictionary to an array format
  csv_data = dict_to_array(TICKETS)
  print("DOWNLOAD: ", csv_data)
  # Create a generator to convert the CSV data into a format that can be served

  # Generate the response with the appropriate headers for file download
  response = Response(generate(csv_data), mimetype='text/csv')
  response.headers.set("Content-Disposition",
                       "attachment; filename=myfile.csv")
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
