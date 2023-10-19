# Очистка списка ссылок от параметров
import re

def clean_links(input_file, output_file):
    with open(input_file, 'r') as infile:
        urls = infile.readlines()

    cleaned_urls = [re.sub(r'\?.*', '', url) for url in urls]

    with open(output_file, 'w') as outfile:
        outfile.write(''.join(cleaned_urls))

# Пример вызова функции
input_file = 'partia4.txt'  # Название вашего входного файла
output_file = 'partia4_utils.txt'  # Название вашего выходного файла

clean_links(input_file, output_file)
