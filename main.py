import os
import fitz
from flask import (
    Flask,
    request,
    redirect,
    url_for,
    render_template,
    send_from_directory,
)
from werkzeug.utils import secure_filename
from diff_match_patch import diff_match_patch
from io import BytesIO
from datetime import datetime
import random
import math

UPLOAD_FOLDER = "static"
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

            file1_bytes = BytesIO(file1.read())
            file2_bytes = BytesIO(file2.read())

            semantic_diff(file1_bytes, file2_bytes)

            return redirect(url_for("uploaded_files"))

    return render_template("index.html")


@app.route("/diff")
def uploaded_files():
    src1 = (
        "\static\diff1.pdf?timestamp="
        + datetime.now().strftime("%m%d%Y%H%M%S")
        + str(math.floor(random.random() * 100000))
    )
    src2 = (
        "\static\diff2.pdf?timestamp="
        + datetime.now().strftime("%m%d%Y%H%M%S")
        + str(math.floor(random.random() * 100000))
    )

    return render_template("diff.html", url1=src1, url2=src2)


def extract_text(file):
    doc = fitz.open(stream=file, filetype="pdf")
    text = ""
    rawdict = None
    newdict = {}
    idx = 0

    for page in doc:
        text = text + page.getText()
        rawdict = page.getText(
            "rawdict",
            flags=fitz.TEXT_PRESERVE_LIGATURES | fitz.TEXT_PRESERVE_WHITESPACE,
        )
        for block in rawdict["blocks"]:
            for line in block["lines"]:
                if idx != 0:
                    newdict[idx] = [None, "\n"]
                    idx += 1
                for span in line["spans"]:
                    for char in span["chars"]:
                        newdict[idx] = [char["origin"], char["c"]]
                        idx += 1

    return (text, newdict)


def step(last_a, last_b, next):
    op, s = next
    l = len(s)

    if -1 == op:
        return ((op, s, (last_a, last_a + l), None), (last_a + l, last_b))

    if 0 == op:
        return (
            (op, s, (last_a, last_a + l), (last_b, last_b + l)),
            (last_a + l, last_b + l),
        )

    if 1 == op:
        return ((op, s, None, (last_b, last_b + l)), (last_a, last_b + l))


def semantic_diff(file1, file2):
    dmp = diff_match_patch()
    dmp.Diff_Timeout = 0
    text1, rawtext1 = extract_text(file1)
    text2, rawtext2 = extract_text(file2)
    diffs = dmp.diff_main(text1, text2)
    dmp.diff_cleanupSemantic(diffs)

    temp_diffs_with_indxs = []
    last_a = 0
    last_b = 0
    for chunk in diffs:
        next, (next_a, next_b) = step(last_a, last_b, chunk)
        last_a = next_a
        last_b = next_b
        temp_diffs_with_indxs.append(next)

    diffs1 = []
    diffs2 = []
    indxs1 = []
    indxs2 = []
    for diff in temp_diffs_with_indxs:
        temp = diff[1].strip("\n")
        if temp == " " or temp == "":
            continue
        if diff[0] == 0:
            continue

        strings = diff[1].splitlines(True)
        if diff[2] is None:
            start_indx = diff[3][0]
            for string in strings:
                diffs2.append(string)
                indxs2.append(start_indx)
                start_indx = start_indx + len(string)
        elif diff[3] is None:
            start_indx = diff[2][0]
            for string in strings:
                diffs1.append(string)
                indxs1.append(start_indx)
                start_indx = start_indx + len(string)

    highlight(file1, rawtext1, diffs1, indxs1)
    highlight(file2, rawtext2, diffs2, indxs2, left=False)


def highlight(file, rawtext, diffs, indxs, left=True):
    red = (0.921, 0.498, 0.521)
    green = (0.498, 0.921, 0.525)

    doc = fitz.open(stream=file, filetype="pdf")

    for diff, indx in zip(diffs, indxs):
        top_left_coord = rawtext[indx][0][0]
        for page in doc:
            instances = page.searchFor(diff)
            if instances is None:
                continue
            for inst in instances:
                if inst[0] == top_left_coord:
                    annot = page.addHighlightAnnot(inst)
                    if left:
                        annot.set_colors(stroke=red)
                    else:
                        annot.set_colors(stroke=green)
                    annot.update()
    if left:
        doc.save(
            os.path.join("static", "diff1.pdf"), garbage=4, deflate=True, clean=True
        )
    else:
        doc.save(
            os.path.join("static", "diff2.pdf"), garbage=4, deflate=True, clean=True
        )


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8080, debug=True)
