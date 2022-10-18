from haystack.backends.solr_backend import SolrEngine, SolrSearchBackend


class AutoCommitSolrSearchBackend(SolrSearchBackend):
    def update(self, index, iterable, commit=False):
        super(AutoCommitSolrSearchBackend, self).update(index, iterable, commit=commit)

    def remove(self, obj_or_string, commit=True):
        super(AutoCommitSolrSearchBackend, self).remove(obj_or_string, commit=commit)


class AutoCommitSolrEngine(SolrEngine):
    """the built-in Solr engine in Haystack performs a manual commit after each update/add/remove/clear. This
    is really slow. Solr is configured by default to auto-commit changes every 15 seconds, so there is no need to
    commit manually on every update.
    """

    backend = AutoCommitSolrSearchBackend
