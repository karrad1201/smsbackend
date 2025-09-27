from fastapi import APIRouter, Depends, status, Query
from fastapi.exceptions import HTTPException
from src.core.di import get_price_service
from src.core.logging_config import get_logger
from src.core.domain.entity.service_price import ServicePrice
from src.core.domain.dto.response_dto import StandardResponse
from typing import List, Optional

price_router = APIRouter(prefix="/prices", tags=["prices"])
logger = get_logger(__name__)


@price_router.get("/catalog", response_model=List[ServicePrice])
async def get_price_catalog(
        price_service=Depends(get_price_service)
) -> List[ServicePrice]:
    try:
        return await price_service.get_full_catalog()
    except Exception as e:
        logger.error(f"Error getting price catalog: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@price_router.get("/service/{service_code}/{country_code}", response_model=ServicePrice)
async def get_service_price(
        service_code: str,
        country_code: str,
        price_service=Depends(get_price_service)
) -> ServicePrice:
    try:
        price = await price_service.get_service_price(service_code, country_code)
        return price
    except KeyError as e:
        logger.warning(f"Validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error getting price for {service_code}/{country_code}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@price_router.get("/country/{country_code}", response_model=List[ServicePrice])
async def get_services_by_country(
        country_code: str,
        price_service=Depends(get_price_service)
) -> List[ServicePrice]:
    try:
        return await price_service.list_services_by_country(country_code)
    except KeyError as e:
        logger.warning(f"Validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error getting services for country {country_code}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@price_router.get("/service/{service_code}", response_model=List[ServicePrice])
async def get_countries_by_service(
        service_code: str,
        price_service=Depends(get_price_service)
) -> List[ServicePrice]:
    try:
        return await price_service.list_countries_by_service(service_code)
    except KeyError as e:
        logger.warning(f"Validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error getting countries for service {service_code}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@price_router.get("/popular/services", response_model=List[ServicePrice])
async def get_popular_services(
        price_service=Depends(get_price_service)
) -> List[ServicePrice]:
    try:
        return await price_service.get_popular_services()
    except Exception as e:
        logger.error(f"Error getting popular services: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@price_router.get("/popular/countries", response_model=List[ServicePrice])
async def get_popular_countries(
        price_service=Depends(get_price_service)
) -> List[ServicePrice]:
    try:
        return await price_service.get_popular_countries()
    except Exception as e:
        logger.error(f"Error getting popular countries: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@price_router.get("/stats")
async def get_availability_stats(
        price_service=Depends(get_price_service)
):
    try:
        stats = await price_service.get_availability_stats()
        return StandardResponse(
            success=True,
            message="Availability stats retrieved successfully",
            data=stats
        )
    except Exception as e:
        logger.error(f"Error getting availability stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@price_router.get("/detailed/{service_code}/{country_code}")
async def get_detailed_prices(
        service_code: str,
        country_code: str,
        price_service=Depends(get_price_service)
):
    try:
        detailed_prices = await price_service.get_detailed_prices(service_code, country_code)
        return StandardResponse(
            success=True,
            message="Detailed prices retrieved successfully",
            data=detailed_prices
        )
    except KeyError as e:
        logger.warning(f"Validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error getting detailed prices for {service_code}/{country_code}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@price_router.get("/search")
async def search_prices(
        service_code: Optional[str] = Query(None),
        country_code: Optional[str] = Query(None),
        price_service=Depends(get_price_service)
):

    try:
        if service_code and country_code:
            price = await price_service.get_service_price(service_code, country_code)
            return StandardResponse(
                success=True,
                message="Price found successfully",
                data=price
            )
        elif service_code:
            countries = await price_service.list_countries_by_service(service_code)
            return StandardResponse(
                success=True,
                message="Countries for service retrieved successfully",
                data=countries
            )
        elif country_code:
            services = await price_service.list_services_by_country(country_code)
            return StandardResponse(
                success=True,
                message="Services for country retrieved successfully",
                data=services
            )
        else:
            catalog = await price_service.get_full_catalog()
            return StandardResponse(
                success=True,
                message="Full catalog retrieved successfully",
                data=catalog
            )

    except Exception as e:
        logger.error(f"Error searching prices: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )
