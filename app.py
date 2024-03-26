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
    text_input = request.form.get("text")
    quiz_type = request.form.get("quiz_type")
    files = request.files.to_dict(flat=False)

    # Read the content of uploaded files
    file_contents = []
    for key, file_list in files.items():
        for file in file_list:
            if file.filename.endswith(".pdf"):
                pdf_file = PdfReader(file)
                text = ""
                for page_num in range(len(pdf_file.pages)):
                    text += pdf_file.pages[page_num].extract_text()
                file_contents.append(text)
            elif file.filename.endswith(".txt"):
                file_contents.append(file.read().decode("utf-8"))
            elif file.filename.endswith(".docx"):
                doc = Document(file)
                text = ""
                for para in doc.paragraphs:
                    text += para.text
                file_contents.append(text)

    # Generate quiz questions and answers using GPT-3.5 turbo
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a student."},
                {"role": "user", "content": text_input},
                {"role": "user", "content": "\n".join(file_contents)},
                {"role": "system", "content": f"Generate {quiz_type} quiz questions and answers."},
            ],
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