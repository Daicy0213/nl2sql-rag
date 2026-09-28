from nl2sql.retrieval import RetrievedDoc, lexical_score, rrf_rank


def test_business_alias_beats_unrelated_doc():
    metric = RetrievedDoc("metric.net_sales", "metric", "net_sales", "", ["净销售额", "净收入"], [])
    unrelated = RetrievedDoc("table.products", "table", "analytics.products", "", ["商品"], [])
    assert lexical_score("华东净销售额是多少", metric) > lexical_score("华东净销售额是多少", unrelated)


def test_rrf_promotes_document_found_by_both_channels():
    ranked = rrf_rank(["a", "b", "c"], ["b", "c", "d"])
    assert ranked[0] == "b"
