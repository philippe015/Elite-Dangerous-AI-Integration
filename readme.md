# 🚀 Améliorations de ce Fork (v3.5+)

Ce fork contient des optimisations majeures pour la stabilité et le support Linux / Steam Deck.

## ✨ Nouvelles Fonctionnalités

### 🐧 Compatibilité Linux & Steam Deck
- **Build Natif :** Workflow GitHub optimisé pour compiler sur Ubuntu 20.04 (compatible glibc SteamOS).
- **Chemins Automatiques :** Détection automatique des journaux (`Journal.log`) dans les dossiers Proton/Compatdata.
- **Dépendances :** Nettoyage du `requirements.txt` pour éviter les erreurs `pywin32` sur Linux.

### 🧠 Intelligence & Farming
- **Tri HGE (High Grade Emissions) :** La recherche de systèmes (`find_systems`) trie désormais par **Population** décroissante.
  - *Avant :* Vous envoyait au système vide le plus proche.
  - *Maintenant :* Vous envoie vers les systèmes peuplés (milliards d'habitants) où les matériaux rares apparaissent.
- **Robustesse API :** Système de "Retry" automatique si Spansh ou EDSM ne répondent pas immédiatement.

### 🛠️ Technique & Debug
- **Mode Headless :** Lancez l'IA sans interface graphique (idéal pour Raspberry Pi ou serveur).
  ```bash
  python src/main.py --headless
