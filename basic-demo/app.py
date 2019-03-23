"""Demo Flask app."""
import sys
import platform
import logging
from argparse import ArgumentParser
from flask import Flask, jsonify

app = Flask(__name__)

# limit logging to errors only
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)


@app.route("/")
def index():
    """Returns values of platform (OS), Python version, and the value of
    a string passed in at runtime to be the value of 'color'."""
    return jsonify({
        "platform": platform.platform(),
        "python_version": sys.version,
        "color": app.config['color']
    })


if __name__ == "__main__":

    # the app takes in a string as command line arg "color"
    parser = ArgumentParser()
    parser.add_argument('color')
    args = parser.parse_args()

    # set the passed-in string as the value of "color" in the app's config
    app.config['color'] = args.color

    # run the Flask app
    app.run(host='0.0.0.0')
