# Instructions to prepare a pair of genuine and adversarial papers for the Codabench challenge


### 1. **Getting the paper template:**  
Clone the [Overleaf NeurIPS template](https://media.neurips.cc/Conferences/NeurIPS2024/Styles.zip)  that includes the NeurIPS'24 checklist to create a new project, which we will call "genuine paper"

### 2. **Filling out and saving the Genuine paper:**  
Horseshoe-fit one of your OWN papers (regardless whether this is a NeurIPS paper) to a "genuine paper" project AND fill out the checklist to the best of your knowledge.  
**IMPORTANT:** For this version of the paper, please provide answers as truthful as possible, with the goal that the LLM checker should give you a 100% correct score to your checklist. Therefore the checklist answers are both your honest answers and the presumed ground truth of the answers.  
Save the PDF as `genuine_PaperTitle.pdf`.

### 3. **Filling out and saving the Adversarial paper and its Ground Truth version:**  
Clone the "genuine paper" project and create an "adversarial paper" project. Include in this version of the paper subtle mistakes that a human reviewer would catch, but that an LLM might fail to identify. You may also make changes to the checklist to try to confuse the LLM into thinking that you are providing good answers when they are actually bad. The answers do NOT need to be truthful.  
Save the PDF as `adversarial_PaperTitle.pdf` 

Therefore, to evaluate the LLM on this paper, we need to get the ground truth of the checklist answers. To that end: Clone the "adversarial paper" project, and re-fill the checklist with HONEST answers (that is if you did not compute error bars, answer “No” in the corresponding checklist question. In the justification of your honest answers, explain what the mistakes that you planted are.  
Save the PDF as `truth_adversarial_PaperTitle.pdf` 

### 4. **Codabench submission:**  
Create one zip file with all the three pdfs:  
`papers.zip`: contains  `genuine_paper_title.pdf`, `adversarial_paper_title.pdf` and `truth_adversarial_paper_title.pdf`  
Make three submissions to the [Codabench Competition](https://www.codabench.org/competitions/2338/?secret_key=9684015e-a9bd-45de-955b-e92f79799763)  using this zip file.
