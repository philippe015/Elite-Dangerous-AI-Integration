import sys
import os
import argparse
import logging
import threading
import time

# Ajout du dossier courant au path pour trouver les modules (Chat, tools, etc.)
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from Chat import CovasBrain
    # On importe AIGUI conditionnellement plus bas pour éviter de charger des libs graphiques en mode "headless"
except ImportError as e:
    print(f"❌ Erreur critique : Impossible d'importer les modules principaux ({e}).")
    print("Avez-vous lancé 'pip install -r requirements.txt' ?")
    sys.exit(1)

# --- CONFIGURATION DU LOGGING (Si pas déjà fait dans Chat.py) ---
# On configure un logger de base pour le démarrage
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [MAIN] %(levelname)s: %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

def parse_arguments():
    """Définition des arguments de la ligne de commande."""
    parser = argparse.ArgumentParser(description="COVAS:NEXT - AI Integration for Elite Dangerous")
    
    parser.add_argument("--headless", action="store_true", 
                        help="Lance l'IA sans interface graphique (Mode Texte/Serveur).")
    
    parser.add_argument("--model", type=str, default="gpt-4o-mini", 
                        help="Modèle IA à utiliser (ex: gpt-4, gpt-3.5-turbo, ollama).")
    
    parser.add_argument("--debug", action="store_true", 
                        help="Active les logs détaillés (DEBUG).")
    
    return parser.parse_args()

def start_gui(brain_instance):
    """Lance l'interface graphique (AIGUI)."""
    try:
        logging.info("🖥️ Lancement de l'interface graphique...")
        # Import local pour éviter les erreurs sur serveur sans écran
        import AIGUI
        # On suppose que AIGUI a une fonction run() ou une classe principale
        # Si AIGUI est un script bloquant, il faudra peut-être le lancer en subprocess
        app = AIGUI.CovasApp(brain_instance) 
        app.run()
    except ImportError:
        logging.error("❌ Impossible de charger l'interface graphique (Modules manquants ?). Passage en mode Headless.")
    except Exception as e:
        logging.error(f"❌ Crash de l'interface graphique : {e}", exc_info=True)

def main():
    args = parse_arguments()

    # Mise à jour du niveau de log si debug demandé
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logging.debug("Mode DEBUG activé.")

    logging.info(f"🚀 Démarrage de COVAS:NEXT (Modèle: {args.model})")

    # 1. Initialisation du Cerveau (Backend)
    try:
        brain = CovasBrain() 
        # Si CovasBrain prend des arguments de config, passez-les ici :
        # brain = CovasBrain(model_name=args.model)
    except Exception as e:
        logging.critical(f"Impossible d'initialiser le cerveau IA : {e}", exc_info=True)
        sys.exit(1)

    # 2. Lancement du Thread IA (Écoute + Journal)
    # On lance le cerveau dans un thread séparé pour ne pas bloquer l'UI
    ai_thread = threading.Thread(target=brain.run, daemon=True)
    ai_thread.start()

    # 3. Choix du mode d'affichage
    if args.headless:
        logging.info("Mode HEADLESS actif. Appuyez sur CTRL+C pour quitter.")
        try:
            # En mode headless, on doit garder le script principal vivant
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logging.info("Arrêt demandé par l'utilisateur.")
    else:
        # En mode normal, on lance l'UI (qui bloquera le script principal jusqu'à fermeture)
        start_gui(brain)

    logging.info("Arrêt du programme. À bientôt Commandant. o7")

if __name__ == "__main__":
    main()
