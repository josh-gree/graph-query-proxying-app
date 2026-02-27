import pytest

from app.query.executor import _parse_return_columns


# --- basic cases ---

def test_single_variable():
    assert _parse_return_columns("MATCH (n) RETURN n") == ["n"]


def test_multiple_variables():
    assert _parse_return_columns("MATCH (n)-[r]->(m) RETURN n, r, m") == ["n", "r", "m"]


def test_alias():
    assert _parse_return_columns("MATCH (n) RETURN n AS person") == ["person"]


def test_property_access():
    assert _parse_return_columns("MATCH (n) RETURN n.name") == ["name"]


def test_property_access_with_alias():
    assert _parse_return_columns("MATCH (n) RETURN n.name AS name") == ["name"]


def test_aggregation_with_alias():
    assert _parse_return_columns("MATCH (n) RETURN count(n) AS total") == ["total"]


def test_mixed():
    assert _parse_return_columns("MATCH (n)-[r]->(m) RETURN n, n.name AS name, count(r) AS cnt") == ["n", "name", "cnt"]


# --- clause terminators ---

def test_order_by():
    assert _parse_return_columns("MATCH (n) RETURN n ORDER BY n.name") == ["n"]


def test_limit():
    assert _parse_return_columns("MATCH (n) RETURN n LIMIT 10") == ["n"]


def test_skip():
    assert _parse_return_columns("MATCH (n) RETURN n SKIP 5 LIMIT 10") == ["n"]


def test_union():
    assert _parse_return_columns("MATCH (n:A) RETURN n UNION MATCH (n:B) RETURN n") == ["n"]


# --- case insensitivity ---

def test_lowercase_return():
    assert _parse_return_columns("match (n) return n") == ["n"]


def test_mixed_case_return():
    assert _parse_return_columns("MATCH (n) Return n As person") == ["person"]


# --- known failure cases (issue #7) ---

@pytest.mark.skip(reason="issue #7 - DISTINCT stripped by validator, parsing fixed")
def test_distinct_raises():
    with pytest.raises(ValueError):
        _parse_return_columns("MATCH (n) RETURN DISTINCT n")


@pytest.mark.skip(reason="issue #7 - subqueries blocked by validator")
def test_subquery_raises():
    with pytest.raises(ValueError):
        _parse_return_columns("CALL { MATCH (n) RETURN n } RETURN n, m")


@pytest.mark.skip(reason="issue #7 - unaliased function calls blocked by validator")
def test_unaliased_aggregation_raises():
    with pytest.raises(ValueError):
        _parse_return_columns("MATCH (n) RETURN count(n)")
