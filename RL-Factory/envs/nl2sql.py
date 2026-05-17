import re
import json
import string
import random
import torch
from .base import Env

import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))

project_root = os.path.abspath(os.path.join(current_dir, "../../.."))


if project_root not in sys.path:
    sys.path.append(project_root)

from utils import sync_compare_sql

class NL2SQLEnv(Env):
    def __init__(self, config, centralized_actor=None):
        super().__init__(config, centralized_actor)
        self.use_verify_tool = False

    # NOTE: Add your reward calculation rules here!
    def _compute_score_with_rules(self, data, tokenizer, if_val=False):

        def em_check(prediction, golden_answer, db_id):
            status, result = sync_compare_sql(prediction, golden_answer, db_id)
            return result == '正确'

        def extract_solution(solution_str):
            """Extract the equation from the solution string."""
            think_pattern = r'<think>.*?</think>'
            solution_str = re.sub(think_pattern, '', solution_str, flags=re.DOTALL)

            answer_pattern = r'<final_sql>(.*?)</final_sql>'
            match = re.finditer(answer_pattern, solution_str, re.DOTALL)
            matches = list(match)
            if len(matches) <= 0:
                return None
            
            return matches[-1].group(1).strip()

        def compute_score_em(solution_str, ground_truth, db_id, format_score=0.0, score=1.):
            """The scoring function for exact match (EM).

            Args:
                solution_str: the solution text
                ground_truth: the ground truth
                method: the method to extract the solution, choices are 'strict' and 'flexible'
                format_score: the score for the format
                score: the score for the correct answer
            """
            answer = extract_solution(solution_str=solution_str)
            do_print = random.randint(1, 64) == 1
            
            if do_print:
                print(f"--------------------------------")
                print(f"Golden answers: {ground_truth['target']}")
                print(f"Extracted answer: {answer}")
                print(f"Solution string: {solution_str}")
            
            answer_format_score = format_score if check_alternate_tags(solution_str, r"</?answer>") else (-1 * format_score)
            num_score=0
            if check_alternate_tags(solution_str, r"</?tool_call>"):
                tool_call_format_score = format_score
                pattern = r"<tool_call>(.*?)</tool_call>"
                matches = re.findall(pattern, solution_str, re.DOTALL)
                if len(matches) == 0:
                    tool_call_format_score = -1 * format_score
                else:
                    success_num, fail_num = 0, 0
                    for idx, content in enumerate(matches):
                        content_stripped = content.strip()
                        try:
                            parsed = json.loads(content_stripped)
                            success_num += 1
                        except json.JSONDecodeError:
                            fail_num += 1
                    
                    tool_call_format_score = 2 * format_score * success_num / (success_num + fail_num) - format_score
                    if success_num + fail_num > 2:
                        tool_call_format_score -= 0.5 * format_score
                        num_score = -format_score
            else:
                tool_call_format_score = -0.5 * format_score
                
            #total_format_score = tool_call_format_score + answer_format_score
            total_format_score = answer_format_score+num_score

            if answer is None:
                return -1 * format_score + 0.5 * total_format_score
            else:
                if em_check(answer, ground_truth, db_id):
                    return score + 0.5 * total_format_score
                else:
                    return total_format_score

        def check_alternate_tags(text, tag_pattern):
            # 用正则提取标签名
            match = re.match(r"<\/?(\w+)>", re.findall(tag_pattern, text)[0]) if re.findall(tag_pattern, text) else None
            if not match:
                return False
            tagname = match.group(1)
            open_tag = f"<{tagname}>"
            close_tag = f"</{tagname}>"

            tags = re.findall(tag_pattern, text)

            stack = []
            for tag in tags:
                if tag == open_tag:
                    if stack:
                        # 发现有嵌套，说明不是严格交替
                        return False
                    stack.append(tag)
                elif tag == close_tag:
                    if not stack:
                        # 没有对应的开放标签，说明标签不配对
                        return False
                    stack.pop()
            # 最终栈必须为空，才是严格交替
            return len(stack) == 0


        format_score = 0.0 if if_val else 0.1
        scores = []
        for i in range(len(data)):
            data_item = data[i]  # DataProtoItem
            
            # process the data_item to the token and decode them
            processed_data = self._process_data(data_item=data_item, tokenizer=tokenizer)
            ground_truth, db_id, response_str = processed_data['ground_truth'], processed_data['db_id'], processed_data['response_str']
            
            # reserved for compatibility
            prompt_str, data_source, extra_info = processed_data['prompt_str'], processed_data['data_source'], processed_data['extra_info']

            score = compute_score_em(response_str, ground_truth, db_id, format_score=format_score)
            scores.append([score])

        return scores
