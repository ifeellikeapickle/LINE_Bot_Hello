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

from config import (
    KEYWORD_HELLO,
    KEYWORD_XINXIN,
    MESSAGE_FOCUS,
    MESSAGE_NEWLINE,
    MESSAGE_SUBWAY,
    WARNING_MESSAGE_HELLO,
    WARNING_MESSAGE_TAGALL,
    WARNING_MESSAGE_TAGSELF,
    UID_PANG,
    MAX_MESSAGE_LENGTH
)

def add_message(messages, new_message):
    if messages:
        messages += MESSAGE_NEWLINE
    messages += new_message
    return messages

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
    
    # Push a default message if the database is empty
    while messages_ref.get() is None:
        messages_ref.push({
            "order": 0,
            "user_id": "UID",
            "message_id": "MID",
            "message_text": "Message Text"
        })
        
    # Variable latest_message is a dictionary
    # Get the order of the last message and push the current message to the database
    latest_message = messages_ref.order_by_key().limit_to_last(1).get()
    for key in latest_message:
        order = messages_ref.child(key).child("order").get() - 1
    messages_ref.push({
        "order": order,
        "user_id": event.source.user_id,
        "message_id": event.message.id,
        "message_text": event.message.text
    })
    
    # Delete the oldest message if the messages exceed
    if len(messages_ref.get()) > MAX_MESSAGE_LENGTH:
        # Variable oldest_message is a dictionary
        oldest_message = messages_ref.order_by_key().limit_to_first(1).get()
        for key in oldest_message:
            messages_ref.child(key).delete()
    else:
        pass
    
    # Get ApiClient ready for reply
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
    
    reply_message_text  = ""
    dont_warn_hello     = False
    
    if event.message.mention is not None:
        mentionees_list     = event.message.mention.mentionees
        mention_all         = False
        mention_self        = False
        mention_pang        = False
        for mentionee in mentionees_list:
            if mentionee.type == "all":
                mention_all = True
            if mentionee.type == "user":
                if mentionee.is_self:
                    mention_self = True
                    dont_warn_hello = True
                if mentionee.user_id == UID_PANG:
                    mention_pang = True
#        if mention_all:
#            reply_message_text = add_message(reply_message_text, WARNING_MESSAGE_TAGALL)
        if mention_self:
            reply_message_text = add_message(reply_message_text, WARNING_MESSAGE_TAGSELF)
#        if mention_pang:
#            reply_message_text = add_message(reply_message_text, MESSAGE_SUBWAY)
    if re.search(regex, event.message.text) and not dont_warn_hello:
        reply_message_text = add_message(reply_message_text, MESSAGE_FUCKPY)
#    if KEYWORD_XINXIN in event.message.text:
#        reply_message_text = add_message(reply_message_text, MESSAGE_FOCUS)
        
    if reply_message_text:
        line_bot_api.reply_message_with_http_info(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=reply_message_text)],
                notification_disabled=True
            )
        )
    else:
        pass

# @handler.add(MessageEvent, message=StickerMessageContent)
# def handle_sticker_message(event):
#     with ApiClient(configuration) as api_client:
#         line_bot_api = MessagingApi(api_client)
#         
#     if event.source.user_id == UID_ADAI:
#         line_bot_api.reply_message_with_http_info(
#             ReplyMessageRequest(
#                 reply_token=event.reply_token,
#                 messages=[TextMessage(text=MESSAGE_HELLO)],
#                 notification_disabled=True
#             )
#         )
#     else:
#         pass

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
                        text=f"你是不是想要說：\n\n「{unsend_message}」"
                    )]
                )
            )
        else:
            pass

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
