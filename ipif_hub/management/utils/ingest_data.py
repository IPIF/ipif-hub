import datetime
import hashlib
import json

from django.core.exceptions import ValidationError
from django.db import transaction
from jsonschema import validate

from ipif_hub.management.utils.ingest_schemas import (
    FACTOID_SCHEMA,
    PERSON_SOURCE_SCHEMA,
    STATEMENT_SCHEMA,
)
from ipif_hub.models import (
    URI,
    Factoid,
    IpifRepo,
    Person,
    Place,
    Source,
    Statement,
    get_ipif_hub_repo_AUTOCREATED_instance,
)

ipif_hub_repo_AUTOCREATED = get_ipif_hub_repo_AUTOCREATED_instance()


class DataFormatError(Exception):
    pass


class DataIntegrityError(Exception):
    pass


NO_CHANGE_TO_DATA = "NO CHANGE TO DATA"


def hash_content(data):
    content_as_json = json.dumps(data, sort_keys=True, ensure_ascii=True, default=str)

    return hashlib.md5(content_as_json.encode()).hexdigest()


def build_qualified_id(endpoint_uri, entity_type, id):

    """Returns the full IPIF-compliant URL version of the entity"""
    uri = endpoint_uri[:-1] if endpoint_uri.endswith("/") else endpoint_uri
    entity_type = f"{entity_type.lower()}s"
    return f"{uri}/{entity_type}/{id}"


def ingest_statement(data, ipif_repo):
    ipif_hub_repo_AUTOCREATED = get_ipif_hub_repo_AUTOCREATED_instance()

    try:
        validate(data, schema=STATEMENT_SCHEMA)
    except Exception as e:
        raise DataFormatError(e)

    data["local_id"] = data.pop("@id")

    qid = build_qualified_id(ipif_repo.endpoint_uri, "Statement", data["local_id"])

    input_content_hash = hash_content(data)
    relatesToPerson_to_set = data.pop("relatesToPerson", [])
    places_to_set = data.pop("places", [])

    try:  # If already exists
        statement = Statement.objects.get(identifier=qid)

        # Hash new content to see if different; if not, do not return
        if statement.inputContentHash == input_content_hash:
            print(f'No change to <Statement @id="{qid}">; skipping ingest.')
            return NO_CHANGE_TO_DATA
        else:
            print(f"Ingesting <Statement @id={qid}>")

        try:  # Now update the object
            statement.local_id = data["local_id"]
            statement.label = data["label"]
            statement.createdBy = data["createdBy"]
            statement.createdWhen = data["createdWhen"]
            statement.modifiedBy = data["modifiedBy"]
            statement.modifiedWhen = data["modifiedWhen"]
            statement.inputContentHash = input_content_hash

            if name := data.get("name"):
                statement.name = name

            if date := data.get("date"):
                statement.date_label = date.get("label", None)
                statement.date_sortdate = date.get("sortdate", None)

            if st := data.get("statementType"):
                statement.statementType_uri = st.get("uri", None)
                statement.statementType_label = st.get("label", None)

            if role := data.get("role"):
                statement.role_uri = role.get("uri", None)
                statement.role_label = role.get("label", None)

            if memberOf := data.get("memberOf"):
                statement.memberOf_label = memberOf.get("label", None)
                statement.memberOf_uri = memberOf.get("uri", None)

            current_places_as_uris = {place.uri for place in statement.places.all()}
            for place_to_set in places_to_set:
                if place_to_set["uri"] not in current_places_as_uris:
                    try:
                        place = Place.objects.get(uri=place_to_set["uri"])
                    except Place.DoesNotExist:
                        place = Place(**place_to_set)
                        place.save()
                    statement.places.add(place)
            places_to_set_uris = {place["uri"] for place in places_to_set}
            current_places = {place for place in statement.places.all()}
            for current_place in current_places:
                if current_place.uri not in places_to_set_uris:
                    statement.places.remove(current_place)

            current_persons_as_uris = {
                person.id for person in statement.relatesToPerson.all()
            }
            for person_to_set in relatesToPerson_to_set:
                if person_to_set["uri"] not in current_persons_as_uris:
                    try:
                        person = Person.objects.get(
                            id=person_to_set["uri"],
                            ipif_repo=ipif_hub_repo_AUTOCREATED,
                        )  ### TODO: MODIFY TO LOOK FOR URIS WELL...NO!!

                    except Person.DoesNotExist:

                        person = Person(
                            identifier=person_to_set["uri"],
                            label=person_to_set["label"],
                            local_id=person_to_set["uri"],
                            modifiedBy="IPIFHUB_AUTOCREATED",
                            modifiedWhen=datetime.date.today(),
                            createdBy="IPIFHUB_AUTOCREATED",
                            createdWhen=datetime.date.today(),
                            inputContentHash=hash_content(person_to_set),
                            ipif_repo=ipif_hub_repo_AUTOCREATED,
                        )
                        person.save()

                    statement.relatesToPerson.add(person)
            statement.save()

            current_persons = {person for person in statement.relatesToPerson.all()}
            persons_to_set_uris = {person["uri"] for person in relatesToPerson_to_set}
            for current_person in current_persons:
                if current_person.id not in persons_to_set_uris:
                    statement.relatesToPerson.remove(current_person)

            statement.save()

        except ValidationError as e:
            raise DataFormatError(f"IPIF JSON 'statement' error: {e}")
        # except Exception as e:
        #    raise DataFormatError(f"ERROR: {e}")

    except Statement.DoesNotExist:  # If does not exist
        print(f"Creating <Statement @id={qid}>")
        try:
            statement = Statement()
            statement.local_id = data["local_id"]
            statement.label = data["label"]
            statement.createdBy = data["createdBy"]
            statement.createdWhen = data["createdWhen"]
            statement.modifiedBy = data["modifiedBy"]
            statement.modifiedWhen = data["modifiedWhen"]
            statement.inputContentHash = input_content_hash

            statement.name = data.get("name", "")
            statement.statementText = data.get("statementText")

            if date := data.get("date"):
                statement.date_label = date.get("label", None)
                statement.date_sortdate = date.get("sortdate", None)

            if st := data.get("statementType"):
                statement.statementType_uri = st.get("uri", None)
                statement.statementType_label = st.get("label", None)

            if role := data.get("role"):
                statement.role_uri = role.get("uri", None)
                statement.role_label = role.get("label", None)

            if memberOf := data.get("memberOf"):
                statement.memberOf_label = memberOf.get("label", None)
                statement.memberOf_uri = memberOf.get("uri", None)

            statement.ipif_repo = ipif_repo

            statement.save()

            current_places_as_uris = {place.uri for place in statement.places.all()}
            for place_to_set in places_to_set:
                if place_to_set["uri"] not in current_places_as_uris:
                    try:
                        place = Place.objects.get(uri=place_to_set["uri"])
                    except Place.DoesNotExist:
                        place = Place(**place_to_set)
                        place.save()
                    statement.places.add(place)

            for person_to_set in relatesToPerson_to_set:
                try:
                    person = Person.objects.get(
                        identifier=person_to_set["uri"],
                        ipif_repo=ipif_hub_repo_AUTOCREATED,
                    )
                except Person.DoesNotExist:
                    person = Person(
                        identifier=person_to_set["uri"],
                        label=person_to_set["label"],
                        local_id=person_to_set["uri"],
                        modifiedBy="IPIFHUB_AUTOCREATED",
                        modifiedWhen=datetime.date.today(),
                        createdBy="IPIFHUB_AUTOCREATED",
                        createdWhen=datetime.date.today(),
                        inputContentHash=hash_content(person_to_set),
                        ipif_repo=ipif_hub_repo_AUTOCREATED,
                    )
                    person.save()

                statement.relatesToPerson.add(person)

            statement.save()
        except ValidationError as e:
            raise DataFormatError(f"IPIF JSON 'meta' error: {e}")


def ingest_person_or_source(entity_class, data, ipif_repo):
    print("DATA", data)
    try:
        validate(data, schema=PERSON_SOURCE_SCHEMA)
    except Exception as e:
        raise DataFormatError(e)

    data["local_id"] = data.pop("@id")

    qid = build_qualified_id(
        ipif_repo.endpoint_uri, entity_class.__name__, data["local_id"]
    )
    uris_to_set = data.pop("uris", [])
    input_content_hash = hash_content(data)

    try:  # Entity exists
        entity = entity_class.objects.get(identifier=qid)

        # If already exists, check whether it's been modified by comparing hashes;
        # if not modified, just return

        if entity.inputContentHash == input_content_hash:
            print(
                f'No change to <{entity_class.__name__} @id="{qid}">; skipping ingest.'
            )
            return NO_CHANGE_TO_DATA
        else:
            print(f"Ingesting <{entity_class.__name__} @id={qid}>")

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
        print(f"Creating <{entity_class.__name__} @id={qid}>")
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


def ingest_factoid(data, ipif_repo):
    try:
        validate(data, schema=FACTOID_SCHEMA)
    except Exception as e:
        raise DataFormatError(e)

    data["local_id"] = data.pop("@id")

    qid = build_qualified_id(ipif_repo.endpoint_uri, "Factoid", data["local_id"])
    input_content_hash = hash_content(data)
    try:  # factoid does exist
        factoid = Factoid.objects.get(identifier=qid)

        if factoid.inputContentHash == input_content_hash:
            print(f'No change to <Factoid @id="{qid}">; skipping ingest.')
            return NO_CHANGE_TO_DATA
        else:
            print(f"Updating <Factoid @id={qid}>")

        factoid.local_id = data["local_id"]
        factoid.createdBy = data["createdBy"]
        factoid.createdWhen = data["createdWhen"]
        factoid.modifiedBy = data["modifiedBy"]
        factoid.modifiedWhen = data["modifiedWhen"]
        factoid.label = data.get("label", "")
        factoid.inputContentHash = input_content_hash
        # factoid.ipif_repo = ipif_repo

        try:
            factoid.person = Person.objects.get(
                identifier=build_qualified_id(
                    ipif_repo.endpoint_uri, "Person", data["person-ref"]["@id"]
                )
            )
        except Person.DoesNotExist:
            raise DataIntegrityError(
                f"IPIF JSON Error: Factoid: {data['local_id']} references non-existant Person @id='{data['person-ref']['@id']}'"
            )

        try:
            factoid.source = Source.objects.get(
                identifier=build_qualified_id(
                    ipif_repo.endpoint_uri, "Source", data["source-ref"]["@id"]
                )
            )
        except Source.DoesNotExist:
            raise DataIntegrityError(
                f"IPIF JSON Error: Factoid: {data['local_id']} references non-existant Source @id='{data['source-ref']['@id']}'"
            )

        current_statements_as_uris = {
            statement.id for statement in factoid.statements.all()
        }
        for statement in data["statement-refs"]:
            try:
                identifier = build_qualified_id(
                    ipif_repo.endpoint_uri, "Statement", statement["@id"]
                )
                if identifier not in current_statements_as_uris:
                    s = Statement.objects.get(identifier=identifier)
                    factoid.statements.add(s)
                    factoid.save()
            except Statement.DoesNotExist:
                raise DataIntegrityError(
                    f"IPIF JSON Error: Factoid: {data['local_id']} references non-existant Statement @id='{statement['@id']}'"
                )

        factoid.save()

        statements_to_add = {
            build_qualified_id(ipif_repo.endpoint_uri, "Statement", s["@id"])
            for s in data["statement-refs"]
        }
        current_statements = {statement for statement in factoid.statements.all()}

        for current_statement in current_statements:

            if current_statement.identifier not in statements_to_add:
                factoid.statements.remove(current_statement)

        factoid.save()

    except Factoid.DoesNotExist:  # Create new factoid
        print(f"Creating <Factoid @id={qid}>")
        factoid = Factoid()
        factoid.local_id = data["local_id"]
        factoid.createdBy = data["createdBy"]
        factoid.createdWhen = data["createdWhen"]
        factoid.modifiedBy = data["modifiedBy"]
        factoid.modifiedWhen = data["modifiedWhen"]
        factoid.label = data.get("label", "")
        factoid.inputContentHash = input_content_hash
        factoid.ipif_repo = ipif_repo

        try:
            factoid.person = Person.objects.get(
                identifier=build_qualified_id(
                    ipif_repo.endpoint_uri, "Person", data["person-ref"]["@id"]
                )
            )
        except Person.DoesNotExist:
            raise DataIntegrityError(
                f"IPIF JSON Error: Factoid: {data['local_id']} references non-existant Person @id='{data['person-ref']['@id']}'"
            )

        try:
            factoid.source = Source.objects.get(
                identifier=build_qualified_id(
                    ipif_repo.endpoint_uri, "Source", data["source-ref"]["@id"]
                )
            )
        except Source.DoesNotExist:
            raise DataIntegrityError(
                f"IPIF JSON Error: Factoid: {data['local_id']} references non-existant Source @id='{data['source-ref']['@id']}'"
            )
        factoid.save()
        for statement in data["statement-refs"]:
            try:
                identifier = build_qualified_id(
                    ipif_repo.endpoint_uri, "Statement", statement["@id"]
                )

                s = Statement.objects.get(identifier=identifier)

                factoid.statements.add(s)
            except Statement.DoesNotExist:
                raise DataIntegrityError(
                    f"IPIF JSON Error: Factoid: {data['local_id']} references non-existant Statement @id='{statement['@id']}'"
                )

        factoid.save()
        # update_factoid_index.delay(factoid.pk)
        # update_person_index.delay(factoid.person.pk)


def ingest_persons(persons_data, ipif_repo):
    # print(persons_data)
    for person in persons_data:
        ingest_person_or_source(Person, person, ipif_repo)


def ingest_sources(sources_data, ipif_repo):
    for source in sources_data:
        ingest_person_or_source(Source, source, ipif_repo)


def ingest_statements(statements_data, ipif_repo):
    for statement in statements_data:
        ingest_statement(statement, ipif_repo)


def ingest_factoids(factoids_data, ipif_repo):
    for factoid in factoids_data:
        ingest_factoid(factoid, ipif_repo)


@transaction.atomic
def ingest_data(endpoint_slug, data):
    # try:
    #    validate(instance=data, schema=FLAT_LIST_SCHEMA)
    # except Exception as e:
    #    raise DataFormatError(e)

    ipif_repo = IpifRepo.objects.get(pk=endpoint_slug)

    # TODO: missing key is not necessarily a problem —— could be
    # pushed in batches!!
    try:
        ingest_persons(data["persons"], ipif_repo)
    except KeyError:
        raise DataFormatError("IPIF JSON is missing 'persons' field")

    try:
        ingest_sources(data["sources"], ipif_repo)
    except KeyError:
        raise DataFormatError("IPIF JSON is missing 'sources' field")

    try:
        ingest_statements(data["statements"], ipif_repo)
    except KeyError:
        raise DataFormatError("IPIF JSON is missing 'statements' field")

    try:
        ingest_factoids(data["factoids"], ipif_repo)
    except KeyError:
        raise DataFormatError("IPIF JSON is missing 'statements' field")
