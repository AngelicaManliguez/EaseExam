from flask import Flask, render_template, request, jsonify, Response
from PyPDF2 import PdfReader
from docx import Document
import openai

app = Flask(__name__)

# Set your OpenAI API key
openai.api_key = "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"

@app.route("/")
def index():
    return render_template("index.html")

def generate_questions_from_pdf(pdf_file):
    pdf_reader = PdfReader(pdf_file)
    for page_num in range(len(pdf_reader.pages)):
        yield pdf_reader.pages[page_num].extract_text()

def generate_questions_from_text_file(text_file):
    for line in text_file:
        yield line

def generate_questions_from_docx(docx_file):
    doc = Document(docx_file)
    for para in doc.paragraphs:
        yield para.text

@app.route("/api/generate_quiz", methods=["POST"])
def generate_quiz():
    text_input = request.form.get("text")
    quiz_type = request.form.get("quiz_type")
    num_questions = int(request.form.get("num_questions"))

    # Calculate the total token count of the messages
    total_tokens = len(text_input.split()) + sum(len(file.read().split()) for file in request.files.getlist("files[]"))

    # Check if the total token count exceeds the maximum context length
    if total_tokens > 16383:
        return jsonify({"error": f"Total token count exceeds the maximum context length. Current token count: {total_tokens}. Maximum allowed token count: 16383."})

    # Generate quiz questions and answers using GPT-3.5 turbo
    try:
        messages = [
            {"role": "system", "content": "You are a student."},
            {"role": "user", "content": text_input},
        ]

        for file in request.files.getlist("files[]"):
            if file.filename.endswith(".pdf"):
                messages.extend({"role": "user", "content": page_text} for page_text in generate_questions_from_pdf(file))
            elif file.filename.endswith(".txt"):
                messages.extend({"role": "user", "content": line} for line in generate_questions_from_text_file(file))
            elif file.filename.endswith(".docx"):
                messages.extend({"role": "user", "content": para} for para in generate_questions_from_docx(file))

        messages.append({"role": "system", "content": f"Generate {quiz_type} quiz questions and answers for {num_questions} questions."})

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=4096
        )

        questions_with_answers = response["choices"][0]["message"]["content"].strip()

        return jsonify({"questions_with_answers": questions_with_answers})
    except Exception as e:
        # Log the exception for debugging
        app.logger.error("Failed to generate questions and answers: %s", str(e))
        return jsonify({"error": "Failed to generate questions and answers. Please try again."})

if __name__ == '__main__':
    app.run(debug=True)