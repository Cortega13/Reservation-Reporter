from firebase_functions import scheduler_fn
#from firebase_functions import logger
from firebase_functions import options

from email_validator import validate_email
import phonenumbers
from bs4 import BeautifulSoup
from datetime import datetime
import pycountry
import imaplib
import email
import json
import os


from firebase_admin import initialize_app, credentials, firestore
cred = credentials.Certificate("credentials.json")
initialize_app(cred)
db = firestore.client()

from facebook_business.adobjects.serverside.custom_data import CustomData
from facebook_business.adobjects.serverside.event import Event
from facebook_business.adobjects.serverside.event_request import EventRequest
from facebook_business.adobjects.serverside.user_data import UserData
from facebook_business.api import FacebookAdsApi

@scheduler_fn.on_schedule(
    schedule="*/30 * * * *",
    min_instances=0,
    max_instances=1,
    memory=options.MemoryOption.MB_256,
    secrets=["reservation-reporter-credentials"]
)
def reservation_reporter(event: scheduler_fn.ScheduledEvent):
    envs = json.loads(os.environ.get('reservation-reporter-credentials'))
    FacebookAdsApi.init(access_token=envs["ACCESS_TOKEN"])
    process_all_emails(envs)

    # try:
    #     process_all_emails()
    # except Exception as e:
    #     logger.error(f"Error processing request: {e}")

def process_all_emails(envs):
    """Fetch and process all emails."""
    mail = connect_to_mailbox(envs)
    _, messages = mail.search(None, 'UNSEEN')
    messages = messages[0].split()
    
    for message in messages:
        process_email_message(mail, message, envs)

    mail.close()
    mail.logout()


def connect_to_mailbox(envs):
    """Connect to the IMAP mailbox."""
    mail = imaplib.IMAP4_SSL(envs["IMAP_HOST"], int(envs["IMAP_PORT"]))
    mail.login(envs["IMAP_USER"], envs["IMAP_PASS"])
    mail.select('inbox')
    return mail


def process_email_message(mail, message, envs):
    """Process an individual email message."""
    typ, msg_data = mail.fetch(message, '(RFC822)')
    if typ != 'OK':
        #logger.error("Failed to fetch mail")
        return

    for response_part in msg_data:
        if isinstance(response_part, tuple):
            msg = email.message_from_bytes(response_part[1])
            process_reservation_email(msg, envs)


def process_reservation_email(msg, envs):
    """Process reservation email."""
    subject = msg['subject']
    if "[Blue Kay Mahahual]" in subject or "Reserva Cancelada" in subject:
        email_timestamp = parse_email_date(msg['Date'])
        if msg.get_content_type() == "text/html":
            html_content = msg.get_payload(decode=True).decode('latin-1')
            reservation_data = parse_html_content(html_content)
            if reservation_data:
                save_and_process_reservation_data(reservation_data, email_timestamp, envs)


def parse_email_date(date_str):
    """Parse the date from email header."""
    return datetime.strptime(date_str[:25], '%a, %d %b %Y %H:%M:%S').timestamp()


def parse_html_content(html_content):
    """Parse HTML content to extract reservation data."""
    soup = BeautifulSoup(html_content, 'html.parser')
    reservation_holder_section = soup.find_all(string=lambda text: is_reservation_holder(text))
    if reservation_holder_section:
        table = reservation_holder_section[0].find_next('table')
        if table:
            rows = table.find_all('tr')
            for row in rows[1:]:
                cells = row.find_all('td')
                if cells:
                    name = cells[0].get_text(strip=True).lower().strip()
                    country = cells[1].get_text(strip=True).lower()
                    email_ = cells[2].get_text(strip=True)
                    phone = cells[3].get_text(strip=True)
                    value = 2000
                    currency = "mxn"
                    try:
                        value_element = soup.find('td', style="font-weight: 600; ").get_text().lower().split()
                        value = value_element[-1]
                        currency = value_element[0]
                    except:
                        pass
                    return data_validation(name, country, email_, phone, currency, value)
        else:
            #logger.error("No client information table found.")
            pass
    else:
        #logger.error("\"Reservation Holder\" section not found.")
        pass

def data_validation(name, country, email_, phone, currency, price):
    if len(country) > 2:
        country = pycountry.countries.get(name=country)
        if country:
            country = country.alpha_2.lower()
        else:
            country = "mx"

    if phone:
        try:
            phone = phonenumbers.parse(phone, "MX")
            if (phonenumbers.is_valid_number(phone)):
                phone = phonenumbers.format_number(phone, phonenumbers.PhoneNumberFormat.E164)[1:]
            else:
                phone = ""
        except:
            pass

    name = [z for z in name.split() if z != "sd"]
    if "agencia" in name:
        name = name[:name.index("agencia")]
    name = " ".join(name)

    if email_:
        try:
            emailinfo = validate_email(email_, check_deliverability=False)
            email_ = emailinfo.normalized
        except:
            pass
    return name, country, email_, phone, currency, price

def save_and_process_reservation_data(data, timestamp, envs):
    name, country, email_, phone, currency_, value_ = data
    db.collection("reservations").add({
        "name": name,
        "country": country,
        "email": email_,
        "phone": phone,
        "currency": currency_,
        "value": value_,
        "timestamp": timestamp
    })
    user_data = UserData(
        first_name=name.split()[0],
        country_codes=[country],
        emails=[email_],
        phones=[phone],
    )
    custom_data = CustomData(
        currency=currency_,
        value=float(value_),
    )
    event = Event(
        event_name='Purchase',
        event_time=int(timestamp),
        user_data=user_data,
        custom_data=custom_data,
    )
    events = [event]
    event_request = EventRequest(
        events=events,
        pixel_id=int(envs["PIXEL_ID"]),
    )
    event_response = event_request.execute()
    #logger.log(event_response)

def is_reservation_holder(text):
    conditions = [
        "Titular de la reserva",
        "Reservation holder",
        "Reservierung Halter",
        "Données de réservation"
    ]
    return any(condition in text for condition in conditions)