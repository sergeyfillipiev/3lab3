from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from datetime import datetime
import os
import json
import uuid

app = FastAPI()

# Путь к папкам для хранения заметок и токенов
NOTES_DIR = "notes"
TOKENS_FILE = "tokens.json"

# Создаём папку для заметок, если её нет
os.makedirs(NOTES_DIR, exist_ok=True)

# Модель для текстовой заметки
class Note(BaseModel):
    text: str

# Модель ответа о времени создания/обновления
class NoteInfo(BaseModel):
    created_at: str
    updated_at: str

# Модель ответа с текстом заметки
class NoteContent(BaseModel):
    id: str
    text: str

# Авторизация через токен
def authenticate(token: str):
    if not os.path.exists(TOKENS_FILE):
        raise HTTPException(status_code=401, detail="Unauthorized")
    with open(TOKENS_FILE, "r") as f:
        tokens = json.load(f)
    if token not in tokens.values():
        raise HTTPException(status_code=401, detail="Invalid token")
    return True

# Генерация токенов для тестирования (однократно)
if not os.path.exists(TOKENS_FILE):
    with open(TOKENS_FILE, "w") as f:
        json.dump({"user": "test_token"}, f)

# API методы
@app.post("/notes/create", response_model=dict)
def create_note(note: Note, token: str):
    authenticate(token)
    note_id = str(uuid.uuid4())
    note_data = {
        "id": note_id,
        "text": note.text,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }
    with open(os.path.join(NOTES_DIR, f"{note_id}.json"), "w") as f:
        json.dump(note_data, f)
    return {"id": note_id}

@app.get("/notes/{note_id}", response_model=NoteContent)
def get_note(note_id: str, token: str):
    authenticate(token)
    file_path = os.path.join(NOTES_DIR, f"{note_id}.json")
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Note not found")
    with open(file_path, "r") as f:
        note = json.load(f)
    return NoteContent(id=note["id"], text=note["text"])

@app.get("/notes/info/{note_id}", response_model=NoteInfo)
def get_note_info(note_id: str, token: str):
    authenticate(token)
    file_path = os.path.join(NOTES_DIR, f"{note_id}.json")
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Note not found")
    with open(file_path, "r") as f:
        note = json.load(f)
    return NoteInfo(created_at=note["created_at"], updated_at=note["updated_at"])

@app.patch("/notes/update/{note_id}", response_model=dict)
def update_note(note_id: str, note: Note, token: str):
    authenticate(token)
    file_path = os.path.join(NOTES_DIR, f"{note_id}.json")
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Note not found")
    with open(file_path, "r") as f:
        note_data = json.load(f)
    note_data["text"] = note.text
    note_data["updated_at"] = datetime.utcnow().isoformat()
    with open(file_path, "w") as f:
        json.dump(note_data, f)
    return {"message": "Note updated successfully"}

@app.delete("/notes/delete/{note_id}", response_model=dict)
def delete_note(note_id: str, token: str):
    authenticate(token)
    file_path = os.path.join(NOTES_DIR, f"{note_id}.json")
    if os.path.exists(file_path):
        os.remove(file_path)
        return {"message": "Note deleted successfully"}
    raise HTTPException(status_code=404, detail="Note not found")

@app.get("/notes/list", response_model=dict)
def list_notes(token: str):
    authenticate(token)
    note_files = os.listdir(NOTES_DIR)
    note_ids = [note_file.split(".")[0] for note_file in note_files]
    return {idx: note_id for idx, note_id in enumerate(note_ids)}
