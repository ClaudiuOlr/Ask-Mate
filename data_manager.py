import connection_manager
from datetime import datetime
from flask import url_for, session, redirect
from functools import wraps


@connection_manager.connection_handler
def get_all_answers(cursor):
    cursor.execute("""SELECT * FROM answer;""")
    return cursor.fetchall()


@connection_manager.connection_handler
def get_all_questions(cursor):
    cursor.execute("""SELECT * FROM question;""")
    return cursor.fetchall()


@connection_manager.connection_handler
def get_all_data(cursor, table, order_by, direction):
    cursor.execute(
        f"""
                    SELECT * FROM {table}
                    ORDER BY {order_by} {direction}
                    """
    )

    return cursor.fetchall()


@connection_manager.connection_handler
def get_latest_questions(cursor, number_of_questions):
    cursor.execute(
        """SELECT * FROM question
                      ORDER BY submission_time DESC
                      LIMIT %(number_of_questions)s;
        """,
        {"number_of_questions": number_of_questions},
    )
    return cursor.fetchall()


@connection_manager.connection_handler
def get_next_question_id(cursor):
    # https://www.postgresqltutorial.com/postgresql-coalesce/
    cursor.execute("""SELECT COALESCE(0, MAX(id)) AS max from question;""")
    return cursor.fetchone()["max"] + 1


@connection_manager.connection_handler
def get_next_answer_id(cursor):
    # https://www.postgresqltutorial.com/postgresql-coalesce/
    cursor.execute("""SELECT COALESCE(0, MAX(id)) AS max from answer;""")
    return cursor.fetchone()["max"] + 1


@connection_manager.connection_handler
def get_question_by_id(cursor, question_id):
    cursor.execute(
        """SELECT id, submission_time, view_number, vote_number, title, message, image, username FROM question
                      WHERE id=%(id)s;""",
        {"id": question_id},
    )
    return cursor.fetchone()


@connection_manager.connection_handler
def get_answer_by_id(cursor, answer_id):
    cursor.execute(
        """SELECT id, submission_time, vote_number, question_id, message, image, username FROM answer
                      WHERE id=%(id)s;""",
        {"id": answer_id},
    )
    return cursor.fetchone()


@connection_manager.connection_handler
def get_answers_by_question_id(cursor, question_id):
    cursor.execute(
        """SELECT id, submission_time, vote_number, question_id, message, image, username FROM answer
                      WHERE question_id=%(id)s;""",
        {"id": question_id},
    )
    return cursor.fetchall()


@connection_manager.connection_handler
def sort_questions_by_time(cursor):
    cursor.execute(
        """SELECT title, id FROM question
                      ORDER BY submission_time DESC;"""
    )
    return cursor.fetchall()


@connection_manager.connection_handler
def search_in_questions(cursor, search_for):
    cursor.execute(
        """
                    SELECT DISTINCT question.id AS id, question.submission_time AS submission_time , question.view_number AS view_number, question.vote_number AS vote_number, question.title AS title, question.message AS message, question.image AS image, answer.id AS a_id, answer.question_id AS a_question_id, answer.submission_time AS a_submission_time, answer.vote_number AS a_vote_number, answer.message AS a_message, answer.image AS a_image 
                    FROM question
                    LEFT JOIN answer
                    ON question.id = answer.question_id
                    WHERE question.title LIKE %(search_for)s 
                    OR question.message LIKE %(search_for)s 
                    OR answer.message LIKE %(search_for)s;
                   """,
        {"search_for": "%" + search_for + "%"},
    )

    return cursor.fetchall()


@connection_manager.connection_handler
def edit_question(cursor, question_id, edited_data):
    cursor.execute(
        """UPDATE question SET
            submission_time = %(submission_time_value)s,
            title = %(title_value)s, 
            message = %(message_value)s,
            image = %(image_value)s
            WHERE id=%(id)s;
        """,
        {
            "submission_time_value": datetime.now().replace(microsecond=0),
            "title_value": edited_data["title"],
            "message_value": edited_data["message"],
            "image_value": edited_data["image"],
            "id": question_id,
        },
    )


@connection_manager.connection_handler
def edit_answer(cursor, answer_id, edited_data):
    cursor.execute(
        """UPDATE answer SET
            submission_time = %(submission_time_value)s,
            message = %(message_value)s,
            image = %(image_value)s
            WHERE id=%(id)s;
        """,
        {
            "submission_time_value": datetime.now().replace(microsecond=0),
            "message_value": edited_data["message"],
            "image_value": edited_data["image"],
            "id": answer_id,
        },
    )


@connection_manager.connection_handler
def delete_question_by_id(cursor, question_id):
    cursor.execute(
        """
        DELETE FROM comment WHERE question_id=%(id)s;
        SELECT id FROM answer WHERE question_id=%(id)s;""",
        {"id": question_id},
    )
    answer_ids = cursor.fetchall()
    for answer_id in answer_ids:
        delete_answer_by_id(answer_id["id"])

    cursor.execute(
        """DELETE FROM question WHERE id=%(id)s;""",
        {"id": question_id},
    )


@connection_manager.connection_handler
def delete_answer_by_id(cursor, answer_id):
    cursor.execute(
        """
        DELETE FROM comment WHERE answer_id=%(id)s;
        DELETE FROM answer WHERE id=%(id)s;
        """,
        {"id": answer_id},
    )


@connection_manager.connection_handler
def get_all_answers_by_id_ordered(cursor, question_id):
    cursor.execute(
        """SELECT * FROM answer
            WHERE question_id=%(id)s
            ORDER BY vote_number DESC;
        """,
        {"id": question_id},
    )
    return cursor.fetchall()


@connection_manager.connection_handler
def write_to_answers(cursor, data):
    cursor.execute(
        """INSERT INTO answer (id, submission_time, vote_number, question_id, message, image, username) 
            VALUES (%(id_value)s, %(submission_time_value)s, %(vote_number_value)s, 
                    %(question_id_value)s, %(message_value)s, %(image_value)s, %(username)s);""",
        {
            "id_value": data["id"],
            "submission_time_value": data["submission_time"],
            "vote_number_value": data["vote_number"],
            "question_id_value": data["id"],
            "message_value": data["message"],
            "image_value": data["image"],
            "username": session.get("username"),
        },
    )


@connection_manager.connection_handler
def write_to_questions(cursor, data):
    print(data)
    cursor.execute(
        """INSERT INTO question (id, submission_time, view_number, vote_number, title, message, image, username) 
            VALUES (%(id_value)s, %(submission_time_value)s, %(view_number)s, %(vote_number_value)s, %(title)s,  
                     %(message_value)s, %(image_value)s, %(username)s);""",
        {
            "id_value": data["id"],
            "submission_time_value": data["submission_time"],
            "view_number": data["view_number"],
            "vote_number_value": data["vote_number"],
            "title": data["title"],
            "message_value": data["message"],
            "image_value": data["image"],
            "username": session.get("username"),
        },
    )


@connection_manager.connection_handler
def vote_up_for_questions(cursor, question_id):
    cursor.execute(
        """UPDATE question SET
            vote_number = vote_number + 1
            WHERE id=%(id)s;
        """,
        {"id": int(question_id)},
    )


@connection_manager.connection_handler
def vote_down_for_questions(cursor, question_id):
    cursor.execute(
        """UPDATE question SET
            vote_number = vote_number - 1
            WHERE id=%(id)s;
        """,
        {"id": int(question_id)},
    )


@connection_manager.connection_handler
def vote_up_for_answers(cursor, answer_id):
    cursor.execute(
        """UPDATE answer SET
            vote_number = vote_number + 1
            WHERE id = %(id)s;
        """,
        {"id": answer_id},
    )


@connection_manager.connection_handler
def vote_down_for_answers(cursor, answer_id):
    cursor.execute(
        """UPDATE answer SET
            vote_number = vote_number - 1
            WHERE id = %(id)s;
        """,
        {"id": answer_id},
    )


def add_new_question():
    new_question_data = {
        "id": get_next_question_id(),
        "submission_time": datetime.now().replace(microsecond=0),
        "view_number": "0",
        "vote_number": "0",
    }
    return new_question_data


def add_new_answer(new_answer, question_id):
    new_data = {
        "id": get_next_answer_id(),
        "submission_time": datetime.now().replace(microsecond=0),
        "vote_number": "0",
        "question_id": question_id,
        "message": new_answer,
        "image": "",
    }
    write_to_answers(new_data)


def generate_time():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


@connection_manager.connection_handler
def register_user(cursor, username, password):
    date = generate_time()
    cursor.execute(
        """insert into users (username, password, registration) values (%(username)s, %(password)s, %(date)s) returning username;""",
        {"username": username, "password": password, "date": date},
    )
    return cursor.fetchone()


@connection_manager.connection_handler
def get_password_for_user(cursor, username):
    cursor.execute(
        """select password from users where username=%(username)s;""",
        {"username": username},
    )
    return cursor.fetchone()


@connection_manager.connection_handler
def get_user_attributes(cursor):
    cursor.execute("""SELECT * FROM users ORDER BY username""")
    return cursor.fetchall()


@connection_manager.connection_handler
def get_one_user_attributes(cursor, username):
    cursor.execute(
        """SELECT id, username, registration, asked, answered, reputation FROM users 
            WHERE username = %(username)s""",
        {"username": username},
    )
    return cursor.fetchone()


@connection_manager.connection_handler
def get_questions_of_user(cursor, username):
    cursor.execute(
        """SELECT submission_time, view_number, vote_number, title, message, image FROM question 
            WHERE username=%(username)s""",
        {"username": username},
    )
    return cursor.fetchall()


@connection_manager.connection_handler
def get_answers_of_user(cursor, username):
    cursor.execute(
        """SELECT submission_time, vote_number, question_id, message, image FROM answer 
            WHERE username=%(username)s""",
        {"username": username},
    )
    return cursor.fetchall()


@connection_manager.connection_handler
def list_tags(cursor):
    cursor.execute(
        """
        SELECT tag.name, COUNT(qt.question_id) as number_of_questions FROM tag
        LEFT JOIN question_tag qt on tag.id = qt.tag_id
        GROUP BY tag.name;
    """
    )
    return cursor.fetchall()


def login_required(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        if "username" in session:
            return function(*args, **kwargs)
        else:
            return redirect(url_for("login"))

    return wrapper


@connection_manager.connection_handler
def select_reputation(cursor, username):
    cursor.execute(
        """
            SELECT reputation FROM users
            WHERE username=%(username)s;
        """,
        {"username": username},
    )
    return cursor.fetchone()


@connection_manager.connection_handler
def update_reputation(cursor, data):
    cursor.execute(
        """
        UPDATE users
        SET reputation = %(reputation)s
        WHERE username = %(username)s;
        """,
        data, # already have dictionary
    )


@connection_manager.connection_handler
def get_username_from_question_id(cursor, question_id):
    cursor.execute(
        """
        SELECT username FROM question 
        WHERE id=%(question_id)s;""",
        {"question_id": question_id},
    )
    return cursor.fetchone()


@connection_manager.connection_handler
def username_exists(cursor, username):
    cursor.execute("SELECT username FROM users;")
    list_of_all_user_names = [user["username"] for user in cursor.fetchall()]

    return username in list_of_all_user_names


@connection_manager.connection_handler
def increase_view_number(cursor, question_id):
    cursor.execute(
        """
        UPDATE question SET
            view_number = (SELECT view_number FROM question WHERE id = %(question_id)s) + 1
            WHERE id=%(question_id)s;""",
        {"question_id": question_id},
    )
