from typing import List
from uuid import uuid4
from fastapi import APIRouter, Body, HTTPException, status
from pydantic import UUID4
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError

from fastapi_pagination import PaginationParams, Page
from fastapi_pagination.paginator import paginate

from workout_api.centro_treinamento.schemas import CentroTreinamentoIn, CentroTreinamentoOut, CentroTreinamentoListOut
from workout_api.centro_treinamento.models import  CentroTreinamentoModel
from workout_api.contrib.dependencies import DataBaseDependency


router = APIRouter()

@router.post(
    path="/",
    summary="Criar um novo Centro de Treinamento",
    status_code=status.HTTP_201_CREATED,
    response_model=CentroTreinamentoOut,
)
async def post(
    db_session: DataBaseDependency, 
    centro_in: CentroTreinamentoIn = Body(...)
) -> CentroTreinamentoOut:
    try:
        centro_out = CentroTreinamentoOut(id=uuid4(), **centro_in.model_dump())
        centro_model = CentroTreinamentoModel(**centro_out.model_dump())

        db_session.add(centro_model)
        await db_session.commit()

        return centro_out
    except IntegrityError as e:
        if "duplicate key value" in str(e):
            raise HTTPException(
                status_code=status.HTTP_303_SEE_OTHER,
                detail=f"Já existe um centro de treinamento cadastrado com o nome: {centro_in.nome}"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Ocorreu um erro ao inserir os dados no banco"
            )



@router.get(
    path="/",
    summary="Consultar todas os Centros de treinamento",
    status_code=status.HTTP_200_OK,
    response_model=Page[CentroTreinamentoListOut], 
)
async def query(
    db_session: DataBaseDependency,
    params: PaginationParams = Depends(),
) -> Page[CentroTreinamentoListOut]:
    query = select(CentroTreinamentoModel.nome, CentroTreinamentoModel.endereco)
    results = await db_session.execute(query)

    centros = paginate(results, params) 
    
    return centros


@router.get(
    path="/{id}", summary="Consultar uma Centro de Treinamento",
    status_code=status.HTTP_200_OK,
    response_model=CentroTreinamentoOut,
)
async def query(
    id: UUID4,
    db_session: DataBaseDependency,
    nome: str = Query(None, description="Filtrar por nome do centro de treinamento"),
) -> CentroTreinamentoOut:
    query = select(CentroTreinamentoModel).filter_by(id=id)
    if nome:
        query = query.filter(CentroTreinamentoModel.nome.ilike(f"%{nome}%"))

    centro_treinamento: CentroTreinamentoOut = (
        await db_session.execute(query)
    ).scalars().first()

    if not centro_treinamento:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Centro de treinamento não encontrado no id: {id}"
        )
    
    return centro_treinamento