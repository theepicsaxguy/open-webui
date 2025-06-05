# Git Ingest API

This document describes the API for ingesting a Git repository or local directory through the backend.
The implementation now relies on the **gitingest** library which provides robust parsing,
token estimation and better handling of different file encodings. Git operations are
executed asynchronously to avoid blocking the API server.

## Endpoint

`POST /api/v1/git-ingest/ingest`

### Request Body

```json
{
  "source": "<git url or local path>",
  "branch": "optional branch",
  "commit": "optional commit",
  "subpath": "optional subpath",
  "max_depth": 20,
  "ingest_file_content": true
}
```

### Response

Returns a JSON object with the following fields:

- `Summary` – textual summary of the ingestion result.
- `DirectoryTree` – directory tree representation.
- `FileContent` – concatenated file contents if requested.
- The `Summary` field also includes an estimated token count derived from the
  ingested files.

You can also use the **Git Ingest** workspace page to interactively run this endpoint and view the results with citations.

## Example

```bash
curl -X POST http://localhost:8080/api/v1/git-ingest/ingest \
  -H "Content-Type: application/json" \
  -d '{"source": "https://github.com/user/repo.git", "max_depth": 5}'
```

## Ingest into Knowledge

`POST /api/v1/git-ingest/knowledge`

### Request Body

```json
{
  "knowledge_id": "existing-knowledge-id", // optional
  "knowledge_name": "My Repo",           // required if knowledge_id not provided
  "description": "optional description",
  "source": "<git url or local path>",
  "branch": "optional branch",
  "commit": "optional commit",
  "subpath": "optional subpath",
  "max_depth": 20
}
```

The endpoint clones or reads the repository, stores each file as a document, and adds them to the specified knowledge base.
