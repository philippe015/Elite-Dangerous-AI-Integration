import tkinter as tk
from tkinter import scrolledtext, ttk
import logging
import queue
import threading

# --- 1. GESTIONNAIRE DE LOGS POUR L'INTERFACE ---
class TextHandler(logging.Handler):
    """
    Cette classe magique capture les logs (INFO, ERROR) du backend
    et les envoie vers l'interface graphique.
    """
    def __init__(self, text_widget):
        logging.Handler.__init__(self)
        self.text_widget = text_widget
        self.log_queue = queue.Queue()
        
        # On lance un update régulier pour vider la file d'attente
        self.text_widget.after(100, self.poll_log_queue)

    def emit(self, record):
        msg = self.format(record)
        self.log_queue.put(msg)

    def poll_log_queue(self):
        """Vérifie s'il y a de nouveaux messages à afficher."""
        while not self.log_queue.empty():
            try:
                msg = self.log_queue.get(block=False)
                # Insertion du texte à la fin
                self.text_widget.configure(state='normal')
                self.text_widget.insert(tk.END, msg + '\n')
                self.text_widget.see(tk.END) # Scroll automatique vers le bas
                self.text_widget.configure(state='disabled')
            except queue.Empty:
                pass
        # On se rappelle dans 100ms
        self.text_widget.after(100, self.poll_log_queue)

# --- 2. L'APPLICATION PRINCIPALE ---
class CovasApp:
    def __init__(self, brain_instance=None):
        self.brain = brain_instance
        self.root = tk.Tk()
        self.root.title("COVAS:NEXT - Control Center")
        self.root.geometry("800x600")
        
        # Style sombre (Dark Mode basique)
        self.root.configure(bg="#1e1e1e")
        style = ttk.Style()
        style.theme_use('clam')
        
        self._setup_ui()
        self._setup_logging()

    def _setup_ui(self):
        # Cadre supérieur (Contrôles)
        top_frame = tk.Frame(self.root, bg="#1e1e1e")
        top_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)

        self.btn_listen = tk.Button(top_frame, text="🛑 STOP Écoute", command=self.toggle_listening, 
                                    bg="#d9534f", fg="white", font=("Arial", 10, "bold"))
        self.btn_listen.pack(side=tk.LEFT, padx=5)

        self.status_label = tk.Label(top_frame, text="Status: EN LIGNE", bg="#1e1e1e", fg="#5cb85c", font=("Arial", 12))
        self.status_label.pack(side=tk.RIGHT, padx=5)

        # Zone de Logs (Console)
        log_frame = tk.LabelFrame(self.root, text="Journal de Bord / Pensées IA", bg="#1e1e1e", fg="white")
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.console = scrolledtext.ScrolledText(log_frame, state='disabled', height=20, 
                                                 bg="#252526", fg="#d4d4d4", font=("Consolas", 10))
        self.console.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Tags de couleur pour les logs
        self.console.tag_config('INFO', foreground='white')
        self.console.tag_config('WARNING', foreground='orange')
        self.console.tag_config('ERROR', foreground='red')

    def _setup_logging(self):
        """Redirige les logs Python vers notre fenêtre."""
        text_handler = TextHandler(self.console)
        formatter = logging.Formatter('%(asctime)s - %(message)s', datefmt='%H:%M:%S')
        text_handler.setFormatter(formatter)
        
        # On s'attache au logger racine pour tout capturer (Chat, Main, Tools)
        logger = logging.getLogger()
        logger.addHandler(text_handler)
        logger.setLevel(logging.INFO)

    def toggle_listening(self):
        """Simulation d'un bouton pause."""
        # Note: Cela nécessite que 'brain' ait une variable 'is_listening'
        # Pour l'instant, c'est visuel
        if self.btn_listen['text'] == "🛑 STOP Écoute":
            self.btn_listen.configure(text="▶ START Écoute", bg="#5cb85c")
            self.status_label.configure(text="Status: PAUSE", fg="orange")
            logging.info("Pause demandée par l'utilisateur.")
        else:
            self.btn_listen.configure(text="🛑 STOP Écoute", bg="#d9534f")
            self.status_label.configure(text="Status: EN LIGNE", fg="#5cb85c")
            logging.info("Reprise de l'écoute.")

    def run(self):
        """Lance la boucle principale de l'interface."""
        logging.info("Interface graphique chargée.")
        
        # Gestion propre de la fermeture
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.mainloop()

    def on_close(self):
        logging.info("Fermeture de l'interface...")
        self.root.destroy()
        # On force l'arrêt complet de Python (pour tuer les threads IA)
        import sys
        sys.exit(0)

# Bloc pour tester le fichier seul
if __name__ == "__main__":
    app = CovasApp()
    # Simulation de logs pour voir si ça marche
    logging.info("Test de l'interface...")
    logging.warning("Ceci est un avertissement test.")
    app.run()
