from flask import Flask, request, render_template, redirect, url_for, session
from werkzeug.security import (
    check_password_hash,
    generate_password_hash,
)

import data_manager

app = Flask(__name__)
app.secret_key = "$2b$12$yxOGxF593XCL.wWfL3xrLbu"

latest_question_id = 0


@app.route("/latest")
def latest_questions_page():
    latest_questions = data_manager.get_latest_questions(5)
    return render_template("base.html", questions=latest_questions)


@app.route("/")
@app.route("/list")
def home_page():
    sort_by = "submission_time"
    sort_direction = "DESC"

    if "sort_by" in request.args and "sort_direction" in request.args:
        sort_by = request.args["sort_by"]
        sort_direction = request.args["sort_direction"]

    questions = data_manager.get_all_data(
        "question",
        sort_by,
        sort_direction,
    )

    return render_template(
        "all_questions.html",
        questions=questions,
        user=session.get("username"),
        sort_direction=sort_direction,
        sort_by=sort_by,
    )


@app.route("/search", methods=["GET", "POST"])
def search():
    search_for = request.form.get("search_for")
    questions = data_manager.search_in_questions(search_for)

    return render_template(
        "search.html",
        search_for=search_for,
        questions=questions,
        user=session.get("username"),
    )


@app.route("/question/<question_id>")
def display_question(question_id):
    global latest_question_id
    latest_question_id = question_id

    question = data_manager.get_question_by_id(question_id)
    answers = data_manager.get_all_answers_by_id_ordered(question_id)
    data_manager.increase_view_number(question_id)

    return render_template(
        "display_question.html",
        question=question,
        answers=answers,
        user=session.get("username"),
    )


@app.route("/add-question", methods=["GET", "POST"])
@data_manager.login_required
def add_new_question():
    if request.method == "POST":
        new_question_data = data_manager.add_new_question()
        new_question_data.update(
            {
                "title": request.form.get("title"),
                "message": request.form.get("message"),
                "image": request.form.get("image"),
            }
        )

        data_manager.write_to_questions(new_question_data)

        return redirect(
            url_for(
                "display_question",
                question_id=new_question_data["id"],
            )
        )

    return render_template("new_question.html", user=session.get("username"))


@app.route("/question/<question_id>/edit", methods=["GET", "POST"])
@data_manager.login_required
def edit_question(question_id):
    if request.method == "POST":
        edited_question_data = {
            "title": request.form.get("question"),
            "message": request.form.get("message"),
            "image": request.form.get("image"),
        }
        data_manager.edit_question(question_id, edited_question_data)

        return redirect(
            url_for(
                "display_question",
                question_id=question_id,
                user=session.get("username"),
            )
        )

    question = data_manager.get_question_by_id(question_id)
    return render_template(
        "edit_question.html",
        question=question,
        user=session.get("username"),
    )


@app.route("/answer/<int:question_id>/new-answer", methods=["GET", "POST"])
@data_manager.login_required
def add_new_answer(question_id):
    if request.method == "POST":
        new_answer = request.form["new_answer"]
        data_manager.add_new_answer(new_answer, question_id)
        return redirect(
            url_for(
                "display_question",
                question_id=question_id,
                user=session.get("username"),
            )
        )

    return render_template(
        "new_answer.html",
        question_id=question_id,
        user=session.get("username"),
    )


@app.route("/answer/<int:answer_id>/edit", methods=["GET", "POST"])
@data_manager.login_required
def edit_answer(answer_id):
    if request.method == "POST":
        question_id = data_manager.get_answer_by_id(answer_id)["question_id"]
        edited_answer_data = {
            "message": request.form.get("message"),
            "image": request.form.get("image"),
        }

        data_manager.edit_answer(answer_id, edited_answer_data)
        return redirect(
            url_for(
                "display_question",
                question_id=question_id,
                user=session.get("username"),
            )
        )

    answer = data_manager.get_answer_by_id(answer_id)
    return render_template(
        "edit_answer.html",
        answer=answer,
        user=session.get("username"),
    )


@app.route("/question/<int:question_id>/delete", methods=["GET", "POST"])
@data_manager.login_required
def delete_question(question_id):
    data_manager.delete_question_by_id(question_id)
    return redirect(url_for("home_page", user=session.get("username")))


@app.route("/answer/<int:answer_id>/delete", methods=["GET", "POST"])
@data_manager.login_required
def delete_answer(answer_id):
    data_manager.delete_answer_by_id(answer_id)
    global latest_question_id
    return redirect(
        url_for(
            "display_question",
            question_id=latest_question_id,
            user=session.get("username"),
        )
    )


@app.route("/questions/<int:question_id>/vote-up", methods=["POST"])
@data_manager.login_required
def question_vote_up(question_id):
    data_manager.vote_up_for_questions(question_id)

    username = dict(data_manager.get_username_from_question_id(question_id))
    reputation = dict(data_manager.select_reputation(username["username"]))
    reputation["reputation"] += 5

    data_rep = {
        "reputation": int(reputation["reputation"]),
        "username": session.get("username"),
    }

    data_manager.update_reputation(data_rep)

    return redirect(
        url_for(
            "display_question",
            question_id=question_id,
            user=session.get("username"),
        )
    )


@app.route("/questions/<int:question_id>/vote-down", methods=["POST"])
@data_manager.login_required
def question_vote_down(question_id):
    data_manager.vote_down_for_questions(question_id)

    username = dict(data_manager.get_username_from_question_id(question_id))
    reputation = dict(data_manager.select_reputation(username["username"]))
    reputation["reputation"] -= 3

    data_rep = {
        "reputation": int(reputation["reputation"]),
        "username": session.get("username"),
    }

    data_manager.update_reputation(data_rep)

    return redirect(
        url_for(
            "display_question",
            question_id=question_id,
            user=session.get("username"),
        )
    )


@app.route("/answers/<int:question_id>/<answer_id>/vote-up", methods=["GET", "POST"])
@data_manager.login_required
def answer_vote_up(question_id, answer_id):
    data_manager.vote_up_for_answers(answer_id)

    username = dict(data_manager.get_username_from_question_id(question_id))
    reputation = dict(data_manager.select_reputation(username["username"]))
    reputation["reputation"] += 7

    data_rep = {
        "reputation": int(reputation["reputation"]),
        "username": session.get("username"),
    }

    data_manager.update_reputation(data_rep)

    return redirect(
        url_for(
            "display_question",
            question_id=question_id,
            user=session.get("username"),
        )
    )


@app.route("/answers/<int:question_id>/<answer_id>/vote-down", methods=["GET", "POST"])
@data_manager.login_required
def answer_vote_down(question_id, answer_id):
    data_manager.vote_down_for_answers(answer_id)

    username = dict(data_manager.get_username_from_question_id(question_id))
    reputation = dict(data_manager.select_reputation(username["username"]))
    reputation["reputation"] -= 4

    data_rep = {
        "reputation": int(reputation["reputation"]),
        "username": session.get("username"),
    }

    data_manager.update_reputation(data_rep)

    return redirect(
        url_for(
            "display_question",
            question_id=question_id,
            user=session.get("username"),
        )
    )


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        password2 = request.form["password2"]

        if data_manager.username_exists(username):
            error_message = "The username you entered is already in use."
            return render_template("register.html", error_message=error_message)

        elif password != password2:
            error_message = "The passwords you entered do not match."
            return render_template("register.html", error_message=error_message)

        hashed_password = generate_password_hash(password=password)

        # split lines here
        uname = data_manager.register_user(username, hashed_password)
        session["username"] = uname.get("username")

        return redirect(url_for("home_page"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if data_manager.username_exists(username):
            user_pass = data_manager.get_password_for_user(username)
            user_pass = user_pass.get("password")

            if check_password_hash(user_pass, password):
                session["username"] = username
                return redirect(url_for("home_page"))

    error_message = "Invalid username or password"

    return render_template("login.html", error_message=error_message)


@app.route("/logout")
@data_manager.login_required
def logout():
    # session.clear()
    session.pop("username", None)

    return redirect(url_for("home_page"))


@app.route("/users")
@data_manager.login_required
def list_users():
    users = data_manager.get_user_attributes()
    return render_template(
        "users.html",
        users=users,
        username=session.get("username"),
    )


@app.route("/users/<username>")
def user_details(username):
    questions = data_manager.get_questions_of_user(username)
    user_attributes = data_manager.get_one_user_attributes(username)
    answers = data_manager.get_answers_of_user(username)

    return render_template(
        "user_page.html",
        username=session.get("username"),
        questions=questions,
        answers=answers,
        user_attributes=user_attributes,
        number_of_questions=len(questions),
        number_of_answers=len(answers),
    )


@app.route("/tags")
def list_tags():
    tags = data_manager.list_tags()
    return render_template("list_tags.html", tags=tags)


if __name__ == "__main__":
    app.run(debug=True)
