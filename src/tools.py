import requests
import json
import time
import logging
from functools import wraps

# --- CONFIGURATION ---
# User-Agent est poli envers les APIs (évite d'être banni)
HEADERS = {
    "User-Agent": "COVAS-NEXT-Client/3.0",
    "Content-Type": "application/json"
}

# --- 1. LE DÉCORATEUR DE ROBUSTESSE (NOUVEAU) ---
def retry_api_call(max_retries=3, delay=1.5):
    """
    Si une fonction API échoue, elle attend et réessaie automatiquement.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for i in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except requests.exceptions.RequestException as e:
                    logging.warning(f"⚠️ Erreur API ({func.__name__}) - Essai {i+1}/{max_retries} : {e}")
                    time.sleep(delay)
                except Exception as e:
                    logging.error(f"❌ Erreur critique dans l'outil {func.__name__} : {e}", exc_info=True)
                    return None
            
            logging.error(f"❌ Abandon après {max_retries} tentatives pour {func.__name__}")
            return None
        return wrapper
    return decorator

# --- 2. LES OUTILS DE NAVIGATION ---

@retry_api_call()
def get_system_coordinates(system_name):
    """Récupère les coordonnées d'un système via EDSM."""
    url = f"https://www.edsm.net/api-v1/system?systemName={system_name}&showCoordinates=1"
    response = requests.get(url, headers=HEADERS, timeout=5)
    
    if response.status_code == 200:
        data = response.json()
        if data and 'coords' in data:
            return data['coords']
    return None

@retry_api_call()
def find_systems(reference_system, search_radius=20, sort_method="distance"):
    """
    Cherche des systèmes via Spansh API.
    Intègre le CORRECTIF pour le tri par Population (HGE Farming).
    """
    logging.info(f"Recherche de systèmes autour de {reference_system} (Tri: {sort_method})...")
    
    # URL fictive pour l'exemple (à remplacer par l'endpoint Spansh réel utilisé dans le projet)
    # Dans le code original, c'est souvent un POST vers spansh.co.uk/api/systems
    url = "https://spansh.co.uk/api/systems/search" 
    
    payload = {
        "filters": {
            "distance": {"min": 0, "max": search_radius}
            # Ajoutez ici les filtres réels du projet (state: Boom, allegiance, etc.)
        },
        "sort": [{"distance": {"direction": "asc"}}],
        "size": 50,
        "page": 0
    }
    
    # Note: L'implémentation réelle dépend de comment Spansh attend les données
    # Ceci est la structure logique pour illustrer le tri
    response = requests.post(url, json=payload, headers=HEADERS, timeout=10)
    
    if response.status_code != 200:
        logging.warning(f"Spansh a répondu : {response.status_code}")
        return []

    data = response.json()
    results = data.get('results', [])

    # --- 3. LOGIQUE DE TRI AMÉLIORÉE (HGE FARMING) ---
    if sort_method == "population":
        # Le correctif robuste (évite le crash sur None)
        sorted_systems = sorted(
            results, 
            key=lambda x: x.get('population') or 0, 
            reverse=True
        )
        logging.info("Systèmes triés par Population (Décroissant).")
        return sorted_systems
    
    else:
        # Tri par distance par défaut
        sorted_systems = sorted(
            results, 
            key=lambda x: x.get('distance', float('inf'))
        )
        return sorted_systems

# --- 4. DÉFINITION DES OUTILS POUR L'IA (JSON SCHEMA) ---
# C'est ce que GPT-4 voit pour savoir qu'il peut utiliser ces fonctions.
def get_tools_definition():
    return [
        {
            "name": "find_systems",
            "description": "Trouve des systèmes stellaires proches selon des critères (utile pour le farming HGE).",
            "parameters": {
                "type": "object",
                "properties": {
                    "reference_system": {"type": "string", "description": "Le système de départ"},
                    "search_radius": {"type": "integer", "description": "Rayon en AL"},
                    "sort_method": {
                        "type": "string", 
                        "enum": ["distance", "population"],
                        "description": "Trier par 'distance' (voyage) ou 'population' (High Grade Emissions)"
                    }
                },
                "required": ["reference_system"]
            }
        }
    ]
