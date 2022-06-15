import datetime
import hashlib
import json

from django.core.exceptions import ValidationError
from django.db import transaction
from ipif_hub.models import URI, IpifRepo, Person, Source


class DataFormatError(Exception):
    pass


REQUIRED_META_FIELDS = {
    "endpoint_name",
    "endpoint_slug",
    "endpoint_uri",
    "refresh_frequency",
    "refresh_time",
    "endpoint_is_ipif",
}
REQUIRED_PERSON_OR_SOURCE_FIELDS = {
    "@id",
    "createdBy",
    "createdWhen",
    "modifiedBy",
    "modifiedWhen",
}


def build_qualified_id(endpoint_uri, entity_type, id):

    """Returns the full IPIF-compliant URL version of the entity"""
    uri = endpoint_uri[:-1] if endpoint_uri.endswith("/") else endpoint_uri
    entity_type = f"{entity_type.lower()}s"
    return f"{uri}/{entity_type}/{id}"


def ingest_endpoint_meta(meta_data):
    """Ingests endpoint metadata in IPIF-Hub Format."""
    provided_keys = set(meta_data.keys())
    # Check data fields present and raise error if missing
    missing_fields = REQUIRED_META_FIELDS - provided_keys
    if missing_fields:
        raise DataFormatError(
            f"IPIF JSON 'meta' fields missing: {', '.join(missing_fields)}"
        )
    invalid_fields = REQUIRED_META_FIELDS.symmetric_difference(provided_keys)
    if invalid_fields:
        raise DataFormatError(
            f"IPIF JSON 'meta' has invalid fields: {', '.join(invalid_fields)}"
        )
    try:
        ipif_repo = IpifRepo.objects.filter(pk=meta_data["endpoint_slug"])
        if ipif_repo:
            ipif_repo.update(**meta_data)
        else:
            ipif_repo = IpifRepo(**meta_data)
            ipif_repo.save()
    except ValidationError as e:
        raise DataFormatError(f"IPIF JSON 'meta' error: {e}")
    except Exception as e:
        raise DataFormatError(f"ERROR: {e}")


def ingest_person_or_source(entity_class, data, ipif_repo):
    provided_keys = set(data.keys())
    missing_fields = REQUIRED_PERSON_OR_SOURCE_FIELDS - provided_keys
    if missing_fields:
        raise DataFormatError(
            f"IPIF JSON 'person' fields missing: {', '.join(missing_fields)}"
        )
    data["local_id"] = data.pop("@id")

    qid = build_qualified_id(
        ipif_repo.endpoint_uri, entity_class.__name__, data["local_id"]
    )
    uris_to_set = data.pop("uris", [])

    try:
        entity = entity_class.objects.get(pk=qid)

        # If already exists, check whether it's been modified by comparing hashes;
        # if not modified, just return
        input_content_hash = hashlib.md5(
            json.dumps(data, sort_keys=True, ensure_ascii=True, default=str).encode()
        ).hexdigest()

        if entity.inputContentHash == input_content_hash:
            print(f"No change to {entity_class.__name__} {qid}")
            return

        try:
            entity.createdBy = data["createdBy"]
            entity.createdWhen = data["createdWhen"]
            entity.modifiedBy = data["modifiedBy"]
            entity.modifiedWhen = data["modifiedWhen"]
            entity.inputContentHash = input_content_hash

            current_uris = {uri.uri for uri in entity.uris.all()}
            for uri_to_set in uris_to_set:
                if uri_to_set not in current_uris:
                    try:
                        uri = URI.objects.get(uri=uri_to_set)
                    except URI.DoesNotExist:
                        uri = URI(uri=uri_to_set)
                        uri.save()
                    entity.uris.add(uri)
            current_uris = {uri for uri in entity.uris.all()}
            for current_uri in current_uris:
                if current_uri.uri not in uris_to_set:
                    entity.uris.remove(current_uri)
            entity.save()
        except ValidationError as e:
            raise DataFormatError(f"IPIF JSON 'person' error: {e}")

    except entity_class.DoesNotExist:
        try:
            data["inputContentHash"] = input_content_hash
            entity = entity_class(**data)
            entity.ipif_repo = ipif_repo
            entity.save()

            for uri_to_add in uris_to_set:
                try:
                    uri = URI.objects.get(uri=uri_to_add)
                except URI.DoesNotExist:
                    uri = URI(uri=uri_to_add)
                    uri.save()
                entity.uris.add(uri)

            entity.save()

        except ValidationError as e:
            raise DataFormatError(f"IPIF JSON 'person' error: {e}")


def ingest_persons(persons_data, ipif_repo):
    # print(persons_data)
    for person in persons_data:
        ingest_person_or_source(Person, person, ipif_repo)


def ingest_sources(sources_data, ipif_repo):
    for source in sources_data:
        ingest_person_or_source(Source, source, ipif_repo)


@transaction.atomic
def ingest_data(data):
    try:
        ingest_endpoint_meta(data["meta"])
        pass
    except KeyError:
        raise DataFormatError("IPIF JSON is missing endpoint 'meta' field")

    ipif_repo = IpifRepo.objects.get(pk=data["meta"]["endpoint_slug"])

    try:
        ingest_persons(data["persons"], ipif_repo)
    except KeyError:
        DataFormatError("IPIF JSON is missing 'persons' field")

    try:
        ingest_sources(data["sources"], ipif_repo)
    except KeyError:
        DataFormatError("IPIF JSON is missing 'sources' field")
