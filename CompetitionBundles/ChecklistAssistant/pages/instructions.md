# Instructions

## Preparing submissions

As an author of NeurIPS'24 paper, please follow the [CFP intructions](https://neurips.cc/Conferences/2024/CallForPapers). For the purpose of making submissions on this platform, please use the [NeurIPS'24 LaTeX template](https://media.neurips.cc/Conferences/NeurIPS2024/Styles.zip), which includes the paper checklist at the end of the paper, after references and all appendices. There is a limit on the length of the papers of 15,000 words (about 35 pages). Longer papers will be truncated.

Please **only submit papers of which you are a co-author.** Fill out the checklist honestly and as correctly as possible.  We welcome only genuine papers that are advanced draft versions of your NeurIPS'24 submissions.

## Submitting

Zip the PDF of your paper and enter it via the **"My submissions" tab**. Only zip the PDF file without the parent directory, do not include other files. Give to your file a recognizable name to identify your submissions easily.


## Viewing results

Processing your submission may take at least 15 minutes, possibly more if the system is congested Please return to the "My submissions" tab later. Once the submission has been processed, the detailed feedback can be retrieved by clicking on the eye icon <i class="icon grey eye eye-icon"></i> in front of the submission.

## Debugging

If you encounter problems, please report them on the forum and we will address them as soon as possible.

We provide a [Sample Paper Submission](https://www.codabench.org/datasets/download/24e27426-4478-49da-af79-594646142f31/). However, we do NOT recommend to submit is "as is", because we have limited compute availability and this would only contribute to congest our system. Also this would count towards your maximum number of allowed submissions. Only use it if you experience problems, for debug purposes. If your computer automatically unzips it, remember to re-zip when you submit it.

## Known issues

While some of the recommendations are useful, there may be both false positive and false negative answers. Be vigilant. We noticed in particular:

* The system tends to ask for detailed checklist justifications from the authors, which might be non necessary. 
* The system may be too picky and ask for excessive non-technical details in the paper,. This could be detrimental because of the limited space, if this would reduce too much the technical content. Check the guidelines and remain concise.
* The system does not always find provided information. Refer to sections both by number and name in your checklist justifications, e.g. “Details provided in Section 3: Experiments” is better than “Details provided in Section 3”.
* For the theory question (checklist Q3), the system often complains when there is no theory in the paper. It does not understand proofs, do not consider that proofs are verified, even if it says so.
* It does not follow links. Furthermore, it sometimes complains that providing a link (e.g., to code+instructions in a GitHub repository) is insufficient. 
* The system often complains about missing error bars because it does not have access to the figures. It also does not have a very good understanding of statistics. Do not take its recommendations on face value.
* The system handles poorly even the simplest adversarial attacks, like substituting a paragraph of your paper by a paragraph of another paper.
* The answers are not all formatted in the same way. We preferred not to constrain the model, to let it best judge of the level of details and what to highlight.