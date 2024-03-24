from flask import Flask, render_template, request, jsonify
from PyPDF2 import PdfReader
from docx import Document
import openai

app = Flask(__name__)

# Set your OpenAI API key
openai.api_key = "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"

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/generate_quiz", methods=["POST"])
def generate_quiz():
    text = request.form.get("text")
    quiz_type = request.form.get("quiz_type")
    files = request.files.to_dict(flat=False)

    # Read the content of uploaded files
    file_texts = []
    for key, file_list in files.items():
        for file in file_list:
            if file.filename.endswith(".pdf"):
                pdf_file = PdfReader(file)
                text = ""
                for page_num in range(len(pdf_file.pages)):
                    text += pdf_file.pages[page_num].extract_text()
                file_texts.append(text)
            elif file.filename.endswith(".txt"):
                file_texts.append(file.read().decode("utf-8"))
            elif file.filename.endswith(".docx"):
                doc = Document(file)
                text = ""
                for para in doc.paragraphs:
                    text += para.text
                file_texts.append(text)

    # Generate quiz questions using GPT-3.5 turbo
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a student."},
                {"role": "user", "content": text},
                {"role": "user", "content": "\n".join(file_texts)},
                {"role": "system", "content": f"Generate {quiz_type} quiz questions."},
            ],
            max_tokens=100
        )

        questions = response["choices"][0]["message"]["content"].strip().split("\n")

        return jsonify({"questions": questions})
    except Exception as e:
        # Log the exception for debugging
        app.logger.error("Failed to generate questions: %s", str(e))
        return jsonify({"error": "Failed to generate questions. Please try again."})

if __name__ == '__main__':
    app.run(debug=True)