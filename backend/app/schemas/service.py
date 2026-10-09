from pydantic import BaseModel


class WhoAmIResponse(BaseModel):
    tenant_id: str
    tenant_name: str
