# ------------------------------------------
# Imports
# ------------------------------------------
import os
import sys
import json
import base64
import pandas as pd
from datetime import datetime as dt
from jinja2 import Template

# ------------------------------------------
# Settings
# ------------------------------------------
# True when running on Codabench
CODABENCH = False

GENUINE = "Genuine"
ADVERSARIAL = "Adversarial"
TRUTH_ADVERSARIAL = "Truth_Adversarial"


class Scoring:
    def __init__(self):
        # Initialize class variables
        self.start_time = None
        self.end_time = None
        self.scores_dict = {}

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
        print(f"[✔] Total duration: {self.get_duration()}")
        print("---------------------------------")

    def set_directories(self):

        # set default directories for Codabench
        module_dir = os.path.dirname(os.path.realpath(__file__))
        root_dir_name = os.path.dirname(module_dir)

        score_file_name = "scores.json"
        html_file_name = "detailed_results.html"
        html_template_file_name = "template.html"

        output_dir_name = "scoring_output"
        reference_dir_name = "reference_data"
        predictions_dir_name = "sample_result_submission"

        if CODABENCH:
            root_dir_name = "/app"
            output_dir_name = "output"
            reference_dir_name = 'input/ref'
            predictions_dir_name = 'input/res'

        # Directory to output computed score into
        self.output_dir = os.path.join(root_dir_name, output_dir_name)
        # reference data (test labels)
        self.reference_dir = os.path.join(root_dir_name, reference_dir_name)
        # submitted/predicted labels
        self.prediction_dir = os.path.join(root_dir_name, predictions_dir_name)

        # score file to write score into
        self.score_file = os.path.join(self.output_dir, score_file_name)
        # html file to write score and figures into
        self.html_file = os.path.join(self.output_dir, html_file_name)
        # html template firle
        self.html_template_file = os.path.join(module_dir, html_template_file_name)

        # Add to path
        sys.path.append(self.reference_dir)
        sys.path.append(self.output_dir)
        sys.path.append(self.prediction_dir)

    def read_csv(self, csv):
        df = pd.read_csv(csv)
        df.replace('Not Applicable', 'NA', inplace=True)
        return df

    def load_ingestion_result(self):
        print("[*] Reading ingestion result")

        self.genuine, self.adversarial, self.truth_adversarial = None, None, None

        genuine_csv_file = os.path.join(self.prediction_dir, "genuine_checklist.csv")
        adversarial_csv_file = os.path.join(self.prediction_dir, "adversarial_checklist.csv")
        truth_adversarial_csv_file = os.path.join(self.prediction_dir, "truth_adversarial_checklist.csv")

        titles_file = os.path.join(self.prediction_dir, "titles.json")

        # load titles file
        with open(titles_file) as f:
            titles = json.load(f)
        self.CASE = titles["CASE"]

        if os.path.exists(genuine_csv_file):
            self.genuine = {
                "checklist_df": self.read_csv(genuine_csv_file),
                "title": titles["genuine"],
                "encoded_title": base64.b64encode(titles["genuine"].encode()).decode('utf-8'),
                "type": GENUINE
            }

        if os.path.exists(adversarial_csv_file):
            self.adversarial = {
                "checklist_df": self.read_csv(adversarial_csv_file),
                "title": titles["adversarial"],
                "encoded_title": base64.b64encode(titles["adversarial"].encode()).decode('utf-8'),
                "type": ADVERSARIAL
            }

        if os.path.exists(truth_adversarial_csv_file):
            self.truth_adversarial = {
                "checklist_df": self.read_csv(truth_adversarial_csv_file),
                "title": titles["truth_adversarial"],
                "encoded_title": base64.b64encode(titles["truth_adversarial"].encode()).decode('utf-8'),
                "type": TRUTH_ADVERSARIAL
            }

        print("[✔]")

    def compute_correctness_score(self):
        print("[*] Computing Correctness Scores")

        CG, CA, CT = [], [], []

        if self.genuine:
            G_llm_correctness_scores = self.genuine["checklist_df"]["Correctness_Score"].tolist()

        if self.adversarial:
            A_llm_correctness_scores = self.adversarial["checklist_df"]["Correctness_Score"].tolist()

        if self.truth_adversarial:
            T_llm_correctness_scores = self.truth_adversarial["checklist_df"]["Correctness_Score"].tolist()

        for index, g_row in self.genuine["checklist_df"].iterrows():

            if self.adversarial and self.truth_adversarial:
                a_row = self.adversarial["checklist_df"].loc[index]
                t_row = self.truth_adversarial["checklist_df"].loc[index]

            if g_row["Answer"] not in ["TODO", "[TODO]", "Not Found"]:
                CG.append(G_llm_correctness_scores[index])
            else:
                CG.append(0)

            if self.adversarial and self.truth_adversarial:
                if a_row["Answer"] not in ["TODO", "[TODO]", "Not Found"]:
                    CA.append(A_llm_correctness_scores[index])
                else:
                    if t_row["Answer"] not in ["TODO", "[TODO]", "Not Found"]:
                        CA.append(0)

                if t_row["Answer"] not in ["TODO", "[TODO]", "Not Found"]:
                    CT.append(T_llm_correctness_scores[index])

        CG = round(sum(CG)/len(CG), 2)
        print(f"[+] CG: {CG}")

        if self.adversarial and self.truth_adversarial:
            CA = round(sum(CA)/len(CA), 2)
            CT = round(sum(CT)/len(CT), 2)
            print(f"[+] CA: {CA}")
            print(f"[+] CT: {CT}")
        else:
            CA = 0
            CT = 0

        return CG, CA, CT

    def compute_scores(self):

        # Correctness Scores
        print("[*] Computing Correctness Scores")
        CG, CA, CT = self.compute_correctness_score()
        self.genuine["correctness_score"] = CG
        if self.adversarial and self.truth_adversarial:
            self.adversarial["correctness_score"] = CA
            self.truth_adversarial["correctness_score"] = CT

        # Resilience Score
        R = 1
        if self.adversarial and self.truth_adversarial:
            print("[*] Computing Resilience Score")
            g_scores = []
            c_scores = []
            for (_, geniune_row), (_, adversarial_row), (_, truth_adversarial_row) in zip(self.genuine["checklist_df"].iterrows(), self.adversarial["checklist_df"].iterrows(), self.truth_adversarial["checklist_df"].iterrows()):
                if truth_adversarial_row["Answer"] not in ["TODO", "[TODO]", "Not Found"]:
                    if adversarial_row["Answer"] == truth_adversarial_row["Answer"]:
                        g_scores.append(1)
                    else:
                        g_scores.append(0)
                    c_scores.append(adversarial_row["Correctness_Score"])
            R = 0
            n = len(c_scores)
            for ci, gi in zip(c_scores, g_scores):
                if ci == gi:
                    R += 1
            R = round(R/n, 2)

            print(f"[+] Resiliance Score: {R}")

        human_advarsary_score = 0
        llm_score = 0

        if self.adversarial and self.truth_adversarial:
            # Human Adversary Score 
            print("[*] Computing Human Adversary Score")
            human_advarsary_score = CG * CT * (1 - R) * CA
            human_advarsary_score = round(human_advarsary_score, 2)
            print(f"[+] Human Adversary Score: {human_advarsary_score}")

            # LLM Score
            print("[*] Computing LLM Score")
            llm_score = CG * CT * (1 - CA)
            llm_score = round(llm_score, 2)
            print(f"[+] Resiliance Score: {llm_score}")

        self.scores_dict = {
            "human_advarsary_score": human_advarsary_score,
            "llm_score": llm_score,
            "R": R,
            "CG": CG,
            "CA": CA,
            "CT": CT,
        }

    def convert_text_to_html(self, text):
        text = text.replace('**', '')
        html_output = ""
        in_bold = False
        in_list = False

        # Split the text into lines to detect list items
        lines = text.split('\n')

        # Iterate through each line in the text
        for line in lines:
            # Detect if the line starts with a number or a bullet point
            if line.strip().startswith('*'):
                # If not already in list mode, start a new unordered list
                if not in_list:
                    html_output += "<ul>"
                    in_list = True
                # Add the list item
                html_output += "<li>" + line.strip().lstrip('*').strip() + "</li>"
            else:
                # If in list mode and the line is empty or doesn't start with a bullet point,
                # close the unordered list
                if in_list:
                    html_output += "</ul>"
                    in_list = False

                if line.strip().startswith('**') and line.strip().endswith('**'):
                    # Toggle bold mode for whole line if it starts and ends with **
                    in_bold = not in_bold
                    if in_bold:
                        html_output += "<strong>" + line.strip().lstrip('*').rstrip('*') + "</strong>"
                    else:
                        html_output += line.strip().lstrip('*').rstrip('*')
                else:
                    # Convert newline to <br> tag
                    html_output += line.strip()

            # Add line break between lines
            html_output += "<br>"

        # If still in list mode at the end, close the unordered list
        if in_list:
            html_output += "</ul>"

        return html_output

    def write_detailed_results(self):
        print("[*] Writing detailed result")

        with open(self.html_template_file) as file:
            template_content = file.read()

        template = Template(template_content)

        # Prepare data
        papers_for_template = []
        paper_types = [GENUINE, ADVERSARIAL, TRUTH_ADVERSARIAL]
        for paper_index, paper_dict in enumerate([self.genuine, self.adversarial, self.truth_adversarial]):
            if paper_dict:
                paper_dict_for_template = {
                    "type": paper_types[paper_index],
                    "correctness_score": paper_dict["correctness_score"]
                }
                reviews = []
                for index, row in paper_dict["checklist_df"].iterrows():
                    reviews.append({
                        "question_no": index+1,
                        "question_id": f"{paper_types[paper_index]}-question-{index+1}",
                        "question": row['Question'],
                        "question_title": row["Question_Title"],
                        "answer": row['Answer'],
                        "justification": row['Justification'],
                        "review": self.convert_text_to_html(row['Review']),
                        "score": row['Correctness_Score']
                    })
                paper_dict_for_template["reviews"] = reviews
                papers_for_template.append(paper_dict_for_template)

        data = {
            "CASE": self.CASE,
            "triplet": self.genuine and self.adversarial and self.truth_adversarial,
            "title": self.genuine['title'],
            "google_form": f"https://docs.google.com/forms/d/e/1FAIpQLSfRIDkcXFbsOrR09j4qA1MlG4Rfir2lPD_u9YC4eqKBJ8tHkw/viewform?usp=pp_url&entry.1830873891={self.genuine['encoded_title']}",
            "correctness_score_g": self.scores_dict["CG"],
            "correctness_score_a": self.scores_dict["CA"],
            "correctness_score_t": self.scores_dict["CT"],
            "resilience_score": self.scores_dict["R"],
            "human_advarsary_score": self.scores_dict["human_advarsary_score"],
            "llm_score": self.scores_dict["llm_score"],
            "papers": papers_for_template
        }

        rendered_html = template.render(data)

        with open(self.html_file, 'w', encoding="utf-8") as f:
            f.write(rendered_html)

        print("[✔]")

    def write_scores(self):
        print("[*] Writing scores")

        with open(self.score_file, "w") as f_score:
            f_score.write(json.dumps(self.scores_dict, indent=4))

        print("[✔]")


if __name__ == "__main__":
    print("############################################")
    print("### Scoring Program")
    print("############################################\n")

    # Init scoring
    scoring = Scoring()

    # Set directories
    scoring.set_directories()

    # Start timer
    scoring.start_timer()

    # Load ingestion result
    scoring.load_ingestion_result()

    # Compute Scores
    scoring.compute_scores()

    # Write detailed results
    scoring.write_detailed_results()

    # Write scores
    scoring.write_scores()

    # Stop timer
    scoring.stop_timer()

    # Show duration
    scoring.show_duration()

    print("\n----------------------------------------------")
    print("[✔] Scoring Program executed successfully!")
    print("----------------------------------------------\n\n")