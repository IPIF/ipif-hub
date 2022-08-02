import json
from django.core.management.base import BaseCommand, CommandError, CommandParser

from ipif_hub.management.utils.ingest_data import (
    ingest_data,
    DataFormatError,
    DataIntegrityError,
)


class Command(BaseCommand):
    help = "Ingests data from IPIF-Hub formatted JSON file"

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("endpoint_id", type=str)
        parser.add_argument("file_path", type=str)

    def handle(
        self, *args, endpoint_id: str = None, file_path: str = None, **options
    ) -> None:
        try:
            with open(file_path, "r") as f:
                data = json.load(f)
        except json.JSONDecodeError:
            raise CommandError(f"{file_path} is not valid JSON")
        except FileNotFoundError:
            raise CommandError(f"'{file_path}' does not exist")

        try:
            ingest_data(endpoint_id, data)
        except DataFormatError as e:
            raise CommandError(f"DataFormatError: {e.args[0]}")
        except DataIntegrityError as e:
            raise CommandError(f"DataIntegrity Error: {e.args[0]}")
