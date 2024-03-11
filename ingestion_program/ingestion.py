# ------------------------------------------
# Imports
# ------------------------------------------

import os
import fitz 
import re
import pandas as pd
from datetime import datetime as dt
import warnings
import sys
warnings.filterwarnings("ignore")


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

    def clean_text(self, text):
        text = re.sub(r'\n\d+\n', ' ', text)
        text = re.sub(r'\-\n', '', text)
        text = re.sub(r'\n+', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        text = text.replace("’", "'")
        text = text.replace("\\'", "'")
        text = text.replace("- ", "")
        text = text.strip()
        return text

    def get_paper_chunks(self, paper_text):

        try:
            # Identify main paper section
            main_paper_end_index = paper_text.find("NeurIPS Paper Checklist")
            if main_paper_end_index == -1:
                raise ValueError("Error: NeurIPS Paper Checklist not found")

            main_paper = paper_text[:main_paper_end_index]

            # Identify checklist section
            checklist_start_index = main_paper_end_index
            checklist_end_index = paper_text.find("For initial submissions, do not include any information that would break anonymity, such as the institution conducting the review.") + len("For initial submissions, do not include any information that would break anonymity, such as the institution conducting the review.")
            if checklist_end_index == -1:
                raise ValueError("Error: End of checklist not found")

            checklist = paper_text[checklist_start_index:checklist_end_index]

            # Appendices section
            appendices_start_index = checklist_end_index
            appendices = paper_text[appendices_start_index:]

            return main_paper, checklist, appendices
        except ValueError as ve:
            raise ve
        except Exception as e:
            raise Exception(f"Error occurred while extracting paper chunks in the {'main paper' if not main_paper else 'checklist' if not checklist else 'appendices'} section: {e}")

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
        # Clean text
        # -----
        print("[*] Cleaning Text")
        paper_text = self.clean_text(paper_text)
        print("[✔]")

        # -----
        # Get paper chunks
        # -----
        print("[*] Breaking down paper into main paper, checklist and appendices")
        self.main_paper, self.checklist, self.appendices = self.get_paper_chunks(paper_text)
        print("[✔]")

    def parse_checklist(self):

        checklist_questions = [
            "Do the main claims made in the abstract and introduction accurately reflect the paper's contributions and scope?",
            "Does the research conducted in the paper conform, in every respect, with the NeurIPS Code of Ethics https://neurips.cc/public/EthicsGuidelines?",
            "Does the paper discuss both potential positive societal impacts and negative societal impacts of the work performed?",
            "Does the paper discuss the limitations of the work performed by the authors?",
            "For each theoretical result, does the paper provide the full set of assumptions and a complete (and correct) proof?",
            "Does the paper fully disclose all the information needed to reproduce the main experimental results of the paper to the extent that it affects the main claims and/or conclusions of the paper (regardless of whether the code and data are provided or not)?",
            "Does the paper provide open access to the data and code, with sufficient instructions to faithfully reproduce the main experimental results, as described in supplemental material?",
            "Does the paper specify all the training and test details (e.g., data splits, hyperparameters, how they were chosen, type of optimizer, etc.) necessary to understand the results?",
            "Does the paper report error bars suitably and correctly defined or other appropriate information about the statistical significance of the experiments?",
            "For each experiment, does the paper provide sufficient information on the computer resources (type of compute workers, memory, time of execution) needed to reproduce the experiments?",
            "Does the paper describe safeguards that have been put in place for responsible release of data or models that have a high risk for misuse (e.g., pretrained language models, image generators, or scraped datasets)?",
            "Are the creators or original owners of assets (e.g., code, data, models), used in the paper, properly credited and are the license and terms of use explicitly mentioned and properly respected?",
            "Are new assets introduced in the paper well documented and is the documentation provided alongside the assets?",
            "For crowdsourcing experiments and research with human subjects, does the paper include the full text of instructions given to participants and screenshots, if applicable, as well as details about compensation (if any)?",
            "Does the paper describe potential risks incurred by study participants, whether such risks were disclosed to the subjects, and whether Institutional Review Board (IRB) approvals (or an equivalent approval/review based on the requirements of your country or institution) were obtained?",            
        ]

        self.checklist_df = pd.DataFrame(columns=['Question', 'Answer', 'Justification'])

        try:
            for question in checklist_questions:
                question_regex = re.escape(question)
                pattern = re.compile(rf"Question:\s+{question_regex}(?:.*?Answer:\s+\[(.*?)\].*?Justification:\s+(.*?))(?=Guidelines:|\Z)", re.DOTALL)

                mtch = pattern.search(self.checklist)
                if mtch:
                    answer = mtch.group(1).strip()
                    justification = mtch.group(2).strip() if mtch.group(2).strip() else None
                    if justification is not None and justification.isdigit():
                        justification = None

                else:
                    answer, justification = "Not Found", "Not Found"

                answer = None if answer == "TODO" else answer
                justification = None if justification == "TODO" else justification

                temp_df = pd.DataFrame([{'Question': question, 'Answer': answer, 'Justification': justification}])
                self.checklist_df = pd.concat([self.checklist_df, temp_df], ignore_index=True)

        except Exception as e:
            raise ValueError(f"Error in extracting answers and justifications: {e}")

    def save_checklist(self):
        print("[*] Saving checklist dataframe")
        result_file = os.path.join(self.output_dir, "checkist.csv")
        self.checklist_df.to_csv(result_file, index=False)
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

    # Save checklist
    ingestion.save_checklist()

    # Stop timer
    ingestion.stop_timer()

    # Show duration
    ingestion.show_duration()

    print("\n----------------------------------------------")
    print("[✔] Ingestions Program executed successfully!")
    print("----------------------------------------------\n\n")
