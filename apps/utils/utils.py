import random,xmltodict
import datetime
import secrets, string
import requests
from core import settings



def generate_code():
    code =random.randint(1000, 9999)   

    return code

def generate_sms_id():
    return secrets.token_hex(32)


def generate_string_code(len:int) -> str:
    return ''.join(random.choices('0123456789', k=len))


STATUS_CHOICE = {
    0:"Сообщения успешно приняты к отправке",
    1:"Ошибка в формате запроса",
    2:"Неверная авторизация",
    3:"Недопустимый IP-адрес отправителя",
    4:"Недостаточно средств на счету клиента,Ошибка сервера",
    5:"Недопустимое имя отправителя",
    6: """Сообщение заблокировано по стоп-словам (в сообщении содержатся слова,блокируемые роботом. Например, нецензурная лексика)""",
    7: "Некорректное написание одного или нескольких номеров телефонов получателей",
    8:"Неверный формат времени отправки",
    9: """Превышение времени обработки запроса (при большом количестве одновременных запросов от клиента). Необходимо повторить запрос с тем же id через 5-10 сек.""",
    10:"""Отправка заблокирована (ошибочная переотправка)....попробуйте через 5 минут""",
    11:"""Сообщение успешно обработано, но не принято к отправке пожалуйств связывайтесь с подержкой"""
}


def to_xml_data(login, password, id, sender, text, phone) -> str:
    xml_data = f"""<?xml version=\"1.0\" encoding=\"UTF-8\"?>
    <message>
        <login>{login}</login>
        <pwd>{password}</pwd>
        <id>{id}</id>
        <sender>{sender}</sender>
        <text>Не делитесь своим кодом. Ваш код для подтверждения: {text}</text>
        <phones>
            <phone>{phone}</phone>
        </phones>
    </message>"""
    return xml_data

def send_code(id, code, phone) -> list:
    api_url = "http://smspro.nikita.kg/api/message"
    id = str(id)
    code = str(code)
    phone = str(phone).replace("+", "")
    login = str(settings.NIKITA_SMPT_LOGIN)
    password = str(settings.NIKITA_SMPT_PASSWORD)
    sender_name = str(settings.NIKITA_SMPT_SENDER_NAME)

    xml_payload = to_xml_data(login=login, 
                              password=password, 
                              sender=sender_name,
                              text=code, id=id,
                              phone=phone)
    print(xml_payload.encode('utf-8'))
    headers = {"Content-Type": "application/xml; charset=UTF-8"}

    try:
        response = requests.post(api_url, data=xml_payload.encode('utf-8'), headers=headers)
        print(response.request.body)
        response.raise_for_status()
        xml_response = response.text
        dict_response = xmltodict.parse(xml_response)
        status_code = int(dict_response['response']['status'])
        return response.status_code, STATUS_CHOICE[status_code], response.text

    except requests.exceptions.RequestException as e:
        return f"Ошибка при отправке запроса: {e}"
    except Exception as e:
        return f"Произошла ошибка: {e}"

def make_bool(val):
    if str(val) == 'false' or str(val) == '0' or str(val) == 'False':
        return False
    else:
        return True



def make_next_date(day):
    now = datetime.datetime.now()
    return now + datetime.timedelta(days=day)



def get_object_or_none(model, **kwargs):
    try:
        return model.objects.get(**kwargs)
    except model.DoesNotExist as e:
        return None

def get_filter_object_or_none(model, **kwargs):
    try:
        return model.objects.filter(**kwargs).latest('created_at')
    
    except model.DoesNotExist as e:
        return None


def make_password():
    letters = string.ascii_letters
    digits = string.digits
    alphabet = letters + digits
    pwd_length = 9
    pwd = ''
    for i in range(pwd_length):
        pwd += ''.join(secrets.choice(alphabet))
    return pwd



def build_absolute_url(file):
    return f"{settings.SITE_CURRENT_HOST_MEDIA_ROOT}{file.url}"