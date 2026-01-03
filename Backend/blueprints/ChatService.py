from flask import Blueprint, render_template, request, jsonify, abort
from flask_jwt_extended import jwt_required
from jinja2 import TemplateNotFound
from typing import Final
import FetchCities

import threading
import torch
import re

# MODEL_NAME: Final[str] = 'HuggingFaceTB/SmolLM2-360M-Instruct'
MODEL_NAME: Final[str] = 'Qwen/Qwen2.5-0.5B-Instruct'
nlp = None

MODEL_EVENT = threading.Event()
model_lock = threading.Lock()
tokenizer = None
model = None

chat_route = Blueprint('chat', __name__, url_prefix = '/chat')

def _load_resources():
    global nlp, tokenizer, model, MODEL_NAME

    import spacy
    nlp = spacy.load("en_core_web_sm")

    from transformers import AutoModelForCausalLM, AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForCausalLM.from_pretrained(MODEL_NAME)
    model.eval()
    print(f'Assistant is ready to go on {next(model.parameters()).device}.')
    MODEL_EVENT.set()

def build_prompt(user_text):
    return (
        f"""
        You are a friendly and helpful assistant named Chip working for TripLink.
        Your role is to assist users quickly and politely, in short and natural English.
        Always keep messages clear, concise, and approachable.
        Use a friendly tone with occasional casual expressions or emojis, but never overdo it. 

        Guidelines:
        1. Always respond in English.
        2. Keep answers short (1 sentence).
        3. Be polite, friendly, and helpful.
        4. Use clear instructions or explanations when needed.
        5. Avoid technical jargon; write like a human assistant.
        6. Make the user feel welcome and supported.
        7. Include emojis occasionally to make messages friendly, but keep them minimal.

        Example interactions:
        User: How do I book a car?
        Assistant: Just pick your location and time, and tap “Book”! 🚗

        User: Can I cancel my reservation?
        Assistant: Yes! Go to your bookings and hit “Cancel.” You'll get a confirmation. 😊

        User: Do I need to pay upfront?
        Assistant: You can pay when you book or at pickup, whichever works best for you.

        User: Are your cars available 24/7?
        Assistant: Most cars are available anytime, but some locations may have hours. Check the map! 🕒

        User: {user_text}
        Assistant:"""
    )

def build_info_prompt(user_text, text):
    return (
        f"""
        You are a friendly and helpful assistant named Chip working for TripLink.
        Your role is to assist users quickly and politely, in short and natural English.
        Always keep messages clear, concise, and approachable.
        Use a friendly tone with occasional casual expressions or emojis, but never overdo it. 

        Guidelines:
        1. Always respond in English.
        2. Keep answers short (1 sentence).
        3. Be polite, friendly, and helpful.
        4. Use clear instructions or explanations when needed.
        5. Avoid technical jargon; write like a human assistant.
        6. Make the user feel welcome and supported.
        7. Include emojis occasionally to make messages friendly, but keep them minimal.

        Example interactions:
        User: What's the distance from A to B?
        Info: The distance from A to B is around 3 km.
        Assistant: The distance from A to B is around 3 km, decently short! 🚗

        User: What's the price from A to B?
        Info: The price from A to B is around 50 RON.
        Assistant: The price from A to B is around 50 RON, but depends on the driver! 😊

        User: {user_text}
        Info: {text}
        Assistant:"""
    )

@chat_route.get('')
def chat_page():
    try:
        return render_template("chat.html")
    except TemplateNotFound:
        abort(404)

def detect_intent(text):
    text = text.lower()
    if any(k in text for k in ["distance", "far", "how long"]):
        return "distance"
    if any(k in text for k in ["price", "cost", "fare"]):
        return "price"
    
    return "chat"

def extract_locations(text):
    doc = nlp(text)
    locations = [
        ent.text for ent in doc.ents
        if ent.label_ in ("GPE", "LOC")
    ]

    return locations

def estimate_trip_cost(distance_km, cost_per_km=1.12, service_fee=2.0):
    return round(distance_km * cost_per_km + service_fee, 2)

def truncate_to_last_sentence(text: str) -> str:
    if not text:
        return text

    text = text.strip()

    match = re.search(r"[.!?](?!.*[.!?])", text)

    if match:
        return text[: match.end()].strip()

    return text

def generate_chat_reply(prompt):
    inputs = tokenizer(prompt, return_tensors="pt")

    with model_lock:
        with torch.no_grad():
            output = model.generate(
                **inputs,
                max_new_tokens=20,
                temperature=0.2,
                top_p=0.9,
                repetition_penalty=1.15,
                do_sample=True
            )

    reply = tokenizer.decode(
        output[0][inputs["input_ids"].shape[-1]:],
        skip_special_tokens=True
    )

    return truncate_to_last_sentence(reply.strip())

@chat_route.post('/message')
@jwt_required()
def chat_message():
    global MODEL_EVENT
    MODEL_EVENT.wait()
    text: str = request.json.get('message', '').strip()

    intent = detect_intent(text)
    locations = extract_locations(text)
    if (intent in ("distance", "price")) and len(locations) >= 2:
        city_a, city_b = locations[:2]
        distance = FetchCities.distance(
            FetchCities.get_location(city_a, None),
            FetchCities.get_location(city_b, None)
        )

        if intent == "distance":
            reply = f"The distance between {city_a} and {city_b} is approximately {distance:.2f} km."
        else:
            price = estimate_trip_cost(distance)
            reply = f"The price for {city_a} to {city_b} is around {price:.2f} RON."

        return jsonify({"reply": generate_chat_reply(build_info_prompt(text, reply))})
    elif (intent in ("distance", "price")) and len(locations) < 2:
        imsg = f'I only recognise {locations[0]}' if len(locations) == 1 else "I don't recognise these cities"
        return jsonify({'reply': f'I don\'t know about that. {imsg}.'})

    reply = generate_chat_reply(build_prompt(text))
    return jsonify({"reply": reply})

def preload():
    threading.Thread(target=_load_resources, daemon=True).start()