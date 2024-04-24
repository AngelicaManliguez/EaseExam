from flask import Flask, render_template, request, jsonify
from PyPDF2 import PdfReader
from docx import Document
import openai

app = Flask(__name__)

# Set your OpenAI API key
openai.api_key = "OpenAI API Key"

@app.route("/")
def index():
    return render_template("index.html")

def generate_questions_from_pdf(pdf_file):
    pdf_reader = PdfReader(pdf_file)
    for page_num in range(len(pdf_reader.pages)):
        yield pdf_reader.pages[page_num].extract_text()

def generate_questions_from_docx(docx_file):
    doc = Document(docx_file)
    for para in doc.paragraphs:
        yield para.text

def is_meaningful_text(text):
    # Check if the text is too short or contains only non-alphanumeric characters
    return text.strip() and len(text.strip()) > 10 and any(char.isalnum() for char in text)

@app.route("/api/generate_quiz", methods=["POST"])
def generate_quiz():
    text_input = request.form.get("text")
    quiz_type = request.form.get("quiz_type")
    num_questions = request.form.get("num_questions")

    # Check if text_input is empty and no files are uploaded
    if not text_input and "files[]" not in request.files:
        return jsonify({"error": "Text input or file upload is required. Please enter some text or upload a file."})

    # Check if num_questions is empty or None
    if not num_questions:
        return jsonify({"error": "Number of questions is required. Please enter a valid number."})

    num_questions = int(num_questions)

    # Calculate the total number of tokens in the input text and files
    total_tokens = len(text_input.split()) if text_input else 0
    for file in request.files.getlist("files[]"):
        total_tokens += len(file.read().split())

    # Log the total number of tokens
    app.logger.info("Total tokens in input: %d", total_tokens)

    # Check if the total number of tokens exceeds the maximum limit
    if total_tokens > 16385:
        return jsonify({"error": f"You have exceeded the maximum token limit of 16385 with {total_tokens} tokens. Please reduce the amount of text or the number of files."})

    messages = [{"role": "system", "content": "You are a student."}]
    if text_input:
        if is_meaningful_text(text_input):
            messages.append({"role": "user", "content": text_input})
        else:
            return jsonify({"error": "Please enter some meaningful text."})

    allowed_extensions = (".docx", ".pdf")
    files = request.files.getlist("files[]")

    combined_text = ""
    for file in files:
        if not file.filename.lower().endswith(allowed_extensions):
            return jsonify({"error": f"Invalid file type. Please upload only {', '.join(allowed_extensions)} files."})

        if file.filename.endswith(".pdf"):
            text = "\n".join(generate_questions_from_pdf(file))
        elif file.filename.endswith(".docx"):
            text = "\n".join(generate_questions_from_docx(file))

        if is_meaningful_text(text):
            combined_text += "\n" + text
        else:
            return jsonify({"error": "Please upload files with meaningful text."})

    if text_input:
        combined_text += "\n" + text_input

    # Check if combined_text is meaningful
    if not is_meaningful_text(combined_text):
        return jsonify({"error": "The input does not contain enough meaningful text. Please provide more information."})

    messages.append({"role": "user", "content": combined_text})
    messages.append({"role": "system", "content": f"Generate {quiz_type} quiz questions and answers for {num_questions} questions."})

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=4096
        )

        questions_with_answers = response["choices"][0]["message"]["content"].strip()

        return jsonify({"questions_with_answers": questions_with_answers})
    except Exception as e:
        app.logger.error("Failed to generate questions and answers: %s", str(e))
        return jsonify({"error": "Failed to generate questions and answers. Please try again."})

if __name__ == '__main__':
    app.run(debug=True)
