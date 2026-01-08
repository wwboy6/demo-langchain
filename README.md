# Demo of langchain

## Usage
Use uvicorn to run this up
```
uvicorn app:app --reload
```
or
```
python -m uvicorn app:app --reload
```

API:
- /chat
  - With payload "content" as string, it response as LLM test response
