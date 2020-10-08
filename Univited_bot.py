import requests
from lxml import html
from lxml import etree as et
import re
from requests.exceptions import HTTPError
from token_api_telegram import return_token
from collections import defaultdict

class Author:

    def __init__(self, authors_id):
        self.authors_name = ''           # имя автора
        self.listofworks = []            # список произведений автора
        self.workid = {}                 # словарь из ключа - название произведения и значения его id
        self.authors_id = authors_id     # id автора
        self.profile_tabs = 'https://ficbook.net/authors/{}/profile/works#profile-tabs'    # профиль автора
        self.author_page =  self.profile_tabs.format(authors_id)                           # ссылка на страницу автора
        self.class_name_author = 'author'             # класс парсинга имени автора
        self.class_List_of_Works = 'visit-link'        # класс персинга произведений автора


    def GET_Authors_page(self, author_page):
        '''
        get запрос по id автора,  author_page - ссылка на страницу профиля автора, формируемая
        в __init__ из profile_tabs и authors_id (передается в класс).
        html.fromstring(response.text) Преобразование тела документа в дерево элементов.
        Конвертировать полученную информацию в строку в кодировке UTF-8. response делает это при помощи .text.
        '''
        response_author_page = requests.get(author_page)
        # Преобразование тела документа в дерево элементов (DOM)
        parsed_author_page = html.fromstring(response_author_page.text)
        return parsed_author_page

    def Authors_Name(self):
        '''
        Получить имя автора,
        find_class - Возвращает список всех элементов с заданным именем класса CSS
        https://lxml.de/lxmlhtml.html
        sub - заменить все вхождения  \s - Любой пробельный символ (пробел, табуляция, конец строки и т.п.)
        + 	Одно или более, синоним {1,}
        '''
        name_author_page = self.GET_Authors_page(self.author_page).find_class(self.class_name_author)
        authors_name = str(name_author_page[0].text_content())
        authors_name = re.sub("\s\s+", " ", authors_name)
        return authors_name

    def List_of_Works(self):
        '''
        Сформировать список произведений автора
        '''
        els_author_page = self.GET_Authors_page(self.author_page).find_class(self.class_List_of_Works)
        listofworks = [work.text_content() for work in els_author_page]
        return listofworks

    def Work_id(self):
        '''
        Свормировать словарь из названия произведения и ссылки на произведения типа /readfic/8957213
        xpath - Выполнение xpath в дереве элементов
        \d - цифрма + Одно или более, синоним {1,}
        '''
        workid_author_page = str(self.GET_Authors_page(self.author_page).xpath('//a/@href'))
        work_ID = re.findall("/readfic/+\d+", workid_author_page)

        for i in range(len(work_ID)):
            self.workid[self.List_of_Works()[i]] = work_ID[i]
        return self.workid



class Composition:
    def __init__(self, Nickname_Authors_Name, Authors_List_of_Works, Authors_Work_id, Name_Composition):
        self.Nickname_Authors_Name = Nickname_Authors_Name   # имя автора
        self.Authors_List_of_Works = Authors_List_of_Works   # список произведений автора
        self.Authors_Work_id = Authors_Work_id          # словарь из ключа - название произведения и значения его id
        self.Name_Composition = Name_Composition             # Название произведения
        self.link_comp = 'https://ficbook.net{}#part_content'
        self.class_name = 'mb-5'

    def generating_links_to_works(self):
        '''
        Генерация ссылки на произведение, если название произведения (Name_Composition), присутствует в
        списке Authors_List_of_Works произведений, то обращаемся к словарю Authors_Work_id для вытягивания
        /readfic/8205186 и формируем ссылку на произведение
        '''
        if self.Name_Composition in self.Authors_List_of_Works:
            self.link_comp = self.link_comp.format(self.Authors_Work_id[self.Name_Composition])
            return self.link_comp
        else:
            return "Произведение не найденно, невозможно создать link, пожалуйста введите правильное название произведения"

    def generating_information_about_a_work(self):
        '''
        Генерация информации о произведении, /inf/Id атора/Произведение
        '''
        self.link_comp = self.generating_links_to_works()
        response = requests.get(self.link_comp)
        # Преобразование тела документа в дерево элементов (DOM)
        parsed_body = html.fromstring(response.text)
        els_mb5 = parsed_body.find_class(self.class_name)
        len_els_mb5 = len(els_mb5)
        information_work = [re.sub("\s\s+", " ", str(els_mb5[t].text_content())) for t in range(len_els_mb5)]
        # Информация о произведении, кроме названия:
        for inf_w in information_work:
            # Cтраницы и кол-во частей
            if re.findall("Размер.+", inf_w):
                size = re.findall("\d+", inf_w)   # ['417', '18']
            # Метки
            if re.findall("Метки.+", inf_w):
                tags = inf_w
            # Описание
            if re.findall("Описание.+", inf_w):
                description = inf_w
            # Примечания автора
            if re.findall("Примечания автора.+", inf_w):
                notes = inf_w

        return size[0] + ' страниц' + '\n' + size[1] + ' частей' + '\n' + tags + '\n' + \
               description + '\n' + notes


    def generating_information_dict_numberOFchapters_published(self):
        self.link_comp = self.generating_links_to_works()
        response = requests.get(self.link_comp)
        parsed_body = html.fromstring(response.text)
        els_mb5 = parsed_body.find_class(self.class_name)
        len_els_mb5 = len(els_mb5)
        information_work = [re.sub("\s\s+", " ", str(els_mb5[t].text_content())) for t in range(len_els_mb5)]
        for inf_w in information_work:
            # Cтраницы и кол-во частей
            if re.findall("Размер.+", inf_w):
                parts = re.findall("\d+", inf_w)[1]   # ['417', '18']
        return parts

class BotHandler:

    def __init__(self, token):
        self.token = token
        self.api_url = "https://api.telegram.org/bot{}/".format(token)

    def get_updates_json(self, offset=None, timeout=30):
        # Получить самое последнее обновление
        params = {'timeout': timeout, 'offset': offset}
        resp = requests.get(self.api_url + 'getUpdates', data=params)
        result_json = resp.json()['result']
        return result_json

    def get_last_update(self):
        get_result = self.get_updates_json()
        if len(get_result) > 0:
            last_update = get_result[-1]
        else:
            last_update = get_result[len(get_result)]

        return last_update

    def send_message(self, chat_id, text):
        params = {'chat_id': chat_id, 'text': text}
        resp = requests.post(self.api_url + 'sendMessage', data=params)
        return resp


token = return_token()
bot = BotHandler(token)

list_tracking_point = {}
dictionary_numberOFchapters_published = {}
dictionary_chat_id_and_tracking_point = defaultdict(list)

