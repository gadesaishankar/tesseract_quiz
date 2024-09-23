from flask import Flask, request, render_template, jsonify
import requests as r
import json

app = Flask(__name__)

# Global variables to hold headers, subjects, and units
head = {}
subjects = {}
units = {}

def get_token(token):
    global head
    head = {
        "Authorization": f"Bearer {token}",
        "Referer": "https://tesseractonline.com/"
    }
    response = r.get(url="https://api.tesseractonline.com/studentmaster/subjects/1/2", headers=head).text
    data = json.loads(response)
    return not data['Error']
    
def fetch_subjects():
    global subjects
    subjects = dashboard()

def fetch_units_data(subject_id):
    global units
    url = f"https://api.tesseractonline.com/studentmaster/get-subject-units/{subject_id}"
    response = r.get(url=url, headers=head).text
    l = json.loads(response)

    if 'Error' in l and l['Error']:
        print("Error fetching units:", l['Message'])  # Log any error message
        return

    units_data = l['payload']
    units = {i['unitId']: i['unitName'] for i in units_data}


def getQuiz(i):
    url = f"https://api.tesseractonline.com/quizattempts/create-quiz/{i}"
    res = r.get(url=url, headers=head).text
    return json.loads(res)

def saveQ(Zid, Qid, Opt):
    url = "https://api.tesseractonline.com/quizquestionattempts/save-user-quiz-answer"
    payload = {
        "quizId": f'{Zid}',
        "questionId": f'{Qid}',
        "userAnswer": f'{Opt}'
    }
    save = r.post(url=url, json=payload, headers=head).text
    return save

def submit(a):
    url = "https://api.tesseractonline.com/quizattempts/submit-quiz"
    payload = {
        "branchCode": "CSE",
        "sectionName": "CSE-PS1",
        "quizId": f'{a}'
    }
    submit = r.post(url=url, json=payload, headers=head).text
    return json.loads(submit)

def write_quiz(i):
    try:
        rc = getQuiz(i)
        quizId = rc["payload"]['quizId']
        questions = rc["payload"]["questions"]
        opt = ['a', 'b', 'c', 'd']
        prev = submit(quizId)["payload"]["score"]
        print("Work in progress, please wait")

        for question in questions:
            for answer in opt:
                saveQ(quizId, question['questionId'], answer)
                scr = submit(quizId)["payload"]["score"]
                if scr == 5:
                    print('Test completed, refresh the page')
                    return
                if scr > prev:
                    prev = scr
                    break
    except KeyError:
        print('This subject or topic is inactive')

def dashboard():
    url = "https://api.tesseractonline.com/studentmaster/subjects/1/2"
    l = r.get(url=url, headers=head).text
    l = json.loads(l)
    subjects_data = l['payload']
    subjects = {i['subject_id']: i['subject_name'] for i in subjects_data}
    return subjects

def units(subject_id):
    url = f"https://api.tesseractonline.com/studentmaster/get-subject-units/{subject_id}"
    l = r.get(url=url, headers=head).text
    l = json.loads(l)
    units_data = l['payload']
    units = {i['unitId']: i['unitName'] for i in units_data}
    return units

def topics(a):
    url = f"https://api.tesseractonline.com/studentmaster/get-topics-unit/{a}"
    l = r.get(url=url, headers=head).text
    l = json.loads(l)
    topics_data = l['payload']['topics']
    top = {f"{i['id']}": {'name': i['name'], 'learningFlag': i['learningFlag'], 'pdf': f"https://api.tesseractonline.com{i['pdf']}", 'video': i['videourl']} for i in topics_data}
    return top

def auto_submit_all_topics_in_unit(unit_id):
    topic_list = topics(unit_id)
    for topic_id in topic_list:
        print(f"Writing quiz for topic: {topic_list[topic_id]['name']} (ID: {topic_id})")
        write_quiz(topic_id)

@app.route('/')
def index():
    return render_template('index.html', subjects={})

@app.route('/fetch-subjects', methods=['POST'])
def fetch_subjects_route():
    token = request.form['token']
    if not get_token(token):
        return jsonify({"message": "The given token is expired or may be wrong."})
    fetch_subjects()
    return jsonify(subjects)

@app.route('/fetch-units/<subject_id>', methods=['GET'])
def fetch_units_route(subject_id):
    fetch_units_data(subject_id)
    return jsonify(units)

@app.route('/submit-quiz', methods=['POST'])
def submit_quiz():
    unit_id = request.form['unit_id']
    auto_submit_all_topics_in_unit(unit_id)
    return jsonify({"message": "Quizzes submitted successfully!"})

if __name__ == '__main__':
    app.run(debug=True)
