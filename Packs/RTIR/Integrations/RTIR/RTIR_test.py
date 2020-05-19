import requests
import demistomock as demisto


class DotDict(dict):
    """dot.notation access to dictionary attributes"""
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__


def test_query_formatting(mocker):
    args = {
        'ticket-id': 1111
    }
    params = {
        'server': 'test',
        'credentials': {
            'identifier': 'test',
            'password': 'test'
        },
        'fetch_priority': 1,
        'fetch_status': 'test',
        'fetch_queue': 'test',
        'proxy': True
    }

    mocker.patch.object(requests, 'session', return_value=DotDict({}))
    mocker.patch.object(demisto, 'args', return_value=args)
    mocker.patch.object(demisto, 'params', return_value=params)

    from RTIR import build_search_query
    query = build_search_query()
    assert not (query.endswith('+OR+') or query.endswith('+AND+'))


RAW_HISTORY = """    
RT/4.4.2 200 Ok

# 24/24 (id/80/total)

id: 80
Ticket: 5
TimeTaken: 0
Type: Create
Field:
OldValue:
NewValue: some new value
Data:
Description: Ticket created by root
Content: Some
Multi line
Content
Creator: root
Created: 2018-07-09 11:25:59
Attachments:

"""


def test_parse_history_response():
    from RTIR import parse_history_response
    parsed_history = parse_history_response(RAW_HISTORY)
    assert parsed_history == {'ID': '80',
                              'Content': 'Some\nMulti line\nContent',
                              'Created': '2018-07-09 11:25:59',
                              'Creator': 'root',
                              'Description': 'Ticket created by root',
                              'NewValue': 'some new value'}
