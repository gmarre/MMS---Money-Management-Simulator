# 🎯 Stratégies de Money Management - Guide d'utilisation

## Vue d'ensemble

Le simulateur MMS intègre désormais **20 stratégies adaptatives de Money Management** qui ajustent automatiquement le risque en fonction de la performance du compte.

## Comment utiliser

### 1. Accéder au simulateur
Ouvrez votre navigateur à l'adresse : `http://127.0.0.1:8000/`

### 2. Configuration initiale

1. **Capital initial** : Définissez votre capital de départ (défaut: 1000€)
2. **Distribution des probabilités** : Choisissez un preset
   - 📊 Équilibré (+0.27R) - distribution équilibrée
   - ⚡ Agressif (-0.18R) - plus de risque
   - 🛡️ Conservateur (+0.55R) - plus sécurisé

### 3. Sélection de la stratégie

#### Option A : Risque Fixe (par défaut)
- Bouton "🎯 Risque Fixe" sélectionné
- Vous choisissez manuellement le risque à chaque trade
- Utilisez les boutons 0.25%, 0.5%, 1%, etc.

#### Option B : Stratégie Adaptative
- Cliquez sur un bouton **S1** à **S20**
- Les paramètres de la stratégie s'affichent automatiquement
- Ajustez les paramètres selon vos préférences (valeurs par défaut recommandées)

### 4. Lancer la simulation

#### Trades individuels (avec Risque Fixe uniquement)
- Cliquez sur un bouton de risque (0.25% à 20%)
- Le trade s'exécute immédiatement
- Les stats et le graphique se mettent à jour

#### Simulation de 1000 trades
- Cliquez sur un bouton **x1000** (ex: "1% x1000")
- **Avec Risque Fixe** : Exécute 1000 trades avec le risque sélectionné
- **Avec Stratégie** : Exécute 1000 trades avec ajustement dynamique du risque
- Une barre de progression s'affiche en temps réel
- Les résultats finaux incluent : capital final, drawdown max, gain moyen, écart-type

## 📋 Liste des 20 Stratégies

### Stratégies basées sur le Drawdown (S1-S4)

**S1 : Drawdown Linéaire**
- Réduit le risque proportionnellement au drawdown
- Paramètres : dd1 (5%), dd2 (20%), base_risk (1%)

**S2 : Drawdown Géométrique**
- Réduction exponentielle du risque
- Paramètres : dd_step (5%), decay (0.8)

**S3 : Mode Sécurité**
- Bascule en mode sécurisé au-delà d'un seuil DD
- Paramètres : dd_threshold (15%), safe_risk (0.25%)

**S4 : DD Max Historique**
- Compare DD actuel au DD max historique
- Paramètres : ratio_threshold (0.7), low_risk (0.5%)

### Stratégies basées sur la Croissance du Capital (S5-S8)

**S5 : Scaling Linéaire Capital**
- Augmente le risque tous les X% de gain
- Paramètres : gain_step (10%), increment (0.1%)

**S6 : Scaling Géométrique**
- Croissance exponentielle du risque
- Paramètres : growth_rate (1.1), step (10%)

**S7 : Risk Reset**
- Augmente après X trades sans nouveau ATH
- Paramètres : plateau_step (5), reset_risk (1.5%)

**S8 : ATH Distance**
- Booste si proche de l'ATH
- Paramètres : ath_distance (10%), boost_risk (1.2%)

### Stratégies basées sur les Séries (S9-S14)

**S9 : Anti-Martingale Inversée**
- Augmente après perte, réduit après gain
- Paramètres : up_factor (1.2), down_factor (0.8)

**S10 : 3 Pertes Consécutives**
- Réduit après série de pertes
- Paramètres : loss_streak (3), reduced_risk (0.5%)

**S11 : Gestion Grosses Pertes**
- Réduction drastique après grosse perte
- Paramètres : threshold_R (3), emergency_risk (0.3%)

**S12 : Anti-Martingale Classique**
- Augmente après gain, réduit après perte
- Paramètres : up_factor (1.2), down_factor (0.8)

**S13 : Série de Gains**
- Accélère après X gains consécutifs
- Paramètres : gain_streak (3), boosted_risk (1.5%)

**S14 : Heat Ramp**
- Augmente progressivement avec les gains
- Paramètres : ramp_factor (0.1%), streak_limit (5)

### Stratégies basées sur la Volatilité (S15-S17)

**S15 : Volatilité Interne**
- Réduit si volatilité élevée
- Paramètres : window (10), vol_factor (0.5)

**S16 : Stress Index**
- Compare variance récente vs globale
- Paramètres : window (20), stress_factor (0.3)

**S17 : Surprise Trade**
- Réagit aux trades exceptionnels
- Paramètres : gain_threshold (5R), loss_threshold (3R)

### Stratégies Mixtes (S18-S20)

**S18 : Déviation vs Espérance**
- Booste si performance > espérance
- Paramètres : window (50), up_factor (1.2)

**S19 : Risk Corridor**
- Mix DD + séries pour couloir de risque
- Paramètres : dd_threshold (10%), streak_threshold (4)

**S20 : Modèle Linéaire 3 Signaux**
- Combine DD, streak et volatilité
- Paramètres : a (0.3), b (0.4), c (0.3)

## 🎮 Exemple d'utilisation

### Scénario 1 : Tester une stratégie conservatrice
1. Capital : 1000€
2. Preset : Équilibré
3. Stratégie : **S3 - Mode Sécurité**
4. Paramètres : dd_threshold=10%, safe_risk=0.25%
5. Cliquer sur "1% x1000" pour lancer 1000 trades
6. Observer comment le risque passe à 0.25% dès que le DD dépasse -10%

### Scénario 2 : Tester une stratégie agressive
1. Capital : 1000€
2. Preset : Agressif
3. Stratégie : **S12 - Anti-Martingale Classique**
4. Paramètres : up_factor=1.3, down_factor=0.7
5. Cliquer sur "1% x1000"
6. Observer comment le risque augmente après chaque gain

### Scénario 3 : Comparer avec risque fixe
1. Capital : 1000€
2. Preset : Équilibré
3. Stratégie : **Risque Fixe** (aucune stratégie)
4. Cliquer sur "1% x1000"
5. Noter le capital final et le drawdown max
6. Redémarrer avec **S1 - Drawdown Linéaire**
7. Comparer les résultats

## 📊 Interprétation des résultats

Après une simulation de 1000 trades, vous verrez :

- **Capital final** : Résultat de la stratégie
- **Performance** : Gain/perte en %
- **Drawdown max** : Perte maximale depuis le sommet
- **Gain moyen** : Profit/perte moyen par trade
- **Écart-type** : Volatilité des résultats
- **Equity curve** : Graphique d'évolution du capital

### Indicateurs de qualité d'une stratégie

✅ **Bonne stratégie** :
- Drawdown max < 20%
- Performance positive sur 1000 trades
- Equity curve régulière avec peu de variations brutales

❌ **Stratégie risquée** :
- Drawdown max > 30%
- Nombreux crashes (capital < 1€)
- Equity curve très volatile

## 💡 Conseils

1. **Testez plusieurs stratégies** avec le même preset pour comparer
2. **Ajustez les paramètres** progressivement pour optimiser
3. **Combinez** : utilisez une stratégie conservatrice (S1-S4) avec un preset équilibré
4. **Notez vos résultats** pour identifier les meilleures configurations
5. **Évitez** : Stratégies agressives (S9, S12, S13) avec preset agressif = risque élevé

## 🔧 Architecture technique

### Frontend (simulator.js)
- Chargement dynamique des 20 stratégies depuis l'API
- Affichage des boutons S1-S20
- Configuration des paramètres
- Exécution via `/money-management/simulate/<strategy>/`

### Backend (money_management/)
- `strategies.py` : 20 fonctions de calcul du risque adaptatif
- `simulator.py` : Moteur de simulation de 1000 trades
- `views.py` : Endpoints API
- `urls.py` : Routing

### Intégration
- Aucune modification des fichiers existants de `home/`
- Module totalement indépendant
- Compatible avec tous les presets

## 🚀 Fonctionnalités futures

- [ ] Sauvegarde des résultats de simulation
- [ ] Comparaison multi-stratégies en parallèle
- [ ] Optimisation automatique des paramètres
- [ ] Export des résultats en CSV
- [ ] Stratégies personnalisées

---

**Développé par** : Money Management Simulator (MMS)  
**Version** : 2.0 - Stratégies Adaptatives
