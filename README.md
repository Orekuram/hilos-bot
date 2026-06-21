# hilos-bot

Reenvía automáticamente a un canal de Discord (`#hilos`) los tweets que
pertenecen a un hilo marcado, ignorando tus tweets sueltos. Sin usar la
API de pago de Twitter/X.

## Cómo funciona

1. Lee tus tweets recientes con `snscrape` (sin necesidad de API key).
2. Compara cada tweet contra `hilos.json`, una lista de IDs de tweets que
   marcan el inicio de un hilo.
3. Si el tweet responde a uno de esos IDs (o es uno de ellos), lo publica
   en Discord vía Webhook y añade su propio ID a `hilos.json`, para que
   la siguiente respuesta del hilo también se detecte en cadena.
4. Guarda en `seen.json` los tweets ya procesados para no duplicar.

## Requisitos

- Python 3.10+
- Una cuenta de Discord con un servidor donde tengas permisos de admin
- Cuenta de GitHub (si quieres correrlo gratis con GitHub Actions)

## Configuración paso a paso

### 1. Crear el Webhook de Discord

1. En tu servidor, crea el canal `#hilos`.
2. Click derecho sobre el canal → **Editar canal** → **Integraciones** → **Webhooks** → **Crear Webhook**.
3. Copia la URL del webhook.

### 2. Configurar variables de entorno (uso local)

```bash
cp .env.example .env
```

Edita `.env` y completa:
- `DISCORD_WEBHOOK`: la URL que copiaste.
- `TWITTER_USER`: tu usuario de Twitter/X sin el `@`.

### 3. Instalar dependencias y probar localmente

```bash
python -m venv venv
source venv/bin/activate      # En Windows: venv\Scripts\activate
pip install -r requirements.txt
python bot.py
```

### 4. Marcar el inicio de un hilo

Cuando publiques el primer tweet de un hilo en Twitter/X:

1. Copia su ID: es el número largo en la URL, ej.
   `https://twitter.com/tu_usuario/status/1801234567890123456` → el ID es
   `1801234567890123456`.
2. Añádelo al array en `hilos.json`:

```json
["1801234567890123456"]
```

A partir de ese momento, cada vez que respondas a ese tweet (o a una
respuesta encadenada de él), el bot lo detectará y publicará en Discord
automáticamente. Los tweets que NO formen parte de esa cadena se ignoran.

## Automatización gratuita con GitHub Actions

1. Crea un repositorio en GitHub y sube esta carpeta.
2. Ve a **Settings → Secrets and variables → Actions → New repository secret**
   y crea dos secrets:
   - `DISCORD_WEBHOOK` con la URL del webhook.
   - `TWITTER_USER` con tu usuario de Twitter/X.
3. El workflow en `.github/workflows/hilos.yml` ya está configurado para
   correr cada 10 minutos automáticamente (gratis dentro del free tier de
   GitHub Actions) y hacer commit de `hilos.json` / `seen.json` para
   mantener el estado entre ejecuciones.
4. Puedes lanzarlo manualmente desde la pestaña **Actions → Revisar hilos
   → Run workflow** para probar que funciona.

## Notas y limitaciones

- `snscrape` lee el sitio público de X sin login. X cambia su frontend
  con frecuencia, así que si el bot deja de detectar tweets, revisa si
  hay una versión más nueva de snscrape (suele haber forks activos de la
  comunidad en GitHub) y actualiza la dependencia en `requirements.txt`.
- El bot solo encadena hilos por respuestas (`reply`) tuyas a ti mismo.
  Si citas tu propio tweet (quote tweet) en vez de responder, no se
  detectará como parte del hilo.
- El intervalo de 10 minutos es ajustable en el `cron` del workflow, pero
  no conviene bajarlo demasiado para evitar bloqueos por scraping
  agresivo.
- Si en algún momento `snscrape` deja de funcionar del todo, la
  alternativa de respaldo es un script con Playwright usando sesión
  logueada, más robusto pero más complejo de mantener.
