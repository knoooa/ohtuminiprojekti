import json

from sqlalchemy import text

from config import db
from entities.citation import Citation


def _to_citation(row):
    """Converts a database row to a Citation object."""
    if not row:
        return None

    fields = row.fields or ""
    if isinstance(fields, str):
        try:
            fields = json.loads(fields)
        except json.JSONDecodeError:
            fields = {}

    return Citation(
        row.id,
        row.entry_type,
        row.citation_key,
        fields
    )


def get_citations(page=None, per_page=None):
    """Fetches citations from the database.

    Optional paging:
      - page: 1-based page number
      - per_page: items per page

    If both `page` and `per_page` are provided, the query uses LIMIT/OFFSET
    to return only that page. If omitted, all citations are returned.
    """
    # N.B. This method should probably have a default per_page value...
    base_sql = (
        """
        SELECT
            c.id,
            et.name AS entry_type,
            c.citation_key, c.fields
        FROM citations c
        JOIN entry_types et ON c.entry_type_id = et.id
        ORDER BY c.id
        """
    )

    params = {}
    if isinstance(page, int) and isinstance(per_page, int):
        page = max(page, 1)
        per_page = max(per_page, 1)
        offset = (page - 1) * per_page

        base_sql = base_sql + " LIMIT :limit OFFSET :offset"
        params["limit"] = per_page
        params["offset"] = offset

    sql = text(base_sql)
    result = db.session.execute(sql, params).fetchall()

    if not result:
        return []

    return [_to_citation(c) for c in result]


def get_citation(citation_id):
    """Fetches a citation by its ID from the database"""

    sql = text(
        """
        SELECT
            c.id,
            et.name AS entry_type,
            c.citation_key, c.fields
        FROM citations c
        JOIN entry_types et ON c.entry_type_id = et.id
        WHERE c.id = :citation_id
        ORDER BY et.name
        """
    )

    params = {
        "citation_id": citation_id,
    }

    result = db.session.execute(sql, params).fetchone()

    if not result:
        return None

    return _to_citation(result)


def create_citation(entry_type_id, citation_key, fields):
    """Creates a new citation entry in the database"""

    sql = text(
        """
        INSERT INTO citations (entry_type_id, citation_key, fields)
        VALUES (:entry_type_id, :citation_key, :fields)
        """
    )

    serialized = json.dumps(fields or {})

    params = {
        "entry_type_id": entry_type_id,
        "citation_key": citation_key,
        "fields": serialized,
    }

    db.session.execute(sql, params)
    db.session.commit()


def update_citation(citation_id, entry_type_id=None, citation_key=None, fields=None):
    """Updates an existing citation entry in the database."""

    values = []
    params = {"citation_id": citation_id}

    if entry_type_id:
        values.append("entry_type_id = :entry_type_id")
        params["entry_type_id"] = entry_type_id

    if citation_key:
        values.append("citation_key = :citation_key")
        params["citation_key"] = citation_key

    if fields:
        serialized = json.dumps(fields or {})
        values.append("fields = :fields")
        params["fields"] = serialized

    # Nothing to update; returning.
    # Should this return a value or raise?
    if not values:
        return

    base_sql = (
        f"""
        UPDATE citations
        SET {", ".join(values)}
        WHERE id = :citation_id
        """
    )

    sql = text(base_sql)

    db.session.execute(sql, params)
    db.session.commit()


def delete_citation(citation_id):
    """Deletes a citation entry from the database by its ID"""

    sql = text(
        """
        DELETE FROM citations
        WHERE id = :citation_id
        """
    )

    db.session.execute(sql, {"citation_id": citation_id})
    db.session.commit()


def search_citations(queries=None):
    base_sql = """
        SELECT
            c.id,
            et.name AS entry_type,
            c.citation_key,
            c.fields
        FROM citations c
        JOIN entry_types et ON c.entry_type_id = et.id
    """

    if not queries:
        return []

    filters = []
    params = {}

    if queries["q"]:
        filters.append("c.fields::text ILIKE :q")
        params["q"] = f"%{queries["q"]}%"

    if queries["citation_key"]:
        filters.append("c.citation_key ILIKE :citation_key")
        params["citation_key"] = f"%{queries["citation_key"]}%"

    if queries["entry_type"]:
        filters.append("et.name = :entry_type")
        params["entry_type"] = queries["entry_type"]

    if queries["author"]:
        filters.append("c.fields->>'author' ILIKE :author")
        params["author"] = f"%{queries["author"]}%"

    if queries["year_from"]:
        filters.append("(c.fields->>'year')::int >= :year_from")
        params["year_from"] = int(queries["year_from"])

    if queries["year_to"]:
        filters.append("(c.fields->>'year')::int <= :year_to")
        params["year_to"] = int(queries["year_to"])

    if filters:
        base_sql += f" WHERE {" AND ".join(filters)}"

    if queries["sort_by"] == "year":
        base_sql += f" ORDER BY (c.fields->>'year')::int {queries["direction"]}"
    elif queries["sort_by"] == "citation_key":
        base_sql += f" ORDER BY c.citation_key {queries["direction"]}"
    else:
        base_sql += " ORDER BY c.id ASC"

    sql = text(base_sql)

    result = db.session.execute(sql, params).fetchall()
    return [_to_citation(r) for r in result]
