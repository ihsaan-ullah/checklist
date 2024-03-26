# ------------------------------------------
# Imports
# ------------------------------------------

import os
import re
import sys
import fitz
import json
import warnings
import pandas as pd
from datetime import datetime as dt
from openai import OpenAI
warnings.filterwarnings("ignore")
from constants import API_KEY


# ------------------------------------------
# Settings
# ------------------------------------------
# True when running on Codabench
CODABENCH = False


# ------------------------------------------
# Ingestion Class
# ------------------------------------------
class Ingestion():

    def __init__(self):

        # Initialize class variables
        self.start_time = None
        self.end_time = None

    def start_timer(self):
        self.start_time = dt.now()

    def stop_timer(self):
        self.end_time = dt.now()

    def get_duration(self):
        if self.start_time is None:
            print("[-] Timer was never started. Returning None")
            return None

        if self.end_time is None:
            print("[-] Timer was never stoped. Returning None")
            return None

        return self.end_time - self.start_time

    def show_duration(self):
        print("\n---------------------------------")
        print(f'[✔] Total duration: {self.get_duration()}')
        print("---------------------------------")

    def set_directories(self):

        # set default directories
        module_dir = os.path.dirname(os.path.realpath(__file__))
        root_dir_name = os.path.dirname(module_dir)

        input_data_dir_name = "input_data"
        output_dir_name = "sample_result_submission"
        program_dir_name = "ingestion_program"
        submission_dir_name = "sample_code_submission"

        if CODABENCH:
            root_dir_name = "/app"
            input_data_dir_name = "input_data"
            output_dir_name = "output"
            program_dir_name = "program"
            submission_dir_name = "ingested_program"

        # Input data directory to read training and test data from
        self.input_dir = os.path.join(root_dir_name, input_data_dir_name)
        # Output data directory to write predictions to
        self.output_dir = os.path.join(root_dir_name, output_dir_name)
        # Program directory
        self.program_dir = os.path.join(root_dir_name, program_dir_name)
        # Directory to read submitted submissions from
        self.submission_dir = os.path.join(root_dir_name, submission_dir_name)

        # Add to path
        sys.path.append(self.input_dir)
        sys.path.append(self.output_dir)
        sys.path.append(self.program_dir)
        sys.path.append(self.submission_dir)

    def clean(self, paper):
        # clean title
        paper["title"] = self.clean_title(paper["title"])

        # clean paper
        paper["paper"] = self.clean_paper(paper["paper"])

        # clean checklist
        paper["checklist"] = self.clean_checklist(paper["checklist"])

        return paper

    def clean_title(self, text):
        text = re.sub(r'\n', '', text)
        text = re.sub(r'\-\s*\n', '', text)
        text = text.strip()
        return text

    def clean_paper(self, text):
        text = re.sub(r'\n\d+', ' ', text)
        text = re.sub(r'\-\s*\n', '', text)
        text = re.sub(r'([a-zA-Z]\.\d+)\n', r'\1 ', text)
        text = re.sub(r'([a-zA-Z])\n', r'\1 ', text)
        text = text.replace("’", "'")
        text = text.replace("\\'", "'")
        text = text.replace("- ", "")
        processed_text = ""
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if len(line.split()) < 6:
                processed_text += '\n'
                processed_text += line + '\n'
            else:
                processed_text += line
                processed_text += ' '
        text = processed_text.strip()
        return text

    def clean_checklist(self, text):
        text = re.sub(r'\n\d+', ' ', text)
        text = re.sub(r'\-\s*\n', '', text)
        text = re.sub(r'  . ', '\n', text)
        text = re.sub(r'([a-zA-Z]\.\d+)\n', r'\1 ', text)
        text = re.sub(r'([a-zA-Z])\n', r'\1 ', text)
        text = text.replace("’", "'")
        text = text.replace("\\'", "'")
        text = text.replace("- ", "")
        text = re.sub(r'\n+', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        return text

    def clean_guidelines(self, text):
        checklist_titles = [
            "Limitations",
            "Theory Assumptions and Proofs",
            "Experimental Result Reproducibility",
            "Open access to data and code",
            "Experimental Setting/Details",
            "Experiment Statistical Significance",
            "Experiments Compute Resources",
            "Code Of Ethics",
            "Broader Impacts",
            "Safeguards",
            "Licenses for existing assets",
            "New Assets",
            "Crowdsourcing and Research with Human Subjects",
            "Institutional Review Board (IRB) Approvals or Equivalent for Research with Human Subjects",
        ]
        for checklist_title in checklist_titles:
            text = text.replace(checklist_title, '')
        return text

    def get_paper_chunks(self, paper_text):

        try:
            # Identify main paper and appendices
            paper_end_index = paper_text.find("NeurIPS Paper Checklist")

            if paper_end_index == -1:
                raise ValueError("[-] Error: NeurIPS Paper Checklist not found")

            paper = paper_text[:paper_end_index]

            # Identify checklist section
            checklist_start_index = paper_end_index
            checklist = paper_text[checklist_start_index:]

            # Identify title
            title_end_index = paper.find("Anonymous Author")
            if title_end_index == -1:
                title = paper.split("\n")[:2]
                title = ''.join(title)
            else:
                title = paper[:title_end_index]

            return {
                "title": title,
                "paper": paper,
                "checklist": checklist
            }
        except ValueError as ve:
            raise ve
        except Exception as e:
            raise Exception(f"[-] Error occurred while extracting paper chunks in the {'paper' if not paper else 'checklist'} section: {e}")

    def get_pdf_text(self, pdf_file):
        pdf_file_path = os.path.join(self.submission_dir, pdf_file)
        paper_text = ""
        with fitz.open(pdf_file_path) as doc:
            for page in doc:
                paper_text += page.get_text()
        return paper_text

    def parse_checklist(self, checklist):

        checklist_questions = [
            "Do the main claims made in the abstract and introduction accurately reflect the paper's contributions and scope?",
            "Does the paper discuss the limitations of the work performed by the authors?",
            "For each theoretical result, does the paper provide the full set of assumptions and a complete (and correct) proof?",
            "Does the paper fully disclose all the information needed to reproduce the main experimental results of the paper to the extent that it affects the main claims and/or conclusions of the paper (regardless of whether the code and data are provided or not)?",
            "Does the paper provide open access to the data and code, with sufficient instructions to faithfully reproduce the main experimental results, as described in supplemental material?",
            "Does the paper specify all the training and test details (e.g., data splits, hyperparameters, how they were chosen, type of optimizer, etc.) necessary to understand the results?",
            "Does the paper report error bars suitably and correctly defined or other appropriate information about the statistical significance of the experiments?",
            "For each experiment, does the paper provide sufficient information on the computer resources (type of compute workers, memory, time of execution) needed to reproduce the experiments?",
            "Does the research conducted in the paper conform, in every respect, with the NeurIPS Code of Ethics https://neurips.cc/public/EthicsGuidelines?",
            "Does the paper discuss both potential positive societal impacts and negative societal impacts of the work performed?",
            "Does the paper describe safeguards that have been put in place for responsible release of data or models that have a high risk for misuse (e.g., pretrained language models, image generators, or scraped datasets)?",
            "Are the creators or original owners of assets (e.g., code, data, models), used in the paper, properly credited and are the license and terms of use explicitly mentioned and properly respected?",
            "Are new assets introduced in the paper well documented and is the documentation provided alongside the assets?",
            "For crowdsourcing experiments and research with human subjects, does the paper include the full text of instructions given to participants and screenshots, if applicable, as well as details about compensation (if any)?",
            "Does the paper describe potential risks incurred by study participants, whether such risks were disclosed to the subjects, and whether Institutional Review Board (IRB) approvals (or an equivalent approval/review based on the requirements of your country or institution) were obtained?"
        ]

        checklist_df = pd.DataFrame(columns=['Question', 'Answer', 'Justification', 'Guidelines', 'Review', 'Correctness_Score'])
        try:
            for question in checklist_questions:
                question_regex = re.escape(question)
                pattern = re.compile(rf"Question:\s+{question_regex}(?:.*?Answer:\s+\[(.*?)\].*?Justification:\s+(.*?))(?:Guidelines:\s+(.*?))(?=Question:|\Z)", re.DOTALL)

                mtch = pattern.search(checklist)
                if mtch:
                    answer = mtch.group(1).strip()
                    justification = mtch.group(2).strip() if mtch.group(2).strip() else None
                    guidelines = mtch.group(3).strip() if mtch.group(3).strip() else None
                    if guidelines:
                        guidelines = self.clean_guidelines(guidelines)

                    if justification is not None and justification.isdigit():
                        justification = None

                else:
                    answer, justification, guidelines = "Not Found", "Not Found", "Not Found"

                temp_df = pd.DataFrame([{'Question': question, 'Answer': answer, 'Justification': justification, 'Guidelines': guidelines}])
                checklist_df = pd.concat([checklist_df, temp_df], ignore_index=True)
            return checklist_df

        except Exception as e:
            raise ValueError(f"[-] Error in extracting answers and justifications: {e}")

    def check_incomplete_questions(self, checklist_df):
        for i, row in checklist_df.iterrows():
            if row["Answer"] in ["TODO", "[TODO]", "Not Found"] or row["Justification"] in ["TODO", "[TODO]", "Not Found"]:
                print(f"\t [!] There seems to be a problem with your answer or justificaiton for Question #: {i}")

    def get_LLM_feedback(self, paper, checklist_df):

        client = OpenAI(
            api_key=API_KEY,
        )

        model = "gpt-4-turbo-preview"
        max_tokens = 1000
        temperature = 1
        top_p = 1
        n = 1

        system_prompt = {
            "role": "system",
            "content":  "You are a computer science researcher currently reviewing a paper for the NeurIPS computer science conference. Your goal is to try to be as objective and truthful as possible in your answers about the answers provided in the 'NeurIPS Paper Checklist'. Your reviews will be used for causal reasoning in determining the quality of the paper."
        }

        for index, row in checklist_df.iterrows():
            q = row["Question"]
            a = row["Answer"]
            j = row["Justification"]
            g = row["Guidelines"]

            user_prompt = {
                "role": "user",
                "content": f"The following is content of the paper you are reviewing. {paper}\n\n\nBased on the content, please review the answer and justification for the following question and provide a brief explanation for the answer and justification you find inconsistent with the paper content. Do not be lenient with the authors, be really critical in your answers. However, also include itemized constructive and actionable suggestions. Use the given guidelines originally provided to the author to answer the question. Also must return a score at the start of the response (Score: 0 if you do not agree with the answer, Score: 1 if you agree and find the answer correct) Socre must be an integer without any formatting.\n\n\n Question: {q}\n Answer: {a}\n Justification: {j}\n Guidelines: {g}"
            }

            messages = [system_prompt, user_prompt]
            chat_completion = client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                n=n
            )

            gpt_review = chat_completion.choices[0].message.content

            score_text_parts = gpt_review.split("Score: ")
            # Extract score and text
            try:
                score = int(score_text_parts[1].split("\n")[0])
            except ValueError:
                score = 0
            text = score_text_parts[1].split("\n", 1)[1].strip()

            checklist_df.loc[index, 'Review'] = text
            checklist_df.loc[index, 'Correctness_Score'] = score

            print(f"[+] Question {index+1}")
        return checklist_df

    def process_papers(self):

        genuine_pdf, adversarial_pdf, truth_adversarial_pdf = None, None, None

        # -----
        # Load PDF from submissions dir
        # -----
        print("[*] Loading PDF papers")
        # get all files from submissions dir
        files = os.listdir(self.submission_dir)
        pdf_files = []
        for filename in files:
            if filename.endswith('.pdf'):
                pdf_files.append(filename)
        num_submitted_papers = len(pdf_files)

        if num_submitted_papers == 0:
            raise FileNotFoundError("[-] No PDF file found in the submission directory")
        elif num_submitted_papers == 1:
            genuine_pdf = pdf_files[0]
            print(f"[!] you have submitted only 1 PDF file: {genuine_pdf}. Considering this as `Genuine Paper`")
        elif num_submitted_papers == 3:
            for file in pdf_files:
                if file.lower().startswith('genuine_'):
                    genuine_pdf = file
                if file.lower().startswith('adversarial_'):
                    adversarial_pdf = file
                if file.lower().startswith('truth_adversarial_'):
                    truth_adversarial_pdf = file

            if genuine_pdf is None or adversarial_pdf is None or truth_adversarial_pdf is None:
                raise ValueError("[-] One or more PDF files have incorrect names. Make sure that they start with `genuine_`, `adversarial_` and `truth_adversarial_`")

            print(f"[+] PDF files: {genuine_pdf} -- {adversarial_pdf} -- {truth_adversarial_pdf}")
        else:
            raise ValueError("[-] Please check that you either submit one PDF (Genuine) or submit three PDFs (Genuine, Adversarial, Truth Adversarial)")

        print("[✔]")

        # -----
        # Load text from PDF
        # -----
        print("[*] Converting PDFs to Text")
        genuine_paper_text, adversarial_paper_text, truth_adversarial_paper_text = "", "", ""
        if genuine_pdf:
            genuine_paper_text = self.get_pdf_text(genuine_pdf)
        if adversarial_pdf:
            adversarial_paper_text = self.get_pdf_text(adversarial_pdf)
        if truth_adversarial_pdf:
            truth_adversarial_paper_text = self.get_pdf_text(truth_adversarial_pdf)
        print("[✔]")

        # -----
        # Get paper chunks
        # -----
        print("[*] Breaking down paper into chunks and cleaning text")
        self.genuine, self.adversarial, self.truth_adversarial = None, None, None
        if genuine_pdf:
            self.genuine = self.clean(self.get_paper_chunks(genuine_paper_text))
        if adversarial_pdf:
            self.adversarial = self.clean(self.get_paper_chunks(adversarial_paper_text))
        if truth_adversarial_pdf:
            self.truth_adversarial = self.clean(self.get_paper_chunks(truth_adversarial_paper_text))
        print("[✔]")

        # -----
        # Parse Checklist
        # -----
        print("[*] Parsing checklist from text")
        if genuine_pdf:
            self.genuine["checklist_df"] = self.parse_checklist(self.genuine["checklist"])
        if adversarial_pdf:
            self.adversarial["checklist_df"] = self.parse_checklist(self.adversarial["checklist"])
        if truth_adversarial_pdf:
            self.truth_adversarial["checklist_df"] = self.parse_checklist(self.truth_adversarial["checklist"])
        print("[✔]")

        # -----
        # Incomplete answers
        # -----
        print("[*] Checking incomplete answers")
        if genuine_pdf:
            print("[*] Genuine Paper")
            self.check_incomplete_questions(self.genuine["checklist_df"])
        if adversarial_pdf:
            print("[*] Adversarial Paper")
            self.check_incomplete_questions(self.adversarial["checklist_df"])
        if truth_adversarial_pdf:
            print("[*] Truth Adversarial Paper")
            self.check_incomplete_questions(self.truth_adversarial["checklist_df"])
        print("[✔]")

        # -----
        # Get GPT Review
        # -----
        print("[*] Asking GPT to review the papers checklist")
        if genuine_pdf:
            print("[*] Genuine Paper")
            self.genuine["checklist_df"] = self.get_LLM_feedback(self.genuine["paper"], self.genuine["checklist_df"])
        if adversarial_pdf:
            print("[*] Adversarial Paper")
            self.adversarial["checklist_df"] = self.get_LLM_feedback(self.adversarial["paper"], self.adversarial["checklist_df"])
        if truth_adversarial_pdf:
            print("[*] Truth Adversarial Paper")
            self.truth_adversarial["checklist_df"] = self.get_LLM_feedback(self.truth_adversarial["paper"], self.truth_adversarial["checklist_df"])
        print("[✔]")

    def save(self, checklist_df, paper_type):

        checklist_file = os.path.join(self.output_dir, f"{paper_type}_checklist.csv")
        checklist_df.replace('NA', 'Not Applicable', inplace=True)
        checklist_df.to_csv(checklist_file, index=False)

    def save_checklists(self):
        print("[*] Saving checklists")

        if self.genuine:
            self.save(self.genuine["checklist_df"], "genuine")
        if self.adversarial:
            self.save(self.adversarial["checklist_df"], "adversarial")
        if self.truth_adversarial:
            self.save(self.truth_adversarial["checklist_df"], "truth_adversarial")

        print("[✔]")

    def save_titles(self):
        print("[*] Saving titles")
        titles_dict = {}
        if self.genuine:
            titles_dict["genuine"] = self.genuine["title"]
        if self.adversarial:
            titles_dict["adversarial"] = self.adversarial["title"]
        if self.truth_adversarial:
            titles_dict["truth_adversarial"] = self.truth_adversarial["title"]

        result_file = os.path.join(self.output_dir, "titles.json")
        with open(result_file, "w") as f_score:
            f_score.write(json.dumps(titles_dict, indent=4))
        print("[✔]")


if __name__ == '__main__':

    print("############################################")
    print("### Ingestion Program")
    print("############################################\n")

    # Init Ingestion
    ingestion = Ingestion()

    ingestion.set_directories()

    # Start timer
    ingestion.start_timer()

    # process paper
    ingestion.process_papers()

    # Save checklist
    ingestion.save_checklists()

    # Save titles
    ingestion.save_titles()

    # Stop timer
    ingestion.stop_timer()

    # Show duration
    ingestion.show_duration()

    print("\n----------------------------------------------")
    print("[✔] Ingestions Program executed successfully!")
    print("----------------------------------------------\n\n")
