from flask import Flask, render_template, request, redirect, url_for, Response
import json
from confluent_kafka import Producer

app = Flask(__name__)

# Kafka producer configuration
conf = {'bootstrap.servers': 'my-cluster-kafka-bootstrap.strimzi.svc.cluster.local:9092'}
producer = Producer(conf)

# Dummy product data
products = [
    {"id": 1, "name": "Product 1", "price": 10, "image": "product1.jpg"},
    {"id": 2, "name": "Product 2", "price": 20, "image": "product2.jpg"},
    {"id": 3, "name": "Product 3", "price": 30, "image": "product3.jpg"},
    {"id": 4, "name": "Product 4", "price": 40, "image": "product4.jpg"}
]

# Shopping cart
shopping_cart = []

# Real-time recommendation update
real_time_recommendations = {}

@app.route('/')
def index():
    return render_template('index.html', products=products)

@app.route('/search', methods=['POST'])
def search():
    query = request.form.get('query')
    search_results = [product for product in products if query.lower() in product['name'].lower()]
    return render_template('search_results.html', query=query, search_results=search_results)

@app.route('/add_to_cart/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    product = next((p for p in products if p['id'] == product_id), None)
    if product:
        shopping_cart.append(product)
        publish_event('productclick', {'product_id': product_id, 'user_id': '123'})
        update_real_time_recommendations(product)
    return redirect(url_for('index'))

@app.route('/purchase', methods=['POST'])
def purchase():
    product_id = request.form.get('product_id')
    user_id = '123'  # Replace with actual user ID
    publish_event('purchase', {'product_id': product_id, 'user_id': user_id})
    return redirect(url_for('view_cart'))

@app.route('/checkout', methods=['POST'])
def checkout():
    user_id = '123'  # Replace with actual user ID
    for product in shopping_cart:
        publish_event('purchase', {'product_id': product['id'], 'user_id': user_id})
    shopping_cart.clear()
    return render_template('checkout_success.html')

def publish_event(topic, event_data):
    event_data_json = json.dumps(event_data)
    producer.produce(topic, value=event_data_json.encode('utf-8'))
    producer.flush()

def update_real_time_recommendations(product):
    recommendations = []
    if product['id'] == 1:
        recommendations.append("Get 10% off on Product 2!")
    elif product['id'] == 2:
        recommendations.append("Buy Product 1 along with Product 2 for a discounted price!")
    real_time_recommendations['recommendations'] = recommendations

@app.route('/view_cart')
def view_cart():
    return render_template('cart.html', shopping_cart=shopping_cart)

@app.route('/help')
def help():
    return render_template('help.html')

@app.route('/recommendations')
def get_recommendations():
    def event_stream():
        while True:
            yield f"data: {json.dumps(real_time_recommendations)}\n\n"
    return Response(event_stream(), content_type='text/event-stream')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=9999)
