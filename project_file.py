from flask import Flask, render_template, redirect, url_for, request
from flask_sqlalchemy import SQLAlchemy
import requests
import re

url='https://meduza.io/api/v3/'
data = requests.get("https://meduza.io/api/v3/search?chrono=news&locale=ru&page=0&per_page=50"
                  ).json()


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgres://postgres:123@localhost/postgres'
db = SQLAlchemy(app)


class NewsPage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.Text)
    body = db.Column(db.Text)

    def __init__(self, title, body):
        self.title = title
        self.body = body



def filter_text(text):
    p = re.compile(r'<.*?>')
    return p.sub('', text)


db.create_all()

def save(my_dict):

    if 'body' in my_dict['root']['content'].keys():
        text = filter_text(str(my_dict['root']['content']['body']))
        db.session.add(NewsPage(str(my_dict['root']['title']), text))
        db.session.commit()


    elif 'blocks' in my_dict['root']['content'].keys():
        if len(my_dict['root']['content']['blocks']) > 2:
            onestr=''
            for i in my_dict['root']['content']['blocks']:
                if type(i['data']) == str:
                    onestr += i['data']

            text = filter_text(onestr)
            db.session.add(NewsPage(str(my_dict['root']['title']), text))
            db.session.commit()

        else:
            text = filter_text(str(my_dict['root']['content']['blocks'][0]['data']['caption']))
            db.session.add(NewsPage(str(my_dict['root']['title']), text))
            db.session.commit()




@app.route('/',methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/news', methods=['GET'])
def news():
    return render_template('news.html', newspages=NewsPage.query.all())


@app.route('/update', methods=['POST'])
def update():
    db.drop_all(bind=None)
    db.create_all()
    for key in data['documents'].keys():
        data1 = requests.get(url + key).json()
        save(data1)

    return redirect(url_for('news'))

@app.route('/add_news', methods=['POST'])
def add_news():
    text = request.form['text']
    data1 = requests.get(url + text[18:]).json()
    save(data1)
    return redirect(url_for('news'))

@app.route('/delete', methods=['POST'])
def delete():
    text = int(request.form['text'])
    x = NewsPage.query.filter_by(id=text).one()
    db.session.delete(x)
    db.session.commit()
    return redirect(url_for('news'))

@app.route('/read', methods=['POST'])
def read():
    text = int(request.form['text'])
    return render_template('read.html', newspages=NewsPage.query.filter_by(id=text).first())




if __name__=='__main__':
    app.run(debug=True)
