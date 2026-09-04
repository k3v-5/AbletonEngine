# engine/session/resolver.py
from typing import Optional, List, Dict, Any, Union
from ..models import TrackNode
from ..errors import ObjectNotFoundError, AmbiguousObjectError

class SessionResolver:
    """Semantic resolver for locating objects in the Session Shadow Graph with ambiguity detection"""
    def __init__(self, graph):
        self.graph = graph

    def resolve(
        self,
        query: Optional[str] = None,
        id: Optional[str] = None,
        name: Optional[str] = None,
        role: Optional[str] = None,
        tags: Optional[Union[str, List[str]]] = None,
        object_type: Optional[str] = None,
        require_single: bool = True
    ) -> Union[TrackNode, List[TrackNode]]:
        """Resolve a track using flexible semantic criteria.
        If require_single is True:
          - Returns a single TrackNode if exactly 1 matches.
          - Raises ObjectNotFoundError if 0 match.
          - Raises AmbiguousObjectError if >1 match.
        If require_single is False:
          - Returns a List[TrackNode] (possibly empty).
        """
        candidates: List[TrackNode] = list(self.graph.tracks.values())

        # If query is passed as a single string, check if it's an ID first
        if query:
            if query in self.graph.tracks:
                candidates = [self.graph.tracks[query]]
            else:
                # Filter candidates by matching name or role case-insensitively
                q_lower = query.strip().lower()
                candidates = [
                    t for t in candidates
                    if t.name.lower() == q_lower or
                       (t.metadata.role and t.metadata.role.lower() == q_lower) or
                       any(tag.lower() == q_lower for tag in t.metadata.tags)
                ]

        # Specific field filters
        if id:
            candidates = [t for t in candidates if t.id == id]

        if name:
            n_lower = name.strip().lower()
            candidates = [t for t in candidates if t.name.lower() == n_lower]

        if role:
            r_upper = role.strip().upper()
            candidates = [t for t in candidates if t.metadata.role and t.metadata.role.upper() == r_upper]

        if tags:
            tag_list = [tags] if isinstance(tags, str) else tags
            tag_list_lower = [tg.strip().lower() for tg in tag_list]
            candidates = [
                t for t in candidates
                if any(tg.lower() in tag_list_lower for tg in t.metadata.tags)
            ]

        if object_type:
            t_lower = object_type.strip().lower()
            candidates = [t for t in candidates if t.type.lower() == t_lower]

        if not require_single:
            return candidates

        if len(candidates) == 0:
            criteria = {
                "query": query, "id": id, "name": name,
                "role": role, "tags": tags, "object_type": object_type
            }
            active_criteria = {k: v for k, v in criteria.items() if v is not None}
            raise ObjectNotFoundError(
                f"No object found matching criteria: {active_criteria}",
                {"criteria": active_criteria}
            )

        if len(candidates) > 1:
            matches_info = [
                {"id": t.id, "name": t.name, "role": t.metadata.role, "type": t.type, "ableton_index": t.ableton_index}
                for t in candidates
            ]
            raise AmbiguousObjectError(
                f"Multiple objects ({len(candidates)}) match criteria. Please disambiguate using specific ID.",
                {"matches_count": len(candidates), "matches": matches_info}
            )

        return candidates[0]
