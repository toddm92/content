from IncidentsPerFeedTable import get_feeds, filter_uuids, _generate_incidents_query
from CommonServerPython import demisto
from uuid import uuid4

MODULES = {"test feed": {"brand": "test feed", "state": "active"},
           "non active feed": {"brand": "non active feed", "state": "disabled"}}


def test_get_active_feeds(mocker):
    mocker.patch.object(demisto, 'getModules', return_value=MODULES)
    feeds = get_feeds()
    assert feeds == {"test feed"}


def test_filter_uuids():
    non_uuid = "1234"
    ids = {str(uuid4()), str(uuid4()), str(uuid4()), non_uuid}
    assert filter_uuids(ids) == {non_uuid}


def test_generate_incidents_query():
    incidents_ids = ["1", "2", "3"]
    query = _generate_incidents_query(incidents_ids, is_false_positive=True)
    assert query == 'closeReason:"False Positive" and (id:1 or id:2 or id:3)'
    query = _generate_incidents_query(incidents_ids, is_false_positive=False)
    assert query == '-closeReason:"False Positive" and (id:1 or id:2 or id:3)'
