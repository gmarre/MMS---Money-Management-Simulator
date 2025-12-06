// Configuration globale
let equityChart = null;
let isSessionStarted = false;
let lastTradeData = null;
let presetsData = {};
let selectedPreset = 'balanced';

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
    setupEventListeners();
    loadPresets();
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
    document.querySelectorAll('.x1000-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            if (isSessionStarted) {
                const riskPercent = parseFloat(this.dataset.risk);
                const multiplier = parseInt(this.dataset.multiplier);
                executeMultipleTrades(riskPercent, multiplier);
            }
        });
    });
    
    // Bouton restart
    document.getElementById('restartBtn').addEventListener('click', showInitialSetup);
    
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
    
    // Stats détaillées
    if (lastTradeData) {
        document.getElementById('lastRisk').textContent = 
            `${lastTradeData.risk_amount > 0 ? (lastTradeData.risk_amount / stats.current_capital * 100).toFixed(2) : 0}%`;
        
        document.getElementById('lastRiskAmount').textContent = 
            `€${lastTradeData.risk_amount.toFixed(2)}`;
        
        const profitLossEl = document.getElementById('lastProfitLoss');
        profitLossEl.textContent = `€${lastTradeData.profit_loss.toFixed(2)}`;
        profitLossEl.className = `stat-value ${lastTradeData.is_win ? 'positive' : 'negative'}`;
    }
    
    document.getElementById('consecutiveWins').textContent = stats.consecutive_wins;
    document.getElementById('consecutiveLosses').textContent = stats.consecutive_losses;
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

// Mettre à jour le graphique
function updateChart(history) {
    if (!history || history.length === 0) {
        return;
    }
    
    const labels = [0, ...history.map(t => t.trade_number)];
    const data = [history[0]?.capital_after || 1000];
    
    history.forEach(trade => {
        data.push(trade.capital_after);
    });
    
    equityChart.data.labels = labels;
    equityChart.data.datasets[0].data = data;
    equityChart.update();
}
