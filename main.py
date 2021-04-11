# Copyright 2018 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# [START gae_python38_render_template]
# [START gae_python3_render_template]
import os

from flask import (
    Flask,
    request,
    redirect,
    url_for,
    render_template,
    send_from_directory,
)
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tmp")
# UPLOAD_FOLDER = "/tmp/"
ALLOWED_EXTENSIONS = {"pdf"}

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/", methods=["GET", "POST"])
def root():
    if request.method == "POST":
        if "file1" not in request.files:
            print("No left file attached in request")
            return redirect(request.url)
        if "file2" not in request.files:
            print("No right file attached in request")
            return redirect(request.url)
        file1 = request.files["file1"]
        file2 = request.files["file2"]
        if file1.filename == "":
            print("No left file selected")
            return redirect(request.url)
        if file2.filename == "":
            print("No right file selected")
            return redirect(request.url)
        if (file1 and allowed_file(file1.filename)) and (
            file2 and allowed_file(file2.filename)
        ):
            filename1 = secure_filename(file1.filename)
            filename2 = secure_filename(file2.filename)
            file_path1 = os.path.join(app.config["UPLOAD_FOLDER"], filename1)
            file1.save(file_path1)
            file_path2 = os.path.join(app.config["UPLOAD_FOLDER"], filename2)
            file2.save(file_path2)
            # process_file(os.path.join(app.config["UPLOAD_FOLDER"], filename), filename)
            return redirect(url_for("uploaded_file"))
    return render_template("index.html")


@app.route("/diff")
def uploaded_file():

    return render_template("diff.html")
    # return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8080, debug=True)
