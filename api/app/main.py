from typing import Optional
from pydantic import BaseModel
from fastapi.responses import PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware
from time import time
import impl
from fastapi import FastAPI, Body, Request, Response

app = FastAPI(
    title="vendor product lookup",
    description="lookup for products of various vendors",
    version="1.0.0",)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


tags_metadata = [
    {
        "name": "funcs",
        "description": "default funcs to get vendor product items, it's refined",
    },
    {
        "name": "raw",
        "description": "get raw data based on the request",
    },
]

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time()
    response = await call_next(request)
    process_time = time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


@app.get("/getCoupangProducts", tags=["funcs"])
async def get_coupang_products(
        query: str,
        sort: Optional[str] = 'scoreDesc',
        page: Optional[str] = '1'
):
    print(f"getting products in coupang for query {query}")
    return impl.coupang_products(query=query, sort=sort, page=page)


@app.get("/getCoupangProductsRaw", tags=["raw"], response_class=PlainTextResponse)
async def get_coupang_products_raw(
        query: str,
        page: Optional[str] = '1'
):
    return impl.coupang_products_raw(query=query, page=page)


@app.get("/getGmarketProducts", tags=["funcs"])
async def get_gmarket_products(
        query: str,
        sort: Optional[str] = '7',
        page: Optional[str] = '1'
):
    print(f"getting products in gmarket for query {query}")
    return impl.gmarket_products(query=query, sort=sort, page=page)


@app.get("/getGmarketProductsRaw", tags=["raw"], response_class=PlainTextResponse)
async def get_gmarket_products_raw(query: str, page: Optional[str] = '1'):
    return impl.gmarket_products_raw(query=query, page=page)


@app.get("/getElevenStreetProducts", tags=["funcs"])
async def get_eleven_street_products(query: str, page: Optional[str] = '1'):
    print(f'getting products in 11st for query {query}')
    return impl.elevenStreet_products(query=query, page=page)


@app.get("/getElevenStreetProductsRaw", response_class=PlainTextResponse, tags=["raw"])
async def get_eleven_street_products_raw(query: str, page: Optional[str] = '1'):
    return impl.elevenStreet_products_raw(query=query, page=page)


@app.get("/getInterparkProducts", tags=["funcs"])
async def get_interpark_products(query: str, page: Optional[str] = '1'):
    print(f'getting products in interpark for query {query}')
    return impl.interpark_products(query=query, page=page)


@app.get("/getInterparkProductsRaw", response_class=PlainTextResponse, tags=["raw"])
async def get_interpark_products_raw(query: str, page: Optional[str] = '1'):
    return impl.interpark_products_raw(query=query, page=page)


@app.get("/getAuctionProducts", tags=["funcs"])
async def get_auction_products(query: str, page: Optional[str] = '1'):
    print(f"getting products in auction for query {query}")
    return impl.auction_products(query=query, page=page)


@app.get("/getAuctionProductsRaw", response_class=PlainTextResponse, tags=["raw"])
async def get_auction_products_raw(query: str, page: Optional[str] = '1'):
    return impl.auction_products_raw(query=query, page=page)


@app.get("/getWemakepriceProducts", tags=["funcs"])
async def get_we_make_price_products(query: str, page: Optional[str] = '1'):
    print(f"getting products in wemakeprice for query {query}")
    return impl.weMakePrice_products(query=query, page=page)


@app.get("/getWemakepriceProductsRaw", response_class=PlainTextResponse, tags=["raw"])
async def get_we_make_price_products_raw(query: str, page: Optional[str] = '1'):
    return impl.weMakePrice_products_raw(query=query, page=page)


@app.get("/getTmonProducts", tags=["funcs"])
async def get_tmon_products(query: str, page: Optional[str] = '1'):
    print(f'getting products in tmon for query {query}')
    return impl.tmon_products(query=query, page=page)


@app.get("/getTmonProductsRaw", response_class=PlainTextResponse, tags=["raw"])
async def get_tmon_products_raw(query: str, page: Optional[str] = '1'):
    return impl.tmon_products_raw(query=query, page=page)


@app.get("/getAllVendorProducts", tags=["funcs"])
async def get_all_vendors(query:str, page:Optional[str]='1'):
    return impl.all_products(query=query, page=page)
