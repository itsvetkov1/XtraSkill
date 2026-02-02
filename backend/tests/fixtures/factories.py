"""Factory-boy factories for test data creation."""

from datetime import datetime
from uuid import uuid4

import factory
from pytest_factoryboy import register

from app.models import (
    User, OAuthProvider, Project, Document, Thread, Message, Artifact, ArtifactType
)


class BaseFactory(factory.Factory):
    """Base factory with common settings."""

    class Meta:
        abstract = True


@register
class UserFactory(factory.Factory):
    """Factory for User model."""

    class Meta:
        model = User

    id = factory.LazyFunction(lambda: str(uuid4()))
    email = factory.Faker("email")
    oauth_provider = OAuthProvider.GOOGLE
    oauth_id = factory.LazyFunction(lambda: f"google-{uuid4()}")
    display_name = factory.Faker("name")
    created_at = factory.LazyFunction(datetime.utcnow)
    updated_at = factory.LazyFunction(datetime.utcnow)


@register
class ProjectFactory(factory.Factory):
    """Factory for Project model."""

    class Meta:
        model = Project

    id = factory.LazyFunction(lambda: str(uuid4()))
    user_id = factory.LazyAttribute(lambda o: str(uuid4()))
    name = factory.Faker("catch_phrase")
    description = factory.Faker("paragraph")
    created_at = factory.LazyFunction(datetime.utcnow)
    updated_at = factory.LazyFunction(datetime.utcnow)


@register
class DocumentFactory(factory.Factory):
    """Factory for Document model."""

    class Meta:
        model = Document

    id = factory.LazyFunction(lambda: str(uuid4()))
    project_id = factory.LazyAttribute(lambda o: str(uuid4()))
    filename = factory.Faker("file_name", extension="md")
    content_encrypted = factory.LazyFunction(lambda: b"encrypted-content-placeholder")
    created_at = factory.LazyFunction(datetime.utcnow)


@register
class ThreadFactory(factory.Factory):
    """Factory for Thread model."""

    class Meta:
        model = Thread

    id = factory.LazyFunction(lambda: str(uuid4()))
    project_id = None  # Optional - set explicitly when needed
    user_id = factory.LazyAttribute(lambda o: str(uuid4()))
    title = factory.Faker("sentence", nb_words=4)
    model_provider = "anthropic"
    created_at = factory.LazyFunction(datetime.utcnow)
    updated_at = factory.LazyFunction(datetime.utcnow)
    last_activity_at = factory.LazyFunction(datetime.utcnow)


@register
class MessageFactory(factory.Factory):
    """Factory for Message model."""

    class Meta:
        model = Message

    id = factory.LazyFunction(lambda: str(uuid4()))
    thread_id = factory.LazyAttribute(lambda o: str(uuid4()))
    role = "user"
    content = factory.Faker("paragraph")
    created_at = factory.LazyFunction(datetime.utcnow)


@register
class ArtifactFactory(factory.Factory):
    """Factory for Artifact model."""

    class Meta:
        model = Artifact

    id = factory.LazyFunction(lambda: str(uuid4()))
    thread_id = factory.LazyAttribute(lambda o: str(uuid4()))
    artifact_type = ArtifactType.BRD
    title = factory.Faker("sentence", nb_words=4)
    content_markdown = factory.Faker("text", max_nb_chars=500)
    content_json = None
    created_at = factory.LazyFunction(datetime.utcnow)


# Helper for creating related objects
class UserWithProjectFactory(UserFactory):
    """User with an associated project."""

    @factory.post_generation
    def projects(self, create, extracted, **kwargs):
        if extracted:
            for project in extracted:
                project.user_id = self.id


class ProjectWithThreadFactory(ProjectFactory):
    """Project with an associated thread."""

    @factory.post_generation
    def threads(self, create, extracted, **kwargs):
        if extracted:
            for thread in extracted:
                thread.project_id = self.id
