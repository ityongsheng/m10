from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_frontend_assets_exist_and_are_local():
    for name in ("index.html", "app.js", "app.css"):
        path = ROOT / "frontend" / name
        assert path.exists()
        assert path.stat().st_size > 500


def test_frontend_has_required_sections_and_no_generation_label():
    html = (ROOT / "frontend" / "index.html").read_text(encoding="utf-8")
    for section in ("overview", "run", "curve", "anomalies", "alerts", "runs"):
        assert f'id="{section}"' in html
    visible_text = html.replace("/static/app.js", "")
    assert "AI生成" not in visible_text
    assert "AI 生成" not in visible_text


def test_launcher_and_customer_docs_are_present():
    assert (ROOT / "launcher.json").exists()
    assert (ROOT / "start.cmd").exists()
    assert (ROOT / "stop.cmd").exists()
    assert (ROOT / "使用说明.txt").exists()


def test_frontend_exposes_real_pvdaq_preset():
    html = (ROOT / "frontend" / "index.html").read_text(encoding="utf-8")
    js = (ROOT / "frontend" / "app.js").read_text(encoding="utf-8")
    assert 'id="useReal"' in html
    assert "/data/real/pvdaq_2107_2022-06_normalized.csv" in js
