# ------------------------------------------
# Imports
# ------------------------------------------

import os
import re
import sys
import fitz
import json
import yaml
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

    def load_yaml(self, yaml_file):
        yaml_file_path = os.path.join(self.submission_dir, yaml_file)

        with open(yaml_file_path, 'r') as file:
            yaml_data = yaml.safe_load(file)

        if not yaml_data:
            raise ValueError("[-] The YAML file is empty or invalid.")

        for key, value in yaml_data.items():
            # Check if key/question is an integer between 1 and 15
            if not isinstance(key, int) or not 1 <= key <= 15:
                raise ValueError("[-] Invalid key: Keys must be integers between 1 and 15.")

            # Check if value is 0, 0.5, or 1
            if value not in [0, 0.5, 1]:
                raise ValueError("[-] Invalid value: Values must be 0, 0.5, or 1.")

        return yaml_data

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

        checklist_question_titles = [
            "Claims",
            "Limitations",
            "Theoritical assumptions and proofs",
            "Experiments reproducibility",
            "Code and data accessibility",
            "Experimental settings/details",
            "Error bars",
            "Compute resources",
            "NeurIPS code of ethics",
            "Impacts",
            "Safeguards",
            "Credits",
            "Documentation",
            "Human subjects",
            "Risks"
        ]

        checklist_df = pd.DataFrame(columns=['Question', 'Question_Title', 'Answer', 'Justification', 'Guidelines', 'Review', 'Score'])
        try:
            for question_index, question in enumerate(checklist_questions):
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

                temp_df = pd.DataFrame([{'Question': question, 'Question_Title': checklist_question_titles[question_index], 'Answer': answer, 'Justification': justification, 'Guidelines': guidelines}])
                checklist_df = pd.concat([checklist_df, temp_df], ignore_index=True)

            return checklist_df

        except Exception as e:
            raise ValueError(f"[-] Error in extracting answers and justifications: {e}")

    def check_incomplete_questions(self, checklist_df):
        for i, row in checklist_df.iterrows():
            if row["Answer"] in ["TODO", "[TODO]", "Not Found"] or row["Justification"] in ["TODO", "[TODO]", "Not Found"]:
                print(f"\t [!] There seems to be a problem with your answer or justificaiton for Question #: {i+1}")

    def get_LLM_feedback(self, paper, checklist_df, ground_truth):

        client = OpenAI(
            api_key=API_KEY,
        )

        model = "gpt-4-turbo-preview"
        max_tokens = 1000
        temperature = 1
        top_p = 1
        n = 1

        """
        You are a NeuIPS reviewer and you are verifying that the NeurIPS checklist answers to the paper fulfill the guidelines and are answered in a correct and complete manner.  
        Based on the content of this paper, identify any discrepancies between the authors' justification for specific questions and the actual paper content. 
        It's acceptable to respond "No" or "Not Applicable" with valid reasoning. Afterwards, provide detailed, actionable feedback based on the initial guidelines provided to the authors, aiming to improve the paper's quality and adherence to NeurIPS standards. 
        Conclude your review with a score in a separate line: 0 if significant issues need addressing, 1 if the submission meets NeurIPS's highest quality standards, or 0.5 if the decision is unclear. This score will guide the authors on the necessity and importance of your feedback.
        """

        system_prompt = {
            "role": "system",
            "content":  "As a reviewer for NeurIPS, you are tasked with ensuring that the responses provided in the NeurIPS checklist for a submitted paper adhere to the conference's guidelines. Your responsibilities include verifying the accuracy and completeness of each response in relation to the content of the paper. If discrepancies or inconsistencies are identified, you should provide detailed, constructive feedback to improve the paper’s adherence to NeurIPS standards. Finally, conclude your review by assigning a final score based on the paper's alignment with the guidelines."
        }

        for index, row in checklist_df.iterrows():

            question_number = index + 1
            skip_question = ground_truth is not None and question_number not in ground_truth

            if skip_question:
                print(f"[!] Skipping Question # {question_number}")
                continue

            q = row["Question"]
            a = row["Answer"]
            j = row["Justification"]
            g = row["Guidelines"]

            paper_prompt = f"Paper Content: {paper}\nQuestion from Checklist: {q}\nAuthor's Answer: {a}\nAuthor's Justification for the Answer: {j}\nInitial Guidelines Provided to Authors: {g}\n\n"
            discrepencies_prompt = "Discrepancies: Are there any discrepancies between the justification provided by the authors and the actual paper content? If yes, describe them. Note that No or NA/Not Applicable answers provided by authors are acceptable as long as their justification is consistent with the paper content.\n\n"
            feedback_prompt = "Feedback: Based on the guidelines and the content of the paper, offer detailed and actionable feedback to enhance the paper’s quality.\n\n"
            score_prompt = "Score:\n0 if significant issues need addressing,\n1 if the paper meets NeurIPS's highest quality standards,\n0.5 if the decision is unclear. This score will guide the authors on the necessity and importance of your feedback. Make sure that score is shown in a new line in this format `Score: score_value` and there is no content after the score."

            user_prompt = {
                "role": "user",
                "content": paper_prompt + discrepencies_prompt + feedback_prompt + score_prompt
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

            score = 99
            text = gpt_review
            score_pattern = r"Score:\s*([0-9]+(?:\.[0-9]+)?)"
            match = re.search(score_pattern, gpt_review)
            if match:
                score = match.group(1)
                text = re.sub(r"Score:.*(\n|$)", "", text)
            checklist_df.loc[index, 'Review'] = text
            checklist_df.loc[index, 'Score'] = score
            print(f"[+] Question # {question_number}")

        return checklist_df

    def process_papers(self):

        # -----
        # Load PDF from submissions dir
        # -----
        print("[*] Loading PDF paper")
        # get all files from submissions dir
        files = os.listdir(self.submission_dir)
        pdf_file = None
        for file in files:
            if file.endswith('.pdf'):
                pdf_file = file
                break

        if not pdf_file:
            raise ValueError("[-] No PDF file found in the submission directory!")
        print(f"[+] PDF file: {pdf_file}")

        ground_truth_file = f"{pdf_file.split('.pdf')[0]}.yaml"
        if ground_truth_file not in files:
            print(f"[!] Ground Truth YAML file not found!. This may happen if your YAML file is not named as: {ground_truth_file}")
        else:
            print(f"[+] YAML file: {ground_truth_file}")

        print("[✔]")

        # -----
        # Load text from PDF
        # -----
        print("[*] Loading and converting PDF to Text")
        paper_text = self.get_pdf_text(pdf_file)
        print("[✔]")

        # -----
        # Get paper chunks
        # -----
        print("[*] Breaking down paper into chunks and cleaning text")
        self.paper = self.clean(self.get_paper_chunks(paper_text))
        print("[✔]")

        # -----
        # Load Ground Truth Scores
        # -----
        if ground_truth_file:
            print("[*] Loading Ground Truth YAML")
            self.paper["ground_truth"] = self.load_yaml(ground_truth_file)
            print("[✔]")
        else:
            self.paper["ground_truth"] = None

        # -----
        # Parse Checklist
        # -----
        print("[*] Parsing checklist from text")
        self.paper["checklist_df"] = self.parse_checklist(self.paper["checklist"])
        print("[✔]")

        # -----
        # Incomplete answers
        # -----
        print("[*] Checking incomplete answers")
        self.check_incomplete_questions(self.paper["checklist_df"])
        print("[✔]")

        # -----
        # Get GPT Review
        # -----
        print("[*] Asking GPT to review the papers checklist")
        self.paper["checklist_df"] = self.get_LLM_feedback(self.paper["paper"], self.paper["checklist_df"], self.paper["ground_truth"])
        print("[✔]")

    def save(self):
        self.save_checklist()
        self.save_title()
        self.save_ground_truth()

    def save_checklist(self):
        print("[*] Saving checklists")
        checklist_file = os.path.join(self.output_dir, "paper_checklist.csv")
        self.paper["checklist_df"].replace('NA', 'Not Applicable', inplace=True)
        self.paper["checklist_df"].replace('N/A', 'Not Applicable', inplace=True)
        self.paper["checklist_df"].replace('[NA]', 'Not Applicable', inplace=True)
        self.paper["checklist_df"].replace('[N/A]', 'Not Applicable', inplace=True)
        self.paper["checklist_df"].to_csv(checklist_file, index=False)
        print("[✔]")

    def save_title(self):
        print("[*] Saving title")
        titles_dict = {"paper_title": self.paper["title"]}
        result_file = os.path.join(self.output_dir, "titles.json")
        with open(result_file, "w") as f_score:
            f_score.write(json.dumps(titles_dict, indent=4))
        print("[✔]")

    def save_ground_truth(self):
        if self.paper["ground_truth"]:
            print("[*] Saving Ground Truth")
            ground_truth_file = os.path.join(self.output_dir, "ground_truth.json")
        with open(ground_truth_file, "w") as f_score:
            f_score.write(json.dumps(self.paper["ground_truth"], indent=4))
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

    # Save result
    ingestion.save()

    # Stop timer
    ingestion.stop_timer()

    # Show duration
    ingestion.show_duration()

    print("\n----------------------------------------------")
    print("[✔] Ingestions Program executed successfully!")
    print("----------------------------------------------\n\n")
