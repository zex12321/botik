
import logging
import os
import re
import paramiko
from pathlib import Path
from dotenv import load_dotenv
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler
import psycopg2
from psycopg2 import Error

dotenv_path = Path.cwd() / Path('.env')
load_dotenv(dotenv_path=dotenv_path)

TOKEN = os.getenv("TOKEN")

logging.basicConfig(
    filename='logfile.txt', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)


def start(update, context):
    user = update.effective_user
    update.message.reply_text(f'Привет {user.full_name}!')

def helpCommand(update, context):
    update.message.reply_text('Help!')

def findPhoneNumbersCommand(update, context):
    update.message.reply_text('Введите текст для поиска телефонных номеров: ')
    return 'findPhoneNumbers'

def findPhoneNumbers(update, context):
    user_input = update.message.text
    phoneNumRegex = re.compile(r"\+?7[ -]?\(?\d{3}\)?[ -]?\d{3}[ -]?\d{2}[ -]?\d{2}|\+?7[ -]?\d{10}|\+?7[ -]?\d{3}[ -]?\d{3}[ -]?\d{4}|8[ -]?\(?\d{3}\)?[ -]?\d{3}[ -]?\d{2}[ -]?\d{2}|8[ -]?\d{10}|8[ -]?\d{3}[ -]?\d{3}[ -]?\d{4}")
    phoneNumberList = phoneNumRegex.findall(user_input)

    phoneNumberSet = set(phoneNumberList)

    if not phoneNumberSet:
        update.message.reply_text('Телефонные номера не найдены')
        return ConversationHandler.END

    phoneNumbers = ''
    for i, phone in enumerate(phoneNumberSet, start=1):
        phoneNumbers += f'{i}. {phone}\n'

    phoneNumbers += "Записать найденные номера в базу данных? Напишите да, если записать и что угодно, если не надо"

    update.message.reply_text(phoneNumbers)
    context.chat_data['phone_numbers'] = list(phoneNumberSet)
    return 'findPhoneNumber2'

def findEmailsCommand(update, context):
    update.message.reply_text('Введите текст для поиска email-адресов: ')
    return 'findEmails'

def findEmails(update, context):
    user_input = update.message.text
    emailRegex = re.compile(r'\b[a-zA-Z0-9.!#$%&\'*+/=?^_`{|}~-]+(?:\.[a-zA-Z0-9.!#$%&\'*+/=?^_`{|}~-]+)*' \
                r'@(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}\b')
    emailList = emailRegex.findall(user_input)

    emailSet = set(emailList)

    if not emailSet:
        update.message.reply_text('Email-адреса не найдены')
        return ConversationHandler.END

    emails = ''
    for i, email in enumerate(emailSet, start=1):
        emails += f'{i}. {email}\n'

    emails += "Записать найденные почты в базу данных? Напишите да, если записать и что угодно, если не надо"
    update.message.reply_text(emails)
    context.chat_data['email_numbers'] = list(emailSet)
    return 'findEmail2'

def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    convHandlerFindPhoneNumbers = ConversationHandler(
        entry_points=[CommandHandler('find_phone_numbers', findPhoneNumbersCommand)],
        states={'findPhoneNumbers': [MessageHandler(Filters.text & ~Filters.command, findPhoneNumbers)],
                'findPhoneNumber2': [MessageHandler(Filters.text & ~Filters.command, findPhoneNumbers2)],},
        fallbacks=[]
    )

    convHandlerFindEmails = ConversationHandler(
        entry_points=[CommandHandler('find_email', findEmailsCommand)],
        states={'findEmails': [MessageHandler(Filters.text & ~Filters.command, findEmails)],
                'findEmail2': [MessageHandler(Filters.text & ~Filters.command, findEmail2)],},
        fallbacks=[]
    )
    convHandlerAptList = ConversationHandler(
        entry_points=[CommandHandler('get_apt_list', getAptListCommand)],
        states={
            'get_apt_list': [MessageHandler(Filters.text & ~Filters.command, getAptList)],
            'get_apt_list2': [MessageHandler(Filters.text & ~Filters.command, getAptList2)],
        },
        fallbacks=[]
    )
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", helpCommand))
    dp.add_handler(convHandlerFindPhoneNumbers)
    dp.add_handler(convHandlerFindEmails)
    dp.add_handler(convHandlerVerifyPassword)
    dp.add_handler(CommandHandler("get_release", get_release))
    dp.add_handler(CommandHandler("get_uname", get_uname))
    dp.add_handler(CommandHandler("get_uptime", get_uptime))
    dp.add_handler(CommandHandler("get_df", get_df))
    dp.add_handler(CommandHandler("get_free", get_free))
    dp.add_handler(CommandHandler("get_mpstat", get_mpstat))
    dp.add_handler(CommandHandler("get_w", get_w))
    dp.add_handler(CommandHandler("get_auths", get_auths))
    dp.add_handler(CommandHandler("get_critical", get_critical))
    dp.add_handler(CommandHandler("get_ps", get_ps))
    dp.add_handler(CommandHandler("get_ss", get_ss))
    dp.add_handler(CommandHandler("get_services", get_services))
    dp.add_handler(convHandlerAptList)
    dp.add_handler(CommandHandler("get_repl_logs", get_repl_logs))
    dp.add_handler(CommandHandler("get_emails", get_emails))
    dp.add_handler(CommandHandler("get_phone_numbers", get_phone_numbers))


    updater.start_polling()
    updater.idle()
def verifyPasswordCommand(update, context):
    update.message.reply_text('Введите пароль для проверки сложности: ')
    return 'verifyPassword'

def verifyPassword(update, context):
    user_input = update.message.text

    passwordRegex = re.compile(r'^(?=.*[A-Z])(?=.*[0-9])(?=.*[!@#$%^&*])(?=.{8,})')
    if passwordRegex.search(user_input):
        update.message.reply_text('Пароль сложный')
    else:
        update.message.reply_text('Пароль слишком простой, он должен содержать не менее 8 символов, буквы, цифры, заглавные буквы, а также спецсимволы!')

    return ConversationHandler.END


IP = os.getenv('RM_HOST')
PORT = os.getenv('RM_PORT')
USERNAME = os.getenv('RM_USER')
PASSWORD = os.getenv('RM_PASSWORD')

def ssh_connect():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(IP, PORT, USERNAME, PASSWORD)
    return ssh

def execute_command_ssh(command):
    ssh = ssh_connect()
    stdin, stdout, stderr = ssh.exec_command(command)
    output = stdout.read().decode(errors='ignore')
    ssh.close()
    return output

def get_release(update, context):
    release_info = execute_command_ssh("cat /etc/os-release")
    update.message.reply_text(release_info)

def get_uname(update, context):
    uname_info = execute_command_ssh("uname -a")
    update.message.reply_text(uname_info)

def get_uptime(update, context):
    uptime_info = execute_command_ssh("uptime")
    update.message.reply_text(uptime_info)

def get_df(update, context):
    df_info = execute_command_ssh("df -h")
    update.message.reply_text(df_info)

def get_free(update, context):
    free_info = execute_command_ssh("free -h")
    update.message.reply_text(free_info)

def get_mpstat(update, context):
    mpstat_info = execute_command_ssh("mpstat")
    update.message.reply_text(mpstat_info)

def get_w(update, context):
    w_info = execute_command_ssh("w")
    update.message.reply_text(w_info)

def get_auths(update, context):
    auths_info = execute_command_ssh("last -n 10")
    update.message.reply_text(auths_info)

def get_critical(update, context):
    critical_info = execute_command_ssh("journalctl -p crit -n 5")


    update.message.reply_text(critical_info)

def get_ps(update, context):
    ps_info = execute_command_ssh("ps")
    update.message.reply_text(ps_info)


def get_ss(update, context):
    ss_info = execute_command_ssh("ss -tuln")
    update.message.reply_text(ss_info)

def get_services(update, context):
    services_info = execute_command_ssh("/usr/sbin/service --status-all | grep +")
    update.message.reply_text(services_info)

def get_repl_logs(update, context):
    repl_logs = execute_command_ssh("docker logs devops_bot-db-1 | grep repl ")
    update.message.reply_text(repl_logs)

def DbSelect(my_db_command):
    connection = None
    try:
        connection = psycopg2.connect(user=os.getenv("DB_USER"),
                                      password=os.getenv("DB_PASSWORD"),
                                      host=os.getenv("DB_HOST"),
                                      port=os.getenv("DB_PORT"),
                                      database=os.getenv("DB_DATABASE"))

        cursor = connection.cursor()
        cursor.execute(my_db_command)
        data = cursor.fetchall()
        k = ''
        for row in data:
            k += str(row)[1:-1].replace(",", ".").replace("'", "") + '\n'
        logging.info("Команда успешно выполнена")
    except (Exception, Error) as error:
        logging.error("Ошибка при работе с PostgreSQL: %s", error)
    finally:
        if connection is not None:
            cursor.close()
            connection.close()
            return (k)

def get_emails(update, context):
    repl_emails = DbSelect('SELECT * FROM emails;')
    update.message.reply_text(repl_emails)

def get_phone_numbers(update, context):
    repl_numbers=DbSelect('SELECT * FROM phones;')
    update.message.reply_text(repl_numbers)


def getAptListCommand(update, context):
    update.message.reply_text('Выберете режим работы: \n 1. Вывод всех пакетов; \n 2. Поиск информации о пакете, название которого будет запрошено у пользователя. \n')

    return 'get_apt_list'

def findEmail2 (update, context):
    user_input = update.message.text
    if user_input == "да":
        email_numbers = context.chat_data.get('email_numbers')
        formatted_email = ', '.join([f"('{email}')" for email in email_numbers])
        StringForINSERT1 = 'INSERT INTO emails (mail) VALUES'
        StringForINSERT2 = ';'
        StringForINSERT = StringForINSERT1 + formatted_email + StringForINSERT2
        a = DbINSERT(StringForINSERT)
        if a == None:
            update.message.reply_text("Ошибка при работе с PostgreSQL")
        update.message.reply_text(a)
    else:
        update.message.reply_text("Вы решили не записывать номера почт в базу данных")
    return ConversationHandler.END

def findPhoneNumbers2 (update, context):
    user_input = update.message.text
    if user_input == "да":
        phone_numbers = context.chat_data.get('phone_numbers')
        formatted_phones = ', '.join([f"('{phone}')" for phone in phone_numbers])
        StringForINSERT1 = 'INSERT INTO phones (number) VALUES'
        StringForINSERT2 = ';'
        StringForINSERT = StringForINSERT1 + formatted_phones + StringForINSERT2
        a = DbINSERT(StringForINSERT)
        if a == None:
            update.message.reply_text("Ошибка при работе с PostgreSQL")
        update.message.reply_text(a)
    else:
        update.message.reply_text("Вы решили не записывать номера телефонов в базу данных")
    return ConversationHandler.END

def DbINSERT(my_db_command):
    connection = None
    try:
        connection = psycopg2.connect(user=os.getenv("DB_USER"),
                                      password=os.getenv("DB_PASSWORD"),
                                      host=os.getenv("DB_HOST"),
                                      port=os.getenv("DB_PORT"),
                                      database=os.getenv("DB_DATABASE"))

        cursor = connection.cursor()
        cursor.execute(my_db_command)
        connection.commit()
        logging.info("Команда успешно выполнена")
        a = "Команда успешно выполнена"
        cursor.close()
        connection.close()
        return(a)
    except (Exception, Error) as error:
        logging.error("Ошибка при работе с PostgreSQL: %s", error)
    finally:
        if connection is not None:
            cursor.close()
            connection.close()

def getAptList (update, context):
    user_input = update.message.text
    if user_input == '1':
        resultAptList = execute_command_ssh('apt list --installed | head -n 50')
        update.message.reply_text(resultAptList)
        return ConversationHandler.END
    elif user_input == '2':
        resultAptList = 'Введите название пакета:'
        update.message.reply_text(resultAptList)
        return 'get_apt_list2'
    else :
        resultAptList = 'не правильный выбор'
        update.message.reply_text(resultAptList)
        return ConversationHandler.END

def getAptList2 (update, context):
    user_input = update.message.text
    commandAptList2 = 'apt list --installed | grep ' + user_input
    update.message.reply_text(execute_command_ssh(commandAptList2))
    return ConversationHandler.END





if __name__ == '__main__':
    convHandlerVerifyPassword = ConversationHandler(
        entry_points=[CommandHandler('verify_password', verifyPasswordCommand)],
        states={'verifyPassword': [MessageHandler(Filters.text & ~Filters.command, verifyPassword)]},
        fallbacks=[]
    )



main()
