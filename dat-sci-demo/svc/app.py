"""Demo Flask app. It loads a trained model and returns a prediction."""
import logging
import numpy as np
from flask import Flask, request, jsonify
from sklearn.externals import joblib

app = Flask(__name__)

log = logging.getLogger('werkzeug')

# load the trained model (classifier)
clf = joblib.load('trained_classifier.pkl')

# map of class numbers to names
class_names = {
    0: 'setosa',
    1: 'versicolor',
    2: 'virginica',
}


@app.route("/", methods=['GET'])
def index():
    """Returns a predicted class to which an iris belongs based on
    sepal length and width.

    Sample usage:

        $ curl -s http://localhost:5001\?length\=5.8\&width\=3.4 | jq
        {
        "predicted_class": "versicolor",
        "sepal_length": 5.8,
        "sepal_width": 3.4
        }
    """

    length = float(request.args.get('length'))
    width = float(request.args.get('width'))

    test_pt = np.array((length, width)).reshape(1, -1)

    class_num = clf.predict(test_pt)[0]

    predicted_class = class_names[class_num]

    return jsonify({
        "sepal_length": length,
        "sepal_width": width,
        "predicted_class": predicted_class
    })


if __name__ == "__main__":
    app.run(host='0.0.0.0')
