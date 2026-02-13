# import os
# import csv
# import jinja2
# from weasyprint import HTML
# import webbrowser
# import base64
#
#
# def format_prep_time(minutes_str):
#     """Преобразует строку с минутами в человекочитаемый формат"""
#     try:
#         total_minutes = int(minutes_str)
#     except (ValueError, TypeError):
#         return minutes_str  # если не число — возвращаем как есть
#
#     if total_minutes < 60:
#         return f"{total_minutes} мин"
#
#     hours = total_minutes // 60
#     remaining_minutes = total_minutes % 60
#
#     if hours < 24:
#         if remaining_minutes > 0:
#             return f"{hours} ч {remaining_minutes} мин"
#         else:
#             return f"{hours} ч"
#     else:
#         days = hours // 24
#         hours_left = hours % 24
#         parts = []
#         if days == 1:
#             parts.append("1 сут.")
#         elif 2 <= days <= 4:
#             parts.append(f"{days} сут.")
#         else:
#             parts.append(f"{days} сут.")
#
#         if hours_left > 0:
#             parts.append(f"{hours_left} ч")
#
#         return " ".join(parts)
#
# def embed_image(path):
#     if not path or not os.path.isfile(path):
#         return None
#     try:
#         with open(path, "rb") as img_file:
#             encoded = base64.b64encode(img_file.read()).decode('utf-8')
#             ext = os.path.splitext(path)[1][1:].lower()
#             if ext == 'jpg':
#                 ext = 'jpeg'
#             return f"data:image/{ext};base64,{encoded}"
#     except Exception as e:
#         print(f"⚠️ Ошибка при чтении фото {path}: {e}")
#         return None
#
# def main():
#     project_root = os.path.abspath('.')
#     os.makedirs('output/pdfs', exist_ok=True)
#     os.makedirs('output/site', exist_ok=True)
#
#     # Чтение рецептов
#     recipes = []
#     with open('recipes.csv', 'r', encoding='utf-8') as f:
#         reader = csv.DictReader(f, delimiter=',')
#         for i, row in enumerate(reader, 1):
#             ingredients_list = [i.strip() for i in row['ingredients'].split(';') if i.strip()]
#             photo_path = row.get('photo', '').strip()
#             photo_abs_path = os.path.abspath(os.path.join(project_root, photo_path)) if photo_path else ''
#
#             # Безопасное имя для файла (макс. 50 символов)
#             safe_name = "".join(c if c.isalnum() or c in " _-" else "_" for c in row['name'])
#             safe_name_50 = safe_name.replace(' ', '_')[:50]
#
#             recipes.append({
#                 **row,
#                 'ingredients_list': ingredients_list,
#                 'instructions_raw': row['instructions'].strip(),
#                 'photo_data_uri': embed_image(photo_abs_path),
#                 'index': i,
#                 'safe_name_50': safe_name_50,
#                 'prep_time_formatted': format_prep_time(row['prep_time'])
#             })
#
#     # Настройка Jinja2
#     env = jinja2.Environment(loader=jinja2.FileSystemLoader('templates'))
#
#     # 🔥 ЗАГРУЖАЕМ ШАБЛОН ДО ИСПОЛЬЗОВАНИЯ!
#     detail_template = env.get_template('recipe_detail.html')
#
#     # Генерация PDF-рецептов (с проверкой на существование)
#     for recipe in recipes:
#         pdf_path = f"output/pdfs/recipe_{recipe['index']}_{recipe['safe_name_50']}.pdf"
#
#         if os.path.exists(pdf_path):
#             print(f"ℹ️  Пропущен (уже существует): {os.path.basename(pdf_path)}")
#         else:
#             html_out = detail_template.render(**recipe)
#             HTML(string=html_out).write_pdf(pdf_path)
#             print(f"✅ Создан PDF: {os.path.basename(pdf_path)}")
#
#     # Генерация списка рецептов
#     index_template = env.get_template('index.html')
#     index_html = index_template.render(recipes=recipes)
#     with open('output/site/index.html', 'w', encoding='utf-8') as f:
#         f.write(index_html)
#     print("✅ Список рецептов: output/site/index.html")
#
#     # Копирование формы добавления
#     add_form_path = 'templates/add_recipe.html'
#     with open(add_form_path, 'r', encoding='utf-8') as src:
#         with open('output/site/add_recipe.html', 'w', encoding='utf-8') as dst:
#             dst.write(src.read())
#     print("✅ Форма добавления: output/site/add_recipe.html")
#
#     # Открываем список рецептов
#     webbrowser.open(os.path.abspath('output/site/index.html'))
#     print("\n🌐 Открыт список рецептов в браузере.")
#
# if __name__ == '__main__':
#     main()

import os
import csv
import jinja2
from weasyprint import HTML
import webbrowser
import base64
import sys

# --- Защита от двойного запуска ---
if os.environ.get("GENERATE_SITE_RUNNING"):
    print("⚠️ Скрипт уже выполняется. Прервано.")
    sys.exit(1)
os.environ["GENERATE_SITE_RUNNING"] = "1"


def embed_image(path):
    if not path or not os.path.isfile(path):
        return None
    try:
        with open(path, "rb") as img_file:
            encoded = base64.b64encode(img_file.read()).decode('utf-8')
            ext = os.path.splitext(path)[1][1:].lower()
            if ext == 'jpg':
                ext = 'jpeg'
            return f"data:image/{ext};base64,{encoded}"
    except Exception as e:
        print(f"⚠️ Ошибка при чтении фото {path}: {e}")
        return None


def format_prep_time(minutes_str):
    try:
        total_minutes = int(minutes_str)
    except (ValueError, TypeError):
        return minutes_str

    if total_minutes < 60:
        return f"{total_minutes} мин"

    hours = total_minutes // 60
    remaining_minutes = total_minutes % 60

    if hours < 24:
        return f"{hours} ч" + (f" {remaining_minutes} мин" if remaining_minutes > 0 else "")
    else:
        days = hours // 24
        hours_left = hours % 24
        parts = []
        if days == 1:
            parts.append("1 сут.")
        elif 2 <= days <= 4:
            parts.append(f"{days} сут.")
        else:
            parts.append(f"{days} сут.")
        if hours_left > 0:
            parts.append(f"{hours_left} ч")
        return " ".join(parts)


def main():
    project_root = os.path.abspath('.')
    os.makedirs('output/pdfs', exist_ok=True)
    os.makedirs('output/site', exist_ok=True)

    # Чтение рецептов
    recipes = []
    with open('recipes.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter=',')
        for i, row in enumerate(reader, 1):
            ingredients_list = [i.strip() for i in row['ingredients'].split(';') if i.strip()]
            photo_path = row.get('photo', '').strip()
            photo_abs_path = os.path.abspath(os.path.join(project_root, photo_path)) if photo_path else ''

            safe_name = "".join(c if c.isalnum() or c in " _-" else "_" for c in row['name'])
            safe_name_50 = safe_name.replace(' ', '_')[:50]

            recipes.append({
                **row,
                'ingredients_list': ingredients_list,
                'instructions_raw': row['instructions'].strip(),
                'photo_data_uri': embed_image(photo_abs_path),
                'index': i,
                'safe_name_50': safe_name_50,
                'prep_time_formatted': format_prep_time(row['prep_time'])
            })

    env = jinja2.Environment(loader=jinja2.FileSystemLoader('templates'))
    detail_template = env.get_template('recipe_detail.html')

    # Генерация PDF
    for recipe in recipes:
        pdf_path = f"output/pdfs/recipe_{recipe['index']}_{recipe['safe_name_50']}.pdf"
        if os.path.exists(pdf_path):
            print(f"ℹ️  Пропущен: {os.path.basename(pdf_path)}")
        else:
            html_out = detail_template.render(**recipe)
            HTML(string=html_out).write_pdf(pdf_path)
            print(f"✅ Создан: {os.path.basename(pdf_path)}")

    # Генерация сайта
    index_template = env.get_template('index.html')
    with open('output/site/index.html', 'w', encoding='utf-8') as f:
        f.write(index_template.render(recipes=recipes))
    print("✅ Список: output/site/index.html")

    with open('templates/add_recipe.html', 'r', encoding='utf-8') as src:
        with open('output/site/add_recipe.html', 'w', encoding='utf-8') as dst:
            dst.write(src.read())
    print("✅ Форма: output/site/add_recipe.html")

    webbrowser.open(os.path.abspath('output/site/index.html'))
    print("\n🌐 Открыт список рецептов.")


if __name__ == '__main__':
    main()
    # Очищаем флаг после завершения
    os.environ.pop("GENERATE_SITE_RUNNING", None)