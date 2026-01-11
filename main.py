from dotenv import load_dotenv
from gmail_reader import fetch_unread_emails
from mailgraph import graph_mail
load_dotenv()

mailmindRun = graph_mail()
email_data=fetch_unread_emails()
if email_data:
    result = mailmindRun.invoke({"input_email":email_data[0]})
    print(result)
else:
    print("No Unread Mails")