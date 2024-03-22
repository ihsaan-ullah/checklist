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

    def clean_title(self, text):
        text = re.sub(r'\-\s*\n', '', text)
        text = re.sub(r'\n', '', text)
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
            else:
                title = paper[:title_end_index]

            return title, paper, checklist
        except ValueError as ve:
            raise ve
        except Exception as e:
            raise Exception(f"[-] Error occurred while extracting paper chunks in the {'paper' if not paper else 'checklist'} section: {e}")

    def load_paper(self):

        # -----
        # Load PDF from submissions dir
        # -----
        print("[*] Loading PDF paper")
        # get all files from submissions dir
        files = os.listdir(self.submission_dir)
        pdf_file = None
        for filename in files:
            if filename.endswith('.pdf'):
                pdf_file = filename
                break
        if not pdf_file:
            raise FileNotFoundError("[-] No PDF file found in the submission directory")
        else:
            print(f"[+] PDF file: {pdf_file}")
        pdf_file_path = os.path.join(self.submission_dir, pdf_file)
        print("[✔]")

        # -----
        # Load text from PDF
        # -----
        print("[*] Converting PDF to Text")
        paper_text = ""
        with fitz.open(pdf_file_path) as doc:
            for page in doc:
                paper_text += page.get_text()
        print("[✔]")

        # -----
        # Get paper chunks
        # -----
        print("[*] Breaking down paper into paper and checklist")
        self.paper_title, self.paper, self.checklist = self.get_paper_chunks(paper_text)
        print("[✔]")

        # -----
        # Clean text
        # -----
        print("[*] Cleaning Text")
        # clean title
        self.paper_title = self.clean_title(self.paper_title)

        # clean paper
        self.paper = self.clean_paper(self.paper)

        # clean checklist
        self.checklist = self.clean_checklist(self.checklist)

        print("[✔]")

    def parse_checklist(self):

        print("[*] Converting checklist to DataFrame")
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

        self.checklist_df = pd.DataFrame(columns=['Question', 'Answer', 'Justification', 'Guidelines', 'Review', 'Correctness_Score'])
        try:
            for question in checklist_questions:
                question_regex = re.escape(question)
                # pattern = re.compile(rf"Question:\s+{question_regex}(?:.*?Answer:\s+\[(.*?)\].*?Justification:\s+(.*?))(?=Guidelines:|\Z)", re.DOTALL)
                pattern = re.compile(rf"Question:\s+{question_regex}(?:.*?Answer:\s+\[(.*?)\].*?Justification:\s+(.*?))(?:Guidelines:\s+(.*?))(?=Question:|\Z)", re.DOTALL)

                mtch = pattern.search(self.checklist)
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

                answer = None if answer == "TODO" else answer
                justification = None if justification == "TODO" else justification

                temp_df = pd.DataFrame([{'Question': question, 'Answer': answer, 'Justification': justification, 'Guidelines': guidelines}])
                self.checklist_df = pd.concat([self.checklist_df, temp_df], ignore_index=True)

            print("[✔]")

        except Exception as e:
            raise ValueError(f"[-] Error in extracting answers and justifications: {e}")

    def check_incomplete_questions(self):

        print("[*] Checking incomplete answers")

        for _, row in self.checklist_df.iterrows():
            if row["Answer"] in ["TODO", "Not Found"] or row["Justification"] in ["TODO", "Not Found"]:
                print(f"[!] There seems to be a problem with your answer or justificaiton.\nQuestion: {row['Question']}\nAnswer: {row['Answer']}\nJustification: {row['Justification']}\n")

        print("[✔]")

    def get_LLM_feedback(self):

        print("[*] Asking GPT to review the checklist")
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
            "content":  "You are a computer science researcher currently reviewing a paper for the NeurIPS computer science conference. Your goal is to try to be as objective and truthful as possible in your answers about the answers provided in the 'NeurIPS Papaer Checklist'. Your reviews will be used for causal reasoning in determining the quality of the paper."
        }

        for index, row in self.checklist_df.iterrows():
            q = row["Question"]
            a = row["Answer"]
            j = row["Justification"]
            g = row["Guidelines"]

            user_prompt = {
                "role": "user",
                "content": f"The following is content of the paper you are reviewing. {self.paper}\n\n\nBased on the content, please review the answer and justification for the following question and provide a brief explanation for the answer and justification you find inconsistent with the paper content. Do not be lenient with the authors, be really critical in your answers. However, also include itemized constructive and actionable suggestions. Use the given guideliness originally provided to the author to answer the question. Also must return a score at the start of the response (Score: 0 if you do not agree with the answer, Score: 1 if you agree and find the answer correct):\n Question: {q}\n Answer: {a}\n Justification: {j}\n Guidelines: {g}"
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
            score = int(score_text_parts[1].split("\n")[0])
            text = score_text_parts[1].split("\n", 1)[1].strip()

            self.checklist_df.loc[index, 'Review'] = text
            self.checklist_df.loc[index, 'Correctness_Score'] = score

            print(f"[+] Question {index+1}")

        print("[✔]")

    def save_result(self):
        print("[*] Saving checklist")
        checklist_file = os.path.join(self.output_dir, "checklist.csv")
        self.checklist_df.replace('NA', 'Not Applicable', inplace=True)
        self.checklist_df.to_csv(checklist_file, index=False)
        print("[✔]")

        print("[*] Saving paper title")
        result_file = os.path.join(self.output_dir, "paper.json")
        with open(result_file, "w") as f_score:
            f_score.write(json.dumps({"paper_title": self.paper_title}, indent=4))
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

    # load paper
    ingestion.load_paper()

    # Parse checklist
    ingestion.parse_checklist()

    # check incomplete questions
    ingestion.check_incomplete_questions()

    # Get LLM's feedback
    ingestion.get_LLM_feedback()

    # Save result
    ingestion.save_result()

    # Stop timer
    ingestion.stop_timer()

    # Show duration
    ingestion.show_duration()

    print("\n----------------------------------------------")
    print("[✔] Ingestions Program executed successfully!")
    print("----------------------------------------------\n\n")
