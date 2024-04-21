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
            "paper": paper_dict_for_template
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
