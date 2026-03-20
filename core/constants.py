from enum import Enum, unique


@unique
class FlowDirectionCode(Enum):
    ENTRY = "ENTRY"
    EXIT = "EXIT"

@unique
class GeneralStatusCode(Enum):
    ENABLE = "ENABLE"
    DISABLE = "DISABLE"


if __name__ == '__main__':
    print(FlowDirectionCode.EXIT.value)
