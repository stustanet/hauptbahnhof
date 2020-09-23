import asyncio
import json
import logging
import secrets
import ssl
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple

import websockets

from core.config import Config
from core.state import State
from core.utils import StateUpdate


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


class WebSocket:
    def __init__(self, config: Config, state: State, logger: logging.Logger):
        self.config = config.get("websocket", {})
        self.logger = logger
        self.state = state

        self.cache: Dict[str, datetime] = {}
        self._token_validity_time = timedelta(
            seconds=self.config.get("tokenValiditySeconds", 3600)
        )

        # initialize ssl
        self.ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        # self.ssl_context.load_cert_chain(Path(self.config.get("chainfile")))

        self.connections = set()

    async def _send_state(self, websocket):
        update = {"type": "state", "state": self.state.to_dict()}
        await websocket.send(json.dumps(update))

    async def send_update(self, msg: Dict):
        encoded_msg = json.dumps(msg)
        await asyncio.wait([conn.send(encoded_msg) for conn in self.connections])

    def _refresh_cache(self):
        for token in list(self.cache.keys()):
            if self.cache[token] <= datetime.now():
                del self.cache[token]

    async def _register(self, websocket):
        self.connections.add(websocket)

    async def _unregister(self, websocket):
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

    @authenticated
    async def _handle_state_update(self, websocket, msg):
        await self.state.process_updates(msg.get("updates", {}))

    async def _handle_ws_message(
        self, websocket, msg: Dict, requires_auth: bool = True
    ):
        msg_type = msg.get("type")
        if msg_type == "state_update":
            await self._handle_state_update(websocket, msg, requires_auth)

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

    async def ws_handler(self, websocket, path, requires_auth=True):
        self.logger.debug("received new websocket connection %s", websocket)
        await self._register(websocket)
        try:
            if not requires_auth:
                await self._send_state(websocket)
            while True:
                msg = await websocket.recv()
                msg_decoded = json.loads(msg)
                self.logger.debug("received websocket message %s", msg_decoded)
                await self._handle_ws_message(
                    websocket, msg_decoded, requires_auth=requires_auth
                )

        finally:
            await self._unregister(websocket)

    async def ws_handler_unauthenticated(self, websocket, path):
        await self.ws_handler(websocket, path, requires_auth=False)

    async def state_handler(self):
        self.logger.info("started websocket state update loop")
        while True:
            update: StateUpdate = await self.state.ws_update_queue.get()
            update_msg = {
                "type": "state_update",
                "updates": {"nodes": {update.topic: update.value}},
            }

            await self.send_update(update_msg)

    def start_server(self):
        return asyncio.gather(
            websockets.serve(
                self.ws_handler,
                self.config.get("externalHost"),
                self.config.get("externalPort"),
                # ssl=self.ssl_context
            ),
            websockets.serve(
                self.ws_handler_unauthenticated,
                self.config.get("internalHost"),
                self.config.get("internalPort"),
                # ssl=self.ssl_context
            ),
        )
