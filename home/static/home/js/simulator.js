// Configuration globale
let equityChart = null;
let riskChart = null;
let isSessionStarted = false;
let lastTradeData = null;
let presetsData = {};
let selectedPreset = 'balanced';
let strategiesData = [];
let selectedStrategy = 'none';
let strategyParams = {};

// Messages de motivation basés sur les résultats
const winMessages = [
    "Patience and precise entry allow you to do like Dan: You win twice your risk with surgical precision.",
    "Excellent timing! Your risk management is paying off.",
    "Perfect execution! This is how professionals trade.",
    "Your discipline is rewarded. Keep maintaining this consistency.",
    "Great trade! Your patience is your greatest asset.",
];

const lossMessages = [
    "Every loss is a lesson. Stay disciplined and keep your risk under control.",
    "Drawdown is temporary. Your strategy and patience will prevail.",
    "The market tests your discipline. Stay focused on the long term.",
    "Even the best traders face losses. What matters is how you manage them.",
    "This is part of the journey. Your money management will protect you.",
];

// Initialisation au chargement de la page
document.addEventListener('DOMContentLoaded', function() {
    initializeChart();
    initializeRiskChart();
    setupEventListeners();
    loadPresets();
    loadStrategies();
    loadStats();
});

// Configuration des écouteurs d'événements
function setupEventListeners() {
    // Bouton de démarrage
    document.getElementById('startBtn').addEventListener('click', startNewSession);
    
    // Boutons de risque (1 trade)
    document.querySelectorAll('.risk-btn:not(.x1000-btn)').forEach(btn => {
        btn.addEventListener('click', function() {
            if (isSessionStarted) {
                const riskPercent = parseFloat(this.dataset.risk);
                executeTrade(riskPercent);
            }
        });
    });
    
    // Boutons x1000 (1000 trades)
    document.querySelectorAll('.x1000-btn:not(.special-btn)').forEach(btn => {
        btn.addEventListener('click', function() {
            if (isSessionStarted) {
                const riskPercent = parseFloat(this.dataset.risk);
                const multiplier = parseInt(this.dataset.multiplier);
                executeMultipleTrades(riskPercent, multiplier);
            }
        });
    });
    
    // Bouton spécial x1000 pour les stratégies
    const specialBtn = document.querySelector('.special-btn');
    if (specialBtn) {
        specialBtn.addEventListener('click', function() {
            if (isSessionStarted) {
                if (selectedStrategy === 'none') {
                    alert('⚠️ Veuillez sélectionner une stratégie de Money Management (S1-S20) avant de lancer la simulation.');
                } else {
                    executeMultipleTrades(1, 1000); // Le risque sera calculé par la stratégie
                }
            }
        });
    }
    
    // Bouton restart
    document.getElementById('restartBtn').addEventListener('click', function() {
        resetStrategySelection();
        showInitialSetup();
    });
    
    // Boutons de preset
    document.querySelectorAll('.preset-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            // Retirer active de tous les boutons
            document.querySelectorAll('.preset-btn').forEach(b => b.classList.remove('active'));
            // Ajouter active au bouton cliqué
            this.classList.add('active');
            
            selectedPreset = this.dataset.preset;
            updateDistributionDisplay();
        });
    });
}

// Charger les stratégies de Money Management
async function loadStrategies() {
    try {
        const response = await fetch('/money-management/strategies/');
        const data = await response.json();
        
        if (data.success) {
            strategiesData = data.strategies;
            displayStrategies();
        }
    } catch (error) {
        console.error('Erreur lors du chargement des stratégies:', error);
    }
}

// Afficher les stratégies dans la grille
function displayStrategies() {
    const grid = document.getElementById('strategiesGrid');
    grid.innerHTML = '';
    
    strategiesData.forEach((strategy, index) => {
        const btn = document.createElement('button');
        btn.className = 'strategy-btn';
        btn.dataset.strategy = strategy.key;
        btn.textContent = `S${index + 1}`;
        btn.title = `${strategy.name}\n${strategy.description}`;
        
        btn.addEventListener('click', function() {
            selectStrategy(strategy.key, strategy, index + 1);
        });
        
        grid.appendChild(btn);
    });
}

// Sélectionner une stratégie
function selectStrategy(strategyKey, strategyInfo, number) {
    selectedStrategy = strategyKey;
    
    // Mettre à jour les boutons actifs
    document.querySelectorAll('.strategy-btn').forEach(b => b.classList.remove('active'));
    document.querySelector(`[data-strategy="${strategyKey}"]`).classList.add('active');
    
    // Afficher les paramètres de la stratégie
    displayStrategyParams(strategyInfo, number);
}

// Afficher les paramètres d'une stratégie
function displayStrategyParams(strategyInfo, number) {
    const paramsContainer = document.getElementById('strategyParams');
    paramsContainer.style.display = 'block';
    
    let html = `<h4>⚙️ Stratégie S${number}: ${strategyInfo.name}</h4>`;
    html += `<p style="color: #888; margin-bottom: 15px; font-size: 0.9rem;">${strategyInfo.description}</p>`;
    
    // Créer les inputs pour chaque paramètre
    for (const [paramName, defaultValue] of Object.entries(strategyInfo.params)) {
        html += `
            <div class="param-group">
                <label for="param_${paramName}">${paramName}:</label>
                <input type="number" 
                       id="param_${paramName}" 
                       name="${paramName}" 
                       value="${defaultValue}" 
                       step="0.1">
            </div>
        `;
    }
    
    paramsContainer.innerHTML = html;
    
    // Initialiser strategyParams avec les valeurs par défaut
    strategyParams = {...strategyInfo.params};
    
    // Écouter les changements de paramètres
    paramsContainer.querySelectorAll('input').forEach(input => {
        input.addEventListener('change', function() {
            strategyParams[this.name] = parseFloat(this.value);
        });
    });
}

// Réinitialiser la sélection de stratégie
function resetStrategySelection() {
    selectedStrategy = 'none';
    strategyParams = {};
    
    // Désactiver tous les boutons de stratégie
    document.querySelectorAll('.strategy-btn').forEach(b => b.classList.remove('active'));
    
    // Cacher les paramètres
    document.getElementById('strategyParams').style.display = 'none';
}

// Charger les presets depuis le serveur
async function loadPresets() {
    try {
        const response = await fetch('/api/get-presets/');
        const data = await response.json();
        
        if (data.success) {
            presetsData = data.presets;
            updateDistributionDisplay();
        }
    } catch (error) {
        console.error('Erreur lors du chargement des presets:', error);
    }
}

// Mettre à jour l'affichage de la distribution
function updateDistributionDisplay() {
    if (!presetsData[selectedPreset]) return;
    
    const preset = presetsData[selectedPreset];
    const desc = preset.description;
    const expectation = preset.expectation;
    
    document.getElementById('distributionDesc').textContent = desc;
    
    const expEl = document.getElementById('expectedValue');
    expEl.textContent = `${expectation >= 0 ? '+' : ''}${expectation.toFixed(3)}R`;
    expEl.style.color = expectation >= 0 ? '#4CAF50' : '#e74c3c';
    
    // Mettre à jour l'espérance dans la distribution
    const expValueEl = document.getElementById('expectation-value');
    const expIconEl = document.getElementById('expectation-icon');
    const expDisplayEl = document.getElementById('expectation-display');
    
    if (expValueEl && expIconEl && expDisplayEl) {
        expValueEl.textContent = `${expectation >= 0 ? '+' : ''}${expectation.toFixed(3)}R par trade`;
        
        if (expectation >= 0) {
            expIconEl.textContent = '(POSITIVE ✅)';
            expDisplayEl.className = 'expectation-info success';
        } else {
            expIconEl.textContent = '(NÉGATIVE ❌)';
            expDisplayEl.className = 'expectation-info warning';
        }
    }
}

// Afficher la configuration initiale
function showInitialSetup() {
    document.getElementById('initialSetup').classList.remove('hidden');
    isSessionStarted = false;
    
    // Réactiver tous les boutons de trading
    document.querySelectorAll('.risk-btn').forEach(btn => btn.disabled = false);
}

// Démarrer une nouvelle session
async function startNewSession() {
    const initialCapital = parseFloat(document.getElementById('initialCapital').value);
    
    if (initialCapital < 100) {
        alert('Le capital initial doit être au moins de 100€');
        return;
    }
    
    // Récupérer la configuration du preset sélectionné
    const outcomesConfig = presetsData[selectedPreset]?.outcomes || {};
    
    try {
        const response = await fetch('/api/start-session/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                initial_capital: initialCapital,
                outcomes_config: outcomesConfig
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            document.getElementById('initialSetup').classList.add('hidden');
            isSessionStarted = true;
            
            // Réinitialiser l'interface
            updateStats({
                current_capital: initialCapital,
                initial_capital: initialCapital,
                total_trades: 0,
                wins: 0,
                losses: 0,
                success_rate: 0,
                performance: 0,
                drawdown: 0,
                max_capital: initialCapital,
                max_performance: 0,
                max_drawdown: 0,
                consecutive_wins: 0,
                consecutive_losses: 0,
                outcome_distribution: {},
            });
            
            // Réinitialiser le graphique
            equityChart.data.labels = [0];
            equityChart.data.datasets[0].data = [initialCapital];
            equityChart.update();
            
            // Réinitialiser le message
            document.getElementById('outcomeMessage').textContent = 
                'Click on a risk percentage to start trading';
            
            // Réinitialiser les stats du dernier trade
            document.getElementById('lastRisk').textContent = '0%';
            document.getElementById('lastRiskAmount').textContent = '€0.00';
            document.getElementById('lastProfitLoss').textContent = '€0.00';
        }
    } catch (error) {
        console.error('Erreur lors du démarrage de la session:', error);
        alert('Erreur lors du démarrage de la session');
    }
}

// Exécuter plusieurs trades en batch (côté serveur avec progression réelle)
async function executeMultipleTrades(riskPercent, count) {
    // Si une stratégie est sélectionnée, utiliser la simulation de stratégie
    if (selectedStrategy !== 'none') {
        return executeStrategySimulation(count);
    }
    
    // Sinon, utiliser le risque fixe classique
    // Désactiver tous les boutons pendant l'exécution
    const allButtons = document.querySelectorAll('.risk-btn, .restart-btn');
    allButtons.forEach(btn => btn.disabled = true);
    
    // Afficher la barre de progression
    const outcomeEl = document.getElementById('outcomeMessage');
    outcomeEl.innerHTML = `
        <div style="color: #4CAF50; margin-bottom: 10px;">⏳ Exécution de ${count} trades avec ${riskPercent}% de risque...</div>
        <div style="width: 100%; background: rgba(255,255,255,0.1); border-radius: 10px; height: 30px; overflow: hidden;">
            <div id="progressBar" style="width: 0%; height: 100%; background: linear-gradient(90deg, #4CAF50, #45a049); transition: width 0.3s ease; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold;">
                0 / ${count}
            </div>
        </div>
    `;
    
    const progressBar = document.getElementById('progressBar');
    const batchSize = 100; // Exécuter par lots de 100
    let totalExecuted = 0;
    let accountCrashed = false;
    
    try {
        // Exécuter les trades par lots
        while (totalExecuted < count && !accountCrashed) {
            const remainingTrades = count - totalExecuted;
            const currentBatchSize = Math.min(batchSize, remainingTrades);
            
            const response = await fetch('/api/execute-batch-trades/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    risk_percent: riskPercent,
                    count: currentBatchSize
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                totalExecuted += data.trades_executed;
                accountCrashed = data.account_crashed;
                
                // Mettre à jour la progression
                const progress = (totalExecuted / count) * 100;
                progressBar.style.width = progress + '%';
                progressBar.textContent = `${totalExecuted} / ${count}`;
                
                // Mettre à jour les stats et le graphique en temps réel
                updateStats(data.stats);
                updateChart(data.history);
                
                // Si le compte a crashé, arrêter
                if (accountCrashed) {
                    break;
                }
            } else {
                throw new Error(data.error || 'Erreur lors de l\'exécution');
            }
        }
        
        // Message final selon l'état du compte
        if (accountCrashed) {
            outcomeEl.innerHTML = `<div style="color: #e74c3c; font-size: 1.2rem; font-weight: bold;">💀 GAME OVER! Votre compte a crashé après ${totalExecuted} trades!</div>`;
        } else {
            outcomeEl.innerHTML = `<div style="color: #4CAF50;">✅ ${totalExecuted} trades exécutés avec succès!</div>`;
        }
        
        // Animation sur le capital
        document.getElementById('currentCapital').classList.add('pulse');
        setTimeout(() => {
            document.getElementById('currentCapital').classList.remove('pulse');
        }, 500);
        
    } catch (error) {
        console.error('Erreur lors de l\'exécution multiple:', error);
        outcomeEl.innerHTML = `<div style="color: #e74c3c;">❌ Erreur lors de l'exécution des trades</div>`;
    } finally {
        // Réactiver tous les boutons
        allButtons.forEach(btn => btn.disabled = false);
    }
}

// Exécuter une simulation avec stratégie de Money Management
// Cette fonction exécute les trades par batch côté serveur avec calcul du risque adaptatif
async function executeStrategySimulation(count) {
    // Désactiver tous les boutons pendant l'exécution
    const allButtons = document.querySelectorAll('.risk-btn, .restart-btn');
    allButtons.forEach(btn => btn.disabled = true);
    
    // Afficher la barre de progression
    const outcomeEl = document.getElementById('outcomeMessage');
    const strategyInfo = strategiesData.find(s => s.key === selectedStrategy);
    outcomeEl.innerHTML = `
        <div style="color: #667eea; margin-bottom: 10px;">🎯 Exécution de ${count} trades avec la stratégie: ${strategyInfo.name}</div>
        <div style="width: 100%; background: rgba(255,255,255,0.1); border-radius: 10px; height: 30px; overflow: hidden;">
            <div id="progressBar" style="width: 0%; height: 100%; background: linear-gradient(90deg, #667eea, #764ba2); transition: width 0.3s ease; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold;">
                0 / ${count}
            </div>
        </div>
    `;
    
    const progressBar = document.getElementById('progressBar');
    const batchSize = 100; // Exécuter par lots de 100 trades
    let totalExecuted = 0;
    let accountCrashed = false;
    
    try {
        // Exécuter les trades par batch
        while (totalExecuted < count && !accountCrashed) {
            const remainingTrades = count - totalExecuted;
            const currentBatchSize = Math.min(batchSize, remainingTrades);
            
            // Appeler le nouveau endpoint qui exécute avec la stratégie
            const response = await fetch('/api/execute-strategy-batch/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    strategy_key: selectedStrategy,
                    params: strategyParams,
                    count: currentBatchSize
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                totalExecuted += data.trades_executed;
                accountCrashed = data.account_crashed;
                
                // Mettre à jour la progression
                const progress = (totalExecuted / count) * 100;
                progressBar.style.width = progress + '%';
                progressBar.textContent = `${totalExecuted} / ${count}`;
                
                // Mettre à jour les stats et le graphique en temps réel
                updateStats(data.stats);
                updateChart(data.history);
                
                // Si le compte a crashé, arrêter
                if (accountCrashed) {
                    break;
                }
            } else {
                throw new Error(data.error || 'Erreur lors de l\'exécution');
            }
        }
        
        // Message final selon l'état du compte
        if (accountCrashed) {
            outcomeEl.innerHTML = `<div style="color: #e74c3c; font-size: 1.2rem; font-weight: bold;">💀 GAME OVER! Le compte a crashé après ${totalExecuted} trades avec la stratégie ${strategyInfo.name}!</div>`;
        } else {
            outcomeEl.innerHTML = `<div style="color: #667eea; font-size: 1.1rem; font-weight: bold;">✅ ${totalExecuted} trades exécutés avec succès avec la stratégie ${strategyInfo.name}!</div>`;
        }
        
        // Animation sur le capital
        document.getElementById('currentCapital').classList.add('pulse');
        setTimeout(() => {
            document.getElementById('currentCapital').classList.remove('pulse');
        }, 500);
        
    } catch (error) {
        console.error('Erreur lors de la simulation avec stratégie:', error);
        outcomeEl.innerHTML = `<div style="color: #e74c3c;">❌ Erreur lors de la simulation: ${error.message}</div>`;
    } finally {
        // Réactiver tous les boutons
        allButtons.forEach(btn => btn.disabled = false);
    }
}

// Exécuter un trade
async function executeTrade(riskPercent, silent = false) {
    try {
        const response = await fetch('/api/execute-trade/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                risk_percent: riskPercent
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            lastTradeData = data.trade;
            
            // Mettre à jour les statistiques
            updateStats(data.stats);
            
            // Mettre à jour le graphique
            updateChart(data.history);
            
            // Vérifier si le compte a crashé (capital < 1€)
            if (data.stats.current_capital < 1) {
                const outcomeEl = document.getElementById('outcomeMessage');
                outcomeEl.innerHTML = `<div style="color: #e74c3c; font-size: 1.2rem; font-weight: bold;">💀 GAME OVER! Votre compte a crashé (capital < 1€)!</div>`;
                // Désactiver tous les boutons
                document.querySelectorAll('.risk-btn').forEach(btn => btn.disabled = true);
            } else if (!silent) {
                // Afficher le résultat du trade seulement si ce n'est pas un trade silencieux
                displayTradeOutcome(data.trade, riskPercent);
            }
            
            // Animation sur le capital
            document.getElementById('currentCapital').classList.add('pulse');
            setTimeout(() => {
                document.getElementById('currentCapital').classList.remove('pulse');
            }, 500);
        }
    } catch (error) {
        console.error('Erreur lors de l\'exécution du trade:', error);
        if (!silent) {
            alert('Erreur lors de l\'exécution du trade');
        }
        throw error; // Propager l'erreur pour executeMultipleTrades
    }
}

// Charger les statistiques
async function loadStats() {
    try {
        const response = await fetch('/api/get-stats/');
        const data = await response.json();
        
        if (data.success && data.stats.total_trades > 0) {
            isSessionStarted = true;
            updateStats(data.stats);
            updateChart(data.history);
            document.getElementById('initialSetup').classList.add('hidden');
        }
    } catch (error) {
        console.error('Erreur lors du chargement des stats:', error);
    }
}

// Mettre à jour les statistiques affichées
function updateStats(stats) {
    // Stats principales
    document.getElementById('currentCapital').textContent = 
        `€${stats.current_capital.toFixed(2)}`;
    
    const drawdownEl = document.getElementById('drawdown');
    drawdownEl.textContent = `${stats.drawdown.toFixed(2)}%`;
    drawdownEl.className = `stat-value ${stats.drawdown < 0 ? 'negative' : ''}`;
    
    const performanceEl = document.getElementById('performance');
    performanceEl.textContent = `${stats.performance.toFixed(2)}%`;
    performanceEl.className = `stat-value ${stats.performance > 0 ? 'positive' : stats.performance < 0 ? 'negative' : ''}`;
    
    document.getElementById('numTrades').textContent = stats.total_trades;
    
    // Stats détaillées - afficher les moyennes et maximums
    // Risk (%) : moyenne
    document.getElementById('lastRisk').textContent = 
        `${stats.avg_risk_percent ? stats.avg_risk_percent.toFixed(2) : 0}%`;
    
    // Risk ($) : moyenne
    document.getElementById('lastRiskAmount').textContent = 
        `€${stats.avg_risk_amount ? stats.avg_risk_amount.toFixed(2) : 0}`;
    
    // Profit or Loss : moyenne
    const profitLossEl = document.getElementById('lastProfitLoss');
    profitLossEl.textContent = `€${stats.avg_profit_loss ? stats.avg_profit_loss.toFixed(2) : 0}`;
    profitLossEl.className = `stat-value ${stats.avg_profit_loss > 0 ? 'positive' : stats.avg_profit_loss < 0 ? 'negative' : ''}`;
    
    // Consecutive Wins : maximum
    document.getElementById('consecutiveWins').textContent = stats.max_consecutive_wins || 0;
    
    // Consecutive Losses : maximum
    document.getElementById('consecutiveLosses').textContent = stats.max_consecutive_losses || 0;
    
    // Success Rate : ok (pourcentage global)
    document.getElementById('successRate').textContent = `${stats.success_rate.toFixed(2)}%`;
    
    document.getElementById('maxCapital').textContent = `€${stats.max_capital.toFixed(2)}`;
    document.getElementById('maxDrawdown').textContent = `${stats.max_drawdown.toFixed(2)}%`;
    document.getElementById('maxPerf').textContent = `${stats.max_performance.toFixed(2)}%`;
    
    // Mettre à jour la distribution des issues
    updateOutcomeDistribution(stats.outcome_distribution || {}, stats.total_trades);
}

// Mettre à jour la distribution des issues
function updateOutcomeDistribution(distribution, totalTrades) {
    // Réinitialiser tous les compteurs
    document.getElementById('outcome-1').textContent = distribution[-1] || 0;
    document.getElementById('outcome-2').textContent = distribution[-2] || 0;
    document.getElementById('outcome-5').textContent = distribution[-5] || 0;
    document.getElementById('outcome2').textContent = distribution[2] || 0;
    document.getElementById('outcome3').textContent = distribution[3] || 0;
    document.getElementById('outcome4').textContent = distribution[4] || 0;
    document.getElementById('outcome5').textContent = distribution[5] || 0;
    document.getElementById('outcome9').textContent = distribution[9] || 0;
    
    // Afficher les pourcentages réels si on a des trades
    if (totalTrades > 0) {
        const updateWithPercentage = (elementId, count) => {
            const el = document.getElementById(elementId);
            const percentage = ((count / totalTrades) * 100).toFixed(1);
            el.textContent = `${count} (${percentage}%)`;
        };
        
        updateWithPercentage('outcome-1', distribution[-1] || 0);
        updateWithPercentage('outcome-2', distribution[-2] || 0);
        updateWithPercentage('outcome-5', distribution[-5] || 0);
        updateWithPercentage('outcome2', distribution[2] || 0);
        updateWithPercentage('outcome3', distribution[3] || 0);
        updateWithPercentage('outcome4', distribution[4] || 0);
        updateWithPercentage('outcome5', distribution[5] || 0);
        updateWithPercentage('outcome9', distribution[9] || 0);
    }
}

// Afficher le résultat du trade
function displayTradeOutcome(trade, riskPercent) {
    const messages = trade.is_win ? winMessages : lossMessages;
    const randomMessage = messages[Math.floor(Math.random() * messages.length)];
    
    const outcomeEl = document.getElementById('outcomeMessage');
    outcomeEl.textContent = randomMessage;
    outcomeEl.style.color = trade.is_win ? '#4CAF50' : '#e74c3c';
}

// Initialiser le graphique
function initializeChart() {
    const ctx = document.getElementById('equityChart').getContext('2d');
    equityChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [0],
            datasets: [{
                label: 'Capital',
                data: [1000],
                borderColor: '#4CAF50',
                backgroundColor: 'rgba(76, 175, 80, 0.1)',
                borderWidth: 2,
                fill: true,
                tension: 0.4,
                pointRadius: 2,
                pointHoverRadius: 5
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    titleColor: '#fff',
                    bodyColor: '#fff',
                    borderColor: '#4CAF50',
                    borderWidth: 1
                }
            },
            scales: {
                x: {
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    },
                    ticks: {
                        color: '#888'
                    }
                },
                y: {
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    },
                    ticks: {
                        color: '#888',
                        callback: function(value) {
                            return '€' + value.toFixed(0);
                        }
                    }
                }
            },
            interaction: {
                mode: 'nearest',
                axis: 'x',
                intersect: false
            }
        }
    });
}

// Mettre à jour le graphique equity curve
function updateChart(history) {
    if (!history || history.length === 0) {
        return;
    }
    
    // Labels: numéro de trade
    const labels = history.map(t => t.trade_number);
    
    // Data: capital après chaque trade
    const data = history.map(t => t.capital_after);
    
    equityChart.data.labels = labels;
    equityChart.data.datasets[0].data = data;
    equityChart.update();
    
    // Mettre à jour aussi le graphique du risque adaptatif
    updateRiskChart(history);
}

// Initialiser le graphique du risque adaptatif
function initializeRiskChart() {
    const ctx = document.getElementById('riskChart').getContext('2d');
    riskChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [0],
            datasets: [
                {
                    label: 'Risque (%)',
                    data: [0],
                    borderColor: '#667eea',
                    backgroundColor: 'rgba(102, 126, 234, 0.1)',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4,
                    pointRadius: 0,
                    pointHoverRadius: 5,
                    yAxisID: 'y'
                },
                {
                    label: 'Drawdown (%)',
                    data: [0],
                    borderColor: '#e74c3c',
                    backgroundColor: 'rgba(231, 76, 60, 0.05)',
                    borderWidth: 2,
                    borderDash: [5, 5],
                    fill: false,
                    tension: 0.4,
                    pointRadius: 0,
                    pointHoverRadius: 4,
                    yAxisID: 'y1'
                },
                {
                    label: 'Pertes Consécutives',
                    data: [0],
                    borderColor: '#f39c12',
                    backgroundColor: 'rgba(243, 156, 18, 0.05)',
                    borderWidth: 2,
                    borderDash: [2, 2],
                    fill: false,
                    tension: 0.1,
                    pointRadius: 0,
                    pointHoverRadius: 4,
                    yAxisID: 'y2'
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: true,
                    position: 'top',
                    labels: {
                        color: '#fff',
                        font: {
                            size: 11
                        },
                        usePointStyle: true,
                        padding: 15
                    }
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    titleColor: '#fff',
                    bodyColor: '#fff',
                    borderColor: '#667eea',
                    borderWidth: 1,
                    callbacks: {
                        label: function(context) {
                            let label = context.dataset.label || '';
                            if (label) {
                                label += ': ';
                            }
                            if (context.parsed.y !== null) {
                                if (context.datasetIndex === 2) {
                                    // Pertes consécutives (nombre entier)
                                    label += Math.round(context.parsed.y);
                                } else {
                                    // Risque et drawdown (pourcentage)
                                    label += context.parsed.y.toFixed(2) + '%';
                                }
                            }
                            return label;
                        }
                    }
                }
            },
            scales: {
                x: {
                    title: {
                        display: true,
                        text: 'Numéro de Trade',
                        color: '#888'
                    },
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    },
                    ticks: {
                        color: '#888'
                    }
                },
                y: {
                    type: 'linear',
                    display: true,
                    position: 'left',
                    title: {
                        display: true,
                        text: 'Risque (% du capital)',
                        color: '#667eea'
                    },
                    grid: {
                        color: 'rgba(102, 126, 234, 0.2)'
                    },
                    ticks: {
                        color: '#667eea',
                        callback: function(value) {
                            return value.toFixed(1) + '%';
                        }
                    }
                },
                y1: {
                    type: 'linear',
                    display: true,
                    position: 'right',
                    // Pas de reverse: les valeurs négatives doivent descendre
                    title: {
                        display: true,
                        text: 'Drawdown (%)',
                        color: '#e74c3c'
                    },
                    grid: {
                        drawOnChartArea: false
                    },
                    ticks: {
                        color: '#e74c3c',
                        callback: function(value) {
                            return value.toFixed(1) + '%';
                        }
                    }
                },
                y2: {
                    type: 'linear',
                    display: true,
                    position: 'right',
                    title: {
                        display: true,
                        text: 'Pertes Consécutives',
                        color: '#f39c12'
                    },
                    grid: {
                        drawOnChartArea: false
                    },
                    ticks: {
                        color: '#f39c12',
                        stepSize: 1,
                        callback: function(value) {
                            return Math.round(value);
                        }
                    }
                }
            },
            interaction: {
                mode: 'nearest',
                axis: 'x',
                intersect: false
            }
        }
    });
}

// Mettre à jour le graphique du risque adaptatif
function updateRiskChart(history) {
    if (!history || history.length === 0) {
        return;
    }
    
    const labels = [];
    const riskData = [];
    const drawdownData = [];
    const consecutiveLossesData = [];
    
    // Peak = le plus-haut historique atteint jusqu'à présent
    let peak = 0;
    let consecutiveLosses = 0;
    
    // DEBUG: Afficher les 5 premiers trades pour vérifier
    console.log('=== DEBUG DRAWDOWN ===');
    console.log('Premier trade:', history[0]);
    console.log('Nombre total de trades:', history.length);
    
    // Parcourir l'historique pour construire les données
    history.forEach((trade, index) => {
        labels.push(trade.trade_number);
        riskData.push(parseFloat(trade.risk_percent));
        
        // Le capital après ce trade (conversion en nombre car Django renvoie des strings)
        const currentCapital = parseFloat(trade.capital_after);
        
        // Au premier trade, initialiser le peak
        if (index === 0) {
            peak = currentCapital;
            console.log(`Trade ${index + 1}: Capital=${currentCapital}, Peak initialisé=${peak}`);
        }
        
        // Mettre à jour le peak si on atteint un nouveau sommet
        // Peak_t = max(Peak_{t-1}, C_t)
        const oldPeak = peak;
        if (currentCapital > peak) {
            peak = currentCapital;
        }
        
        // ✅ FORMULE CORRECTE DU DRAWDOWN ACTUEL :
        // DD_t = (C_t - Peak_t) / Peak_t
        // 
        // Si C_t = Peak_t (nouveau plus haut) → DD = 0%
        // Si C_t < Peak_t (en dessous du peak) → DD < 0% (négatif)
        const drawdown = ((currentCapital - peak) / peak) * 100;
        drawdownData.push(drawdown);
        
        // Debug pour les 5 premiers et derniers trades
        if (index < 5 || index >= history.length - 5) {
            console.log(`Trade ${index + 1}: Capital=${currentCapital.toFixed(2)}, Peak=${peak.toFixed(2)}, DD=${drawdown.toFixed(2)}%`);
        }
        
        // Calculer les pertes consécutives (basé sur la variation du capital)
        if (index > 0) {
            const previousCapital = history[index - 1].capital_after;
            if (currentCapital < previousCapital) {
                consecutiveLosses++;
            } else {
                consecutiveLosses = 0;
            }
        }
        consecutiveLossesData.push(consecutiveLosses);
    });
    
    console.log('Peak final:', peak);
    console.log('Drawdown min:', Math.min(...drawdownData).toFixed(2) + '%');
    console.log('Drawdown max:', Math.max(...drawdownData).toFixed(2) + '%');
    console.log('======================');
    
    // Mettre à jour le graphique
    riskChart.data.labels = labels;
    riskChart.data.datasets[0].data = riskData;
    riskChart.data.datasets[1].data = drawdownData;
    riskChart.data.datasets[2].data = consecutiveLossesData;
    riskChart.update();
}
