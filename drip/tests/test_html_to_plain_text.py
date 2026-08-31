from drip.utils import html_to_plain_text


class TestHtmlToPlainText:
    """Tests for the html_to_plain_text utility."""

    def test_preserves_link_urls(self):
        """<a> tags should be converted to 'text (url)' format."""
        html = '<a href="http://example.com/">my example</a>'
        result = html_to_plain_text(html)
        assert result == "my example (http://example.com/)"

    def test_link_text_matches_url_no_duplicate(self):
        """When the link text IS the URL, don't duplicate it."""
        html = '<a href="http://example.com/">http://example.com/</a>'
        result = html_to_plain_text(html)
        assert result == "http://example.com/"

    def test_multiple_links(self):
        """Multiple links in one string should all be converted."""
        html = (
            'Visit <a href="http://a.com">A</a> '
            'and <a href="http://b.com">B</a>.'
        )
        result = html_to_plain_text(html)
        assert "A (http://a.com)" in result
        assert "B (http://b.com)" in result

    def test_br_tags_become_newlines(self):
        """<br> and <br/> should be converted to newlines."""
        html = "line1<br>line2<br/>line3"
        result = html_to_plain_text(html)
        assert "line1\nline2\nline3" in result

    def test_block_tags_become_newlines(self):
        """Closing block-level tags should produce newlines."""
        html = "<p>paragraph one</p><p>paragraph two</p>"
        result = html_to_plain_text(html)
        assert "paragraph one" in result
        assert "paragraph two" in result
        # Should be on separate lines
        lines = [line.strip() for line in result.split("\n") if line.strip()]
        assert lines == ["paragraph one", "paragraph two"]

    def test_html_entities_decoded(self):
        """Common HTML entities should be decoded."""
        html = "5 &gt; 3 &amp; 2 &lt; 4"
        result = html_to_plain_text(html)
        assert result == "5 > 3 & 2 < 4"

    def test_strips_remaining_tags(self):
        """Tags without special handling should be stripped."""
        html = "<h2>This</h2> is an <b>example</b> html <strong>body</strong>."
        result = html_to_plain_text(html)
        assert "This" in result
        assert "example" in result
        assert "body" in result
        assert "<" not in result
        assert ">" not in result

    def test_empty_string(self):
        assert html_to_plain_text("") == ""

    def test_none_returns_none(self):
        assert html_to_plain_text(None) is None

    def test_plain_text_passthrough(self):
        """Plain text without HTML should pass through unchanged."""
        text = "Just some plain text."
        assert html_to_plain_text(text) == text

    def test_whitespace_collapsed(self):
        """Excessive whitespace should be collapsed."""
        html = "word1     word2      word3"
        result = html_to_plain_text(html)
        assert result == "word1 word2 word3"

    def test_link_with_extra_attributes(self):
        """Links with extra attributes (class, target) should still work."""
        html = '<a href="http://example.com/" class="btn" target="_blank">Click here</a>'
        result = html_to_plain_text(html)
        assert result == "Click here (http://example.com/)"
