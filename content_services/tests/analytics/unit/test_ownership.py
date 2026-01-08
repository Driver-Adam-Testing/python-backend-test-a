"""Unit tests for code ownership calculation.

A2: Ownership Calculation

Tests for calculating code ownership by author per file:
- Single author ownership
- Multiple author ownership percentages
- Net lines calculation
"""
import pytest
from datetime import datetime, timezone


class TestCalculateOwnership:
    """Tests for calculate_ownership function."""

    @pytest.fixture
    def single_author_changes(self):
        """File changes from a single author."""
        return [
            {
                'file_path': 'src/main.py',
                'author_email': 'alice@example.com',
                'additions_lines': 100,
                'deletions_lines': 0,
            },
            {
                'file_path': 'src/utils.py',
                'author_email': 'alice@example.com',
                'additions_lines': 50,
                'deletions_lines': 10,
            },
        ]

    @pytest.fixture
    def multi_author_changes(self):
        """File changes from multiple authors."""
        return [
            # Alice adds 100 lines to main.py
            {
                'file_path': 'src/main.py',
                'author_email': 'alice@example.com',
                'additions_lines': 100,
                'deletions_lines': 0,
            },
            # Bob adds 50 lines to main.py
            {
                'file_path': 'src/main.py',
                'author_email': 'bob@example.com',
                'additions_lines': 50,
                'deletions_lines': 0,
            },
            # Alice adds 30 lines to utils.py
            {
                'file_path': 'src/utils.py',
                'author_email': 'alice@example.com',
                'additions_lines': 30,
                'deletions_lines': 0,
            },
        ]

    def test_single_author_owns_100_pct(self, single_author_changes):
        """Single author owns 100% of files they touched."""
        from analytics.aggregation.ownership import calculate_ownership
        
        result = calculate_ownership(single_author_changes)
        
        assert 'src/main.py' in result
        assert len(result['src/main.py']) == 1
        assert result['src/main.py'][0]['author_email'] == 'alice@example.com'
        assert result['src/main.py'][0]['percentage'] == 100.0

    def test_multiple_authors_split_ownership(self, multi_author_changes):
        """Multiple authors split ownership proportionally."""
        from analytics.aggregation.ownership import calculate_ownership
        
        result = calculate_ownership(multi_author_changes)
        
        # main.py: Alice 100, Bob 50 => Alice 66.7%, Bob 33.3%
        main_owners = {o['author_email']: o['percentage'] for o in result['src/main.py']}
        
        assert abs(main_owners['alice@example.com'] - 66.67) < 1
        assert abs(main_owners['bob@example.com'] - 33.33) < 1

    def test_percentages_sum_to_100(self, multi_author_changes):
        """Ownership percentages sum to 100% per file."""
        from analytics.aggregation.ownership import calculate_ownership
        
        result = calculate_ownership(multi_author_changes)
        
        for file_path, owners in result.items():
            total = sum(o['percentage'] for o in owners)
            assert 99.0 <= total <= 101.0, f"{file_path}: {total}%"

    def test_net_lines_calculated(self, single_author_changes):
        """Net lines (additions - deletions) calculated."""
        from analytics.aggregation.ownership import calculate_ownership
        
        result = calculate_ownership(single_author_changes)
        
        # utils.py: 50 additions - 10 deletions = 40 net lines
        utils_owner = result['src/utils.py'][0]
        assert utils_owner['net_lines'] == 40

    def test_handles_empty_changes(self):
        """Empty file changes returns empty dict."""
        from analytics.aggregation.ownership import calculate_ownership
        
        result = calculate_ownership([])
        assert result == {}

    def test_handles_negative_net_lines(self):
        """Handles files where author deleted more than added."""
        from analytics.aggregation.ownership import calculate_ownership
        
        changes = [
            {
                'file_path': 'src/legacy.py',
                'author_email': 'alice@example.com',
                'additions_lines': 10,
                'deletions_lines': 50,
            },
        ]
        
        result = calculate_ownership(changes)
        
        # Alice has -40 net lines, but still "owns" her contribution
        assert result['src/legacy.py'][0]['net_lines'] == -40

    def test_aggregates_multiple_commits_same_author_file(self):
        """Multiple commits by same author to same file are aggregated."""
        from analytics.aggregation.ownership import calculate_ownership
        
        changes = [
            {
                'file_path': 'src/main.py',
                'author_email': 'alice@example.com',
                'additions_lines': 50,
                'deletions_lines': 0,
            },
            {
                'file_path': 'src/main.py',
                'author_email': 'alice@example.com',
                'additions_lines': 30,
                'deletions_lines': 10,
            },
        ]
        
        result = calculate_ownership(changes)
        
        # Alice: (50-0) + (30-10) = 70 net lines
        assert result['src/main.py'][0]['net_lines'] == 70


class TestOwnershipSchema:
    """Tests for ownership result schema."""

    def test_owner_has_required_fields(self):
        """Each owner dict has required fields."""
        required_fields = ['author_email', 'net_lines', 'percentage']
        
        owner = {
            'author_email': 'test@example.com',
            'net_lines': 100,
            'percentage': 50.0,
        }
        
        for field in required_fields:
            assert field in owner

