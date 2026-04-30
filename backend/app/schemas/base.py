from pydantic import BaseModel, ConfigDict


def to_camel(value: str) -> str:
    """Convert a snake_case field name to lower camelCase for JSON APIs."""
    first, *rest = value.split("_")
    return first + "".join(word.capitalize() for word in rest)


class APIModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        from_attributes=True,
        populate_by_name=True,
    )
