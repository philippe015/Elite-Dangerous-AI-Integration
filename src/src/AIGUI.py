    def toggle_listening(self):
        """Active ou désactive l'écoute de l'IA."""
        # Changement visuel
        if self.btn_listen['text'] == "🛑 STOP Écoute":
            self.btn_listen.configure(text="▶ START Écoute", bg="#5cb85c")
            self.status_label.configure(text="Status: PAUSE", fg="orange")
            logging.info("Pause demandée par l'utilisateur.")
            
            # ACTION RÉELLE SUR LE CERVEAU
            if self.brain:
                self.brain.paused = True 

        else:
            self.btn_listen.configure(text="🛑 STOP Écoute", bg="#d9534f")
            self.status_label.configure(text="Status: EN LIGNE", fg="#5cb85c")
            logging.info("Reprise de l'écoute.")
            
            # ACTION RÉELLE SUR LE CERVEAU
            if self.brain:
                self.brain.paused = False
