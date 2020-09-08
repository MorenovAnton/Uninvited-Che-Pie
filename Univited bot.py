import requests
from lxml import html
from lxml import etree as et
import re
from requests.exceptions import HTTPError

class Author:

    def __init__(self, authors_id):
        self.authors_name = ''           # имя автора
        self.listofworks = []            # список произведений автора
        self.workid = {}                 # словарь из ключа - название произведения и значения его id
        self.authors_id = authors_id     # id автора
        self.profile_tabs = 'https://ficbook.net/authors/{}/profile/works#profile-tabs'    # профиль автора
        #self.basic_url = 'https://ficbook.net{}'
        self.author_page =  self.profile_tabs.format(authors_id)                           # ссылка на страницу автора
        #self.response_author_page = ''
        #self.parsed_author_page = ''
        self.class_name_author = 'author'              # класс парсинга имени автора
        #self.authors_name = ''
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
            #print(self.List_of_Works()[i], work_ID[i])
            self.workid[self.List_of_Works()[i]] = work_ID[i]

        return self.workid


class Composition:
    def __init__(self, Nickname_Authors_Name, Authors_List_of_Works, Authors_Work_id, Name_Composition):
        self.Nickname_Authors_Name = Nickname_Authors_Name   # имя автора
        self.Authors_List_of_Works = Authors_List_of_Works   # список произведений автора
        self.Authors_Work_id = Authors_Work_id          # словарь из ключа - название произведения и значения его id
        self.Name_Composition = Name_Composition             # Название произведения
        self.link_comp = 'https://ficbook.net{}#part_content'

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
            pass



aut = Author(1149804)
Nickname_Authors_Name = aut.Authors_Name()
Authors_List_of_Works = aut.List_of_Works()
Authors_Work_id = aut.Work_id()

print(Nickname_Authors_Name)
print(Authors_List_of_Works)
print(Authors_Work_id)
Name_Composition = str(input('Введиите название произведения: '))

comp_on = Composition(Nickname_Authors_Name, Authors_List_of_Works, Authors_Work_id, Name_Composition)
print(comp_on.generating_links_to_works())
