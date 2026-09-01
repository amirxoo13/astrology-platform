from fastapi import HTTPException


def validate_lat_lon(latitude: float, longitude: float) -> None:
    if not -90 <= latitude <= 90:
        raise HTTPException(
            status_code=422,
            detail=f"Latitude must be between -90 and 90. Got: {latitude}",
        )
    if not -180 <= longitude <= 180:
        raise HTTPException(
            status_code=422,
            detail=f"Longitude must be between -180 and 180. Got: {longitude}",
        )
