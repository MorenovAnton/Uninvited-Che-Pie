import Univited_bot
from time import sleep
import time
import threading
import random


def main():
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
            #sleep(5)
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
                # Если мы еще не ослеживаем это произведение
                # Если ссылки на это произведение нет в словере отслеживаемых list_tracking_point произведений
                if composition.generating_links_to_works() not in Univited_bot.list_tracking_point:
                    # добавлеем в словарь -> list_tracking_point (ссылку на произведение: произведение)
                    Univited_bot.list_tracking_point[composition.generating_links_to_works()]  = composition
                    # формируем текущее кол-вл частей у произведения
                    parts = composition.generating_information_dict_numberOFchapters_published()
                    # в словарь dictionary_numberOFchapters_published по произведению добавляем кол-во у него частей
                    Univited_bot.dictionary_numberOFchapters_published[composition] = parts
                    # dictionary_chat_id_and_tracking_point словарь список chat_id которые следят за книгой
                    Univited_bot.dictionary_chat_id_and_tracking_point[composition.generating_links_to_works()].append(last_chat_id)

                    #print('list_tracking_point', Univited_bot.list_tracking_point)
                    #print('dictionary_numberOFchapters_published', Univited_bot.dictionary_numberOFchapters_published)
                    #print('dictionary_chat_id_and_tracking_point', Univited_bot.dictionary_chat_id_and_tracking_point)
                else:
                    # Проверка что в dictionary_chat_id_and_tracking_point (по ключу ссылки на произведение) мы не добавим id чата коорый уже
                    # отслеживает это произведение
                    if last_chat_id not in Univited_bot.dictionary_chat_id_and_tracking_point[composition.generating_links_to_works()]:
                        Univited_bot.dictionary_chat_id_and_tracking_point[composition.generating_links_to_works()].append(last_chat_id)
                        #print('dictionary_chat_id_and_tracking_point', Univited_bot.dictionary_chat_id_and_tracking_point)

            if last_chat_text_author_id[1] == 'my_author':
                # должны показать авторов/произведения которые отслеживает человек
                pass

            update_id = last_update_id
            #sleep(10)

        if time.time() - starttime  > 120:
            starttime = time.time()
            # Проходим по всем отслеживаемым произведениям:
            for link_composition in Univited_bot.list_tracking_point:
                # ссылка на произведение
                print(link_composition)
                # кол-во частей у произведения
                #print('*--->', Univited_bot.dictionary_numberOFchapters_published[Univited_bot.list_tracking_point[link_composition]])
                #print('*--->', Univited_bot.list_tracking_point[link_composition].generating_information_dict_numberOFchapters_published())
                ''''
                #Генерируем колво частей у произведения, сравниваем его с кол-вом частей которое хранятся в словаре
                #и если по generating_information_dict_numberOFchapters_published получилось больше изменяем
                #кол-во частей в словаре
                '''
                if Univited_bot.dictionary_numberOFchapters_published[Univited_bot.list_tracking_point[link_composition]] \
                    != Univited_bot.list_tracking_point[link_composition].generating_information_dict_numberOFchapters_published():

                    # Проходим по всем chat id в которые нужно послать оповещение
                    for chat_ID in Univited_bot.dictionary_chat_id_and_tracking_point[link_composition]:
                        Univited_bot.bot.send_message(chat_ID, "В произведении {}, изменилось кол-во глав".format(link_composition))

                    # изменяем кол-во частей в словаре
                    Univited_bot.dictionary_numberOFchapters_published[Univited_bot.list_tracking_point[link_composition]] \
                    = Univited_bot.list_tracking_point[link_composition].generating_information_dict_numberOFchapters_published()



if __name__ == '__main__':
    main()
