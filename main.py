import datetime

from flask import Flask, render_template, request, jsonify
import json

app = Flask(__name__)

from google.cloud import datastore

datastore_client = datastore.Client()

def store_message(text, quote):
    entity = datastore.Entity(key=datastore_client.key('quote', quote , 'message'))
    created_at = datetime.datetime.now()
    entity.update({
        'text': text,
        'created_at': created_at
    })

    datastore_client.put(entity)

def store_comment(comments, quote):
    key = datastore_client.key('quote', str(quote))
    quote = datastore_client.get(key)

    for prop in quote:
        quote[prop] = quote[prop]

    quote['comments'] = comments
    datastore_client.put(quote)

# def store_quote(text, page):
#     created_at = datetime.datetime.now()
#     q_id = created_at.strftime("%Y%m%d%H%M%S")
#     key = datastore_client.key('quote', str(q_id))
#     entity = datastore.Entity(key)
    
#     entity.update({
#         'text': text,
#         'novel': "The Hitchhiker's Guide to the Galaxy",
#         'page_nr': page,
#         'created_at': created_at,
#         'created_by': 'admin',
#         'quote_key': key,
#         'comments': []
#     })

#     datastore_client.put(entity)


def fetch_quotes(limit):
    query = datastore_client.query(kind='quote')
    #query.order = ['+created_at']

    quotes = query.fetch(limit=limit)

    return quotes

@app.route('/')
def root():
    return render_template('index.html')

@app.route('/error/<string:err_type>')
def error(err_type):
    if err_type == 'too-much':
        text = 'More than 3000 characters? Looks like overkill...'
    elif err_type == 'not-enough':
        text = 'Less than three characters... meh.'
    else:
        text = 'Boiiiii... Not found. :('
        err_type = 'not-found'

    img_path = "img/" + err_type
    error = {"text":text, "img":img_path}

    return render_template('error.html', error = error)

@app.route('/api/quotes', methods=['GET'])
def get_quotes():
    d = datetime.datetime.now() + datetime.timedelta(hours=1)
    curr_month=int(d.strftime("%m"))
    quotes = {"quotes": []}

    if curr_month == 12:
        daysInMonth = int(d.strftime("%d"))
        q_iter = fetch_quotes(daysInMonth)

        for q in q_iter:
            full_key = q['quote_key'].__dict__
            q['quote_key'] = full_key['_path'][0]['name']
            quotes["quotes"].append(q)

    return jsonify(quotes), 200

@app.route('/api/currtime', methods=['GET'])
def get_server_time():
    d = datetime.datetime.now() + datetime.timedelta(hours=1)
    curr_time=d.strftime("%m/%d/%Y, %H:%M:%S")
    return curr_time

@app.route('/api/sendThought/<int:quote_id>', methods=['POST'])
def send_thoughts(quote_id):
    thoughts = request.json['thoughts']
    user = request.json['user']

    if user == "zaphod":
        created_at = datetime.datetime.now()
        thoughts[len(thoughts)-1]['created_at'] = created_at
        store_comment(thoughts, quote_id)
        return 'comment', 200
    elif user == "arthur":
        created_at = datetime.datetime.now()
        message = thoughts[len(thoughts)-1]['text']
        store_message(message, quote_id)
        return 'message', 200
    else:
        return 'Vogons are not welcomed on this ship.', 403


    

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8081, debug=True)
