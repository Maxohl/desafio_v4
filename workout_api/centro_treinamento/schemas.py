from typing import Annotated
from pydantic import UUID4, Field

from workout_api.contrib.schemas import BaseSchema


class CentroTreinamentoIn(BaseSchema):
    nome: Annotated[str, Field(description="Nome do Centro de Treinamento", example="CT King", max_length=20)]
    endereco: Annotated[str, Field(description="Endereco do Centro de Treinamento", example="Cidade/Estado", max_length=60)]
    proprietario: Annotated[str, Field(description="Proprietario do Centro de Treinamento", example="Joao Carlos", max_length=30)]


class CentroTreinamentoAtleta(BaseSchema):
    nome: Annotated[str, Field(description="Nome do centro de treinamento", example="CT King?", max_length=20)]


class CentroTreinamentoOut(CentroTreinamentoIn):
    id: Annotated[UUID4, Field(description="Identificador do Centro de Treinamento")]

class CentroTreinamentoListOut(BaseSchema):
    nome: Annotated[str, Field(description="Nome do Centro de Treinamento", example="CT King", max_length=20)]
    endereco: Annotated[str, Field(description="Endereco do Centro de Treinamento", example="Cidade/Estado", max_length=60)]