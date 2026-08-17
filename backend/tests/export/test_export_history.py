from uuid import uuid4

from aiimage.export.models import ExportRecord
from aiimage.export.service import list_export_records


async def test_export_records_are_append_only_business_history(session_factory) -> None:
    async with session_factory() as session:
        batch_id = uuid4()
        first = ExportRecord(
            batch_id=batch_id,
            archive_asset_id=uuid4(),
            manifest_sha256="a" * 64,
            created_by_user_id=uuid4(),
        )
        second = ExportRecord(
            batch_id=batch_id,
            archive_asset_id=uuid4(),
            manifest_sha256="a" * 64,
            created_by_user_id=uuid4(),
        )
        session.add_all([first, second])
        await session.commit()

        history = await list_export_records(session, batch_id)

        assert {record.id for record in history} == {first.id, second.id}
        assert len(history) == 2
