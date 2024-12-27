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

app = Flask(__name__)

# Load .env file
load_dotenv()

channel_access_token = os.getenv("CHANNEL_ACCESS_TOKEN")
channel_secret = os.getenv("CHANNEL_SECRET")

configuration = Configuration(access_token=channel_access_token)
handler = WebhookHandler(channel_secret)

KEYWORD_HELLO = "哈囉"
KEYWORD_XINXIN = "心心"
KEYWORD_TAGALL = "@All"
MESSAGE_HELLO = "哈囉哈囉"
MESSAGE_FOCUS = "不好意思大家!我最近比較需要專注，我比較容易分心，有訊息強迫症，我先退出群組了~  有事情可以透過ig或是line找我，謝謝！愛你們"
WARNING_MESSAGE_HELLO = "請勿哈囉！"
WARNING_MESSAGE_TAGALL = "不好意思 可以不要隨便使用@All嗎"
UID_ADAI = "U94caa77e789684671659c08bde60fce1"

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
    elif re.search(regex, event.message.text):
        line_bot_api.reply_message_with_http_info(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=WARNING_MESSAGE_HELLO)],
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

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)