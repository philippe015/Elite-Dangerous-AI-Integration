import os
import glob
import json
import time
import logging
import platform
from pathlib import Path

# --- CONFIGURATION DES CHEMINS ---
# ID Steam d'Elite Dangerous : 359320
LINUX_ELITE_PATH = os.path.expanduser("~/.local/share/Steam/steamapps/compatdata/359320/pfx/drive_c/users/steamuser/Saved Games/Frontier Developments/Elite Dangerous")
WINDOWS_ELITE_PATH = os.path.expanduser(r"~\Saved Games\Frontier Developments\Elite Dangerous")

class JournalWatcher:
    def __init__(self):
        self.journal_dir = self._detect_journal_directory()
        self.current_file = None
        self.file_handle = None
        self.last_position = 0
        
        if self.journal_dir:
            logging.info(f"📂 Dossier des journaux détecté : {self.journal_dir}")
        else:
            logging.error("❌ Impossible de trouver le dossier des logs Elite Dangerous !")

    def _detect_journal_directory(self):
        """Détecte automatiquement l'OS et le bon dossier."""
        system = platform.system()
        
        # 1. Essai Windows Standard
        if os.path.exists(WINDOWS_ELITE_PATH):
            return WINDOWS_ELITE_PATH
            
        # 2. Essai Linux / Steam Deck (Proton)
        if os.path.exists(LINUX_ELITE_PATH):
            return LINUX_ELITE_PATH
            
        # 3. Essai manuel (si l'utilisateur a configuré un chemin custom)
        # Vous pouvez ajouter une lecture de config.json ici
        return None

    def get_latest_journal_file(self):
        """Trouve le fichier Journal.log le plus récent."""
        if not self.journal_dir:
            return None
            
        # Cherche tous les fichiers Journal.*.log
        list_of_files = glob.glob(os.path.join(self.journal_dir, 'Journal.*.log'))
        if not list_of_files:
            return None
            
        # Trie par date de modification (le plus récent en dernier)
        return max(list_of_files, key=os.path.getmtime)

    def listen_for_events(self, callback_function):
        """
        Boucle infinie (générateur) qui surveille le fichier.
        À lancer dans un Thread séparé pour ne pas bloquer la voix.
        """
        logging.info("👁️ Surveillance du journal activée...")
        
        while True:
            # 1. Vérifier si on doit changer de fichier (nouveau lancement du jeu)
            latest_file = self.get_latest_journal_file()
            
            if latest_file != self.current_file:
                if self.file_handle:
                    self.file_handle.close()
                
                logging.info(f"Nouveau fichier journal détecté : {os.path.basename(latest_file)}")
                self.current_file = latest_file
                self.file_handle = open(self.current_file, 'r', encoding='utf-8')
                # On va à la fin du fichier pour ne lire que les NOUVEAUX événements
                self.file_handle.seek(0, os.SEEK_END)

            # 2. Lecture des nouvelles lignes
            if self.file_handle:
                line = self.file_handle.readline()
                if line:
                    try:
                        event_data = json.loads(line)
                        event_type = event_data.get("event", "Unknown")
                        
                        # Filtrer les événements inutiles (ex: musique) pour ne pas spammer
                        if event_type not in ["Music", "ReceiveText"]:
                            logging.debug(f"Événement Jeu : {event_type}")
                            # Appel de la fonction de cerveau (Chat.py)
                            if callback_function:
                                callback_function(event_data)
                                
                    except json.JSONDecodeError:
                        pass # Ligne incomplète, on ignore
                else:
                    time.sleep(0.5) # Pas de nouvelle ligne, on attend un peu
            else:
                time.sleep(2) # Pas de fichier trouvé, on attend

# --- TEST UNITAIRE RAPIDE ---
if __name__ == "__main__":
    # Ce bloc permet de tester ce fichier seul sans lancer tout le jeu
    logging.basicConfig(level=logging.INFO)
    
    def test_callback(event):
        print(f"--> Reçu : {event['event']}")

    watcher = JournalWatcher()
    try:
        watcher.listen_for_events(test_callback)
    except KeyboardInterrupt:
        print("Arrêt du test.")
