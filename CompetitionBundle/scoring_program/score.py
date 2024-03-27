# ------------------------------------------
# Imports
# ------------------------------------------
import os
import sys
import json
import base64
import pandas as pd
from datetime import datetime as dt

# ------------------------------------------
# Settings
# ------------------------------------------
# True when running on Codabench
CODABENCH = False

COLORS = {
    'blue': '#0000FF',
    'green': '#008000',
    'violet': '#7F00FF'
}


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

        if os.path.exists(genuine_csv_file):
            self.genuine = {
                "checklist_df": self.read_csv(genuine_csv_file),
                "title": titles["genuine"],
                "encoded_title": base64.b64encode(titles["genuine"].encode()).decode('utf-8'),
                "type": "genuine"
            }

        if os.path.exists(adversarial_csv_file):
            self.adversarial = {
                "checklist_df": self.read_csv(adversarial_csv_file),
                "title": titles["adversarial"],
                "encoded_title": base64.b64encode(titles["adversarial"].encode()).decode('utf-8'),
                "type": "adversarial"
            }

        if os.path.exists(truth_adversarial_csv_file):
            self.truth_adversarial = {
                "checklist_df": self.read_csv(truth_adversarial_csv_file),
                "title": titles["truth_adversarial"],
                "encoded_title": base64.b64encode(titles["truth_adversarial"].encode()).decode('utf-8'),
                "type": "truth_adversarial"
            }

        self._print(f"<h2>{self.genuine['title']}</h2>", False)

        print("[✔]")

    def compute_correctness_score(self, paper_type, checklist_df):
        print(f"[*] Computing Correctness Score for {paper_type}")

        scores = []
        llm_correctness_scores = checklist_df["Correctness_Score"].tolist()
        for index, row in checklist_df.iterrows():
            if row["Answer"] in ["TODO", "TODO", "Not Found"]:
                scores.append(0)
            else:
                scores.append(llm_correctness_scores[index])
        total_correct_answers = sum(scores)
        total_answers = len(checklist_df)

        correctness_rate = total_correct_answers / total_answers
        correctness_rate = round(correctness_rate, 2)

        self._print("--------------------------------------")
        self._print(f"[+] Correctness Rate ({paper_type}): {correctness_rate}")
        self._print("--------------------------------------")

        return correctness_rate

    def compute_scores(self):

        print("[*] Computing Correctness Scores")
        if self.genuine:
            self.genuine["correctness_score"] = self.compute_correctness_score(self.genuine["type"], self.genuine["checklist_df"])
        if self.adversarial:
            self.adversarial["correctness_score"] = self.compute_correctness_score(self.adversarial["type"], self.adversarial["checklist_df"])
        if self.truth_adversarial:
            self.truth_adversarial["correctness_score"] = self.compute_correctness_score(self.truth_adversarial["type"], self.truth_adversarial["checklist_df"])

        print("[*] Computing Resilience Score")
        self.resiliance_score = 0
        if self.adversarial and self.truth_adversarial:
            g_scores = []
            c_scores = []
            n = len(self.genuine["checklist_df"])
            for (_, geniune_row), (_, adversarial_row), (_, truth_adversarial_row) in zip(self.genuine["checklist_df"].iterrows(), self.adversarial["checklist_df"].iterrows(), self.truth_adversarial["checklist_df"].iterrows()):
                if adversarial_row["Answer"] == truth_adversarial_row["Answer"]:
                    g_scores.append(1)
                else:
                    g_scores.append(0)
                c_scores.append(geniune_row["Correctness_Score"])

            for ci, gi in zip(c_scores, g_scores):
                if ci == gi:
                    self.resiliance_score += 1
            self.resiliance_score = round(self.resiliance_score/n, 2)

            self._print("--------------------------------------")
            self._print(f"[+] Resiliance Score: {self.resiliance_score}")
            self._print("--------------------------------------")
        else:
            print("[-] Resilience score can be comouted only if you have submitted adversarial and truth adversarial papers" )

        print("[*] Computing Combined Score")
        CG, CA, CT, R = 0, 0, 0, 1
        if self.genuine:
            CG = self.genuine["correctness_score"]
        if self.adversarial:
            CA = self.adversarial["correctness_score"]
        if self.truth_adversarial:
            CT = self.truth_adversarial["correctness_score"]
        if self.resiliance_score:
            R = self.resiliance_score

        self.combined_score = CG * (CA * (1-R)) * CT
        self.combined_score = round(self.combined_score, 2)

        self._print("--------------------------------------")
        self._print(f"[+] Combined Score: {self.combined_score}")
        self._print("--------------------------------------")

        self.scores_dict = {
            "S": self.combined_score,
            "R": self.resiliance_score,
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

    def write_reviews_to_html(self):

        print("[*] Writing reviews to detailed result")
        for paper_dict in [self.genuine, self.adversarial, self.truth_adversarial]:
            if paper_dict:

                print(f"[*] \t{paper_dict['type']}")
                self._print(f"<h1><strong>{paper_dict['type']}</strong></h1>", False)
                for index, row in paper_dict["checklist_df"].iterrows():
                    self._print("--------------------------------------", False)
                    self._print(f"Question # {index+1}: {row['Question']}", False)
                    self._print(f"Answer: {row['Answer']}", False)
                    self._print(f"Justification: {row['Justification']}", False)
                    self._print(f"Review: {self.convert_text_to_html(row['Review'])}", False)
                    self._print(f"Correctness Score: {row['Correctness_Score']}", False)
                    self._print("--------------------------------------", False)
        print("[✔]")

    def write_google_form(self):

        form_link = f"https://docs.google.com/forms/d/e/1FAIpQLSfRIDkcXFbsOrR09j4qA1MlG4Rfir2lPD_u9YC4eqKBJ8tHkw/viewform?usp=pp_url&entry.463237339={self.genuine['encoded_title']}"
        htmlized_link = f"<h3> Post Submission Survey</h3><p><a href='{form_link}'>Click here to submit a post submission survey</a></p><br><br><br><br><br>"
        self.write_html(htmlized_link)

    def write_scores(self):
        print("[*] Writing scores")

        with open(self.score_file, "w") as f_score:
            f_score.write(json.dumps(self.scores_dict, indent=4))

        print("[✔]")

    def write_html(self, content):
        with open(self.html_file, 'a', encoding="utf-8") as f:
            f.write(content)

    def _print(self, content, console_print=True):
        if console_print:
            print(content)
        if content.startswith("Answer:"):
            content = self._color_content(content, COLORS["green"])
        if content.startswith("Justification:"):
            content = self._color_content(content, COLORS["green"])
        if content.startswith("Review:"):
            content = self._color_content(content, COLORS["blue"])
        self.write_html(content + "<br>")

    def _color_content(self, content, color):
        content = f"<span style='color:{color};'>{content}</span>"
        return content


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

    # Write review to html
    scoring.write_reviews_to_html()

    # Write google form link to html
    # scoring.write_google_form()

    # Write scores
    scoring.write_scores()

    # Stop timer
    scoring.stop_timer()

    # Show duration
    scoring.show_duration()

    print("\n----------------------------------------------")
    print("[✔] Scoring Program executed successfully!")
    print("----------------------------------------------\n\n")