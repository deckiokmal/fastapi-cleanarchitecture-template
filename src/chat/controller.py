from fastapi import APIRouter, status
from typing import List
from uuid import UUID

from ..database.core import DbSession
from . import  models
from . import service
from ..auth.service import CurrentUser

router = APIRouter(
    prefix="/chats",
    tags=["Chats"]
)

@router.post("/", response_model=models.Conversation, status_code=status.HTTP_201_CREATED)
def create_conversation(db: DbSession, conversation: models.ConversationCreate, current_user: CurrentUser):
    return service.create_conversation(current_user, db, conversation)


@router.get("/", response_model=List[models.Conversation])
def get_user_conversations(db: DbSession, current_user: CurrentUser):
    return service.get_user_conversations(current_user, db)


# @router.get("/{todo_id}", response_model=models.TodoResponse)
# def get_todo(db: DbSession, todo_id: UUID, current_user: CurrentUser):
#     return service.get_todo_by_id(current_user, db, todo_id)


# @router.put("/{todo_id}", response_model=models.TodoResponse)
# def update_todo(db: DbSession, todo_id: UUID, todo_update: models.TodoCreate, current_user: CurrentUser):
#     return service.update_todo(current_user, db, todo_id, todo_update)


# @router.put("/{todo_id}/complete", response_model=models.TodoResponse)
# def complete_todo(db: DbSession, todo_id: UUID, current_user: CurrentUser):
#     return service.complete_todo(current_user, db, todo_id)


# @router.delete("/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
# def delete_todo(db: DbSession, todo_id: UUID, current_user: CurrentUser):
#     service.delete_todo(current_user, db, todo_id)
