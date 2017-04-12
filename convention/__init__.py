import flask

from convention import api


app = flask.Flask(__name__)
app.register_blueprint(api.api, url_prefix="/api")


@app.route("/")
def hello_world():
    return "Hello, World!"


if __name__ == "__main__":
    app.run(debug=True)
