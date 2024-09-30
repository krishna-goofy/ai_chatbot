from flask import Flask, render_template, request, jsonify
from scraper.scraper import scrape_website, download_pdf
from database.db import create_database, insert_web_data, insert_pdf_data, get_processed_urls, add_processed_url, get_processed_pdfs, add_processed_pdf
import sqlite3
import google.generativeai as genai
import os
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)

# Create database and trigger initial scraping if database is empty
def check_and_scrape_initial_data():
    create_database()

    # Check if web_data or pdf_data tables are empty
    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM web_data")
    web_data_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM pdf_data")
    pdf_data_count = cursor.fetchone()[0]
    conn.close()

    # Trigger scraping if database is empty
    if web_data_count == 0 and pdf_data_count == 0:
        print("Database is empty. Starting initial scraping...")
        url = "https://doj.gov.in/"
        scrape_and_process_data(url)
        print("Initial scraping completed!")

# Gemini API configuration
genai.configure(api_key="AIzaSyCviPpSbfCRlV052u1ga7O2kMGH8-H3KeI")

# Gemini API function using google.generativeai
def ask_gemini(question, db_content):
    model = genai.GenerativeModel("gemini-1.5-flash")
    prompt = (f"You are a friendly assistant. Provide a short, engaging, and conversational response to the question below. "
              f"Use the context if needed, but keep the answer brief.\n\n"
              f"Context:\n{db_content}\n\n"
              f"Question: {question}")
    response = model.generate_content(prompt)
    cleaned_text = response.text.replace('*', '')

    return {"answer": cleaned_text}


# Route to render the front end
@app.route('/')
def index():
    return render_template('index.html')

# Route to return predefined questions as JSON
@app.route('/get_predefined_questions', methods=['GET'])
def get_predefined_questions():
    questions = [
        "What is the Department of Justice’s role?",
        "How does the Department tackle systemic discrimination?",
        "What steps promote justice and equality?",
        "How does the Department assist victims of injustice?",
        "What initiatives improve legal access?",
        "How are corruption cases handled?",
        "How does the Department uphold human rights?",
        "How does the Department collaborate with other agencies?",
        "What are the strategies for legal reform?",
        "How does the Department ensure transparency?"
    ]
    return jsonify(questions)

# Route to trigger scraping
@app.route('/scrape', methods=['POST'])
def scrape():
    url = request.json.get('url')
    scrape_and_process_data(url)
    return jsonify({"message": "Scraping completed!"})

# Function to scrape website and process data
def scrape_and_process_data(url):
    processed_urls = get_processed_urls()  # Get already processed URLs
    text, pdf_links = scrape_website(url)

    # Only insert new data into the database
    if url not in processed_urls:
        insert_web_data(url, text)
        add_processed_url(url)  # Add the URL to the processed list

    # Handle PDFs
    processed_pdfs = get_processed_pdfs()  # Get already processed PDFs
    for pdf_url in pdf_links:
        if pdf_url not in processed_pdfs:
            pdf_path, pdf_text = download_pdf(pdf_url)
            if pdf_path:
                insert_pdf_data(pdf_path, pdf_text)
                add_processed_pdf(pdf_url)  # Mark the PDF as processed

# Route to handle chatbot queries
@app.route('/ask', methods=['POST'])
def ask_question():
    question = request.json.get('question')

    # Fetch all content from the database
    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()
    cursor.execute("SELECT text_data FROM web_data")
    web_data = " ".join([row[0] for row in cursor.fetchall()])
    cursor.execute("SELECT text_data FROM pdf_data")
    pdf_data = " ".join([row[0] for row in cursor.fetchall()])
    db_content = web_data + " " + pdf_data
    conn.close()

    response = ask_gemini(question, db_content)
    return jsonify(response)

# Scheduler to scrape every hour
def schedule_scraping():
    print("Scheduled scraping started")
    url = "https://doj.gov.in/"
    scrape_and_process_data(url)
    print("Scheduled scraping completed")

# Set up background scheduler for periodic scraping
scheduler = BackgroundScheduler()
scheduler.add_job(schedule_scraping, 'interval', hours=1)
scheduler.start()

if __name__ == '__main__':
    try:
        # Check if database is empty and start scraping if necessary
        check_and_scrape_initial_data()

        app.run(host='0.0.0.0', port=5000, debug=True)  # Bind to all interfaces on port 5000
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
