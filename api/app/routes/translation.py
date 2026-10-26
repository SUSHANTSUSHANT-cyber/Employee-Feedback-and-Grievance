import json
from urllib.parse import urlencode
from urllib.request import urlopen

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from ..auth import require_admin

router = APIRouter(prefix="/translate", tags=["translation"], dependencies=[Depends(require_admin)])


class TranslationRequest(BaseModel):
    text: str = Field(min_length=1, max_length=2000)
    target: str


@router.post("")
def translate(data: TranslationRequest):
    """Best-effort public translation helper; no API key is stored by this server."""
    language = {"hi": "hi", "ja": "ja"}.get(data.target)
    if not language:
        raise HTTPException(422, "Supported translation targets are hi and ja.")
    url = "https://api.mymemory.translated.net/get?" + urlencode({"q": data.text, "langpair": f"en|{language}"})
    try:
        with urlopen(url, timeout=8) as response:
            translated = json.loads(response.read().decode("utf-8"))["responseData"]["translatedText"]
        return {"text": translated}
    except Exception as exc:
        raise HTTPException(503, "Free translation service is currently unavailable.") from exc
