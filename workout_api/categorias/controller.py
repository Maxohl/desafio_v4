from typing import List
from uuid import uuid4
from fastapi import APIRouter, Body, HTTPException, status, Query
from fastapi.params import Depends
from pydantic import UUID4
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError

from fastapi_pagination import PaginationParams, Page
from fastapi_pagination.paginator import paginate

from workout_api.categorias.schemas import CategoriaIn, CategoriaOut, CategoriaListOut
from workout_api.categorias.models import  CategoriaModel
from workout_api.contrib.dependencies import DataBaseDependency


router = APIRouter()

@router.post(
    path="/",
    summary="Criar nova Categoria",
    status_code=status.HTTP_201_CREATED,
    response_model=CategoriaOut,
)
async def post(
    db_session: DataBaseDependency, 
    categoria_in: CategoriaIn = Body(...)
) -> CategoriaOut:
    try:
        categoria_out = CategoriaOut(id=uuid4(), **categoria_in.model_dump())
        categoria_model = CategoriaModel(**categoria_out.model_dump())

        db_session.add(categoria_model)
        await db_session.commit()

        return categoria_out
    except IntegrityError as e:
        if "duplicate key value" in str(e):
            raise HTTPException(
                status_code=status.HTTP_303_SEE_OTHER,
                detail=f"Já existe uma categoria cadastrada com o nome: {categoria_in.nome}"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Ocorreu um erro ao inserir os dados no banco"
            )


@router.get(
    path="/",
    summary="Consultar todas as Categorias",
    status_code=status.HTTP_200_OK,
    response_model=Page[CategoriaListOut],
)
async def query(
    db_session: DataBaseDependency,
    params: PaginationParams = Depends(),
) -> Page[CategoriaListOut]:
    query = select(CategoriaModel)
    results = await db_session.execute(query)

    categorias = paginate(results, params)

    return categorias


@router.get(
    path="/{id}", summary="Consultar uma Categoria",
    status_code=status.HTTP_200_OK,
    response_model=CategoriaOut,
)
async def query(
    id: UUID4,
    db_session: DataBaseDependency,
    nome: str = Query(None, description="Filtrar por nome da categoria"),
) -> CategoriaOut:
    query = select(CategoriaModel).filter_by(id=id)
    if nome:
        query = query.filter(CategoriaModel.nome.ilike(f"%{nome}%"))

    categoria: CategoriaOut = (await db_session.execute(query)).scalars().first()

    if not categoria:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Categoria não encontrada no id: {id}"
        )

    return categoria