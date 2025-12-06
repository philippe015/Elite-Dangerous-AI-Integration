import os
import sys
import time
import json
import logging
import threading
from datetime import datetime

# Imports tiers
try:
    import speech_recognition as sr
    from openai import OpenAI # On utilise le client officiel (plus robuste)
    
    # Imports locaux
    import tools
    from journal_reader import JournalWatcher
    
    # Optionnel : TTS Local pour éviter les coûts
    try:
        import pyttsx3
        tts_engine = pyttsx3.init()
    except ImportError:
        tts_engine = None

except ImportError as e:
    print(f"CRITIQUE : Module manquant - {e}")
    sys.exit(1)

# --- 1. CONFIGURATION DU LOGGING ---
log_dir = "logs"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

log_filename = os.path.join(log_dir, f"covas_{datetime.now().strftime('%Y-%m-%d')}.log")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(module)s: %(message)s',
    handlers=[
        logging.FileHandler(log_filename, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

# --- 2. CHARGEMENT DE LA CONFIGURATION ---
CONFIG = {
    "wakeword": "computer",
    "openai_key": os.getenv("OPENAI_API_KEY", ""),
    "model": "gpt-4o-mini",
    "language": "fr-FR"
}

# Tentative de chargement depuis config.json
if os.path.exists("config.json"):
    try:
        with open("config.json", "r", encoding="utf-8") as f:
            user_config = json.load(f)
            # Mise à jour des clés existantes uniquement
            for key in CONFIG:
                if key in user_config:
                    CONFIG[key] = user_config[key]
            # Cas spécial pour la clé API si elle est dans le JSON
            if "openai_api_key" in user_config:
                CONFIG["openai_api_key"] = user_config["openai_api_key"]
    except Exception as e:
        logging.warning(f"Erreur lecture config.json: {e}")

class CovasBrain:
    def __init__(self):
        logging.info("🧠 Initialisation du Cerveau IA...")
        
        # 1. Audio
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        
        # 2. Client OpenAI
        if not CONFIG["openai_api_key"]:
            logging.warning("⚠️ AUCUNE CLÉ OPENAI DÉTECTÉE ! L'IA ne pourra pas répondre.")
        self.client = OpenAI(api_key=CONFIG["openai_api_key"])

        # 3. Historique de conversation
        self.history = [
            {"role": "system", "content": "Tu es COVAS:NEXT, une IA de vaisseau dans Elite Dangerous. Tu es concise, technique et utile. Tu as accès aux systèmes du vaisseau via des outils. Si on te demande une route, utilise 'find_systems'."}
        ]

        # 4. Intégration du Journal (Les Yeux sur le Jeu)
        logging.info("👁️ Connexion au Journal du Commandant...")
        self.journal_watcher = JournalWatcher()
        self.game_thread = threading.Thread(
            target=self.journal_watcher.listen_for_events, 
            args=(self.handle_game_event,),
            daemon=True
        )
        self.game_thread.start()

        # Calibration du micro
        with self.microphone as source:
            logging.info("Calibration micro (1s)...")
            self.recognizer.adjust_for_ambient_noise(source, duration=1)

    def handle_game_event(self, event):
        """Callback déclenché quand le jeu génère un événement."""
        ev_type = event.get("event")
        
        # Exemple de réactions automatiques
        if ev_type == "FSDJump":
            sys_name = event.get("StarSystem", "Inconnu")
            logging.info(f"🚀 Saut détecté vers : {sys_name}")
            # On pourrait faire parler l'IA ici : self.speak(f"Arrivée dans {sys_name}")
            
        elif ev_type == "HullDamage":
            health = event.get("Health", 0)
            if health < 0.5:
                self.speak("Alerte critique ! Intégrité de la coque sous 50%.")

    def listen(self):
        """Écoute passive."""
        with self.microphone as source:
            logging.info("En écoute...")
            try:
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)
                logging.debug("Traitement audio...")
                text = self.recognizer.recognize_google(audio, language=CONFIG["language"])
                logging.info(f"ENTENDU : '{text}'")
                return text.lower()
            except sr.WaitTimeoutError:
                return None
            except sr.UnknownValueError:
                return None # Ignorer les bruits non compris
            except Exception as e:
                logging.error(f"Erreur Micro : {e}")
                return None

    def think_and_act(self, user_text):
        """Logique principale : Texte -> LLM -> Outil -> LLM -> Voix"""
        if not user_text: return

        # 1. Ajouter l'utilisateur à l'historique
        self.history.append({"role": "user", "content": user_text})

        try:
            # 2. Premier appel à l'IA (Est-ce qu'elle veut parler ou agir ?)
            logging.info("Réflexion en cours...")
            response = self.client.chat.completions.create(
                model=CONFIG["model"],
                messages=self.history,
                tools=tools.get_tools_definition(), # On lui donne la liste des outils
                tool_choice="auto"
            )

            msg = response.choices[0].message
            
            # 3. Vérifier si l'IA veut utiliser un outil (Function Calling)
            if msg.tool_calls:
                self.history.append(msg) # On garde la trace de la demande d'outil
                
                for tool_call in msg.tool_calls:
                    func_name = tool_call.function.name
                    args = json.loads(tool_call.function.arguments)
                    logging.info(f"🔧 L'IA utilise l'outil : {func_name} avec {args}")
                    
                    # Exécution dynamique de la fonction depuis tools.py
                    if hasattr(tools, func_name):
                        function_to_call = getattr(tools, func_name)
                        result = function_to_call(**args) # Exécution réelle (Recherche Spansh etc.)
                        
                        # On renvoie le résultat à l'IA
                        self.history.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": json.dumps(result)
                        })
                    else:
                        logging.error(f"Outil inconnu : {func_name}")

                # 4. Second appel à l'IA pour qu'elle interprète le résultat de l'outil
                final_response = self.client.chat.completions.create(
                    model=CONFIG["model"],
                    messages=self.history
                )
                ai_text = final_response.choices[0].message.content
            else:
                # Pas d'outil, réponse directe
                ai_text = msg.content

            # 5. Réponse finale et vocalisation
            self.history.append({"role": "assistant", "content": ai_text})
            logging.info(f"REPONSE IA : {ai_text}")
            self.speak(ai_text)

        except Exception as e:
            logging.error(f"Erreur Cerveau : {e}", exc_info=True)
            self.speak("Erreur de traitement des données.")

    def speak(self, text):
        """TTS : Synthèse vocale."""
        if not text: return
        print(f"\n🗣️ [COVAS]: {text}\n")
        
        # Utilisation de pyttsx3 si disponible (Offline & Gratuit)
        if tts_engine:
            try:
                tts_engine.say(text)
                tts_engine.runAndWait()
            except Exception as e:
                logging.warning(f"Erreur TTS : {e}")

    def run(self):
        """Boucle principale."""
        self.speak("Systèmes en ligne. Prêt.")
        try:
            while True:
                text = self.listen()
                if text:
                    # Détection du mot-clé (Wakeword) ou commande directe
                    if CONFIG["wakeword"] in text:
                        # On nettoie la phrase (enlève "computer")
                        clean_text = text.replace(CONFIG["wakeword"], "").strip()
                        if clean_text:
                            self.think_and_act(clean_text)
                        else:
                            self.speak("Oui commandant ?")
                    # Optionnel : Si vous voulez parler sans mot clé, enlevez le 'if' ci-dessus
                
                time.sleep(0.1)
        except KeyboardInterrupt:
            logging.info("Arrêt manuel.")

if __name__ == "__main__":
    brain = CovasBrain()
    brain.run()
