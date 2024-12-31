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
    PushMessageRequest,
    ReplyMessageRequest,
    StickerMessage,
    TextMessage
)
from linebot.v3.webhooks import (
    MessageEvent,
    UnsendEvent,
    StickerMessageContent,
    TextMessageContent
)

import firebase_admin
from firebase_admin import credentials
from firebase_admin import db

KEYWORD_HELLO = "哈囉"
KEYWORD_XINXIN = "心心"
KEYWORD_TAGALL = "@All"
MESSAGE_HELLO = "哈囉哈囉"
MESSAGE_FOCUS = "不好意思大家!我最近比較需要專注，我比較容易分心，有訊息強迫症，我先退出群組了~  有事情可以透過ig或是line找我，謝謝！愛你們"
MESSAGE_NEWYEAR = "新年快樂！祝大家新的一年不要再被哈囉哈囉了！"
WARNING_MESSAGE_HELLO = "請勿哈囉！"
WARNING_MESSAGE_TAGALL = "不好意思 可以不要隨便使用@All嗎"
UID_ADAI = "U94caa77e789684671659c08bde60fce1"
MAX_MESSAGE_LENGTH = 500

app = Flask(__name__)

# Load .env file
load_dotenv()

channel_access_token = os.getenv("CHANNEL_ACCESS_TOKEN")
channel_secret = os.getenv("CHANNEL_SECRET")

configuration = Configuration(access_token=channel_access_token)
handler = WebhookHandler(channel_secret)

# Fetch the service account key JSON file contents
cred = credentials.Certificate("serviceAccountKey.json")

# Initialize the app with a service account, granting admin privileges
firebase_admin.initialize_app(cred, {
    "databaseURL": "https://line-bot-hello-bc7c4-default-rtdb.asia-southeast1.firebasedatabase.app/"
})

# As an admin, the app has access to read and write all data, regradless of Security Rules
messages_ref = db.reference("messages")

allowed_chars = r".*"
pattern = allowed_chars.join(KEYWORD_HELLO)
regex = rf"{pattern}"

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

@handler.add(MessageEvent, message=TextMessageContent)
def handle_text_message(event):
    
    while messages_ref.get() == None:
        messages_ref.push({
            "order": 0,
            "user_id": "UID",
            "message_id": "MID",
            "message_text": "Message Text"
        })
        
    # Variable latest_message is a dictionary
    latest_message = messages_ref.order_by_key().limit_to_last(1).get()
    for key in latest_message:
        order = messages_ref.child(key).child("order").get() - 1
    messages_ref.push({
        "order": order,
        "user_id": event.source.user_id,
        "message_id": event.message.id,
        "message_text": event.message.text
    })
    
    if len(messages_ref.get()) > MAX_MESSAGE_LENGTH:
        # Variable oldest_message is a dictionary
        oldest_message = messages_ref.order_by_key().limit_to_first(1).get()
        for key in oldest_message:
            messages_ref.child(key).delete()
    else:
        pass
    
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        
    if True:
        line_bot_api.reply_message_with_http_info(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=MESSAGE_NEWYEAR)],
                notification_disabled=False
            )
        )
    elif event.source.user_id == UID_ADAI:
        line_bot_api.reply_message_with_http_info(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=MESSAGE_HELLO)],
                notification_disabled=True
            )
        )
    elif KEYWORD_TAGALL in event.message.text:
        line_bot_api.reply_message_with_http_info(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=WARNING_MESSAGE_TAGALL)],
                notification_disabled=True
            )
        )
    elif re.search(regex, event.message.text):
        line_bot_api.reply_message_with_http_info(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=WARNING_MESSAGE_HELLO)],
                notification_disabled=True
            )
        )
    elif KEYWORD_XINXIN in event.message.text:
        line_bot_api.reply_message_with_http_info(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=MESSAGE_FOCUS)],
                notification_disabled=True
            )
        )
    else:
        pass

@handler.add(MessageEvent, message=StickerMessageContent)
def handle_sticker_message(event):
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        
    if event.source.user_id == UID_ADAI:
        line_bot_api.reply_message_with_http_info(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=MESSAGE_HELLO)],
                notification_disabled=True
            )
        )
    else:
        pass

@handler.add(UnsendEvent)
def handle_unsend(event):
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        
    ordered_messages = messages_ref.order_by_child("order").get()
    for key in ordered_messages:
        if messages_ref.child(key).child("message_id").get() == event.unsend.message_id:
            unsend_message = messages_ref.child(key).child("message_text").get()
            line_bot_api.push_message_with_http_info(
                PushMessageRequest(
                    to=event.source.group_id,
                    messages=[TextMessage(
                        text=f"你是不是想要說：「{unsend_message}」"
                    )]
                )
            )
        else:
            pass

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)