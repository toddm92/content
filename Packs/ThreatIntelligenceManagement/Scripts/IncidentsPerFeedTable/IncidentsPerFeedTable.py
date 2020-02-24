from CommonServerPython import *
from typing import Any, Dict, Set
import re


def get_feed_indicators(feed, from_date):
    """Return all indicators from a given feed
    Args:
        feed: Feed to look for indicators in
        from_date: Time range to search incidents in

    Returns:
        All indicators from the feed in the time range
    """
    res = demisto.executeCommand('findIndicators', {'query': f'sourceBrands:"{feed}" and investigationsCount:>0',
                                                    'size': 1000000000,
                                                    'fromdate': from_date})
    indicators = res[0]['Contents']
    return indicators


def get_feeds() -> set:
    """Return all enabled modules
            Returns:
                A set with feed names
    """
    modules = demisto.getModules()  # type: ignore  # pylint: disable=E1101
    return {module_details['brand'] for module_details in modules.values() if  # pylint: disable=E1101
            module_details['state'] == 'active'}


def feed_incidents_ids(feed: str, from_date: str) -> set:
    """Queries all indicators from a given feed and return a set of all InvestigationIDs of those indicators
    Args:
        feed: Feed to look for indicators in
        from_date: Time range to search incidents in

    Returns:
        A set of all incident IDs
    """
    incidents_ids = set()
    indicators = get_feed_indicators(feed, from_date)
    for indicator in indicators:
        incidents_ids.update(
            [incident_id for incident_id in indicator.get('investigationIDs', [])])
    return filter_uuids(incidents_ids)


def filter_uuids(incidents_ids: set) -> set:
    """Sometimes indicator's investigationIDs can contain a uuid which is not an actual incident_id.
        Therefore there is no need to query for those ids.
        Args:
            incidents_ids: Incident ids that came from indicators 'investigationIDs' attribute

    Returns:
        A set of all non uuid incident_id
    """
    uuid_pattern = re.compile(r'^[\da-f]{8}-([\da-f]{4}-){3}[\da-f]{12}$', re.IGNORECASE)
    return {incident_id for incident_id in incidents_ids if not uuid_pattern.match(incident_id)}


def count_incidents(incidents_ids: set, from_date: str, is_false_positive: bool) -> int:
    """Counts the number of incidents that has one of incidents_ids, from a given date
    Args:
        incidents_ids: A list of incidents ids to to look for
        from_date: Time range to search incidents in
        is_false_positive: A boolean which tells weather the function should search false positive incidents or not

    Returns:
        The number of incidents that matched the query
    """
    if not incidents_ids:
        return 0
    query = _generate_incidents_query(incidents_ids, is_false_positive)
    params = {'query': query,
              'fromdate': from_date,
              'size': 1}
    res = demisto.executeCommand('getIncidents', params)
    queried_incidents_count = res[0]['Contents']['total']
    return queried_incidents_count


def _generate_incidents_query(incidents_ids, is_false_positive):
    query = 'closeReason:"False Positive"' if is_false_positive else '-closeReason:"False Positive"'
    query += ' and (' + ' or '.join([f'id:{incident_id}' for incident_id in incidents_ids]) + ')'
    return query


def generate_table_data(feed_types: Set[str], from_date: str) -> Dict[str, Any]:
    """Generate a table data structure with all number of incidents, false positive incidents, and their ratio sorted by
    the ratio in desc order.
        Args:
               from_date: Time range to search incidents in
               feed_types :A set Containing feed names
        Returns:
            The total number of enabled feeds and the generated data about them.
        """
    data = []
    for feed in feed_types:
        incident_ids = feed_incidents_ids(feed, from_date)
        true_positive_incidents_count = count_incidents(incident_ids, from_date, is_false_positive=False)
        false_positive_incidents_count = count_incidents(incident_ids, from_date, is_false_positive=True)

        true_positive_to_false_positive_incidents_ratio = \
            1 - (false_positive_incidents_count / true_positive_incidents_count) if true_positive_incidents_count else 0
        data.append({'Feed name': feed,
                     'True Positive Incidents': true_positive_incidents_count,
                     'False Positive Incidents': false_positive_incidents_count,
                     'True/False Positive Incidents Ratio': f'{true_positive_to_false_positive_incidents_ratio * 100:,.2f}%'})

    table_data = {'total': len(feed_types),
                  'data': sorted(data,
                                 key=lambda feed_details: -float(
                                     feed_details['True/False Positive Incidents Ratio'].strip('%')))}  # type: ignore
    return table_data


def main():
    feed_types = get_feeds()
    from_date = demisto.args().get('from')
    table_data = generate_table_data(feed_types, from_date)
    human_readable = tableToMarkdown('Incidents count by feed', table_data)
    demisto.results({
        'Type': entryTypes['note'],
        'Contents': table_data,
        'ContentsFormat': formats['text'],
        'ReadableContentsFormat': formats['markdown'],
        'HumanReadable': human_readable
    })


if __name__ in ('__main__', '__builtin__', 'builtins'):
    main()
