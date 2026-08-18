"""
Pydantic models for Akiya Scout
"""
from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional
from datetime import datetime


class Property(BaseModel):
    """
    Normalized property model for Japanese akiya listings.
    All optional fields default to None when data is not available.
    """
    model_config = ConfigDict(strict=True, json_encoders={datetime: lambda v: v.isoformat() + "Z" if v.tzinfo is None else v.isoformat()})
    
    id: str = Field(..., description="Unique property identifier")
    title: str = Field(..., description="Property title")
    listing_type: str = Field(default="SALE", description="Listing type: SALE or RENTAL")
    price: Optional[int] = Field(None, description="Price in Japanese Yen (integer)")
    prefecture: Optional[str] = Field(None, description="Prefecture name (e.g., Tokyo, Osaka)")
    municipality: Optional[str] = Field(None, description="Municipality/city name")
    area: Optional[str] = Field(None, description="Area/neighborhood name")
    land_size_m2: Optional[float] = Field(None, description="Land size in square meters")
    building_size_m2: Optional[float] = Field(None, description="Building size in square meters")
    build_year: Optional[int] = Field(None, description="Year the building was constructed")
    rooms: Optional[str] = Field(None, description="Room layout (e.g., 3LDK, 2DK)")
    structure: Optional[str] = Field(None, description="Building structure (e.g., Wooden, RC)")
    floors: Optional[int] = Field(None, description="Number of floors")
    parking: Optional[str] = Field(None, description="Parking availability information")
    description: Optional[str] = Field(None, description="Property description")
    source_name: str = Field(..., description="Name of the source website")
    source_url: str = Field(..., description="Original listing URL")
    image_url: Optional[str] = Field(None, description="Main image URL")
    latitude: Optional[float] = Field(None, description="Latitude coordinate")
    longitude: Optional[float] = Field(None, description="Longitude coordinate")
    collected_at: datetime = Field(default_factory=datetime.utcnow, description="When the data was collected")

    @field_validator('listing_type')
    @classmethod
    def validate_listing_type(cls, v):
        """Validate that listing_type is SALE or RENTAL."""
        if v.upper() not in ['SALE', 'RENTAL']:
            raise ValueError('listing_type must be SALE or RENTAL')
        return v.upper()

    @field_validator('price')
    @classmethod
    def validate_price(cls, v):
        """Validate that price is a positive integer when provided."""
        if v is not None and v < 0:
            raise ValueError('Price must be a positive integer')
        return v

    @field_validator('land_size_m2', 'building_size_m2')
    @classmethod
    def validate_sizes(cls, v):
        """Validate that sizes are positive floats when provided."""
        if v is not None and v < 0:
            raise ValueError('Size must be a positive number')
        return v

    @field_validator('latitude')
    @classmethod
    def validate_latitude(cls, v):
        """Validate latitude range."""
        if v is not None and (v < -90 or v > 90):
            raise ValueError('Latitude must be between -90 and 90')
        return v

    @field_validator('longitude')
    @classmethod
    def validate_longitude(cls, v):
        """Validate longitude range."""
        if v is not None and (v < -180 or v > 180):
            raise ValueError('Longitude must be between -180 and 180')
        return v


class PropertyListResponse(BaseModel):
    """Response model for property list endpoint."""
    properties: list[Property] = Field(default_factory=list, description="List of properties")
    total: int = Field(0, description="Total number of properties")