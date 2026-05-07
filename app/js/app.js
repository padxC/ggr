// ============================================
// UI MANAGER
// ============================================
class UI {
    constructor() {
        this.elements = {
            connectionStatus: document.getElementById('connectionStatus'),
            statusIndicator: document.getElementById('statusIndicator'),
            activeNode: document.getElementById('activeNode'),
            activePing: document.getElementById('activePing'),
            currentSpeed: document.getElementById('currentSpeed'),
            wsDot: document.getElementById('wsDot'),
            wsText: document.getElementById('wsText')
        };
    }

    updateVPNStatus(connected, server = null) {
        const { connectionStatus, statusIndicator } = this.elements;
        
        if (connected) {
            if (connectionStatus) {
                connectionStatus.textContent = 'Connected';
                connectionStatus.style.color = '#10b981';
            }
            if (statusIndicator) statusIndicator.className = 'status-indicator connected';
        } else {
            if (connectionStatus) {
                connectionStatus.textContent = 'Disconnected';
                connectionStatus.style.color = '#9ca3af';
            }
            if (statusIndicator) statusIndicator.className = 'status-indicator disconnected';
        }
        
        if (server && server !== 'undefined') {
            const nodeId = server.split(':')[0];
            if (this.elements.activeNode) this.elements.activeNode.textContent = nodeId;
        }
    }

    updateWebSocketStatus(connected) {
        const { wsDot, wsText } = this.elements;
        
        if (connected) {
            if (wsDot) wsDot.className = 'ws-dot connected';
            if (wsText) wsText.textContent = 'Connected';
        } else {
            if (wsDot) wsDot.className = 'ws-dot disconnected';
            if (wsText) wsText.textContent = 'Disconnected';
        }
    }

    updateServerDetails(server, stats) {
        if (this.elements.activeNode) {
            this.elements.activeNode.textContent = stats.nodeId;
        }
        if (this.elements.activePing) {
            this.elements.activePing.textContent = `${stats.ping} ms`;
        }
        if (this.elements.currentSpeed) {
            this.elements.currentSpeed.textContent = stats.speed > 0 ? stats.speed.toFixed(1) : 'N/A';
        }
    }
}

// ============================================
// ACTIVITY LOG MANAGER
// ============================================
class Activity {
    constructor(containerId, maxEntries = 100) {
        this.container = document.getElementById(containerId);
        this.maxEntries = maxEntries;
        this.entries = [];
    }

    add(message, type = 'info') {
        const timestamp = new Date().toLocaleTimeString();
        const entry = {
            timestamp,
            message,
            type,
            element: this.createLogEntry(timestamp, message, type)
        };
        
        this.entries.push(entry);
        this.container.appendChild(entry.element);
        entry.element.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        
        // Trim old entries
        while (this.entries.length > this.maxEntries) {
            const oldEntry = this.entries.shift();
            if (oldEntry.element && oldEntry.element.remove) {
                oldEntry.element.remove();
            }
        }
    }

    createLogEntry(timestamp, message, type) {
        const p = document.createElement('p');
        const colorClass = type === 'error' ? 'timestamp accent' : 
                          type === 'success' ? 'timestamp success' : 'timestamp';
        p.innerHTML = `<span class="${colorClass}">[${timestamp}]</span> ${message}`;
        return p;
    }

    clear() {
        this.container.innerHTML = '';
        this.entries = [];
    }
}

// ============================================
// SERVER TABLE MANAGER
// ============================================
class ServerTableManager {
    constructor(tableBodyId, onServerSelect) {
        this.tableBody = document.getElementById(tableBodyId);
        this.servers = [];           // Full server list
        this.filteredServers = [];   // Filtered list
        this.selectedServer = null;
        this.onServerSelect = onServerSelect;
        this.sortField = null;
        this.sortDirection = 'asc';
        this.countryFilter = 'KR';   // Default to Korea
    }

    updateServers(servers) {
        // Store full server list
        this.servers = servers;
        
        // Apply current filter
        this.applyFilter();
    }
    
    setCountryFilter(countryCode) {
        this.countryFilter = countryCode;
        this.applyFilter();
        
        // Update active state on toggle buttons
        const toggles = document.querySelectorAll('.filter-toggle');
        toggles.forEach(toggle => {
            if (toggle.dataset.country === countryCode) {
                toggle.classList.add('active');
            } else {
                toggle.classList.remove('active');
            }
        });
    }
    
    applyFilter() {
        // Filter only for KR or TH
        this.filteredServers = this.servers.filter(
            server => server.countryShort === this.countryFilter
        );
        
        // Re-render with filtered list
        this.render();
    }
    
    render() {
        if (!this.tableBody) return;
        
        this.tableBody.innerHTML = '';
        
        if (!this.filteredServers || this.filteredServers.length === 0) {
            const countryName = this.countryFilter === 'KR' ? 'Korea' : 'Thailand';
            this.tableBody.innerHTML = `<tr><td colspan="5" style="text-align: center;">No servers available for ${countryName}</td></tr>`;
            return;
        }
        
        // Apply sorting if active
        let displayServers = [...this.filteredServers];
        if (this.sortField) {
            displayServers.sort((a, b) => {
                let valA = this.getSortValue(a, this.sortField);
                let valB = this.getSortValue(b, this.sortField);
                return this.sortDirection === 'asc' ? valA - valB : valB - valA;
            });
        }
        
        displayServers.forEach(server => {
            const row = this.createRow(server);
            this.tableBody.appendChild(row);
        });
    }

    getSortValue(server, field) {
        switch(field) {
            case 'ping': return parseInt(server.ping) || 9999;
            case 'speed': return parseFloat(server.speed) || 0;
            case 'score': return this.calculateScore(server);
            default: return 0;
        }
    }

    calculateScore(server) {
        const pingValue = parseInt(server.ping) || 999;
        const speedValue = parseFloat(server.speed) || 0;
        
        if (pingValue < 999 && speedValue > 0) {
            return Math.max(0, Math.min(100, 
                Math.round(((1000 - Math.min(pingValue, 500)) / 10) * (Math.min(speedValue, 100) / 100))
            ));
        } else if (pingValue < 999) {
            return Math.max(0, Math.min(100, Math.round((1000 - Math.min(pingValue, 500)) / 10)));
        }
        return 0;
    }

    createRow(server) {
        const row = document.createElement('tr');
        const isSelected = this.selectedServer && this.selectedServer.hostname === server.hostname;
        
        if (isSelected) {
            row.className = 'selected';
        }
        
        const nodeId = this.getNodeId(server);
        const pingValue = parseInt(server.ping) || 999;
        const speedValue = parseFloat(server.speed) || 0;
        const score = this.calculateScore(server);
        const usersValue = server.totalUsers || 'N/A';
        
        row.appendChild(this.createCell(nodeId, true));
        row.appendChild(this.createCell(score.toString(), true, '#00dbe9'));
        row.appendChild(this.createCell(speedValue > 0 ? speedValue.toFixed(1) + ' mbps' : 'N/A'));
        row.appendChild(this.createCell(`${pingValue} ms`, false, pingValue < 150 ? '#00dbe9' : '#9ca3af'));
        row.appendChild(this.createCell(`${usersValue} users`, true, '#6b7280', '10px'));
        
        row.addEventListener('click', () => {
            if (this.selectedServer?.hostname === server.hostname && window.app?.isConnecting) {
                return;
            }
            
            this.selectedServer = server;
            this.render();
            
            if (this.onServerSelect) {
                this.onServerSelect(server, {
                    nodeId,
                    ping: pingValue,
                    speed: speedValue,
                    score
                });
            }
            
            // Connect ONLY when clicked
            if (window.app) {
                window.app.connectToServer(server);
            }
        });
        
        return row;
    }

    createCell(content, isHtml = false, color = null, fontSize = null) {
        const cell = document.createElement('td');
        if (isHtml) {
            const span = document.createElement('span');
            if (color) span.style.color = color;
            if (fontSize) span.style.fontSize = fontSize;
            span.innerHTML = content;
            cell.appendChild(span);
        } else {
            cell.textContent = content;
            if (color) cell.style.color = color;
            if (fontSize) cell.style.fontSize = fontSize;
        }
        return cell;
    }

    getNodeId(server) {
        return server.hostname.split('.')[0];
    }

    getSelectedServer() {
        return this.selectedServer;
    }

    sortByLatency() {
        if (this.sortField === 'ping' && this.sortDirection === 'asc') {
            this.sortDirection = 'desc';
        } else {
            this.sortField = 'ping';
            this.sortDirection = 'asc';
        }
        this.render();
    }

    resetSort() {
        this.sortField = null;
        this.sortDirection = 'asc';
        this.render();
    }
}

// ============================================
// MAIN APPLICATION
// ============================================
class App {
    constructor() {
        this.ws = null;
        this.repository = null;
        this.ui = null;
        this.activity = null;
        this.serverTable = null;
        this.isConnecting = false;
        
        this.init();
    }

    init() {
        // Setup message handlers
        const messageHandlers = {
            'connected': (data) => {
                // Server confirmed connection, now request data
                this.activity.add(data.message, 'success');
                this.requestInitialData();
            },
            'vpn_status': (data) => this.handleVPNStatus(data),
            'server_list': (data) => this.handleServerList(data),
        };
        
        // Initialize managers
        this.ui = new UI();
        this.activity = new Activity('activityLog');
        
        // Initialize WebSocket
        this.ws = new Ws('ws://localhost:8766', messageHandlers);
        
        // Setup WebSocket event handlers
        this.ws.on('onOpen', () => {
            this.ui.updateWebSocketStatus(true);
            this.activity.add('WebSocket connection established', 'success');
        });
        
        this.ws.on('onClose', () => {
            this.ui.updateWebSocketStatus(false);
            this.activity.add('WebSocket disconnected - Reconnecting...', 'error');
        });
        
        this.ws.on('onError', () => {
            this.activity.add('WebSocket error occurred', 'error');
        });
        
        // Initialize API
        this.repository = new Repository(this.ws);
        
        // Initialize server table
        this.serverTable = new ServerTableManager('serverTableBody', 
            (server, stats) => this.onServerSelected(server, stats)
        );
        
        // Setup event listeners
        this.setupEventListeners();
        
        // Connect
        this.ws.connect();
    }

    setupEventListeners() {
        // Sort button
        const sortBtn = document.getElementById('sortByLatency');
        if (sortBtn) {
            sortBtn.addEventListener('click', () => this.sortServers());
        }
        
        // Refresh button
        const refreshBtn = document.getElementById('refreshServers');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => this.refreshServers());
        }
        
    const filterToggles = document.querySelectorAll('.filter-toggle');
    filterToggles.forEach(toggle => {
        toggle.addEventListener('click', (e) => {
            const country = e.currentTarget.dataset.country;
            this.serverTable.setCountryFilter(country);
            const countryName = country === 'KR' ? 'Korea' : 'Thailand';
            this.activity.add(`Filtered: ${countryName} servers`, 'info');
        });
    });
        
        
        // Disconnect button
        const disconnectBtn = document.getElementById('disconnectBtn');
        if (disconnectBtn) {
            disconnectBtn.addEventListener('click', () => this.disconnectVPN());
        }
        
        // Auto-connect button
        const autoConnectBtn = document.getElementById('autoConnectBtn');
        if (autoConnectBtn) {
            autoConnectBtn.addEventListener('click', () => this.autoConnect());
        }
        
        // Open browser button
        const openBrowserBtn = document.getElementById('openBrowserBtn');
        if (openBrowserBtn) {
            openBrowserBtn.addEventListener('click', () => {
                window.open('https://tr.rhaon.co.kr', '_blank');
            });
        }
    }


    handleVPNStatus(data) {
        this.isConnecting = false;
        this.ui.updateVPNStatus(data.connected, data.server);
        this.activity.add(
            `VPN ${data.connected ? 'connected' : 'disconnected'}`,
            data.connected ? 'success' : 'info'
        );
    }

    handleServerList(data) {
        if (data.servers && data.servers.length > 0) {
            // Convert speed from bps to Mbps when receiving
            const convertedServers = data.servers.map(server => ({
                ...server,
                speed: parseFloat(server.speed) / 1000000  // Convert bps to Mbps
            }));
            
            this.serverTable.updateServers(convertedServers);
            this.activity.add(`Loaded ${convertedServers.length} servers from VPN Gate`, 'success');
        } else {
            this.activity.add('No servers available from VPN Gate', 'error');
        }
    }


    onServerSelected(server, stats) {
        this.ui.updateServerDetails(server, stats);
        this.activity.add(`Selected: ${stats.nodeId} (${stats.ping}ms)`, 'info');
    }

    sortServers() {
        this.serverTable.sortByLatency();
        this.activity.add('Sorted servers by latency', 'info');
    }

    refreshServers() {
        if (this.repository.refreshServers()) {
            this.activity.add('Refreshing server list...', 'info');
        } else {
            this.activity.add('Cannot refresh. WebSocket not connected.', 'error');
        }
    }

    connectToServer() {
        const server = this.serverTable.getSelectedServer();
        
        if (!server) {
            this.activity.add('Please select a server first', 'error');
            return;
        }
        
        this.isConnecting = true;
        
        const nodeId = this.serverTable.getNodeId(server);
        this.activity.add(`Connecting to ${nodeId}...`, 'info');
        this.activity.add(`Server address: ${server.hostname}`, 'info');
        
        this.repository.connect(server.hostname);
    }

    disconnectVPN() {
        this.activity.add('Disconnecting VPN...', 'info');
        this.repository.disconnect();
    }

    autoConnect() {
        const servers = this.serverTable.servers;
        
        if (!servers || servers.length === 0) {
            this.activity.add('No servers available. Please refresh the list first.', 'error');
            return;
        }
        
        // Find best server (lowest ping)
        const bestServer = [...servers].sort((a, b) => {
            const pingA = parseInt(a.ping) || 9999;
            const pingB = parseInt(b.ping) || 9999;
            return pingA - pingB;
        })[0];
        
        const nodeId = this.serverTable.getNodeId(bestServer);
        this.activity.add(`Auto-selected best server: ${nodeId} (${bestServer.ping}ms)`, 'success');
        
        // Update selection
        this.serverTable.selectedServer = bestServer;
        this.serverTable.render();
        
        // Connect
        this.repository.connect(bestServer.hostname);
    }

    requestInitialData() {
        this.repository.getStatus();
        setTimeout(() => {
            this.repository.refreshServers();
        }, 500);
    }
}

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.app = new App();
});