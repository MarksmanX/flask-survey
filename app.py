from flask import Flask, render_template, redirect, flash, request, session, make_response
from flask_debugtoolbar import DebugToolbarExtension
from surveys import surveys

CURRENT_SURVEY_KEY = 'current-survey'
RESPONSES_KEY = "responses"

app = Flask(__name__)

app.debug = True
app.config['SECRET_KEY'] = 'secret'
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False

debug = DebugToolbarExtension(app)

@app.route('/')
def show_survey_pick_form():
    """Show pick-a-survey form."""

    return render_template('startpage.html', surveys=surveys)


@app.route("/", methods=["POST"])
def pick_survey():
    """Select a survey."""

    survey_id = request.form['survey_code']
    survey = surveys[survey_id]
    session[CURRENT_SURVEY_KEY] = survey_id

    # don't let them re-take a survey until cookie times out
    if request.cookies.get(f"completed_{survey_id}"):
        return render_template("already-done.html", survey=survey)

    return render_template("survey-start.html", survey=survey)

@app.route('/begin', methods=["POST"])
def begin_survey():
    """Clear the session of responses"""

    session[RESPONSES_KEY] = []

    return redirect("/questions/0")


@app.route("/questions/<int:qid>")
def show_question(qid):
    """Display current question"""
    responses = session.get(RESPONSES_KEY)
    survey_code = session[CURRENT_SURVEY_KEY]
    survey = surveys[survey_code]

    if (responses is None):
        # trying to access question page too soon
        return redirect("/")
    
    if (len(responses) == len(survey.questions)):
        # They've answered all the questions! thank them.
        return redirect("/complete")
    
    if (len(responses) != qid):
        #Trying to access questions out of order.
        flash(f"Invalid question id: {qid}.")
        return redirect(f"/questions/{len(responses)}")
    
    question = survey.questions[qid]

    return render_template("question.html",
                           question_num=qid,
                           question=question)


@app.route('/answer', methods=["POST"])
def handle_question():
    """Save response and redirect to next question."""

    #get the response choice
    choice = request.form['answer']
    text = request.form.get("text", "")

    #add this response to the session
    responses = session[RESPONSES_KEY]
    responses.append({"choice": choice, "text": text})

    # add this response to the session
    session[RESPONSES_KEY] = responses
    survey_code = session[CURRENT_SURVEY_KEY]
    survey = surveys[survey_code]

    if (len(responses) == len(survey.questions)):
        #They've answered all the questions! Thank them.
        return redirect("/complete")
    
    else: return redirect(f"/questions/{len(responses)}")


@app.route("/complete")
def complete():
    """Thank user and list responses"""

    survey_id = session[CURRENT_SURVEY_KEY]
    survey = surveys[survey_id]
    responses = session[RESPONSES_KEY]

    html = render_template("completion.html",
                           survey=survey,
                           responses=responses)

    # Set cookie noting this survey is dones so they can't re-do it
    response = make_response(html)
    response.set_cookie(f"completed_{survey_id}", "yes", max_age=60)
    return response