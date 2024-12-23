from flask import Flask, request, abort, jsonify
from dotenv import load_dotenv
import os
import re

from linebot.v3 import (
    WebhookHandler
)
from linebot.v3.exceptions import (
    InvalidSignatureError
)
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage
)
from linebot.v3.webhooks import (
    MessageEvent,
    TextMessageContent
)

from google.auth.transport.requests import Request
from google.oauth2 import service_account
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file credentials.json.
SERVICE_ACCOUNT_FILE = "credentials.json"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

# The ID and range of a sample spreadsheet.
SPREADSHEET_ID = "1foihGnfiA9n8jW-f0kxvgU6KyLrZd6Ftshw81knMOIU"
RANGE_NAME = "Sheet1!A2:C"

app = Flask(__name__)

# Load .env file
load_dotenv()

channel_access_token = os.getenv("CHANNEL_ACCESS_TOKEN")
channel_secret = os.getenv("CHANNEL_SECRET")

configuration = Configuration(access_token=channel_access_token)
handler = WebhookHandler(channel_secret)


@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        app.logger.info("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)

    return 'OK'

@app.route("/get", methods=['GET'])
def get():
    # Retrieve query parameters
    param1 = request.args.get('param1', default='default_value')

    # Create a response
    response = {
        'message': 'GET method received!',
        'param1': param1
    }
    return jsonify(response)

def append_values(values):

    creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)

    try:
        service = build("sheets", "v4", credentials=creds)

        body = {"values": values}
        result = (
            service.spreadsheets()
            .values()
            .append(
                spreadsheetId=SPREADSHEET_ID,
                range=RANGE_NAME,
                valueInputOption="USER_ENTERED",
                body=body,
            )
            .execute()
        )
        print(f"{(result.get('updates').get('updatedCells'))} cells appended.")
        return result

    except HttpError as error:
        print(f"An error occurred: {error}")
        return error

keyword_hello = "哈囉"
keyword_xinxin = "心心"
hello_message = "哈囉哈囉"
hello_warning_message = "請勿哈囉！"
focus_message = "不好意思大家!我最近比較需要專注，我比較容易分心，有訊息強迫症，我先退出群組了~  有事情可以透過ig或是line找我，謝謝！愛你們"
uid_adai = "U94caa77e789684671659c08bde60fce1"
allowed_chars = r".*"
pattern = allowed_chars.join(keyword_hello)
regex = rf"{pattern}"

@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        
    if event.source.user_id == uid_adai:
        line_bot_api.reply_message_with_http_info(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=hello_message)],
                notification_disabled=True
            )
        )
    elif re.search(regex, event.message.text):
        line_bot_api.reply_message_with_http_info(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=hello_warning_message)],
                notification_disabled=True
            )
        )
    elif keyword_xinxin in event.message.text:
        line_bot_api.reply_message_with_http_info(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=focus_message)],
                notification_disabled=True
            )
        )
    else:
        pass
    
    append_values([[event.source.user_id, event.message.id, event.message.text]])

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)