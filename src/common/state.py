"""State classes."""

import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(kw_only=True)
class Project:
    """Represents a project state."""

    id: str
    name: str
    path: str

    @classmethod
    def _name_to_id(cls, name: str):
        id = re.sub(r"[^\w\s]", "", name.lower())
        id = re.sub(r"\s+", "-", id)

        # If no alphanumeric characters were present
        if not id:
            id = "new-project"

        return id

    @classmethod
    def from_name(cls, name: str) -> "Project":
        """Create a new project from a name."""
        id = cls._name_to_id(name)
        projects_path = (
            Path(__file__).parent.absolute().joinpath("..", "..", "projects").resolve()
        )
        path = projects_path.joinpath(id)
        idx = 2
        while path.exists():
            id = f"{id}-{idx}"
            path = projects_path.joinpath(id)
            idx += 1
        return Project(id=id, name=name, path=str(path))
