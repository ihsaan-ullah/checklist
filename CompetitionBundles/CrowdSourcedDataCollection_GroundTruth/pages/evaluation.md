# Evaluation

In the [NeurIPS'24 LaTeX template](https://media.neurips.cc/Conferences/NeurIPS2024/Styles.zip), participants are given in the checklist a placeholder answer [TODO] by default, for all responses. They are then expected to replace it with [Yes], [No], or [NA], as appropriate. We introduce a metric called the **Correctness Score** to evaluate the accuracy of the checklist responses submitted by participants, as assessed by the AI assistant:

$$
C = \frac{\sum_{i=1}^{n} c_i}{n} ~,
$$

where $c_i$ is the AI assessment of the correctness of the $i^{th}$ answer to the checklist, and $n$ is the total number of answers. 
A score of $c_i = 0$ is given if the participant's response is [TODO] or if the AI assistant determines that the answer is incorrect or inconsistent with the paper. Conversely, if the provided answer is deemed correct and consistent, then $c_i = 1$.
The larger the Correctness Score, the better.

The participants can retrieve their results from the "My submissions" tab,  by clicking on their submission, then on VISUALIZATION. The score is visible from the leaderboard only if they post their submission on the leaderboard (optional).