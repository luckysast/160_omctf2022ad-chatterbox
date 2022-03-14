from model import *
from flask import render_template

def as_dict(data, columns):
    results = [{col: getattr(d, col) for col in columns} for d in data]
    return results

def get_users_id(messages, user_id):
    users_id = set()
    for i in range(len(messages)):
        users_id.add(messages[i]['sender_id'])
        users_id.add(messages[i]['recipient_id'])
    users_id.remove(user_id)
    users_id = list(users_id)
    return users_id

def last_messages(messages, user_id):
    users_id = get_users_id(messages, user_id)
    results = []
    for i in messages:
        for j in users_id:
            if j == i['sender_id'] or j == i['recipient_id']:
                results.append(i)
                users_id.remove(j)
    return results