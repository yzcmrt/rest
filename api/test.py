from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/api/test', methods=['GET'])
def test():
    return jsonify({"status": "ok", "message": "Test endpoint working"})

if __name__ == '__main__':
    app.run(debug=True)
