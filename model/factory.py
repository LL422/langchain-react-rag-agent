from abc import ABC, abstractmethod
from typing import Optional, List
from langchain_core.embeddings import Embeddings
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from utils.config_handler import rag_conf
import os
import logging

logger = logging.getLogger(__name__)

LM_STUDIO_BASE_URL = os.getenv("LM_STUDIO_BASE_URL", "http://localhost:1234/v1")


class BaseModelFactory(ABC):
    @abstractmethod
    def generator(self) -> Optional[Embeddings | ChatOpenAI]:
        pass


class ChatModelFactory(BaseModelFactory):
    def generator(self) -> Optional[Embeddings | ChatOpenAI]:
        return ChatOpenAI(
            model=rag_conf["chat_model_name"],
            base_url=LM_STUDIO_BASE_URL,
            api_key="not-needed",
            temperature=0.7,
        )


class FixLMStudioEmbeddings(OpenAIEmbeddings):
    """
    LM Studio's embedding endpoint rejects the token-ID arrays that
    langchain-openai's _get_len_safe_embeddings produces. Override to
    send raw text strings one batch at a time instead.
    """

    def _get_len_safe_embeddings(
        self, texts: List[str], **kwargs
    ) -> List[List[float]]:
        embeddings: List[List[float]] = []
        for text in texts:
            try:
                response = self.client.create(
                    input=[text],
                    model=self.model,
                )
                embeddings.append(response.data[0].embedding)
            except Exception as e:
                logger.error(f"Embedding failed for text starting with: {text[:80]}... Error: {e}")
                raise e
        return embeddings


class EmbeddingsFactory(BaseModelFactory):
    def generator(self) -> Optional[Embeddings | ChatOpenAI]:
        return FixLMStudioEmbeddings(
            model=rag_conf["embedding_model_name"],
            base_url=LM_STUDIO_BASE_URL,
            api_key="not-needed",
        )


chat_model = ChatModelFactory().generator()
embed_model = EmbeddingsFactory().generator()
