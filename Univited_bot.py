import requests
from lxml import html
from time import sleep
from lxml import etree as et
import re
from requests.exceptions import HTTPError
from token_api_telegram import return_token


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
        self.parsed_body = ''
        self.class_name = 'mb-5'
        self.els_mb5 = ''
        # Информация о произведении, кроме названия:
        self.pages = ''
        self.parts = ''
        self.tags = ''
        self.description = ''
        self.notes = ''

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
        self.link_comp = self.generating_links_to_works()
        response = requests.get(self.link_comp)
        # Преобразование тела документа в дерево элементов (DOM)
        self.parsed_body = html.fromstring(response.text)
        self.els_mb5 = self.parsed_body.find_class(self.class_name)
        # Информация о произведении, кроме названия:
        # страницы и кол-во частей
        size = str(self.els_mb5[0].text_content())
        size = re.sub("\s\s+", " ", size)
        pages , self.parts = re.findall("\d+", size)
        # Метки
        self.tags = str(self.els_mb5[1].text_content())
        self.tags = re.sub("\s\s+", " ", self.tags)
        # Описание
        self.description = str(self.els_mb5[2].text_content())
        self.description = re.sub("\s\s+", " ", self.description)
        # Примечания автора
        self.notes = str(self.els_mb5[3].text_content())
        self.notes = re.sub("\s\s+", " ", self.notes)

        return self.pages + ' страниц' + '\n' + self.parts + ' частей' + '\n' + self.tags + '\n' + \
               self.description + '\n' + self.notes


class BotHandler:

    def __init__(self, token):
        self.token = token
        self.api_url = "https://api.telegram.org/bot{}/".format(token)

    def get_updates_json(self, offset=None, timeout=30):
        # https://api.telegram.org/bot1288091950:AAGtzfTqchhqiIWbu8jxOUJBWBDaqJ-5Q4I/getUpdates
        # Получить самое последнее обновление
        params = {'timeout': timeout, 'offset': offset}
        resp = requests.get(self.api_url + 'getUpdates', data=params)
        result_json = resp.json()['result']
        return result_json

    def get_last_update(self):
        get_result = self.get_updates_json()
        #print('len(get_result)' кол-во обновлений в getUpdates)
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
#pages, parts, tags, description, notes = '', '', '', '', ''

def main():
    update_id = bot.get_last_update()['update_id'] # самый  последний update_id

    while True:
        new_offset = None
        bot.get_updates_json(new_offset)
        last_update_id = bot.get_last_update()['update_id']        # #update_id = last_update(get_updates_json(url))['update_id']
        last_chat_text = bot.get_last_update()['message']['text']
        last_chat_id = bot.get_last_update()['message']['chat']['id']
        last_chat_name = bot.get_last_update()['message']['chat']['first_name']

        last_chat_text_author_id = last_chat_text.split('/')            # 1) Команда 2) id автора 2) Название произведение
        print(last_update_id, last_chat_text, last_chat_id, last_chat_name, last_chat_text_author_id)
        if update_id == last_update_id:
            update_id = bot.get_last_update()['update_id']
            sleep(10)
        else:
            aut = Author(int(last_chat_text_author_id[2]))

            if last_chat_text_author_id[1] == 'Composition':
                Nickname_Authors_Name = aut.Authors_Name()
                Authors_Work_id = aut.Work_id()
                bot.send_message(last_chat_id, Nickname_Authors_Name + '\n'  + str(Authors_Work_id))

            if last_chat_text_author_id[1] == 'inf':
                comp_on = Composition(aut.Authors_Name(), aut.List_of_Works(), aut.Work_id(), last_chat_text_author_id[3])
                bot.send_message(last_chat_id, comp_on.generating_information_about_a_work())

            update_id = bot.get_last_update()['update_id']
            sleep(10)

if __name__ == '__main__':
    main()


        #
        # last_chat_id сохраним его в отдельную переменную, и по этим значениям можем слать сообщения

        #print(type(last_update_id), type(bot.get_last_update()['update_id']))
        #print(last_update_id == bot.get_last_update()['update_id']-1)

        #print('count_requests_last', count_requests_last, 'count_requests', count_requests)

        #if not(last_update_id == bot.get_last_update()['update_id']):     #or count_requests-1 ==  count_requests_last
            #

    ''''
        count_requests_last = count_requests
        count_requests+=1
        print('count_requests_last', count_requests_last, 'count_requests', count_requests)
        aut = Author(last_chat_text_author_id[1])
        comp_on = Composition(aut.Authors_Name(), aut.List_of_Works(), aut.Work_id(), last_chat_text_author_id[2])
        bot.send_message(last_chat_id, comp_on.generating_information_about_a_work())
    '''




'''



Name_Composition = str(input('Введиите название произведения: '))

comp_on = Composition(Nickname_Authors_Name, Authors_List_of_Works, Authors_Work_id, Name_Composition)
print(comp_on.generating_links_to_works())
print(comp_on.generating_information_about_a_work())
'''
