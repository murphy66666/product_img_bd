import asyncio
from dataclasses import dataclass

from app.schemas.generation import GenerationJobCreateRequest
from app.services.generation_service import get_generation_service


@dataclass(frozen=True)
class GenerationTask:
    user_id: str
    job_id: str
    payload: GenerationJobCreateRequest


class GenerationQueue:
    def __init__(self) -> None:
        self._queue: asyncio.Queue[GenerationTask] = asyncio.Queue()
        self._worker: asyncio.Task[None] | None = None
        self._stop_event = asyncio.Event()

    async def start(self) -> None:
        if self._worker is None or self._worker.done():
            self._stop_event.clear()
            self._worker = asyncio.create_task(self._run())

    async def stop(self) -> None:
        self._stop_event.set()
        if self._worker is not None:
            self._worker.cancel()
            try:
                await self._worker
            except asyncio.CancelledError:
                pass
            self._worker = None

    async def enqueue(self, task: GenerationTask) -> None:
        await self._queue.put(task)

    async def _run(self) -> None:
        service = get_generation_service()
        while not self._stop_event.is_set():
            task = await self._queue.get()
            try:
                await service.run_job(task.user_id, task.job_id, task.payload)
            finally:
                self._queue.task_done()


generation_queue = GenerationQueue()


async def enqueue_generation_job(
    user_id: str,
    job_id: str,
    payload: GenerationJobCreateRequest,
) -> None:
    await generation_queue.enqueue(GenerationTask(user_id=user_id, job_id=job_id, payload=payload))


async def start_generation_queue() -> None:
    await generation_queue.start()


async def stop_generation_queue() -> None:
    await generation_queue.stop()
