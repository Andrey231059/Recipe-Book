import os
import csv
import subprocess
import base64
from flask import Flask, request, render_template_string, send_file

app = Flask(__name__)
CSV_FILE = 'recipes.csv'


# --- Вспомогательные функции ---
def read_recipes():
    """Читает рецепты и добавляет photo_data_uri и prep_time_formatted"""
    if not os.path.isfile(CSV_FILE):
        return []

    recipes = []
    project_root = os.path.abspath('.')
    with open(CSV_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader, 1):
            # Форматируем время подготовки
            try:
                mins = int(row.get('prep_time', '0'))
                if mins < 60:
                    prep_fmt = f"{mins} мин"
                elif mins < 1440:
                    h = mins // 60
                    m = mins % 60
                    prep_fmt = f"{h} ч" + (f" {m} мин" if m else "")
                else:
                    d = mins // 1440
                    h = (mins % 1440) // 60
                    prep_fmt = f"{d} сут."
                    if h: prep_fmt += f" {h} ч"
            except:
                prep_fmt = row.get('prep_time', '')

            # Фото (base64)
            photo_path = row.get('photo', '').strip()
            photo_data_uri = None
            if photo_path:
                full_path = os.path.abspath(os.path.join(project_root, photo_path))
                if os.path.isfile(full_path):
                    try:
                        with open(full_path, "rb") as img_file:
                            encoded = base64.b64encode(img_file.read()).decode('utf-8')
                            ext = os.path.splitext(full_path)[1][1:].lower()
                            if ext == 'jpg': ext = 'jpeg'
                            photo_data_uri = f"data:image/{ext};base64,{encoded}"
                    except:
                        pass

            recipes.append({
                **row,
                'index': i,
                'prep_time_formatted': prep_fmt,
                'photo_data_uri': photo_data_uri
            })
    return recipes


def write_recipes(recipes):
    if not recipes:
        return
    fieldnames = recipes[0].keys()
    # Убираем служебные поля
    clean_fieldnames = [k for k in fieldnames if k not in ('index', 'prep_time_formatted', 'photo_data_uri')]
    with open(CSV_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=clean_fieldnames)
        writer.writeheader()
        for r in recipes:
            clean_r = {k: v for k, v in r.items() if k in clean_fieldnames}
            writer.writerow(clean_r)


def backup_csv():
    if os.path.isfile(CSV_FILE):
        with open(CSV_FILE, 'rb') as src, open(CSV_FILE + '.bak', 'wb') as dst:
            dst.write(src.read())


# --- HTML-шаблоны ---
HOME_HTML = '''
<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8">
  <title>Книга рецептов</title>
  <style>
    body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; max-width: 900px; margin: 0 auto; padding: 20px; background: #fdf6f0; }
    .header { text-align: center; margin-bottom: 30px; padding-bottom: 15px; border-bottom: 2px solid #d4a574; }
    .btn { display: inline-block; background: #a67c52; color: white; padding: 10px 20px; text-decoration: none; border-radius: 6px; margin: 10px; }
    .btn:hover { background: #8b4513; }
    .recipe-list { margin-top: 20px; }
    .recipe-item { 
      padding: 15px; 
      margin: 12px 0; 
      background: white; 
      border-radius: 10px; 
      box-shadow: 0 2px 6px rgba(0,0,0,0.1);
      display: flex;
      gap: 20px;
      align-items: flex-start;
    }
    .recipe-img {
      width: 100px;
      height: 100px;
      object-fit: cover;
      border-radius: 8px;
      background: #eee;
      display: flex;
      align-items: center;
      justify-content: center;
      color: #888;
      font-size: 12px;
    }
    .recipe-info { flex: 1; }
    .recipe-title { font-weight: bold; color: #8b4513; font-size: 18px; margin-bottom: 6px; }
    .recipe-meta { color: #666; font-size: 0.95em; margin-bottom: 10px; }
    .recipe-actions a { 
      margin-right: 15px; 
      color: #1a73e8; 
      text-decoration: none; 
      font-weight: bold;
    }
    .recipe-actions a:hover { text-decoration: underline; }
    .no-recipes { text-align: center; color: #888; margin-top: 30px; font-style: italic; }
  </style>
</head>
<body>
  <div class="header">
    <h1>📚 Книга рецептов горячего копчения</h1>
    <a href="/add" class="btn">➕ Добавить рецепт</a>
  </div>

  {% if recipes %}
    <div class="recipe-list">
      {% for recipe in recipes %}
      <div class="recipe-item">
        {% if recipe.photo_data_uri %}
          <img src="{{ recipe.photo_data_uri }}" alt="{{ recipe.name }}" class="recipe-img">
        {% else %}
          <div class="recipe-img">📷 Нет фото</div>
        {% endif %}

        <div class="recipe-info">
          <div class="recipe-title">{{ recipe.index }}. {{ recipe.name }}</div>
          <div class="recipe-meta">
            {{ recipe.category }} • Подготовка: {{ recipe.prep_time_formatted }} • Копчение: {{ recipe.cook_time }} мин
          </div>
          <div class="recipe-actions">
            <a href="/pdf/{{ recipe.index }}" target="_blank">📄 PDF</a>
            <a href="/edit/{{ recipe.index }}">✏️ Изменить</a>
          </div>
        </div>
      </div>
      {% endfor %}
    </div>
  {% else %}
    <div class="no-recipes">
      Пока нет рецептов. <a href="/add" style="color:#a67c52;">Добавьте первый!</a>
    </div>
  {% endif %}
</body>
</html>
'''

FORM_HTML = '''
<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8">
  <title>{{ 'Редактировать' if recipe else 'Добавить' }} рецепт</title>
  <style>
    body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; max-width: 700px; margin: 0 auto; padding: 20px; background: #fdf6f0; }
    h1 { color: #8b4513; text-align: center; }
    .form-group { margin-bottom: 20px; }
    label { display: block; margin-bottom: 6px; font-weight: bold; color: #555; }
    input, textarea, select { width: 100%; padding: 10px; border: 1px solid #ccc; border-radius: 6px; font-family: inherit; font-size: 16px; }
    textarea { min-height: 100px; resize: vertical; }
    .btn { background: #a67c52; color: white; border: none; padding: 12px 24px; border-radius: 6px; cursor: pointer; font-size: 16px; font-weight: bold; width: 100%; }
    .btn:hover { background: #8b4513; }
    .back-link { display: inline-block; margin-top: 20px; color: #a67c52; text-decoration: none; }
  </style>
</head>
<body>
  <h1>{{ '✏️ Редактировать рецепт' if recipe else '➕ Добавить рецепт' }}</h1>

  <form method="POST">
    <input type="hidden" name="index" value="{{ recipe.index if recipe else '' }}">

    <div class="form-group">
      <label>Название *</label>
      <input type="text" name="name" value="{{ recipe.name if recipe else '' }}" required>
    </div>

    <div class="form-group">
      <label>Категория</label>
      <select name="category">
        {% for cat in ['Горячее копчение', 'Холодное копчение', 'Засолка', 'Маринады'] %}
          <option {% if cat == (recipe.category if recipe else 'Горячее копчение') %}selected{% endif %}>{{ cat }}</option>
        {% endfor %}
      </select>
    </div>

    <div class="form-group">
      <label>Подготовка (мин)</label>
      <input type="number" name="prep_time" value="{{ recipe.prep_time if recipe else '120' }}" min="0" required>
    </div>

    <div class="form-group">
      <label>Копчение (мин)</label>
      <input type="number" name="cook_time" value="{{ recipe.cook_time if recipe else '60' }}" min="0" required>
    </div>

    <div class="form-group">
      <label>Температура</label>
      <input type="text" name="temp_range" value="{{ recipe.temp_range if recipe else '' }}" placeholder="80–120°C">
    </div>

    <div class="form-group">
      <label>Порции</label>
      <input type="text" name="servings" value="{{ recipe.servings if recipe else '' }}" placeholder="4–6 порций">
    </div>

    <div class="form-group">
      <label>Ингредиенты (;)</label>
      <textarea name="ingredients">{{ recipe.ingredients if recipe else '' }}</textarea>
    </div>

    <div class="form-group">
      <label>Рецепт</label>
      <textarea name="instructions">{{ recipe.instructions if recipe else '' }}</textarea>
    </div>

    <div class="form-group">
      <label>Фото (путь)</label>
      <input type="text" name="photo" value="{{ recipe.photo if recipe else '' }}" placeholder="photos/my.jpg">
    </div>

    <button type="submit" class="btn">{{ '💾 Сохранить' if recipe else '✅ Добавить' }}</button>
  </form>

  <a href="/" class="back-link">← Назад к списку</a>
</body>
</html>
'''

SUCCESS_REDIRECT = '''
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><meta http-equiv="refresh" content="1;url=/"></head>
<body style="text-align:center; padding:50px; font-family:sans-serif;">
  <h2>✅ {{ message }}</h2>
  <p>Перенаправление на главную...</p>
</body>
</html>
'''


# --- Маршруты ---
@app.route('/')
def home():
    recipes = read_recipes()
    return render_template_string(HOME_HTML, recipes=recipes)


@app.route('/add')
def add_form():
    return render_template_string(FORM_HTML)


@app.route('/add', methods=['POST'])
def add_recipe():
    backup_csv()
    data = {k: v.strip() for k, v in request.form.items()}
    if not data.get('name'):
        return "❌ Название обязательно!", 400

    recipes = read_recipes()
    # Удаляем служебные поля перед сохранением
    clean_data = {k: v for k, v in data.items() if k != 'index'}
    recipes.append(clean_data)
    write_recipes(recipes)

    try:
        subprocess.run(['python', 'generate_site.py'], check=True, cwd=os.getcwd())
    except Exception as e:
        print(f"⚠️ Ошибка генерации: {e}")

    return render_template_string(SUCCESS_REDIRECT, message="Рецепт добавлен!")


@app.route('/edit/<int:index>')
def edit_form(index):
    recipes = read_recipes()
    if index < 1 or index > len(recipes):
        return "Рецепт не найден", 404
    recipe = recipes[index - 1]
    return render_template_string(FORM_HTML, recipe=recipe)


@app.route('/edit/<int:index>', methods=['POST'])
def update_recipe(index):
    backup_csv()
    recipes = read_recipes()
    if index < 1 or index > len(recipes):
        return "Рецепт не найден", 404

    data = {k: v.strip() for k, v in request.form.items()}
    if not data.get('name'):
        return "❌ Название обязательно!", 400

    # Обновляем только данные, без служебных полей
    clean_data = {k: v for k, v in data.items() if k != 'index'}
    recipes[index - 1] = {**recipes[index - 1], **clean_data}
    write_recipes(recipes)

    try:
        subprocess.run(['python', 'generate_site.py'], check=True, cwd=os.getcwd())
    except Exception as e:
        print(f"⚠️ Ошибка генерации: {e}")

    return render_template_string(SUCCESS_REDIRECT, message="Рецепт обновлён!")


@app.route('/pdf/<int:index>')
def serve_pdf(index):
    recipes = read_recipes()
    if index < 1 or index > len(recipes):
        return "PDF не найден", 404

    recipe = recipes[index - 1]
    safe_name = "".join(c if c.isalnum() or c in " _-" else "_" for c in recipe['name'])
    safe_name_50 = safe_name.replace(' ', '_')[:50]
    pdf_filename = f"recipe_{index}_{safe_name_50}.pdf"
    pdf_path = os.path.join('output', 'pdfs', pdf_filename)

    if not os.path.isfile(pdf_path):
        return f"Файл не найден: {pdf_path}", 404

    return send_file(pdf_path, as_attachment=False)


if __name__ == '__main__':
    print("🚀 Сервер запущен: http://localhost:5000")
    app.run(debug=True, port=5000)