# app.py

from flask import Flask, render_template, request, redirect, url_for, session
import json

app = Flask(__name__)
app.secret_key = 'secret_key_for_session'

with open('decision_tree.json', encoding='utf-8') as f:
    tree = json.load(f)


@app.route('/')
def index():
    session['comments'] = []
    return redirect(url_for('question', node_id='start'))


@app.route('/question/<node_id>')
def question(node_id):
    node = tree.get(node_id)
    if 'result' in node:
        return render_template('result.html', result=node['result'], comments=session.get('comments', []))

    return render_template(
        'question.html',
        node_id=node_id,
        question=node['question'],
        choices=node['choices'],
        qtype=node.get('type', 'single'),
        next_node=node.get('next', 'result')
    )


@app.route('/answer', methods=['POST'])
def answer():
    node_id = request.form['node_id']
    qtype = request.form['qtype']
    comments = session.get('comments', [])

    if qtype == 'single':
        value = request.form['choice']
        comment, next_node = parse_value(value)
        if comment:
            comments.append(comment)
        session['comments'] = comments
        return redirect(url_for('question', node_id=next_node))

    elif qtype == 'multiple':
        selected = request.form.getlist('choices')
        for val in selected:
            comment, _ = parse_value(val)
            if comment:
                comments.append(comment)
        session['comments'] = comments
        next_node = request.form.get('next_node', 'result')
        return redirect(url_for('question', node_id=next_node))

    return redirect(url_for('index'))


def parse_value(value):
    # 形式: comment〇〇|次ノードID または comment〇〇 / ノードIDだけ
    if '|' in value:
        left, right = value.split('|', 1)
        comment = left.replace('comment', '', 1) if left.startswith('comment') else None
        return comment, right
    elif value.startswith('comment'):
        return value.replace('comment', '', 1), 'result'
    else:
        return None, value


if __name__ == '__main__':
    app.run(debug=True)
