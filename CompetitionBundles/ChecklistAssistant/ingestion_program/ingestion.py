# ------------------------------------------
# Imports
# ------------------------------------------

import os
import re
import sys
import fitz
import time
import json
import warnings
import pandas as pd
from datetime import datetime as dt
from openai import OpenAI
import google.generativeai as genai
warnings.filterwarnings("ignore")
from checklist_constants import checklist_data
from constants import GPT_KEY, GEMINI_KEYS
from prompts import PROMPT_3_6_B as PAPER_PROMPT


# ------------------------------------------
# Settings
# ------------------------------------------
# True when running on Codabench
CODABENCH = True
USE_GEMINI = True


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
        text = re.sub(r'\n', ' ', text)
        text = re.sub(r'\-\s*\n', ' ', text)
        text = text.strip()
        return text

    def has_line_numbers(self, text):
        lines = text.split('\n')
        lines_to_iterate = len(lines) if len(lines) < 2000 else 2000
        numbered_lines = []
        for i in range(0, lines_to_iterate):
            numbered_lines.append(lines[i].strip().isdigit())
        if sum(numbered_lines) > int(lines_to_iterate * 0.10):
            return True
        return False

    def clean_paper(self, text):
        paper_has_line_numbers = self.has_line_numbers(text)
        if paper_has_line_numbers:
            # text = re.sub(r'((\d+(\.\d+)?\n)+)(?=\D)(.+)$', r'\2\4', text, flags=re.MULTILINE)
            text = re.sub(r'^(\d+)\n(\d+(\.\d+)?)\n(.+)$', r'\2 \4', text, flags=re.MULTILINE)
        else:
            text = re.sub(r'^(\d+)\n(.+)$', r'\1 \2', text, flags=re.MULTILINE)
        text = re.sub(r'\n\d+\n', r'\n', text)
        text = re.sub(r'\n\-\n', r'\n', text)
        text = re.sub(r'\-\s*\n', '', text)
        # text = re.sub(r'([a-zA-Z]\.\d+)\n', r'\1 ', text)
        # text = re.sub(r'\n\d+', r'\n', text)
        # text = re.sub(r'([a-zA-Z])\n', r'\1 ', text)
        text = text.replace("’", "'")
        text = text.replace("\\'", "'")
        text = text.replace("- ", "")
        processed_text = ""
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if len(line.split()) < 6 and len(line.split()) > 1:
                processed_text += "\n"
                processed_text += line + "\n"
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
                raise ValueError("[-] Error: NeurIPS Paper Checklist not found. Please make sure that the checklist is at the end of the PDF.")

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

        general_guidelines = """If you answer Yes to a question, in the justification please point to the section(s) where related material for the question can be found.
While "Yes" is generally preferable to "No", it is perfectly acceptable to answer "No" provided a proper justification is given (e.g., "error bars are not reported because it would be too computationally expensive" or "we were unable to find the license for the dataset we used").
"""

        checklist_df = pd.DataFrame(columns=['Question', 'Question_Title', 'Answer', 'Justification', 'Guidelines', 'Review', 'Score'])
        try:
            for question_index, checklist_item in enumerate(checklist_data):

                question_title = checklist_item["question_title"]
                question = checklist_item["question"]
                question_guidelines = checklist_item["guidelines"]

                question_regex = re.escape(question)
                pattern = re.compile(rf"Question:\s*{question_regex}(?:.*?Answer:\s*\[(.*?)\].*?Justification:\s*(.*?))(?:Guidelines:\s+(.*?))(?=Question:|\Z)", re.DOTALL)

                mtch = pattern.search(checklist)
                if mtch:
                    answer = mtch.group(1).strip()
                    justification = mtch.group(2).strip() if mtch.group(2).strip() else None
                    # guidelines = mtch.group(3).strip() if mtch.group(3).strip() else None
                    # if guidelines:
                    #     guidelines = self.clean_guidelines(guidelines)

                    if justification is not None and justification.isdigit():
                        justification = None

                else:
                    answer, justification = "Not Found", "Not Found"

                temp_df = pd.DataFrame([
                    {
                        'Question': question,
                        'Question_Title': question_title,
                        'Answer': answer,
                        'Justification': justification,
                        'Guidelines': general_guidelines + question_guidelines}
                ])

                checklist_df = pd.concat([checklist_df, temp_df], ignore_index=True)
            return checklist_df

        except Exception as e:
            raise ValueError(f"[-] Error in extracting answers and justifications: {e}")

    def check_incomplete_questions(self, checklist_df):
        for i, row in checklist_df.iterrows():
            if row["Answer"] in ["TODO", "[TODO]", "Not Found"] or row["Justification"] in ["TODO", "[TODO]", "Not Found"]:
                print(f"\t [!] There seems to be a problem with your answer or justificaiton for Question #: {i+1}")

    def print_prompt(self):
        print(f"[*] Prompt version: {PAPER_PROMPT['name']}")
        print(f"[*] Prompt: {PAPER_PROMPT['value']}\n")

    def get_LLM_feedback(self, paper, checklist_df):

        max_tokens = 1000
        temperature = 1
        top_p = 1
        n = 1

        for index, row in checklist_df.iterrows():

            if USE_GEMINI:
                model = "models/gemini-1.5-pro-latest"
                genai.configure(api_key=GEMINI_KEYS[index])
                client = genai.GenerativeModel(
                    model,
                    generation_config=genai.GenerationConfig(
                        temperature=temperature,
                        top_p=top_p,
                        max_output_tokens=max_tokens,
                        candidate_count=n,
                    ),
                )
            else:
                model = "gpt-4-turbo-preview"
                client = OpenAI(
                    api_key=GPT_KEY,
                )

            question_number = index + 1

            q = row["Question"]
            a = row["Answer"]
            j = row["Justification"]
            g = row["Guidelines"]

            paper_prompt = PAPER_PROMPT["value"]

            paper_prompt = paper_prompt.replace("{q}", q)
            paper_prompt = paper_prompt.replace("{a}", a)
            paper_prompt = paper_prompt.replace("{j}", j)
            paper_prompt = paper_prompt.replace("{g}", g)
            paper_prompt = paper_prompt.replace("{paper}", paper)

            llm_review = ""
            try:
                if USE_GEMINI:
                    messages = [paper_prompt]
                    response = client.generate_content(contents=messages)
                    llm_review = response.text
                else:
                    user_prompt = {
                        "role": "user",
                        "content": paper_prompt
                    }
                    messages = [user_prompt]
                    chat_completion = client.chat.completions.create(
                        model=model,
                        messages=messages,
                        max_tokens=max_tokens,
                        temperature=temperature,
                        top_p=top_p,
                        n=n
                    )
                    llm_review = chat_completion.choices[0].message.content
            except:
                print(f"[-] Error in processing Question #: {question_number}")
                checklist_df.loc[index, 'Review'] = "Error occurred while processing this question!"
                checklist_df.loc[index, 'Score'] = 0
                continue

            score = 0
            text = llm_review

            if text == '' or len(text) < 50:
                print("[!] There seems to be a problem with this review!")

            score_pattern1 = r"Score:\s*([0-9]+(?:\.[0-9]+)?)"
            score_pattern2 = r"\*\*Score\*\*:\s*([0-9]+(?:\.[0-9]+)?)"

            match1 = re.search(score_pattern1, llm_review)
            match2 = re.search(score_pattern2, llm_review)

            if match1:
                score = match1.group(1)
                text = re.sub(r"Score:.*(\n|$)", "", text)
            elif match2:
                score = match2.group(1)
                text = re.sub(r"**Score**:.*(\n|$)", "", text)

            checklist_df.loc[index, 'Review'] = text
            checklist_df.loc[index, 'Score'] = score
            print(f"[+] Question # {question_number}")

            if USE_GEMINI and question_number != 15:
                time.sleep(60)

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

        print("[✔]")

        # -----
        # Load text from PDF
        # -----
        print("[*] Loading and converting PDF to Text")
        paper_text = self.get_pdf_text(pdf_file)
        if paper_text == "":
            raise ValueError("[-] Reading PDF file failed or your PDF has no text! Please check that you have a valid PDF file.")
        print("[✔]")

        # -----
        # Get paper chunks
        # -----
        print("[*] Breaking down paper into chunks and cleaning text")
        self.paper = self.clean(self.get_paper_chunks(paper_text))
        print("[✔]")

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
        # Print prompt
        # -----
        self.print_prompt()

        # -----
        # Get GPT Review
        # -----
        print("[*] Reviewing the paper's checklist")
        self.paper["checklist_df"] = self.get_LLM_feedback(self.paper["paper"], self.paper["checklist_df"])
        print("[✔]")

    def save(self):
        self.save_checklist()
        self.save_title()

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
