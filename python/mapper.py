from dataclasses import MISSING, fields, is_dataclass
from enum import Enum
from typing import Any, Type, TypeVar, get_args, get_origin

T = TypeVar("T")


def _has_field(msg: Any, name: str) -> bool:
    try:
        return hasattr(msg, name)
    except Exception:
        return False


def _map_value(target_type: Any, value: Any) -> Any:
    origin = get_origin(target_type)
    args = get_args(target_type)

    if origin is list and args:
        item_type = args[0]
        return [_map_value(item_type, item) for item in value]

    if origin in (tuple, set) and args:
        item_type = args[0]
        mapped = [_map_value(item_type, item) for item in value]
        if origin is tuple:
            return tuple(mapped)
        return set(mapped)

    if origin is not None and type(None) in args:
        inner = next((a for a in args if a is not type(None)), Any)
        return None if value is None else _map_value(inner, value)

    if isinstance(target_type, type) and issubclass(target_type, Enum):
        if isinstance(value, target_type):
            return value
        if isinstance(value, str):
            try:
                return target_type[value]
            except KeyError:
                return target_type(value)
        return target_type(value)

    if isinstance(target_type, type) and is_dataclass(target_type):
        return from_proto(target_type, value)

    if target_type in (int, float, str, bool):
        return target_type(value)

    return value


def from_proto(cls: Type[T], proto_msg: Any) -> T:
    if not is_dataclass(cls):
        raise TypeError(f"Target class {cls} must be a dataclass")

    kwargs = {}
    for field in fields(cls):
        if _has_field(proto_msg, field.name):
            raw = getattr(proto_msg, field.name)
            kwargs[field.name] = _map_value(field.type, raw)
            continue

        if field.default is not MISSING:
            kwargs[field.name] = field.default
            continue

        if field.default_factory is not MISSING:  # type: ignore[attr-defined]
            kwargs[field.name] = field.default_factory()  # type: ignore[misc]
            continue

        raise ValueError(f"Missing required field '{field.name}' for {cls.__name__}")

    return cls(**kwargs)


def from_proto_list(cls: Type[T], proto_messages: Any) -> list[T]:
    return [from_proto(cls, msg) for msg in proto_messages]


def _serialize_value(value: Any, enum_mode: str) -> Any:
    if isinstance(value, Enum):
        return value.name if enum_mode == "name" else value.value

    if is_dataclass(value):
        return {
            field.name: _serialize_value(getattr(value, field.name), enum_mode)
            for field in fields(value)
        }

    if isinstance(value, list):
        return [_serialize_value(item, enum_mode) for item in value]

    return value


def to_proto(message_cls: Any, source: Any, enum_mode: str = "name") -> Any:
    if not is_dataclass(source):
        raise TypeError(f"Source instance {type(source)} must be a dataclass")

    kwargs = {}
    for field in fields(source):
        kwargs[field.name] = _serialize_value(getattr(source, field.name), enum_mode)
    return message_cls(**kwargs)


def to_proto_list(
    message_cls: Any, sources: list[Any], enum_mode: str = "name"
) -> list[Any]:
    return [to_proto(message_cls, source, enum_mode=enum_mode) for source in sources]
