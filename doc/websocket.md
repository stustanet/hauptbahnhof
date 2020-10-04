# API documentation for the core Websocket interface
All messages are passed in json format of the general form
```json
{
  "type": "<message type>",
  "token": "<auth token>",
  ... additional fields
}
```
The token field is required for not implicitly trusted clients. A token can be fetched by first authenticating.

## Messages

### State update
```json
{
  "type": "state_update",
  "updates": {
    "nodes": {
      "/some/topic": 123,
      "/another/topic": 1321,
      ... remaining topic updates
    },
    ... remaining sate updates 
  }
}
```
Sent by the websocket server to broadcast individual state changes, can also be sent by clients to change the state.

### Full state broadcast
```json
{
  "type": "state",
  "state": {
    "nodes": {
      "/haspa/licht/1/c": 0,
      "/haspa/licht/2/c": 0,
      "/haspa/licht/3/w": 123,
      ... all remaining node topics
    },
    .. all remaining state values
  }
}
```
Sent by the websocket server after a new client connects to push the initial state.

### Authentication request
```json
{
  "type": "authenticate",
  "username": "<user name>",
  "password": "<password>"
}
```
### Token Refresh Request
```json
{
  "type": "refresh_token",
  "token": "<token>"
}
```
If a valid token is provided will be answered with a `authenticated` response containing a new valid token.

### Authentication response
```json
{
  "type": "authenticated",
  "token": "<token>",
  "expires_at": "<token expiry time as utc timestamp>"
}
```
