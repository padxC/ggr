// WebSocket Manager
class Ws {
    constructor(url, messageHandlers = {}) {
        this.url = url;
        this.ws = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 10;
        this.reconnectDelay = 3000;
        this.messageHandlers = messageHandlers;
        this.eventListeners = {
            onOpen: [],
            onClose: [],
            onError: []
        };
    }

    connect() {
        console.log(`Attempting to connect to WebSocket at ${this.url}`);
        try {
            this.ws = new WebSocket(this.url);
            this.setupEventHandlers();
        } catch (error) {
            console.error('Failed to connect:', error);
            this.reconnect();
        }
    }

    setupEventHandlers() {
        this.ws.onopen = () => {
            console.log('WebSocket connected');
            this.reconnectAttempts = 0;
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

        this.ws.onclose = () => {
            console.log('WebSocket disconnected');
            this.triggerEvent('onClose');
            this.reconnect();
        };

        this.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
            this.triggerEvent('onError', error);
        };
    }

    handleMessage(data) {
        const handler = this.messageHandlers[data.type];
        if (handler) {
            handler(data);
        } else {
            console.log('No handler for message type:', data.type);
        }
    }

    send(command, data = {}) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({ command, ...data }));
            return true;
        }
        console.error('WebSocket is not connected');
        return false;
    }

    reconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            setTimeout(() => {
                this.reconnectAttempts++;
                console.log(`Reconnecting... Attempt ${this.reconnectAttempts}`);
                this.connect();
            }, this.reconnectDelay);
        }
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
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
    }
}