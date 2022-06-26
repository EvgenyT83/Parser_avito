import time

import pandas
import requests
import re
from bs4 import BeautifulSoup
from pandas import ExcelWriter
from hyper.contrib import HTTP20Adapter

# parser avito с сохранением в эксель


url = 'https://www.avito.ru/'

go_headers = {
        "Accept": "*/*",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.160 YaBrowser/22.5.2.612 Yowser/2.5 Safari/537.36"
    }


search = input('Введите запрос поиска: ')
min_price = input('Введите минимальную стоимость: ')
max_price = input('Введите максимальную стоимость: ')

# search = 'велосипед'
# min_price = '25000'
# max_price = '50000'

s = requests.Session()
s.mount('https://', HTTP20Adapter())
resp = s.get(url, headers=go_headers, params={'bt': 1, 'pmax': max_price, 'pmin': min_price, 'q': search, 's': '2', 'view': 'gallery'})
print('Ссылка со всеми параметрами:\n', resp.url)
print(resp.status_code)
soup = BeautifulSoup(resp.text, 'html.parser')


# вытаскиваем заголовок основной темы страницы (вариант 2)
h1 = soup.h1.get_text()

# находим кол-во страниц, иначе количество страниц равно 1
try:
    str = soup.find('span', {'data-marker': 'pagination-button/next'}).previous_element
except:
    str = 1

print(f'Категория: {h1}\nКоличество страниц: {str}')

pagination = int(input('Введите кол-во страниц: '))

# важно ставить список с данными до цикла, иначе data будет перезаписываться данными с новых страниц
data = []
my_city = "ekaterinburg"
print('Мой город:', my_city)
# реализуем проход по страницам
for page in range(1, pagination + 1):
    response = s.get(url, headers=go_headers, params={'bt': 1, 'p': page, 'pmax': max_price, 'pmin': min_price, 'q': search, 's': '104', 'view': 'gallery'})
    soup = BeautifulSoup(response.text, 'html.parser')
    blocks = soup.find_all('div', class_=re.compile('iva-item-root'))
    # сбор данных с страницы
    for block in blocks:
        # выберем только те результаты, которые относятся к нашему городу
        if my_city == block.find('a', class_=re.compile('link-link')).get('href').split('/')[1]:
            data.append({
                'title': block.find('a', class_=re.compile('link-link')).get_text(strip=True),
                'price': int(block.find('span', class_=re.compile('price-text')).get_text(strip=True).replace('₽', '').replace('\xa0', '').replace('за час', '').replace('от ', '').replace('за услугу', '')),
                'city': block.find('a', class_=re.compile('link-link')).get('href').split('/')[1],
                'district': block.find('div', class_=re.compile('geo-root')).get_text(strip=True),
                'link': url + block.find('a', class_=re.compile('link-link')).get('href'),
            })
    time.sleep(1)
    print(f'Парсинг страницы {page} из {pagination}')

print(f'Количество собранных позиций по городу "{my_city}": {len(data)}')


# сохраняем полученные данные в эксель с помощью dataframe от pandas
dataframe = pandas.DataFrame(data)
newdataframe = dataframe.rename(columns={
    'title': 'Наименование', 'price': 'Цена, ₽',
    'link': 'Ссылка', 'city': 'Город', 'district': 'Район'
})
writer = ExcelWriter(f'results/{search}.xlsx')
newdataframe.to_excel(writer, f'{search}')
writer.save()
print(f'Данные сохранены в файл "{search}.xlsx"')
