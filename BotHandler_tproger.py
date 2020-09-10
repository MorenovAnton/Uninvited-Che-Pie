# этот файл мы не станем добалять в git
from time import sleep
import requests

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

    def get_chat_id(self, update):
        # Первая будет доставать chat_id из обновления
        chat_id = update['message']['chat']['id']
        return chat_id

    def send_message(self, chat_id, text):
        params = {'chat_id': chat_id, 'text': text}
        resp = requests.post(self.api_url + 'sendMessage', data=params)
        return resp





bot = BotHandler(token)


def main():
    new_offset = None

    while True:
        bot.get_updates_json(new_offset)
        last_update = bot.get_last_update()

        last_update_id = last_update['update_id']        # #update_id = last_update(get_updates_json(url))['update_id']
        last_chat_text = last_update['message']['text']
        last_chat_id = bot.get_chat_id(last_update)
        last_chat_name = last_update['message']['chat']['first_name']

        print(last_update_id, last_chat_text, last_chat_id, last_chat_name)  # last_chat_id сохраним его в отдельную переменную, и по этим значениям
        # можем слать сообщения






        #if update_id == last_update(get_updates_json(url))['update_id']:
           #send_mess(get_chat_id(last_update(get_updates_json(url))), 'test')
           #update_id += 1
        #sleep(1)

if __name__ == '__main__':  
    main()



