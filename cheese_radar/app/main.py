from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
import logging
from typing import Dict

from stores import MagnitScraper, PerekrestokScraper, LentaScraper
from product_scraper import ProductScraper
from utils import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI()


class ScraperRequest(BaseModel):
    store: str


class ScrapeResponse(BaseModel):
    status: str
    store: str
    total_in_database: int
    new_products_saved: int


@app.post("/scrape")
async def scrape_store(request: ScraperRequest) -> ScrapeResponse:
    logger.info(f"Запрос на скрапинг: {request.store}")

    store_map: Dict[str, tuple] = {
        "magnit": ("Магнит", MagnitScraper),
        # "perekrestok": ("Перекрёсток", PerekrestokScraper),
        # "lenta": ("Лента", LentaScraper),
    }

    if request.store not in store_map:
        raise HTTPException(
            status_code=400,
            detail=f"Неизвестный магазин: {request.store}"
        )

    try:
        display_name, scraper_class = store_map[request.store]
        logger.info(f"Запуск скрапера для магазина: {display_name}")

        scraper_instance = scraper_class()
        product_scraper = ProductScraper(scraper_instance)
        total_in_db, new_saved = product_scraper.scrape()

        return ScrapeResponse(
            status="success",
            store=display_name,
            total_in_database=total_in_db,
            new_products_saved=new_saved
        )

    except Exception as e:
        logger.error(f"Ошибка при скрапинге {request.store}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=5080, reload=True, workers=1)
