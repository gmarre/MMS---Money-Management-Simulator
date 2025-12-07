# Batch Simulation System - Guide d'utilisation

## 🎯 Objectif

Le système de simulation en batch permet de lancer des milliers de simulations automatiquement pour analyser statistiquement les performances de différentes stratégies de Money Management.

## 📍 URLs Principales

- **Page d'accueil** : http://127.0.0.1:8000/
- **Batch Runner** : http://127.0.0.1:8000/money-management/batch/
- **Résultats** : http://127.0.0.1:8000/money-management/batch/results/
- **Visualiseur** : http://127.0.0.1:8000/money-management/

## 🚀 Comment lancer un batch

### 1. Accéder au Batch Runner
Allez sur http://127.0.0.1:8000/money-management/batch/

### 2. Configurer vos simulations

Pour chaque configuration que vous voulez tester :

1. Cliquez sur **"+ Ajouter une Configuration"**
2. Sélectionnez une **Stratégie** (S1 à S20)
3. Configurez :
   - **Nombre de simulations** : Ex: 20 (pour avoir des statistiques)
   - **Nombre de trades** : Ex: 3000 (par simulation)
   - **Capital initial** : Ex: 10000€
4. Ajustez les **paramètres de la stratégie** qui apparaissent automatiquement

### 3. Exemple de configuration

**Configuration 1 : Stratégie 1 (Drawdown Linéaire)**
- Stratégie : S1 - Drawdown Linéaire
- Nombre de simulations : 20
- Nombre de trades : 3000
- Capital initial : 10000€
- Paramètres :
  - base_risk : 0.5
  - dd1 : 5
  - dd2 : 20

**Configuration 2 : Stratégie 2 (Drawdown Géométrique)**
- Stratégie : S2 - Drawdown Géométrique
- Nombre de simulations : 20
- Nombre de trades : 3000
- Capital initial : 10000€
- Paramètres :
  - base_risk : 0.5
  - dd_step : 5
  - decay : 0.8
  - min_risk : 0.1

**Configuration 3 : Stratégie 26**
- Stratégie : S26
- Nombre de simulations : 20
- Nombre de trades : 3000
- Capital initial : 10000€
- Paramètres : (ajuster selon la stratégie)

### 4. Lancer le batch

Cliquez sur **"▶️ LANCER LE BATCH"**

Le système va :
- Exécuter toutes les simulations (ex: 20 x 3 configs = 60 simulations au total)
- Stocker les résultats dans la base de données
- Afficher un lien vers les résultats

## 📊 Visualiser les résultats

### 1. Accéder aux résultats
Allez sur http://127.0.0.1:8000/money-management/batch/results/

### 2. Sélectionner un batch
Choisissez le batch que vous voulez analyser dans le menu déroulant

### 3. Analyser les statistiques

Le tableau affiche pour chaque stratégie testée :

**Colonnes principales :**
- **Stratégie** : Nom de la stratégie
- **Nb Sims** : Nombre de simulations effectuées
- **Perf Médiane** : Performance médiane (50e percentile)
- **Perf Moy** : Performance moyenne
- **Perf Max** : Meilleure performance observée
- **DD Moyen** : Drawdown moyen
- **DD Médian** : Drawdown médian
- **DD Max** : Pire drawdown observé
- **Taux Succès** : Taux de réussite moyen
- **Wins Consec.** : Maximum de gains consécutifs moyen
- **Losses Consec.** : Maximum de pertes consécutives moyen

### 4. Trier les résultats

Utilisez le menu déroulant "Trier par" pour classer les stratégies selon :
- Performance (Médiane) ↓ / ↑
- Drawdown (Moyen) ↑ / ↓
- Taux de Réussite ↓

## 🎯 Comment interpréter les résultats

### Critères de sélection d'une bonne stratégie

1. **Performance Médiane élevée** : Indique que la stratégie performe bien dans la majorité des cas
2. **Drawdown faible** : Un DD < -25% est acceptable, < -20% est excellent
3. **Écart-type faible** : Différence faible entre Perf Min et Max = plus stable
4. **Taux de succès cohérent** : > 45% est bon pour ce système

### Code couleur automatique

- **Performance** :
  - Vert : Positive
  - Rouge : Négative

- **Drawdown** :
  - Vert : > -20% (excellent)
  - Orange : entre -20% et -35% (acceptable)
  - Rouge : < -35% (dangereux)

### Exemple d'analyse

D'après votre screenshot, les meilleures stratégies sont :

**Top Performances :**
1. S26 : +6 219 316% (DD: -46%)
2. S18 : +1 837 891% (DD: -47.46%)
3. S23 : +1 926 142% (DD: -47.32%)

**Meilleur profil risque/rendement :**
- S14 : +8 944% (DD: -18.19%) ✅ Excellent ratio

## 💾 Base de données

Les résultats sont stockés dans 2 tables :

1. **SimulationResult** : Chaque simulation individuelle
2. **SimulationBatch** : Métadonnées des batchs

Vous pouvez interroger directement la base si besoin :
```python
from money_management.models import SimulationResult, SimulationBatch

# Récupérer tous les résultats d'une stratégie
results = SimulationResult.objects.filter(strategy_key='strategy_1')

# Statistiques
from django.db.models import Avg, Max, Min
stats = results.aggregate(
    avg_perf=Avg('final_performance_pct'),
    max_dd=Max('max_drawdown_pct')
)
```

## ⚡ Optimisations

Pour accélérer les simulations :
1. Augmentez le nombre de simulations par configuration (20-50)
2. Réduisez le nombre de trades si vous testez beaucoup de configs
3. Les simulations sont exécutées de manière synchrone (pas de equity curve générée)

## 🔧 Personnalisation

Pour ajouter des statistiques :
1. Modifiez `models.py` pour ajouter des champs
2. Créez une migration : `python manage.py makemigrations`
3. Appliquez : `python manage.py migrate`
4. Mettez à jour `views.py` (fonction `run_batch_simulations`)
5. Mettez à jour `batch_results.html` pour afficher les nouvelles stats
