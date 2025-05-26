from flask import Flask
from flask_restx import Api
from data_models import trip_ns, country_ns, location_ns

app = Flask(__name__)
api = Api(app, title="Travel WebApp BACKEND ")

api.add_namespace(trip_ns, path='/trips')
api.add_namespace(country_ns, path='/countries')
api.add_namespace(location_ns, path='/locations')


if __name__ == '__main__':
    app.run(debug=True)
