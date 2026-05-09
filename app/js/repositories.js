// Repository/API Layer
class Repository {
    constructor(ws) {
        this.ws = ws;
    }

    connect(hostname, region) {
        return this.ws.send('connect', { hostname, region });
    }

    disconnect() {
        return this.ws.send('disconnect');
    }

    getStatus() {
        return this.ws.send('get_status');
    }

    refreshServers() {
        return this.ws.send('refresh_servers');
    }
}