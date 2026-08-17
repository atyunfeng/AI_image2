from enum import StrEnum


class BatchStatus(StrEnum):
    DRAFT = "draft"
    READY = "ready"
    QUEUED = "queued"
    RUNNING = "running"
    QA_PENDING = "qa_pending"
    REVIEW_PENDING = "review_pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPORTED = "exported"
    FAILED = "failed"
    CANCELED = "canceled"
    RETRY_QUEUED = "retry_queued"


class StepStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELED = "canceled"
    RETRY_QUEUED = "retry_queued"


class InvalidTransition(RuntimeError):
    pass


ALLOWED_TRANSITIONS: dict[BatchStatus, set[BatchStatus]] = {
    BatchStatus.DRAFT: {BatchStatus.READY, BatchStatus.CANCELED},
    BatchStatus.READY: {BatchStatus.QUEUED, BatchStatus.CANCELED},
    BatchStatus.QUEUED: {BatchStatus.RUNNING, BatchStatus.CANCELED, BatchStatus.FAILED},
    BatchStatus.RUNNING: {
        BatchStatus.QA_PENDING,
        BatchStatus.FAILED,
        BatchStatus.CANCELED,
    },
    BatchStatus.QA_PENDING: {BatchStatus.REVIEW_PENDING, BatchStatus.FAILED},
    BatchStatus.REVIEW_PENDING: {
        BatchStatus.APPROVED,
        BatchStatus.REJECTED,
        BatchStatus.RETRY_QUEUED,
    },
    BatchStatus.RETRY_QUEUED: {BatchStatus.QUEUED, BatchStatus.CANCELED},
    BatchStatus.APPROVED: {BatchStatus.EXPORTED},
    BatchStatus.REJECTED: {BatchStatus.RETRY_QUEUED},
    BatchStatus.EXPORTED: set(),
    BatchStatus.FAILED: {BatchStatus.RETRY_QUEUED},
    BatchStatus.CANCELED: set(),
}


def transition_batch(source: BatchStatus, target: BatchStatus) -> BatchStatus:
    if target not in ALLOWED_TRANSITIONS[source]:
        raise InvalidTransition(f"Cannot transition batch from {source.value} to {target.value}")
    return target

