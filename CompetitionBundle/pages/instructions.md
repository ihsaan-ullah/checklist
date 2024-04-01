# Instructions

The authors of NeurIPS'24 papers should follow the [CFP intructions](https://neurips.cc/Conferences/2024/CallForPapers). For the purpose of making submissions on this platform, please use the [NeurIPS'24 LaTeX template](https://media.neurips.cc/Conferences/NeurIPS2024/Styles.zip), which includes the paper checklist, at the bottom. Please **only submit papers of which you are a co-author.**

All submissions should be made as **zip file** to the **"My submissions" tab**. 

## Checklist assistant phase

In this phase, we only accept **Genuine** (G) paper.

Prepare **a zip file containing a PDF of your G paper**, including at the bottom the checklist, filled out using the **predefined macros** of the [NeurIPS'24 LaTeX template]. Please fill out the checklist honestly and as correctly as possible. G papers are meant to be advanced draft versions of your NeurIPS'24 submissions. However, you may format some of your own papers submitted elsewhere in that format, and submit them, for test purposes, provided that you make best efforts to provide a good paper with a correctly answered checklist. See the Evaluation page for details on the score.

## Adversarial phase

In this phase, we accept triplets (G, A, T) of papers:  **Genuine** (G), **Adversarial** (A), and **Truth adversarial** (T).
While G papers are "good" papers with a checklist filled out with best effort, like in the previous phase, A and T papers are **2 identical copies of the G paper**, in which the authors purposely planted errors to test the resilience of the assistant. **They only differ in the checklist.** The checklist of the A version includes answers that are not truthful. For instance, it could simply be a copy of the checklist of the G paper. In contrast, the checklist of the T version should include only honest answers, hence admit to errors or limitations by answering [No] or [NA] to some questions, then provide a detailed explanation of such errors or limitations as justification. See the Evaluation page for details on the score and how to make successful submissions.

The workflow to prepare a triplet is as follows:

* Prepare a G paper, as in the "Assistant Phase".
* Make a T copy of G and prepare an adversarial version in which you purposely plant errors in the body of the paper or the appendices. Replace the answers in the G checklist by **truthful answers**, admitting to the errors or limitations that you introduced, and provide **detailed explanation of such errors or limitations as justification**. This version of the paper serves to provide ground truth for the checklist answers of the A paper. We find it is easier to prepare T before A.
* Make a copy A of T, and replace the T checklist by the G checklist or change the answers of T to make them non truthful or flawed in some other manner. This version should be designed to make the assistant fail to identify flaws, limitations, or inexactitudes in the paper.

Save the PDFs of all 3 versions, respecting this nomenclature:
* G: genuine_PaperTitle.pdf.
* T: truth_adversarial_PaperTitle.pdf
* A: adversarial_PaperTitle.pdf

Zip all 3 papers together (without zipping the directory in which you out them) and submit the zip file to the "My Submissions" tab.

## Results

Once the submission has been processed, its score will appear, and the detailed feedback can be retrieved by clicking on the submission, then on the "VISUALIZATION" tab.

![VISUALIZATION](https://clopinet.com/images/visualisation.jpg)