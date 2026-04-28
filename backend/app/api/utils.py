from collections.abc import Iterable

from fastapi import HTTPException

from app.services.taxonomy import TaxonomyError


def apply_update_fields(model: object, update_data: dict, fields: Iterable[str]) -> None:
    for field in fields:
        if field in update_data:
            setattr(model, field, update_data[field])


def taxonomy_http_error(exc: TaxonomyError) -> HTTPException:
    return HTTPException(status_code=422, detail=str(exc))
