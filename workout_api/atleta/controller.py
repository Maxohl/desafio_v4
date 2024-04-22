from datetime import datetime
from uuid import uuid4
from fastapi import APIRouter, Body, HTTPException, status, Query
from pydantic import UUID4
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError

from workout_api.atleta.models import AtletaModel
from workout_api.atleta.schemas import AtletaIn, AtletaOut, AtletaUpdate, AtletaListOut
from workout_api.categorias.models import CategoriaModel
from workout_api.centro_treinamento.models import CentroTreinamentoModel
from workout_api.contrib.dependencies import DataBaseDependency


router = APIRouter()

@router.post(
    path="/", summary="Criar um novo atleta",
    status_code = status.HTTP_201_CREATED,
    response_model=AtletaOut
)
async def post(
    db_session: DataBaseDependency, 
    atleta_in: AtletaIn = Body(...)
):
    categoria_name = atleta_in.categoria.nome
    centro_treinamento_nome = atleta_in.centro_treinameto.nome

    categoria = (await db_session.execute(
        select(CategoriaModel).filter_by(nome=categoria_name))
    ).scalars().first()

    if not categoria:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail= f"A categoria {categoria_name} não foi encontrada."
        )
    


    centro_treinamento = (await db_session.execute(
        select(CentroTreinamentoModel).filter_by(nome=centro_treinamento_nome))
    ).scalars().first()

    if not centro_treinamento:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail= f"O centro de treinamento {centro_treinamento_nome} não foi encontrado."
        )

    try:
        atleta_out = AtletaOut(id=uuid4(), created_at=datetime.utcnow(), **atleta_in.model_dump())
        atleta_model = AtletaModel(**atleta_out.model_dump(exclude={"categoria", "centro_treinamento"}))
        atleta_model.categoria_id = categoria.pk_i
        atleta_model.centro_treinamento_id = centro_treinamento.pk_id

        db_session.add(atleta_model)
        await db_session.commit
    except IntegrityError as e:
        # Checar se o erro é por conta de dois cpfs iguais
        if "Duplicate entry" in str(e):
            raise HTTPException(
                status_code=status.HTTP_303_SEE_OTHER,
                detail=f"Já existe um atleta cadastrado com o CPF: {atleta_in.cpf}"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
                detail="Ocorreu um erro ao inserir os dados no banco"
            )

    return atleta_out


@router.get(
    path="/",
    summary="Consultar todos os atletas",
    status_code=status.HTTP_200_OK,
    response_model=list[AtletaListOut],
)
async def query(db_session: DataBaseDependency) -> list[AtletaListOut]:
    atletas: list[AtletaListOut] = []
    results = await db_session.execute(select(AtletaModel.nome, AtletaModel.cpf))
    for nome, cpf in results.all():
        atletas.append(AtletaListOut(nome=nome, cpf=cpf))
    return atletas


@router.get(
    path="/{id}", summary="Consultar um Atleta por id",
    status_code=status.HTTP_200_OK,
    response_model=AtletaOut,
)
async def query(
    id: UUID4,
    db_session: DataBaseDependency,
    nome: str = Query(None, description="Filtrar por nome do atleta"),
    cpf: str = Query(None, description="Filtrar por CPF do atleta"),
) -> AtletaOut:
    query = select(AtletaModel).filter_by(id=id)
    if nome:
        query = query.filter(AtletaModel.nome.ilike(f"%{nome}%"))
    if cpf:
        query = query.filter(AtletaModel.cpf == cpf)

    atleta: AtletaOut = (await db_session.execute(query)).scalars().first()

    if not atleta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Atleta não encontrado no id: {id}"
        )

    return atleta

@router.patch(
    path="/{id}", summary="Editar um Atleta",
    status_code = status.HTTP_200_OK,
    response_model= AtletaOut,
)
async def query(id: UUID4, db_session: DataBaseDependency, atleta_up : AtletaUpdate = Body(...)) -> AtletaOut:
    atleta: AtletaOut = (
        await db_session.execute(select(AtletaModel).filter_by(id=id))
    ).scalars().first

    if not atleta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Categoria não encontrado no id: {id}"
        )
    
    atleta_update = atleta_up.model_dump(exclude_unset= True)
    for key, value in atleta_update.items():
        setattr(atleta, key, value)

    await db_session.commit()
    await db_session.refresh(atleta)
    return atleta

@router.delete(
    path="/{id}", summary="Deletar um Atleta por id",
    status_code = status.HTTP_204_NO_CONTENT
)
async def query(id: UUID4, db_session: DataBaseDependency) -> None:
    atleta: AtletaOut = (
        await db_session.execute(select(AtletaModel).filter_by(id=id))
    ).scalars().first

    if not atleta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Categoria não encontrado no id: {id}"
        )
    
    await db_session.delete(atleta)
    await db_session.commit()