// JavaScript functionality for Binance Trading Bot Frontend

class TradingBotUI {
    constructor() {
        this.isConnected = false;
        this.currentSymbol = 'BTCUSDT';
        this.currentSide = 'BUY';
        this.activeOrders = [];
        this.orderHistory = [];
        
        this.initializeUI();
        this.bindEvents();
        this.startPriceUpdates();
    }

    initializeUI() {
        // Initialize tabs
        this.showTab('basic');
        this.showOrdersTab('active');
        
        // Set default form values
        document.getElementById('symbol-selector').value = this.currentSymbol;
        
        // Update connection status
        this.updateConnectionStatus();
        
        // Initialize side buttons
        this.updateSideButtons();
    }

    bindEvents() {
        // Tab switching
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.showTab(e.target.dataset.tab);
            });
        });

        // Orders tab switching
        document.querySelectorAll('.orders-tab-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.showOrdersTab(e.target.dataset.tab);
            });
        });

        // Side button switching
        document.querySelectorAll('.side-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const form = e.target.closest('.tab-content');
                form.querySelectorAll('.side-btn').forEach(b => b.classList.remove('active'));
                e.target.classList.add('active');
                this.currentSide = e.target.dataset.side;
            });
        });

        // Symbol selector
        document.getElementById('symbol-selector').addEventListener('change', (e) => {
            this.currentSymbol = e.target.value;
            this.updatePrice();
        });

        // Connection modal
        document.getElementById('connect-btn').addEventListener('click', () => {
            this.showConnectionModal();
        });

        document.getElementById('modal-close').addEventListener('click', () => {
            this.hideConnectionModal();
        });

        document.getElementById('cancel-connection').addEventListener('click', () => {
            this.hideConnectionModal();
        });

        // Connection form
        document.getElementById('connection-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleConnection();
        });

        // Order forms
        document.getElementById('basic-order-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleBasicOrder();
        });

        document.getElementById('stop-limit-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleStopLimitOrder();
        });

        document.getElementById('oco-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleOCOOrder();
        });

        document.getElementById('twap-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleTWAPOrder();
        });

        document.getElementById('grid-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleGridOrder();
        });

        // Order type change
        document.getElementById('basic-order-type').addEventListener('change', (e) => {
            const limitPriceGroup = document.querySelector('.limit-price-group');
            if (e.target.value === 'market') {
                limitPriceGroup.style.display = 'none';
            } else {
                limitPriceGroup.style.display = 'block';
            }
        });

        // Refresh orders
        document.getElementById('refresh-orders').addEventListener('click', () => {
            this.refreshOrders();
        });
    }

    showTab(tabName) {
        // Hide all tabs
        document.querySelectorAll('.tab-content').forEach(tab => {
            tab.classList.remove('active');
        });
        
        // Show selected tab
        document.getElementById(`${tabName}-tab`).classList.add('active');
        
        // Update tab buttons
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
    }

    showOrdersTab(tabName) {
        document.querySelectorAll('.orders-tab-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
        
        if (tabName === 'active') {
            this.displayActiveOrders();
        } else {
            this.displayOrderHistory();
        }
    }

    showConnectionModal() {
        document.getElementById('connection-modal').classList.add('active');
    }

    hideConnectionModal() {
        document.getElementById('connection-modal').classList.remove('active');
    }

    async handleConnection() {
        const apiKey = document.getElementById('api-key').value;
        const apiSecret = document.getElementById('api-secret').value;
        const testnet = document.getElementById('testnet').checked;

        if (!apiKey || !apiSecret) {
            this.showNotification('Please enter both API Key and Secret', 'error');
            return;
        }

        try {
            // Show loading state
            document.getElementById('connection-form').classList.add('loading');

            // Simulate API connection (replace with actual API call)
            await this.simulateAPICall(2000);

            this.isConnected = true;
            this.updateConnectionStatus();
            this.hideConnectionModal();
            this.showNotification('Successfully connected to Binance!', 'success');
            
            // Update balance and orders
            this.updateBalance();
            this.refreshOrders();

        } catch (error) {
            this.showNotification('Connection failed. Please check your credentials.', 'error');
        } finally {
            document.getElementById('connection-form').classList.remove('loading');
        }
    }

    updateConnectionStatus() {
        const statusDot = document.querySelector('.status-dot');
        const statusText = statusDot.nextElementSibling;
        const connectBtn = document.getElementById('connect-btn');

        if (this.isConnected) {
            statusDot.className = 'status-dot online';
            statusText.textContent = 'Connected';
            connectBtn.innerHTML = '<i class="fas fa-sign-out-alt"></i> Disconnect';
            connectBtn.onclick = () => this.disconnect();
        } else {
            statusDot.className = 'status-dot offline';
            statusText.textContent = 'Disconnected';
            connectBtn.innerHTML = '<i class="fas fa-plug"></i> Connect';
            connectBtn.onclick = () => this.showConnectionModal();
        }
    }

    disconnect() {
        this.isConnected = false;
        this.updateConnectionStatus();
        this.showNotification('Disconnected from Binance', 'info');
        
        // Reset UI state
        this.updateBalance(true);
        this.activeOrders = [];
        this.displayActiveOrders();
    }

    async handleBasicOrder() {
        if (!this.isConnected) {
            this.showNotification('Please connect to Binance first', 'error');
            return;
        }

        const form = document.getElementById('basic-order-form');
        const orderType = document.getElementById('basic-order-type').value;
        const quantity = document.getElementById('basic-quantity').value;
        const price = document.getElementById('basic-price').value;
        const side = document.querySelector('#basic-tab .side-btn.active').dataset.side;

        if (!quantity || (orderType === 'limit' && !price)) {
            this.showNotification('Please fill in all required fields', 'error');
            return;
        }

        try {
            form.classList.add('loading');

            // Simulate order placement
            await this.simulateAPICall(1000);

            const order = {
                id: Date.now(),
                symbol: this.currentSymbol,
                type: orderType,
                side: side,
                quantity: parseFloat(quantity),
                price: orderType === 'limit' ? parseFloat(price) : null,
                status: 'ACTIVE',
                time: new Date().toLocaleTimeString()
            };

            this.activeOrders.push(order);
            this.displayActiveOrders();
            this.updateActiveOrdersCount();

            this.showNotification(`${orderType.toUpperCase()} order placed successfully!`, 'success');
            form.reset();

        } catch (error) {
            this.showNotification('Failed to place order', 'error');
        } finally {
            form.classList.remove('loading');
        }
    }

    async handleStopLimitOrder() {
        if (!this.isConnected) {
            this.showNotification('Please connect to Binance first', 'error');
            return;
        }

        const form = document.getElementById('stop-limit-form');
        const quantity = document.getElementById('stop-limit-quantity').value;
        const stopPrice = document.getElementById('stop-price').value;
        const limitPrice = document.getElementById('limit-price').value;
        const side = document.querySelector('#stop-limit-tab .side-btn.active').dataset.side;

        if (!quantity || !stopPrice || !limitPrice) {
            this.showNotification('Please fill in all required fields', 'error');
            return;
        }

        try {
            form.classList.add('loading');
            await this.simulateAPICall(1500);

            const order = {
                id: Date.now(),
                symbol: this.currentSymbol,
                type: 'stop-limit',
                side: side,
                quantity: parseFloat(quantity),
                stopPrice: parseFloat(stopPrice),
                limitPrice: parseFloat(limitPrice),
                status: 'MONITORING',
                time: new Date().toLocaleTimeString()
            };

            this.activeOrders.push(order);
            this.displayActiveOrders();
            this.updateActiveOrdersCount();

            this.showNotification('Stop-Limit order created successfully!', 'success');
            form.reset();

        } catch (error) {
            this.showNotification('Failed to create stop-limit order', 'error');
        } finally {
            form.classList.remove('loading');
        }
    }

    async handleOCOOrder() {
        if (!this.isConnected) {
            this.showNotification('Please connect to Binance first', 'error');
            return;
        }

        const form = document.getElementById('oco-form');
        const quantity = document.getElementById('oco-quantity').value;
        const takeProfitPrice = document.getElementById('take-profit-price').value;
        const stopLossPrice = document.getElementById('stop-loss-price').value;
        const side = document.querySelector('#oco-tab .side-btn.active').dataset.side;

        if (!quantity || !takeProfitPrice || !stopLossPrice) {
            this.showNotification('Please fill in all required fields', 'error');
            return;
        }

        try {
            form.classList.add('loading');
            await this.simulateAPICall(1500);

            const order = {
                id: Date.now(),
                symbol: this.currentSymbol,
                type: 'oco',
                side: side,
                quantity: parseFloat(quantity),
                takeProfitPrice: parseFloat(takeProfitPrice),
                stopLossPrice: parseFloat(stopLossPrice),
                status: 'ACTIVE',
                time: new Date().toLocaleTimeString()
            };

            this.activeOrders.push(order);
            this.displayActiveOrders();
            this.updateActiveOrdersCount();

            this.showNotification('OCO order created successfully!', 'success');
            form.reset();

        } catch (error) {
            this.showNotification('Failed to create OCO order', 'error');
        } finally {
            form.classList.remove('loading');
        }
    }

    async handleTWAPOrder() {
        if (!this.isConnected) {
            this.showNotification('Please connect to Binance first', 'error');
            return;
        }

        const form = document.getElementById('twap-form');
        const quantity = document.getElementById('twap-quantity').value;
        const duration = document.getElementById('twap-duration').value;
        const interval = document.getElementById('twap-interval').value;
        const useMarketOrders = document.getElementById('use-market-orders').checked;
        const side = document.querySelector('#twap-tab .side-btn.active').dataset.side;

        if (!quantity || !duration || !interval) {
            this.showNotification('Please fill in all required fields', 'error');
            return;
        }

        if (parseInt(interval) > parseInt(duration)) {
            this.showNotification('Interval cannot be greater than duration', 'error');
            return;
        }

        try {
            form.classList.add('loading');
            await this.simulateAPICall(2000);

            const order = {
                id: Date.now(),
                symbol: this.currentSymbol,
                type: 'twap',
                side: side,
                totalQuantity: parseFloat(quantity),
                duration: parseInt(duration),
                interval: parseInt(interval),
                useMarketOrders: useMarketOrders,
                status: 'EXECUTING',
                time: new Date().toLocaleTimeString()
            };

            this.activeOrders.push(order);
            this.displayActiveOrders();
            this.updateActiveOrdersCount();

            this.showNotification('TWAP order started successfully!', 'success');
            form.reset();

        } catch (error) {
            this.showNotification('Failed to start TWAP order', 'error');
        } finally {
            form.classList.remove('loading');
        }
    }

    async handleGridOrder() {
        if (!this.isConnected) {
            this.showNotification('Please connect to Binance first', 'error');
            return;
        }

        const form = document.getElementById('grid-form');
        const quantity = document.getElementById('grid-quantity').value;
        const minPrice = document.getElementById('grid-min-price').value;
        const maxPrice = document.getElementById('grid-max-price').value;
        const stepSize = document.getElementById('grid-step-size').value;
        const rebalance = document.getElementById('grid-rebalance').checked;
        const side = document.querySelector('#grid-tab .side-btn.active').dataset.side;

        if (!quantity || !minPrice || !maxPrice || !stepSize) {
            this.showNotification('Please fill in all required fields', 'error');
            return;
        }

        if (parseFloat(maxPrice) <= parseFloat(minPrice)) {
            this.showNotification('Max price must be greater than min price', 'error');
            return;
        }

        try {
            form.classList.add('loading');
            await this.simulateAPICall(2500);

            const order = {
                id: Date.now(),
                symbol: this.currentSymbol,
                type: 'grid',
                side: side,
                quantityPerOrder: parseFloat(quantity),
                minPrice: parseFloat(minPrice),
                maxPrice: parseFloat(maxPrice),
                stepSize: parseFloat(stepSize),
                rebalance: rebalance,
                status: 'ACTIVE',
                time: new Date().toLocaleTimeString()
            };

            this.activeOrders.push(order);
            this.displayActiveOrders();
            this.updateActiveOrdersCount();

            this.showNotification('Grid trading started successfully!', 'success');
            form.reset();

        } catch (error) {
            this.showNotification('Failed to start grid trading', 'error');
        } finally {
            form.classList.remove('loading');
        }
    }

    displayActiveOrders() {
        const tbody = document.getElementById('orders-tbody');
        const noOrders = document.getElementById('no-orders');

        if (this.activeOrders.length === 0) {
            tbody.innerHTML = '';
            noOrders.style.display = 'block';
            return;
        }

        noOrders.style.display = 'none';
        tbody.innerHTML = this.activeOrders.map(order => {
            let priceDisplay = '';
            if (order.type === 'market') {
                priceDisplay = 'Market';
            } else if (order.type === 'limit') {
                priceDisplay = `$${order.price.toFixed(2)}`;
            } else if (order.type === 'stop-limit') {
                priceDisplay = `Stop: $${order.stopPrice.toFixed(2)} / Limit: $${order.limitPrice.toFixed(2)}`;
            } else if (order.type === 'oco') {
                priceDisplay = `TP: $${order.takeProfitPrice.toFixed(2)} / SL: $${order.stopLossPrice.toFixed(2)}`;
            } else if (order.type === 'twap') {
                priceDisplay = `${order.duration}m / ${order.interval}m`;
            } else if (order.type === 'grid') {
                priceDisplay = `$${order.minPrice.toFixed(2)} - $${order.maxPrice.toFixed(2)}`;
            }

            return `
                <tr>
                    <td>${order.time}</td>
                    <td>${order.symbol}</td>
                    <td><span class="status-badge">${order.type.toUpperCase()}</span></td>
                    <td><span class="side-${order.side.toLowerCase()}">${order.side}</span></td>
                    <td>${order.quantity || order.totalQuantity || order.quantityPerOrder}</td>
                    <td>${priceDisplay}</td>
                    <td><span class="status-badge ${order.status.toLowerCase()}">${order.status}</span></td>
                    <td>
                        <button class="btn btn-secondary" onclick="tradingBot.cancelOrder(${order.id})">
                            <i class="fas fa-times"></i>
                        </button>
                    </td>
                </tr>
            `;
        }).join('');
    }

    displayOrderHistory() {
        const tbody = document.getElementById('orders-tbody');
        const noOrders = document.getElementById('no-orders');

        if (this.orderHistory.length === 0) {
            tbody.innerHTML = '';
            noOrders.style.display = 'block';
            noOrders.querySelector('p').textContent = 'No order history';
            return;
        }

        noOrders.style.display = 'none';
        // Implementation for order history display
        tbody.innerHTML = '<tr><td colspan="8" style="text-align: center; padding: 40px;">Order history will be displayed here</td></tr>';
    }

    async cancelOrder(orderId) {
        if (!confirm('Are you sure you want to cancel this order?')) {
            return;
        }

        try {
            await this.simulateAPICall(500);
            
            const orderIndex = this.activeOrders.findIndex(order => order.id === orderId);
            if (orderIndex > -1) {
                const cancelledOrder = this.activeOrders.splice(orderIndex, 1)[0];
                cancelledOrder.status = 'CANCELLED';
                this.orderHistory.push(cancelledOrder);
                
                this.displayActiveOrders();
                this.updateActiveOrdersCount();
                this.showNotification('Order cancelled successfully', 'info');
            }
        } catch (error) {
            this.showNotification('Failed to cancel order', 'error');
        }
    }

    refreshOrders() {
        if (!this.isConnected) {
            this.showNotification('Please connect to Binance first', 'error');
            return;
        }

        // Simulate refreshing orders
        this.showNotification('Orders refreshed', 'info');
        this.displayActiveOrders();
    }

    updateActiveOrdersCount() {
        document.getElementById('active-orders-count').textContent = this.activeOrders.length;
    }

    updateBalance(reset = false) {
        if (reset) {
            document.getElementById('usdt-balance').textContent = '0.00';
            document.getElementById('btc-balance').textContent = '0.00000000';
            return;
        }

        if (this.isConnected) {
            // Simulate balance updates
            document.getElementById('usdt-balance').textContent = '10,000.00';
            document.getElementById('btc-balance').textContent = '0.38547621';
        }
    }

    startPriceUpdates() {
        this.updatePrice();
        setInterval(() => {
            if (this.isConnected) {
                this.updatePrice();
            }
        }, 5000);
    }

    updatePrice() {
        // Simulate price updates
        const basePrice = this.getBasePrice(this.currentSymbol);
        const variation = (Math.random() - 0.5) * 0.02; // ±1% variation
        const currentPrice = basePrice * (1 + variation);
        const change = (variation * 100).toFixed(2);

        document.getElementById('current-price').textContent = `$${currentPrice.toFixed(2)}`;
        
        const changeElement = document.getElementById('price-change');
        changeElement.textContent = `${change >= 0 ? '+' : ''}${change}%`;
        changeElement.className = `price-change ${change >= 0 ? 'positive' : 'negative'}`;
    }

    getBasePrice(symbol) {
        const prices = {
            'BTCUSDT': 43000,
            'ETHUSDT': 2600,
            'BNBUSDT': 250,
            'ADAUSDT': 0.5
        };
        return prices[symbol] || 100;
    }

    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.innerHTML = `
            <div style="display: flex; align-items: center; gap: 10px;">
                <i class="fas fa-${this.getNotificationIcon(type)}"></i>
                <span>${message}</span>
            </div>
        `;

        document.getElementById('notifications').appendChild(notification);

        // Auto remove after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 5000);
    }

    getNotificationIcon(type) {
        const icons = {
            'success': 'check-circle',
            'error': 'exclamation-circle',
            'info': 'info-circle'
        };
        return icons[type] || 'info-circle';
    }

    simulateAPICall(delay) {
        return new Promise((resolve, reject) => {
            setTimeout(() => {
                // Simulate 95% success rate
                if (Math.random() < 0.95) {
                    resolve();
                } else {
                    reject(new Error('API Error'));
                }
            }, delay);
        });
    }

    updateSideButtons() {
        // Set default active side button for each form
        document.querySelectorAll('.side-btn[data-side="BUY"]').forEach(btn => {
            btn.classList.add('active');
        });
        
        document.querySelectorAll('.side-btn[data-side="SELL"]').forEach(btn => {
            btn.classList.remove('active');
        });
    }
}

// Initialize the trading bot UI when the page loads
let tradingBot;
document.addEventListener('DOMContentLoaded', function() {
    tradingBot = new TradingBotUI();
});
