
import unittest
from unittest.mock import patch

import reboot.agent as agent


class ResearchPipelineTests(unittest.TestCase):

    def test_relevant_paper_ranks_above_unrelated_paper(self):
        papers = [
            {
                "title": "Sensor Allocation against Attackers",
                "abstract": "Regret minimization for sensor allocation.",
                "url": "https://arxiv.org/abs/1111.1111",
            },
            {
                "title": "Double Neural Counterfactual Regret Minimization",
                "abstract": (
                    "Counterfactual regret minimization in "
                    "imperfect information games."
                ),
                "url": "https://arxiv.org/abs/2222.2222",
            },
        ]

        queries = [
            "counterfactual regret minimization",
            "poker imperfect information games",
        ]

        ranked = agent._rank_papers(papers, queries)

        self.assertEqual(
            ranked[0]["title"],
            "Double Neural Counterfactual Regret Minimization",
        )
        self.assertGreater(
            ranked[0]["_reboot_score"],
            ranked[1]["_reboot_score"],
        )

    @patch.object(agent, "MAX_FULL_TEXTS", 1)
    @patch.object(agent, "search_papers")
    @patch.object(agent, "fetch_paper_text")
    @patch.object(agent.time, "sleep")
    @patch.object(agent, "_build_queries")
    def test_research_deduplicates_papers_and_tracks_queries(
        self, mock_queries, mock_sleep, mock_fetch, mock_search
    ):
        query_one = "counterfactual regret minimization"
        query_two = "poker imperfect information games"

        mock_queries.return_value = [query_one, query_two]

        cfr_paper = {
            "title": "Double Neural Counterfactual Regret Minimization",
            "abstract": (
                "Counterfactual regret minimization for "
                "imperfect information games."
            ),
            "url": "https://arxiv.org/abs/2222.2222",
        }

        unrelated_paper = {
            "title": "Sensor Allocation against Attackers",
            "abstract": "Regret minimization for sensor allocation.",
            "url": "https://arxiv.org/abs/1111.1111",
        }

        mock_search.side_effect = [
            [cfr_paper, unrelated_paper],
            [dict(cfr_paper)],
        ]

        mock_fetch.return_value = {
            "status": "partial",
            "reason": "Opening pages extracted.",
            "text": "Extracted paper text.",
        }

        queries, papers = agent._find_research({})

        urls = [paper["url"] for paper in papers]

        self.assertEqual(queries, [query_one, query_two])
        self.assertEqual(len(urls), len(set(urls)))
        self.assertEqual(len(papers), 2)

        result = next(
            paper for paper in papers
            if paper["url"] == cfr_paper["url"]
        )

        self.assertEqual(
            result["matched_queries"],
            [query_one, query_two],
        )
        self.assertEqual(result["full_text_status"], "partial")
        self.assertTrue(result["_reboot_score"] > 0)

        # Only one paper should have been selected for extraction.
        self.assertEqual(mock_fetch.call_count, 1)

    @patch.object(agent, "MAX_FULL_TEXTS", 1)
    @patch.object(agent, "search_papers")
    @patch.object(agent, "fetch_paper_text")
    @patch.object(agent.time, "sleep")
    @patch.object(agent, "_build_queries")
    def test_pdf_failure_does_not_crash_research(
        self, mock_queries, mock_sleep, mock_fetch, mock_search
    ):
        mock_queries.return_value = [
            "counterfactual regret minimization"
        ]

        mock_search.return_value = [
            {
                "title": "Counterfactual Regret Minimization",
                "abstract": (
                    "Counterfactual regret minimization "
                    "for imperfect information games."
                ),
                "url": "https://arxiv.org/abs/2222.2222",
            }
        ]

        mock_fetch.side_effect = OSError("PDF download failed")

        queries, papers = agent._find_research({})

        self.assertEqual(len(queries), 1)
        self.assertEqual(len(papers), 1)
        self.assertEqual(
            papers[0]["full_text_status"],
            "unavailable",
        )
        self.assertIn("PDF extraction failed", papers[0]["full_text_note"])


if __name__ == "__main__":
    unittest.main()
