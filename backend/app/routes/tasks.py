from flask.views import MethodView
from flask_smorest import Blueprint, abort
from marshmallow import Schema, fields, validate, EXCLUDE
from typing import Dict, Any
from app import store as task_store


# Marshmallow Schemas

class TaskSchema(Schema):
    """Schema representing a Task entity."""
    id = fields.Int(required=True, description="Task ID")
    title = fields.Str(required=True, description="Task title")
    completed = fields.Bool(required=True, description="Completion status")


class TaskCreateSchema(Schema):
    """Schema for creating a new task."""
    class Meta:
        unknown = EXCLUDE

    title = fields.Str(
        required=True,
        validate=validate.Length(min=1),
        description="Title for the new task",
    )


class TaskUpdateSchema(Schema):
    """Schema for updating an existing task fields."""
    class Meta:
        unknown = EXCLUDE

    title = fields.Str(validate=validate.Length(min=1), description="Updated title")
    completed = fields.Bool(description="Updated completion status")


class TaskListSchema(Schema):
    """Schema for a list of tasks."""
    tasks = fields.List(fields.Nested(TaskSchema), required=True, description="List of tasks")


# Flask-Smorest Blueprint
blp = Blueprint(
    "Tasks",
    "tasks",
    url_prefix="/api/tasks",
    description="Endpoints to manage to-do tasks",
)


@blp.route("/")
class TasksCollection(MethodView):
    """
    PUBLIC_INTERFACE
    get:
        List all tasks.
    post:
        Create a new task.
    """

    @blp.response(200, TaskListSchema)
    @blp.doc(summary="List tasks", description="Returns all tasks currently stored.")
    def get(self):
        """
        List tasks.
        Returns:
            JSON object containing list of tasks.
        """
        tasks = task_store.list_tasks()
        return {"tasks": tasks}

    @blp.arguments(TaskCreateSchema)
    @blp.response(201, TaskSchema)
    @blp.doc(summary="Create task", description="Create a new task with a given title.")
    def post(self, json_data: Dict[str, Any]):
        """
        Create a task.
        Args:
            json_data: Validated payload containing title.
        Returns:
            The created task.
        """
        try:
            task = task_store.create_task(json_data["title"])
        except ValueError as e:
            abort(400, message=str(e))
        return task


@blp.route("/<int:task_id>")
class TaskItem(MethodView):
    """
    PUBLIC_INTERFACE
    patch:
        Update fields for an existing task.
    delete:
        Delete an existing task.
    """

    @blp.arguments(TaskUpdateSchema)
    @blp.response(200, TaskSchema)
    @blp.doc(
        summary="Update task",
        description="Update one or more fields of a task: title and/or completed.",
        parameters=[{"in": "path", "name": "task_id", "schema": {"type": "integer"}, "required": True}],
    )
    def patch(self, json_data: Dict[str, Any], task_id: int):
        """
        Update a task.
        Args:
            json_data: Partial update payload.
            task_id: ID of the task to update.
        Returns:
            The updated task or 404 if not found.
        """
        existing = task_store.get_task(task_id)
        if not existing:
            abort(404, message="Task not found")

        try:
            updated = task_store.update_task(task_id, json_data or {})
        except ValueError as e:
            abort(400, message=str(e))

        if not updated:
            abort(404, message="Task not found")
        return updated

    @blp.response(204)
    @blp.doc(
        summary="Delete task",
        description="Delete a task by its ID.",
        parameters=[{"in": "path", "name": "task_id", "schema": {"type": "integer"}, "required": True}],
    )
    def delete(self, task_id: int):
        """
        Delete a task by id.
        Args:
            task_id: ID to delete.
        Returns:
            204 No Content on success, 404 if not found.
        """
        removed = task_store.delete_task(task_id)
        if not removed:
            abort(404, message="Task not found")
        return "", 204
