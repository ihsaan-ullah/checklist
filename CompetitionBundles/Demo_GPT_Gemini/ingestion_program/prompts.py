
PROMPT_3_5 = {
    "name": "Prompt 3.5",
    "value": """
You are provided with a “Paper” to be submitted to the NeurIPS conference. You are assisting the authors in preparing their “Answer” to one checklist “Question”. Please examine carefully the proposed author's “Answer” and the proposed author's “Justification” provided, and identify any discrepancies with the actual ”Paper” content, for this specific “Question”, taking into account the “Guidelines” provided to authors. Afterwards, provide itemized, actionable feedback, based on the “Guidelines”, aiming to improve the “Paper” quality. Concentrate on a few of the most significant improvements that can be made, and write in terse technical English.
Conclude your review with a score for this specific “Question”, in a separate line:
1: The paper is acceptable without carrying out the proposed improvements.
0.5: The recommended improvements should be made to enhance the likelihood of acceptance, though no fatal flaws exist.
0: The issues identified are critical and must be resolved, as they could almost certainly cause rejection if unaddressed.
Make sure that the score is shown in a new line in this format “Score: score_value” and there is no content after the score.
Question: {q}
Answer: {a}
Justification: {j}
Guidelines: {g}
Paper: {paper}
"""
}


PROMPT_3_6_A = {
    "name": "Prompt 3.6 A",
    "value": """
You are provided with a “Paper” to be submitted to the NeurIPS conference. You are assisting the authors in preparing their “Answer” to one checklist “Question”. Please examine carefully the proposed author's “Answer” and the proposed author's “Justification” provided, and identify any discrepancies with the actual ”Paper” content, for this specific “Question”, taking into account the “Guidelines” provided to authors.  Afterwards, provide itemized, actionable feedback, based on the “Guidelines”, aiming to improve the paper quality. Concentrate on a few of the most significant improvements that can be made, and write in terse technical English.  Please note that the Authors' Proposed Justification (if any) is not expected to contain anything more than a reference to the relevant section in the “Paper” (although it is fine if it contains more details).
Conclude your review with a score for this specific “Question”, in a separate line: 
1: Everything OK or mild issues
0.5: Needs improvements. Use this score sparingly.
0: Critical issues 
Make sure that score is shown in a new line in this format “Score: score_value” and there is no content after the score.
Question: {q}
Answer: {a}
Justification: {j}
Guidelines: {g}
Paper: {paper}
"""
}

PROMPT_3_6_B = {
    "name": "Prompt 3.6 B",
    "value": """
You are provided with a “Paper” to be submitted to the NeurIPS conference. You are assisting the authors in preparing their “Answer” to one checklist “Question”. Please examine carefully the proposed author's “Answer” and the proposed author's “Justification” provided, and identify any discrepancies with the actual ”Paper” content, for this specific “Question”, taking into account the “Guidelines” provided to authors.  Afterwards, provide itemized, actionable feedback, based on the “Guidelines”, aiming to improve the paper quality. Concentrate on a few of the most significant improvements that can be made, and write in terse technical English. While Authors' Proposed Answer is generally preferred to be a "Yes", it is acceptable to answer "No" or "NA" provided a proper Authors' Proposed Justification is given (e.g., "error bars are not reported because it would be too computationally expensive" or "we were unable to find the license for the dataset we used"). If the Authors' Proposed Answer is Yes, the Authors' Proposed Justification for the Answer should point to the section(s) within which related material for the question can be found. Note that the Authors' Proposed Justification is not expected to contain anything else (although it is fine if it contains more details).
Conclude your review with a score for this specific “Question”, in a separate line: 
1: Everything OK or mild issues
0.5: Needs improvements. Use this score sparingly.
0: Critical issues 
Make sure that score is shown in a new line in this format “Score: score_value” and there is no content after the score.
Question: {q}
Answer: {a}
Justification: {j}
Guidelines: {g}
Paper: {paper}
"""
}

PROMPT_3_6_B_Finally = {
    "name": "Prompt 3.6 B Finally",
    "value": """
You are provided with a “Paper” to be submitted to the NeurIPS conference. You are assisting the authors in preparing their “Answer” to one checklist “Question”. Please examine carefully the proposed author's “Answer” and the proposed author's “Justification” provided, and identify any discrepancies with the actual ”Paper” content, for this specific “Question”, taking into account the “Guidelines” provided to authors.  Afterwards, provide itemized, actionable feedback, based on the “Guidelines”, aiming to improve the paper quality. Concentrate on a few of the most significant improvements that can be made, and write in terse technical English. While Authors' Proposed Answer is generally preferred to be a "Yes", it is acceptable to answer "No" or "NA" provided a proper Authors' Proposed Justification is given (e.g., "error bars are not reported because it would be too computationally expensive" or "we were unable to find the license for the dataset we used"). If the Authors' Proposed Answer is Yes, the Authors' Proposed Justification for the Answer should point to the section(s) within which related material for the question can be found. Note that the Authors' Proposed Justification is not expected to contain anything else (although it is fine if it contains more details).
Finally, after performing all previous steps, conclude your review with a score for this specific “Question”, in a separate line: 
1: Everything OK or mild issues
0.5: Needs improvements. Use this score sparingly.
0: Critical issues 
Make sure that score is shown in a new line in this format “Score: score_value” and there is no content after the score.
Question: {q}
Answer: {a}
Justification: {j}
Guidelines: {g}
Paper: {paper}
"""
}

PROMPT_3_6_B_Khuong_single_line = {
    "name": "Prompt 3.6 B Khuong Single Line",
    "value": """
You are provided with a “Paper” to be submitted to the NeurIPS conference. You are assisting the authors in preparing their “Answer” to one checklist “Question”. Please examine carefully the proposed author's “Answer” and the proposed author's “Justification” provided, and identify any discrepancies with the actual ”Paper” content, for this specific “Question”, taking into account the “Guidelines” provided to authors.  Afterwards, provide itemized, actionable feedback, based on the “Guidelines”, aiming to improve the paper quality. Concentrate on a few of the most significant improvements that can be made, and write in terse technical English. While Authors' Proposed Answer is generally preferred to be a "Yes", it is acceptable to answer "No" or "NA" provided a proper Authors' Proposed Justification is given (e.g., "error bars are not reported because it would be too computationally expensive" or "we were unable to find the license for the dataset we used"). If the Authors' Proposed Answer is Yes, the Authors' Proposed Justification for the Answer should point to the section(s) within which related material for the question can be found. Note that the Authors' Proposed Justification is not expected to contain anything else (although it is fine if it contains more details). Conclude your review with a score for this specific “Question”, in a separate line (1: Everything OK or mild issues; 0.5: Needs improvements. Use this score sparingly; 0: Critical issues). Make sure that score is shown in a new line in this format “Score: score_value” and there is no content after the score.
Question: {q}
Answer: {a}
Justification: {j}
Guidelines: {g}
Paper: {paper}
"""
}

PROMPT_3_6_B_Khuong_single_line_finally = {
    "name": "Prompt 3.6 B Khuong Single Line",
    "value": """
You are provided with a “Paper” to be submitted to the NeurIPS conference. You are assisting the authors in preparing their “Answer” to one checklist “Question”. Please examine carefully the proposed author's “Answer” and the proposed author's “Justification” provided, and identify any discrepancies with the actual ”Paper” content, for this specific “Question”, taking into account the “Guidelines” provided to authors.  Afterwards, provide itemized, actionable feedback, based on the “Guidelines”, aiming to improve the paper quality. Concentrate on a few of the most significant improvements that can be made, and write in terse technical English. While Authors' Proposed Answer is generally preferred to be a "Yes", it is acceptable to answer "No" or "NA" provided a proper Authors' Proposed Justification is given (e.g., "error bars are not reported because it would be too computationally expensive" or "we were unable to find the license for the dataset we used"). If the Authors' Proposed Answer is Yes, the Authors' Proposed Justification for the Answer should point to the section(s) within which related material for the question can be found. Note that the Authors' Proposed Justification is not expected to contain anything else (although it is fine if it contains more details). Finally, after performing all previous steps, conclude your review with a score for this specific “Question”, in a separate line (1: Everything OK or mild issues; 0.5: Needs improvements. Use this score sparingly; 0: Critical issues). Make sure that score is shown in a new line in this format “Score: score_value” and there is no content after the score.
Question: {q}
Answer: {a}
Justification: {j}
Guidelines: {g}
Paper: {paper}
"""
}

PROMPT_3_6_B_Khuong_start_end = {
    "name": "Prompt 3.6 B Khuong Start End",
    "value": """
You are provided with a “Paper” to be submitted to the NeurIPS conference. You are assisting the authors in preparing their “Answer” to one checklist “Question”. Please examine carefully the proposed author's “Answer” and the proposed author's “Justification” provided, and identify any discrepancies with the actual ”Paper” content, for this specific “Question”, taking into account the “Guidelines” provided to authors.  Afterwards, provide itemized, actionable feedback, based on the “Guidelines”, aiming to improve the paper quality. Concentrate on a few of the most significant improvements that can be made, and write in terse technical English. While Authors' Proposed Answer is generally preferred to be a "Yes", it is acceptable to answer "No" or "NA" provided a proper Authors' Proposed Justification is given (e.g., "error bars are not reported because it would be too computationally expensive" or "we were unable to find the license for the dataset we used"). If the Authors' Proposed Answer is Yes, the Authors' Proposed Justification for the Answer should point to the section(s) within which related material for the question can be found. Note that the Authors' Proposed Justification is not expected to contain anything else (although it is fine if it contains more details). Finally, after performing all previous steps, conclude your review with a score for this specific “Question”, in a separate line (1: Everything OK or mild issues; 0.5: Needs improvements. Use this score sparingly; 0: Critical issues). Make sure that score is shown in a new line in this format “Score: score_value” and there is no content after the score.
Question: 
<START OF QUESTION>
{q}
<END OF QUESTION>
Answer: 
<START OF ANSWER>
{a}
<END OF ANSWER>
Justification:
<START OF JUSTIFICATION>
{j}
<END OF JUSTIFICATION>
Guidelines:
<START OF GUIDELINES>
{g}
<END OF GUIDELINES>
Paper:
<START OF PAPER>
{paper}
<END OF PAPER>
"""
}
