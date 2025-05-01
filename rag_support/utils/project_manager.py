#!/usr/bin/env python3
"""
Project management module for the LLM Platform.

Handles project organization, documents, chats, and artifacts for the RAG system.
"""

import os
import json
import shutil
import uuid
import time
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional, Union, Set

# Import from core modules
from core.logging import get_logger
from core.utils import timer

# Import from RAG modules
from rag.documents import Document, DocumentCollection
from rag.storage import FileSystemStorage
from rag.indexer import TfidfIndex
from rag.search import SearchEngine

# Get logger for this module
logger = get_logger("rag_support.project_manager")

# Import BASE_DIR from rag_support
try:
    from rag_support import BASE_DIR
except ImportError:
    # Fallback if the import fails
    import os

    SCRIPT_DIR = Path(__file__).resolve().parent
    BASE_DIR = SCRIPT_DIR.parent.parent
    # Use environment variable if available
    BASE_DIR = Path(os.environ.get("LLM_BASE_DIR", str(BASE_DIR)))

# Standard directory locations
PROJECTS_DIR = BASE_DIR / "rag_support" / "projects"


class ProjectManager:
    """
    Manages projects, documents, chats, and artifacts.

    Provides a unified interface for working with RAG components within projects.
    """

    def __init__(self):
        """Initialize project manager and ensure base directories exist"""
        self.projects_dir = PROJECTS_DIR
        self.projects_dir.mkdir(exist_ok=True, parents=True)

        # Cache for project metadata
        self.projects_cache = None
        self.last_cache_update = 0

        # Search engines for each project (project_id -> SearchEngine)
        self.search_engines = {}

        # Storage backends for each project (project_id -> FileSystemStorage)
        self.storage_backends = {}

        # Document collections for each project (project_id -> DocumentCollection)
        self.document_collections = {}

        logger.info(f"Project manager initialized with projects directory: {self.projects_dir}")

    def get_storage(self, project_id: str) -> FileSystemStorage:
        """
        Get or create a storage backend for a project.

        Args:
            project_id: Project ID

        Returns:
            FileSystemStorage instance for the project
        """
        if project_id not in self.storage_backends:
            documents_dir = self.projects_dir / project_id / "documents"
            self.storage_backends[project_id] = FileSystemStorage(documents_dir)

        return self.storage_backends[project_id]

    def get_search_engine(self, project_id: str) -> SearchEngine:
        """
        Get or create a search engine for a project.

        Args:
            project_id: Project ID

        Returns:
            SearchEngine instance for the project
        """
        if project_id not in self.search_engines:
            storage = self.get_storage(project_id)
            index = TfidfIndex()
            self.search_engines[project_id] = SearchEngine(index=index, storage=storage)

            # Index documents if the engine is new
            collection = self.get_document_collection(project_id)
            self.search_engines[project_id].index_collection(collection)

        return self.search_engines[project_id]

    def get_document_collection(self, project_id: str) -> DocumentCollection:
        """
        Get or create a document collection for a project.

        Args:
            project_id: Project ID

        Returns:
            DocumentCollection instance for the project
        """
        if project_id not in self.document_collections:
            storage = self.get_storage(project_id)
            self.document_collections[project_id] = storage.get_all_documents()

        return self.document_collections[project_id]

    @timer
    def create_project(self, name: str, description: str = "") -> str:
        """
        Create a new project and return its ID.

        Args:
            name: Project name
            description: Project description

        Returns:
            Project ID
        """
        # Generate a unique ID for the project
        project_id = str(uuid.uuid4())
        project_dir = self.projects_dir / project_id

        # Create project directory structure
        project_dir.mkdir(exist_ok=True)
        (project_dir / "chats").mkdir(exist_ok=True)
        (project_dir / "documents").mkdir(exist_ok=True)
        (project_dir / "artifacts").mkdir(exist_ok=True)

        # Create project metadata
        project_data = {
            "id": project_id,
            "name": name,
            "description": description,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "document_count": 0,
            "artifact_count": 0,
            "chat_count": 0,
        }

        # Write metadata to project.json
        with open(project_dir / "project.json", "w") as f:
            json.dump(project_data, f, indent=2)

        # Invalidate cache
        self.projects_cache = None

        logger.info(f"Created project '{name}' with ID {project_id}")
        return project_id

    @timer
    def get_projects(self, force_refresh=False) -> List[Dict[str, Any]]:
        """
        Get list of all projects with metadata.

        Args:
            force_refresh: Whether to force a cache refresh

        Returns:
            List of project metadata dictionaries
        """
        # Use cached result if available and recent
        current_time = time.time()
        if (
            not force_refresh
            and self.projects_cache is not None
            and current_time - self.last_cache_update < 30
        ):
            return self.projects_cache

        logger.debug(f"Loading projects from {self.projects_dir}")

        projects = []

        # Scan projects directory with improved error handling
        try:
            # First, check if directory exists
            if not self.projects_dir.exists():
                logger.warning(f"Projects directory does not exist: {self.projects_dir}")
                self.projects_dir.mkdir(exist_ok=True, parents=True)
                return []

            # Get all directories excluding hidden ones (those starting with .)
            project_dirs = [
                d for d in self.projects_dir.glob("*") if d.is_dir() and not d.name.startswith(".")
            ]
            logger.debug(f"Found {len(project_dirs)} potential project directories")

            for project_dir in project_dirs:
                project_file = project_dir / "project.json"

                if project_file.exists():
                    try:
                        with open(project_file, "r") as f:
                            project_data = json.load(f)

                        logger.debug(f"Loaded project: {project_data.get('name', 'Unknown')}")

                        # Count items to ensure accurate numbers
                        if (
                            "document_count" not in project_data
                            or "recalculate_counts" in project_data
                        ):
                            document_count = len(list((project_dir / "documents").glob("*.md")))
                            artifact_count = len(list((project_dir / "artifacts").glob("*")))
                            chat_count = len(list((project_dir / "chats").glob("*.json")))

                            project_data["document_count"] = document_count
                            project_data["artifact_count"] = artifact_count
                            project_data["chat_count"] = chat_count

                            # Update the project.json with correct counts
                            with open(project_file, "w") as f:
                                json.dump(project_data, f, indent=2)

                        projects.append(project_data)
                    except Exception as e:
                        logger.error(
                            f"Error reading project {project_dir.name}: {e}", exc_info=True
                        )
                else:
                    logger.warning(f"Project file does not exist: {project_file}")
        except Exception as e:
            logger.error(f"Error scanning projects directory: {e}", exc_info=True)

        # Sort by updated_at (most recent first)
        projects.sort(key=lambda p: p.get("updated_at", ""), reverse=True)

        # Update cache
        self.projects_cache = projects
        self.last_cache_update = current_time

        return projects

    def get_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific project by ID.

        Args:
            project_id: ID of the project to get

        Returns:
            Project metadata dictionary if found, None otherwise
        """
        project_dir = self.projects_dir / project_id

        if not project_dir.exists() or not (project_dir / "project.json").exists():
            return None

        try:
            with open(project_dir / "project.json", "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error reading project {project_id}: {e}")
            return None

    def update_project(self, project_id: str, name: str = None, description: str = None) -> bool:
        """
        Update project metadata.

        Args:
            project_id: ID of the project to update
            name: New project name (optional)
            description: New project description (optional)

        Returns:
            True if the update was successful, False otherwise
        """
        project_dir = self.projects_dir / project_id
        project_file = project_dir / "project.json"

        if not project_file.exists():
            return False

        try:
            with open(project_file, "r") as f:
                project_data = json.load(f)

            if name is not None:
                project_data["name"] = name

            if description is not None:
                project_data["description"] = description

            project_data["updated_at"] = datetime.now().isoformat()

            with open(project_file, "w") as f:
                json.dump(project_data, f, indent=2)

            # Invalidate cache
            self.projects_cache = None

            logger.info(f"Updated project {project_id}")
            return True
        except Exception as e:
            logger.error(f"Error updating project {project_id}: {e}")
            return False

    def delete_project(self, project_id: str) -> bool:
        """
        Delete a project and all its contents.

        Args:
            project_id: ID of the project to delete

        Returns:
            True if the deletion was successful, False otherwise
        """
        project_dir = self.projects_dir / project_id

        if not project_dir.exists():
            return False

        try:
            # Remove from caches
            if project_id in self.storage_backends:
                del self.storage_backends[project_id]

            if project_id in self.search_engines:
                del self.search_engines[project_id]

            if project_id in self.document_collections:
                del self.document_collections[project_id]

            # Delete directory
            shutil.rmtree(project_dir)

            # Invalidate cache
            self.projects_cache = None

            logger.info(f"Deleted project {project_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting project {project_id}: {e}")
            return False

    @timer
    def add_document(
        self, project_id: str, title: str, content: str, tags: List[str] = None
    ) -> Optional[str]:
        """
        Add a document to a project.

        Args:
            project_id: ID of the project
            title: Document title
            content: Document content
            tags: List of tags for the document

        Returns:
            Document ID if the document was added successfully, None otherwise
        """
        try:
            # Create a document using the Document class
            document = Document.create(title=title, content=content, tags=tags or [])

            # Save the document using the storage backend
            storage = self.get_storage(project_id)
            success = storage.save_document(document)

            if not success:
                logger.error(f"Failed to save document to storage for project {project_id}")
                return None

            # Update document collection and index
            if project_id in self.document_collections:
                self.document_collections[project_id].add(document)

            if project_id in self.search_engines:
                self.search_engines[project_id].index_document(document)

            # Update project metadata
            self._update_project_counts(project_id)

            logger.info(f"Added document '{title}' with ID {document.id} to project {project_id}")
            return document.id
        except Exception as e:
            logger.error(f"Error adding document to project {project_id}: {e}", exc_info=True)
            return None

    def get_document(self, project_id: str, doc_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a document by ID.

        Args:
            project_id: ID of the project
            doc_id: ID of the document

        Returns:
            Document dictionary if found, None otherwise
        """
        try:
            # Get the document from storage
            storage = self.get_storage(project_id)
            document = storage.get_document(doc_id)

            if not document:
                return None

            # Convert to dictionary with expanded metadata
            result = document.to_dict()

            # Add computed fields
            result["preview"] = document.get_preview(200)
            result["token_count"] = document.get_token_count()

            return result
        except Exception as e:
            logger.error(f"Error getting document {doc_id} from project {project_id}: {e}")
            return None

    @timer
    def list_documents(self, project_id: str) -> List[Dict[str, Any]]:
        """
        List all documents in a project.

        Args:
            project_id: ID of the project

        Returns:
            List of document metadata dictionaries
        """
        try:
            storage = self.get_storage(project_id)
            documents = storage.list_documents()

            # Sort by updated_at (most recent first)
            documents.sort(key=lambda d: d.get("updated_at", ""), reverse=True)

            return documents
        except Exception as e:
            logger.error(f"Error listing documents for project {project_id}: {e}")
            return []

    def update_document(
        self,
        project_id: str,
        doc_id: str,
        title: str = None,
        content: str = None,
        tags: List[str] = None,
    ) -> bool:
        """
        Update a document.

        Args:
            project_id: ID of the project
            doc_id: ID of the document to update
            title: New document title (optional)
            content: New document content (optional)
            tags: New document tags (optional)

        Returns:
            True if the update was successful, False otherwise
        """
        try:
            # Get the document from storage
            storage = self.get_storage(project_id)
            document = storage.get_document(doc_id)

            if not document:
                logger.warning(f"Document {doc_id} not found in project {project_id}")
                return False

            # Update document properties
            update_kwargs = {}
            if title is not None:
                update_kwargs["title"] = title

            if content is not None:
                update_kwargs["content"] = content

            if tags is not None:
                update_kwargs["tags"] = tags

            # Apply updates
            document.update(**update_kwargs)

            # Save back to storage
            success = storage.save_document(document)

            if not success:
                logger.error(f"Failed to save updated document {doc_id} to storage")
                return False

            # Update index if needed
            if project_id in self.search_engines and (
                content is not None or title is not None or tags is not None
            ):
                # Remove old document from index and add updated version
                self.search_engines[project_id].index.remove_document(doc_id)
                self.search_engines[project_id].index_document(document)

            logger.info(f"Updated document {doc_id} in project {project_id}")
            return True
        except Exception as e:
            logger.error(f"Error updating document {doc_id} in project {project_id}: {e}")
            return False

    def delete_document(self, project_id: str, doc_id: str) -> bool:
        """
        Delete a document.

        Args:
            project_id: ID of the project
            doc_id: ID of the document to delete

        Returns:
            True if the deletion was successful, False otherwise
        """
        try:
            # Delete from storage
            storage = self.get_storage(project_id)
            success = storage.delete_document(doc_id)

            if not success:
                logger.warning(f"Failed to delete document {doc_id} from storage")
                return False

            # Remove from collection if exists
            if project_id in self.document_collections:
                self.document_collections[project_id].remove(doc_id)

            # Remove from index if exists
            if project_id in self.search_engines:
                self.search_engines[project_id].index.remove_document(doc_id)

            # Update project metadata
            self._update_project_counts(project_id)

            logger.info(f"Deleted document {doc_id} from project {project_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting document {doc_id} from project {project_id}: {e}")
            return False

    @timer
    def search_documents(
        self, project_id: str, query: str, tags: List[str] = None, max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search documents in a project.

        Args:
            project_id: ID of the project
            query: Search query
            tags: List of tags to filter by
            max_results: Maximum number of results to return

        Returns:
            List of document metadata dictionaries matching the search
        """
        try:
            # If no query and no tags, just list all documents
            if not query and not tags:
                return self.list_documents(project_id)

            # Get search engine for the project
            search_engine = self.get_search_engine(project_id)

            # Perform search
            search_results = search_engine.search(query, max_results=max_results)

            # Filter by tags if needed
            if tags:
                filtered_results = []
                for result in search_results:
                    document = result.document
                    if document.has_tags(tags):
                        filtered_results.append(result)
                search_results = filtered_results

            # Convert to dictionaries
            results = []
            for result in search_results:
                document = result.document

                # Create result dictionary
                # Handle both Document objects and dictionaries
                if hasattr(document, 'id'):
                    # Document object
                    doc_dict = {
                        "id": document.id,
                        "title": document.title,
                        "preview": document.get_preview(200),
                        "created_at": document.created_at,
                        "updated_at": document.updated_at,
                        "tags": document.tags,
                        "score": result.score,
                    }
                else:
                    # Dictionary (string) document or SearchResult object
                    # For SearchResult object, try to get ID from document attribute
                    if hasattr(result, 'document') and hasattr(result.document, 'id'):
                        doc_id = result.document.id
                    elif hasattr(result, 'document_id'):
                        doc_id = result.document_id
                    else:
                        doc_id = str(uuid.uuid4())
                    
                    # Handle different document types (dict, string, or other)
                    if isinstance(document, dict):
                        # Dictionary document
                        doc_dict = {
                            "id": doc_id,
                            "title": document.get("title", "Untitled"),
                            "preview": document.get("content", "")[:200] + "..." if document.get("content") else "",
                            "created_at": document.get("created_at", ""),
                            "updated_at": document.get("updated_at", ""),
                            "tags": document.get("tags", []),
                            "score": result.score,
                        }
                    elif isinstance(document, str):
                        # String document
                        doc_dict = {
                            "id": doc_id,
                            "title": "Untitled",
                            "preview": document[:200] + "..." if document else "",
                            "created_at": "",
                            "updated_at": "",
                            "tags": [],
                            "score": result.score,
                        }
                    else:
                        # Other object type, try to access attributes directly
                        doc_dict = {
                            "id": doc_id,
                            "title": getattr(document, "title", "Untitled"),
                            "preview": str(getattr(document, "content", ""))[:200] + "..." if hasattr(document, "content") else "",
                            "created_at": getattr(document, "created_at", ""),
                            "updated_at": getattr(document, "updated_at", ""),
                            "tags": getattr(document, "tags", []),
                            "score": result.score,
                        }

                results.append(doc_dict)

            return results
        except Exception as e:
            logger.error(f"Error searching documents in project {project_id}: {e}", exc_info=True)
            return []

    def add_chat(self, project_id: str, title: str = None) -> Optional[str]:
        """
        Create a new chat in a project.

        Args:
            project_id: ID of the project
            title: Chat title

        Returns:
            Chat ID if the chat was created successfully, None otherwise
        """
        project_dir = self.projects_dir / project_id
        chats_dir = project_dir / "chats"

        if not chats_dir.exists():
            return None

        try:
            # Generate chat ID
            chat_id = str(uuid.uuid4())

            # Create chat data
            chat_data = {
                "id": chat_id,
                "title": title or f"Chat {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "messages": [],
            }

            # Write to file
            with open(chats_dir / f"{chat_id}.json", "w") as f:
                json.dump(chat_data, f, indent=2)

            # Update project metadata
            self._update_project_counts(project_id)

            logger.info(f"Created chat '{title}' with ID {chat_id} in project {project_id}")
            return chat_id
        except Exception as e:
            logger.error(f"Error creating chat in project {project_id}: {e}")
            return None

    def get_chat(self, project_id: str, chat_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a chat by ID.

        Args:
            project_id: ID of the project
            chat_id: ID of the chat

        Returns:
            Chat dictionary if found, None otherwise
        """
        chat_path = self.projects_dir / project_id / "chats" / f"{chat_id}.json"

        if not chat_path.exists():
            return None

        try:
            with open(chat_path, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error reading chat {chat_id}: {e}")
            return None

    def list_chats(self, project_id: str) -> List[Dict[str, Any]]:
        """
        List all chats in a project.

        Args:
            project_id: ID of the project

        Returns:
            List of chat metadata dictionaries
        """
        chats_dir = self.projects_dir / project_id / "chats"

        if not chats_dir.exists():
            return []

        chats = []
        for chat_path in chats_dir.glob("*.json"):
            try:
                with open(chat_path, "r") as f:
                    chat_data = json.load(f)

                # Only include minimal information
                chats.append(
                    {
                        "id": chat_data.get("id", chat_path.stem),
                        "title": chat_data.get("title", chat_path.stem),
                        "created_at": chat_data.get("created_at", ""),
                        "updated_at": chat_data.get("updated_at", ""),
                        "message_count": len(chat_data.get("messages", [])),
                    }
                )
            except Exception as e:
                logger.error(f"Error reading chat {chat_path.name}: {e}")

        # Sort by updated_at (most recent first)
        chats.sort(key=lambda c: c.get("updated_at", ""), reverse=True)

        return chats

    def add_message(
        self, project_id: str, chat_id: str, role: str, content: str, context_docs: List[str] = None
    ) -> bool:
        """
        Add a message to a chat.

        Args:
            project_id: ID of the project
            chat_id: ID of the chat
            role: Message role (user, assistant, system)
            content: Message content
            context_docs: List of document IDs used as context

        Returns:
            True if the message was added successfully, False otherwise
        """
        chat_path = self.projects_dir / project_id / "chats" / f"{chat_id}.json"

        if not chat_path.exists():
            return False

        try:
            # Read existing chat
            with open(chat_path, "r") as f:
                chat_data = json.load(f)

            # Create message
            message = {
                "id": str(uuid.uuid4()),
                "role": role,
                "content": content,
                "timestamp": datetime.now().isoformat(),
            }

            # Add context document references if provided
            if context_docs:
                message["context_docs"] = context_docs

            # Add message to chat
            chat_data["messages"].append(message)
            chat_data["updated_at"] = datetime.now().isoformat()

            # Update title if this is the first user message
            if role == "user" and len(chat_data["messages"]) <= 2:
                # Use the first ~30 chars of the first user message as title
                chat_data["title"] = (content[:30] + "...") if len(content) > 30 else content

            # Write back to file
            with open(chat_path, "w") as f:
                json.dump(chat_data, f, indent=2)

            logger.info(f"Added {role} message to chat {chat_id} in project {project_id}")
            return True
        except Exception as e:
            logger.error(f"Error adding message to chat {chat_id}: {e}")
            return False

    def delete_chat(self, project_id: str, chat_id: str) -> bool:
        """
        Delete a chat.

        Args:
            project_id: ID of the project
            chat_id: ID of the chat to delete

        Returns:
            True if the deletion was successful, False otherwise
        """
        chat_path = self.projects_dir / project_id / "chats" / f"{chat_id}.json"

        if not chat_path.exists():
            return False

        try:
            os.remove(chat_path)

            # Update project metadata
            self._update_project_counts(project_id)

            logger.info(f"Deleted chat {chat_id} from project {project_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting chat {chat_id}: {e}")
            return False

    def save_artifact(
        self, project_id: str, content: str, title: str = None, file_ext: str = "md"
    ) -> Optional[str]:
        """
        Save an artifact file.

        Args:
            project_id: ID of the project
            content: Artifact content
            title: Artifact title
            file_ext: File extension for the artifact

        Returns:
            Artifact ID if the artifact was saved successfully, None otherwise
        """
        artifacts_dir = self.projects_dir / project_id / "artifacts"

        if not artifacts_dir.exists():
            return None

        try:
            # Generate artifact ID and filename
            artifact_id = str(uuid.uuid4())
            artifact_path = artifacts_dir / f"{artifact_id}.{file_ext}"

            # Create metadata
            metadata = {
                "id": artifact_id,
                "title": title or f"Artifact {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                "created_at": datetime.now().isoformat(),
                "file_type": file_ext,
            }

            # Create metadata file
            with open(artifacts_dir / f"{artifact_id}.json", "w") as f:
                json.dump(metadata, f, indent=2)

            # Write artifact content
            with open(artifact_path, "w") as f:
                f.write(content)

            # Update project metadata
            self._update_project_counts(project_id)

            logger.info(f"Saved artifact '{title}' with ID {artifact_id} in project {project_id}")
            return artifact_id
        except Exception as e:
            logger.error(f"Error saving artifact to project {project_id}: {e}")
            return None

    def get_artifact(self, project_id: str, artifact_id: str) -> Optional[Dict[str, Any]]:
        """
        Get an artifact by ID.

        Args:
            project_id: ID of the project
            artifact_id: ID of the artifact

        Returns:
            Artifact dictionary if found, None otherwise
        """
        artifacts_dir = self.projects_dir / project_id / "artifacts"
        metadata_path = artifacts_dir / f"{artifact_id}.json"

        if not metadata_path.exists():
            return None

        try:
            # Read metadata
            with open(metadata_path, "r") as f:
                metadata = json.load(f)

            # Determine artifact file path
            file_ext = metadata.get("file_type", "md")
            artifact_path = artifacts_dir / f"{artifact_id}.{file_ext}"

            # Read content if file exists
            content = ""
            if artifact_path.exists():
                with open(artifact_path, "r") as f:
                    content = f.read()

            return {**metadata, "content": content, "path": str(artifact_path)}
        except Exception as e:
            logger.error(f"Error reading artifact {artifact_id}: {e}")
            return None

    def list_artifacts(self, project_id: str) -> List[Dict[str, Any]]:
        """
        List all artifacts in a project.

        Args:
            project_id: ID of the project

        Returns:
            List of artifact metadata dictionaries
        """
        artifacts_dir = self.projects_dir / project_id / "artifacts"

        if not artifacts_dir.exists():
            return []

        artifacts = []
        for metadata_path in artifacts_dir.glob("*.json"):
            try:
                with open(metadata_path, "r") as f:
                    metadata = json.load(f)

                artifacts.append(metadata)
            except Exception as e:
                logger.error(f"Error reading artifact metadata {metadata_path.name}: {e}")

        # Sort by created_at (most recent first)
        artifacts.sort(key=lambda a: a.get("created_at", ""), reverse=True)

        return artifacts

    def delete_artifact(self, project_id: str, artifact_id: str) -> bool:
        """
        Delete an artifact.

        Args:
            project_id: ID of the project
            artifact_id: ID of the artifact to delete

        Returns:
            True if the deletion was successful, False otherwise
        """
        artifacts_dir = self.projects_dir / project_id / "artifacts"
        metadata_path = artifacts_dir / f"{artifact_id}.json"

        if not metadata_path.exists():
            return False

        try:
            # Read metadata to get file type
            with open(metadata_path, "r") as f:
                metadata = json.load(f)

            # Delete main artifact file
            file_ext = metadata.get("file_type", "md")
            artifact_path = artifacts_dir / f"{artifact_id}.{file_ext}"

            if artifact_path.exists():
                os.remove(artifact_path)

            # Delete metadata file
            os.remove(metadata_path)

            # Update project metadata
            self._update_project_counts(project_id)

            logger.info(f"Deleted artifact {artifact_id} from project {project_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting artifact {artifact_id}: {e}")
            return False

    def _update_project_counts(self, project_id: str) -> None:
        """
        Update document, artifact, and chat counts in project metadata.

        Args:
            project_id: ID of the project
        """
        project_dir = self.projects_dir / project_id
        project_file = project_dir / "project.json"

        if not project_file.exists():
            return

        try:
            with open(project_file, "r") as f:
                project_data = json.load(f)

            # Count items
            document_count = len(list((project_dir / "documents").glob("*.md")))
            artifact_count = len(list((project_dir / "artifacts").glob("*.json")))
            chat_count = len(list((project_dir / "chats").glob("*.json")))

            # Update counts and timestamp
            project_data["document_count"] = document_count
            project_data["artifact_count"] = artifact_count
            project_data["chat_count"] = chat_count
            project_data["updated_at"] = datetime.now().isoformat()

            # Write back to file
            with open(project_file, "w") as f:
                json.dump(project_data, f, indent=2)

            # Invalidate cache
            self.projects_cache = None

            logger.debug(
                f"Updated project counts for {project_id}: {document_count} documents, {chat_count} chats, {artifact_count} artifacts"
            )
        except Exception as e:
            logger.error(f"Error updating project counts for {project_id}: {e}")


# Create a default instance
project_manager = ProjectManager()

if __name__ == "__main__":
    # Simple test
    logger.info("Testing project manager...")

    # Create a test project
    project_id = project_manager.create_project("Test Project", "A test project")
    logger.info(f"Created project with ID: {project_id}")

    # Add a document
    doc_id = project_manager.add_document(
        project_id=project_id,
        title="Test Document",
        content="This is a test document for the RAG system.",
        tags=["test", "example"],
    )

    logger.info(f"Added document with ID: {doc_id}")

    # Test search
    results = project_manager.search_documents(project_id, "test")
    logger.info(f"Search results: {results}")

    # Test chat creation
    chat_id = project_manager.add_chat(project_id, "Test Chat")
    logger.info(f"Created chat with ID: {chat_id}")

    # Add messages to chat
    project_manager.add_message(project_id, chat_id, "user", "Hello, this is a test message.")
    project_manager.add_message(project_id, chat_id, "assistant", "This is a test response.")

    # Save an artifact
    artifact_id = project_manager.save_artifact(
        project_id=project_id,
        content="# Test Artifact\n\nThis is a test artifact.",
        title="Test Artifact",
    )

    logger.info(f"Saved artifact with ID: {artifact_id}")

    # List all projects
    projects = project_manager.get_projects()
    logger.info(f"All projects: {len(projects)}")
