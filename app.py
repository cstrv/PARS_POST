# source /home/castrv/Документы/in_progress/CODER_CASTROV_srv/.venv/bin/activate
import shutil
import os
import sys
import time
import requests
import json
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from bs4 import NavigableString
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import uuid
import argparse
from PIL import Image
from io import BytesIO

def parse_args():
    parser = argparse.ArgumentParser(description='Start index for parsing.')
    parser.add_argument('--start_index', type=int, default=1, help='The index to start parsing from.')
    args = parser.parse_args()
    return args

def start_browser_and_login():
    # user_agent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36'
    url = 'https://medium.com/'
    cookies_filename = 'cookies.json'
    
    chrome_options = Options()
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--headless")
    # chrome_options.add_argument(f"user-agent={user_agent}")
    
    driver = webdriver.Chrome(options=chrome_options)
    
    # Установка размера окна браузера
    driver.set_window_size(1366, 768)
    driver.get(url)
    
    if os.path.exists(cookies_filename):
        with open(cookies_filename, 'r') as file:
            cookies_str = file.read()
            cookies = json.loads(cookies_str)  # Теперь json.loads должен работать корректно
            for cookie in cookies:
                # Удаляем неподдерживаемые ключи
                cookie.pop('hostOnly', None)
                cookie.pop('session', None)
                cookie.pop('storeId', None)
                cookie.pop('sameSite', None)  # Удаляем ключ 'sameSite'
                
                # Конвертируем 'expirationDate' в 'expiry' и убеждаемся, что это int
                if 'expirationDate' in cookie:
                    cookie['expiry'] = int(cookie.pop('expirationDate'))
                
                # Добавляем куки в браузер
                driver.add_cookie(cookie)
        
        # Перезагружаем страницу, чтобы куки вступили в силу
        driver.refresh()
        driver.get("https://medium.com/")
    
    else:
        print("Файл с куки не найден. Остановка выполнения скрипта.")
        sys.exit(1)
        
    return driver

def read_urls_from_file(filename, start_index=1):
    with open(filename, 'r') as file:
        return [line.strip() for line in file][start_index - 1:]

    
def save_content_to_files(content, base_filename):
    file_count = 1
    file_content = []

    def save_file_content():
        nonlocal file_count
        if file_content:
            with open(f"Inbox/{base_filename}_{file_count}.mdx", 'w', encoding='utf-8') as file:
                file.write('\n'.join(file_content))
            file_count += 1

    def char_count(content_list):
        return sum(len(item) for item in content_list)
    
    for i, elem in enumerate(content):
        is_header = elem.startswith(('#', '##', '###', '####', '#####', '######'))  # Проверяем, является ли элемент заголовком
        if is_header and file_content and char_count(file_content) >= 600:  # Если это заголовок, file_content не пуст, и сумма символов >= 600, сохраняем текущее содержимое в файл
            save_file_content()
            file_content = [elem]  # Начинаем новый файл с текущим заголовком
        else:
            # Иначе просто добавляем текущий элемент в содержимое текущего файла
            file_content.append(elem)
            # Проверяем, достигло ли общее количество символов 600 в последнем фрагменте, и является ли следующий элемент заголовком
            if i + 1 < len(content) and content[i + 1].startswith(('#', '##', '###', '####', '#####', '######')) and char_count(file_content) < 600:
                # Если следующий элемент является заголовком и символов в текущем фрагменте меньше 600, продолжаем добавлять элементы до достижения 600 символов
                continue

    save_file_content()
           
def extract_and_save_second_prev_content(driver, folder, filename):
    try:
        footer_element = driver.find_element(By.TAG_NAME, 'footer')
        
        second_prev_element = driver.execute_script("""
        var element = arguments[0];
        var prevElement = element.previousElementSibling;
        if(prevElement) prevElement = prevElement.previousElementSibling;
        return prevElement;
        """, footer_element)
        
        if second_prev_element:
            second_prev_html = second_prev_element.get_attribute('outerHTML')
            
            soup = BeautifulSoup(second_prev_html, 'html.parser')
            
            content = []
            for a in soup.find_all('a'):
                text = a.get_text(strip=True)
                if text:  # Проверка, что текст не пуст
                    content.append(f"{text}")
            
            try:
                with open(f"Inbox/{folder}/{filename}", 'w', encoding='utf-8') as file:
                    file.write('\n'.join(content))
            except Exception as e:
                print(f"Could not save the second previous content to the file: {e}")
                
    except Exception as e:
        print(f"Could not extract the content of the second previous div: {e}")
        
def download_and_save_image(url, folder):
    try:
        response = requests.get(url)
        response.raise_for_status()
        
        # Генерация случайного имени файла
        random_file_name = f"{uuid.uuid4().hex[:10]}.jpg"
        
        with open(os.path.join(folder, random_file_name), 'wb') as file:
            file.write(response.content)
        
        return os.path.join(folder, random_file_name)
    except Exception as e:
        print(f"Could not download and save image from {url}: {e}")
        return url
        
def parse_and_save_content(driver, folder, filename):
    try:
        time.sleep(5)
        
        try:
            footer_element = driver.find_element(By.TAG_NAME, 'footer')
            
            driver.execute_script("""
            var element = arguments[0];
            var nextElement = element.nextElementSibling;
            if(nextElement && nextElement.tagName.toLowerCase() === 'div') {
                nextElement.parentNode.removeChild(nextElement);
            }
            """, footer_element)
        except Exception as e:
            print(f"Could not remove the unwanted div: {e}")
        
        extract_and_save_second_prev_content(driver, folder, 'seo_tags.mdx')
            
        article_element = driver.find_element(By.TAG_NAME, 'article')
        
        article_html = article_element.get_attribute('outerHTML')
        
        soup = BeautifulSoup(article_html, 'html.parser')
        
        for block in soup.find_all(class_='speechify-ignore'):
            block.decompose()
            
        def process_nested_tags(element):
            for em in element.find_all('em'):
                em.replace_with(NavigableString(f"_{em.get_text()}_"))
            for strong in element.find_all('strong'):
                strong.replace_with(NavigableString(f"**{strong.get_text()}**"))
            # for mark in element.find_all('mark'):
            #     mark.replace_with(NavigableString(f"=={mark.get_text()}=="))
            for a in element.find_all('a', href=True):
                a.replace_with(NavigableString(f"[{a.get_text()}]({a['href']})"))
            for code in element.find_all('code'):
                code.replace_with(NavigableString(f"`{code.get_text()}`"))

        def process_table(table):
            rows = table.find_all('tr')
            table_data = []
            for row in rows:
                cells = row.find_all(['th', 'td'])
                cells = [cell.get_text(strip=True) for cell in cells]
                table_data.append(cells)
            
            col_widths = [max(len(str(cell)) for cell in col) for col in zip(*table_data)]
            
            table_str_list = []
            for i, row in enumerate(table_data):
                row_str = "| " + " | ".join(str(cell).ljust(col_widths[j]) for j, cell in enumerate(row)) + " |"
                table_str_list.append(row_str)
                if i == 0:  # После строки заголовка добавляем строку разделителя
                    table_str_list.append("|-" + "-|-".join("-" * width for width in col_widths) + "-|")
            
            return "\n".join(table_str_list)
        
        content = []
        
        for elem in soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'img', 'video', 'pre', 'table', 'blockquote', 'ul', 'div']):
            if elem.find_parent(lambda tag: tag.name == 'div' and tag.get('role') == 'button' and tag.get('tabindex') == '0' and 'ab' in tag.get('class', [])):
                continue
            
            if elem.parent.name == 'blockquote':
                continue
            
            process_nested_tags(elem)
            if elem.name == 'blockquote':
                blockquote_content = []
                for nested_elem in elem.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'code', 'strong', 'em']):
                    process_nested_tags(nested_elem)
                    blockquote_content.append(nested_elem.get_text())
                
                blockquote_text = '> ' + '\n> '.join(blockquote_content)
                content.append(blockquote_text + '\n')
            if elem.name == 'table':
                content.append(process_table(elem) + '\n')
            if elem.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                content.append(f"{'#' * int(elem.name[1])} {elem.get_text()}\n")
            elif elem.name == 'p':
                content.append(f"{elem.get_text()}\n")
            
            elif elem.name == 'ul':
                list_items = elem.find_all('li')
                list_content = '\n'.join(f"- {item.get_text()}" for item in list_items)
                content.append(list_content + '\n')
            
            elif elem.name == 'div' and elem.get('role') == 'separator':
                content.append('---\n') 
            
            elif elem.name == 'img':
                src = elem.get('src', '')
                width = elem.get('width')  # Получение ширины изображения
                height = elem.get('height')
                
                # Если атрибуты width и height отсутствуют, загружаем изображение и определяем его размеры
                if width is None or height is None:
                    try:
                        response = requests.get(src)
                        response.raise_for_status()
                        img = Image.open(BytesIO(response.content))
                        width, height = img.size
                    except Exception as e:
                        print(f"Could not get image dimensions for {src}: {e}")
                        width, height = 'auto', 'auto'  # Если возникла ошибка, устанавливаем размеры в 'auto'
                
                # Проверяем, есть ли рядом тег figcaption
                parent = elem.find_parent('figure')
                if parent:
                    figcaption = parent.find('figcaption')
                    if figcaption:
                        figcaption_text = figcaption.get_text(strip=True)
                        # Проверяем наличие Markdown синтаксиса для ссылок в тексте figcaption
                        if '][' in figcaption_text or 'http' in figcaption_text:
                            alt = ''  # Если есть ссылка, устанавливаем alt как пустую строку
                        else:
                            alt = figcaption_text  # Если нет ссылки, используем текст figcaption
                    else:
                        alt = elem.get('alt', '')  # Если figcaption отсутствует, используем атрибут alt тега img
                else:
                    alt = elem.get('alt', '')  # Если родительский элемент не является тегом figure, используем атрибут alt тега img
                
                        
                # Убедитесь, что папка существует
                img_folder = 'blogs'
                if not os.path.exists(img_folder):
                    os.makedirs(img_folder)
                
                new_src = download_and_save_image(src, img_folder)
                
                img_str = f'<Image\n  src="/{new_src}"\n  width="{width}"\n  height="{height}"\n  alt="{alt}"\n  sizes="100vw"\n/>'
                # img_str = f'<Image\n  src="/{new_src}"\n  width="718"\n  height="404"\n  alt="{alt}"\n  sizes="100vw"\n/>'
                
                content.append(img_str + '\n')

            elif elem.name == 'video':
                content.append(f"Video: {elem.get('src', '')}\n")
            elif elem.name == 'pre':
                span_texts = []
                for span in elem.find_all('span', recursive=False):
                    span_text = ''
                    for s in span.children:
                        if isinstance(s, NavigableString):
                            span_text += str(s)
                        elif s.name == 'br':
                            span_text += '\n'
                        elif s.name == 'span':
                            span_text += s.get_text()
                    span_texts.append(span_text)
                content.append(f"```\n{''.join(span_texts)}\n```\n")
        
        save_content_to_files(content, f"{folder}/parsed_content")
        
        print(f"Ссылка {folder} ok")
    
    except Exception as e:
        print(f"Error occurred: {e}")

def process_subdirectories(root_dir='Inbox'):
    # Получаем список всех подпапок в указанной папке
    subdirs = [d for d in os.listdir(root_dir) if os.path.isdir(os.path.join(root_dir, d))]

    # Фильтруем подпапки, исключая 'blogs' и оставляя только те, что названы числами
    subdirs = [d for d in subdirs if d.isdigit() and d != 'blogs']

    # Сортируем подпапки по номерам (от меньшего к большему)
    subdirs.sort(key=int)

    # Инициализируем список папок для удаления
    dirs_to_remove = []

    # Перебираем все подпапки и проверяем количество файлов в каждой из них
    for subdir in subdirs:
        subdir_path = os.path.join(root_dir, subdir)
        files = [f for f in os.listdir(subdir_path) if os.path.isfile(os.path.join(subdir_path, f))]
        if len(files) < 2:
            print(f"Directory with less than two files found: {subdir_path}")
            dirs_to_remove.append(subdir_path)

    # Удаляем папки с меньше чем два файла
    for dir_path in dirs_to_remove:
        shutil.rmtree(dir_path)
        print(f"Removed directory: {dir_path}")

    # Получаем обновленный список подпапок после удаления
    subdirs = [d for d in os.listdir(root_dir) if os.path.isdir(os.path.join(root_dir, d)) and d.isdigit()]

    # Сортируем подпапки по номерам (от меньшего к большему)
    subdirs.sort(key=int)

    # Переименовываем подпапки, чтобы исключить пробелы в нумерации
    for idx, subdir in enumerate(subdirs, start=1):
        if int(subdir) != idx:
            print(f"Gap detected: Expected {idx} but got {subdir}")
        old_path = os.path.join(root_dir, subdir)
        new_path = os.path.join(root_dir, str(idx))
        os.rename(old_path, new_path)
        print(f"Renamed directory: {old_path} -> {new_path}")

    print(f"Total directories removed: {len(dirs_to_remove)}")
    print(f"Total directories renamed: {len(subdirs)}")
    
                   
def main(start_index=1):
    driver = start_browser_and_login()
    args = parse_args()  # Получаем аргументы командной строки
    start_index = args.start_index
    urls_to_parse = read_urls_from_file("partia3.txt", start_index)
    
    for index, url in enumerate(urls_to_parse, start=start_index):
        folder_name = str(index)
        # Создайте папку для каждого URL
        folder_name = str(index)
        if not os.path.exists(os.path.join('Inbox', folder_name)):
            os.makedirs(os.path.join('Inbox', folder_name))
        
        try:
            # Переходим на страницу
            driver.get(url)
        
            # Парсим и сохраняем контент
            parse_and_save_content(driver, folder_name, 'parsed_content.mdx')
            extract_and_save_second_prev_content(driver, folder_name, 'seo_tags.mdx')
        except Exception as e:
            print(f"Error occurred while processing URL {url}: {e}")
            time.sleep(10)
            continue  # Пропускаем текущий URL и продолжаем со следующего
    
    # Перемещение папки blogs в папку Inbox
    if os.path.exists('blogs'):
        shutil.move('blogs', 'Inbox/blogs')
        
    print("Готово")
    process_subdirectories()
    driver.quit()

main()