from pymongo import MongoClient
from flask import Flask, render_template, request, jsonify, flash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'

client = MongoClient('localhost', 27018)
db = client["database"]
orders = db["order"]

def count_stock(color):
    return db.storage.find({'color':color}).count()

@app.route('/', methods=['GET'])
def dropdown():
    colours = ['red', 'yellow', 'white']
    dests = ['1','2', '3']
    return render_template('main_page.html', colours=colours, dests=dests)

@app.route("/json", methods=['POST'])
def order_new():
    colours = ['red', 'yellow', 'white']
    dests = ['1','2', '3']
    color = request.form['colours']
    dest = request.form['dests']
    new_order = {'color':color, 'dest':dest, 'status':0}
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
    ods = list(db.order.find({'status':{'$lte':3}}))
    for odr in ods:
        odr["tag_color"]="w3-"+odr["color"]
    print(ods)
    return render_template('orders.html', orders = ods)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)