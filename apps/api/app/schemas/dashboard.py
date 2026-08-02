from pydantic import BaseModel


class DashboardStats(BaseModel):
    searches_count: int
    favorites_count: int
    analyses_count: int
