# Evaluation
This challenge serves a dual purpose: assisting authors in verifying their checklist and stress-testing the AI assistant. Consequently, we employ two types of metrics. The first one is a **Correctness Score**, designed to offer participants feedback on the accuracy of their checklist responses. The second metric is the **Resilience Score**, which assesses the AI assistant's ability to withstand attempts by participants to mislead it through the introduction of subtle errors or inaccurate responses that are difficult to detect. 

## Metrics


### Correctness Score
In the [NeurIPS'24 LaTeX template](https://media.neurips.cc/Conferences/NeurIPS2024/Styles.zip), participants are given in the checklist a placeholder answer [TODO] by default, for all responses. They are then expected to replace it with [Yes], [No], or [NA], as appropriate. We introduce a metric called the **Correctness Score** to evaluate the accuracy of the checklist responses submitted by participants, as assessed by the AI assistant:

$$
C = \frac{\sum_{i=1}^{n} c_i}{n} ~,
$$

where $c_i$ is the AI assessment of the correctness of the $i^{th}$ answer to the checklist, and $n$ is the total number of answers. 
A score of $c_i = 0$ is given if the participant's response is [TODO] or if the AI assistant determines that the answer is incorrect or inconsistent with the paper. Conversely, if the provided answer is deemed correct and consistent, then $c_i = 1$.
The larger the Correctness Score, the better.

### Resilience Score
In addition to submitting a Genuine papers (G), which is (or could be) an actual quality NeurIPS submission (complemented by a diligently completed checklist), the participants may submit variants of their paper:

* An Adversarial paper (A): This version includes deliberately inserted errors in the paper and inaccurate responses in the checklist.
* Truth adversarial paper (T): This is the same paper as paper (A), but accompanied by a checklist that contains truthful answers. It acknowledges any errors and offers as "justification" a detailed explanation of the inserted inaccuracies. This version serves as the "ground truth" for accurate checklist responses.

Therefore, the ability of the AI to identify incorrect responses can be evaluated. We define the **Resilience Score** as:

$$
\text{R} = \frac{\sum_{i=1}^{N} \textbf{1}(c_i = g_i)} {n} ~.
$$

where $c_i$ is the AI assessment of the $i^{th}$ answer in the ``Aversarial'' paper and $g_i = \textbf{1}(a_i = t_i)$ is **ground truth** for the correctness score ($a_i$ representing the (possibly inaccurate) answer given to question $i$ in the Adversarial paper (A), and $t_i$ is the corresponding honest ground truth answer provided in the associated "Truth adversarial" paper (T). The higher the resilience score, the more effectively the LLM assistant has resisted adversarial attacks and identified planted errors. 

![Metrics](https://clopinet.com/images/workflow.png)

### Combined Score
As explained in the Instructions tab, participants are expected to either submit a Genuine paper (G), or a triplet of papers (G, A, T).
If they submit a triplet (G, A, T), they will receive three correctness scores $C_G, C_A, C_T$, and a Resilience Score $R$ (computed from papers A, paper T and the AI results for G). If they only submit G, they will still obtain an assessment of their paper and a Correctness Score $C_G$, but they will be given default scores $C_A=0, C_T=0, R=1$.

We propose a combined score, which captures the effectiveness of the participant's submission:

$$
S = C_G ~ C_A ~ (1-R) ~ C_T  ~.
$$

This score rewards the participants for jointly providing: 

* a quality Genuine paper with a correct checklist, yielding a high $C_G$,
* an Adversarial paper with a deceiving checklist (with incorrect answers that go undetected), resulting in a high Correctness Score $C_A$, but a low Resilience score $R$,
* a Truth Adversarial paper with accurate answers and good justifications, yielding a high $C_T$.

The product $C_A (1-R)$ captures well the effectiveness of the design of the **Adversarial** paper (A). If participants are successful in subtly embedding errors, the paper A, incorrectly deemed accurate by the LLM assistant, is expected to receive a high correctness score $C_A$ and a low Resilience Score $R$. On the other hand, if the Resilience Score $R$ is high (indicating few errors were overlooked by the LLM) and the Correctness Score $C_A$ is low, this suggests that the adversarial paper's effectiveness is limited. 

Our score $S$ multiplies $C_A (1-R)$ by $C_G$ and $C_T$, because it is also important to reward the participants for having high $C_G$ and $C_T$ scores, to ensure that they correctly fill out the checklist of the Genuine and Truth Adversarial papers. In particular, it would be possible to obtain a high $C_A (1-R)$ by submitting a fake paper A that has no mistakes and a correctly filled out checklist (e.g., the genuine paper itself) and a fake T paper, containing reversed answers, to minimize the score $R$. The last condition of having a high $C_T$ is important to avoid this.

All scores will be reported on the leaderboard, but the ranking of submissions will be made according to the score $S$. Hence, the participants submitting only paper G will have the lower possible ranking score of 0. This should encourage them to submit adversarial papers.