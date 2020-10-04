import React from 'react';
import "bootswatch/dist/cosmo/bootstrap.min.css";
import './App.css';
import Login from "./components/Login";
import Haspa from "./components/Haspa";
import Loading from "./components/Loading";

const wsURL = 'ws://localhost:8001';

class App extends React.Component {
    state = {
        loading: true,
        auth: null,
        nodeState: {},
        ws: null
    }

    ws = new WebSocket(wsURL);

    initWS = () => {
        this.ws.onopen = () => {
            console.log("websocket connected")
            this.setState({loading: false})

            const auth = localStorage.getItem("token");
            if (auth !== null && auth !== undefined) {
                let authState;
                try {
                    authState = JSON.parse(auth);
                    if (authState["expiresAt"] > new Date().getTime() / 1000) {
                        this.ws.send(JSON.stringify({
                            "type": "refresh_token",
                            "token": authState["token"]
                        }))
                    } else {
                        console.log("found expired auth token in local storage", authState);
                    }
                } catch {
                    console.log("found invalid auth token in local storage");
                }
            }
        }

        this.ws.onmessage = evt => {
            const message = JSON.parse(evt.data)
            console.log("received message", message)
            if (message["type"] === "authenticated") {
                const auth = {
                    token: message["token"],
                    expiresAt: message["expires_at"]
                }
                localStorage.setItem("token", JSON.stringify(auth));
                this.setState({auth: auth, loading: false});

                // set a timer to refresh the received token 10 seconds before it expires
                setTimeout(this.refreshToken, message["expires_at"] * 1000 - new Date().getTime() - 10000);
            } else if (message["type"] === "error") {
                if (message["code"] === 403) {
                    this.setState({loading: false, auth: null});
                }
            } else if (message["type"] === "state") {
                if (!message.hasOwnProperty("state")) {
                    console.log("error, invalid state message:", message);
                } else {
                    this.setState({nodeState: message["state"]["nodes"]})
                }
            } else if (message["type"] === "state_update") {
                if (!message.hasOwnProperty("updates")) {
                    console.log("error, invalid state message:", message);
                } else {
                    this.setState({nodeState: Object.assign(this.state.nodeState, message["updates"]["nodes"])});
                }
            }
        }

        this.ws.onclose = () => {
            console.log("websocket disconnected")
            this.setState({
                loading: true,
                auth: null
            })

            // try to reconnect after 1 second
            setTimeout(() => {
                this.ws = new WebSocket(wsURL);
                this.initWS();
            }, 1000);
        }
    }

    componentDidMount() {
        this.initWS();
    }

    refreshToken = () => {
        if (!this.state.loading && this.state.auth !== null) {
            this.ws.send(JSON.stringify({
                "type": "refresh_token",
                "token": this.state.auth.token
            }))
        }
    }

    authenticate = (username, password) => {
        this.setState({loading: true});
        this.ws.send(JSON.stringify({
            type: "authenticate",
            username: username,
            password: password
        }))
    }

    send = (payload) => {
        if (this.state.auth === null || this.state.auth.expiresAt < new Date().getTime() / 1000) {
            this.setState({auth: null});
            return
        }

        const msg = {
            token: this.state.auth.token,
            ...payload
        }

        console.log("sending message:", msg);
        this.ws.send(JSON.stringify(msg));
    }

    render() {
        if (this.state.loading) {
            return (
                <Loading/>
            );
        } else {
            if (this.state.auth !== null) {
                return (
                    <Haspa nodeState={this.state.nodeState} send={this.send}/>
                );
            } else {
                return (
                    <Login authenticate={this.authenticate}/>
                );
            }
        }
    }
}

export default App;
