import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException, NoSuchElementException
import time
import re
import requests
import random
import os
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN") or "8742776802:AAHSzD1qTwCqMEOdoW9_pT2l5GfmMBWUZQY"
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID") or "7427648935"

URL = "https://www.premierbet.co.mz/virtuals/game/aviator-291195"

def enviar_telegram(mensagem):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": mensagem, "parse_mode": "Markdown"}
    try:
        r = requests.post(url, data=payload, timeout=10, verify=False)
        if r.status_code == 200:
            logger.info("Mensagem enviada")
        else:
            logger.error(f"Erro Telegram: {r.status_code}")
    except Exception as e:
        logger.error(f"Falha Telegram: {e}")

def iniciar_driver():
    options = uc.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--window-size=1366,768")
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36")

    # Caminho FIXO do Chromium no container
    options.browser_executable_path = "/usr/bin/chromium-browser"

    driver = uc.Chrome(options=options, headless=True, version_main=145)
    logger.info("Driver iniciado com sucesso")
    return driver

driver = iniciar_driver()

historico_anterior = []

logger.info("Monitoramento iniciado...")

while True:
    try:
        driver.get(URL)
        time.sleep(random.uniform(10, 20))

        # Retry para iframe
        iframe_ok = False
        for attempt in range(5):
            try:
                iframe = WebDriverWait(driver, 25).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "iframe.casino-game-launch-iframe__frame"))
                )
                driver.switch_to.frame(iframe)
                logger.info("Entrou no iframe (tentativa %d)", attempt + 1)
                iframe_ok = True
                break
            except TimeoutException:
                logger.warning("Iframe não encontrado na tentativa %d", attempt + 1)
                driver.refresh()
                time.sleep(15)

        if not iframe_ok:
            logger.error("Iframe não encontrado após retries, reiniciando driver")
            driver.quit()
            driver = iniciar_driver()
            time.sleep(30)
            continue

        # Captura histórico
        try:
            items_wrapper = WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div._itemsWrapper_7l84e_35"))
            )

            spans = items_wrapper.find_elements(
                By.CSS_SELECTOR, "button._container_12jzl_1 span._container_1p5jb_1"
            )

            historico_atual = []
            for span in spans:
                txt = span.text.strip()
                if txt and re.match(r'^\d+\.?\d*$', txt):
                    historico_atual.append(float(txt))

            if historico_atual and historico_atual != historico_anterior:
                historico_anterior = historico_atual[:]

                lista_str = ", ".join(f"{v:.2f}" for v in historico_atual[-30:])
                msg = (
                    f"*Histórico Atualizado – Aviator Premier Bet*\n\n"
                    f"[{lista_str}]\n\n"
                    f"Total visível: **{len(historico_atual)}** rodadas\n"
                    f"Mais recente: **{historico_atual[-1]:.2f}x**"
                )
                logger.info("Novo histórico detectado. Enviando...")
                enviar_telegram(msg)

        except Exception as e:
            logger.error(f"Erro ao capturar histórico: {e}")

        driver.switch_to.default_content()

    except Exception as e:
        logger.error(f"Erro geral no loop: {e}")
        try:
            driver.quit()
        except:
            pass
        driver = iniciar_driver()
        time.sleep(30)

    time.sleep(random.uniform(60, 120))
