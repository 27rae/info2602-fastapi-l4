from fastapi import APIRouter, HTTPException, Depends, status
from sqlmodel import select
from app.database import SessionDep
from app.models import *
from app.auth import AuthDep

category_router = APIRouter(tags=["Category Management"], prefix="/category")

@category_router.post("/", response_model=CategoryResponse)
def create_category(
    db:SessionDep, 
    user:AuthDep, 
    text:str
):

    existing=db.exec(
        select(Category).where(
            Category.user_id==user.id, 
            Category.text==text
        )
    ).one_or_none()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Category with this text already exists",
        )
    
    category=Category(text=text, user_id=user.id)
    try:
        db.add(category)
        db.commit()
        db.refresh(category)
        return category
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"An error occurred while creating category: {str(e)}",
        )

@category_router.post("/{cat_id}/todo/{todo_id}", status_code=status.HTTP_200_OK)
def add_category_to_todo(
    cat_id: int, 
    todo_id: int, 
    db: SessionDep, 
    user: AuthDep
):
    todo=db.exec(
        select(Todo).where(Todo.id == todo_id, Todo.user_id == user.id)
    ).one_or_none()
    if not todo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Todo not found",
        )

    category=db.exec(
        select(Category).where(Category.id == cat_id, Category.user_id == user.id)
    ).one_or_none()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )
    
    existing = db.exec(
        select(TodoCategory).where(
            TodoCategory.todo_id == todo_id,
            TodoCategory.category_id == cat_id
        )
    ).one_or_none()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Category already assigned to this todo",
        )
    todo_category=TodoCategory(todo_id=todo_id, category_id=cat_id)
    try:
        db.add(todo_category)
        db.commit()
        return {"message": "Category added to todo successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"An error occurred: {str(e)}",
        )

@category_router.delete("/{cat_id}/todo/{todo_id}",status_code=status.HTTP_200_OK)
def remove_category_from_todo(
    cat_id: int,
    todo_id: int,
    db: SessionDep,
    user: AuthDep
):

    todo=db.exec(
        select(Todo).where(Todo.id == todo_id, Todo.user_id == user.id)
    ).one_or_none()
    if not todo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Todo not found",
        )
    
    category =db.exec(
        select(Category).where(Category.id == cat_id, Category.user_id == user.id)
    ).one_or_none()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )

    todo_category=db.exec(
        select(TodoCategory).where(
            TodoCategory.todo_id == todo_id,
            TodoCategory.category_id == cat_id
        )
    ).one_or_none()
    
    if not todo_category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not assigned to this todo",
        )
    
    try:
        db.delete(todo_category)
        db.commit()
        return {"message": "Category removed from todo successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"An error occurred: {str(e)}",
        )

@category_router.get("/{cat_id}/todos",response_model=list[TodoResponse])
def get_todos_for_category(
    cat_id: int,
    db: SessionDep,
    user: AuthDep
):

    category=db.exec(
        select(Category).where(Category.id==cat_id, Category.user_id == user.id)
    ).one_or_none()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )
    todos =db.exec(
        select(Todo)
        .join(TodoCategory, Todo.id == TodoCategory.todo_id)
        .where(
            TodoCategory.category_id== cat_id,
            Todo.user_id==user.id
        )
    ).all()
    
    return todos