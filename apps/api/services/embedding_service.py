import tiktoken
from openai import AsyncOpenAI
from apps.api.config import settings

class EmbeddingService:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_embedding_model
        self.encoding = tiktoken.get_encoding("cl100k_base")
    
    async def generate_embedding(self, text: str) -> list[float]:
        response = await self.client.embeddings.create(input=[text], model=self.model)
        return response.data[0].embedding
    
    async def generate_embeddings_batch(self, texts: list[str]) -> list[list[float]]:
        response = await self.client.embeddings.create(input=texts, model=self.model)
        return [item.embedding for item in response.data]
    
    def chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
        tokens = self.encoding.encode(text)
        chunks = []
        start = 0
        while start < len(tokens):
            end = min(start + chunk_size, len(tokens))
            chunk_tokens = tokens[start:end]
            chunks.append(self.encoding.decode(chunk_tokens))
            start += chunk_size - overlap
            if start >= len(tokens):
                break
        return chunks
    
    def count_tokens(self, text: str) -> int:
        return len(self.encoding.encode(text))
