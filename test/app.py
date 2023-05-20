from flask import Flask, jsonify, request

app = Flask(__name__)

@app.route('/')
def home():
    return "Welcome to our server!"

@app.route('/api/data', methods=['GET'])
def get_data():
    data = {"key": "value"}  # just a simple stub
    return jsonify(data)

@app.route('/api/data', methods=['POST'])
def post_data():
    data = request.get_json()  # assume you're receiving JSON data
    # ... do something with the data ...
    return jsonify({"message": "Received data!"}), 200

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5050)
