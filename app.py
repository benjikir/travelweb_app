from flask import Flask
from data_manager.sqlite_data_manager import SQLiteDataManager

app = Flask(__name__)
data_manager = SQLiteDataManager()



#Routes

@app.route('/')
def home():
    return "Welcome to the Travel App!"


'''
@app.route()
def get_countries():





@app.route()
def user_countries():
    


@app.route()
def update_countries():




@app.route('')
def delete_country():

'''




if __name__ == '__main__':
    app.run(debug=True, port=5000)