from dotenv import load_dotenv
load_dotenv()

from abc import ABC, abstractmethod
from typing import Optional, List
from langchain_core.embeddings import Embeddings
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from utils.config_handler import rag_conf
import os
import time
import logging

logger = logging.getLogger(__name__)

LLM_BASE_URL = os.getenv("LLM_BASE_URL", "http://localhost:1234/v1")
LLM_API_KEY = os.getenv("LLM_API_KEY", "not-needed")
EMBED_BASE_URL = os.getenv("EMBED_BASE_URL", os.getenv("LLM_BASE_URL", "http://localhost:1234/v1"))
EMBED_API_KEY = os.getenv("EMBED_API_KEY", os.getenv("LLM_API_KEY", "not-needed"))

MAX_RETRIES = 3
RETRY_BACKOFF = [1, 2, 4]  # seconds


class BaseModelFactory(ABC):
    @abstractmethod
    def generator(self) -> Optional[Embeddings | ChatOpenAI]:
        pass


class ChatModelFactory(BaseModelFactory):
    def generator(self) -> Optional[Embeddings | ChatOpenAI]:
        return ChatOpenAI(
            model=rag_conf["chat_model_name"],
            base_url=LLM_BASE_URL,
            api_key=LLM_API_KEY,
            temperature=0.7,
            max_retries=MAX_RETRIES,
        )


class CompatibleEmbeddings(OpenAIEmbeddings):
    """
    OpenAI-compatible embeddings with per-text request style and retry.
    Avoids token-ID arrays that some endpoints reject.
    """

    def _get_len_safe_embeddings(
        self, texts: List[str], **kwargs
    ) -> List[List[float]]:
        embeddings: List[List[float]] = []
        for text in texts:
            last_error = None
            for attempt in range(MAX_RETRIES):
                try:
                    response = self.client.create(
                        input=[text],
                        model=self.model,
                    )
                    embeddings.append(response.data[0].embedding)
                    break
                except Exception as e:
                    last_error = e
                    status = getattr(e, "status_code", None) or getattr(
                        getattr(e, "response", None), "status_code", None
                    )
                    if status and status < 500 and status != 429:
                        raise e
                    if attempt < MAX_RETRIES - 1:
                        wait = RETRY_BACKOFF[attempt]
                        logger.warning(
                            f"Embedding retry {attempt + 1}/{MAX_RETRIES} "
                            f"after {wait}s: {str(e)[:100]}"
                        )
                        time.sleep(wait)
                    else:
                        logger.error(
                            f"Embedding failed after {MAX_RETRIES} attempts: "
                            f"{text[:80]}... Error: {last_error}"
                        )
                        raise last_error
        return embeddings


class EmbeddingsFactory(BaseModelFactory):
    def generator(self) -> Optional[Embeddings | ChatOpenAI]:
        return CompatibleEmbeddings(
            model=rag_conf["embedding_model_name"],
            base_url=EMBED_BASE_URL,
            api_key=EMBED_API_KEY,
        )


chat_model = ChatModelFactory().generator()
embed_model = EmbeddingsFactory().generator()
