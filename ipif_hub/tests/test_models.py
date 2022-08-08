import datetime

from django.db import IntegrityError
from django.test import TestCase

from ipif_hub.models import Person, IpifRepo


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


class TestIpifRepoModel(TestCase):
    def test_create_ipif_repo_without_endpoint_slug_raises_exception(self):
        repo = IpifRepo(**test_repo_no_slug)
        with self.assertRaises(IntegrityError):
            repo.save()

    def test_create_repo_succeeds_with_endpoint_slug(self):
        repo = IpifRepo(endpoint_slug="testrepo", **test_repo_no_slug)
        repo.save()


class TestCreateEntity(TestCase):
    def setUp(self):
        self.repo = IpifRepo(endpoint_slug="testrepo", **test_repo_no_slug)
        self.repo.save()

    def test_get_repo(self):
        self.assertEqual(self.repo.pk, IpifRepo.objects.first().pk)

    def test_create_person_and_correct_id(self):
        p = Person(local_id="person1", ipif_repo=self.repo, **created_modified)
        p.save()

        # Test the qualified uri works
        uri_id = p.build_uri_id_from_slug("person1")
        self.assertEqual(uri_id, "http://test.com/persons/person1")

    def test_create_person_and_correct_id_when_id_is_uri(self):
        p = Person(
            local_id="http://test.com/persons/person1",
            ipif_repo=self.repo,
            **created_modified
        )
        p.save()

        # Test the qualified uri works
        uri_id = p.build_uri_id_from_slug("http://test.com/persons/person1")
        self.assertEqual(uri_id, "http://test.com/persons/person1")
