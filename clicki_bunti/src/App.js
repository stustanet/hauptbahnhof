import React from 'react';
import "bootswatch/dist/cosmo/bootstrap.min.css";
import './App.css';
import Login from "./components/Login";
import Haspa from "./components/Haspa";
import Loading from "./components/Loading";
import mqtt from "mqtt";

const mqttURL = 'ws://knecht.stusta.de:9001';

class App extends React.Component {
    constructor(props) {
        super(props);

        this.state = {
            client: null,
            connected: false,
            loading: true
        }
    }
    componentDidMount() {
        this.connectMQTT();
    }

    authenticate(username, password) {
        localStorage.setItem('username', username);
        localStorage.setItem('password', password);

        this.setupClient(username, password);
    }

    connectMQTT() {
        const username = localStorage.getItem('username');
        const password = localStorage.getItem('password');

        if (username !== null && password !== null) {
            this.setupClient(username, password);
            return true;
        }
        return false;
    }

    setupClient(username, password) {
        const options = {
            username: username,
            password: password,
            rejectUnauthorized: false
        }
        const client = mqtt.connect(mqttURL, options);

        client.on('connect', () => {
            console.log('connected to mqtt');
            this.setState({connected: true, loading: false});
        })

        client.on('disconnect', () => {
            console.log('disconnected');
            this.setState({connected: false, loading: false});
        })

        client.on('error', (error) => {
            console.log('error occurred', error);
            this.setState({loading: false});
        })

        client.on('message', (topic, message) => {
            console.log(topic, message.toString());
        })

        this.setState({client: client})
    }

    publish(topic, message) {
        console.log('publishing on topic', topic, message);
    }

    render() {
        if (this.state.loading) {
            return (
                <Loading/>
            );
        } else {
            if (this.state.connected) {
                return (
                    <Haspa publish={this.publish.bind(this)}/>
                );
            } else {
                return (
                    <Login authenticate={this.authenticate.bind(this)}/>
                );
            }
        }
    }
}

export default App;
