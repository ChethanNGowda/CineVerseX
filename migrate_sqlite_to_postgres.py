import argparse
import importlib
import os
import subprocess
import sys
from collections import OrderedDict
from getpass import getpass
from pathlib import Path
from urllib.parse import quote_plus

from dotenv import load_dotenv
from sqlalchemy import create_engine, func, inspect, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker


ROOT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = ROOT_DIR / "backend"

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


load_dotenv(ROOT_DIR / ".env")
load_dotenv(BACKEND_DIR / ".env")


MODEL_MODULES = [
    "models.user",
    "models.movie",
    "models.theater",
    "models.show",
    "models.booking",
    "models.ticket",
    "models.review",
    "models.wishlist",
    "models.activity_log",
    "models.setting",
]


def parse_args():
    parser = argparse.ArgumentParser(
        description="Migrate CineVerseX application data from SQLite to PostgreSQL."
    )
    parser.add_argument(
        "--sqlite-path",
        default=str(BACKEND_DIR / "cineversex.db"),
        help="Path to the SQLite database file.",
    )
    parser.add_argument(
        "--postgres-url",
        default=os.environ.get("DATABASE_URL", ""),
        help="Full PostgreSQL SQLAlchemy URL. If omitted, URL is built from --pg-* options.",
    )
    parser.add_argument("--pg-host", default=os.environ.get("PGHOST", "localhost"))
    parser.add_argument("--pg-port", default=os.environ.get("PGPORT", "5432"))
    parser.add_argument("--pg-db", default=os.environ.get("PGDATABASE", "cineversex"))
    parser.add_argument("--pg-user", default=os.environ.get("PGUSER", "cineversex_user"))
    parser.add_argument("--pg-password", default=os.environ.get("PGPASSWORD", ""))
    parser.add_argument(
        "--skip-schema-upgrade",
        action="store_true",
        help="Skip running Flask-Migrate upgrade before data copy.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=500,
        help="Rows to stream per batch from SQLite.",
    )
    parser.add_argument(
        "--on-existing",
        choices=["skip", "update"],
        default="update",
        help="Behavior when a row with the same primary key already exists in PostgreSQL.",
    )
    parser.add_argument(
        "--fail-if-target-not-empty",
        action="store_true",
        help="Abort if any destination model table already has rows.",
    )
    parser.add_argument(
        "--strict-counts",
        action="store_true",
        help="Exit with failure when any SQLite/PostgreSQL row counts differ.",
    )
    return parser.parse_args()


def build_postgres_url(args):
    if args.postgres_url:
        return args.postgres_url

    password = args.pg_password or os.environ.get("POSTGRES_PASSWORD", "")
    if not password:
        password = getpass(f"Password for PostgreSQL user '{args.pg_user}': ")

    user = quote_plus(args.pg_user)
    password_encoded = quote_plus(password)
    return (
        f"postgresql+psycopg2://{user}:{password_encoded}@"
        f"{args.pg_host}:{args.pg_port}/{args.pg_db}"
    )


def import_models():
    for module_name in MODEL_MODULES:
        importlib.import_module(module_name)


def get_model_order(db):
    mapper_by_table = {}
    for mapper in db.Model.registry.mappers:
        mapper_by_table[mapper.local_table.name] = mapper.class_

    ordered = []
    for table in db.metadata.sorted_tables:
        model_class = mapper_by_table.get(table.name)
        if model_class is not None:
            ordered.append(model_class)
    return ordered


def run_schema_upgrade(postgres_url):
    print("[schema] Running migration: flask --app backend.app db upgrade")
    env = os.environ.copy()
    env["DATABASE_URL"] = postgres_url
    env["SKIP_STARTUP_INIT"] = "1"

    command = [sys.executable, "-m", "flask", "--app", "backend.app", "db", "upgrade"]
    result = subprocess.run(
        command,
        cwd=ROOT_DIR,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    if result.stdout.strip():
        print(result.stdout.strip())
    if result.returncode != 0:
        if result.stderr.strip():
            print(result.stderr.strip())
        raise RuntimeError("Flask-Migrate upgrade failed.")


def verify_schema_matches_models(engine, metadata):
    inspector = inspect(engine)
    db_tables = set(inspector.get_table_names())
    model_tables = {table.name for table in metadata.sorted_tables}

    missing_tables = sorted(model_tables - db_tables)
    extra_tables = sorted(db_tables - model_tables - {"alembic_version", "imdb_image_cache"})

    mismatches = []

    for table_name in sorted(model_tables & db_tables):
        model_columns = {column.name for column in metadata.tables[table_name].columns}
        db_columns = {column["name"] for column in inspector.get_columns(table_name)}

        missing_columns = sorted(model_columns - db_columns)
        extra_columns = sorted(db_columns - model_columns)

        if missing_columns or extra_columns:
            mismatches.append(
                {
                    "table": table_name,
                    "missing_columns": missing_columns,
                    "extra_columns": extra_columns,
                }
            )

    print("[schema] Verification report")
    if missing_tables:
        print(f"  Missing tables in PostgreSQL: {', '.join(missing_tables)}")
    else:
        print("  Missing tables in PostgreSQL: none")

    if extra_tables:
        print(f"  Extra tables in PostgreSQL: {', '.join(extra_tables)}")
    else:
        print("  Extra tables in PostgreSQL: none")

    if mismatches:
        for mismatch in mismatches:
            print(f"  Column mismatch for {mismatch['table']}:")
            if mismatch["missing_columns"]:
                print(f"    Missing columns: {', '.join(mismatch['missing_columns'])}")
            if mismatch["extra_columns"]:
                print(f"    Extra columns: {', '.join(mismatch['extra_columns'])}")
    else:
        print("  Column mismatches: none")

    if missing_tables or mismatches:
        raise RuntimeError("PostgreSQL schema does not match SQLAlchemy models.")


def pk_filter(model_class, row_data):
    pk_columns = list(model_class.__mapper__.primary_key)
    if len(pk_columns) == 1:
        pk_name = pk_columns[0].name
        return {pk_name: row_data.get(pk_name)}

    return {column.name: row_data.get(column.name) for column in pk_columns}


def row_to_dict(model_class, row):
    return {column.name: getattr(row, column.name) for column in model_class.__table__.columns}


def apply_row_data(target_obj, row_data):
    for key, value in row_data.items():
        setattr(target_obj, key, value)


def reset_postgres_sequences(engine, model_order):
    print("[sequence] Aligning PostgreSQL sequences with migrated primary keys")
    with engine.begin() as connection:
        for model_class in model_order:
            pk_columns = list(model_class.__mapper__.primary_key)
            if len(pk_columns) != 1:
                continue

            pk_column = pk_columns[0]
            try:
                if pk_column.type.python_type is not int:
                    continue
            except NotImplementedError:
                continue

            table_name = model_class.__tablename__
            column_name = pk_column.name

            sequence_sql = text(
                """
                SELECT setval(
                    pg_get_serial_sequence(:table_name, :column_name),
                    COALESCE((SELECT MAX({column_name}) FROM {table_name}), 1),
                    COALESCE((SELECT MAX({column_name}) FROM {table_name}) IS NOT NULL, false)
                )
                """.replace("{table_name}", table_name).replace("{column_name}", column_name)
            )
            connection.execute(
                sequence_sql,
                {"table_name": table_name, "column_name": column_name},
            )


def migrate_data(source_session, target_session, model_order, batch_size, on_existing):
    summary = OrderedDict()

    try:
        with target_session.begin():
            for model_class in model_order:
                table_name = model_class.__tablename__
                source_count = source_session.query(func.count()).select_from(model_class).scalar() or 0

                print(f"[migrate] Table: {table_name} (source rows: {source_count})")

                migrated = 0
                updated = 0
                skipped = 0
                failed = 0

                query = source_session.query(model_class)
                for row in query.yield_per(batch_size):
                    row_data = row_to_dict(model_class, row)
                    pk_values = pk_filter(model_class, row_data)

                    existing = target_session.query(model_class).filter_by(**pk_values).first()
                    if existing is not None:
                        if on_existing == "skip":
                            skipped += 1
                            continue

                        try:
                            savepoint = target_session.begin_nested()
                            apply_row_data(existing, row_data)
                            target_session.flush()
                            savepoint.commit()
                            updated += 1
                        except Exception as exc:  # noqa: BLE001
                            savepoint.rollback()
                            failed += 1
                            print(f"  [error] {table_name} PK={pk_values} update failed: {exc}")
                        continue

                    target_obj = model_class(**row_data)

                    try:
                        savepoint = target_session.begin_nested()
                        target_session.add(target_obj)
                        target_session.flush()
                        savepoint.commit()
                        migrated += 1
                    except IntegrityError as exc:
                        savepoint.rollback()
                        # Only skip when the primary key row now exists; otherwise surface failure.
                        duplicate_pk = target_session.query(model_class).filter_by(**pk_values).first() is not None
                        if duplicate_pk:
                            skipped += 1
                        else:
                            failed += 1
                            print(f"  [error] {table_name} PK={pk_values} integrity error: {exc}")
                    except Exception as exc:  # noqa: BLE001
                        savepoint.rollback()
                        failed += 1
                        print(f"  [error] {table_name} PK={pk_values}: {exc}")

                summary[table_name] = {
                    "source": source_count,
                    "migrated": migrated,
                    "updated": updated,
                    "skipped": skipped,
                    "failed": failed,
                }

                print(
                    f"  [done] migrated={migrated}, updated={updated}, skipped={skipped}, failed={failed}"
                )
    except Exception:
        target_session.rollback()
        raise

    return summary


def verify_counts(source_session, target_session, model_order):
    print("[verify] Comparing row counts between SQLite and PostgreSQL")
    matches_all = True

    for model_class in model_order:
        table_name = model_class.__tablename__
        source_count = source_session.query(func.count()).select_from(model_class).scalar() or 0
        target_count = target_session.query(func.count()).select_from(model_class).scalar() or 0

        status = "MATCH" if source_count == target_count else "MISMATCH"
        if status == "MISMATCH":
            matches_all = False

        print(f"  {table_name}: sqlite={source_count}, postgres={target_count} [{status}]")

    return matches_all


def inspect_target_occupancy(target_session, model_order):
    occupancy = OrderedDict()
    for model_class in model_order:
        table_name = model_class.__tablename__
        count = target_session.query(func.count()).select_from(model_class).scalar() or 0
        occupancy[table_name] = count
    return occupancy


def main():
    args = parse_args()
    sqlite_path = Path(args.sqlite_path).resolve()

    if not sqlite_path.exists():
        raise FileNotFoundError(f"SQLite file not found: {sqlite_path}")

    postgres_url = build_postgres_url(args)
    import_models()

    from flask import Flask
    from extensions import db

    app = Flask("cineversex-migration")
    app.config["SQLALCHEMY_DATABASE_URI"] = postgres_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)

    source_engine = create_engine(f"sqlite:///{sqlite_path.as_posix()}")

    with app.app_context():
        if not args.skip_schema_upgrade:
            run_schema_upgrade(postgres_url)

        verify_schema_matches_models(db.engine, db.metadata)

        source_session_factory = sessionmaker(bind=source_engine, autoflush=False)
        target_session_factory = sessionmaker(bind=db.engine, autoflush=False)

        source_session = source_session_factory()
        target_session = target_session_factory()

        try:
            model_order = get_model_order(db)
            source_tables = set(inspect(source_engine).get_table_names())
            model_order = [m for m in model_order if m.__tablename__ in source_tables]

            target_occupancy = inspect_target_occupancy(target_session, model_order)
            non_empty_tables = [name for name, count in target_occupancy.items() if count > 0]
            if non_empty_tables:
                print("[precheck] Non-empty PostgreSQL tables detected:")
                for table_name in non_empty_tables:
                    print(f"  {table_name}: {target_occupancy[table_name]}")

                if args.fail_if_target_not_empty:
                    raise RuntimeError(
                        "Target is not empty and --fail-if-target-not-empty was set."
                    )
            else:
                print("[precheck] All destination model tables are empty.")

            print("[source] SQLite file:", sqlite_path)
            print("[target] PostgreSQL URL:", postgres_url.rsplit("@", 1)[-1])
            print("[order] Migration order:", ", ".join(model.__tablename__ for model in model_order))

            summary = migrate_data(
                source_session=source_session,
                target_session=target_session,
                model_order=model_order,
                batch_size=args.batch_size,
                on_existing=args.on_existing,
            )

            reset_postgres_sequences(db.engine, model_order)

            print("[summary] Per-table migration results")
            for table_name, stats in summary.items():
                print(
                    f"  {table_name}: source={stats['source']}, migrated={stats['migrated']}, "
                    f"updated={stats['updated']}, skipped={stats['skipped']}, failed={stats['failed']}"
                )

            counts_match = verify_counts(source_session, target_session, model_order)
            if counts_match:
                print("[result] Success: all table row counts match.")
            else:
                print("[result] Completed with count mismatches. Review logs above.")
                if args.strict_counts:
                    raise RuntimeError("Count verification failed in strict mode.")
        finally:
            source_session.close()
            target_session.close()


if __name__ == "__main__":
    main()