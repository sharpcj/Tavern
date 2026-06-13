"""Tavern project package."""

try:
    import pymysql
except ImportError:  # pragma: no cover - mysqlclient may be used instead.
    pymysql = None

if pymysql is not None:
    pymysql.install_as_MySQLdb()
