from pydantic import BaseModel
from typing import (
    Dict,
    Type
)


class LoginSchema(BaseModel):
    email: str
    password: str

    class Config:
        extra = "forbid"


class ProjectSchema(BaseModel):
    url: str = None
    name: str = None
    description: str = None

    class Config:
        extra = "forbid"


class CompanySchema(BaseModel):
    name: str = None
    description: str = None

    class Config:
        extra = "forbid"


class PasswordSchema(BaseModel):
    new_password: str
    current_password: str
    repeat_password: str = None

    class Config:
        extra = "forbid"


def validate_input(schema_type: Type[BaseModel], **input: Dict) -> bool:
    try:
        return bool(schema_type(**input))
    except ValueError as _:
        return False
