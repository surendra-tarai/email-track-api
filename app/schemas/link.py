from pydantic import BaseModel, HttpUrl, field_validator


class CreateLinkRequest(BaseModel):
    original_url: str

    @field_validator("original_url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        if not v.startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")
        return v


class CreateLinkResponse(BaseModel):
    link_id: str
    tracking_url: str
    tracking_pixel: str
