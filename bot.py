"""
Bot de hilos: revisa los tweets recientes de TU CUENTA de Twitter/X
(iniciando sesión como tú, vía twikit) y reenvía a un canal de Discord
(vía Webhook) los que pertenecen a un hilo marcado manualmente en
hilos.json.

No usa la API oficial de pago de X: usa twikit, que inicia sesión como
una cuenta normal (igual que el navegador) y lee los tweets desde ahí.
snscrape ya no funciona porque X bloqueó el endpoint que usaba.
"""

import asyncio
import json
import os
import sys
import requests
from twikit import Client
from dotenv import load_dotenv

load_dotenv()

WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK")
TWITTER_USER = os.getenv("TWITTER_USER")  # tu @usuario, sin el @
TWITTER_USERNAME = os.getenv("TWITTER_USERNAME")  # usuario de login (igual a TWITTER_USER normalmente)
TWITTER_EMAIL = os.getenv("TWITTER_EMAIL")  # email asociado a la cuenta
TWITTER_PASSWORD = os.getenv("TWITTER_PASSWORD")
MAX_TWEETS_TO_CHECK = int(os.getenv("MAX_TWEETS_TO_CHECK", "50"))

HILOS_PATH = "hilos.json"
SEEN_PATH = "seen.json"


def load_json(path, default):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return default


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def enviar_a_discord(texto):
    if not WEBHOOK_URL:
        print("ERROR: no se configuró DISCORD_WEBHOOK", file=sys.stderr)
        return False
    resp = requests.post(WEBHOOK_URL, json={"content": texto}, timeout=15)
    if resp.status_code not in (200, 204):
        print(f"ERROR Discord ({resp.status_code}): {resp.text}", file=sys.stderr)
        return False
    return True


def main():
    if not TWITTER_USER:
        print("ERROR: no se configuró TWITTER_USER", file=sys.stderr)
        sys.exit(1)
    if not (TWITTER_USERNAME and TWITTER_EMAIL and TWITTER_PASSWORD):
        print("ERROR: faltan TWITTER_USERNAME, TWITTER_EMAIL o TWITTER_PASSWORD", file=sys.stderr)
        sys.exit(1)

    hilos = set(load_json(HILOS_PATH, []))
    seen = set(load_json(SEEN_PATH, []))

    nuevos_publicados = asyncio.run(
        revisar_y_publicar(hilos, seen)
    )

    save_json(HILOS_PATH, sorted(hilos))
    save_json(SEEN_PATH, sorted(seen))

    print(f"Listo. {nuevos_publicados} tweet(s) nuevo(s) publicado(s) en Discord.")


async def revisar_y_publicar(hilos, seen):
    client = Client("en-US")

    print(f"Iniciando sesión como @{TWITTER_USERNAME}...")
    await client.login(
        auth_info_1=TWITTER_USERNAME,
        auth_info_2=TWITTER_EMAIL,
        password=TWITTER_PASSWORD,
    )

    print(f"Revisando últimos tweets de @{TWITTER_USER}...")
    user = await client.get_user_by_screen_name(TWITTER_USER)

    # 'Replies' incluye también las respuestas (necesario para detectar hilos),
    # 'Tweets' solo muestra los tweets "principales".
    tweets = await user.get_tweets("Replies", count=MAX_TWEETS_TO_CHECK)

    tweets = list(tweets)
    # Orden cronológico (más antiguo -> más reciente) para encadenar bien los hilos
    tweets.sort(key=lambda t: t.created_at_datetime)

    nuevos_publicados = 0

    for t in tweets:
        tid = str(t.id)
        if tid in seen:
            continue

        autor = (t.user.screen_name if t.user else "").lower()
        if autor != TWITTER_USER.lower():
            # Nos interesan solo tweets/respuestas escritos por ti mismo
            seen.add(tid)
            continue

        in_reply_to = str(t.in_reply_to) if getattr(t, "in_reply_to", None) else None

        es_de_hilo = (tid in hilos) or (in_reply_to in hilos)

        if es_de_hilo:
            if tid not in hilos:
                hilos.add(tid)

            url = f"https://twitter.com/{TWITTER_USER}/status/{tid}"
            mensaje = f"🧵 {url}"
            if enviar_a_discord(mensaje):
                print(f"Publicado: {url}")
                nuevos_publicados += 1

        seen.add(tid)

    return nuevos_publicados


if __name__ == "__main__":
    main()
