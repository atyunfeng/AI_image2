import pytest

from aiimage.workflow.state import BatchStatus, InvalidTransition, transition_batch


@pytest.mark.parametrize(
    ("source", "target"),
    [
        (BatchStatus.DRAFT, BatchStatus.READY),
        (BatchStatus.READY, BatchStatus.QUEUED),
        (BatchStatus.QUEUED, BatchStatus.RUNNING),
        (BatchStatus.RUNNING, BatchStatus.QA_PENDING),
        (BatchStatus.QA_PENDING, BatchStatus.REVIEW_PENDING),
    ],
)
def test_valid_batch_transitions(source: BatchStatus, target: BatchStatus) -> None:
    assert transition_batch(source, target) is target


def test_approved_cannot_return_to_running() -> None:
    with pytest.raises(InvalidTransition):
        transition_batch(BatchStatus.APPROVED, BatchStatus.RUNNING)

