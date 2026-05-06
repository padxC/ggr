// Repository/API Layer
class Repository {
    constructor(ws) {
        this.ws = ws;
    }

    connect(hostname, name = 'MyVPN') {
        return this.ws.send('connect', { hostname, name });
    }

    disconnect() {
        return this.ws.send('disconnect');
    }

    getStatus() {
        return this.ws.send('get_status');
    }

    refresh() {
        return this.ws.send('refresh_servers');
    }
}