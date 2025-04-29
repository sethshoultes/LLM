#!/usr/bin/env python3
# project_manager.py - Handles project organization for the RAG system

import os
import json
import shutil
import uuid
import time
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

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

PROJECTS_DIR = BASE_DIR / "rag_support" / "projects"

class ProjectManager:
    """Manages projects, documents, and artifacts"""
    
    def __init__(self):
        """Initialize project manager and ensure base directories exist"""
        self.projects_dir = PROJECTS_DIR
        self.projects_dir.mkdir(exist_ok=True, parents=True)
        
        # Cache for project metadata
        self.projects_cache = None
        self.last_cache_update = 0
    
    def create_project(self, name: str, description: str = "") -> str:
        """Create a new project and return its ID"""
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
            "chat_count": 0
        }
        
        # Write metadata to project.json
        with open(project_dir / "project.json", "w") as f:
            json.dump(project_data, f, indent=2)
        
        # Invalidate cache
        self.projects_cache = None
        
        return project_id
    
    def get_projects(self, force_refresh=False) -> List[Dict[str, Any]]:
        """Get list of all projects with metadata"""
        # Use cached result if available and recent
        current_time = time.time()
        if not force_refresh and self.projects_cache is not None and current_time - self.last_cache_update < 30:
            return self.projects_cache
        
        projects = []
        
        # Scan projects directory
        for project_dir in self.projects_dir.glob("*"):
            if project_dir.is_dir() and (project_dir / "project.json").exists():
                try:
                    with open(project_dir / "project.json", "r") as f:
                        project_data = json.load(f)
                        
                    # Count items to ensure accurate numbers
                    if "document_count" not in project_data or "recalculate_counts" in project_data:
                        document_count = len(list((project_dir / "documents").glob("*.md")))
                        artifact_count = len(list((project_dir / "artifacts").glob("*")))
                        chat_count = len(list((project_dir / "chats").glob("*.json")))
                        
                        project_data["document_count"] = document_count
                        project_data["artifact_count"] = artifact_count 
                        project_data["chat_count"] = chat_count
                        
                        # Update the project.json with correct counts
                        with open(project_dir / "project.json", "w") as f:
                            json.dump(project_data, f, indent=2)
                    
                    projects.append(project_data)
                except Exception as e:
                    print(f"Error reading project {project_dir.name}: {e}")
        
        # Sort by updated_at (most recent first)
        projects.sort(key=lambda p: p.get("updated_at", ""), reverse=True)
        
        # Update cache
        self.projects_cache = projects
        self.last_cache_update = current_time
        
        return projects
    
    def get_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific project by ID"""
        project_dir = self.projects_dir / project_id
        
        if not project_dir.exists() or not (project_dir / "project.json").exists():
            return None
        
        try:
            with open(project_dir / "project.json", "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error reading project {project_id}: {e}")
            return None
    
    def update_project(self, project_id: str, name: str = None, description: str = None) -> bool:
        """Update project metadata"""
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
            
            return True
        except Exception as e:
            print(f"Error updating project {project_id}: {e}")
            return False
    
    def delete_project(self, project_id: str) -> bool:
        """Delete a project and all its contents"""
        project_dir = self.projects_dir / project_id
        
        if not project_dir.exists():
            return False
        
        try:
            shutil.rmtree(project_dir)
            
            # Invalidate cache
            self.projects_cache = None
            
            return True
        except Exception as e:
            print(f"Error deleting project {project_id}: {e}")
            return False
    
    def add_document(self, project_id: str, title: str, content: str, 
                    tags: List[str] = None) -> Optional[str]:
        """Add a document to a project"""
        project_dir = self.projects_dir / project_id
        documents_dir = project_dir / "documents"
        
        if not documents_dir.exists():
            return None
        
        try:
            # Generate document ID and prepare metadata
            doc_id = str(uuid.uuid4())
            metadata = {
                "id": doc_id,
                "title": title,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "tags": tags or []
            }
            
            # Create content with metadata as frontmatter
            frontmatter = "---\n"
            for key, value in metadata.items():
                frontmatter += f"{key}: {json.dumps(value)}\n"
            frontmatter += "---\n\n"
            
            # Combine frontmatter and content
            full_content = frontmatter + content
            
            # Write to file
            with open(documents_dir / f"{doc_id}.md", "w") as f:
                f.write(full_content)
            
            # Update project metadata
            self._update_project_counts(project_id)
            
            return doc_id
        except Exception as e:
            print(f"Error adding document to project {project_id}: {e}")
            return None
    
    def get_document(self, project_id: str, doc_id: str) -> Optional[Dict[str, Any]]:
        """Get a document by ID"""
        project_dir = self.projects_dir / project_id
        doc_path = project_dir / "documents" / f"{doc_id}.md"
        
        if not doc_path.exists():
            return None
        
        try:
            with open(doc_path, "r") as f:
                content = f.read()
            
            # Parse frontmatter and content
            if content.startswith("---"):
                # Extract frontmatter
                _, frontmatter, markdown = content.split("---", 2)
                
                # Parse frontmatter
                metadata = {}
                for line in frontmatter.strip().split("\n"):
                    if ":" in line:
                        key, value = line.split(":", 1)
                        try:
                            metadata[key.strip()] = json.loads(value.strip())
                        except:
                            metadata[key.strip()] = value.strip()
                
                return {
                    "id": doc_id,
                    "content": markdown.strip(),
                    "metadata": metadata,
                    **metadata
                }
            else:
                # No frontmatter, return basic info
                return {
                    "id": doc_id,
                    "title": doc_id,
                    "content": content,
                    "created_at": datetime.fromtimestamp(doc_path.stat().st_ctime).isoformat(),
                    "updated_at": datetime.fromtimestamp(doc_path.stat().st_mtime).isoformat(),
                    "tags": []
                }
        except Exception as e:
            print(f"Error reading document {doc_id}: {e}")
            return None
    
    def list_documents(self, project_id: str) -> List[Dict[str, Any]]:
        """List all documents in a project"""
        project_dir = self.projects_dir / project_id
        documents_dir = project_dir / "documents"
        
        if not documents_dir.exists():
            return []
        
        documents = []
        for doc_path in documents_dir.glob("*.md"):
            try:
                doc_id = doc_path.stem
                document = self.get_document(project_id, doc_id)
                if document:
                    # Only include minimal information
                    documents.append({
                        "id": document.get("id", doc_id),
                        "title": document.get("title", doc_id),
                        "created_at": document.get("created_at", ""),
                        "updated_at": document.get("updated_at", ""),
                        "tags": document.get("tags", [])
                    })
            except Exception as e:
                print(f"Error reading document {doc_path.name}: {e}")
        
        # Sort by updated_at (most recent first)
        documents.sort(key=lambda d: d.get("updated_at", ""), reverse=True)
        
        return documents
    
    def update_document(self, project_id: str, doc_id: str, 
                       title: str = None, content: str = None, 
                       tags: List[str] = None) -> bool:
        """Update a document"""
        # Get existing document
        document = self.get_document(project_id, doc_id)
        if not document:
            return False
        
        try:
            # Update metadata
            metadata = document.get("metadata", {})
            
            if title is not None:
                metadata["title"] = title
            
            if tags is not None:
                metadata["tags"] = tags
            
            metadata["updated_at"] = datetime.now().isoformat()
            
            # Generate frontmatter
            frontmatter = "---\n"
            for key, value in metadata.items():
                frontmatter += f"{key}: {json.dumps(value)}\n"
            frontmatter += "---\n\n"
            
            # Combine with new or existing content
            full_content = frontmatter + (content if content is not None else document.get("content", ""))
            
            # Write to file
            doc_path = self.projects_dir / project_id / "documents" / f"{doc_id}.md"
            with open(doc_path, "w") as f:
                f.write(full_content)
            
            return True
        except Exception as e:
            print(f"Error updating document {doc_id}: {e}")
            return False
    
    def delete_document(self, project_id: str, doc_id: str) -> bool:
        """Delete a document"""
        doc_path = self.projects_dir / project_id / "documents" / f"{doc_id}.md"
        
        if not doc_path.exists():
            return False
        
        try:
            os.remove(doc_path)
            
            # Update project metadata
            self._update_project_counts(project_id)
            
            return True
        except Exception as e:
            print(f"Error deleting document {doc_id}: {e}")
            return False
    
    def search_documents(self, project_id: str, query: str, 
                        tags: List[str] = None) -> List[Dict[str, Any]]:
        """Search documents in a project"""
        if not query and not tags:
            return self.list_documents(project_id)
        
        results = []
        for doc_path in (self.projects_dir / project_id / "documents").glob("*.md"):
            try:
                doc_id = doc_path.stem
                document = self.get_document(project_id, doc_id)
                
                if not document:
                    continue
                
                # Check if document matches the query
                matches_query = False
                if query:
                    query_lower = query.lower()
                    content_lower = document.get("content", "").lower()
                    title_lower = document.get("title", "").lower()
                    
                    if query_lower in content_lower or query_lower in title_lower:
                        matches_query = True
                else:
                    # If no query, consider it a match
                    matches_query = True
                
                # Check if document has the required tags
                matches_tags = False
                if not tags:
                    # If no tags filter, consider it a match
                    matches_tags = True
                else:
                    doc_tags = set(document.get("tags", []))
                    if doc_tags and all(tag in doc_tags for tag in tags):
                        matches_tags = True
                
                # Add to results if both conditions are met
                if matches_query and matches_tags:
                    # Only include minimal information
                    results.append({
                        "id": document.get("id", doc_id),
                        "title": document.get("title", doc_id),
                        "preview": document.get("content", "")[:200] + "..." if len(document.get("content", "")) > 200 else document.get("content", ""),
                        "created_at": document.get("created_at", ""),
                        "updated_at": document.get("updated_at", ""),
                        "tags": document.get("tags", [])
                    })
            except Exception as e:
                print(f"Error searching document {doc_path.name}: {e}")
        
        # Sort by updated_at (most recent first)
        results.sort(key=lambda d: d.get("updated_at", ""), reverse=True)
        
        return results
    
    def add_chat(self, project_id: str, title: str = None) -> Optional[str]:
        """Create a new chat in a project"""
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
                "messages": []
            }
            
            # Write to file
            with open(chats_dir / f"{chat_id}.json", "w") as f:
                json.dump(chat_data, f, indent=2)
            
            # Update project metadata
            self._update_project_counts(project_id)
            
            return chat_id
        except Exception as e:
            print(f"Error creating chat in project {project_id}: {e}")
            return None
    
    def get_chat(self, project_id: str, chat_id: str) -> Optional[Dict[str, Any]]:
        """Get a chat by ID"""
        chat_path = self.projects_dir / project_id / "chats" / f"{chat_id}.json"
        
        if not chat_path.exists():
            return None
        
        try:
            with open(chat_path, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error reading chat {chat_id}: {e}")
            return None
    
    def list_chats(self, project_id: str) -> List[Dict[str, Any]]:
        """List all chats in a project"""
        chats_dir = self.projects_dir / project_id / "chats"
        
        if not chats_dir.exists():
            return []
        
        chats = []
        for chat_path in chats_dir.glob("*.json"):
            try:
                with open(chat_path, "r") as f:
                    chat_data = json.load(f)
                
                # Only include minimal information
                chats.append({
                    "id": chat_data.get("id", chat_path.stem),
                    "title": chat_data.get("title", chat_path.stem),
                    "created_at": chat_data.get("created_at", ""),
                    "updated_at": chat_data.get("updated_at", ""),
                    "message_count": len(chat_data.get("messages", []))
                })
            except Exception as e:
                print(f"Error reading chat {chat_path.name}: {e}")
        
        # Sort by updated_at (most recent first)
        chats.sort(key=lambda c: c.get("updated_at", ""), reverse=True)
        
        return chats
    
    def add_message(self, project_id: str, chat_id: str, 
                   role: str, content: str,
                   context_docs: List[str] = None) -> bool:
        """Add a message to a chat"""
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
                "timestamp": datetime.now().isoformat()
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
            
            return True
        except Exception as e:
            print(f"Error adding message to chat {chat_id}: {e}")
            return False
    
    def delete_chat(self, project_id: str, chat_id: str) -> bool:
        """Delete a chat"""
        chat_path = self.projects_dir / project_id / "chats" / f"{chat_id}.json"
        
        if not chat_path.exists():
            return False
        
        try:
            os.remove(chat_path)
            
            # Update project metadata
            self._update_project_counts(project_id)
            
            return True
        except Exception as e:
            print(f"Error deleting chat {chat_id}: {e}")
            return False
    
    def save_artifact(self, project_id: str, content: str, 
                     title: str = None, file_ext: str = "md") -> Optional[str]:
        """Save an artifact file"""
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
                "file_type": file_ext
            }
            
            # Create metadata file
            with open(artifacts_dir / f"{artifact_id}.json", "w") as f:
                json.dump(metadata, f, indent=2)
            
            # Write artifact content
            with open(artifact_path, "w") as f:
                f.write(content)
            
            # Update project metadata
            self._update_project_counts(project_id)
            
            return artifact_id
        except Exception as e:
            print(f"Error saving artifact to project {project_id}: {e}")
            return None
    
    def get_artifact(self, project_id: str, artifact_id: str) -> Optional[Dict[str, Any]]:
        """Get an artifact by ID"""
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
            
            return {
                **metadata,
                "content": content,
                "path": str(artifact_path)
            }
        except Exception as e:
            print(f"Error reading artifact {artifact_id}: {e}")
            return None
    
    def list_artifacts(self, project_id: str) -> List[Dict[str, Any]]:
        """List all artifacts in a project"""
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
                print(f"Error reading artifact metadata {metadata_path.name}: {e}")
        
        # Sort by created_at (most recent first)
        artifacts.sort(key=lambda a: a.get("created_at", ""), reverse=True)
        
        return artifacts
    
    def delete_artifact(self, project_id: str, artifact_id: str) -> bool:
        """Delete an artifact"""
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
            
            return True
        except Exception as e:
            print(f"Error deleting artifact {artifact_id}: {e}")
            return False
    
    def _update_project_counts(self, project_id: str) -> None:
        """Update document, artifact, and chat counts in project metadata"""
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
        except Exception as e:
            print(f"Error updating project counts for {project_id}: {e}")

# Create a default instance
project_manager = ProjectManager()

if __name__ == "__main__":
    # Simple test
    print("Testing project manager...")
    
    # Create a test project
    project_id = project_manager.create_project("Test Project", "A test project")
    print(f"Created project with ID: {project_id}")
    
    # Add a document
    doc_id = project_manager.add_document(
        project_id=project_id,
        title="Test Document",
        content="This is a test document for the RAG system.",
        tags=["test", "example"]
    )
    
    print(f"Added document with ID: {doc_id}")
    
    # Test search
    results = project_manager.search_documents(project_id, "test")
    print(f"Search results: {results}")
    
    # Test chat creation
    chat_id = project_manager.add_chat(project_id, "Test Chat")
    print(f"Created chat with ID: {chat_id}")
    
    # Add messages to chat
    project_manager.add_message(project_id, chat_id, "user", "Hello, this is a test message.")
    project_manager.add_message(project_id, chat_id, "assistant", "This is a test response.")
    
    # Save an artifact
    artifact_id = project_manager.save_artifact(
        project_id=project_id,
        content="# Test Artifact\n\nThis is a test artifact.",
        title="Test Artifact"
    )
    
    print(f"Saved artifact with ID: {artifact_id}")
    
    # List all projects
    projects = project_manager.get_projects()
    print(f"All projects: {projects}")