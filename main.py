
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from datetime import datetime
from typing import List, Dict, Optional

app = FastAPI()


class Vendor(BaseModel):
    name: str


class VendorCreate(Vendor):
    market_location: str
    phone: str


class VendorInDatabase(VendorCreate):
    created_at: datetime
    updated_at: datetime


class VendorsResponse(Vendor):
    created_at: datetime
    updated_at: datetime


class Produce(BaseModel):
    name: str
    quantity_kg: float
    price_per_kg: float
    category: str


class ProduceInDb(Produce):
    id: int
    vendor_id: int
    is_available: bool
    created_at: datetime
    updated_at: datetime


class Order(BaseModel):
    id: int
    produce_id: int
    buyer_name: str
    buyer_phone: str
    produce_name: str
    quantity_kg: float
    total_price: float
    delivery_area: str
    status: str
    order_date: datetime


class DataBase:
    def __init__(self):
        self.vendors_db: Dict[int, VendorInDatabase] = {}
        self.produce_db: Dict[int, List[ProduceInDb]] = {}
        self.orders_db: Dict[int, List[Order]] = {}
        self.default_vendor_id = 1
        self.default_produce_id = 1
        self.default_order_id = 1

    def increment_vendor_id(self):
        self.default_vendor_id += 1

    def increment_produce_id(self):
        self.default_produce_id += 1

    def increment_order_id(self):
        self.default_order_id += 1

    def create_vendor(self, vendor: VendorInDatabase):
        for _, vendor_data in self.vendors_db.items():
            if vendor_data.name == vendor.name:
                return None
        vendor_id = self.default_vendor_id
        self.vendors_db[vendor_id] = vendor
        self.increment_vendor_id()
        return vendor

    def add_product(self, vendor_id: int, produce: ProduceInDb):
        self.produce_db.setdefault(vendor_id, []).append(produce)

    def delete_produce(self, vendor_id: int, produce_id: int):
        produce_list = self.produce_db.get(vendor_id, [])
        for item in produce_list:
            if item.id == produce_id:
                produce_list.remove(item)
                return True
        return False

    def get_all_vendors(self):
        all_vendors = {}
        for id, vendor in self.vendors_db.items():
            user = VendorsResponse(**vendor.model_dump(exclude_unset=True))
            all_vendors[id] = user
        return all_vendors
    
    def create_order(self, order: Order):
        self.orders_db.setdefault(order.produce_id, []).append(order)
        self.increment_order_id()
        return order


database_object = DataBase()


@app.post("/vendors")
def register_vendors(vendor: VendorCreate):
    if not vendor.name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="All fields are required"
        )

    new_vendor = VendorInDatabase(
        **vendor.model_dump(),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

    created_vendor = database_object.create_vendor(new_vendor)
    if not created_vendor:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Vendor already exists"
        )

    return {
        "success": True,
        "data": VendorsResponse(**created_vendor.model_dump(exclude_unset=True)),
        "message": "Vendor created successfully"
    }


@app.get("/vendors")
def get_all_vendors():
    vendors = database_object.get_all_vendors()
    return {
        "success": True,
        "message": "All vendors retrieved successfully",
        "data": list(vendors.values())
    }


@app.get("/vendors/{vendor_id}")
def get_vendor_with_produce(vendor_id: int):
    vendor = database_object.vendors_db.get(vendor_id)
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    produce = database_object.produce_db.get(vendor_id, [])
    return {
        "vendor": vendor,
        "produce": produce
    }


@app.post("/produce")
def add_produce(vendor_id: int, produce: Produce):
    vendor = database_object.vendors_db.get(vendor_id)
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")

    new_produce = ProduceInDb(
        id=database_object.default_produce_id,
        vendor_id=vendor_id,
        is_available=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        **produce.model_dump()
    )

    database_object.add_product(vendor_id, new_produce)
    database_object.increment_produce_id()

    return {
        "success": True,
        "message": "Produce added successfully",
        "data": new_produce
    }


@app.get("/produce")
def get_all_produce():
    all_produce = database_object.get_all_produce()
    return {
        "success": True,
        "message": "All available produce retrieved successfully",
        "total_produce": len(all_produce),
        "data": all_produce
    }
    

@app.get("/produce/{produce_id}")
def get_produce_by_id(produce_id: int):
    for vendor_produce in database_object.produce_db.values():
        for produce in vendor_produce:
            if produce.id == produce_id:
                return {
                    "success": True,
                    "message": "Produce retrieved successfully",
                    "data": produce
                }

    raise HTTPException(status_code=404, detail="Produce not found")
