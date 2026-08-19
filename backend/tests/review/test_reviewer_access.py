async def test_reviewer_can_read_batches_but_cannot_manage_models(reviewer_client) -> None:
    batches = await reviewer_client.get("/api/v1/batches")
    models = await reviewer_client.get("/api/v1/models")

    assert batches.status_code == 200
    assert batches.json() == []
    assert models.status_code == 403
