"""
Script de vérification de l'espérance mathématique du simulateur
"""

# Définition des issues
outcomes = (
    [-2] * 12 +  # 12 issues de perte 2R
    [-5] * 2 +   # 2 issues de perte 5R
    [2] * 3 +    # 3 issues de gain 2R
    [3] * 2 +    # 2 issues de gain 3R
    [4] * 1 +    # 1 issue de gain 4R
    [5] * 1 +    # 1 issue de gain 5R
    [9] * 1      # 1 issue de gain 9R
)

print("=" * 60)
print("VÉRIFICATION DES PROBABILITÉS DU SIMULATEUR")
print("=" * 60)
print()

# Vérifier qu'on a bien 22 issues
print(f"Nombre total d'issues : {len(outcomes)}")
print()

# Compter chaque issue
from collections import Counter
count = Counter(outcomes)

print("Distribution des issues :")
print("-" * 60)
for multiplier in sorted(count.keys()):
    nb = count[multiplier]
    prob = (nb / len(outcomes)) * 100
    print(f"  {multiplier:+3}R : {nb:2} fois -> {prob:5.2f}% de chances")
print()

# Calculer l'espérance mathématique
expectation = sum(outcomes) / len(outcomes)
print("=" * 60)
print(f"ESPÉRANCE MATHÉMATIQUE : {expectation:+.4f}R par trade")
print("=" * 60)
print()

# Simulation sur 10000 trades
import random
print("SIMULATION SUR 10 000 TRADES :")
print("-" * 60)

capital = 1000
risk_percent = 0.5  # 0.5% de risque
results = []

for i in range(10000):
    risk_amount = capital * (risk_percent / 100)
    multiplier = random.choice(outcomes)
    profit_loss = risk_amount * multiplier
    capital += profit_loss
    results.append(multiplier)

final_performance = ((capital - 1000) / 1000) * 100

print(f"Capital initial : 1000€")
print(f"Risque par trade : {risk_percent}%")
print(f"Capital final : {capital:.2f}€")
print(f"Performance : {final_performance:+.2f}%")
print()

# Vérifier la distribution réelle
count_real = Counter(results)
print("Distribution réelle sur 10 000 trades :")
print("-" * 60)
for multiplier in sorted(count_real.keys()):
    nb = count_real[multiplier]
    prob_real = (nb / len(results)) * 100
    prob_expected = (count[multiplier] / len(outcomes)) * 100
    diff = prob_real - prob_expected
    print(f"  {multiplier:+3}R : {nb:4} fois -> {prob_real:5.2f}% (attendu: {prob_expected:5.2f}%, diff: {diff:+.2f}%)")

print()
print("=" * 60)
if expectation > 0:
    print("✅ Espérance POSITIVE : Le jeu est gagnant sur le long terme")
    print("   Avec un bon money management, le capital devrait croître.")
else:
    print("⚠️  Espérance NÉGATIVE : Le jeu est perdant sur le long terme")
    print("   Même avec un bon money management, le capital va diminuer.")
    print("   C'est un bon simulateur pour comprendre l'importance de")
    print("   l'espérance mathématique et du money management !")
print("=" * 60)
