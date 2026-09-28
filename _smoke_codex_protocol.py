from __future__ import annotations

import json
import os
import sys
from typing import TextIO

from PySide6.QtCore import QCoreApplication, QTimer

from app import CodexAppClient


def emit(output: TextIO, payload: dict) -> None:
    output.write(json.dumps(payload, separators=(",", ":")) + "\n")
    output.flush()


def run_server() -> int:
    turns = 0
    waiting_for = ""
    for line in sys.stdin:
        message = json.loads(line)
        method = message.get("method", "")
        request_id = message.get("id")
        if method == "initialize":
            emit(sys.stdout, {"id": request_id, "result": {"serverInfo": {"name": "fake"}}})
        elif method == "account/read":
            emit(sys.stdout, {"id": request_id, "result": {"account": {"type": "fake", "planType": "test"}}})
        elif method == "model/list":
            emit(sys.stdout, {"id": request_id, "result": {"data": [{"model": "fake-model"}]}})
        elif method == "thread/start":
            emit(sys.stdout, {"id": request_id, "result": {"thread": {"id": f"thread-{turns + 1}"}}})
        elif method == "turn/start":
            turns += 1
            if turns == 1:
                input_items = message.get("params", {}).get("input", [])
                if [item.get("type") for item in input_items] != ["text", "text", "text", "localImage"]:
                    return 22
                if "document.pdf — trang 1" not in input_items[1].get("text", ""):
                    return 23
                if "document.pdf — trang 2" not in input_items[2].get("text", ""):
                    return 24
                if not os.path.isfile(input_items[3].get("path", "")):
                    return 25
            emit(sys.stdout, {"id": request_id, "result": {"turn": {"id": f"turn-{turns}"}}})
            if turns == 1:
                waiting_for = "command"
                emit(
                    sys.stdout,
                    {
                        "id": "approval-command",
                        "method": "item/commandExecution/requestApproval",
                        "params": {},
                    },
                )
            elif turns == 2:
                emit(sys.stdout, {"method": "item/agentMessage/delta", "params": {"delta": "second"}})
                emit(sys.stdout, {"method": "turn/completed", "params": {"turn": {"status": "completed"}}})
            else:
                emit(
                    sys.stdout,
                    {
                        "method": "turn/completed",
                        "params": {
                            "turn": {"status": "failed", "error": {"message": "synthetic failure"}}
                        },
                    },
                )
        elif request_id == "approval-command" and waiting_for == "command":
            if message.get("result") != {"decision": "cancel"}:
                return 20
            waiting_for = "permission"
            emit(
                sys.stdout,
                {
                    "id": "approval-permission",
                    "method": "item/permissions/requestApproval",
                    "params": {},
                },
            )
        elif request_id == "approval-permission" and waiting_for == "permission":
            if message.get("result") != {"permissions": {}}:
                return 21
            waiting_for = ""
            emit(sys.stdout, {"method": "item/agentMessage/delta", "params": {"delta": "hel"}})
            emit(sys.stdout, {"method": "item/agentMessage/delta", "params": {"delta": "lo"}})
            emit(sys.stdout, {"method": "turn/completed", "params": {"turn": {"status": "completed"}}})
    return 0


def run_smoke() -> int:
    app = QCoreApplication(sys.argv)
    client = CodexAppClient(executable=sys.executable, arguments=[os.path.abspath(__file__), "--server"])
    state = {"phase": 0, "models": False, "account": False}

    def fail(message: str) -> None:
        print("CODEX_PROTOCOL_SMOKE_FAIL:", message)
        client.shutdown()
        app.exit(1)

    def ready(connected: bool, message: str) -> None:
        if not connected and not client.shutting_down:
            fail(message)

    def models(values: list) -> None:
        if values != ["fake-model"]:
            fail(f"models={values!r}")
            return
        state["models"] = True
        maybe_start()

    def account(value: str) -> None:
        if value != "fake • test":
            fail(f"account={value!r}")
            return
        state["account"] = True
        maybe_start()

    def maybe_start() -> None:
        if state["phase"] == 0 and state["models"] and state["account"]:
            state["phase"] = 1
            client.send_message(
                "fake-model",
                "first",
                [
                    {
                        "kind": "pdf",
                        "name": "document.pdf",
                        "pages": [
                            {"page": 1, "kind": "text", "text": "PDF text"},
                            {"page": 2, "kind": "image", "data": b"synthetic-png"},
                        ],
                    }
                ],
                "inspect",
            )

    def succeeded(text: str) -> None:
        if state["phase"] == 1 and text == "hello":
            client.reset_thread()
            if client.thread_id:
                fail("reset kept thread ID")
                return
            state["phase"] = 2
            client.send_message("fake-model", "second", [], "inspect")
        elif state["phase"] == 2 and text == "second":
            client.reset_thread()
            state["phase"] = 3
            client.send_message("fake-model", "fail", [], "inspect")
        else:
            fail(f"unexpected success phase={state['phase']} text={text!r}")

    def failed(message: str) -> None:
        if state["phase"] == 3 and message == "synthetic failure":
            print("CODEX_PROTOCOL_SMOKE_OK")
            client.shutdown()
            app.quit()
        else:
            fail(f"unexpected failure phase={state['phase']} message={message!r}")

    client.ready_changed.connect(ready)
    client.models_changed.connect(models)
    client.account_changed.connect(account)
    client.succeeded.connect(succeeded)
    client.failed.connect(failed)
    QTimer.singleShot(10_000, lambda: fail("timeout"))
    client.start()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(run_server() if "--server" in sys.argv else run_smoke())
