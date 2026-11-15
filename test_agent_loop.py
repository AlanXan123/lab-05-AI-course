"""Offline checks of the notebook loop; these do not run or evaluate Qwen."""
import json
from pathlib import Path
import unittest

import lab05_core as core

ROOT = Path(__file__).resolve().parent


def tool_call(name, **arguments):
    return '<tool_call>' + json.dumps({'name': name, 'arguments': arguments}) + '</tool_call>'


class ScriptedModel:
    def __init__(self, replies):
        self.replies = iter(replies)
        self.inputs = []

    def generate(self, messages, **kwargs):
        self.inputs.append([dict(m) for m in messages])
        return core.Generation(next(self.replies), 10, 5)


class AgentLoopTests(unittest.TestCase):
    def setUp(self):
        notebook = json.loads((ROOT / 'lab05_harness.ipynb').read_text(encoding='utf-8'))
        source = next(''.join(c['source']) for c in notebook['cells']
                      if ''.join(c['source']).startswith('def my_agent('))
        self.model = ScriptedModel([])
        self.toolbox = core.Toolbox(core.load_dataset(ROOT / 'data'))
        self.scope = dict(build_messages=core.build_messages, parse_tool_calls=core.parse_tool_calls,
                          llm=self.model, toolbox=self.toolbox)
        exec(compile(source, 'notebook:my_agent', 'exec'), self.scope)
        self.agent = self.scope['my_agent']

    def replies(self, *texts):
        self.model = ScriptedModel(texts)
        self.scope['llm'] = self.model

    def test_final_reply_stops_immediately(self):
        self.replies('ANSWER: NO DATA')
        answer, messages = self.agent('question')
        self.assertEqual(answer, 'ANSWER: NO DATA')
        self.assertEqual([m['role'] for m in messages], ['system', 'user', 'assistant'])

    def test_tool_result_is_visible_to_next_model_call(self):
        self.replies(tool_call('calculate', expression='2 + 3'), 'ANSWER: 5')
        answer, messages = self.agent('Add two and three')
        self.assertEqual(answer, 'ANSWER: 5')
        self.assertEqual(self.model.inputs[1][-1]['role'], 'tool')
        self.assertIn('5', self.model.inputs[1][-1]['content'])
        self.assertEqual(messages[-1]['role'], 'assistant')

    def test_all_calls_in_one_reply_are_executed_in_order(self):
        self.replies(tool_call('list_regions') + tool_call('list_indicators'), 'ANSWER: done')
        _, messages = self.agent('List metadata')
        results = [json.loads(m['content']) for m in messages if m['role'] == 'tool']
        self.assertEqual(results[0], self.toolbox.data.regions)
        self.assertEqual(results[1], list(self.toolbox.data.indicators.values()))

    def test_bare_loop_propagates_unknown_alias_error(self):
        self.replies(tool_call('get_series', region='Nur-Sultan',
                               indicator='unemployment_rate', start_year=2022, end_year=2022))
        with self.assertRaisesRegex(core.ToolError, 'Unknown region'):
            self.agent('q21')
        self.assertEqual(len(self.model.inputs), 1)

    def test_budget_stops_repeated_tool_use(self):
        self.replies(*(tool_call('list_regions') for _ in range(2)))
        answer, messages = self.agent('Keep calling tools', max_steps=2)
        self.assertEqual(answer, '')
        self.assertEqual(len(self.model.inputs), 2)
        self.assertEqual(sum(m['role'] == 'tool' for m in messages), 2)

    def test_zero_budget_does_not_call_model(self):
        answer, messages = self.agent('question', max_steps=0)
        self.assertEqual(answer, '')
        self.assertEqual(len(messages), 2)
        self.assertEqual(self.model.inputs, [])

    def test_lookup_ranking_and_arithmetic_match_reference_conversation(self):
        questions = {q.qid: q for q in core.build_questions(self.toolbox.data)}
        scripts = {
            'q01': [tool_call('get_series', region='Astana', indicator='population',
                              start_year=2024, end_year=2024), 'ANSWER: test'],
            'q07': [tool_call('compare_regions', indicator='population', year=2024), 'ANSWER: test'],
            'q12': [tool_call('get_series', region='Astana', indicator='population'),
                    tool_call('calculate', expression='(12 - 10) / 10 * 100'), 'ANSWER: 20'],
        }
        for qid, replies in scripts.items():
            with self.subTest(qid=qid):
                self.replies(*replies)
                answer, messages = self.agent(questions[qid].text)
                reference_model = ScriptedModel(replies)
                reference = core.run_agent(reference_model, self.toolbox, questions[qid], core.BARE)
                self.assertEqual(self.model.inputs, reference_model.inputs)
                self.assertEqual(core.extract_answer(answer), reference.answer)
                self.assertEqual(sum(m['role'] == 'tool' for m in messages),
                                 sum(e['kind'] == 'tool' for e in reference.trace))


if __name__ == '__main__':
    unittest.main()
