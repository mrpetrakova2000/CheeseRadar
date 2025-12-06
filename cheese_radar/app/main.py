from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
import logging

from stores import MagnitScraper, PerekrestokScraper, LentaScraper
from product_scraper import ProductScraper
from utils import setup_logging


setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI()


class ScraperRequest(BaseModel):
    store: str

@app.post("/scrape")
async def scrape_store(request: ScraperRequest):
    store_map = {
        "magnit": MagnitScraper,
        "perekrestok": PerekrestokScraper,
        "lenta": LentaScraper,
    }

    if request.store not in store_map:
        raise HTTPException(status_code=400, detail=f"Неизвестный магазин: {request.store}")

    try:
        scraper_class = store_map[request.store]
        scraper_instance = scraper_class()

        product_scraper = ProductScraper(scraper_instance)
        products_count, new_products = product_scraper.scrape_to_json()

        return {
            "store": request.store,
            "products_count": products_count,
            "new_products": new_products,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)