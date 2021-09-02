import json

from flask import Flask, render_template, request, flash
from pymongo import MongoClient

settings_file = open("../../settings.json")
settings_data = json.load(settings_file)
settings_file.close()

secrets_file = open("../../secrets.json")
secrets_data = json.load(secrets_file)
secrets_file.close()

app = Flask(__name__)
app.config['SECRET_KEY'] = secrets_data['cloud']['web_secret_code']

client = MongoClient(settings_data['cloud']['db_address'], settings_data['cloud']['db_port'])
db = client[settings_data['cloud']['db_name']]
orders = db[settings_data['cloud']['db_order_table_name']]


def count_stock(color):
    return db.repository.find({'color': color}).count()


@app.route('/', methods=['GET'])
def dropdown():
    colours = ['red', 'yellow', 'white']
    dests = ['0', '1', '2']
    return render_template('main_page.html', colours=colours, dests=dests)


@app.route("/json", methods=['POST'])
def order_new():
    colours = ['red', 'yellow', 'white']
    dests = ['0', '1', '2']
    color = request.form['colours']
    dest = request.form['dests']
    new_order = {'color': color, 'dest': dest, 'status': 0}
    orders.insert_one(new_order)
    flash("Order Completed!")
    return render_template('main_page.html', colours=colours, dests=dests)


@app.route("/stocks")
def show_stocks():
    red = count_stock('red')
    yellow = count_stock('yellow')
    white = count_stock('white')
    return render_template('stocks.html', red=red, yellow=yellow, white=white)


@app.route("/orders")
def show_orders():
    ods = list(db.order.find({'status': {'$lte': 3}}))
    for odr in ods:
        odr["tag_color"] = "w3-" + odr["color"]
    print(ods)
    return render_template('orders.html', orders=ods)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)
