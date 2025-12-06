import requests
import json
import time
import logging
from functools import wraps

# --- CONFIGURATION ---
# User-Agent est poli envers les APIs (évite d'être banni)
HEADERS = {
    "User-Agent": "COVAS-NEXT-Client/3.5",
    "Content-Type": "application/json"
}

# --- 1. LE DÉCORATEUR DE ROBUSTESSE ---
def retry_api_call(max_retries=3, delay=1.5):
    """
    Décorateur : Si une fonction API échoue, elle attend et réessaie automatiquement.
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
    """
    Récupère les coordonnées (x, y, z) d'un système via EDSM.
    Nécessaire car Spansh a besoin de coordonnées pour calculer les distances.
    """
    # EDSM est très sensible aux noms exacts, on encode proprement l'URL
    url = "https://www.edsm.net/api-v1/system"
    params = {
        "systemName": system_name,
        "showCoordinates": 1
    }
    
    response = requests.get(url, params=params, headers=HEADERS, timeout=5)
    
    if response.status_code == 200:
        data = response.json()
        if data and 'coords' in data:
            return data['coords']
            
    logging.warning(f"Coordonnées introuvables pour : {system_name}")
    return None

@retry_api_call()
def find_systems(reference_system, search_radius=20, sort_method="distance"):
    """
    Cherche des systèmes via Spansh API.
    - Si sort_method="population" : Active le mode Farming HGE (Filtre Boom + Tri Population).
    - Sinon : Recherche standard triée par distance.
    """
    logging.info(f"🔍 Recherche Spansh autour de '{reference_system}' (Rayon: {search_radius} AL, Mode: {sort_method})...")
    
    # Étape 1 : On a besoin des coordonnées du point de départ
    coords = get_system_coordinates(reference_system)
    if not coords:
        logging.error(f"Impossible de localiser '{reference_system}'. Recherche annulée.")
        return []

    # Étape 2 : Préparation de la requête Spansh
    url = "https://spansh.co.uk/api/systems/search"
    
    # Filtres de base
    filters = {
        "distance": {"min": 0, "max": search_radius}
    }
    
    # LOGIQUE SPÉCIALE HGE FARMING
    if sort_method == "population":
        # Les HGE (High Grade Emissions) apparaissent surtout dans les systèmes en BOOM
        # On force ce filtre pour ne pas envoyer le joueur dans des systèmes inutiles
        filters["state"] = {"match": ["Boom"]}
        logging.info("--> Filtre 'State: Boom' activé pour le farming HGE.")

    payload = {
        "filters": filters,
        "sort": [{"distance": {"direction": "asc"}}], # On laisse Spansh trier par distance, on retriera après
        "size": 50,
        "page": 0,
        "reference_coords": coords # Spansh calcule la distance par rapport à ça
    }
    
    response = requests.post(url, json=payload, headers=HEADERS, timeout=10)
    
    if response.status_code != 200:
        logging.warning(f"Erreur Spansh API : {response.status_code}")
        return []

    data = response.json()
    results = data.get('results', [])

    if not results:
        logging.info("Aucun système trouvé avec ces critères.")
        return []

    # Étape 3 : Le Tri Final (Python)
    if sort_method == "population":
        # Tri descendant (Du plus peuplé au moins peuplé)
        # .get('population') or 0 -> Sécurité anti-crash si la pop est inconnue
        sorted_systems = sorted(
            results, 
            key=lambda x: x.get('population') or 0, 
            reverse=True
        )
        
        # Petit log pour vérifier que ça marche
        top_sys = sorted_systems[0]
        logging.info(f"✅ Top Résultat HGE : {top_sys.get('name')} (Pop: {top_sys.get('population'):,})")
        return sorted_systems
    
    else:
        # Tri par distance (Comportement standard pour voyager)
        # On s'assure que la distance est traitée comme un nombre (float)
        sorted_systems = sorted(
            results, 
            key=lambda x: float(x.get('distance', 99999))
        )
        return sorted_systems

# --- 3. DÉFINITION DES OUTILS POUR L'IA ---
def get_tools_definition():
    """
    Retourne le schéma JSON que OpenAI utilise pour comprendre les outils.
    """
    return [
        {
            "name": "find_systems",
            "description": "Cherche des systèmes stellaires proches. Utile pour trouver une destination ou pour le farming de matériaux (HGE).",
            "parameters": {
                "type": "object",
                "properties": {
                    "reference_system": {
                        "type": "string", 
                        "description": "Le nom du système actuel ou de référence (ex: Sol, Achenar)."
                    },
                    "search_radius": {
                        "type": "integer", 
                        "description": "Rayon de recherche en Années-Lumière (défaut: 20)."
                    },
                    "sort_method": {
                        "type": "string", 
                        "enum": ["distance", "population"],
                        "description": "Utiliser 'distance' pour le voyage, ou 'population' pour trouver des systèmes riches (HGE Farming)."
                    }
                },
                "required": ["reference_system"]
            }
        }
    ]

# --- TEST RAPIDE (S'exécute seulement si on lance ce fichier directement) ---
if __name__ == "__main__":
    # Configuration des logs pour voir ce qui se passe
    logging.basicConfig(level=logging.INFO)
    
    print("\n--- TEST RAPIDE SPANSH ---")
    results = find_systems("Sol", search_radius=15, sort_method="population")
    
    if results:
        print(f"\nTop 3 systèmes pour Farming autour de Sol :")
        for i, sys in enumerate(results[:3]):
            print(f"{i+1}. {sys['name']} - Pop: {sys.get('population')} - Dist: {sys.get('distance')} AL")
    else:
        print("Aucun résultat.")
