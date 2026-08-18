from eval.harness import filter_items_by_ids, parse_ids_filter


def test_parse_ids_filter():
    assert parse_ids_filter(None) is None
    assert parse_ids_filter("") is None
    assert parse_ids_filter("cq024,cq026, s004") == {"cq024", "cq026", "s004"}


def test_filter_items_by_ids():
    items = [{"id": "cq001"}, {"id": "cq024"}, {"id": "s001"}]
    assert filter_items_by_ids(items, {"cq024", "s001"}) == [{"id": "cq024"}, {"id": "s001"}]
    assert filter_items_by_ids(items, None) == items
