// WebSocket Manager with Heartbeat and Auto-Reconnection
class Ws {
    constructor(url, messageHandlers = {}) {
        this.url = url;
        this.ws = null;
        this.connected = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = Infinity;
        this.reconnectDelay = 1000;
        this.maxReconnectDelay = 30000;
        this.messageHandlers = messageHandlers;
        this.eventListeners = {
            onOpen: [],
            onClose: [],
            onError: []
        };
        this.shouldReconnect = true;
    }

    connect() {
        if (this.ws && (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING)) {
            return;
        }
        
        console.log(`Connecting to ${this.url}...`);
        try {
            this.ws = new WebSocket(this.url);
            this.setupEventHandlers();
        } catch (error) {
            console.error('Failed to connect:', error);
            this.scheduleReconnect();
        }
    }

    setupEventHandlers() {
        this.ws.onopen = () => {
            console.log('WebSocket connected');
            this.connected = true;
            this.reconnectAttempts = 0;
            this.reconnectDelay = 1000;
            this.triggerEvent('onOpen');
        };

        this.ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                this.handleMessage(data);
            } catch (e) {
                console.error('Error parsing message:', e);
            }
        };

        this.ws.onclose = (event) => {
            console.log('WebSocket disconnected:', event.code, event.reason);
            this.connected = false;
            this.triggerEvent('onClose', event);
            
            if (this.shouldReconnect && event.code !== 1000) {
                this.scheduleReconnect();
            }
        };

        this.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
            this.triggerEvent('onError', error);
        };
    }



    scheduleReconnect() {
        if (!this.shouldReconnect) return;
        
        const delay = Math.min(this.reconnectDelay * Math.pow(1.5, this.reconnectAttempts), this.maxReconnectDelay);
        
        setTimeout(() => {
            this.reconnectAttempts++;
            console.log(`Reconnecting attempt ${this.reconnectAttempts}...`);
            this.connect();
        }, delay);
    }

    handleMessage(data) {
        // Handle error messages
        if (data.type === 'error') {
            console.error('Server error:', data.message);
            this.triggerEvent('onError', data.message);
            return;
        }
        
        // Route to registered handlers
        const handler = this.messageHandlers[data.type];
        if (handler) {
            handler(data);
        } else {
            console.log('No handler for message type:', data.type, data);
        }
    }

    send(command, data = {}) {
        if (this.connected && this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({ command, ...data }));
            return true;
        }
        console.warn('WebSocket not connected, cannot send:', command);
        return false;
    }

    reconnect() {
        if (this.ws) {
            this.ws.close();
        }
        this.connect();
    }

    on(event, callback) {
        if (this.eventListeners[event]) {
            this.eventListeners[event].push(callback);
        }
    }

    triggerEvent(event, ...args) {
        if (this.eventListeners[event]) {
            this.eventListeners[event].forEach(callback => callback(...args));
        }
    }

    get readyState() {
        return this.ws ? this.ws.readyState : WebSocket.CLOSED;
    }

    disconnect() {
        this.shouldReconnect = false;
        if (this.ws) {
            this.ws.close(1000, 'User disconnected');
            this.ws = null;
        }
        this.connected = false;
    }
}
