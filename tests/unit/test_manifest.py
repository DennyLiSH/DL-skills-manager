"""Tests for manifest module."""

from __future__ import annotations

from pathlib import Path

from dl_skills_manager.core.manifest import (
    add_skill_to_manifest,
    ensure_project_manifest_dir,
    get_installed_skills,
    get_project_manifest_path,
    read_project_manifest,
    remove_skill_from_manifest,
    write_project_manifest,
)


class TestGetProjectManifestPath:
    """Tests for get_project_manifest_path function."""

    def test_returns_correct_path(self, tmp_path: Path) -> None:
        """Test manifest path is .claude/skills/skills.toml."""
        result = get_project_manifest_path(tmp_path)
        expected = tmp_path / ".claude" / "skills" / "skills.toml"
        assert result == expected


class TestEnsureProjectManifestDir:
    """Tests for ensure_project_manifest_dir function."""

    def test_creates_directory(self, tmp_path: Path) -> None:
        """Test directory is created."""
        result = ensure_project_manifest_dir(tmp_path)
        expected = tmp_path / ".claude" / "skills"
        assert expected.exists()
        assert result == expected


class TestReadProjectManifest:
    """Tests for read_project_manifest function."""

    def test_returns_empty_dict_when_missing(self, tmp_path: Path) -> None:
        """Test returns empty manifest when manifest doesn't exist."""
        result = read_project_manifest(tmp_path)
        assert result == {"skills": {}}

    def test_reads_existing_manifest(self, tmp_path: Path) -> None:
        """Test reading an existing manifest."""
        manifest_path = get_project_manifest_path(tmp_path)
        manifest_path.parent.mkdir(parents=True)
        manifest_path.write_text(
            """[skills.code-review]
source = "~/.skills-repo/skills/code-review"
version = "2026.03.23"
"""
        )

        result = read_project_manifest(tmp_path)

        assert "code-review" in result["skills"]
        assert result["skills"]["code-review"]["version"] == "2026.03.23"


class TestWriteProjectManifest:
    """Tests for write_project_manifest function."""

    def test_creates_manifest_file(self, tmp_path: Path) -> None:
        """Test manifest file is created."""
        manifest = {
            "skills": {
                "code-review": {
                    "source": "~/.skills-repo/skills/code-review",
                    "version": "2026.03.23",
                }
            }
        }

        write_project_manifest(tmp_path, manifest)

        manifest_path = get_project_manifest_path(tmp_path)
        assert manifest_path.exists()

    def test_overwrites_existing_manifest(self, tmp_path: Path) -> None:
        """Test existing manifest is overwritten."""
        manifest_path = get_project_manifest_path(tmp_path)
        manifest_path.parent.mkdir(parents=True)
        manifest_path.write_text("[skills.old]")

        new_manifest = {"skills": {"new-skill": {"source": "path", "version": "1.0"}}}
        write_project_manifest(tmp_path, new_manifest)

        result = read_project_manifest(tmp_path)
        assert "old" not in result["skills"]
        assert "new-skill" in result["skills"]


class TestGetInstalledSkills:
    """Tests for get_installed_skills function."""

    def test_returns_empty_list_when_no_manifest(self, tmp_path: Path) -> None:
        """Test empty list when manifest doesn't exist."""
        result = get_installed_skills(tmp_path)
        assert result == []

    def test_parses_installed_skills(self, tmp_path: Path) -> None:
        """Test parsing installed skills."""
        manifest = {
            "skills": {
                "code-review": {
                    "source": "~/.skills-repo/skills/code-review",
                    "version": "2026.03.23",
                },
                "design-review": {
                    "source": "~/.skills-repo/skills/design-review",
                    "version": "2026.03.20",
                },
            }
        }
        write_project_manifest(tmp_path, manifest)

        result = get_installed_skills(tmp_path)

        assert len(result) == 2
        names = {s.name for s in result}
        assert "code-review" in names
        assert "design-review" in names


class TestAddSkillToManifest:
    """Tests for add_skill_to_manifest function."""

    def test_adds_skill(self, tmp_path: Path) -> None:
        """Test adding a skill to manifest."""
        add_skill_to_manifest(
            tmp_path,
            "code-review",
            Path("~/.skills-repo/skills/code-review"),
            "2026.03.23",
        )

        result = get_installed_skills(tmp_path)
        assert len(result) == 1
        assert result[0].name == "code-review"
        assert result[0].version == "2026.03.23"


class TestRemoveSkillFromManifest:
    """Tests for remove_skill_from_manifest function."""

    def test_removes_existing_skill(self, tmp_path: Path) -> None:
        """Test removing an existing skill."""
        manifest = {
            "skills": {
                "code-review": {"source": "path", "version": "1.0"},
                "design-review": {"source": "path2", "version": "2.0"},
            }
        }
        write_project_manifest(tmp_path, manifest)

        remove_skill_from_manifest(tmp_path, "code-review")

        result = get_installed_skills(tmp_path)
        assert len(result) == 1
        assert result[0].name == "design-review"

    def test_does_nothing_for_nonexistent_skill(self, tmp_path: Path) -> None:
        """Test removing nonexistent skill doesn't error."""
        manifest = {"skills": {"code-review": {"source": "path", "version": "1.0"}}}
        write_project_manifest(tmp_path, manifest)

        remove_skill_from_manifest(tmp_path, "nonexistent")

        result = get_installed_skills(tmp_path)
        assert len(result) == 1
