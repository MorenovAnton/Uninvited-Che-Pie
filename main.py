import Univited_bot
from time import sleep
import time
import threading
import random
from mysql_server_connect import create_connection, execute_read_query, execute_query
from connection_parameters import mysql_parameters
import re
import requests
from lxml import html


def main():
    connection = create_connection(*mysql_parameters())
    print("---------------------->", connection, "<----------------------")
    update_id = Univited_bot.bot.get_last_update()['update_id'] # самый  последний update_id
    starttime = time.time()

    while True:
        last_parameters = Univited_bot.bot.get_last_update()

        last_update_id = last_parameters['update_id']
        last_chat_text = last_parameters['message']['text']
        last_chat_id = last_parameters['message']['chat']['id']
        last_chat_name = last_parameters['message']['chat']['first_name']

        last_chat_text_author_id = last_chat_text.split('/')            # 1) Команда 2) id автора 2) Название произведение
        print(last_update_id, last_chat_text, last_chat_id, last_chat_name, last_chat_text_author_id)

        '''
        #Есди update_id полученный при первом запуске совпадает с последним last_update_id т.е если новых запосов
        #не было, update_id присваивается последний Univited_bot.bot.get_last_update()['update_id']
        #и ждем некоторое время до новой проверки полученных сообщений
        '''
        if update_id == last_update_id:
            update_id = last_update_id
        else:
            '''
            #Если это не так и разница между update_id и last_update_id есть, т.е если за это время были новые
            #поступления данны/запросы в бот
            '''
            aut = Univited_bot.Author(int(last_chat_text_author_id[2]))
            Nickname_Authors_Name, Authors_Work_id, List_of_Works = '', '', ''
            
            try:
                Nickname_Authors_Name = aut.Authors_Name()
                Authors_Work_id = aut.Work_id()
                List_of_Works = aut.List_of_Works()
            except IndexError:
                Univited_bot.bot.send_message(last_chat_id, 'Не удалось получить имя автора, возможно не созданно '
                                                                'ни одного произведения или в работе 0 частей')

            ''' получаем список произведений (Composition) автора '''
            if last_chat_text_author_id[1] == 'сom':
                Univited_bot.bot.send_message(last_chat_id, Nickname_Authors_Name + '\n'  + str(Authors_Work_id))

            ''' получаем информацию об произведении '''
            if last_chat_text_author_id[1] == 'inf':
                composition = Univited_bot.Composition(Nickname_Authors_Name, List_of_Works, Authors_Work_id, last_chat_text_author_id[3])
                Univited_bot.bot.send_message(last_chat_id, composition.generating_information_about_a_work())

            ''' формируем список произведений за которыми будет производиться слежка '''
            if last_chat_text_author_id[1] == 'trac':
                # формируем объект проиизведение:
                composition = Univited_bot.Composition(Nickname_Authors_Name, List_of_Works, Authors_Work_id, last_chat_text_author_id[3])
                idcomposition = re.findall("\d+", composition.generating_links_to_works()) # # вот как раз этот id произведения будем добавлять в базу в idcomposition_numberpart
                # Если мы еще не ослеживаем это произведение то у нас нет записи данного id произвежения в idcomposition_numberpart
                сheck_existence_idcomposition = execute_read_query(connection, "SELECT * from idcomposition_numberpart idc where idc.idcomposition={};".format(*idcomposition))
                print('сheck_existence_idcomposition', сheck_existence_idcomposition)
                # если ничего не будет то check_existence_idcomposition выведет пустой массив [], в этом случае мы должны, получить кол-во частей у  данного произведения и записать в базу
                # это  значит что записи для этого произведения вообще нету в базе
                if not сheck_existence_idcomposition:
                    # формируем текущее кол-вл частей у произведения
                    parts = composition.generating_information_dict_numberOFchapters_published()
                    execute_query(connection, "INSERT INTO idcomposition_numberpart VALUES ({}, {});".format(*idcomposition, parts))
                    # записываем также нового пользователя в idcomposition_chatid
                    execute_query(connection, "INSERT INTO idcomposition_chatid VALUES ({}, {}, {});".format(*idcomposition, last_chat_id, 1))

                # в этом случае в idcomposition_numberpart присутствует id необходимого произведения и в таблице храниться кол-во частей этого произведения
                # значит существуют люди которые отслеживают, или отслеживали произведение. Проверяем входит ли в них пользователь и если нет, добавляем его
                if сheck_existence_idcomposition:
                    # чаты которые отслеживают это произведение
                    get_chat_id = execute_read_query(connection, "SELECT ch.chat_id from idcomposition_chatid ch, idcomposition_numberpart idn where \
                                                                                idn.idcomposition = {} and ch.status = 1;".format(*idcomposition))
                    # проверяем отслеживвал ли человек это произведение, если id этого чата нету в отслеживааемых добавдяем в idcomposition_chatid
                    if last_chat_id not in get_chat_id[0]:
                        execute_query(connection, "INSERT INTO idcomposition_chatid VALUES ({}, {}, {});".format(*idcomposition, last_chat_id, 1))

                    # посмотри если этот человек раньше отслеживаал это произведение, в idcomposition_chatid  его статус может быть равен 0
                    # в этом случае его можно переписывать

            if last_chat_text_author_id[1] == 'my_author':
                # должны показать авторов/произведения которые отслеживает человек
                pass

            update_id = last_update_id


        # здесь composition уже использовать нельзя
        if time.time() - starttime  > 10: # 40
            starttime = time.time()
            # Проходим по всем отслеживаемым произведениям:
            idcomp_status_yes = execute_read_query(connection, "SELECT ch.idcomp from idcomposition_chatid ch where ch.status = 1;")
            # проходим по idcomp_status_yes и формируем ссылки на произведения, если существующее кол-во частей отличаются с существующим в базе, шлем оповещение
            for id_link_composition in idcomp_status_yes[0]:
                # ссылка на произведение
                link_composition = 'https://ficbook.net/readfic/{}#part_content'.format(id_link_composition)
                # кол-во частей у произведения
                response = requests.get(link_composition)
                parsed_body = html.fromstring(response.text)
                els_mb5 = parsed_body.find_class('mb-5')
                len_els_mb5 = len(els_mb5)
                information_work = [re.sub("\s\s+", " ", str(els_mb5[t].text_content())) for t in range(len_els_mb5)]
                for inf_w in information_work:
                    # Cтраницы и кол-во частей
                    if re.findall("Размер.+", inf_w):
                        parts = re.findall("\d+", inf_w)[1]   # кол-во частей при опросе

                # получаем кол-во частей произведения хранящийся в базе
                numberpart_in_idcomposition_numberpart = execute_read_query(connection, "SELECT idc.numberpart from idcomposition_numberpart idc where idc.idcomposition={};".format(id_link_composition))
                numberpart_in_idcomposition_numberpart =   int(*numberpart_in_idcomposition_numberpart[0])

                '''
                Если кол-во частей при опросе отсличаются от данных в базе, получаем id всех чатов из базы которые отслеживвают данное произведение, 
                а так же меняем в базе значение numberpart в idcomposition_numberpart и шлем оповещение по id этих чатов
                '''
                # /inf/4751346/testB
                if  parts != numberpart_in_idcomposition_numberpart:
                    get_chat_idin_idcomposition_chatid = execute_read_query(connection, "SELECT ch.chat_id from idcomposition_chatid ch where ch.idcomp={};".format(id_link_composition))

                print('get_chat_idin_idcomposition_chatid', get_chat_idin_idcomposition_chatid)



                    # Проходим по всем chat id в которые нужно послать оповещение
                    #for chat_ID in Univited_bot.dictionary_chat_id_and_tracking_point[link_composition]:
                        #Univited_bot.bot.send_message(chat_ID, "В произведении {}, изменилось кол-во глав".format(link_composition))

                    # изменяем кол-во частей в словаре
                    #Univited_bot.dictionary_numberOFchapters_published[Univited_bot.list_tracking_point[link_composition]] \
                    #= Univited_bot.list_tracking_point[link_composition].generating_information_dict_numberOFchapters_published()


if __name__ == '__main__':
    main()
