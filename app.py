import os
import csv
import subprocess
from flask import Flask, request, render_template_string, redirect, url_for

app = Flask(__name__)
CSV_FILE = 'recipes.csv'

# HTML-форма (встроенная, без внешних файлов)
FORM_HTML = '''
<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8">
  <title>Добавить рецепт</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    body {
      font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
      max-width: 700px;
      margin: 0 auto;
      padding: 20px;
      background-color: #fdf6f0;
      color: #333;
    }
    h1 {
      color: #8b4513;
      text-align: center;
    }
    .form-group {
      margin-bottom: 20px;
    }
    label {
      display: block;
      margin-bottom: 6px;
      font-weight: bold;
      color: #555;
    }
    input, textarea, select {
      width: 100%;
      padding: 10px;
      border: 1px solid #ccc;
      border-radius: 6px;
      font-family: inherit;
      font-size: 16px;
    }
    textarea {
      min-height: 100px;
      resize: vertical;
    }
    .btn {
      background: #a67c52;
      color: white;
      border: none;
      padding: 12px 24px;
      border-radius: 6px;
      cursor: pointer;
      font-size: 16px;
      font-weight: bold;
      width: 100%;
    }
    .btn:hover {
      background: #8b4513;
    }
    .back-link {
      display: inline-block;
      margin-top: 20px;
      color: #a67c52;
      text-decoration: none;
    }
  </style>
</head>
<body>
  <h1>➕ Добавить новый рецепт</h1>

  <form method="POST">
    <div class="form-group">
      <label for="name">Название рецепта *</label>
      <input type="text" id="name" name="name" required>
    </div>

    <div class="form-group">
      <label for="category">Категория</label>
      <select id="category" name="category">
        <option>Горячее копчение</option>
        <option>Холодное копчение</option>
        <option>Засолка</option>
        <option>Маринады</option>
      </select>
    </div>

    <div class="form-group">
      <label for="prep_time">Время подготовки (минуты) *</label>
      <input type="number" id="prep_time" name="prep_time" value="120" min="0" required>
      <small>Например: 30 (мин), 120 (2 ч), 1440 (1 сут.)</small>
    </div>

    <div class="form-group">
      <label for="cook_time">Время копчения (минуты) *</label>
      <input type="number" id="cook_time" name="cook_time" value="60" min="0" required>
    </div>

    <div class="form-group">
      <label for="temp_range">Температура копчения</label>
      <input type="text" id="temp_range" name="temp_range" placeholder="80–120°C">
    </div>

    <div class="form-group">
      <label for="servings">Порции</label>
      <input type="text" id="servings" name="servings" placeholder="4–6 порций">
    </div>

    <div class="form-group">
      <label for="ingredients">Ингредиенты (разделяйте ;)</label>
      <textarea id="ingredients" name="ingredients" placeholder="Свиная грудинка — 1.5 кг; Соль — 4 ст.л.; ..."></textarea>
    </div>

    <div class="form-group">
      <label for="instructions">Пошаговый рецепт (сохраняйте нумерацию: 1. ... 2. ...)</label>
      <textarea id="instructions" name="instructions" placeholder="1. Промойте мясо...&#10;2. Приготовьте рассол..."></textarea>
    </div>

    <div class="form-group">
      <label for="photo">Путь к фото (относительно проекта)</label>
      <input type="text" id="photo" name="photo" placeholder="photos/my_recipe.jpg">
    </div>

    <button type="submit" class="btn">✅ Добавить рецепт и обновить сайт</button>
  </form>

  <a href="/preview" class="back-link">← Посмотреть список рецептов</a>
</body>
</html>
'''

SUCCESS_HTML = '''
<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8">
  <title>Успех!</title>
  <style>
    body { font-family: sans-serif; text-align: center; padding: 50px; background: #e8f5e9; }
    h2 { color: #2e7d32; }
    a { color: #1b5e20; text-decoration: underline; margin-top: 20px; display: inline-block; }
  </style>
</head>
<body>
  <h2>✅ Рецепт успешно добавлен!</h2>
  <p><strong>{{ name }}</strong></p>
  <p>PDF и сайт обновлены.</p>
  <a href="/">Добавить ещё</a> • 
  <a href="/preview">Посмотреть список</a>
</body>
</html>
'''


@app.route('/')
def index():
    return render_template_string(FORM_HTML)


@app.route('/', methods=['POST'])
def add_recipe():
    # Получаем данные
    data = {
        'name': request.form.get('name', '').strip(),
        'category': request.form.get('category', 'Горячее копчение').strip(),
        'prep_time': request.form.get('prep_time', '120').strip(),
        'cook_time': request.form.get('cook_time', '60').strip(),
        'temp_range': request.form.get('temp_range', '').strip(),
        'ingredients': request.form.get('ingredients', '').strip(),
        'instructions': request.form.get('instructions', '').strip(),
        'servings': request.form.get('servings', '').strip(),
        'photo': request.form.get('photo', '').strip(),
    }

    if not data['name']:
        return "❌ Название обязательно!", 400

    # Записываем в CSV
    fieldnames = ['name', 'category', 'prep_time', 'cook_time', 'temp_range',
                  'ingredients', 'instructions', 'servings', 'photo']

    file_exists = os.path.isfile(CSV_FILE)
    with open(CSV_FILE, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow(data)

    # Перегенерируем сайт и PDF
    try:
        subprocess.run(['python', 'generate_site.py'], check=True, cwd=os.getcwd())
    except Exception as e:
        print(f"⚠️ Ошибка при генерации: {e}")

    return render_template_string(SUCCESS_HTML, name=data['name'])


@app.route('/preview')
def preview():
    abs_path = os.path.abspath('output/site/index.html')
    return f'''
    <!DOCTYPE html>
    <html>
    <head><meta charset="utf-8"><title>Список рецептов</title></head>
    <body style="padding: 20px; font-family: sans-serif;">
      <h2>📚 Список рецептов</h2>
      <p>Откройте в браузере:</p>
      <p><code>{abs_path}</code></p>
      <p><a href="file://{abs_path}" target="_blank">👉 Открыть сейчас</a></p>
      <p><a href="/">← Назад</a></p>
    </body>
    </html>
    '''


if __name__ == '__main__':
    print("🚀 Сервер запущен: http://localhost:5000")
    app.run(debug=True, port=5000)