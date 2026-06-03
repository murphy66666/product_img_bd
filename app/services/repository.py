import json
from datetime import datetime
from uuid import uuid4

from pydantic import BaseModel
from sqlalchemy import bindparam, text
from sqlalchemy.exc import SQLAlchemyError

from app.db.mysql import mysql_sessions
from app.schemas.gallery import GeneratedImage
from app.schemas.generation import GenerationJob
from app.schemas.session import ChatMessage, ChatSession, SessionConfig
from app.schemas.template import SmartTemplate, SmartTemplateType
from app.services.clock import now_text
from app.services.providers.base import ProviderResult


class MySQLRepository:
    async def list_sessions(self, user_id: str, page: int, page_size: int) -> tuple[list[ChatSession], int]:
        offset = (page - 1) * page_size
        try:
            async for session in mysql_sessions.session():
                total_result = await session.execute(
                    text(
                        """
                        SELECT COUNT(*) AS total
                        FROM generation_sessions
                        WHERE user_id = :user_id AND deleted_at IS NULL
                        """
                    ),
                    {"user_id": user_id},
                )
                total = int(total_result.scalar_one() or 0)
                session_result = await session.execute(
                    text(
                        """
                        SELECT id, title, category, config, created_at
                        FROM generation_sessions s
                        WHERE s.user_id = :user_id AND s.deleted_at IS NULL
                        ORDER BY s.created_at DESC
                        LIMIT :limit OFFSET :offset
                        """
                    ),
                    {"user_id": user_id, "limit": page_size, "offset": offset},
                )
                sessions = [_session_from_row(row) for row in session_result.mappings().all()]
                if not sessions:
                    return [], total
                message_result = await session.execute(
                    text(
                        """
                        SELECT session_id, id, sender, message_type, text, payload, created_at
                        FROM generation_messages
                        WHERE session_id IN :session_ids
                        ORDER BY created_at ASC
                        """
                    ).bindparams(bindparam("session_ids", expanding=True)),
                    {"session_ids": [item.id for item in sessions]},
                )
                by_id = {item.id: item for item in sessions}
                for row in message_result.mappings().all():
                    by_id[row["session_id"]].messages.append(_message_from_row(row))
                return sessions, total
        except (SQLAlchemyError, OSError, RuntimeError, AttributeError):
            return [], 0
        return [], 0

    async def create_session(self, user_id: str, category: str, title: str | None = None) -> ChatSession:
        session_id = f"s-{uuid4().hex[:12]}"
        created = now_text()
        config = SessionConfig(aspectRatio="1:1" if category == "main" else "9:16")
        messages = _tutorial_messages(category, created)
        session = ChatSession(
            id=session_id,
            title=title or ("New main image session" if category == "main" else "New detail image session"),
            category=category,
            createdAt=created,
            config=config,
            messages=messages,
        )
        try:
            async for db in mysql_sessions.session():
                await db.execute(
                    text(
                        """
                        INSERT INTO generation_sessions (id, user_id, title, category, config)
                        VALUES (:id, :user_id, :title, :category, :config)
                        """
                    ),
                    {
                        "id": session.id,
                        "user_id": user_id,
                        "title": session.title,
                        "category": session.category,
                        "config": _json(config),
                    },
                )
                for message in messages:
                    await db.execute(
                        text(
                            """
                            INSERT INTO generation_messages (id, session_id, sender, message_type, text, payload)
                            VALUES (:id, :session_id, :sender, :message_type, :text, :payload)
                            """
                        ),
                        {
                            "id": message.id,
                            "session_id": session.id,
                            "sender": message.sender,
                            "message_type": message.type,
                            "text": message.text,
                            "payload": _json(message.payload),
                        },
                    )
                await db.commit()
        except (SQLAlchemyError, OSError, RuntimeError, AttributeError) as exc:
            raise RuntimeError("Failed to create session in database") from exc
        return session

    async def rename_session(self, user_id: str, session_id: str, title: str) -> ChatSession | None:
        try:
            async for db in mysql_sessions.session():
                result = await db.execute(
                    text(
                        """
                        UPDATE generation_sessions
                        SET title = :title
                        WHERE id = :session_id AND user_id = :user_id AND deleted_at IS NULL
                        """
                    ),
                    {"title": title, "session_id": session_id, "user_id": user_id},
                )
                await db.commit()
                if result.rowcount == 0:
                    return None
        except (SQLAlchemyError, OSError, RuntimeError, AttributeError):
            return None
        sessions, _total = await self.list_sessions(user_id, page=1, page_size=100)
        return next((item for item in sessions if item.id == session_id), None)

    async def delete_session(self, user_id: str, session_id: str) -> bool:
        try:
            async for db in mysql_sessions.session():
                result = await db.execute(
                    text(
                        """
                        UPDATE generation_sessions
                        SET deleted_at = CURRENT_TIMESTAMP
                        WHERE id = :session_id AND user_id = :user_id AND deleted_at IS NULL
                        """
                    ),
                    {"session_id": session_id, "user_id": user_id},
                )
                await db.commit()
                return result.rowcount > 0
        except (SQLAlchemyError, OSError, RuntimeError, AttributeError):
            return False
        return False

    async def list_messages(self, user_id: str, session_id: str) -> list[ChatMessage]:
        try:
            async for db in mysql_sessions.session():
                result = await db.execute(
                    text(
                        """
                        SELECT m.id, m.sender, m.message_type, m.text, m.payload, m.created_at
                        FROM generation_messages m
                        INNER JOIN generation_sessions s ON s.id = m.session_id
                        WHERE s.id = :session_id AND s.user_id = :user_id AND s.deleted_at IS NULL
                        ORDER BY m.created_at ASC
                        """
                    ),
                    {"session_id": session_id, "user_id": user_id},
                )
                return [_message_from_row(row) for row in result.mappings().all()]
        except (SQLAlchemyError, OSError, RuntimeError, AttributeError):
            return []
        return []

    async def add_message(self, user_id: str, session_id: str, message: ChatMessage) -> None:
        try:
            async for db in mysql_sessions.session():
                await db.execute(
                    text(
                        """
                        INSERT INTO generation_messages (id, session_id, sender, message_type, text, payload)
                        SELECT :id, s.id, :sender, :message_type, :text, :payload
                        FROM generation_sessions s
                        WHERE s.id = :session_id AND s.user_id = :user_id AND s.deleted_at IS NULL
                        """
                    ),
                    {
                        "id": message.id,
                        "session_id": session_id,
                        "user_id": user_id,
                        "sender": message.sender,
                        "message_type": message.type,
                        "text": message.text,
                        "payload": _json(message.payload),
                    },
                )
                await db.commit()
        except (SQLAlchemyError, OSError, RuntimeError, AttributeError):
            return

    async def add_gallery_images(
        self,
        user_id: str,
        job_id: str,
        session_id: str | None,
        provider: str,
        images: list[GeneratedImage],
        source_image_ids: list[str] | None = None,
    ) -> None:
        try:
            async for db in mysql_sessions.session():
                for image in images:
                    await db.execute(
                        text(
                            """
                            INSERT INTO generated_images (
                              id, job_id, user_id, session_id, url, original_url, prompt,
                              provider, model, resolution, aspect_ratio, category, tags,
                              remote_url, local_path, public_url, storage_date, file_name,
                              file_ext, mime_type, file_size, checksum_sha256, source_upload_ids
                            )
                            VALUES (
                              :id, :job_id, :user_id, :session_id, :url, :original_url, :prompt,
                              :provider, :model, :resolution, :aspect_ratio, :category, :tags,
                              :remote_url, :local_path, :public_url, :storage_date, :file_name,
                              :file_ext, :mime_type, :file_size, :checksum_sha256, :source_upload_ids
                            )
                            """
                        ),
                        {
                            "id": image.id,
                            "job_id": job_id,
                            "user_id": user_id,
                            "session_id": session_id,
                            "url": image.url,
                            "original_url": image.original_url,
                            "prompt": image.prompt,
                            "provider": provider,
                            "model": image.model,
                            "resolution": image.resolution,
                            "aspect_ratio": image.aspect_ratio,
                            "category": image.category,
                            "tags": _json(image.tags),
                            "remote_url": image.remote_url,
                            "local_path": image.local_path,
                            "public_url": image.public_url,
                            "storage_date": _storage_date(image.local_path),
                            "file_name": _file_name(image.local_path),
                            "file_ext": _file_ext(image.local_path),
                            "mime_type": image.mime_type,
                            "file_size": image.file_size,
                            "checksum_sha256": image.checksum_sha256,
                            "source_upload_ids": _json(source_image_ids or []),
                        },
                    )
                await db.commit()
        except (SQLAlchemyError, OSError, RuntimeError, AttributeError):
            return

    async def list_gallery(
        self,
        user_id: str,
        category: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[GeneratedImage], int]:
        offset = (page - 1) * page_size
        query = """
            SELECT id, COALESCE(public_url, url) AS url, remote_url, local_path, public_url,
                   mime_type, file_size, checksum_sha256,
                   original_url, prompt, model, resolution, aspect_ratio,
                   category, tags, created_at
            FROM generated_images
            WHERE user_id = :user_id AND deleted_at IS NULL
        """
        params = {"user_id": user_id}
        if category is not None:
            query += " AND category = :category"
            params["category"] = category
        count_query = """
            SELECT COUNT(*) AS total
            FROM generated_images
            WHERE user_id = :user_id AND deleted_at IS NULL
        """
        if category is not None:
            count_query += " AND category = :category"
        query += " ORDER BY created_at DESC LIMIT :limit OFFSET :offset"
        params["limit"] = page_size
        params["offset"] = offset
        try:
            async for db in mysql_sessions.session():
                total_result = await db.execute(text(count_query), {k: v for k, v in params.items() if k not in {"limit", "offset"}})
                result = await db.execute(text(query), params)
                return [_image_from_row(row) for row in result.mappings().all()], int(total_result.scalar_one() or 0)
        except (SQLAlchemyError, OSError, RuntimeError, AttributeError):
            return [], 0
        return [], 0

    async def delete_gallery_image(self, user_id: str, image_id: str) -> bool:
        try:
            async for db in mysql_sessions.session():
                result = await db.execute(
                    text(
                        """
                        UPDATE generated_images
                        SET deleted_at = CURRENT_TIMESTAMP
                        WHERE id = :image_id AND user_id = :user_id AND deleted_at IS NULL
                        """
                    ),
                    {"image_id": image_id, "user_id": user_id},
                )
                await db.commit()
                return result.rowcount > 0
        except (SQLAlchemyError, OSError, RuntimeError, AttributeError):
            return False
        return False

    async def list_smart_templates(self, template_type: SmartTemplateType | None = None) -> list[SmartTemplate]:
        query = """
            SELECT id, name, image_url, prompt, model, aspect_ratio,
                   resolution, quantity, type
            FROM smart_templates
            WHERE is_enabled = 1
        """
        params: dict[str, object] = {}
        if template_type is not None:
            query += " AND type = :type"
            params["type"] = template_type
        query += " ORDER BY sort_order ASC, created_at DESC"
        try:
            async for db in mysql_sessions.session():
                result = await db.execute(text(query), params)
                return [_smart_template_from_row(row) for row in result.mappings().all()]
        except (SQLAlchemyError, OSError, RuntimeError, AttributeError) as exc:
            raise RuntimeError("Failed to list smart templates from database") from exc
        return []

    async def save_job(self, user_id: str, job: GenerationJob, session_id: str | None) -> None:
        try:
            async for db in mysql_sessions.session():
                await db.execute(
                    text(
                        """
                        INSERT INTO generation_jobs (
                          id, user_id, session_id, provider, model, category, status,
                          aspect_ratio, resolution, quantity, prompt, source_image_url, request_payload,
                          provider_endpoint, provider_request_payload, size, quality, output_format,
                          stream, requested_count, returned_count, source_upload_ids,
                          error_code, error_message
                        )
                        VALUES (
                          :id, :user_id, :session_id, :provider, :model, :category, :status,
                          :aspect_ratio, :resolution, :quantity, :prompt, :source_image_url, :request_payload,
                          :provider_endpoint, :provider_request_payload, :size, :quality, :output_format,
                          :stream, :requested_count, :returned_count, :source_upload_ids,
                          :error_code, :error_message
                        )
                        """
                    ),
                    {
                        "id": job.id,
                        "user_id": user_id,
                        "session_id": session_id,
                        "provider": job.provider,
                        "model": job.model,
                        "category": job.category,
                        "status": job.status,
                        "aspect_ratio": job.aspect_ratio,
                        "resolution": job.resolution,
                        "quantity": job.quantity,
                        "prompt": job.prompt,
                        "source_image_url": job.source_image_url,
                        "request_payload": _json(job.model_dump(mode="json", by_alias=True)),
                        "provider_endpoint": "/images/edits" if job.model == "gpt-image-2" else None,
                        "provider_request_payload": _json(job.model_dump(mode="json", by_alias=True)),
                        "size": job.size,
                        "quality": job.quality,
                        "output_format": job.output_format,
                        "stream": job.stream,
                        "requested_count": job.requested_count,
                        "returned_count": job.returned_count,
                        "source_upload_ids": _json(job.source_image_ids),
                        "error_code": job.error_code,
                        "error_message": job.error_message,
                    },
                )
                await db.commit()
        except (SQLAlchemyError, OSError, RuntimeError, AttributeError):
            return

    async def update_job_result(
        self,
        *,
        user_id: str,
        job_id: str,
        status: str,
        provider_result: ProviderResult,
        requested_count: int,
        returned_count: int,
        source_image_ids: list[str],
        size: str,
        quality: str,
        output_format: str,
        stream: bool,
    ) -> None:
        try:
            async for db in mysql_sessions.session():
                await db.execute(
                    text(
                        """
                        UPDATE generation_jobs
                        SET status = :status,
                            provider_endpoint = :provider_endpoint,
                            provider_request_payload = :provider_request_payload,
                            provider_response_payload = :provider_response_payload,
                            provider_created = :provider_created,
                            size = :size,
                            quality = :quality,
                            output_format = :output_format,
                            stream = :stream,
                            requested_count = :requested_count,
                            returned_count = :returned_count,
                            source_upload_ids = :source_upload_ids,
                            total_tokens = :total_tokens,
                            input_tokens = :input_tokens,
                            output_tokens = :output_tokens,
                            input_text_tokens = :input_text_tokens,
                            input_image_tokens = :input_image_tokens
                        WHERE id = :job_id AND user_id = :user_id
                        """
                    ),
                    {
                        "status": status,
                        "provider_endpoint": provider_result.endpoint,
                        "provider_request_payload": _json(provider_result.request_payload or {}),
                        "provider_response_payload": _json(provider_result.response_payload or {}),
                        "provider_created": provider_result.provider_created,
                        "size": size,
                        "quality": quality,
                        "output_format": output_format,
                        "stream": stream,
                        "requested_count": requested_count,
                        "returned_count": returned_count,
                        "source_upload_ids": _json(source_image_ids),
                        "total_tokens": provider_result.total_tokens,
                        "input_tokens": provider_result.input_tokens,
                        "output_tokens": provider_result.output_tokens,
                        "input_text_tokens": provider_result.input_text_tokens,
                        "input_image_tokens": provider_result.input_image_tokens,
                        "job_id": job_id,
                        "user_id": user_id,
                    },
                )
                await db.commit()
        except (SQLAlchemyError, OSError, RuntimeError, AttributeError):
            await self.update_job_status(user_id, job_id, status)

    async def update_job_status(
        self,
        user_id: str,
        job_id: str,
        status: str,
        error_code: str | None = None,
        error_message: str | None = None,
    ) -> None:
        try:
            async for db in mysql_sessions.session():
                await db.execute(
                    text(
                        """
                        UPDATE generation_jobs
                        SET status = :status,
                            error_code = :error_code,
                            error_message = :error_message
                        WHERE id = :job_id AND user_id = :user_id
                        """
                    ),
                    {
                        "status": status,
                        "error_code": error_code,
                        "error_message": error_message,
                        "job_id": job_id,
                        "user_id": user_id,
                    },
                )
                await db.commit()
        except (SQLAlchemyError, OSError, RuntimeError, AttributeError):
            return

    async def get_job(self, user_id: str, job_id: str) -> GenerationJob | None:
        try:
            async for db in mysql_sessions.session():
                result = await db.execute(
                    text(
                        """
                        SELECT id, provider, model, category, status, aspect_ratio, resolution,
                               quantity, prompt, source_image_url, source_upload_ids, size,
                               quality, output_format, stream, requested_count, returned_count,
                               error_code, error_message,
                               created_at, updated_at
                        FROM generation_jobs
                        WHERE id = :job_id AND user_id = :user_id
                        LIMIT 1
                        """
                    ),
                    {"job_id": job_id, "user_id": user_id},
                )
                row = result.mappings().first()
                if row is None:
                    return None
                images = await self._list_job_images(user_id, job_id)
                return _job_from_row(row, images)
        except (SQLAlchemyError, OSError, RuntimeError, AttributeError):
            return None
        return None

    async def _list_job_images(self, user_id: str, job_id: str) -> list[GeneratedImage]:
        async for db in mysql_sessions.session():
            result = await db.execute(
                text(
                    """
                    SELECT id, COALESCE(public_url, url) AS url, remote_url, local_path, public_url,
                           mime_type, file_size, checksum_sha256,
                           original_url, prompt, model, resolution, aspect_ratio,
                           category, tags, created_at
                    FROM generated_images
                    WHERE user_id = :user_id AND job_id = :job_id AND deleted_at IS NULL
                    ORDER BY created_at ASC
                    """
                ),
                {"user_id": user_id, "job_id": job_id},
            )
            return [_image_from_row(row) for row in result.mappings().all()]
        return []


def _json(value: object) -> str:
    if isinstance(value, BaseModel):
        return value.model_dump_json(by_alias=True)
    return json.dumps(value, ensure_ascii=False)


def _loads(value: object, default: object) -> object:
    if value is None:
        return default
    if isinstance(value, str):
        return json.loads(value)
    return value


def _time_text(value: object) -> str:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, str):
        return value
    return now_text()


def _tutorial_messages(category: str, created_at: str) -> list[ChatMessage]:
    scene = "主图" if category == "main" else "详情图"
    ratio = "1:1" if category == "main" else "9:16"
    example_prompt = (
        "生成一张电商主图：白色保温杯放在浅灰背景上，柔和棚拍光，水珠质感，"
        "画面干净，高级感，适合淘宝首图。"
        if category == "main"
        else "生成一张商品详情图：展示白色保温杯的杯盖、防漏结构和保温层剖面，"
        "竖版排版，清晰卖点标注，现代电商风格。"
    )
    assistant_reply = (
        f"可以。建议使用 {ratio} 比例，提示词要同时说明商品、背景、光线、构图和用途。"
        "如果有参考图，先上传商品图，再把要保留的外观和要增强的氛围写清楚。"
    )
    return [
        ChatMessage(
            id=f"m-{uuid4().hex[:12]}",
            sender="assistant",
            text=f"欢迎进入{scene}生成教程。你可以先上传商品图，再告诉我想要的场景、风格和卖点。",
            createdAt=created_at,
            type="message",
            payload={"tutorial": True, "step": "intro"},
        ),
        ChatMessage(
            id=f"m-{uuid4().hex[:12]}",
            sender="user",
            text=example_prompt,
            createdAt=created_at,
            type="message",
            payload={"tutorial": True, "step": "example_prompt"},
        ),
        ChatMessage(
            id=f"m-{uuid4().hex[:12]}",
            sender="assistant",
            text=assistant_reply,
            createdAt=created_at,
            type="message",
            payload={"tutorial": True, "step": "assistant_tip"},
        ),
    ]


def _message_from_row(row: object) -> ChatMessage:
    return ChatMessage(
        id=row["id"],
        sender=row["sender"],
        text=row["text"],
        createdAt=_time_text(row["created_at"]),
        type=row["message_type"],
        payload=_loads(row["payload"], None),
    )


def _image_from_row(row: object) -> GeneratedImage:
    return GeneratedImage(
        id=row["id"],
        url=row["url"],
        remoteUrl=_optional_row_value(row, "remote_url"),
        localPath=_optional_row_value(row, "local_path"),
        publicUrl=_optional_row_value(row, "public_url"),
        mimeType=_optional_row_value(row, "mime_type"),
        fileSize=_optional_row_value(row, "file_size"),
        checksumSha256=_optional_row_value(row, "checksum_sha256"),
        originalUrl=row["original_url"] or "",
        prompt=row["prompt"],
        model=row["model"],
        resolution=row["resolution"],
        aspectRatio=row["aspect_ratio"],
        category=row["category"],
        createdAt=_time_text(row["created_at"]),
        tags=_loads(row["tags"], []),
    )


def _smart_template_from_row(row: object) -> SmartTemplate:
    return SmartTemplate(
        id=row["id"],
        name=row["name"],
        imageUrl=row["image_url"],
        prompt=row["prompt"],
        model=row["model"],
        aspectRatio=row["aspect_ratio"],
        resolution=row["resolution"],
        quantity=row["quantity"],
        type=row["type"],
    )


def _session_from_row(row: object) -> ChatSession:
    return ChatSession(
        id=row["id"],
        title=row["title"],
        category=row["category"],
        createdAt=_time_text(row["created_at"]),
        config=SessionConfig(**_loads(row["config"], {})),
        messages=[],
    )


def _job_from_row(row: object, images: list[GeneratedImage]) -> GenerationJob:
    return GenerationJob(
        id=row["id"],
        status=row["status"],
        provider=row["provider"],
        model=row["model"],
        category=row["category"],
        aspectRatio=row["aspect_ratio"],
        resolution=row["resolution"],
        quantity=row["quantity"],
        prompt=row["prompt"],
        sourceImageUrl=row["source_image_url"] or "",
        sourceImageIds=_loads(_optional_row_value(row, "source_upload_ids"), []),
        size=_optional_row_value(row, "size") or row["resolution"],
        quality=_optional_row_value(row, "quality") or "high",
        n=row["quantity"],
        outputFormat=_optional_row_value(row, "output_format") or "png",
        stream=bool(_optional_row_value(row, "stream") or False),
        requestedCount=_optional_row_value(row, "requested_count"),
        returnedCount=_optional_row_value(row, "returned_count"),
        createdAt=_time_text(row["created_at"]),
        updatedAt=_time_text(row["updated_at"]),
        images=images,
        messages=[],
        errorCode=row["error_code"],
        errorMessage=row["error_message"],
    )


def _optional_row_value(row: object, key: str) -> object | None:
    try:
        return row[key]
    except KeyError:
        return None


def _storage_date(local_path: str | None) -> str | None:
    if not local_path:
        return None
    parts = local_path.replace("\\", "/").split("/")
    return parts[-2] if len(parts) >= 2 else None


def _file_name(local_path: str | None) -> str | None:
    if not local_path:
        return None
    return local_path.replace("\\", "/").split("/")[-1]


def _file_ext(local_path: str | None) -> str | None:
    file_name = _file_name(local_path)
    if not file_name or "." not in file_name:
        return None
    return file_name.rsplit(".", 1)[-1]


def _sessions_from_rows(rows: list[object]) -> list[ChatSession]:
    sessions: dict[str, ChatSession] = {}
    for row in rows:
        if row["id"] not in sessions:
            sessions[row["id"]] = ChatSession(
                id=row["id"],
                title=row["title"],
                category=row["category"],
                createdAt=_time_text(row["created_at"]),
                config=SessionConfig(**_loads(row["config"], {})),
                messages=[],
            )
        if row["message_id"] is not None:
            sessions[row["id"]].messages.append(
                ChatMessage(
                    id=row["message_id"],
                    sender=row["sender"],
                    text=row["text"],
                    createdAt=_time_text(row["message_created_at"]),
                    type=row["message_type"],
                    payload=_loads(row["payload"], None),
                )
            )
    return list(sessions.values())


repository = MySQLRepository()
