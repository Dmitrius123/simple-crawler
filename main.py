from flask import Flask, render_template, send_file, request, jsonify, redirect, url_for, session
import requests
import csv
import os
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

app = Flask(__name__)


parsed_data = []

def is_allowed_to_scrape(url):
    parsed_url = urlparse(url)
    robots_url = f"{parsed_url.scheme}://{parsed_url.netloc}/robots.txt"
    rp = RobotFileParser()
    rp.set_url(robots_url)
    try:
        rp.read()
        return rp.can_fetch("*", url)
    except:
        return False

# Функция за парсинга
def fetch_content(url, selectors):
    if not is_allowed_to_scrape(url):
        return f"Парсинга е забранен от robots.txt за {url}"

    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        return f"Error {url}: {e}"

    soup = BeautifulSoup(response.content, 'html.parser')
    texts = []
    for selector in selectors:
        elements = soup.find_all(selector['tag'])
        texts.extend([element.get_text() for element in elements])
    return ", ".join(texts)

# Основна страница
@app.route('/')
def index():
    return render_template('index.html', parsed_data=parsed_data)

# Обработка на изпращане на формуляр с парсинга
@app.route('/run-crawler', methods=['post'])
def run_crawler():
    try:
        url = request.form['url']
        selected_tags = request.form.getlist('tags')  # избрани тагове от чекбокси
        additional_tags = request.form.get('additional_tags', '')  # Тагове от текстово поле

        if not url:
            return render_template('index.html', error="URL не е посочен!")
        if not selected_tags and not additional_tags.strip():
            return render_template('index.html', error="Не са избрани или не са въведени тагове за парсинга!")

        # Обеденяване на тагове от чекбокси и текстово поле
        tags = selected_tags + [tag.strip() for tag in additional_tags.split(',') if tag.strip()]
        selectors = [{'tag': tag} for tag in tags]

        # Пускане на парсинга
        content = fetch_content(url, selectors)

        # Речник с резултата
        new_data = [{
            "url": url,
            "tags": tags,
            "content": content
        }]

        # +нови данни към стари
        global parsed_data
        parsed_data.insert(0, new_data[0])

        return render_template('index.html', parsed_data=parsed_data)

    except Exception as e:
        return render_template('index.html', error=str(e))

# за изтриване на данни
@app.route('/clear-history', methods=['post'])
def clear_history():
    global parsed_data
    parsed_data.clear()  # изтриване
    return redirect(url_for('index'))


@app.route('/export-csv', methods=['post'])
def export_csv():
    global parsed_data

    if not parsed_data:
        return render_template('index.html', error="Няма данни за експорта!")

    # Името на CSV файл
    csv_file = "parsing_results.csv"

    try:
        # Създаване на CSV-файл
        with open(csv_file, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["Сайт", "Тагове", "Резултат"])  # Заглавия
            for data in parsed_data:
                writer.writerow([data['url'], ", ".join(data['tags']), data['content']])

        # Пращане на файла за теглене
        return send_file(csv_file, as_attachment=True)

    except Exception as e:
        return render_template('index.html', error=f"Грешка при експортиране на CSV: {e}")

    finally:
        # Изтриваме файла след изпращане
        if os.path.exists(csv_file):
            os.remove(csv_file)


@app.route('/import-csv', methods=['post'])
def import_csv():
    global parsed_data

    file = request.files['file']
    if not file or not file.filename.endswith('.csv'):
        return render_template('index.html', error="Качете правилния CSV-файл!")

    try:
        # Четене на данни от файла в текстов режим
        stream = file.stream.read().decode('utf-8')  # Декодиране на байтове в низове
        reader = csv.DictReader(stream.splitlines(), delimiter=',')

        for row in reader:
            parsed_data.append({
                "url": row["Сайт"],
                "tags": row["Тагове"].split(", "),
                "content": row["Резултат"]
            })

        return render_template('index.html', parsed_data=parsed_data)

    except Exception as e:
        return render_template('index.html', error=f"Грешка при импортиране на CSV: {e}")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5003, debug=True)