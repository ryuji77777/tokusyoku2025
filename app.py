from flask import Flask, render_template, request, redirect, url_for, session
import json

app = Flask(__name__)
app.secret_key = 'secret_key_for_session'

# JSON読み込み
with open('decision_tree.json', encoding='utf-8') as f:
    tree = json.load(f)


@app.route('/')
def index():
    session['merged_data'] = {
        "next": "start",
        "comments": [],
        "meal": [],
        "risk_score": 0
    }
    return redirect(url_for('question', node_id='start'))


@app.route('/question/<node_id>', methods=['GET', 'POST'])
def question(node_id):
    node = tree.get(node_id)

    # POST: 回答受け取り
    if request.method == 'POST':
        merged_data = session.get('merged_data', {
            "next": node_id,
            "comments": [],
            "meal": [],
            "risk_score": 0
        })

        qtype = node.get('type', 'single')
        selected_choices = []

        if qtype == 'single':
            value = request.form.get('answer')
            choice_data = node['choices'].get(value, {})
            selected_choices.append(choice_data)

        elif qtype == 'multiple':
            values = request.form.getlist('answer')
            for v in values:
                selected_choices.append(node['choices'].get(v, {}))

        elif qtype == 'multi_single':
            for sub_id, subq in node.get('subquestions', {}).items():
                value = request.form.get(sub_id)
                if value:
                    selected_choices.append(subq['choices'].get(value, {}))

        # コメントとリスクスコアを更新
        for c in selected_choices:
            if c.get('comment'):
                merged_data['comments'].append(c['comment'])
            if c.get('meal'):
                merged_data['meal'].append(c['meal'])
            merged_data['risk_score'] += c.get('risk', 0)
        for c in selected_choices:
            # 修正済
            if 'comment' in c:
                merged_data['comments'].append(c['comment'])
            if 'meal' in c:
                merged_data['meal'].append(c['meal'])
            if 'risk' in c:
                merged_data['risk_score'] += c['risk']

        # 次のノード決定
        next_node = None
        go_result = False
        for c in selected_choices:
            if c.get('next') == 'result':
                go_result = True
            elif c.get('next'):
                next_node = c.get('next')

        merged_data['next'] = 'result' if go_result else next_node or node_id

        # セッション保存
        session['merged_data'] = merged_data

        # 開発用 print("DEBUG merged_data:", merged_data)とcookie
        print('merged_data', merged_data)
        print("DEBUG session size:", len(json.dumps(session.get('merged_data', {}))))

        return redirect(url_for('question', node_id=merged_data['next']))

    # GET: 質問表示
    merged_data = session.get('merged_data', {
        "next": node_id,
        "comments": [],
        "risk_score": 0
    })

    if 'result' in node or merged_data.get('next') == 'result':
        comments = merged_data.get('comments', []).copy()
        meals = merged_data.get('meal', []).copy()

        # risk_score > 0 の場合はコメントを追加
        if merged_data.get('risk_score', 0) > 0:
            comments.append("心血管リスクあり、心エコーなどの検査を検討")
            comments.append("検査で心不全所見があれば心臓食を検討")

        # 特食なしでコメントが空なら一般食推奨
        if not meals and not comments:
            meals = ["一般食を継続、または内科医に相談"]   # comment?

        return render_template(
            'result.html',
            meals=meals,
            comments=comments
        )

    return render_template(
        'question.html',
        node_id=node_id,
        question=node['question'],
        choices=node.get('choices', {}),
        subquestions=node.get('subquestions', {}),
        qtype=node.get('type', 'single')
    )


if __name__ == '__main__':
    app.run(debug=True)
