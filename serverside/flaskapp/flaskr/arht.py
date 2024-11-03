from flask import Flask, render_template, Flask, jsonify
from flask_mysqldb import MySQL
import pandas as pd

app = Flask(__name__)
app.config['MYSQL_HOST'] = '192.168.1.200'
app.config['MYSQL_USER'] = 'lurker'
app.config['MYSQL_PASSWORD'] = 'LurkPass1'
app.config['MYSQL_DB'] = 'arht_test'
mysql = MySQL(app)

@app.route("/")
def index():
    return render_template("index.html")

#debug data
@app.route("/debug_data")
def raw_data():
    test_dataframe = pd.DataFrame()
    cur = mysql.connection.cursor()
    cur.execute('''select * from study_1 where sens_time > "2024-11-02 10:00:00"''')
    data = cur.fetchall()
    print(type(data)+'\n')
    print(data)
    cur.close()
    return jsonify(data)


if __name__ == "__main__":
    app.run(host='0.0.0.0')