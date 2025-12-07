"""
20 Stratégies de Money Management Adaptatif
Chaque stratégie calcule le risque à appliquer au prochain trade
en fonction de l'historique des trades précédents.
"""

from decimal import Decimal


def strategy_1_drawdown_lineaire(history, capital, dd1=5, dd2=20, base_risk=1.0):
    """
    Drawdown linéaire : réduit le risque proportionnellement au DD
    
    Params:
        dd1: Seuil DD (%) où commence la réduction (défaut: 5%)
        dd2: Seuil DD (%) où le risque atteint le minimum (défaut: 20%)
        base_risk: Risque de base en % (défaut: 1.0%)
    """
    if not history:
        return base_risk
    
    # Calculer le drawdown actuel
    max_capital = max([t['capital_after'] for t in history] + [capital])
    dd = ((capital - max_capital) / max_capital) * 100
    
    if dd >= -dd1:
        return base_risk
    elif dd <= -dd2:
        return base_risk * 0.2  # 20% du risque de base
    else:
        # Interpolation linéaire entre dd1 et dd2
        ratio = (abs(dd) - dd1) / (dd2 - dd1)
        return base_risk * (1 - 0.8 * ratio)


def strategy_2_dd_lineaire(history, capital, base_risk=1.0, dd_step=5, decay=0.8, min_risk=0.1):
    """
    Drawdown linéaire : réduit le risque par paliers de DD
    
    Params:
        base_risk: Risque de base en % (défaut: 1.0%)
        dd_step: Intervalle DD (%) pour chaque réduction (défaut: 5%)
        decay: Facteur de décroissance (défaut: 0.8)
        min_risk: Risque minimum en % (défaut: 0.1%)
    """
    if not history:
        return base_risk
    
    max_capital = max([t['capital_after'] for t in history] + [capital])
    dd = ((capital - max_capital) / max_capital) * 100
    
    # Nombre de paliers de DD
    steps = max(0, int(abs(dd) / dd_step))
    risk = base_risk * (decay ** steps)
    
    # Appliquer le seuil minimum
    return max(min_risk, risk)


def strategy_3_mode_securite(history, capital, base_risk=1.0, dd_threshold=15, safe_risk=0.25):
    """
    Mode sécurité : bascule vers un risque minimal au-delà d'un seuil DD
    
    Params:
        base_risk: Risque de base en % (défaut: 1.0%)
        dd_threshold: Seuil DD (%) pour activer le mode sécurité (défaut: 15%)
        safe_risk: Risque en mode sécurité en % (défaut: 0.25%)
    """
    if not history:
        return base_risk
    
    max_capital = max([t['capital_after'] for t in history] + [capital])
    dd = ((capital - max_capital) / max_capital) * 100
    
    return safe_risk if dd < -dd_threshold else base_risk


def strategy_4_dd_max_historique(history, capital, base_risk=1.0, ratio_threshold=0.7, low_risk=0.5):
    """
    Basé sur DD max historique : si DD actuel > 70% du DD max, réduire
    
    Params:
        base_risk: Risque de base en % (défaut: 1.0%)
        ratio_threshold: Ratio DD actuel / DD max pour réduire (défaut: 0.7)
        low_risk: Risque réduit en % (défaut: 0.5%)
    """
    if not history or len(history) < 10:
        return base_risk
    
    # Calculer DD actuel
    max_capital = max([t['capital_after'] for t in history] + [capital])
    current_dd = ((capital - max_capital) / max_capital) * 100
    
    # Calculer DD max historique
    max_dd = 0
    for i, trade in enumerate(history):
        peak = max([t['capital_after'] for t in history[:i+1]])
        dd = ((trade['capital_after'] - peak) / peak) * 100
        max_dd = min(max_dd, dd)
    
    if max_dd == 0:
        return base_risk
    
    ratio = current_dd / max_dd
    return low_risk if ratio > ratio_threshold else base_risk


def strategy_5_scaling_lineaire_capital(history, capital, base_risk=1.0, gain_step=10, increment=0.1, max_risk=5.0):
    """
    Scaling linéaire capital : augmente le risque tous les X% de gain
    
    Params:
        base_risk: Risque de base en % (défaut: 1.0%)
        gain_step: Palier de gain (%) pour augmenter le risque (défaut: 10%)
        increment: Augmentation du risque par palier en % (défaut: 0.1%)
        max_risk: Risque maximum à ne jamais dépasser en % (défaut: 5.0%)
    """
    if not history:
        return base_risk
    
    initial_capital = history[0]['capital_before'] if history else capital
    gain_percent = ((capital - initial_capital) / initial_capital) * 100
    
    if gain_percent <= 0:
        return base_risk
    
    steps = int(gain_percent / gain_step)
    calculated_risk = base_risk + (steps * increment)
    return min(calculated_risk, max_risk)


def strategy_6_scaling_geometrique(history, capital, base_risk=1.0, growth_rate=1.1, step=10, max_risk=5.0):
    """
    Scaling géométrique : croissance exponentielle du risque
    
    Params:
        base_risk: Risque de base en % (défaut: 1.0%)
        growth_rate: Taux de croissance (défaut: 1.1 = +10%)
        step: Palier de gain (%) pour augmenter (défaut: 10%)
        max_risk: Risque maximum à ne jamais dépasser en % (défaut: 5.0%)
    """
    if not history:
        return base_risk
    
    initial_capital = history[0]['capital_before'] if history else capital
    gain_percent = ((capital - initial_capital) / initial_capital) * 100
    
    if gain_percent <= 0:
        return base_risk
    
    steps = int(gain_percent / step)
    calculated_risk = base_risk * (growth_rate ** steps)
    return min(calculated_risk, max_risk)


def strategy_7_risk_reset(history, capital, base_risk=1.0, plateau_step=5, reset_risk=1.5):
    """
    Risk Reset : augmente le risque après X trades sans nouveau ATH
    
    Params:
        base_risk: Risque de base en % (défaut: 1.0%)
        plateau_step: Nombre de trades sans ATH pour boost (défaut: 5)
        reset_risk: Risque augmenté en % (défaut: 1.5%)
    """
    if not history or len(history) < plateau_step:
        return base_risk
    
    # Trouver le dernier ATH
    max_capital = max([t['capital_after'] for t in history])
    trades_since_ath = 0
    
    for trade in reversed(history):
        if trade['capital_after'] >= max_capital:
            break
        trades_since_ath += 1
    
    return reset_risk if trades_since_ath >= plateau_step else base_risk


def strategy_8_ath_distance(history, capital, base_risk=1.0, ath_distance=10, boost_risk=1.2):
    """
    ATH distance : booste le risque si proche de l'ATH
    
    Params:
        base_risk: Risque de base en % (défaut: 1.0%)
        ath_distance: Distance (%) de l'ATH pour boost (défaut: 10%)
        boost_risk: Risque boosté en % (défaut: 1.2%)
    """
    if not history:
        return base_risk
    
    max_capital = max([t['capital_after'] for t in history] + [capital])
    distance = ((max_capital - capital) / max_capital) * 100
    
    return boost_risk if distance < ath_distance else base_risk


def strategy_9_anti_martingale_inversee(history, capital, base_risk=1.0, up_factor=1.2, down_factor=0.8, min_risk=0.1, max_risk=5.0):
    """
    Anti-martingale inversée : augmente après perte, réduit après gain
    
    Params:
        base_risk: Risque de base en % (défaut: 1.0%)
        up_factor: Facteur d'augmentation après perte (défaut: 1.2)
        down_factor: Facteur de réduction après gain (défaut: 0.8)
        min_risk: Risque minimum en % (défaut: 0.1%)
        max_risk: Risque maximum en % (défaut: 5.0%)
    """
    if not history:
        return base_risk
    
    last_trade = history[-1]
    was_win = last_trade['profit_loss'] > 0
    
    risk = base_risk * down_factor if was_win else base_risk * up_factor
    
    # Appliquer les seuils min et max
    return max(min_risk, min(risk, max_risk))


def strategy_10_pertes_consecutives(history, capital, base_risk=1.0, loss_streak=3, reduced_risk=0.5):
    """
    3 pertes consécutives : réduit le risque après une série de pertes
    
    Params:
        base_risk: Risque de base en % (défaut: 1.0%)
        loss_streak: Nombre de pertes consécutives pour réduire (défaut: 3)
        reduced_risk: Risque réduit en % (défaut: 0.5%)
    """
    if not history or len(history) < loss_streak:
        return base_risk
    
    # Vérifier les N derniers trades
    recent_trades = history[-loss_streak:]
    consecutive_losses = all(t['profit_loss'] < 0 for t in recent_trades)
    
    return reduced_risk if consecutive_losses else base_risk


def strategy_11_gestion_grosses_pertes(history, capital, base_risk=1.0, threshold_R=3, emergency_risk=0.3):
    """
    Gestion grosses pertes : réduit drastiquement après une grosse perte
    
    Params:
        base_risk: Risque de base en % (défaut: 1.0%)
        threshold_R: Seuil de perte en R pour réduire (défaut: 3R)
        emergency_risk: Risque d'urgence en % (défaut: 0.3%)
    """
    if not history:
        return base_risk
    
    last_trade = history[-1]
    loss_R = abs(last_trade['outcome_multiplier']) if last_trade['profit_loss'] < 0 else 0
    
    return emergency_risk if loss_R >= threshold_R else base_risk


def strategy_13_anti_martingale_classique(history, capital, base_risk=1.0, up_factor=1.2, down_factor=0.8, min_risk=0.1, max_risk=5.0):
    """
    Anti-martingale classique : augmente après gain, réduit après perte
    
    Params:
        base_risk: Risque de base en % (défaut: 1.0%)
        up_factor: Facteur d'augmentation après gain (défaut: 1.2)
        down_factor: Facteur de réduction après perte (défaut: 0.8)
        min_risk: Risque minimum en % (défaut: 0.1%)
        max_risk: Risque maximum en % (défaut: 5.0%)
    """
    if not history:
        return base_risk
    
    last_trade = history[-1]
    was_win = last_trade['profit_loss'] > 0
    
    risk = base_risk * up_factor if was_win else base_risk * down_factor
    
    # Appliquer les seuils min et max
    return max(min_risk, min(risk, max_risk))


def strategy_13_serie_gains(history, capital, base_risk=1.0, gain_streak=3, boosted_risk=1.5):
    """
    Série de gains : accélère après X gains consécutifs
    
    Params:
        base_risk: Risque de base en % (défaut: 1.0%)
        gain_streak: Nombre de gains consécutifs pour boost (défaut: 3)
        boosted_risk: Risque boosté en % (défaut: 1.5%)
    """
    if not history or len(history) < gain_streak:
        return base_risk
    
    recent_trades = history[-gain_streak:]
    consecutive_wins = all(t['profit_loss'] > 0 for t in recent_trades)
    
    return boosted_risk if consecutive_wins else base_risk


def strategy_14_heat_ramp(history, capital, base_risk=1.0, ramp_factor=0.1, streak_limit=5):
    """
    Heat Ramp : augmente progressivement le risque avec les gains
    
    Params:
        base_risk: Risque de base en % (défaut: 1.0%)
        ramp_factor: Augmentation par gain consécutif (défaut: 0.1%)
        streak_limit: Limite de la série (défaut: 5)
    """
    if not history:
        return base_risk
    
    consecutive_wins = 0
    for trade in reversed(history):
        if trade['profit_loss'] > 0:
            consecutive_wins += 1
        else:
            break
    
    consecutive_wins = min(consecutive_wins, streak_limit)
    return base_risk + (consecutive_wins * ramp_factor)


def strategy_15_volatilite_interne(history, capital, base_risk=1.0, window=10, vol_factor=0.5):
    """
    Volatilité interne : réduit le risque si volatilité élevée
    
    Params:
        base_risk: Risque de base en % (défaut: 1.0%)
        window: Fenêtre de calcul de volatilité (défaut: 10 trades)
        vol_factor: Facteur de réduction par unité de vol (défaut: 0.5)
    """
    if not history or len(history) < window:
        return base_risk
    
    recent_trades = history[-window:]
    returns = [t['profit_loss'] / t['capital_before'] for t in recent_trades]
    
    # Calculer l'écart-type
    mean_return = sum(returns) / len(returns)
    variance = sum((r - mean_return) ** 2 for r in returns) / len(returns)
    volatility = variance ** 0.5
    
    # Réduire le risque si volatilité > 5%
    if volatility > 0.05:
        return max(0.25, base_risk - vol_factor * (volatility - 0.05) * 10)
    
    return base_risk


def strategy_16_stress_index(history, capital, base_risk=1.0, window=20, stress_factor=0.3):
    """
    Stress Index : compare variance récente vs variance globale
    
    Params:
        base_risk: Risque de base en % (défaut: 1.0%)
        window: Fenêtre de comparaison (défaut: 20 trades)
        stress_factor: Réduction par unité de stress (défaut: 0.3)
    """
    if not history or len(history) < window * 2:
        return base_risk
    
    # Variance globale
    all_returns = [t['profit_loss'] / t['capital_before'] for t in history]
    global_mean = sum(all_returns) / len(all_returns)
    global_var = sum((r - global_mean) ** 2 for r in all_returns) / len(all_returns)
    
    # Variance récente
    recent_trades = history[-window:]
    recent_returns = [t['profit_loss'] / t['capital_before'] for t in recent_trades]
    recent_mean = sum(recent_returns) / len(recent_returns)
    recent_var = sum((r - recent_mean) ** 2 for r in recent_returns) / len(recent_returns)
    
    if global_var == 0:
        return base_risk
    
    stress = recent_var / global_var
    
    if stress > 1.5:  # Stress élevé
        return max(0.25, base_risk - stress_factor * (stress - 1.5))
    
    return base_risk


def strategy_17_surprise_trade(history, capital, base_risk=1.0, gain_threshold=5, loss_threshold=3, boost_factor=1.3, reduce_factor=0.5):
    """
    Surprise trade : réagit aux trades exceptionnels
    
    Params:
        base_risk: Risque de base en % (défaut: 1.0%)
        gain_threshold: Seuil de gain (R) pour boost (défaut: 5R)
        loss_threshold: Seuil de perte (R) pour réduction (défaut: 3R)
        boost_factor: Facteur de boost (défaut: 1.3)
        reduce_factor: Facteur de réduction (défaut: 0.5)
    """
    if not history:
        return base_risk
    
    last_trade = history[-1]
    multiplier = abs(last_trade['outcome_multiplier'])
    
    if last_trade['profit_loss'] > 0 and multiplier >= gain_threshold:
        return base_risk * boost_factor  # Boost après gros gain
    elif last_trade['profit_loss'] < 0 and multiplier >= loss_threshold:
        return base_risk * reduce_factor  # Réduction après grosse perte
    
    return base_risk


def strategy_18_deviation_vs_esperance(history, capital, base_risk=1.0, window=50, up_factor=1.2):
    """
    Déviation vs espérance : booste si performance > espérance
    
    Params:
        base_risk: Risque de base en % (défaut: 1.0%)
        window: Fenêtre de calcul (défaut: 50 trades)
        up_factor: Facteur de boost (défaut: 1.2)
    """
    if not history or len(history) < window:
        return base_risk
    
    recent_trades = history[-window:]
    
    # Performance moyenne
    avg_return = sum(t['profit_loss'] / t['risk_amount'] for t in recent_trades) / len(recent_trades)
    
    # Espérance théorique (calculée à partir des multipliers observés)
    multipliers = [t['outcome_multiplier'] for t in recent_trades]
    expected_return = sum(multipliers) / len(multipliers)
    
    # Si performance > espérance, boost
    if avg_return > expected_return * 1.2:
        return base_risk * up_factor
    
    return base_risk


def strategy_19_risk_corridor(history, capital, base_risk=1.0, dd_threshold=10, streak_threshold=4, drastic_factor=0.25, moderate_factor=0.5):
    """
    Risk Corridor : mix DD + séries pour définir un couloir de risque
    
    Params:
        base_risk: Risque de base en % (défaut: 1.0%)
        dd_threshold: Seuil DD (%) pour réduction (défaut: 10%)
        streak_threshold: Nombre de pertes pour réduction (défaut: 4)
        drastic_factor: Facteur de réduction drastique (défaut: 0.25)
        moderate_factor: Facteur de réduction modérée (défaut: 0.5)
    """
    if not history:
        return base_risk
    
    # Calcul DD
    max_capital = max([t['capital_after'] for t in history] + [capital])
    dd = ((capital - max_capital) / max_capital) * 100
    
    # Calcul série de pertes
    consecutive_losses = 0
    for trade in reversed(history):
        if trade['profit_loss'] < 0:
            consecutive_losses += 1
        else:
            break
    
    # Critères de réduction
    dd_signal = dd < -dd_threshold
    streak_signal = consecutive_losses >= streak_threshold
    
    if dd_signal and streak_signal:
        return base_risk * drastic_factor  # Réduction drastique
    elif dd_signal or streak_signal:
        return base_risk * moderate_factor  # Réduction modérée
    
    return base_risk


def strategy_20_modele_lineaire_3_signaux(history, capital, base_risk=1.0, a=0.3, b=0.4, c=0.3):
    """
    Modèle linéaire 3 signaux : combine DD, streak et volatilité
    
    Params:
        base_risk: Risque de base en % (défaut: 1.0%)
        a: Poids du signal DD (défaut: 0.3)
        b: Poids du signal streak (défaut: 0.4)
        c: Poids du signal volatilité (défaut: 0.3)
    """
    if not history or len(history) < 10:
        return base_risk
    
    # Signal 1: DD (0 = pas de DD, 1 = DD max)
    max_capital = max([t['capital_after'] for t in history] + [capital])
    dd = ((capital - max_capital) / max_capital) * 100
    dd_signal = min(1.0, abs(dd) / 20)  # Normalisé sur 20%
    
    # Signal 2: Streak de pertes (0 = pas de série, 1 = série max)
    consecutive_losses = 0
    for trade in reversed(history):
        if trade['profit_loss'] < 0:
            consecutive_losses += 1
        else:
            break
    streak_signal = min(1.0, consecutive_losses / 5)  # Normalisé sur 5 pertes
    
    # Signal 3: Volatilité (0 = basse vol, 1 = haute vol)
    recent_trades = history[-10:]
    returns = [t['profit_loss'] / t['capital_before'] for t in recent_trades]
    mean_return = sum(returns) / len(returns)
    variance = sum((r - mean_return) ** 2 for r in returns) / len(returns)
    volatility = variance ** 0.5
    vol_signal = min(1.0, volatility / 0.1)  # Normalisé sur 10% de vol
    
    # Modèle linéaire
    risk_reduction = a * dd_signal + b * streak_signal + c * vol_signal
    
    # Risque final: base_risk si signaux = 0, base_risk * 0.25 si signaux = max
    return max(0.25 * base_risk, base_risk * (1.0 - 0.75 * risk_reduction))


# Dictionnaire des stratégies pour accès facile
STRATEGIES = {
    'strategy_1': {
        'name': 'Drawdown Linéaire',
        'function': strategy_1_drawdown_lineaire,
        'params': {'dd1': 5, 'dd2': 20, 'base_risk': 1.0},
        'description': 'Réduit le risque proportionnellement au drawdown'
    },
    'strategy_2': {
        'name': 'Drawdown Géométrique',
        'function': strategy_2_dd_lineaire,
        'params': {'base_risk': 1.0, 'dd_step': 5, 'decay': 0.8, 'min_risk': 0.1},
        'description': 'Réduction exponentielle du risque selon le DD'
    },
    'strategy_3': {
        'name': 'Mode Sécurité',
        'function': strategy_3_mode_securite,
        'params': {'base_risk': 1.0, 'dd_threshold': 15, 'safe_risk': 0.25},
        'description': 'Bascule en mode sécurisé au-delà d\'un seuil DD'
    },
    'strategy_4': {
        'name': 'DD Max Historique',
        'function': strategy_4_dd_max_historique,
        'params': {'base_risk': 1.0, 'ratio_threshold': 0.7, 'low_risk': 0.5},
        'description': 'Compare DD actuel au DD max historique'
    },
    'strategy_5': {
        'name': 'Scaling Linéaire Capital',
        'function': strategy_5_scaling_lineaire_capital,
        'params': {'base_risk': 1.0, 'gain_step': 10, 'increment': 0.1, 'max_risk': 5.0},
        'description': 'Augmente le risque tous les X% de gain'
    },
    'strategy_6': {
        'name': 'Scaling Géométrique',
        'function': strategy_6_scaling_geometrique,
        'params': {'base_risk': 1.0, 'growth_rate': 1.1, 'step': 10, 'max_risk': 5.0},
        'description': 'Croissance exponentielle du risque'
    },
    'strategy_7': {
        'name': 'Risk Reset',
        'function': strategy_7_risk_reset,
        'params': {'base_risk': 1.0, 'plateau_step': 5, 'reset_risk': 1.5},
        'description': 'Augmente après X trades sans ATH'
    },
    'strategy_8': {
        'name': 'ATH Distance',
        'function': strategy_8_ath_distance,
        'params': {'base_risk': 1.0, 'ath_distance': 10, 'boost_risk': 1.2},
        'description': 'Booste si proche de l\'ATH'
    },
    'strategy_9': {
        'name': 'Anti-Martingale Inversée',
        'function': strategy_9_anti_martingale_inversee,
        'params': {'base_risk': 1.0, 'up_factor': 1.2, 'down_factor': 0.8, 'min_risk': 0.1, 'max_risk': 5.0},
        'description': 'Augmente après perte, réduit après gain'
    },
    'strategy_10': {
        'name': '3 Pertes Consécutives',
        'function': strategy_10_pertes_consecutives,
        'params': {'base_risk': 1.0, 'loss_streak': 3, 'reduced_risk': 0.5},
        'description': 'Réduit après série de pertes'
    },
    'strategy_11': {
        'name': 'Gestion Grosses Pertes',
        'function': strategy_11_gestion_grosses_pertes,
        'params': {'base_risk': 1.0, 'threshold_R': 3, 'emergency_risk': 0.3},
        'description': 'Réduction drastique après grosse perte'
    },
    'strategy_12': {
        'name': 'Anti-Martingale Classique',
        'function': strategy_13_anti_martingale_classique,
        'params': {'base_risk': 1.0, 'up_factor': 1.2, 'down_factor': 0.8, 'min_risk': 0.1, 'max_risk': 5.0},
        'description': 'Augmente après gain, réduit après perte'
    },
    'strategy_13': {
        'name': 'Série de Gains',
        'function': strategy_13_serie_gains,
        'params': {'base_risk': 1.0, 'gain_streak': 3, 'boosted_risk': 1.5},
        'description': 'Accélère après X gains consécutifs'
    },
    'strategy_14': {
        'name': 'Heat Ramp',
        'function': strategy_14_heat_ramp,
        'params': {'base_risk': 1.0, 'ramp_factor': 0.1, 'streak_limit': 5},
        'description': 'Augmente progressivement avec les gains'
    },
    'strategy_15': {
        'name': 'Volatilité Interne',
        'function': strategy_15_volatilite_interne,
        'params': {'base_risk': 1.0, 'window': 10, 'vol_factor': 0.5},
        'description': 'Réduit si volatilité élevée'
    },
    'strategy_16': {
        'name': 'Stress Index',
        'function': strategy_16_stress_index,
        'params': {'base_risk': 1.0, 'window': 20, 'stress_factor': 0.3},
        'description': 'Compare variance récente vs globale'
    },
    'strategy_17': {
        'name': 'Surprise Trade',
        'function': strategy_17_surprise_trade,
        'params': {'base_risk': 1.0, 'gain_threshold': 5, 'loss_threshold': 3, 'boost_factor': 1.3, 'reduce_factor': 0.5},
        'description': 'Réagit aux trades exceptionnels'
    },
    'strategy_18': {
        'name': 'Déviation vs Espérance',
        'function': strategy_18_deviation_vs_esperance,
        'params': {'base_risk': 1.0, 'window': 50, 'up_factor': 1.2},
        'description': 'Booste si performance > espérance'
    },
    'strategy_19': {
        'name': 'Risk Corridor',
        'function': strategy_19_risk_corridor,
        'params': {'base_risk': 1.0, 'dd_threshold': 10, 'streak_threshold': 4, 'drastic_factor': 0.25, 'moderate_factor': 0.5},
        'description': 'Mix DD + séries pour couloir de risque'
    },
    'strategy_20': {
        'name': 'Modèle Linéaire 3 Signaux',
        'function': strategy_20_modele_lineaire_3_signaux,
        'params': {'base_risk': 1.0, 'a': 0.3, 'b': 0.4, 'c': 0.3},
        'description': 'Combine DD, streak et volatilité'
    }
}
