# ------------------------------------------
# Imports
# ------------------------------------------
import os
import re
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

        self.paper = None

        csv_file = os.path.join(self.prediction_dir, "paper_checklist.csv")
        titles_file = os.path.join(self.prediction_dir, "titles.json")
        ground_truth_file = os.path.join(self.prediction_dir, "ground_truth.json")

        # load titles file
        with open(titles_file) as f:
            titles = json.load(f)

        # load ground truth file
        try:
            with open(ground_truth_file) as f:
                ground_truth = json.load(f)
                ground_truth = {int(k): v for k, v in ground_truth.items()}
        except:
            ground_truth = None

        if os.path.exists(csv_file):
            self.paper = {
                "checklist_df": self.read_csv(csv_file),
                "ground_truth": ground_truth,
                "title": titles["paper_title"],
                "encoded_title": base64.b64encode(titles["paper_title"].encode()).decode('utf-8')
            }
        else:
            raise ValueError("[-] Checklist CSV not found!")

        print("[✔]")

    def compute_scores(self):

        non_skipped_scores = []
        groun_truth_scores = []
        ground_truth = self.paper["ground_truth"]
        for i, row in self.paper["checklist_df"].iterrows():
            question_number = i + 1
            skip_question = ground_truth is not None and question_number not in ground_truth
            if skip_question:
                print(f"[!] Skipping Question # {question_number}")
                continue
            non_skipped_scores.append(float(row["Score"]))
            if ground_truth is not None:
                groun_truth_scores.append(ground_truth[question_number])

        print("[*] Computing Paper Quality Score")
        paper_quality_score = round(sum(non_skipped_scores) / len(non_skipped_scores), 2)
        print(f"[+] Paper Quality Score: {paper_quality_score}")
        print("[✔]")

        llm_accuracy = 0
        if len(groun_truth_scores) > 0:
            print("[*] Computing LLM Accuracy")
            sum_abs_differences = 0
            n = len(groun_truth_scores)
            for i in range(n):
                sum_abs_differences += abs(groun_truth_scores[i] - non_skipped_scores[i])
            llm_accuracy = round(sum_abs_differences / n, 2)
            print(f"[+] LLM Accuracy: {llm_accuracy}")
            print("[✔]")

        self.scores_dict = {
            "llm_accuracy": llm_accuracy,
            "paper_quality_score": paper_quality_score,
        }

    def convert_text_to_html(self, text):
        try:
            html_output = ""
            is_list = False
            list_type = None

            # Split the text into lines
            lines = text.split('\n')

            # Iterate through each line in the text
            for line in lines:

                if line.strip() in ["**", "#", "##", "###", "# Score", "## Score", "### Score"]:
                    continue

                if '**' in line:
                    line = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', line)

                if len(line) == 0:
                    html_output += "<br>"
                elif line.startswith('# '):
                    html_output += f"<h3>{line.strip()[2:]}</h3>"
                elif line.startswith('## '):
                    html_output += f"<h3>{line.strip()[3:]}</h3>"
                elif line.startswith('### '):
                    html_output += f"<h3>{line.strip()[4:]}</h3>"
                elif line.startswith('#### '):
                    html_output += f"<h4>{line.strip()[5:]}</h4>"
                elif line.startswith('- ') or line.startswith('* '):
                    if not is_list:
                        is_list = True
                        list_type = "ul"
                        html_output += f"<{list_type}>"
                    html_output += f"<li>{line.strip()[2:]}</li>"
                elif re.match(r'^\d+\.', line.strip()):
                    if not is_list:
                        is_list = True
                        list_type = "ol"
                        html_output += f"<{list_type}>"
                    html_output += f"<li>{line.strip()[line.find('.')+1:]}</li>"
                elif line.startswith("    *"):
                    nested_line_text = line
                    nested_line_text = nested_line_text.replace("    *", "• ")
                    html_output += f"&nbsp;&nbsp; {nested_line_text}<br>"
                elif line.startswith("        *"):
                    nested_line_text = line
                    nested_line_text = nested_line_text.replace("        *", "○ ")
                    html_output += f"&nbsp;&nbsp;&nbsp;&nbsp; {nested_line_text}<br>"
                else:
                    if is_list:
                        html_output += f"</{list_type}>"
                        is_list = False
                        list_type = None
                    html_output += line.strip()

            if is_list:
                html_output += f"</{list_type}>"

            return html_output
        except:
            return text

    def write_detailed_results(self):
        print("[*] Writing detailed result")

        with open(self.html_template_file) as file:
            template_content = file.read()

        template = Template(template_content)

        # Prepare data
        paper_dict_for_template = {
            "title": self.paper["title"]
        }
        reviews = []
        ground_truth = self.paper["ground_truth"]
        for index, row in self.paper["checklist_df"].iterrows():

            question_number = index + 1
            skip_question = ground_truth is not None and question_number not in ground_truth
            if skip_question:
                continue
            reviews.append({
                "question_no": question_number,
                "question_id": f"question-{question_number}",
                "question": row['Question'],
                "question_title": row["Question_Title"],
                "answer": row['Answer'],
                "justification": row['Justification'],
                "review": self.convert_text_to_html(row['Review']),
                "score": row['Score']
            })
        paper_dict_for_template["reviews"] = reviews

        data = {
            "llm_accuracy": self.scores_dict["llm_accuracy"],
            "paper_quality_score": self.scores_dict["paper_quality_score"],
            "paper": paper_dict_for_template,
            "google_form": f"https://docs.google.com/forms/d/e/1FAIpQLScr4fjvUGhtiTzBfsqm5CCVvAGafp3sLSSB_Txz2YHhnLiiyw/viewform?usp=pp_url&entry.1830873891={self.paper['encoded_title']}"
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
    print("[✔] You can check the detailed review by clicking the `eye` icon in front of your submission!")
    print("----------------------------------------------\n\n")
