import json

# --- 1. Simulation du Nouveau Code (La Logique 3.4.2) ---
def sort_systems_logic(systems, sort_method="distance"):
    """
    Ceci est la reproduction exacte de la logique ajoutée dans la version 3.4.2
    pour permettre le farming HGE (High Grade Emissions).
    """
    print(f"\n--- Tri demandé par : {sort_method.upper()} ---")
    
    if sort_method == "population":
        # LA NOUVEAUTÉ : Tri par population décroissante (Plus peuplé = Meilleur pour HGE)
        # L'utilisation de .get('population', 0) protège contre les bugs si la donnée est manquante.
        sorted_list = sorted(systems, key=lambda x: x.get('population', 0), reverse=True)
        explain_sort(sorted_list, "population")
        return sorted_list
    
    else:
        # L'ANCIEN COMPORTEMENT : Tri par distance croissante (Plus près = Plus rapide)
        sorted_list = sorted(systems, key=lambda x: x.get('distance', float('inf')))
        explain_sort(sorted_list, "distance")
        return sorted_list

def explain_sort(sorted_list, key):
    """Petit utilitaire pour visualiser ce que le code fait."""
    print(f"Top 3 résultats après tri :")
    for i, sys in enumerate(sorted_list[:3]):
        val = sys.get(key, 'N/A')
        print(f"  {i+1}. {sys['name']} - {key}: {val} (Dist: {sys.get('distance')} AL)")

# --- 2. Données de Test (Simule la réponse de l'API Spansh/EDSM) ---
# Imaginez que l'IA a cherché "Systèmes en état Boom"
mock_api_response = [
    {'name': 'Alpha Centauri', 'population': 100, 'distance': 4.3},   # Très près, mais vide (Nul pour HGE)
    {'name': 'Sol',            'population': 20000000000, 'distance': 0}, # Le top
    {'name': 'Achenar',        'population': 15000000000, 'distance': 139}, # Loin mais riche
    {'name': 'Wolf 359',       'population': 500000, 'distance': 7.8},
    {'name': 'Empty System',   'population': None, 'distance': 50}    # Cas piège (Bug potentiel)
]

# --- 3. Exécution de la Comparaison ---
if __name__ == "__main__":
    print("=== DÉMONSTRATION DU NOUVEAU CODE DE TRI (v3.4.2) ===")
    
    # Cas A : L'ancien fonctionnement (ce que l'utilisateur voyait avant)
    print("\n[Cas A] Comportement Ancien (Sort by Distance)")
    results_old = sort_systems_logic(mock_api_response, "distance")
    
    # Cas B : La nouvelle fonctionnalité (ce que la v3.4.2 apporte)
    print("\n[Cas B] Nouvelle Fonctionnalité (Sort by Population)")
    results_new = sort_systems_logic(mock_api_response, "population")
    
    # Vérification automatique
    if results_new[0]['name'] == 'Sol':
        print("\n✅ SUCCÈS : Le nouveau code privilégie bien la population (Sol est premier).")
    else:
        print("\n❌ ÉCHEC : Le tri par population ne fonctionne pas.")
