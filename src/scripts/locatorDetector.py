import os
from mistralai import Mistral
import streamlit as st
from dotenv import load_dotenv

import requests
from bs4 import BeautifulSoup
import re

load_dotenv()

# Assure-toi que la clé API est définie comme variable d’environnement
api_key = os.getenv("MISTRAL_API_KEY")
client = Mistral(api_key=api_key)

model_name = "mistral-tiny"  # ou le modèle que tu as choisi

systemPrompt = """
    Tu es un agent expert en automatisation de test (Test Automation Engineer).
    Ta mission est d'analyser une page web contenant des articles paginés et d'en extraire les locators CSS ou XPath nécessaires à l'automatisation.
    Tu ne cliques sur rien, tu ne modifies rien : tu observes uniquement la structure HTML.
    Sois rigoureux dans le choix des locators : ils doivent être stables, explicites et applicables à plusieurs éléments similaires.

    Accède à l’URL fournie. Détecte les éléments suivants sur la page :
    - Le titre de chaque article (locatorTitle)
    - Le résumé ou la description (locatorDescription)
    - Le lien cliquable vers l’article (locatorLink)
    - La date (si disponible) (locatorDate)
    - Le bouton de pagination actif (Next ou Previous) (locatorNextPage)
    - Les locators peuvent être des sélecteurs CSS ou XPath. 
    
    Utilise ta logique pour comprendre la structure HTML. 
    Utilise de préférence des Id ou des class. 
    Ne tronque pas le nom.Certains locators sont accessibles par id, class, ou autres attributs (data-*, aria-*, etc.).
    Privilégie les locators fiables, évite ceux qui sont générés dynamiquement.

    Vérifie que les locators trouvés existent dans la page.

    
    <Input format>
    {   "url": "https://exemple.com/resultats?query=data",   "category": "actualités" }

    <Output>
    {   "url": "<url d'origine>",   "locator_title": "<locator CSS ou XPath du titre>",   "locator_description": "<locator du résumé>",   "locator_date": "<locator de la date ou null>",   "locator_link": "<locator du lien>",   "locator_next_page": "<locator du bouton de pagination actif>",   "category": "<valeur de catégorie entrée>" } 
    <Output example>
    {
    "url": "https://www.therapixel.fr/blog/",
    "locator_title": "h3 > a",
    "locator_description": ".entry-content > p",
    "locator_date": ".entry-date",
    "locator_link": ".entry-image > a",
    "locator_next_page": ".pagination .page-next",
    "category": "medical"
    }
    
    """

def locatorDetection(input_url):

    #response = client.chat.complete(
    #    model=model_name,
    #    messages=[
    #        {
    #            "role": "system",
    #            "content": systemPrompt
    #        },
    #        {
    #            "role": "user",
    #            "content": input
    #        }
    #    ],
    #    stream=False  # si tu ne veux pas de streaming
    #)
    cache = load_cache()
    raw_html = fetch_html(input_url)
    cleaned_html = clean_html(raw_html)

    if input_url in cache:
        st.write(f"✅ Cache trouvé pour {input_url}")
        locators_json = cache[input_url]
        st.write("Locators Cache:", locators_json)
        return locators_json

    else:
        locators_json = get_locators_from_mistral(cleaned_html, api_key)
        #st.write("Locators Mistral:", locators_json)
        check_results, clean_locator = check_locators(cleaned_html, locators_json)
          # Indications si locators manquants
        for i, res in enumerate(check_results):
            for k, exists in res.items():
                if not exists:
                    st.write(f"Article {i+1}: le locator {k} n'existe pas. Il faudra ajuster le sélecteur ou vérifier le HTML.")
                    
                
        cache[input_url] = clean_locator
        save_cache(cache)
        return clean_locator
        



# ------------------------
# 1️⃣ Fonction pour récupérer le HTML
# ------------------------
def fetch_html(url: str) -> str:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9,fr;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Referer": "https://www.google.com/",
    }

    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.text

# ------------------------
# 2️⃣ Nettoyage et découpage du HTML
# ------------------------
def clean_html(raw_html: str, max_repeat=4) -> str:
    soup = BeautifulSoup(raw_html, "html.parser")
    
    # Supprimer header/footer global, scripts, styles, nav, svg inutiles
    for tag in soup(["script", "style", "header", "footer", "nav", "noscript", "svg"]):
        tag.decompose()
    
    # Trouver le contenu principal (main ou body)
    main_content = soup.find("main") or soup.body or soup
    
    # Identifier les blocs qui se répètent (articles)
    candidates = main_content.find_all(True)  # tous les tags
    repeated_tags = []
    tag_counts = {}
    for tag in candidates:
        key = tag.name + ("." + tag.get("class")[0] if tag.get("class") else "")
        tag_counts[key] = tag_counts.get(key, 0) + 1
    
    # Garder seulement les tags qui se répètent au moins 2 fois
    repeated_tags = [k for k, v in tag_counts.items() if v >= 2]
    
    # Construire le HTML nettoyé avec les premiers max_repeat occurrences
    cleaned_html = ""
    for tag_name in repeated_tags:
        found = main_content.select(tag_name)
        for i, t in enumerate(found[:max_repeat]):
            cleaned_html += str(t)
    
    return cleaned_html

# ------------------------
# 3️⃣ Envoyer le HTML nettoyé à Mistral pour extraire les locators
# ------------------------
SYSTEM_PROMPT = """
Tu es un agent autonome spécialisé dans l'extraction de locators d'articles sur les pages web.
Tu dois détecter pour chaque article :
    - Le titre de chaque article (locator_title)
    - Le résumé ou la description (locator_description)
    - Le lien cliquable vers l’article (locator_link)
    - La date (si disponible) (locator_date)
    - Le bouton de pagination actif (Next ou Previous) (locator_next_page)
    

Renvoie un JSON comme ceci :
{
"url": "https://www.therapixel.fr/blog/",
"locator_title": "h3 > a",
"locator_description": ".entry-content > p",
"locator_date": ".entry-date",
"locator_link": ".entry-image > a",
"locator_next_page": ".pagination .page-next",
"category": "medical"
}

Si tu ne trouves pas un élément, mets null.
"""

def get_locators_from_mistral(html_content: str, api_key: str):
    
    client = Mistral(api_key=api_key)
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": html_content}
    ]
    response = client.chat.complete(
        model=model_name,
        messages=messages
    )
    content = response.choices[0].message.content
    return content

# ------------------------
# 4️⃣ Vérifier si les locators existent dans le HTML
# ------------------------
def check_locators(html_content: str, locators_json: str):
    import json
    soup = BeautifulSoup(html_content, "html.parser")
    results = []
    locators_json =  re.split(r'(?=\{|\[)', locators_json, maxsplit=1)[-1]

    locators_json = re.split(r'(?<=\}|\])', locators_json, maxsplit=1)[0].strip()
    locators = json.loads(locators_json.replace('\n', '').strip())
    
    for key, selector in locators.items():
        article_result = {}
        if key != "url" and key != "category":
            if selector:
                found = soup.select(selector)
                article_result[key] = bool(found)
            else:
                article_result[key] = False
    results.append(article_result)
    return results, locators


import json
import os
from pathlib import Path

CACHE_FILE = Path("mistral_cache.json")

# --- Fonction de chargement du cache ---
def load_cache():
    if CACHE_FILE.exists():
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}

# --- Fonction de sauvegarde du cache ---
def save_cache(cache):
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2, ensure_ascii=False)


