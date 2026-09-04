# engine/models/ids.py
import uuid

def generate_id(prefix: str) -> str:
    """Generate a short, collision-resistant identifier with a semantic prefix.
    Example: track_a91f72, clip_83bc11, tx_91ab82, snap_82fa11
    """
    short_uuid = uuid.uuid4().hex[:8]
    return f"{prefix}_{short_uuid}"
