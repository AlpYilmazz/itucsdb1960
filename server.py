from flask import Flask


app = Flask(__name__)


@app.route("/")
def home_page():
    return "10.10.2019"


if __name__ == "__main__":
    app.run()
