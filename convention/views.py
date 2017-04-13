import convention


@convention.app.route("/")
def hello_world():
    return "Hello, World!"
