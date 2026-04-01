"""ChromaDB vector store integration."""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime
from loguru import logger

from src.providers.provider_manager import ProviderManager


class ChromaStore:
    """Vector store for CVs and job descriptions using ChromaDB."""
    
    def __init__(
        self,
        persist_directory: str = ".chroma",
        provider_manager: Optional[ProviderManager] = None,
    ):
        """Initialize ChromaDB store.
        
        Args:
            persist_directory: Directory for persistent storage
            provider_manager: Provider manager for embeddings
        """
        self.persist_directory = Path(persist_directory)
        self.provider_manager = provider_manager
        self.client = None
        self.cv_collection = None
        self.job_collection = None
    
    async def initialize(self) -> bool:
        """Initialize ChromaDB connection.
        
        Returns:
            True if successful
        """
        try:
            import chromadb
            from chromadb.config import Settings
            
            # Create persistent client
            self.client = chromadb.PersistentClient(
                path=str(self.persist_directory),
                settings=Settings(anonymized_telemetry=False),
            )
            
            # Create collections
            self.cv_collection = self.client.get_or_create_collection(
                name="cvs",
                metadata={"description": "Generated CVs and their embeddings"},
            )
            
            self.job_collection = self.client.get_or_create_collection(
                name="jobs",
                metadata={"description": "Job postings and their embeddings"},
            )
            
            logger.info(f"ChromaDB initialized at {self.persist_directory}")
            return True
            
        except Exception as e:
            logger.warning(f"ChromaDB initialization failed: {e}")
            return False
    
    async def store_cv(
        self,
        cv_id: str,
        cv_data: Dict[str, Any],
        job_url: str,
        scores: Dict[str, Any],
    ) -> bool:
        """Store a CV in the vector store.
        
        Args:
            cv_id: Unique CV identifier
            cv_data: CV data dictionary
            job_url: Associated job URL
            scores: Score report
            
        Returns:
            True if successful
        """
        if not self.cv_collection:
            logger.warning("ChromaDB not initialized")
            return False
        
        try:
            # Create text for embedding
            cv_text = self._cv_to_embedding_text(cv_data)
            
            # Generate embedding
            embedding = await self._generate_embedding(cv_text)
            
            # Store with metadata
            self.cv_collection.upsert(
                ids=[cv_id],
                embeddings=[embedding] if embedding else None,
                documents=[cv_text],
                metadatas=[{
                    "job_url": job_url,
                    "created_at": datetime.now().isoformat(),
                    "ats_score": scores.get("ats", {}).get("overall_score", 0),
                    "job_fit_score": scores.get("job_fit", {}).get("overall_score", 0),
                    "cv_json": json.dumps(cv_data),
                }],
            )
            
            logger.info(f"Stored CV: {cv_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store CV: {e}")
            return False
    
    async def store_job(
        self,
        job_id: str,
        job_data: Dict[str, Any],
    ) -> bool:
        """Store a job posting in the vector store.
        
        Args:
            job_id: Unique job identifier
            job_data: Job data dictionary
            
        Returns:
            True if successful
        """
        if not self.job_collection:
            logger.warning("ChromaDB not initialized")
            return False
        
        try:
            # Create text for embedding
            job_text = self._job_to_embedding_text(job_data)
            
            # Generate embedding
            embedding = await self._generate_embedding(job_text)
            
            # Store with metadata
            self.job_collection.upsert(
                ids=[job_id],
                embeddings=[embedding] if embedding else None,
                documents=[job_text],
                metadatas=[{
                    "url": job_data.get("url", ""),
                    "title": job_data.get("title", ""),
                    "company": job_data.get("company", ""),
                    "stored_at": datetime.now().isoformat(),
                    "job_json": json.dumps(job_data),
                }],
            )
            
            logger.info(f"Stored job: {job_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store job: {e}")
            return False
    
    async def find_similar_cvs(
        self,
        job_description: str,
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """Find CVs similar to a job description.
        
        Args:
            job_description: Job description text
            limit: Maximum results to return
            
        Returns:
            List of similar CVs with metadata
        """
        if not self.cv_collection:
            return []
        
        try:
            # Generate embedding for job
            embedding = await self._generate_embedding(job_description)
            
            if not embedding:
                return []
            
            # Query for similar CVs
            results = self.cv_collection.query(
                query_embeddings=[embedding],
                n_results=limit,
                include=["metadatas", "documents"],
            )
            
            # Parse results
            cvs = []
            if results["metadatas"] and results["metadatas"][0]:
                for metadata in results["metadatas"][0]:
                    try:
                        cv_data = json.loads(metadata.get("cv_json", "{}"))
                        cvs.append({
                            "cv_data": cv_data,
                            "job_url": metadata.get("job_url", ""),
                            "ats_score": metadata.get("ats_score", 0),
                            "job_fit_score": metadata.get("job_fit_score", 0),
                        })
                    except json.JSONDecodeError:
                        continue
            
            return cvs
            
        except Exception as e:
            logger.error(f"Failed to find similar CVs: {e}")
            return []
    
    async def get_cv_history(self, job_url: str) -> List[Dict[str, Any]]:
        """Get CV history for a specific job URL.
        
        Args:
            job_url: Job posting URL
            
        Returns:
            List of historical CVs for this job
        """
        if not self.cv_collection:
            return []
        
        try:
            results = self.cv_collection.get(
                where={"job_url": job_url},
                include=["metadatas"],
            )
            
            history = []
            if results["metadatas"]:
                for metadata in results["metadatas"]:
                    try:
                        cv_data = json.loads(metadata.get("cv_json", "{}"))
                        history.append({
                            "cv_data": cv_data,
                            "created_at": metadata.get("created_at", ""),
                            "ats_score": metadata.get("ats_score", 0),
                            "job_fit_score": metadata.get("job_fit_score", 0),
                        })
                    except json.JSONDecodeError:
                        continue
            
            return sorted(history, key=lambda x: x.get("created_at", ""), reverse=True)
            
        except Exception as e:
            logger.error(f"Failed to get CV history: {e}")
            return []
    
    def _cv_to_embedding_text(self, cv_data: Dict[str, Any]) -> str:
        """Convert CV data to text for embedding."""
        parts = []
        
        personal = cv_data.get("personal_info", {})
        parts.append(f"Name: {personal.get('name', '')}")
        
        if cv_data.get("summary"):
            parts.append(f"Summary: {cv_data['summary']}")
        
        for exp in cv_data.get("experience", []):
            parts.append(f"Role: {exp.get('role', '')} at {exp.get('company', '')}")
            parts.append(f"Achievements: {' '.join(exp.get('achievements', []))}")
            parts.append(f"Technologies: {', '.join(exp.get('technologies', []))}")
        
        parts.append(f"Skills: {', '.join(cv_data.get('skills', []))}")
        
        return "\n".join(parts)
    
    def _job_to_embedding_text(self, job_data: Dict[str, Any]) -> str:
        """Convert job data to text for embedding."""
        parts = [
            f"Title: {job_data.get('title', '')}",
            f"Company: {job_data.get('company', '')}",
            f"Description: {job_data.get('description', '')}",
            f"Requirements: {' '.join(job_data.get('requirements', []))}",
        ]
        return "\n".join(parts)
    
    async def _generate_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding for text.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector or None
        """
        if not self.provider_manager:
            return None
        
        try:
            return await self.provider_manager.embed(text)
        except Exception as e:
            logger.warning(f"Embedding generation failed: {e}")
            return None
    
    async def close(self) -> None:
        """Close ChromaDB connection."""
        self.client = None
        logger.debug("ChromaDB connection closed")
