from dataclasses import dataclass
import json


@dataclass
class IoTConfig:
    endpoint: str
    client_id: str
    cert_file: str
    key_file: str
    root_ca: str
    topics: list[str]

    @classmethod
    def from_json(cls, path: str):
        with open(path) as f:
            data = json.load(f)

        return cls(
            endpoint=data["iotEndpoint"],
            client_id=data["clientId"],
            cert_file=data["certificateFile"],
            key_file=data["privateKeyFile"],
            root_ca=data["rootCaFile"],
            topics=data["allowedTopics"]
        )