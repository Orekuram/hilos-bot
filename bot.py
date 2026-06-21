"""
Bot de hilos: revisa los tweets recientes de un usuario de Twitter/X y
reenvía a un canal de Discord (vía Webhook) los que pertenecen a un hilo
marcado manualmente en hilos.json.

No usa la API oficial de pago de X: usa snscrape para leer tweets públicos.
"""

import json
import os
import sys
import requests
import snscrape.modules.twitter as sntwitter
from dotenv import load_dotenv

load_dotenv()

WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK")
TWITTER_USER = os.getenv("TWITTER_USER")
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

    hilos = set(load_json(HILOS_PATH, []))
    seen = set(load_json(SEEN_PATH, []))

    print(f"Revisando últimos tweets de @{TWITTER_USER}...")

    scraper = sntwitter.TwitterUserScraper(TWITTER_USER)
    tweets = []
    for i, tweet in enumerate(scraper.get_items()):
        tweets.append(tweet)
        if i >= MAX_TWEETS_TO_CHECK - 1:
            break

    # Orden cronológico (más antiguo -> más reciente) para encadenar bien los hilos
    tweets.sort(key=lambda t: t.date)

    nuevos_publicados = 0

    for t in tweets:
        tid = str(t.id)
        if tid in seen:
            continue

        in_reply_to = str(t.inReplyToTweetId) if t.inReplyToTweetId else None
        es_propia_respuesta = (
            t.inReplyToUser is not None
            and t.inReplyToUser.username.lower() == TWITTER_USER.lower()
        )

        es_de_hilo = (tid in hilos) or (
            in_reply_to in hilos and es_propia_respuesta
        )

        if es_de_hilo:
            if tid not in hilos:
                hilos.add(tid)

            mensaje = f"🧵 {t.url}"
            if enviar_a_discord(mensaje):
                print(f"Publicado: {t.url}")
                nuevos_publicados += 1

        seen.add(tid)

    save_json(HILOS_PATH, sorted(hilos))
    save_json(SEEN_PATH, sorted(seen))

    print(f"Listo. {nuevos_publicados} tweet(s) nuevo(s) publicado(s) en Discord.")


if __name__ == "__main__":
    main()
