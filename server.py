from flask import Flask, jsonify, request, render_template

app = Flask(__name__)

import indicators

@app.route("/")
def index():
    return render_template('index.html')

if __name__ == '__main__':
    print("Doc: http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)