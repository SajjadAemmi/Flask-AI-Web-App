import os
import bcrypt
from dotenv import load_dotenv
import numpy as np
from PIL import Image
from flask import (
    Flask,
    jsonify,
    flash,
    render_template,
    request,
    redirect,
    url_for,
    session,
)

from sqlmodel import Session, select
from database import get_user_by_username, create_user, engine, User, Comment, Topic
from models import LoginModel, RegisterModel
from src.face_analysis import FaceAnalysis
from src.object_detection import YOLOv8
from utils.image import encode_image
from utils.data import relative_time, allowed_file
import config


load_dotenv()


app = Flask("AI Web App")
app.secret_key = os.getenv("SECRET_KEY")
app.config["UPLOAD_FOLDER"] = "./uploads"

face_analysis = FaceAnalysis(
    config.face_detection_onnx_model_path, config.age_gender_estimation_onnx_model_path
)
object_detector = YOLOv8(config.object_detection_onnx_model_path)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")
    elif request.method == "POST":
        try:
            login_data = LoginModel(
                username=request.form["username"], password=request.form["password"]
            )
        except:
            flash("Type error", "warning")
            return redirect(url_for("login"))

        user = get_user_by_username(login_data.username)
        if user:
            password_byte = login_data.password.encode("utf-8")
            if bcrypt.checkpw(password_byte, bytes(user.password, "utf-8")):
                flash("خوش اومدی", "success")
                session["user_id"] = user.id
                session["user_username"] = user.username
                return redirect(url_for("profile"))
            else:
                flash("در وارد کردن گذرواژه بیشتر دقت کن", "danger")
                return redirect(url_for("login"))
        else:
            flash("در وارد کردن نام کاربری بیشتر دقت کن", "danger")
            return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")
    elif request.method == "POST":
        try:
            register_data = RegisterModel(
                city=request.form["city"],
                username=request.form["username"],
                password=request.form["password"],
            )
        except:
            flash("Type error")
            return redirect(url_for("register"))

        with Session(engine) as db_session:
            statement = select(User).where(User.username == register_data.username)
            result = db_session.exec(statement).first()

        if not result:
            password_byte = register_data.password.encode("utf-8")
            password_hash = bcrypt.hashpw(password_byte, bcrypt.gensalt())
            password_hash = password_hash.decode("utf8")
            create_user(register_data.username, password_hash)
            flash("از اینکه در وب‌اپ هوش مصنوعی ثبت نام کردی ازت ممنونم", "success")
            return redirect(url_for("login"))
        else:
            flash(
                "این نام کاربری قبلا استفاده شده دوست من، یک نام کاربری دیگه انتخاب کن",
                "danger",
            )
            return redirect(url_for("register"))


@app.route("/logout")
def logout():
    session.pop("user_id")
    return redirect(url_for("index"))


@app.route("/profile", methods=["GET", "POST"])
def profile():
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("login"))

    with Session(engine) as db_session:
        user = db_session.get(User, user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404

        return render_template("profile.html", username=user.username)


@app.route("/ai-face-analysis", methods=["GET", "POST"])
def ai_face_analysis():
    if session.get("user_id"):
        if request.method == "GET":
            return render_template("ai_face_analysis.html")
        elif request.method == "POST":
            input_image_file = request.files["image"]
            if input_image_file.filename == "":
                return redirect(url_for("upload"))
            else:
                if input_image_file and allowed_file(input_image_file.filename):
                    input_image = Image.open(input_image_file.stream)
                    input_image = np.array(input_image)
                    output_image, genders, ages = face_analysis(input_image)
                    image_uri = encode_image(output_image)
                    return render_template(
                        "ai_face_analysis.html",
                        genders=genders,
                        ages=ages,
                        image_uri=image_uri,
                    )
    else:
        return redirect(url_for("login"))


@app.route("/ai-object-detection", methods=["GET", "POST"])
def ai_object_detection():
    if session.get("user_id"):
        if request.method == "GET":
            return render_template("ai_object_detection.html")
        elif request.method == "POST":
            input_image_file = request.files["image"]
            if input_image_file.filename == "":
                return redirect(url_for("upload"))
            else:
                if input_image_file and allowed_file(input_image_file.filename):
                    input_image = Image.open(input_image_file.stream)
                    input_image = np.array(input_image)
                    output_image, labels = object_detector(input_image)
                    image_uri = encode_image(output_image)
                    return render_template(
                        "ai_object_detection.html", labels=labels, image_uri=image_uri
                    )
    else:
        return redirect(url_for("login"))


@app.route("/ai-pose-detection", methods=["GET"])
def ai_pose_detection():
    if session.get("user_id"):
        return render_template("ai_pose_detection.html")
    else:
        return redirect(url_for("login"))


@app.route("/mind-reader")
def mind_reader():
    return render_template("mind_reader.html")


@app.route("/mind-reader-process", methods=["POST"])
def mind_reader_process():
    x = request.form["number"]
    return redirect(url_for("mind_reader_result", number=x))


@app.route("/mind-reader-result")
def mind_reader_result():
    number = request.args.get("number")
    return render_template("mind_reader_result.html", number=number)


@app.route("/blog")
def blog():
    with Session(engine) as db_session:
        statement = select(Topic)
        topics = list(db_session.exec(statement))

    # for topic in topics:
    #     topic.timestamp = relative_time(topic.timestamp)

    return render_template("blog.html", topics=topics)


@app.route("/blog/<int:topic_id>")
def blog_topic(topic_id):
    with Session(engine) as db_session:
        topic = db_session.query(Topic).filter_by(id=topic_id).first()
        return render_template("topic.html", topic=topic)


@app.route("/admin")
def admin():
    # user_id = session.get('user_id')
    # role = session.get('role')
    # if not user_id or role != "Admin":
    #     return redirect(url_for('login'))

    with Session(engine) as db_session:
        statement = select(User)
        users = list(db_session.exec(statement))

    for user in users:
        user.join_time = relative_time(user.join_time)

    return render_template("admin.html", users=users)


@app.route("/admin/blog")
def admin_blog():
    # user_id = session.get('user_id')
    # role = session.get('role')
    # if not user_id or role != "Admin":
    #     return redirect(url_for('login'))

    with Session(engine) as db_session:
        statement = select(Topic)
        topics = list(db_session.exec(statement))

    # for topic in topics:
        # topic.timestamp = relative_time(topic.timestamp)

    return render_template("admin_blog.html", topics=topics)


@app.route("/admin/blog/add-topic", methods=["GET", "POST"])
def admin_blog_add_topic():
    user_id = session.get("user_id")
    # role = session.get('role')
    # if not user_id or role != "Admin":
    #     return redirect(url_for('login'))

    if request.method == "GET":
        return render_template("admin_blog_add_topic.html")
    elif request.method == "POST":
        topic = Topic(
            title=request.form["title"],
            body=request.form["body"],
            user_id=user_id,
            image="",
        )
        with Session(engine) as db_session:
            db_session.add(topic)
            db_session.commit()
        return redirect(url_for("admin_blog"))
    
@app.route("/admin/blog/edit-topic/<int:topic_id>", methods=["GET", "POST"])
def admin_blog_edit_topic(topic_id):
    user_id = session.get("user_id")

    with Session(engine) as db_session:
        topic = db_session.query(Topic).filter_by(id=topic_id).first()

        if request.method == "GET":
            if topic:
                return render_template("admin_blog_edit_topic.html", topic=topic)
            else:
                return "Topic not found", 404
        
        elif request.method == "POST":
            if topic:
                topic.title = request.form["title"]
                topic.body = request.form["body"]
                db_session.commit()
                return redirect(url_for("admin_blog"))
            else:
                return "Topic not found", 404


@app.route("/admin/blog/delete-topic/<int:topic_id>", methods=["POST"])
def admin_blog_delete_topic(topic_id):
    with Session(engine) as db_session:
        topic = db_session.query(Topic).filter_by(id=topic_id).first()

        if topic:
            db_session.delete(topic)
            db_session.commit()
            return redirect(url_for("admin_blog"))
        else:
            return "Topic not found", 404


@app.route("/add-new-comment", methods=["POST"])
def add_new_comment():
    text = request.form["text"]
    with Session(engine) as db_session:
        new_comment = Comment(user_id=session.get("user_id"), content=text)
        db_session.add(new_comment)
        db_session.commit()
    return redirect(url_for("ai_face_analysis"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
