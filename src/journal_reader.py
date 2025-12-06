import os
import glob
import json
import time
import logging
import platform

# --- CONFIGURATION DES CHEMINS PAR DÉFAUT ---
LINUX_ELITE_PATH = os.path.expanduser("~/.local/share/Steam/steamapps/compatdata/359320/pfx/drive_c/users/steamuser/Saved Games/Frontier Developments/Elite Dangerous")
WINDOWS_ELITE_PATH = os.path.expanduser(r"~\Saved Games\Frontier Developments\Elite Dangerous")

class JournalWatcher:
    def __init__(self):
        self.journal_dir = self._detect_journal_directory()
        self.current_file = None
        self.file_handle = None
        
        if self.journal_dir:
            logging.info(f"📂 Dossier des journaux détecté : {self.journal_dir}")
        else:
            logging.error("❌ ERREUR CRITIQUE : Impossible de trouver le dossier des logs Elite Dangerous !")
            logging.error("👉 Vérifiez 'config.json' ou lancez le jeu une fois.")

    def _detect_journal_directory(self):
        """Détecte le dossier via config.json, ou devine selon l'OS."""
        
        # 1. Priorité absolue : Fichier de config
        if os.path.exists("config.json"):
            try:
                with open("config.json", "r", encoding="utf-8") as f:
                    config = json.load(f)
                    custom_path = config.get("game", {}).get("journal_path")
                    
                    if custom_path and custom_path != "auto" and os.path.exists(custom_path):
                        logging.info("Chemin personnalisé chargé depuis config.json")
                        return custom_path
            except Exception as e:
                logging.warning(f"Erreur lecture config.json : {e}")

        # 2. Essai Windows Standard
        if os.path.exists(WINDOWS_ELITE_PATH):
            return WINDOWS_ELITE_PATH
            
        # 3. Essai Linux / Steam Deck (Proton)
        if os.path.exists(LINUX_ELITE_PATH):
            return LINUX_ELITE_PATH
            
        return None

    def get_latest_journal_file(self):
        """Trouve le fichier Journal.log le plus récent."""
        if not self.journal_dir:
            return None
            
        # Cherche tous les fichiers Journal.*.log
        try:
            list_of_files = glob.glob(os.path.join(self.journal_dir, 'Journal.*.log'))
            if not list_of_files:
                return None
            # Trie par date de modification (le plus récent en dernier)
            return max(list_of_files, key=os.path.getmtime)
        except Exception as e:
            logging.error(f"Erreur accès fichiers journaux : {e}")
            return None

    def listen_for_events(self, callback_function):
        """
        Boucle infinie qui surveille le fichier.
        """
        logging.info("👁️ Surveillance du journal activée...")
        
        while True:
            try:
                # 1. Vérifier si on doit changer de fichier (Nouveau lancement du jeu)
                latest_file = self.get_latest_journal_file()
                
                if latest_file and latest_file != self.current_file:
                    if self.file_handle:
                        self.file_handle.close()
                    
                    logging.info(f"Lecture du journal : {os.path.basename(latest_file)}")
                    self.current_file = latest_file
                    
                    # 'errors=replace' évite le crash si le jeu écrit un caractère bizarre
                    self.file_handle = open(self.current_file, 'r', encoding='utf-8', errors='replace')
                    
                    # IMPORTANT : On va à la fin pour ne lire que le futur
                    self.file_handle.seek(0, os.SEEK_END)

                # 2. Lecture des nouvelles lignes
                if self.file_handle:
                    line = self.file_handle.readline()
                    if line:
                        try:
                            event_data = json.loads(line)
                            event_type = event_data.get("event", "Unknown")
                            
                            # Filtrage du spam
                            if event_type not in ["Music", "ReceiveText", "Market", "Outfitting"]:
                                logging.debug(f"Event Jeu: {event_type}")
                                if callback_function:
                                    callback_function(event_data)
                                    
                        except json.JSONDecodeError:
                            pass # Ligne incomplète (ça arrive souvent lors de l'écriture disque)
                    else:
                        time.sleep(0.5) # Pause CPU
                else:
                    time.sleep(2) # Pas de fichier, on attend
                    
            except Exception as e:
                logging.error(f"Erreur dans la boucle de surveillance : {e}")
                time.sleep(1)

# --- TEST LOCAL ---
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("Test du lecteur de journaux...")
    
    def my_callback(event):
        print(f"--> {event['event']}")

    watcher = JournalWatcher()
    if watcher.journal_dir:
        try:
            watcher.listen_for_events(my_callback)
        except KeyboardInterrupt:
            print("Stop.")
