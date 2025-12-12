# Vigie Order Processing

Application de traitement et d'analyse de commandes e-commerce au format JSONL.

## Description

Ce programme lit un fichier de commandes au format JSONL (un objet JSON par ligne), calcule des statistiques de revenus par marketplace, et identifie les commandes suspectes contenant des anomalies.

## Prérequis

- Python 3.12+

## Installation

Aucune dépendance externe n'est requise. Le programme utilise uniquement la bibliothèque standard Python.

```bash
git clone <repository-url>
cd <project-directory>
```

## Utilisation

### Lancer l'application

```bash
python3.12 src/core_lib/main.py
```

### Avec filtre de date

Pour inclure uniquement les commandes à partir d'une date donnée :

```bash
python3.12 src/core_lib/main.py -from=2024-11-01
```

### Lancer les tests

```bash
python3.12 -m unittest discover -v
```

Ou pour un module spécifique :

```bash
python3.12 -m unittest -v
```

## Structure du projet

```
src/
├── core_lib/
│   ├── adapters/
│   │   ├── filters.py      # Parsing des arguments CLI
│   │   └── orders.py       # Logique métier et formatage
│   ├── models/
│   │   └── order.py        # Dataclasses (Order, Stats, SuspiciousOrder)
│   ├── data/
│   │   └── orders.json     # Données de test
│   └── main.py             # Point d'entrée
└── tests/
    └── adapter/
        ├── test_orders.py  # Tests unitaires
        └── orders_test_*.json  # Fixtures de test
```

## Exemple de sortie

```
Total revenue: 93.96 EUR

Revenue by marketplace:
- amazon: 41.97 EUR
- cdiscount: 47.98 EUR
- ebay: 7.99 EUR

Suspicious orders:
- o3: negative amount (-500)
- o4: empty marketplace
```

## Fonctionnalités

- ✅ Calcul du revenu total en euros (2 décimales)
- ✅ Revenu par marketplace (trié par ordre décroissant)
- ✅ Détection des commandes suspectes :
  - Montants négatifs
  - Marketplace vide ou manquante
  - Montants invalides ou manquants
- ✅ Filtre optionnel par date (`-from`)
- ✅ Tests unitaires

## Questions "mindset"

### 1. Si ce programme tournait en production, que surveiller / logger en priorité ?

**Métriques opérationnelles :**
- Nombre total de commandes traitées par exécution
- Nombre de commandes suspectes détectées (par type d'anomalie)
- Temps d'exécution et taille des fichiers traités
- Taux d'erreurs (fichiers non trouvés, JSON malformé)

**Logs prioritaires :**
- Chaque commande suspecte avec son ID et la raison détaillée
- Erreurs de parsing JSON avec le numéro de ligne
- Exceptions lors de la lecture de fichiers (permissions, corruption)
- Statistiques résumées à la fin de chaque traitement

**Alerting :**
- Taux de commandes suspectes > seuil (ex: 5%)
- Échec complet du traitement
- Montants anormalement élevés ou patterns inhabituels

### 2. Si le fichier passait de 10 Ko → 10 Go, que changerais-tu dans ton approche ?

**Optimisations nécessaires :**

1. **Traitement par streaming** : Ne plus charger toutes les commandes en mémoire, mais traiter ligne par ligne
2. **Agrégation incrémentale** : Calculer les statistiques au fur et à mesure plutôt qu'en fin de traitement
3. **Batch processing** : Traiter par chunks de N commandes pour équilibrer mémoire/performance
4. **Base de données** : Pour 10 Go+, considérer PostgreSQL ou ClickHouse pour des requêtes analytiques efficaces
5. **Parallélisation** : Diviser le fichier en segments et traiter en parallèle (multiprocessing)
6. **Compression** : Supporter les fichiers compressés (gzip, bzip2)

**Structure modifiée :**
```python
# Au lieu de : orders = list(all_orders)
# Faire : 
for order in stream_orders(file):
    update_stats(order)
```

### 3. Quel est selon toi le cas de test prioritaire, et pourquoi ?

**Le test prioritaire : `test_revenue_and_suspicious()`**

**Raisons :**

1. **Couvre la logique métier principale** : Calcul de revenus + détection d'anomalies
2. **Teste la robustesse** : Vérifie que les données invalides (montants négatifs, marketplace vide) n'impactent pas les statistiques fiables
3. **Valide les règles business critiques** :
   - Exclusion des montants négatifs du revenu total
   - Agrégation correcte par marketplace
   - Identification exhaustive des anomalies
4. **Cas réaliste** : Mélange de commandes valides et suspectes, comme en production

**Second test important :** Le filtre de date (`test_from_date_filter`) car il valide une feature optionnelle qui pourrait causer des bugs silencieux si mal implémentée.

---

## Améliorations possibles

Voir la section suivante pour des suggestions d'amélioration.