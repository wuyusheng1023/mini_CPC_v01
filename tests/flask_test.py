from flask import Flask
app = Flask(__name__)

@app.route("/")
def hello():
    return "<h1>Here's Chenran's Family!<h1>"

if __name__ == '__main__':
 	app.run(debug=True, host='0.0.0.0', port=80)