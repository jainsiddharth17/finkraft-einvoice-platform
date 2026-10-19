from app.status import normalize, can_advance, Status
def test_out_of_order_status_does_not_regress():
    assert not can_advance(Status.DELIVERED.value, normalize("asp_b","ACCEPTED"))
def test_c5_mapping():
    assert normalize("asp_b","TAX_CONFIRMED") == Status.REPORTED
