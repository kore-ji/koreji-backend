"""Shared utility functions for LLM response parsing."""
import json
from typing import List, Dict, Any


def parse_question_response(content: str) -> Dict[str, List[str]]:
    """
    Parse LLM JSON response and convert to compact string format.
    
    This is a generic parser that can be used by both tasks and AI services.
    
    Expected input format from LLM:
    {
      "questions": [
        {"question": "...", "suggested_answers": ["A", "B", "C"]},
        ...
      ]
    }
    
    Output format:
    {
      "questions": [
        "問題內容  [A：\"選項1\", B：\"選項2\", C：\"選項3\"]",
        ...
      ]
    }
    """
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        cleaned = content.strip().removeprefix("```json").removesuffix("```").strip()
        data = json.loads(cleaned)

    out: dict = {"questions": []}
    
    raw_questions = data.get("questions", [])
    if not isinstance(raw_questions, list):
        return out

    for q in raw_questions:
        if not isinstance(q, dict):
            continue
            
        q_text = (q.get("question") or "").strip()
        if not q_text:
            continue
            
        answers = q.get("suggested_answers", [])
        if not isinstance(answers, list):
            answers = []

        labels = ["A", "B", "C"]
        parts: list[str] = []
        for i in range(3):
            if i < len(answers) and isinstance(answers[i], str):
                parts.append(f'{labels[i]}："{answers[i]}"')
            else:
                parts.append(f'{labels[i]}："其他"')

        combined = f'{q_text}  [{", ".join(parts)}]'
        out["questions"].append(combined)

    return out
