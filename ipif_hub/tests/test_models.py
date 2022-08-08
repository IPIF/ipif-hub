import datetime
import json

from django.db import IntegrityError
from django.test import TestCase, override_settings
from django.core.management import call_command

from ipif_hub.models import Factoid, Person, IpifRepo, Source, Statement
from ipif_hub.search_indexes import PersonIndex


test_repo_no_slug = {
    "endpoint_name": "TestRepo",
    "endpoint_uri": "http://test.com/",
    "refresh_frequency": "daily",
    "refresh_time": datetime.time(0, 0, 0),
    "endpoint_is_ipif": False,
    "description": "A test repo",
    "provider": "University of Test",
}

created_modified = {
    "createdWhen": datetime.date(2022, 3, 1),
    "createdBy": "researcher1",
    "modifiedWhen": datetime.date(2022, 4, 1),
    "modifiedBy": "researcher2",
}


@override_settings(
    CELERY_ALWAYS_EAGER=True,
    CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
    broker_url="memory://",
    backend="memory",
)
class TestIpifRepoModel(TestCase):
    def test_create_ipif_repo_without_endpoint_slug_raises_exception(self):
        repo = IpifRepo(**test_repo_no_slug)
        with self.assertRaises(IntegrityError):
            repo.save()

    def test_create_repo_succeeds_with_endpoint_slug(self):
        repo = IpifRepo(endpoint_slug="testrepo", **test_repo_no_slug)
        repo.save()


@override_settings(
    CELERY_ALWAYS_EAGER=True,
    CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
    broker_url="memory://",
    backend="memory",
)
class TestCreateEntity(TestCase):
    def setUp(self):
        # Clear the Solr index using management command
        call_command("clear_index", interactive=False, verbosity=0)

        # Create a repo
        self.repo = IpifRepo(endpoint_slug="testrepo", **test_repo_no_slug)
        self.repo.save()

    def tearDown(self) -> None:
        call_command("clear_index", interactive=False, verbosity=0)
        return super().tearDown()

    def test_get_repo(self):
        self.assertEqual(self.repo.pk, IpifRepo.objects.first().pk)

    def test_create_person_and_correct_id(self):
        p = Person(local_id="person1", ipif_repo=self.repo, **created_modified)
        p.save()

        # Test the qualified uri works
        uri_id = p.build_uri_id_from_slug("person1")
        self.assertEqual(uri_id, "http://test.com/persons/person1")

    def test_created_person_in_db(self):
        p = Person(local_id="person1", ipif_repo=self.repo, **created_modified)
        p.save()

        looked_up_p = Person.objects.get(pk="http://test.com/persons/person1")
        self.assertEqual(looked_up_p.pk, p.pk)

    def test_create_person_and_correct_id_when_id_is_uri(self):
        # If the id is already a URL, we can use that instead
        p = Person(
            local_id="http://test.com/persons/person1",
            ipif_repo=self.repo,
            **created_modified
        )
        p.save()

        # Test the qualified uri works
        uri_id = p.build_uri_id_from_slug("http://test.com/persons/person1")
        self.assertEqual(uri_id, "http://test.com/persons/person1")

    def test_entity_is_in_haystack(self):
        """Test created person is pushed to Haystack on save"""
        p = Person(local_id="person1", ipif_repo=self.repo, **created_modified)
        p.save()

        pi = PersonIndex.objects.filter(
            id="ipif_hub.person.http://test.com/persons/person1"
        )[0]
        self.assertEqual(pi.pk, p.pk)

    def test_related_entity_triggers_index_update(self):
        p = Person(local_id="person1", ipif_repo=self.repo, **created_modified)
        p.save()

        pi = PersonIndex.objects.filter(
            id="ipif_hub.person.http://test.com/persons/person1"
        )[0]

        pi_data = json.loads(pi.pre_serialized)
        self.assertEqual(pi_data["@id"], "http://test.com/persons/person1")

        # Check that no factoid-refs yet added
        self.assertFalse(pi_data["factoid-refs"])

        s = Source(local_id="source1", ipif_repo=self.repo, **created_modified)
        s.save()
        st = Statement(
            local_id="statement1",
            ipif_repo=self.repo,
            **created_modified,
            name="John Smith"
        )
        st.save()

        f = Factoid(local_id="factoid1", ipif_repo=self.repo, **created_modified)
        f.person = p
        f.source = s
        f.save()
        f.statement.add(st)
        f.save()
        import time

    def test_create_factoid(self):

        p = Person.objects.create(
            local_id="person1", ipif_repo=self.repo, **created_modified
        )
        p.save()

        s = Source(local_id="source1", ipif_repo=self.repo, **created_modified)
        s.save()
        st = Statement(
            local_id="statement1",
            ipif_repo=self.repo,
            **created_modified,
            name="John Smith"
        )
        st.save()

        f = Factoid(local_id="factoid1", ipif_repo=self.repo, **created_modified)
        f.person = p
        f.source = s
        f.save()
        f.statement.add(st)
        f.save()

        pi = PersonIndex.objects.filter(
            id="ipif_hub.person.http://test.com/persons/person1"
        )[0]
        pi_json = json.loads(pi.pre_serialized)
        self.assertTrue(pi_json["factoid-refs"])
        self.assertEqual(
            pi_json["factoid-refs"][0]["source-ref"]["@id"],
            "http://test.com/sources/source1",
        )
        self.assertEqual(
            pi_json["factoid-refs"][0]["statement-refs"][0]["@id"],
            "http://test.com/statements/statement1",
        )
