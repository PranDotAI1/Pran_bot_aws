import aiohttp
from typing import Any, Awaitable, Callable, Dict, Text
from rasa.core.channels.channel import InputChannel
from sanic import Blueprint, response
from sanic.request import Request
import os

class CustomRestInput(InputChannel):
 @classmethod
 def name(cls) -> Text:
 return "custom_rest"

 def blueprint(self, on_new_message: Callable[[Any], Awaitable[Any]]):
 custom_webhook = Blueprint("custom_webhook", __name__)

 @custom_webhook.route("/webhook", methods=["POST"])
 async def receive(request: Request):
 sender_id = request.json.get("sender", None)
 text = request.json.get("message", None)

 if not sender_id or not text:
 return response.json({"error": "Missing sender or message"}, status=400)

 async with aiohttp.ClientSession() as session:
 
 # Use environment variable for Rasa server URL
 rasa_url = os.getenv("RASA_SERVER_URL", "http://localhost:5005")
 async with session.post(
 f"{rasa_url}/model/parse",
 json={"text": text}
 ) as parse_resp:
 parse_result = await parse_resp.json()

 intent_name = parse_result.get("intent", {}).get("name", "unknown")
 intent_confidence = parse_result.get("intent", {}).get("confidence", 0)
 entities = parse_result.get("entities", [])

 
 async with session.post(
 f"{rasa_url}/webhooks/rest/webhook",
 json={"sender": sender_id, "message": text}
 ) as rasa_resp:
 bot_responses = await rasa_resp.json()

 bot_messages = [msg.get("text", "") for msg in bot_responses]

 
 return response.json({
 "sender": sender_id,
 "message": text,
 "intent": intent_name,
 "confidence": intent_confidence,
 "entities": entities,
 "bot_responses": bot_messages
 })

 return custom_webhook
