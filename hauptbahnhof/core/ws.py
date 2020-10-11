import asyncio
import json
import logging
import secrets
import ssl
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional, Tuple, List

import websockets
from websockets import WebSocketServerProtocol

from .config import Config
from .state import State
from .utils import StateUpdate


async def _send_error(websocket, error_code: int):
    msg = {"type": "error", "code": error_code}
    await websocket.send(json.dumps(msg))


def authenticated(func):
    async def wrapped(self, websocket, msg: Dict, requires_auth: bool = False):
        if (
            requires_auth
            and self._is_authenticated(msg.get("token"))
            or not requires_auth
        ):
            await func(self, websocket, msg)
        else:
            await _send_error(websocket, 403)

    return wrapped


def privileged(func):
    async def wrapped(self, websocket, msg: Dict, requires_auth: bool = False):
        if not requires_auth:
            await func(self, websocket, msg)
        else:
            await _send_error(websocket, 403)

    return wrapped


class WebSocket:
    def __init__(self, config: Config, state: State, logger: logging.Logger):
        self.config = config.get("websocket", {})
        self.logger = logger
        self.state = state

        self.block_unprivileged = False

        self.cache: Dict[str, datetime] = {}
        self._token_validity_time = timedelta(
            seconds=self.config.get("token_alidity_seconds", 3600)
        )

        # initialize ssl
        self.ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        self.ssl_context.load_cert_chain(Path(self.config.get("chainfile")), Path(self.config.get("private_key")))

        self.connections = set()

    async def _send_state(self, websocket: WebSocketServerProtocol):
        update = {"type": "state", "state": self.state.to_dict(), "block_unprivileged": self.block_unprivileged}
        await websocket.send(json.dumps(update))

    async def _send_client_info(self, websocket: WebSocketServerProtocol):
        client_ip = websocket.remote_address[0]
        client_info = {
            "type": "client_info",
            "client_ip": client_ip,
            "privileged_address": f'wss://{self.config.get("internal_host")}:{self.config.get("internal_port")}',
            "unprivileged_address": f'ws://{self.config.get("external_host")}:{self.config.get("external_port")}'
        }
        await websocket.send(json.dumps(client_info))

    async def send_update(self, msg: Dict):
        encoded_msg = json.dumps(msg)
        await asyncio.wait([conn.send(encoded_msg) for conn in self.connections])

    def _refresh_cache(self):
        for token in list(self.cache.keys()):
            if self.cache[token] <= datetime.now():
                del self.cache[token]

    async def _register(self, websocket: WebSocketServerProtocol):
        self.connections.add(websocket)

    async def _unregister(self, websocket: WebSocketServerProtocol):
        self.connections.remove(websocket)
        self._refresh_cache()

    def _generate_token(self) -> Tuple[str, datetime]:
        token = secrets.token_hex(32)
        expires_at = datetime.now() + self._token_validity_time
        self.cache[token] = expires_at

        return token, expires_at

    def _refresh_token(self, token: str) -> Optional[Tuple[str, datetime]]:
        if self._is_authenticated(token):
            del self.cache[token]
            token, expires_at = self._generate_token()
            return token, expires_at

        return None

    def _is_authenticated(self, token: str) -> bool:
        return token in self.cache and self.cache[token] > datetime.now()

    def _authenticate(
        self, username: str, password: str
    ) -> Optional[Tuple[str, datetime]]:
        if (
            username in self.config.get("users", {})
            and self.config.get("users", {})[username] == password
        ):
            token, expires_at = self._generate_token()
            self.logger.debug(
                "authenticated user %s, token expires at %s", username, expires_at
            )
            return token, expires_at

        return None

    @privileged
    async def _handle_update_troll_block(self, websocket: WebSocketServerProtocol, msg: Dict):
        if "block_unprivileged" in msg and isinstance(msg["block_unprivileged"], bool):
            self.block_unprivileged = msg["block_unprivileged"]
            self.logger.info("updated block_unprivileged = %s", self.block_unprivileged)

    @authenticated
    async def _handle_state_update(self, websocket: WebSocketServerProtocol, msg: Dict):
        await self.state.process_updates(msg.get("updates", {}))

    async def _handle_ws_message(
        self, websocket: WebSocketServerProtocol, msg: Dict, requires_auth: bool = True
    ):
        if self.block_unprivileged and requires_auth:
            await _send_error(websocket, 503)
            return

        msg_type = msg.get("type")
        if msg_type == "state_update":
            await self._handle_state_update(websocket, msg, requires_auth)

        if msg_type == "update_troll_block":
            await self._handle_update_troll_block(websocket, msg, requires_auth)

        if msg_type == "refresh_token":
            token = self._refresh_token(msg.get("token"))
            if token:
                await websocket.send(
                    json.dumps(
                        {
                            "type": "authenticated",
                            "token": token[0],
                            "expires_at": int(token[1].timestamp()),
                        }
                    )
                )
                await self._send_state(websocket)
            else:
                await _send_error(websocket, 403)

        elif msg_type == "authenticate":
            if "password" not in msg or "username" not in msg:
                self.logger.error(
                    "received invalid authenticate message on websocket: %s", msg
                )
            token = self._authenticate(msg["username"], msg["password"])
            if token:
                await websocket.send(
                    json.dumps(
                        {
                            "type": "authenticated",
                            "token": token[0],
                            "expires_at": int(token[1].timestamp()),
                        }
                    )
                )
                await self._send_state(websocket)

    async def ws_handler(self, websocket: WebSocketServerProtocol, path: str, requires_auth=True):
        self.logger.debug("received new websocket connection %s, privileged: %s", websocket, not requires_auth)
        await self._register(websocket)
        try:
            if not requires_auth:
                await self._send_state(websocket)

            await self._send_client_info(websocket)

            while True:
                msg = await websocket.recv()
                msg_decoded = json.loads(msg)
                self.logger.debug("received websocket message %s", msg_decoded)
                await self._handle_ws_message(
                    websocket, msg_decoded, requires_auth=requires_auth
                )

        finally:
            await self._unregister(websocket)

    async def ws_handler_privileged(self, websocket: websockets.WebSocketServerProtocol, path: str):
        await self.ws_handler(websocket, path, requires_auth=False)

    async def state_handler(self):
        self.logger.info("started websocket state update loop")
        while True:
            updates: List[StateUpdate] = await self.state.ws_update_queue.get()
            update_msg = {
                "type": "state_update",
                "updates": {"nodes": {
                    update.topic: update.value for update in updates
                }},
            }

            await self.send_update(update_msg)

    def start_server(self):
        return asyncio.gather(
            websockets.serve(
                self.ws_handler,
                self.config.get("external_host"),
                self.config.get("external_port"),
                ssl=self.ssl_context
            ),
            websockets.serve(
                self.ws_handler_privileged,
                self.config.get("internal_host"),
                self.config.get("internal_port"),
            ),
        )
