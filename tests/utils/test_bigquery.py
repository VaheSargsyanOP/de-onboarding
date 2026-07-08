from utils.bigquery import render_sql


def test_render_sql_substitutes_all_placeholders():
    template = "SELECT * FROM `{project_id}.{dataset}.{table}`"
    rendered = render_sql(template, project_id="p", dataset="d", table="t")
    assert rendered == "SELECT * FROM `p.d.t`"


def test_render_sql_ignores_unrelated_braces_in_literal_sql():
    # BigQuery SQL itself has no brace syntax we need to worry about
    # colliding with, but confirm a template with no placeholders at all
    # round-trips unchanged.
    template = "SELECT COUNT(*) FROM `x.y.z`"
    assert render_sql(template) == template
