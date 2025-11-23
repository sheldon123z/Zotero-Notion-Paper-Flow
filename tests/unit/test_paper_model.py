"""论文模型单元测试"""
import pytest

class TestPaperModel:
    """Paper模型测试"""

    def test_paper_creation(self, sample_paper):
        """测试论文创建"""
        assert sample_paper.id == "2401.00001"
        assert sample_paper.title == "Test Paper Title"
        assert len(sample_paper.authors) == 2

    def test_paper_to_dict(self, sample_paper):
        """测试论文转字典"""
        paper_dict = sample_paper.to_dict()
        assert isinstance(paper_dict, dict)
        assert paper_dict['id'] == "2401.00001"

    def test_paper_default_values(self):
        """测试论文默认值"""
        from models.paper import Paper

        paper = Paper(id="test", title="Test")
        assert paper.authors == []
        assert paper.tags == []
        assert paper.summary == ""
