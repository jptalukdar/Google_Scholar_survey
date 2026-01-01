from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, List

class JobStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class JobConfig:
    start: int = 0
    max_results: int = 10
    step: int = 10
    since_year: int = 2020
    download_pdfs: bool = False
    sites: List[str] = field(default_factory=list)

@dataclass
class Job:
    id: str
    query: str
    status: JobStatus
    config: JobConfig
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    progress: float = 0.0
    total_results: int = 0
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "query": self.query,
            "status": self.status.value,
            "config": self.config.__dict__,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "progress": self.progress,
            "total_results": self.total_results,
            "error": self.error
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Job':
        config = JobConfig(**data.get("config", {}))
        return cls(
            id=data["id"],
            query=data["query"],
            status=JobStatus(data["status"]),
            config=config,
            created_at=datetime.fromisoformat(data["created_at"]),
            started_at=datetime.fromisoformat(data["started_at"]) if data.get("started_at") else None,
            completed_at=datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None,
            progress=data.get("progress", 0.0),
            total_results=data.get("total_results", 0),
            error=data.get("error")
        )
