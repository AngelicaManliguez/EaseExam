from flask import Flask, render_template, request, jsonify
import os
import fitz  # PyMuPDF
import openai

app = Flask(__name__)

# Set your OpenAI API key
openai.api_key = "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"

# Store the paths of uploaded files
uploaded_files = {}

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/upload", methods=["POST"])
def upload_file():
    # Get the uploaded file
    file = request.files["file"]
    if file.filename == "":
        return "No file selected"
    
    # Save the file
    file_path = os.path.join("static/uploads", file.filename)
    file.save(file_path)
    
    # Store the uploaded file path
    uploaded_files[file.filename] = file_path
    
    # Check if the file is a PDF
    if file.filename.endswith(".pdf"):
        # Convert PDF to text
        text = convert_pdf_to_text(file_path)
        return render_template("result.html", text=text)
    else:
        return "Unsupported file format"

@app.route("/api/generate_quiz", methods=["POST"])
def generate_quiz():
    text = request.form.get("text")
    files = request.files.to_dict(flat=False)

    # Save files to txt in static/uploads folder
    saved_files = []
    for key, file_list in files.items():
        for file in file_list:
            if file.filename:
                file_path = os.path.join("static", "uploads", file.filename + ".txt")
                file.save(file_path)
                saved_files.append(file_path)

    # Read the content of uploaded files
    file_texts = []
    for file_path in saved_files:
        with open(file_path, "r") as file:
            file_texts.append(file.read())

    # Generate quiz questions using GPT-3.5 turbo
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a student."},
            {"role": "user", "content": text},
            {"role": "user", "content": "\n".join(file_texts)},
        ],
        max_tokens=100
    )

    questions = response["choices"][0]["message"]["content"].strip().split("\n")

    return jsonify({"questions": questions, "saved_files": saved_files})

def convert_pdf_to_text(pdf_file_path):
    pdf_document = fitz.open(pdf_file_path)
    text = ""
    for page_num in range(len(pdf_document)):
        page = pdf_document[page_num]
        text += page.get_text()
    pdf_document.close()
    return text

if __name__ == '__main__':
    app.run(debug=True)